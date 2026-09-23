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


    def _login_token(self):
        import json
        import re

        from config import EMAIL_OUTBOX
        from services import auth_service, security

        auth_service.issue_email_code("bin@b.co")
        with open(EMAIL_OUTBOX, encoding="utf-8") as f:
            code = re.search(r"(\d{6})", json.load(f)[-1]["body"]).group(1)
        _user, sid = auth_service.login_with_email_code("bin@b.co", code)
        return security.make_session_token(sid)

    def test_bin_requires_auth_and_serves_file(self):
        """板端 OTA 下载契约：未登录 401；有 manifest 无文件 404；有文件返回字节。"""
        import json

        from config import STORAGE_DIR
        from main import app

        from fastapi.testclient import TestClient
        token = self._login_token()
        fwdir = os.path.join(STORAGE_DIR, "firmware")
        with TestClient(app) as c:
            # 未带任何凭据 → 401（本 client 从未走 HTTP 登录，cookie jar 为空；
            # token 是直接由 service 造的，不经过响应 set_cookie）
            self.assertEqual(c.get("/api/device/firmware/bin").status_code, 401)
            # 已登录但文件不存在 → 404
            os.makedirs(fwdir, exist_ok=True)
            self.assertEqual(
                c.get("/api/device/firmware/bin", headers={"X-Zizhao-Sid": token}).status_code, 404
            )
            # 放 firmware.bin → 200，返回原始字节
            with open(os.path.join(fwdir, "firmware.bin"), "wb") as f:
                f.write(b"OTA-PAYLOAD")
            r = c.get("/api/device/firmware/bin", headers={"X-Zizhao-Sid": token})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.content, b"OTA-PAYLOAD")
            # 板端实际走 Cookie: zsid=<签名token>（与 X-Zizhao-Sid 头是两条路，必须都过）
            rc = c.get("/api/device/firmware/bin", headers={"Cookie": f"zsid={token}"})
            self.assertEqual(rc.status_code, 200)
            self.assertEqual(rc.content, b"OTA-PAYLOAD")
            # 裸 sid（非签名 token）经 cookie 必须 401，钉死“禁裸 sid”契约
            self.assertEqual(c.get("/api/device/firmware/bin", headers={"Cookie": "zsid=raw-sid-no-sig"}).status_code, 401)
            # manifest 用相对 url，latest 原样回传（补绝对由固件做）
            with open(os.path.join(fwdir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"version": "1.0.2", "url": "/api/device/firmware/bin", "sha256": "ab"}, f)
            rl = c.get("/api/device/firmware/latest", headers={"Cookie": f"zsid={token}"})
            self.assertEqual(rl.status_code, 200)
            self.assertEqual(rl.json()["url"], "/api/device/firmware/bin")
            self.assertEqual(rl.json()["version"], "1.0.2")


if __name__ == "__main__":
    unittest.main()
