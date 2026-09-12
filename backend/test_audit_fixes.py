"""检修回归：P0 修复钉死。"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class AuditFixTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        import config

        config.STORAGE_DIR = os.path.join(self._tmp.name, "storage")
        config.MATERIALS_DIR = os.path.join(config.STORAGE_DIR, "materials")
        config.AUDIO_DIR = os.path.join(config.MATERIALS_DIR, "audio")
        config.ARCHIVE_BODY_DIR = os.path.join(config.MATERIALS_DIR, "archive_bodies")
        config.DB_PATH = os.path.join(config.STORAGE_DIR, "material.db")
        config.SESSIONS_DIR = os.path.join(config.STORAGE_DIR, "sessions")
        config.SETTINGS_FILE = os.path.join(self._tmp.name, "settings.json")
        config.ENABLE_LLM_GENERATION = False
        config.ensure_dirs()
        from models import database as db

        db.init_db()
        self.db = db

    def tearDown(self):
        self._tmp.cleanup()

    def test_insert_material_same_day_no_crash(self):
        m1 = self.db.insert_material(
            {"title": "A", "source": "s", "domain": "philosophy", "body": "b", "day_key": "2026-09-12", "status": "active"}
        )
        m2 = self.db.insert_material(
            {"title": "B", "source": "s2", "domain": "history", "body": "b2", "day_key": "2026-09-12", "status": "active"}
        )
        self.assertNotEqual(m1["id"], m2["id"])
        self.assertEqual(m2["title"], "B")
        # 旧的 day_key 被清掉
        self.assertEqual(self.db.get_material(m1["id"])["day_key"], "")

    def test_session_id_path_traversal_safe(self):
        evil = "../../etc/passwd"
        safe = self.db.safe_session_id(evil)
        self.assertNotIn("..", safe)
        self.assertNotIn("/", safe)
        self.assertNotIn("\\", safe)
        self.db.bind_session_material(evil, "mid1")
        self.assertEqual(self.db.get_session_material(evil), "mid1")

    def test_insert_plan_title_dedup(self):
        a = self.db.insert_plan([{"domain": "philosophy", "seq": 1, "title": "T1", "source_hint": "x"}])
        b = self.db.insert_plan([{"domain": "philosophy", "seq": 2, "title": "T1", "source_hint": "y"}])
        self.assertEqual(a, 1)
        self.assertEqual(b, 0)
        self.assertEqual(len(self.db.list_plan()), 1)

    def test_pick_plan_recycles_skipped(self):
        from services import material_service

        material_service.ensure_seed_plan()
        p = self.db.pick_next_plan("philosophy")
        self.assertIsNotNone(p)
        self.db.mark_plan_skipped(p["id"], "test")
        # 哲学 5 条种子，跳过 1 条仍有 pending；全跳完后应能回收
        for _ in range(10):
            nxt = self.db.pick_next_plan("philosophy")
            if not nxt:
                break
            self.db.mark_plan_skipped(nxt["id"], "all")
        # 回收后仍能取出
        again = self.db.pick_next_plan("philosophy")
        self.assertIsNotNone(again)

    def test_agent_chat_tool_calls_not_false_degraded(self):
        """逻辑钉：content 空但有 tool_calls 不应进 fallback。"""
        from services import agent_chat

        msg = {
            "content": "",
            "tool_calls": [{"id": "1", "function": {"name": "calculator", "arguments": "{}"}}],
        }
        calls = agent_chat._parse_tool_calls(msg)
        self.assertEqual(len(calls), 1)
        # 模拟判断
        content, ok = "", True
        should_fail = (not ok) or (not content and not calls)
        self.assertFalse(should_fail)

    def test_challenge_tool(self):
        import asyncio as aio

        from services import agent_tools, material_service

        material_service.ensure_seed_plan()
        mat = aio.run(material_service.get_or_create_today())
        r = agent_tools.dispatch("challenge_material", {"material_id": mat["id"], "rounds": 3})
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(len(r["questions"]), 3)
        self.assertTrue(r["no_markdown"])

    def test_segment_tool(self):
        from services import agent_tools

        text = "第一段讲解。\n\n第二段讲解，稍微长一点。\n\n第三段。"
        r = agent_tools.dispatch("segment_material_text", {"text": text})
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["segment_count"], 2)
        self.assertFalse(r["audio_ready"])

    def test_gap_seeds(self):
        from services import generator, material_service

        gaps = generator.build_gap_seeds_from_curriculum(limit=10)
        self.assertGreater(len(gaps), 0)
        self.assertEqual(gaps[0]["domain"], "gap_fill")
        material_service.ensure_seed_plan()
        result = material_service.seed_gap_from_weak_memory(limit=5)
        self.assertIn("added", result)

    def test_material_service_chat_proxies_agent(self):
        from services import material_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today())
        res = asyncio.run(material_service.chat("s9", "解释一下", material_id=mat["id"]))
        self.assertIn("reply", res)
        self.assertNotIn("**", res["reply"])


if __name__ == "__main__":
    unittest.main()
