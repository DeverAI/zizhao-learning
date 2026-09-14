"""固件清单接口：仅后台、无用户升级入口。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class FirmwareEndpointTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        import config

        base = self._tmp.name
        for name, rel in [
            ("STORAGE_DIR", "storage"),
            ("MATERIALS_DIR", "storage/materials"),
            ("AUDIO_DIR", "storage/materials/audio"),
            ("ARCHIVE_BODY_DIR", "storage/materials/archive_bodies"),
            ("SESSIONS_DIR", "storage/sessions"),
            ("USERS_DIR", "storage/users"),
            ("FILES_DIR", "storage/files"),
            ("MEDIA_DIR", "storage/media"),
            ("RESIDENT_DIR", "storage/resident"),
        ]:
            setattr(config, name, os.path.join(base, rel))
        config.DB_PATH = os.path.join(base, "storage", "material.db")
        config.SETTINGS_FILE = os.path.join(base, "settings.json")
        config.EMAIL_OUTBOX = os.path.join(base, "storage", "email_outbox.json")
        config.ENABLE_LLM_GENERATION = False
        config.ensure_dirs()
        from models import database as db

        db.init_db()

    def tearDown(self):
        self._tmp.cleanup()

    def test_manifest_404_then_ok(self):
        from config import STORAGE_DIR
        from services import auth_service

        from fastapi.testclient import TestClient
        from main import app

        auth_service.issue_email_code("fw@b.co")
        import json
        import re

        from config import EMAIL_OUTBOX

        with open(EMAIL_OUTBOX, encoding="utf-8") as f:
            code = re.search(r"(\d{6})", json.load(f)[-1]["body"]).group(1)
        user, sid = auth_service.login_with_email_code("fw@b.co", code)
        from services import security

        token = security.make_session_token(sid)
        with TestClient(app) as c:
            r = c.get("/api/device/firmware/latest", headers={"X-Zizhao-Sid": token})
            self.assertEqual(r.status_code, 404)
            os.makedirs(os.path.join(STORAGE_DIR, "firmware"), exist_ok=True)
            with open(os.path.join(STORAGE_DIR, "firmware", "manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"version": "1.0.1", "url": "/api/device/firmware/bin", "sha256": "x"}, f)
            r = c.get("/api/device/firmware/latest", headers={"X-Zizhao-Sid": token})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["policy"], "background_only_no_user_ui")
            # 未登录必须 401
            r2 = c.get("/api/device/firmware/latest")
            self.assertEqual(r2.status_code, 401)


if __name__ == "__main__":
    unittest.main()
