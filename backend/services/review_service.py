"""每日素材多轮挑刺审核：挑不出来才 passed，passed 才允许出音频。

规则（产品硬约定）：
- AI 写完/录完 **不等于** 完成
- 每轮：规则底线 + LLM 找茬；有 issue 就改写再审
- max_rounds 用尽仍未净 → review_status=failed，离线包 audio 禁用
- 只有 review_status=passed 才 synthesize_mp3 / 进 bundle.audio
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from config import STORAGE_DIR, atomic_write_json, beijing_today, ensure_dirs, load_settings
from models import database as db
from services import generator, persona


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _review_path(day_key: str, user_id: str = "") -> str:
    ensure_dirs()
    import re

    uid = re.sub(r"[^\w-]", "_", user_id or "anon")[:40] or "anon"
    d = os.path.join(STORAGE_DIR, "reviews", day_key)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{uid}.json")


def set_review_status(material_id: str, status: str, rounds: int = 0, note: str = "") -> None:
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE materials SET review_status=?, review_rounds=?, review_note=? WHERE id=?",
            (status, str(int(rounds)), (note or "")[:500], material_id),
        )


def get_review_fields(mat: dict) -> dict:
    return {
        "review_status": mat.get("review_status") or "pending",
        "review_rounds": int(mat.get("review_rounds") or 0),
        "review_note": mat.get("review_note") or "",
    }


def audio_allowed(mat: dict) -> bool:
    return (mat.get("review_status") or "pending") == "passed"


def rule_review(mat: dict) -> dict:
    """不依赖 LLM 的底线挑刺。"""
    issues = []
    body = mat.get("body") or ""
    title = mat.get("title") or ""
    source = mat.get("source") or ""
    if not title:
        issues.append("无标题")
    if len(body) < 200:
        issues.append(f"正文过短 len={len(body)}")
    if not source:
        issues.append("无出处")
    if mat.get("degraded"):
        issues.append("degraded 生成")
    if "**" in body or body.strip().startswith("#"):
        issues.append("疑似 Markdown 残留")
    keys = mat.get("key_points") or []
    if len(keys) < 2:
        issues.append("关键点不足")
    # 可朗读性：过长句
    long_sentences = [s for s in body.replace("\n", "。").split("。") if len(s) > 180]
    if long_sentences:
        issues.append(f"存在超长句×{len(long_sentences)}，不利于朗读")
    score = max(0, 100 - len(issues) * 15)
    return {"rule_score": score, "issues": issues, "ok": score >= 70 and not mat.get("degraded")}


async def llm_critique(mat: dict, user_id: str = "", round_no: int = 1) -> dict:
    """一轮 LLM 找茬。失败 degraded=true，由规则结果兜底。"""
    from services import user_api_service

    prompt = (
        f"第 {round_no} 轮挑刺。你是不讨好的初三自招审核。\n"
        "输出 JSON：{\"score\":0-100,\"issues\":[],\"rewrite_hints\":[]}\n"
        f"标题：{mat.get('title')}\n出处：{mat.get('source')}\n"
        f"正文：\n{(mat.get('body') or '')[:2000]}\n"
        f"关键点：{mat.get('key_points')}\n"
        "硬查：出处可核、不跑题、深度够自招、无 Markdown、可朗读、无重复套话。"
        "挑不出问题时 issues=[] 且 score>=85。"
    )
    messages = [{"role": "user", "content": prompt}]
    cred = user_api_service.get_text_creds(user_id) if user_id else {}
    content = ""
    provider = "none"
    ok = False
    if cred:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    user_api_service.compose_chat_url(cred["base_url"]),
                    headers={"Authorization": f"Bearer {cred['api_key']}"},
                    json={"model": cred["model"], "messages": messages, "temperature": 0.2},
                )
                if r.status_code < 400:
                    content = (
                        (r.json().get("choices") or [{}])[0].get("message", {}).get("content") or ""
                    )
                    ok = bool(content)
                    provider = "user_api"
        except Exception:  # noqa: BLE001
            ok = False
    if not ok:
        content, ok, provider = await generator._chat_completion(messages, temperature=0.2, user_id=user_id)
    if not ok or not content:
        return {
            "llm_score": None,
            "issues": [],
            "rewrite_hints": [],
            "provider": provider,
            "degraded": True,
        }
    data = generator._parse_json_block(content)
    return {
        "llm_score": int(data.get("score") or 0),
        "issues": [str(x) for x in (data.get("issues") or [])],
        "rewrite_hints": [str(x) for x in (data.get("rewrite_hints") or [])],
        "provider": provider,
        "degraded": False,
    }


async def _rewrite_body(mat: dict, hints: list[str], user_id: str = "") -> str:
    messages = [
        {
            "role": "user",
            "content": (
                "改写初三自招讲解稿。纯文本，禁止 Markdown，800-1200字，保留出处。\n"
                f"原标题：{mat.get('title')}\n原出处：{mat.get('source')}\n"
                f"原正文：\n{(mat.get('body') or '')[:2500]}\n"
                f"必须处理：{hints}\n只输出改写正文。"
            ),
        }
    ]
    content, ok, _ = await generator._chat_completion(messages, temperature=0.4, user_id=user_id)
    if not ok:
        return ""
    return persona.strip_markdown(content)


def _update_body(material_id: str, body: str) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE materials SET body=?, degraded=0 WHERE id=?",
            (body, material_id),
        )


async def run_review_loop(
    material_id: str,
    user_id: str = "",
    max_rounds: int | None = None,
) -> dict:
    """多轮挑刺：有刺就改写再审；挑不出才 passed。"""
    settings = load_settings()
    max_rounds = int(max_rounds or settings.get("material_review_max_rounds", 4))
    mat = db.get_material(material_id)
    if not mat:
        return {"ok": False, "error": "material not found"}
    history = []
    status = "pending"
    for rnd in range(1, max_rounds + 1):
        mat = db.get_material(material_id) or mat
        rule = rule_review(mat)
        llm = await llm_critique(mat, user_id=user_id, round_no=rnd)
        issues = list(rule.get("issues") or []) + list(llm.get("issues") or [])
        # 去重
        uniq = list(dict.fromkeys(issues))
        clean = rule["ok"] and (not llm.get("issues")) and (
            llm.get("llm_score") is None or llm.get("llm_score") >= 85 or llm.get("degraded")
        )
        # LLM 不可用时：仅规则 ok 且非 degraded 生成 → 可过（诚实降级）
        if llm.get("degraded"):
            clean = bool(rule["ok"])

        history.append(
            {
                "round": rnd,
                "rule": rule,
                "llm": llm,
                "issues": uniq,
                "clean": clean,
            }
        )
        if clean:
            status = "passed"
            set_review_status(material_id, "passed", rnd, note="挑刺通过")
            break
        # 改写
        hints = list(llm.get("rewrite_hints") or []) + [f"修：{i}" for i in uniq[:5]]
        new_body = await _rewrite_body(mat, hints, user_id=user_id)
        if new_body and len(new_body) >= 200:
            _update_body(material_id, new_body)
        else:
            history[-1]["rewrite_failed"] = True
        status = "pending"
        set_review_status(material_id, "pending", rnd, note="改写后待复审")
    else:
        status = "failed"
        set_review_status(material_id, "failed", max_rounds, note=f"{max_rounds} 轮仍未净")

    result = {
        "ok": True,
        "material_id": material_id,
        "user_id": user_id,
        "day_key": beijing_today(),
        "status": status,
        "rounds": len(history),
        "audio_allowed": status == "passed",
        "history": history,
        "reviewed_at": _now(),
    }
    try:
        atomic_write_json(_review_path(beijing_today(), user_id), result)
    except Exception:  # noqa: BLE001
        pass
    return result


async def review_today(user_id: str = "", optimize: bool = True) -> dict:
    """对今日素材跑完整多轮审核。optimize 已并入循环（有刺必改写）。"""
    day = beijing_today()
    mat = db.get_today_material(day, user_id=user_id)
    if not mat:
        return {"ok": False, "degraded": True, "error": "no material today", "day_key": day}
    # 已 passed 则跳过
    if audio_allowed(mat):
        return {
            "ok": True,
            "status": "passed",
            "material_id": mat["id"],
            "audio_allowed": True,
            "skipped": True,
            "note": "已通过审核",
        }
    return await run_review_loop(mat["id"], user_id=user_id)


async def review_all_users_optimize() -> dict:
    settings = load_settings()
    day = beijing_today()
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT user_id FROM materials WHERE day_key=?", (day,)
        ).fetchall()
    users = [r["user_id"] or "" for r in rows] or [""]
    results = []
    for uid in users:
        try:
            results.append(await review_today(user_id=uid))
        except Exception as exc:  # noqa: BLE001
            results.append({"ok": False, "user_id": uid, "error": str(exc)[:200]})
    # 夜间审核后：对 passed 且无音频的补 TTS（可选）
    if settings.get("material_auto_tts_after_review", True):
        from services import media_service

        for uid in users:
            mat = db.get_today_material(day, user_id=uid)
            if mat and audio_allowed(mat):
                body = (mat.get("body") or "")[:1500]
                if body and not (mat.get("audio_path") or ""):
                    path, deg, prov = media_service.synthesize_mp3(
                        body, f"review_{mat['id']}.mp3", user_id=uid
                    )
                    if path:
                        with db.get_conn() as conn:
                            conn.execute(
                                "UPDATE materials SET audio_path=? WHERE id=?", (path, mat["id"])
                            )
    return {"day_key": day, "count": len(results), "results": results}
