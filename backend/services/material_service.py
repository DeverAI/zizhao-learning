"""素材主链路：计划、幂等今日素材、去重、归档、对话、进度。"""
from __future__ import annotations

import asyncio
import os
import re
import threading
from typing import Optional

from config import (
    beijing_today,
    load_settings,
)
from models import database as db
from services import agent_bridge, generator

# threading.Lock：跨 asyncio.run / 多次事件循环安全（单测与多 worker 场景）
_material_lock = threading.Lock()


def ensure_seed_plan() -> dict:
    existing = db.list_plan()
    if existing:
        return {"seeded": False, "count": len(existing)}
    seeds = (
        generator.build_default_plan_seeds()
        + generator.build_plan_seeds_from_shared()
        + generator.build_gap_seeds_from_curriculum()
    )
    n = db.insert_plan(seeds)
    return {"seeded": True, "count": n, "total_plan": len(db.list_plan())}


def seed_gap_from_weak_memory(limit: int = 15) -> dict:
    """初三补漏：海马体弱项 + 课程体系前置 → 计划表。"""
    added = db.insert_plan(generator.build_gap_seeds_from_weak(limit=limit))
    return {"added": added, "total_plan": len(db.list_plan())}


def hard_key_for(domain: str, source: str, title: str) -> str:
    return generator.make_hard_key(domain or "", source or "", title or "")


def check_duplicate(domain: str, source: str, title: str, concept_keys: list[str],
                    threshold: Optional[float] = None) -> dict:
    settings = load_settings()
    thr = float(
        threshold
        if threshold is not None
        else settings.get("material_dedup_threshold", 0.6)
    )
    hk = hard_key_for(domain, source, title)
    # L1
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM material_archive WHERE hard_key=?", (hk,)
        ).fetchone()
        if row:
            return {"duplicate": True, "layer": "L1", "hard_key": hk}
        row = conn.execute(
            "SELECT 1 FROM materials WHERE title=? AND source=? AND status!='failed' "
            "AND day_key != ?",
            (title, source, beijing_today()),
        ).fetchone()
        if row:
            return {"duplicate": True, "layer": "L1", "hard_key": hk}
    # L2
    for concepts in db.archive_concept_sets(domain):
        score = generator.jaccard(concept_keys or [], list(concepts))
        if score >= thr:
            return {
                "duplicate": True,
                "layer": "L2",
                "score": score,
                "threshold": thr,
            }
    return {"duplicate": False}


def archive_rows() -> list[dict]:
    return db.list_archive()


async def _generate_with_dedup(plan: dict, domain: str, max_tries: int = 3, user_id: str = "") -> Optional[dict]:
    negative = generator.used_fingerprint_prompt(archive_rows())
    memory_ctx = agent_bridge.teaching_context(domain=domain, title=plan.get("title") or "", user_id=user_id)
    last_result: Optional[dict] = None
    for attempt in range(max_tries):
        draft = await generator.generate_from_plan(
            plan, domain, negative_list=negative, memory_ctx=memory_ctx, user_id=user_id
        )
        source = draft.get("source") or plan.get("source_hint") or ""
        title = draft.get("title") or plan.get("title") or ""
        keys = draft.get("concept_keys") or []
        dup = check_duplicate(domain, source, title, keys)
        if not dup.get("duplicate"):
            draft["domain"] = domain
            draft["plan_id"] = plan.get("id") or ""
            draft["hard_key"] = hard_key_for(domain, source, title)
            return draft
        last_result = {"duplicate": dup, "attempt": attempt + 1, "draft_title": title}
    return last_result  # type: ignore[return-value]


async def get_or_create_today(force_domain: Optional[str] = None, user_id: str = "") -> dict:
    settings = load_settings()
    day_key = beijing_today()
    existing = db.get_today_material(day_key, user_id=user_id)
    if existing:
        existing["reused"] = True
        return existing

    ensure_seed_plan()
    picked: Optional[dict] = None
    last_err: Optional[dict] = None
    for _ in range(5):
        plan = db.pick_next_plan(force_domain)
        if not plan:
            break
        # 网络生成期间绝不持 threading.Lock（会堵死事件循环）
        result = await _generate_with_dedup(plan, force_domain or plan["domain"], user_id=user_id)
        if result and result.get("body"):
            picked = {**result, "plan": plan}
            break
        db.mark_plan_skipped(plan["id"], note="同质或重复，已跳过")
        last_err = result

    if not picked:
        recents = [m for m in db.list_recent_materials() if (m.get("user_id") or "") == (user_id or "")] or (
            db.list_recent_materials() if not user_id else []
        )
        if recents:
            fallback = recents[0]
            fallback["reused"] = True
            fallback["note"] = "今日生成失败，返回最近素材作回顾"
            fallback["degraded"] = True
            return fallback
        raise RuntimeError(f"无法生成今日素材：{last_err}")

    plan = picked.pop("plan")
    with _material_lock:
        existing = db.get_today_material(day_key, user_id=user_id)
        if existing:
            existing["reused"] = True
            return existing
        db.demote_old_active(except_id="", user_id=user_id)
        material = db.insert_material(
            {
                "plan_id": plan.get("id") or "",
                "domain": picked.get("domain") or plan.get("domain"),
                "title": picked.get("title") or plan.get("title"),
                "source": picked.get("source") or plan.get("source_hint") or "",
                "body": picked.get("body") or "",
                "key_points": picked.get("key_points") or [],
                "followups": picked.get("followups") or [],
                "concept_keys": picked.get("concept_keys") or [],
                "fingerprint": picked.get("fingerprint") or {},
                "status": "active",
                "day_key": day_key,
                "degraded": picked.get("degraded"),
                "user_id": user_id,
            }
        )
        db.mark_plan_used(plan["id"], material["id"])
        material["reused"] = False
        material["provider"] = picked.get("provider")
        material["audio_segments"] = []
        material["progress"] = db.get_progress(material["id"])
        return material


async def refresh_material(domain: Optional[str] = None, user_id: str = "") -> dict:
    """主动换素材：生成期间不持锁，只在写库时短锁。"""
    day_key = beijing_today()
    existing = db.get_today_material(day_key, user_id=user_id)
    if existing:
        db.update_material_status(existing["id"], "recent")
    return await _create_forced(domain=domain, user_id=user_id)


async def _create_forced(domain: Optional[str] = None, user_id: str = "") -> dict:
    day_key = beijing_today()
    ensure_seed_plan()
    picked = None
    for _ in range(5):
        plan = db.pick_next_plan(domain)
        if not plan:
            break
        result = await _generate_with_dedup(plan, domain or plan["domain"], user_id=user_id)
        if result and result.get("body"):
            picked = {**result, "plan": plan}
            break
        db.mark_plan_skipped(plan["id"], note="refresh 同质跳过")
    if not picked:
        raise RuntimeError("refresh 失败：无可用计划或生成重复")
    plan = picked.pop("plan")
    with _material_lock:
        existing = db.get_today_material(day_key, user_id=user_id)
        if existing:
            db.update_material_status(existing["id"], "recent")
        db.demote_old_active(except_id="", user_id=user_id)
        material = db.insert_material(
        {
            "plan_id": plan.get("id") or "",
            "domain": picked.get("domain") or plan.get("domain"),
            "title": picked.get("title") or plan.get("title"),
            "source": picked.get("source") or plan.get("source_hint") or "",
            "body": picked.get("body") or "",
            "key_points": picked.get("key_points") or [],
            "followups": picked.get("followups") or [],
            "concept_keys": picked.get("concept_keys") or [],
            "fingerprint": picked.get("fingerprint") or {},
            "status": "active",
            "day_key": day_key,
            "degraded": picked.get("degraded"),
            "user_id": user_id,
        }
    )
    db.mark_plan_used(plan["id"], material["id"])
    material["reused"] = False
    material["provider"] = picked.get("provider")
    return material


def one_line(body: str, title: str) -> str:
    text = re.sub(r"\s+", " ", (body or title or "").strip())
    return text[:80]


def archive_material(material: dict) -> Optional[str]:
    from config import ARCHIVE_BODY_DIR

    source = material.get("source") or ""
    title = material.get("title") or ""
    domain = material.get("domain") or ""
    hk = hard_key_for(domain, source, title)
    # 正文冷存
    body_path = os.path.join(ARCHIVE_BODY_DIR, f"{material['id']}.txt")
    try:
        with open(body_path, "w", encoding="utf-8") as f:
            f.write(material.get("body") or "")
    except OSError:
        body_path = ""
    aid = db.insert_archive(
        {
            "material_id": material["id"],
            "domain": domain,
            "title": title,
            "source": source,
            "concept_keys": material.get("concept_keys") or [],
            "fingerprint": material.get("fingerprint") or {},
            "one_line": one_line(material.get("body") or "", title),
            "hard_key": hk,
            "used_day": material.get("day_key") or "",
        }
    )
    if aid:
        db.update_material_status(material["id"], "archived")
    return aid


def run_archive_once(recent_days: Optional[int] = None) -> dict:
    settings = load_settings()
    days = int(recent_days or settings.get("material_recent_days", 30))
    # 1) 超出 recent 窗口
    archived = 0
    skipped = 0
    for mat in db.materials_ready_for_archive(days):
        if archive_material(mat):
            archived += 1
        else:
            skipped += 1
    # 2) 当天已是 active 之外、且有 finished 进度的也可提前归档
    for mat in db.list_recent_materials():
        if mat.get("status") != "recent":
            continue
        prog = db.get_progress(mat["id"])
        if prog and prog.get("finished"):
            if archive_material(mat):
                archived += 1
    return {"archived": archived, "skipped_duplicate": skipped, "recent_days": days}


def chat_system_prompt(material: dict) -> str:
    keys = material.get("key_points") or []
    follows = material.get("followups") or []
    memory_ctx = agent_bridge.teaching_context(
        domain=material.get("domain") or "",
        title=material.get("title") or "",
        user_id=material.get("user_id") or "",
    )
    weak = memory_ctx.get("weak_topics") or []
    weak_line = "；".join(f"{w.get('topic')}" for w in weak[:5]) or "无"
    return (
        "你是自招学习助手，当前会话挂载了一份素材。回答要围绕素材展开，"
        "必要时可延伸，但不要否认素材本身。"
        f"\n\n【今日素材】{material.get('title','')}"
        f"\n【来源】{material.get('source','')}"
        f"\n【正文】\n{material.get('body','')}"
        f"\n【关键点】{keys}"
        f"\n【追问种子】{follows}"
        f"\n【共享记忆薄弱点】{weak_line}"
        "\n\n若用户要求换素材/聊别的，应明确说明需要调用 refresh_material。"
    )


async def chat(session_id: str, message: str, material_id: Optional[str] = None) -> dict:
    """兼容入口：统一走 agent_chat，避免双轨与 Markdown 泄漏。"""
    from services import agent_chat

    return await agent_chat.agent_chat(
        session_id=session_id, message=message, material_id=material_id
    )
