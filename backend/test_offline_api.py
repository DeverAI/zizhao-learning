"""用户 API / 离线包 / 审核 单元测试（不打真网）。"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class OfflineApiTest(unittest.TestCase):
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
        self.db = db

    def tearDown(self):
        self._tmp.cleanup()

    def test_user_api_mask_and_probe_degraded(self):
        from services import user_api_service

        user_api_service.save_user_apis(
            "u1",
            text={"base_url": "https://x.test/v1", "api_key": "sk-secret-123456", "model": "m1"},
            tts={"base_url": "https://x.test/v1", "api_key": "sk-tts-999999", "model": "tts-1", "voice": "alloy"},
        )
        view = user_api_service.public_view("u1")
        self.assertTrue(view["text"]["configured"])
        self.assertNotIn("secret", view["text"]["api_key_masked"])
        self.assertIn("…", view["text"]["api_key_masked"])
        cred = user_api_service.get_text_creds("u1")
        self.assertEqual(cred["model"], "m1")
        # 未配置用户 probe 应 degraded
        p = asyncio.run(user_api_service.probe_text("nobody"))
        self.assertFalse(p.get("ok"))
        self.assertTrue(p.get("degraded"))

    def test_offline_manifest_and_bundle(self):
        from services import material_service, offline_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today(user_id="u1"))
        man = offline_service.build_manifest("u1")
        self.assertTrue(man.get("ok"))
        self.assertTrue(man.get("daily_bundle_ready"))
        self.assertIn("volume_idle_sec", man.get("device_policy") or {})
        self.assertEqual(man["device_policy"]["volume_idle_sec"], 600)
        bundle = offline_service.build_daily_bundle("u1")
        self.assertEqual(bundle["material"]["id"], mat["id"])
        self.assertTrue(bundle.get("etag"))
        pkg = offline_service.component_package("zizhao", "u1")
        self.assertTrue(pkg.get("ok"))
        self.assertTrue(pkg.get("etag"))

    def test_rule_review_flags_degraded(self):
        from services import review_service

        r = review_service.rule_review(
            {"title": "T", "body": "短", "source": "", "key_points": [], "degraded": True}
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("短" in i or "过短" in i for i in r["issues"]))


if __name__ == "__main__":
    unittest.main()
