"""Agent / 人格 / 上传 / 背诵 回归。LLM 关闭，不打真实网络。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class AgentStackTest(unittest.TestCase):
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

    def tearDown(self):
        self._tmp.cleanup()

    def test_strip_markdown_no_dollar_star(self):
        from services.persona import strip_markdown

        raw = "**很重要**\n# 标题\n- 条目\n`code`"
        out = strip_markdown(raw)
        self.assertNotIn("**", out)
        self.assertNotIn("#", out.split("\n")[0])
        self.assertIn("很重要", out)

    def test_calculator_safe(self):
        from services.agent_tools import safe_calculate, dispatch

        self.assertTrue(safe_calculate("(3/8)*100")["ok"])
        self.assertAlmostEqual(safe_calculate("(3/8)*100")["value"], 37.5)
        self.assertFalse(safe_calculate("__import__('os')")["ok"])
        r = dispatch("calculator", {"expression": "12*12"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["value"], 144)

    def test_search_shared_limited(self):
        from services.agent_tools import tool_search_shared

        r = tool_search_shared({"query": "勾股", "limit": 3})
        self.assertTrue(r["ok"])
        self.assertLessEqual(r["count"], 3)

    def test_profile_observes_and_stages(self):
        from services import persona

        p = persona.load_profile()
        for i in range(5):
            p = persona.observe_from_message(p, "我不会，太难了，详细讲清楚为什么")
        persona.save_profile(p)
        p2 = persona.load_profile()
        self.assertGreaterEqual(p2["stats"]["turns"], 5)
        self.assertIn(p2["impression"]["stage"], {"observed", "known", "stranger"})
        self.assertEqual(p2["preferences"]["detail_level"], "deep")

    def test_upload_txt_into_framework(self):
        from services import upload_service

        item = upload_service.save_upload(
            filename="note.txt",
            content="苏格拉底：未经审视的人生不值得过。".encode("utf-8"),
            framework="素材",
            title="审视人生",
            source="自编",
            tags=["philosophy"],
        )
        self.assertEqual(item["framework"], "素材")
        self.assertGreater(item["text_len"], 0)
        plans = __import__("models.database", fromlist=["x"]).list_plan()
        self.assertTrue(any("审视人生" in (x.get("title") or "") for x in plans))

    def test_recitation_grade(self):
        from services import recitation

        item = recitation.load_items()[0]
        good = item["passage"]
        g = recitation.grade_attempt(item["id"], good)
        self.assertTrue(g["ok"])
        self.assertTrue(g["passed"])
        g2 = recitation.grade_attempt(item["id"], "hello world")
        self.assertFalse(g2["passed"])

    def test_agent_chat_degrades_honestly(self):
        import asyncio
        from services import agent_chat, material_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today())
        res = asyncio.run(
            agent_chat.agent_chat("s1", "详细解释这个概念并布置下一步", material_id=mat["id"])
        )
        self.assertIn("reply", res)
        self.assertTrue(res["degraded"])
        self.assertTrue(res["no_markdown"])
        self.assertNotIn("**", res["reply"])
        self.assertIn("下一步", res["reply"] + "下一步")  # fallback 含动作
        self.assertTrue(res["reply"].find("下一步") >= 0 or "复述" in res["reply"])


if __name__ == "__main__":
    unittest.main()
