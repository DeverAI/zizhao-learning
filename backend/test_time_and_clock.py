"""时间/日期回归：/api/system/time + 前端顶栏时钟契约。

为什么单列一个测试文件：
页面「日期时间正常显示」是硬需求，而日期一旦错一天，
今天的素材、时间表高亮、离线包 day_key 全部会串到错误的「今天」。
时间是最容易被时区悄悄搞坏、又最难肉眼看出来的东西，必须有断言钉住。
"""
from __future__ import annotations

import re
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import config
from config import beijing_now, beijing_today, beijing_weekday_cn, BEIJING_TZ
from main import app


class TestBeijingTimeHelpers(unittest.TestCase):
    def test_beijing_tz_is_utc_plus_8(self):
        self.assertEqual(BEIJING_TZ.utcoffset(None), timedelta(hours=8))

    def test_beijing_now_matches_utc_plus_8(self):
        expect = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
        got = beijing_now()
        delta = abs((expect - got).total_seconds())
        self.assertLess(delta, 5, "beijing_now 与 UTC+8 偏差应 <5s")

    def test_beijing_today_format(self):
        self.assertRegex(beijing_today(), r"^\d{4}-\d{2}-\d{2}$")

    def test_weekday_cn_consistent_with_iso_weekday(self):
        now = beijing_now()
        names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.assertEqual(beijing_weekday_cn(), names[now.weekday()])

    def test_day_rollover_boundary(self):
        """UTC 16:00 = 北京次日 00:00，这是最容易错一天的临界点。"""
        utc_1600 = datetime(2026, 3, 20, 16, 0, 0, tzinfo=timezone.utc)
        beijing = utc_1600.astimezone(BEIJING_TZ)
        self.assertEqual(beijing.strftime("%Y-%m-%d"), "2026-03-21")
        self.assertEqual(beijing.strftime("%H:%M"), "00:00")

    def test_day_key_uses_beijing_not_utc(self):
        """同一时刻 UTC 与北京可能不同日；day_key 必须是北京那一份。"""
        utc = datetime.now(timezone.utc)
        bj = utc.astimezone(BEIJING_TZ)
        self.assertEqual(config.beijing_today(), bj.strftime("%Y-%m-%d"))


class TestTimeEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = TestClient(app)

    def test_time_is_open_path(self):
        """/api/system/time 必须免鉴权：登录页也要能显示时间。"""
        r = self.c.get("/api/system/time")
        self.assertEqual(r.status_code, 200)

    def test_time_payload_shape(self):
        d = self.c.get("/api/system/time").json()
        for k in ("ok", "day_key", "date_cn", "weekday", "weekday_index",
                  "hm", "hms", "iso", "unix", "tz"):
            self.assertIn(k, d, f"缺字段 {k}")
        self.assertTrue(d["ok"])
        self.assertEqual(d["tz"], "CST-8")

    def test_time_formats(self):
        d = self.c.get("/api/system/time").json()
        self.assertRegex(d["day_key"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(d["date_cn"], r"^\d{4}年\d{2}月\d{2}日$")
        self.assertRegex(d["hm"], r"^\d{2}:\d{2}$")
        self.assertRegex(d["hms"], r"^\d{2}:\d{2}:\d{2}$")
        self.assertIn(d["weekday"], ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])

    def test_unix_matches_iso_and_beijing_today(self):
        d = self.c.get("/api/system/time").json()
        dt = datetime.fromisoformat(d["iso"])
        self.assertEqual(int(dt.timestamp()), d["unix"])
        self.assertEqual(dt.strftime("%Y-%m-%d"), d["day_key"])
        self.assertEqual(d["day_key"], beijing_today())

    def test_weekday_index_agrees_with_weekday_name(self):
        d = self.c.get("/api/system/time").json()
        names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.assertEqual(names[d["weekday_index"]], d["weekday"])

    def test_health_and_time_share_day_key(self):
        a = self.c.get("/api/system/time").json()["day_key"]
        b = self.c.get("/api/system/health").json()["day_key"]
        self.assertEqual(a, b)


class TestFrontendClockContract(unittest.TestCase):
    """前端时钟靠本地走时 + 服务端校时。这里只钉住两者约定，不跑浏览器。"""

    @classmethod
    def setUpClass(cls):
        import os

        backend = os.path.dirname(os.path.abspath(__file__))

        def slurp(name: str) -> str:
            with open(os.path.join(backend, "static", name), encoding="utf-8") as fh:
                return fh.read()

        cls.html = slurp("index.html")
        cls.js = slurp("app.js")
        cls.css = slurp("app.css")

    def test_topbar_has_clock_nodes(self):
        self.assertIn('id="clockHm"', self.html)
        self.assertIn('id="clockDate"', self.html)

    def test_clock_starts_before_login_gate(self):
        """startClock 必须在 bootstrap 之前调用：否则登录页看不到时间。

        只看 init() 里的调用序，不能拿全文 index —— renderHome 里也定义了
        同名的 loadApiSettings，且文件里 bootstrap 调用出现在多处。
        """
        tail = self.js[self.js.index("(async function init()"):]
        i_clock = tail.index("startClock();")
        i_boot = tail.index("await bootstrap();")
        self.assertLess(i_clock, i_boot, "时钟应先于登录态初始化启动")

    def test_clock_syncs_from_server_time(self):
        self.assertIn("/api/system/time", self.js)
        self.assertIn("clockSkewMs", self.js)

    def test_clock_ticking_every_second(self):
        self.assertRegex(self.js, r"setInterval\(renderClock,\s*1000\)")

    def test_clock_css_defined(self):
        self.assertIn(".top-clock", self.css)
        self.assertIn(".clock-hm", self.css)
        self.assertIn(".clock-date", self.css)

    def test_timetable_today_highlight_index_math(self):
        """JS getDay() 周日=0，服务端 weekday 周一=0；换算写错就高亮错一天。"""
        self.assertIn("getDay() + 6) % 7", self.js)
        self.assertIn("is-today", self.css)

    def test_panel_2_css_var_actually_defined(self):
        """app.js 用 var(--panel-2)，名字对不上就静默失效。"""
        self.assertIn("var(--panel-2)", self.js)
        self.assertIn("--panel-2:", self.css)

    def test_no_bare_await_in_sync_render_home(self):
        """renderHome 是同步函数，里面出现裸 await 就是解析期语法错误 → 全站白屏。

        正确做法：剥掉所有 async 函数体后，剩下的同步代码里不得再有 await。
        只按 async function 名字匹配容易漏掉 IIFE 写法，这里按括号配对粗剥。
        """
        start = self.js.index("function renderHome()")
        end = self.js.index("function renderZizhao()")
        body = self.js[start:end]

        def strip_async(src: str) -> str:
            out, i = [], 0
            while True:
                j = src.find("async ", i)
                if j < 0:
                    out.append(src[i:])
                    break
                out.append(src[i:j])
                k = src.find("{", j)
                if k < 0:
                    break
                depth, m = 0, k
                while m < len(src):
                    if src[m] == "{":
                        depth += 1
                    elif src[m] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    m += 1
                i = m + 1
            return "".join(out)

        self.assertNotIn(" await ", strip_async(body), "renderHome 同步段里不得出现 await")

    def test_render_home_is_called_synchronously_by_render(self):
        """render() 是同步调用 VIEWS[route]()，别把 renderHome 写成 async。"""
        self.assertNotRegex(self.js, r"async function renderHome")
        self.assertIn("fn = VIEWS[route] || renderHome", self.js)


if __name__ == "__main__":
    unittest.main()
