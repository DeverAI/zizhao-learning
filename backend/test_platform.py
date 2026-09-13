"""平台鉴权/组件/时间表/常驻资料 回归。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class PlatformTest(unittest.TestCase):
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

    def _last_code(self, email: str) -> str:
        import json
        import re

        from config import EMAIL_OUTBOX

        with open(EMAIL_OUTBOX, encoding="utf-8") as f:
            outbox = json.load(f)
        for item in reversed(outbox):
            if item.get("to") == email:
                m = re.search(r"(\d{6})", item.get("body") or "")
                if m:
                    return m.group(1)
        raise AssertionError(f"no code for {email}")

    def test_email_code_login_and_sid(self):
        from services import auth_service, security

        auth_service.issue_email_code("stu@example.com")
        code = self._last_code("stu@example.com")
        user, sid = auth_service.login_with_email_code("stu@example.com", code)
        self.assertTrue(sid.startswith("s"))
        token = security.make_session_token(sid)
        self.assertEqual(security.verify_session_token(token), sid)

    def test_device_passkey(self):
        from services import auth_service

        auth_service.issue_email_code("dev@example.com")
        code = self._last_code("dev@example.com")
        user, _ = auth_service.login_with_email_code("dev@example.com", code)
        prov = auth_service.provision_device(user["id"], "esp")
        self.assertIn("passkey", prov)
        u2, sid = auth_service.login_with_device_passkey(prov["device_id"], prov["passkey"])
        self.assertEqual(u2["id"], user["id"])
        with self.assertRaises(auth_service.AuthError):
            auth_service.login_with_device_passkey(prov["device_id"], "wrong")

    def test_timetable_and_resident(self):
        from services import resident_service, timetable_service

        uid = "u_test_1"
        timetable_service.add_item(uid, "数学", 0, "08:00", "09:00")
        items = timetable_service.list_items(uid)
        self.assertEqual(len(items), 1)
        bulk = timetable_service.bulk_from_text(uid, "周二 19:00-19:30 英语背诵")
        self.assertGreaterEqual(bulk["added"], 1)
        resident_service.add(uid, "古诗一句", "学而不思则罔", kind="classics")
        hits = resident_service.search(uid, "学而")
        self.assertEqual(len(hits), 1)

    def test_security_sanitize_and_rate(self):
        from services import security

        self.assertTrue(security.valid_email("a@b.co"))
        self.assertFalse(security.valid_email("not-an-email"))
        self.assertNotIn("../", security.sanitize_text("../../etc/passwd"))
        for _ in range(12):
            try:
                security.check_rate_limit("auth", "t1")
            except security.RateLimitError:
                break
        else:
            # 上限 10，应已抛出
            self.fail("rate limit not triggered")

    def test_component_registry(self):
        from services import component_registry

        catalog = component_registry.catalog()
        ids = {c["id"] for c in catalog}
        self.assertIn("zizhao", ids)
        self.assertIn("english", ids)
        payload = component_registry.home_payload("u_home")
        self.assertGreaterEqual(len(payload["components"]), 3)


if __name__ == "__main__":
    unittest.main()
