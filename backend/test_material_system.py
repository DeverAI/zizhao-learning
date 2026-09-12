"""自招素材后端回归：共享源、幂等今日、去重、归档、记忆增量。"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


class MaterialSystemTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        import config

        config.STORAGE_DIR = os.path.join(self._tmp.name, "storage")
        config.MATERIALS_DIR = os.path.join(config.STORAGE_DIR, "materials")
        config.AUDIO_DIR = os.path.join(config.MATERIALS_DIR, "audio")
        config.ARCHIVE_BODY_DIR = os.path.join(config.MATERIALS_DIR, "archive_bodies")
        config.DB_PATH = os.path.join(config.STORAGE_DIR, "material.db")
        config.SESSIONS_DIR = os.path.join(config.STORAGE_DIR, "sessions")
        config.SETTINGS_FILE = os.path.join(self._tmp.name, "settings.json")
        config.ENABLE_LLM_GENERATION = False
        config.ensure_dirs()

        from models import database as db

        self.db = db
        db.init_db()

    def tearDown(self):
        self._tmp.cleanup()

    def test_shared_source_readable(self):
        from services import agent_bridge

        status = agent_bridge.shared_status()
        self.assertTrue(status["exists"], "应能找到左邻右舍 学习Agent_new")
        self.assertTrue(status["curriculum"])
        self.assertTrue(status["hippocampus"])
        nodes = agent_bridge.extract_zizhao_nodes("自招")
        self.assertGreater(len(nodes), 0, "课程体系应包含自招 band 节点")
        mem = agent_bridge.load_shared_memory(apply_decay=True)
        self.assertIn("topics", mem)
        self.assertTrue(mem.get("source_available"))

    def test_today_idempotent_and_dedup_archive(self):
        from services import material_service
        from config import beijing_today

        material_service.ensure_seed_plan()
        first = asyncio.run(material_service.get_or_create_today())
        self.assertTrue(first.get("id"))
        self.assertEqual(first.get("day_key"), beijing_today())
        self.assertIn(
            first.get("domain"),
            {"philosophy", "history", "classics", "shared_curriculum"},
        )
        self.assertTrue(first.get("body"))
        self.assertTrue(first.get("degraded"), "关闭 LLM 后应标记 degraded")

        second = asyncio.run(material_service.get_or_create_today())
        self.assertEqual(first["id"], second["id"], "同日应幂等复用")
        self.assertTrue(second.get("reused"))

        dup = material_service.check_duplicate(
            first["domain"],
            first["source"],
            first["title"],
            first.get("concept_keys") or [],
        )
        self.assertFalse(dup.get("duplicate"), "当前 active 不应被 L1 判为 archive 重复")

        self.db.update_material_status(first["id"], "recent")
        with self.db.get_conn() as conn:
            conn.execute(
                "UPDATE materials SET day_key='2000-01-01' WHERE id=?", (first["id"],)
            )
        result = material_service.run_archive_once(recent_days=30)
        self.assertGreaterEqual(result["archived"], 1)
        archived = self.db.list_archive()
        self.assertGreaterEqual(len(archived), 1)
        self.assertTrue(archived[0]["hard_key"])

        dup2 = material_service.check_duplicate(
            first["domain"],
            first["source"],
            first["title"],
            first.get("concept_keys") or [],
        )
        self.assertTrue(dup2.get("duplicate"))
        self.assertEqual(dup2.get("layer"), "L1")

    def test_feedback_writes_local_memory_delta(self):
        from services import agent_bridge, material_service
        from config import STORAGE_DIR

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today())
        before = agent_bridge.load_shared_memory(apply_decay=False)
        agent_bridge.write_local_memory_delta(mat["title"], 0.05, reason="test")
        delta_path = os.path.join(STORAGE_DIR, "memory_delta.json")
        self.assertTrue(os.path.exists(delta_path))
        after = agent_bridge.load_shared_memory(apply_decay=False)
        self.assertEqual(set(before.get("topics", {})), set(after.get("topics", {})))

    def test_chat_degrades_without_lying(self):
        from services import material_service

        material_service.ensure_seed_plan()
        mat = asyncio.run(material_service.get_or_create_today())
        result = asyncio.run(
            material_service.chat(
                "sess-test", "请围绕素材介绍核心观点", material_id=mat["id"]
            )
        )
        self.assertIn("reply", result)
        self.assertEqual(result["material_id"], mat["id"])
        self.assertTrue(result.get("degraded"))
        self.assertIn("降级", result["reply"])


if __name__ == "__main__":
    unittest.main()
