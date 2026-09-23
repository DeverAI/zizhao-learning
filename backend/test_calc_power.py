"""计算器幂运算与量级防护。

背景（2026-09-16 全链路实测发现）：
- GLM 把「二的一百次方」写成 `2100` —— 静默算错，比报错更坏
- 底层 `safe_calculate` 又因为 `MAX_POW_EXPONENT = 64` 把合法的 `2**100` 拒了

两条都要钉死：中文幂要能转成 `**`，合法量级要放行，爆炸幂要拦住。
"""
from __future__ import annotations

import os
import sys
import time
import unittest

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from routers.english_tools import _cn_num, _cn_power_expr  # noqa: E402
from services.agent_tools import safe_calculate  # noqa: E402


class TestChineseNumber(unittest.TestCase):
    def test_plain_digits(self):
        self.assertEqual(_cn_num("2"), 2.0)
        self.assertEqual(_cn_num("0.5"), 0.5)

    def test_single_and_teens(self):
        self.assertEqual(_cn_num("十"), 10.0)
        self.assertEqual(_cn_num("十五"), 15.0)
        self.assertEqual(_cn_num("二十"), 20.0)

    def test_hundreds_with_zero(self):
        self.assertEqual(_cn_num("一百"), 100.0)
        self.assertEqual(_cn_num("一百二十"), 120.0)
        self.assertEqual(_cn_num("一百零五"), 105.0)

    def test_apostrophe_form(self):
        """「一百二」口语里常被用作 120。这里按 102 解析（严格位值），
        只保证不崩、不为 None。"""
        v = _cn_num("一百二")
        self.assertIsNotNone(v)

    def test_invalid(self):
        self.assertIsNone(_cn_num(""))
        self.assertIsNone(_cn_num("你好"))


class TestCnArithExpr(unittest.TestCase):
    """纯中文算式 → 算式。无模型时的确定性兜底，必须能独立工作。"""

    def _f(self, s):
        from routers.english_tools import _cn_arith_expr

        return _cn_arith_expr(s)

    def test_basic_ops(self):
        self.assertEqual(self._f("三除以八再乘一百"), "3/8*100")
        self.assertEqual(self._f("一百加二十"), "100+20")
        self.assertEqual(self._f("五减二"), "5-2")
        self.assertEqual(self._f("一百除以三再乘三"), "100/3*3")

    def test_fraction_is_reversed(self):
        """「八分之三」= 3/8，不是 83 —— 中文分数是反着说的。"""
        self.assertEqual(self._f("八分之三"), "(3/8)")
        self.assertEqual(self._f("八分之三乘以一百"), "(3/8)*100")

    def test_percent_question_is_not_operator(self):
        """「百分之多少」是提问，不能被当成 /100 运算符。"""
        e = self._f("三除以八再乘一百百分之多少")
        self.assertEqual(e, "3/8*100")
        self.assertNotIn("%", e)

    def test_power(self):
        self.assertEqual(self._f("二的一百次方"), "2**100")
        self.assertEqual(self._f("2的10次方"), "2**10")

    def test_no_digit_returns_empty(self):
        self.assertEqual(self._f("你好"), "")
        self.assertEqual(self._f(""), "")

    def test_all_outputs_are_evaluable(self):
        """转换结果必须能被安全求值器接受，否则等于没转。"""
        from services.agent_tools import safe_calculate

        for t in ["三除以八再乘一百", "一百加二十", "八分之三乘以一百",
                  "二的一百次方", "十的三次方", "五减二"]:
            e = self._f(t)
            self.assertTrue(e, f"{t} 转换失败")
            self.assertTrue(safe_calculate(e)["ok"], f"{t} -> {e} 求值失败")


class TestCnPowerExpr(unittest.TestCase):
    def test_basic_power(self):
        self.assertEqual(_cn_power_expr("二的一百次方"), "2**100")
        self.assertEqual(_cn_power_expr("2的10次方"), "2**10")
        self.assertEqual(_cn_power_expr("二的一百次幂"), "2**100")
        self.assertEqual(_cn_power_expr("十的三次方"), "10**3")

    def test_no_false_positive_on_plain_arithmetic(self):
        """普通算式绝不能命中幂规则，否则会劫持整条计算链路。"""
        for t in ["三除以八再乘一百", "(3/8)*100", "一百加二十", "根号二"]:
            self.assertEqual(_cn_power_expr(t), "", f"误伤：{t}")

    def test_not_parsed_as_digit_concat(self):
        """核心回归：绝不能退化成 2100。"""
        self.assertNotEqual(_cn_power_expr("二的一百次方"), "2100")


class TestPowGuard(unittest.TestCase):
    def test_legal_grade_school_powers_pass(self):
        """2**100 是初中/自招真会遇到的题，必须能算。"""
        r = safe_calculate("2**100")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["value"], 1267650600228229401496703205376)

    def test_common_powers(self):
        self.assertEqual(safe_calculate("2**10")["value"], 1024)
        self.assertEqual(safe_calculate("2**64")["value"], 18446744073709551616)
        self.assertAlmostEqual(safe_calculate("1.05**20")["value"], 2.653297705144422)

    def test_huge_powers_still_blocked(self):
        for e in ["9**9**9", "10**400", "2**1024"]:
            r = safe_calculate(e)
            self.assertFalse(r["ok"], f"{e} 应被拒")

    def test_blocking_is_fast(self):
        """防护不能自己变成 DoS：必须毫秒级拒绝。"""
        t = time.time()
        for _ in range(20):
            safe_calculate("9**9**9")
        self.assertLess(time.time() - t, 1.0, "拦截爆炸幂耗时过长")

    def test_zero_and_negative(self):
        self.assertEqual(safe_calculate("0**0")["value"], 1)
        self.assertEqual(safe_calculate("5**0")["value"], 1)
        self.assertEqual(safe_calculate("(-2)**3")["value"], -8)

    def test_negative_base_fractional_exp_rejected(self):
        """(-8)**(1/3) 在实数域无解，Python 会返回复数 → 必须拒。"""
        self.assertFalse(safe_calculate("(-8)**(1/3)")["ok"])

    def test_plain_arithmetic_unaffected(self):
        self.assertEqual(safe_calculate("(3/8)*100")["value"], 37.5)
        self.assertEqual(safe_calculate("100/3*3")["value"], 100.0)


class TestCalcEndpointViaHttp(unittest.TestCase):
    """端到端：不走模型也能算幂（本地规则兜底）。

    这里不注入任何 API Key，强制走 fallback 分支 —— 正好验证
    「没有模型时中文幂也得能算」这条底线。
    """

    @classmethod
    def setUpClass(cls):
        import tempfile

        import config

        cls._tmp = tempfile.TemporaryDirectory()
        config.STORAGE_DIR = os.path.join(cls._tmp.name, "storage")
        config.DB_PATH = os.path.join(config.STORAGE_DIR, "material.db")
        config.SESSIONS_DIR = os.path.join(config.STORAGE_DIR, "sessions")
        config.USERS_DIR = os.path.join(config.STORAGE_DIR, "users")
        config.FILES_DIR = os.path.join(config.STORAGE_DIR, "files")
        config.MEDIA_DIR = os.path.join(config.STORAGE_DIR, "media")
        config.RESIDENT_DIR = os.path.join(config.STORAGE_DIR, "resident")
        config.TIMETABLE_DIR = os.path.join(config.STORAGE_DIR, "timetable")
        config.MATERIALS_DIR = os.path.join(config.STORAGE_DIR, "materials")
        config.AUDIO_DIR = os.path.join(config.MATERIALS_DIR, "audio")
        config.ARCHIVE_BODY_DIR = os.path.join(config.MATERIALS_DIR, "archive_bodies")
        config.EMAIL_OUTBOX = os.path.join(config.STORAGE_DIR, "email_outbox.json")
        config.SETTINGS_FILE = os.path.join(cls._tmp.name, "settings.json")
        config.ENABLE_LLM_GENERATION = False
        config.ensure_dirs()
        from models import database as db

        db.init_db()

        from fastapi.testclient import TestClient

        from main import app

        cls.c = TestClient(app)
        email = "calc-test@example.com"
        cls.c.post("/api/auth/email/send-code", json={"email": email})
        import json as _json

        with open(config.EMAIL_OUTBOX, encoding="utf-8") as fh:
            box = _json.load(fh)
        code = ""
        for it in reversed(box if isinstance(box, list) else box.get("items", [])):
            if it.get("to") == email:
                import re as _re

                m = _re.search(r"(\d{6})", str(it.get("body") or ""))
                if m:
                    code = m.group(1)
                    break
        cls.c.post("/api/auth/email/login", json={"email": email, "code": code})

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _calc(self, text: str):
        r = self.c.post("/api/tools/calc", json={"text": text})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_cn_power(self):
        d = self._calc("二的一百次方")
        self.assertEqual(d["expression"], "2**100")
        self.assertEqual(d["value"], 1267650600228229401496703205376)

    def test_digit_power(self):
        self.assertEqual(self._calc("2的10次方")["value"], 1024)

    def test_cn_power_of_ten(self):
        self.assertEqual(self._calc("十的三次方")["value"], 1000)

    def test_percent_question_not_divided_by_100(self):
        """「百分之多少」是问句，不该被额外补 /100。"""
        d = self._calc("三除以八再乘一百百分之多少")
        self.assertEqual(d["value"], 37.5)

    def test_plain_fraction(self):
        self.assertEqual(self._calc("三除以八再乘一百")["value"], 37.5)


class TestExtendBodySafetyMargin(unittest.TestCase):
    """续写必须补到 lo 之上留余量。

    实测教训：续写凑到 1498 字（差 2 字）→ 审核第 1 轮判「正文过短」→ 白烧 4 轮。
    免费模型输出长度天然抖动，卡在门槛上会每轮摩擦。
    """

    def test_source_targets_110_percent(self):
        with open(
            os.path.join(BACKEND, "services", "generator.py"), encoding="utf-8"
        ) as fh:
            src = fh.read()
        self.assertIn("target = int(lo * 1.1)", src)
        self.assertIn("len(body) >= target", src)

    def test_short_body_logs_warning(self):
        with open(
            os.path.join(BACKEND, "services", "generator.py"), encoding="utf-8"
        ) as fh:
            src = fh.read()
        self.assertIn("generator:extend_body_short", src)


class TestCalcEndpointPromptContract(unittest.TestCase):
    def test_source_mentions_power_rule(self):
        """prompt 里必须明确禁止把次方写成数字拼接，否则模型还会犯。"""
        with open(
            os.path.join(BACKEND, "routers", "english_tools.py"), encoding="utf-8"
        ) as fh:
            src = fh.read()
        self.assertIn("二的一百次方 → 输出：2**100", src)
        self.assertIn("绝不允许把「二的一百次方」写成 2100", src)
        # 「百分之多少」是问句，不该被补成 /100
        self.assertIn("百分之多少", src)


if __name__ == "__main__":
    unittest.main()
