"""LLM 活体套测：默认 skip（无 Key）；设 RUN_LLM_LIVE=1 且配置 Key 后跑。

验证：用户自注册 OpenAI 文本/TTS、素材生成、审核，禁止无 Key 时假装成功。
"""
from __future__ import annotations

import asyncio
import os
import sys
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

RUN = os.environ.get("RUN_LLM_LIVE") == "1"


@unittest.skipUnless(RUN, "set RUN_LLM_LIVE=1 to run live LLM suite")
class LiveLLMTest(unittest.TestCase):
    def test_user_text_and_tts_probe(self):
        import config

        config.ENABLE_LLM_GENERATION = True
        from services import user_api_service

        uid = os.environ.get("ZIZHAO_LIVE_USER", "live")
        view = user_api_service.public_view(uid)
        self.assertTrue(
            view["text"]["configured"] and view["tts"]["configured"],
            "请先在设置页配置 OpenAI 文本+TTS",
        )
        r1 = asyncio.run(user_api_service.probe_text(uid))
        r2 = asyncio.run(user_api_service.probe_tts(uid))
        print("text", r1)
        print("tts", r2)
        self.assertTrue(r1.get("ok"), r1)
        self.assertTrue(r2.get("ok"), r2)

    def test_generate_and_review(self):
        import config

        config.ENABLE_LLM_GENERATION = True
        from models import database as db
        from services import material_service, review_service

        db.init_db()
        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today(user_id="live"))
        self.assertTrue(mat.get("body"))
        # 真模型时 degraded 应为 False
        self.assertFalse(mat.get("degraded"), mat)
        rev = asyncio.run(review_service.review_today(user_id="live", optimize=False))
        self.assertTrue(rev.get("ok"))
        self.assertIn("rule", rev)


if __name__ == "__main__":
    unittest.main()
