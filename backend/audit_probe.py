"""深度检修探针：验证怀疑的缺陷，不改生产库（用临时库）。"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import traceback

BACKEND = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND)

FINDINGS: list[dict] = []


def find(severity: str, code: str, title: str, evidence: str, fix: str = "") -> None:
    FINDINGS.append(
        {
            "severity": severity,
            "code": code,
            "title": title,
            "evidence": evidence,
            "fix": fix,
        }
    )
    print(f"[{severity}] {code}: {title}\n  {evidence[:200]}")


def isolate():
    import config

    tmp = tempfile.TemporaryDirectory()
    config.STORAGE_DIR = os.path.join(tmp.name, "storage")
    config.MATERIALS_DIR = os.path.join(config.STORAGE_DIR, "materials")
    config.AUDIO_DIR = os.path.join(config.MATERIALS_DIR, "audio")
    config.ARCHIVE_BODY_DIR = os.path.join(config.MATERIALS_DIR, "archive_bodies")
    config.DB_PATH = os.path.join(config.STORAGE_DIR, "material.db")
    config.SESSIONS_DIR = os.path.join(config.STORAGE_DIR, "sessions")
    config.SETTINGS_FILE = os.path.join(tmp.name, "settings.json")
    config.ENABLE_LLM_GENERATION = False
    config.ensure_dirs()
    from models import database as db

    db.init_db()
    return tmp, db


def main() -> int:
    tmp, db = isolate()

    # --- P0-1 insert_material UNIQUE(day_key) silent ignore + assert ---
    try:
        m1 = db.insert_material(
            {
                "title": "A",
                "source": "s",
                "domain": "philosophy",
                "body": "b1",
                "day_key": "2026-09-12",
                "status": "active",
            }
        )
        m2 = db.insert_material(
            {
                "title": "B",
                "source": "s2",
                "domain": "history",
                "body": "b2",
                "day_key": "2026-09-12",
                "status": "active",
            }
        )
        # 因 UNIQUE ON CONFLICT IGNORE，第二条可能根本没插入，却拿到第一条数据或 assert
        if m2["title"] != "B" or m2["id"] == m1["id"]:
            find(
                "P0",
                "DB-01",
                "insert_material 同 day_key 被静默忽略，却返回错误对象",
                f"m1={m1['id']}/{m1['title']} m2={m2['id']}/{m2['title']} day2={m2['day_key']}",
                "去掉 ON CONFLICT IGNORE 或插入前清 day_key / 用 INSERT OR REPLACE 显式策略",
            )
        else:
            find("INFO", "DB-01", "insert_material 第二次同日插入未复现（或 schema 宽松）", f"m2 title={m2['title']}")
    except Exception as exc:  # noqa: BLE001
        find("P0", "DB-01", "insert_material 同 day_key 直接崩溃", traceback.format_exc()[-300:], "修复 UNIQUE 策略")

    # --- P0-2 agent_chat: 空 content + tool_calls 被当成失败 ---
    from services import agent_chat

    msg = {
        "content": "",
        "tool_calls": [
            {"id": "1", "function": {"name": "calculator", "arguments": '{"expression":"1+1"}'}}
        ],
    }
    calls = agent_chat._parse_tool_calls(msg)
    # 逻辑缺陷：if not ok or not content 会在 content=='' 时降级，即使有 tool_calls
    content = ""
    ok = True
    if not ok or not content:
        find(
            "P0",
            "CHAT-01",
            "agent_chat 将「有 tool_calls 但 content 为空」误判为失败",
            f"parsed_calls={len(calls)} content_empty={content==''}",
            "改为 if not ok or (not content and not tool_calls)",
        )

    # --- P0-3 refresh 锁外生成，且 day_key 清理与 get_or_create 竞态 ---
    src = open(os.path.join(BACKEND, "services", "material_service.py"), encoding="utf-8").read()
    if "return await _create_forced(domain=domain)" in src and "_material_lock" in src:
        # _create_forced 在锁外
        if src.find("async with _material_lock:") < src.find("return await _create_forced"):
            find(
                "P1",
                "LOCK-01",
                "refresh_material 释放锁后才 _create_forced，存在竞态",
                "async with 块结束后才调用 _create_forced",
                "把 _create_forced 放进同一把锁，或让其自取锁",
            )

    # --- P1: 计划条目过少 / 不可复用 pending 耗尽 ---
    from services import material_service

    material_service.ensure_seed_plan()
    pending0 = len(db.list_plan("pending"))
    if pending0 < 40:
        find(
            "P1",
            "PLAN-01",
            "默认计划条目过少，撑不过几周每日素材",
            f"pending={pending0}",
            "从共享 curriculum 全量（不只自招 band）补种子 + 用户上传补充",
        )
    # pending 耗尽后无回收
    for _ in range(pending0 + 2):
        p = db.pick_next_plan()
        if not p:
            break
        db.mark_plan_used(p["id"], "x")
    if db.pick_next_plan() is None:
        find(
            "P1",
            "PLAN-02",
            "pending 耗尽后系统无法再取计划（无回收/无自动生成）",
            "pick_next_plan 返回 None",
            "增加 reset_skipped / 从 curriculum 再灌 / 报告空计划并给运维动作",
        )

    # --- P1: insert_plan 无 title 唯一，重复灌会膨胀 ---
    n_before = len(db.list_plan())
    db.insert_plan([{"domain": "philosophy", "seq": 1, "title": "苏格拉底·无知之知", "source_hint": "x"}])
    n_after = len(db.list_plan())
    # INSERT OR IGNORE 靠主键 id，title 不同 id 会重复
    dups = [p for p in db.list_plan() if p["title"] == "苏格拉底·无知之知"]
    if len(dups) > 1:
        find(
            "P1",
            "PLAN-03",
            "insert_plan 按 title 不去重，重复导入会膨胀计划表",
            f"count_title={len(dups)}",
            "唯一索引 (domain,title) 或插入前 SELECT",
        )

    # --- P1: material_service.chat 仍可能吐 Markdown（死代码但测试还在用）---
    if "strip_markdown" not in src.split("async def chat")[1][:1500]:
        find(
            "P2",
            "CHAT-02",
            "material_service.chat 未 strip_markdown，且与 agent_chat 双轨",
            "routers 已切 agent_chat，但 service.chat 保留原始模型输出",
            "废弃 service.chat 或改为代理到 agent_chat；测试改钉 agent_chat",
        )

    # --- P1: 无鉴权 ---
    main_src = open(os.path.join(BACKEND, "main.py"), encoding="utf-8").read()
    if "Depends" not in main_src and "api_password" not in main_src:
        find(
            "P1",
            "SEC-01",
            "全部 API 无鉴权（settings 有 api_password 字段但未用）",
            "main/routers 无 Depends 鉴权",
            "本地默认关；settings.api_password 非空时启用 Bearer",
        )

    # --- P1: 找茬式多轮无专用链路 ---
    if "challenge" not in open(os.path.join(BACKEND, "services", "agent_tools.py"), encoding="utf-8").read():
        find(
            "P1",
            "FEAT-01",
            "缺少「找茬式」多轮抬杠/追问工具（方案要求）",
            "agent_tools 无 challenge/quiz",
            "增加 challenge_material 工具与 /api/material/challenge 端点",
        )

    # --- P1: 音频 P5 未接 ---
    if "xiaomi_tts" not in open(os.path.join(BACKEND, "services", "generator.py"), encoding="utf-8").read():
        find(
            "P1",
            "FEAT-02",
            "音频预生成/分段（P5）未实现，设备 MP3 链路空",
            "material_audio 表在，无生成服务",
            "接共享 TTS 或标注 degraded 无音频；至少给出文本分段 API",
        )

    # --- P2: 归档正文无回读 API ---
    if "archive_bodies" in open(os.path.join(BACKEND, "services", "material_service.py"), encoding="utf-8").read():
        mat_router = open(os.path.join(BACKEND, "routers", "material.py"), encoding="utf-8").read()
        if "archive/body" not in mat_router and "cold" not in mat_router:
            find(
                "P2",
                "ARCH-01",
                "归档正文冷存到文件，但无回读接口",
                "archive_material 写 txt，router 无 GET",
                "增加 GET /api/material/archive/{id}/body",
            )

    # --- P2: 补漏（curriculum 非自招 band）未接入素材计划 ---
    if "补漏" not in src and "review" not in src:
        find(
            "P1",
            "FEAT-03",
            "初三知识补漏未接入：只有自招/哲学历史种子，无薄弱知识点补漏计划",
            "curriculum 仅抽 band=自招",
            "增加 /api/plan/seed_gap：按海马体弱项+prereq 生成补漏计划条目",
        )

    # --- P2: session_id 未消毒 ---
    if "session_id" in src and "../" not in src:
        # bind_session_material 直接拼路径
        db_src = open(os.path.join(BACKEND, "models", "database.py"), encoding="utf-8").read()
        if 'f"{session_id}.json"' in db_src and "replace" not in db_src.split("bind_session")[1][:400]:
            find(
                "P0",
                "SEC-02",
                "session_id 直接拼路径，可能路径穿越",
                "bind_session_material 使用 session_id 文件名",
                "白名单 [A-Za-z0-9_-]{1,64} 否则 hash",
            )

    print("\n===== FINDINGS", len(FINDINGS), "=====")
    for f in FINDINGS:
        print(f"{f['severity']}|{f['code']}|{f['title']}")
    tmp.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
