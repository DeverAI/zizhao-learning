"""审核门控 / 离线音频 / 开关机策略 钉测。"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class ReviewGateTest(unittest.TestCase):
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

    def test_audio_blocked_until_review_passed(self):
        from services import material_service, offline_service, review_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today(user_id="u1"))
        self.assertEqual(review_service.get_review_fields(mat)["review_status"], "pending")
        self.assertFalse(review_service.audio_allowed(mat))
        bundle = offline_service.build_daily_bundle("u1")
        self.assertFalse(bundle["audio_ready"])
        self.assertIn("review_status", bundle.get("audio_blocked_reason") or "")
        # 手动标 passed 后允许
        review_service.set_review_status(mat["id"], "passed", 1, note="test")
        mat2 = self.db.get_material(mat["id"])
        self.assertTrue(review_service.audio_allowed(mat2))

    def test_review_loop_rules_only_when_llm_off(self):
        from services import material_service, review_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today(user_id="u2"))
        # degraded 模板 → 规则必失败，循环会改写但 LLM 关 → 改写失败 → failed
        r = asyncio.run(review_service.run_review_loop(mat["id"], user_id="u2", max_rounds=2))
        self.assertTrue(r["ok"])
        self.assertIn(r["status"], {"passed", "failed", "pending"})
        self.assertFalse(r["audio_allowed"] or r["status"] == "passed")
        self.assertEqual(r["rounds"], 2)

    def test_power_policy_in_manifest(self):
        from services import material_service, offline_service

        material_service.ensure_seed_plan()
        asyncio.run(material_service.get_or_create_today(user_id="u3"))
        man = offline_service.build_manifest("u3")
        p = man["device_policy"]["power"]
        self.assertEqual(p["shutdown_hhmm"], "04:30")
        self.assertEqual(p["boot_hhmm"], "06:00")
        self.assertEqual(p["reboot_idle_sec"], 900)
        self.assertIn("onsite", man["device_policy"]["provision"])

    def test_review_fields_migrated(self):
        from services import material_service, review_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today(user_id="u4"))
        self.assertIn("review_status", mat)
        self.assertEqual(mat["review_status"], "pending")


if __name__ == "__main__":
    unittest.main()
