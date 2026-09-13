"""三人分用隔离回归。"""
from __future__ import annotations

import asyncio as aio
import os
import re
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class MultiUserIsolationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        import config

        base = self._tmp.name
        config.STORAGE_DIR = os.path.join(base, "storage")
        config.MATERIALS_DIR = os.path.join(config.STORAGE_DIR, "materials")
        config.AUDIO_DIR = os.path.join(config.MATERIALS_DIR, "audio")
        config.ARCHIVE_BODY_DIR = os.path.join(config.MATERIALS_DIR, "archive_bodies")
        config.DB_PATH = os.path.join(config.STORAGE_DIR, "material.db")
        config.SESSIONS_DIR = os.path.join(config.STORAGE_DIR, "sessions")
        config.USERS_DIR = os.path.join(config.STORAGE_DIR, "users")
        config.FILES_DIR = os.path.join(config.STORAGE_DIR, "files")
        config.MEDIA_DIR = os.path.join(config.STORAGE_DIR, "media")
        config.RESIDENT_DIR = os.path.join(config.STORAGE_DIR, "resident")
        config.SETTINGS_FILE = os.path.join(base, "settings.json")
        config.EMAIL_OUTBOX = os.path.join(config.STORAGE_DIR, "email_outbox.json")
        config.ENABLE_LLM_GENERATION = False
        config.ensure_dirs()
        from models import database as db

        db.init_db()
        self.db = db

    def tearDown(self):
        self._tmp.cleanup()

    def _login(self, email: str):
        from config import EMAIL_OUTBOX
        from services import auth_service

        auth_service.issue_email_code(email)
        with open(EMAIL_OUTBOX, encoding="utf-8") as f:
            import json

            outbox = json.load(f)
        for item in reversed(outbox):
            if item.get("to") == email:
                code = re.search(r"(\d{6})", item["body"]).group(1)
                break
        return auth_service.login_with_email_code(email, code)

    def test_profiles_isolated(self):
        from services import persona

        p1 = persona.load_profile("u1")
        p1["impression"]["traits"].append("用户1特质")
        persona.save_profile(p1, "u1")
        p2 = persona.load_profile("u2")
        self.assertNotIn("用户1特质", p2.get("impression", {}).get("traits") or [])
        p1b = persona.load_profile("u1")
        self.assertIn("用户1特质", p1b["impression"]["traits"])

    def test_today_materials_isolated(self):
        from services import material_service

        material_service.ensure_seed_plan()
        m1 = aio.run(material_service.get_or_create_today(user_id="u1"))
        m2 = aio.run(material_service.get_or_create_today(user_id="u2"))
        self.assertEqual(m1["user_id"], "u1")
        self.assertEqual(m2["user_id"], "u2")
        self.assertNotEqual(m1["id"], m2["id"])
        # 再取应各自复用
        m1b = aio.run(material_service.get_or_create_today(user_id="u1"))
        self.assertEqual(m1b["id"], m1["id"])

    def test_feedback_forbidden_across_users(self):
        from services import agent_bridge, material_service

        material_service.ensure_seed_plan()
        m1 = aio.run(material_service.get_or_create_today(user_id="u1"))
        # u2 不能写 u1 的 memory（服务层按 user_id 分文件）
        agent_bridge.write_local_memory_delta("T", 0.1, user_id="u1")
        d1 = agent_bridge.load_local_memory_delta("u1")
        d2 = agent_bridge.load_local_memory_delta("u2")
        self.assertIn("T", d1.get("topics", {}))
        self.assertNotIn("T", d2.get("topics", {}))
        self.assertEqual(m1["user_id"], "u1")

    def test_session_chat_scoped_by_user_prefix(self):
        from models import database as db
        from services import material_service

        material_service.ensure_seed_plan()
        m1 = aio.run(material_service.get_or_create_today(user_id="u1"))
        db.bind_session_material("u1:web", m1["id"])
        db.save_chat("u1:web", m1["id"], "user", "hello from u1")
        # u2 会话应为空
        self.assertEqual(db.get_session_material("u2:web"), "")
        self.assertEqual(len(db.list_chat("u2:web")), 0)
        self.assertEqual(len(db.list_chat("u1:web")), 1)

    def test_upload_list_filtered(self):
        from services import upload_service

        upload_service.save_upload(
            filename="a.txt", content=b"hello u1", framework="素材", title="A", user_id="u1"
        )
        upload_service.save_upload(
            filename="b.txt", content=b"hello u2", framework="素材", title="B", user_id="u2"
        )
        l1 = upload_service.list_uploads(user_id="u1")
        l2 = upload_service.list_uploads(user_id="u2")
        self.assertEqual(len(l1), 1)
        self.assertEqual(len(l2), 1)
        self.assertEqual(l1[0]["title"], "A")
        self.assertEqual(l2[0]["title"], "B")


if __name__ == "__main__":
    unittest.main()
