"""R03 修复钉：PassKey 验签、签名会话、quiz 闭环、工具注入。"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class R03FixTest(unittest.TestCase):
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

    def test_passkey_forbidden_without_valid_sig(self):
        from services import auth_service, security

        user, _ = self._login("pk@b.co")
        self.db.upsert_passkey(
            {
                "credential_id": "cred_x_123456",
                "user_id": user["id"],
                "public_key": "PUBKEY",
                "kind": "web",
                "created_at": "t",
            }
        )
        with self.assertRaises(auth_service.AuthError):
            auth_service.login_with_passkey("cred_x_123456", "chal", "forged")
        good = security.hmac_public_key("PUBKEY", "chal")
        u2, sid = auth_service.login_with_passkey("cred_x_123456", "chal", good)
        self.assertEqual(u2["id"], user["id"])

    def test_bare_sid_rejected_by_verify(self):
        from services import security

        sid = "s" + "a" * 20
        self.assertIsNone(security.verify_session_token(sid))
        self.assertEqual(security.verify_session_token(security.make_session_token(sid)), sid)

    def test_quiz_miss_feeds_gap_plan(self):
        import asyncio as aio

        from services import material_service, quiz_service

        material_service.ensure_seed_plan()
        mat = aio.run(material_service.get_or_create_today())
        quiz = quiz_service.build_quiz(mat["id"], rounds=4)
        self.assertGreaterEqual(len(quiz["questions"]), 3)
        answers = [{"id": q["id"], "text": ""} for q in quiz["questions"]]
        before = len(self.db.list_plan("pending"))
        g = quiz_service.grade_quiz(mat["id"], answers)
        self.assertLess(g["score"], g["total"])
        self.assertGreaterEqual(g["gap_plan_added"], 1)

    def test_agent_injects_user_id(self):
        import inspect

        from services import agent_chat

        src = inspect.getsource(agent_chat)
        self.assertIn("user_id", src)
        self.assertIn("_inject_uid", src)
        self.assertIn("resident_service", src)

    def test_rate_limit_default_raised(self):
        from config import RATE_LIMIT

        self.assertGreaterEqual(int(RATE_LIMIT["default"]["max"]), 600)


if __name__ == "__main__":
    unittest.main()
