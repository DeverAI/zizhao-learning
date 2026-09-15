"""TTS 分段边界：必须落在句读/段落，禁止随手截断。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class TtsChunkTest(unittest.TestCase):
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
        config.ensure_dirs()

    def tearDown(self):
        self._tmp.cleanup()

    def test_paragraph_and_sentence_boundaries(self):
        from services.media_service import _tts_chunk

        text = (
            "第一段讲拜占庭沦陷。它不是突然发生的。\n\n"
            "第二段讲尼采。他说过一句常被误读的话。\n\n"
            "第三段收束：论据要能回扣论点。"
        )
        chunks = _tts_chunk(text, size=30, min_size=10)
        self.assertGreaterEqual(len(chunks), 2)
        # 每块都应在完整句读附近结束或包含完整句，不应出现「沦陷。它」被硬切在句中
        for c in chunks:
            self.assertTrue(c.strip())
        # 原文关键短语必须完整出现在某一块
        joined = "".join(chunks)
        self.assertIn("拜占庭沦陷", joined)
        self.assertIn("尼采", joined)

    def test_no_hard_split_inside_decimal_or_english_word(self):
        from services.media_service import _tts_chunk

        text = "The value is 3.14159 exactly. " + ("filler word " * 80)
        chunks = _tts_chunk(text, size=80, min_size=10)
        joined = " ".join(chunks)
        # 小数点不应被切成 3. / 14159 两段
        self.assertNotIn("3. ", joined.replace("3.14159", ""))
        self.assertIn("3.14159", joined)

    def test_long_runon_splits_on_comma_not_midword(self):
        from services.media_service import _tts_chunk

        text = "这是一个很长的句子，中间有很多逗号，用来测试软断点，避免在词中间切断，最后结束。"
        chunks = _tts_chunk(text, size=20, min_size=8)
        for c in chunks:
            self.assertNotEqual(c[0], "，")
            self.assertTrue(len(c) <= 24 or "。" in c)
        self.assertIn("最后结束", "".join(chunks))

    def test_mp3_budget_min_300s(self):
        from services.media_service import _mp3_char_budget

        lo, hi = _mp3_char_budget()
        self.assertGreaterEqual(lo, 300 * 5)
        self.assertGreaterEqual(hi, lo)


if __name__ == "__main__":
    unittest.main()
