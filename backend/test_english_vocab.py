"""英语三库/进度/计算器 本地检（不打真网）。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class EnglishVocabTest(unittest.TestCase):
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

    def tearDown(self):
        self._tmp.cleanup()

    def test_three_banks_loaded(self):
        from services import english_vocab

        stats = english_vocab.bank_stats("u1")
        ids = {b["id"] for b in stats["banks"]}
        self.assertIn("gaokao", ids)
        self.assertIn("prep_collocations", ids)
        self.assertIn("familiar_new_sense", ids)
        for b in stats["banks"]:
            self.assertGreater(b["count"], 20, b)

    def test_card_and_grade_wrong_bank(self):
        from services import english_vocab

        card = english_vocab.next_card("u1", "gaokao", "en2cn", "new", "freq")
        self.assertTrue(card["ok"])
        word = card["answer"]["word"]
        r = english_vocab.grade_card("u1", "gaokao", word, "wrong")
        self.assertTrue(r["in_wrong_bank"])
        # wrong source 应能抽到
        c2 = english_vocab.next_card("u1", "gaokao", "cn2en", "wrong", "freq")
        self.assertTrue(c2["ok"])
        # known 移出错词
        english_vocab.grade_card("u1", "gaokao", word, "known")
        stats = english_vocab.bank_stats("u1")
        self.assertGreaterEqual(stats["known"], 1)

    def test_vague_options(self):
        from services import english_vocab

        r = english_vocab.vague_famous_sentence("abandon")
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["options"]), 2)
        self.assertIn(r["correct_index"], (0, 1))
        self.assertTrue(r["sentence"])

    def test_calc_tool_fallback(self):
        from services import agent_tools

        r = agent_tools.dispatch("calculator", {"expression": "(3/8)*100"})
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(float(r["value"]), 37.5)


if __name__ == "__main__":
    unittest.main()
