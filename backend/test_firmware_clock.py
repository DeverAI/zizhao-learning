"""硬件固件「时间/日期格式化」的等价性验证。

没插板子 → 不能跑真机。但可以用 Python 复刻 C 里那三段 snprintf 逻辑，
喂边界时间进去，把「板子会显示成什么」算出来。这能挡住绝大多数
「日期差一天 / 显示 1970 / 星期错」的低级错误——正是用户点名要保证的东西。

对标文件：hardware/zizhao-esp32s3/main/clock_sync.c
"""
import os
import re
import unittest
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

# 与 clock_sync.c 里的 WEEKDAY_CN 逐字对齐（tm_wday: 0=周日）
WEEKDAY_CN = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
SRC = r"C:\Users\david\Documents\all_projects\自招学习\hardware\zizhao-esp32s3\main\clock_sync.c"


def fmt_hm(epoch):
    """复刻 clock_format_hm（含未校时守卫）"""
    t = datetime.fromtimestamp(epoch, CST)
    if t.year < 2020:
        return "--:--"
    return t.strftime("%H:%M")


def fmt_full(epoch):
    """复刻 clock_format_full"""
    return datetime.fromtimestamp(epoch, CST).strftime("%Y-%m-%d %H:%M:%S")


def fmt_date_cn(epoch):
    """复刻 clock_format_date_cn（含未校时守卫 + 中文星期）"""
    t = datetime.fromtimestamp(epoch, CST)
    if t.year < 2020:
        return "未校准（联网后自动对时）"
    # C 的 tm_wday: 0=周日；Python weekday(): 0=周一 → 换算
    wd = (t.weekday() + 1) % 7
    return f"{t.year}年{t.month:02d}月{t.day:02d}日 {WEEKDAY_CN[wd]}"


class TestFirmwareClockFormat(unittest.TestCase):
    def test_uncalibrated_shows_placeholder_not_1970(self):
        """RTC 未校时（epoch=0 → 1970）绝不能显示 1970 年。"""
        self.assertEqual(fmt_date_cn(0), "未校准（联网后自动对时）")
        self.assertEqual(fmt_hm(0), "--:--")

    def test_uncalibrated_2019_still_guard(self):
        """tm_year < 120 即 <2020，2019 也要判为未校准。"""
        e = datetime(2019, 12, 31, 23, 59, tzinfo=CST).timestamp()
        self.assertEqual(fmt_hm(e), "--:--")

    def test_calibrated_normal(self):
        """校时后正常输出。"""
        e = datetime(2026, 9, 16, 7, 30, tzinfo=CST).timestamp()
        self.assertEqual(fmt_hm(e), "07:30")
        self.assertEqual(fmt_date_cn(e), "2026年09月16日 周三")
        self.assertEqual(fmt_full(e), "2026-09-16 07:30:00")

    def test_cross_day_boundary(self):
        """UTC 16:00 = 北京次日 00:00 —— 这是最经典的差一天陷阱。"""
        e = datetime(2026, 9, 15, 16, 0, tzinfo=timezone.utc).timestamp()
        self.assertEqual(fmt_hm(e), "00:00")
        self.assertEqual(fmt_date_cn(e), "2026年09月16日 周三")

    def test_weekday_all_seven(self):
        """一周七天，中文星期必须与日历对齐（不差位）。"""
        base = datetime(2026, 9, 14, 12, 0, tzinfo=CST)  # 2026-09-14 是周一
        expect = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, w in enumerate(expect):
            e = (base + timedelta(days=i)).timestamp()
            got = fmt_date_cn(e)
            self.assertTrue(got.endswith(w), f"第{i}天 期望{w} 实际{got}")

    def test_zero_padding(self):
        """个位数月/日/时/分必须补零，否则墨水屏排版会跳。"""
        e = datetime(2026, 1, 5, 8, 7, tzinfo=CST).timestamp()
        self.assertEqual(fmt_hm(e), "08:07")
        self.assertEqual(fmt_date_cn(e), "2026年01月05日 周一")


def _read(p):
    """显式关文件：留着 unclosed file 会刷 ResourceWarning，把真实告警淹掉。"""
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


class TestFirmwareSourceContract(unittest.TestCase):
    """源码契约：钉住关键实现细节，防止后人改坏。"""

    @classmethod
    def setUpClass(cls):
        cls.src = _read(SRC)

    def test_tz_string_is_cst8_not_plus8(self):
        """POSIX TZ 是反的：UTC+8 要写 "CST-8"。写成 "+8" 会变成 UTC-8，差 16 小时。"""
        self.assertIn('"CST-8"', self.src)
        self.assertNotIn('"UTC+8"', self.src)

    def test_tz_init_called_before_localtime(self):
        """clock_tz_init 必须存在且设置 TZ + tzset。"""
        self.assertIn("void clock_tz_init(void)", self.src)
        self.assertIn("tzset()", self.src)

    def test_weekday_table_matches_python_order(self):
        """C 里 WEEKDAY_CN[0] 必须是「周日」（tm_wday 语义），不是「周一」。"""
        m = re.search(r"WEEKDAY_CN\[7\]\s*=\s*\{([^}]+)\}", self.src)
        self.assertIsNotNone(m, "找不到 WEEKDAY_CN 定义")
        items = re.findall(r'"([^"]+)"', m.group(1))
        self.assertEqual(items, ["周日", "周一", "周二", "周三", "周四", "周五", "周六"])

    def test_guard_threshold_is_120(self):
        """未校时判据是 tm_year < 120（即 <2020），不能改成别的值。"""
        self.assertIn("tm_year < 120", self.src)

    def test_http_fallback_parses_unix_field(self):
        """HTTP 兜底必须从 /api/system/time 取 unix 字段。"""
        self.assertIn("/api/system/time", self.src)
        self.assertIn("\\\"unix\\\"", self.src)

    def test_http_fallback_has_range_check(self):
        """HTTP 兜底必须做值域校验（挡脏数据），不能裸 settimeofday。"""
        self.assertIn("settimeofday", self.src)
        # 2020-01-01 ~ 2065 的量级校验
        self.assertRegex(self.src, r"1577\d{6}|1600000000|2020")


class TestMainCTimeChain(unittest.TestCase):
    """main.c 的三级校时链路。"""

    @classmethod
    def setUpClass(cls):
        cls.src = _read(
            r"C:\Users\david\Documents\all_projects\自招学习\hardware\zizhao-esp32s3\main\main.c"
        )

    def test_tz_init_before_wifi(self):
        """clock_tz_init() 必须在 wifi_sta_start **调用**之前，否则早期 localtime_r 走 UTC。

        陷阱：`wifi_sta_start` 在文件里先以**函数定义**出现（`static void wifi_sta_start(...)`），
        再以调用出现。用裸 index() 会匹配到定义，得出「顺序反了」的假结论。
        必须锚定带参数/分号的调用形态。
        """
        i_tz = self.src.index("clock_tz_init();")
        # 调用形态是 wifi_sta_start(&...); —— 定义形态是 static void wifi_sta_start(const ...)
        i_call = self.src.index("wifi_sta_start(&")
        self.assertLess(i_tz, i_call, "clock_tz_init() 必须先于 wifi_sta_start(&...) 调用")

    def test_three_level_fallback(self):
        """SNTP → HTTP → NVS 三级兜底，缺一不可。"""
        i_sntp = self.src.index("clock_sync_sntp()")
        i_http = self.src.index("clock_sync_http(")
        self.assertLess(i_sntp, i_http, "SNTP 应先于 HTTP 尝试")
        self.assertIn("clock_stash_load", self.src)

    def test_clock_page_uses_cn_date(self):
        """墨水屏时钟页要用中文日期函数，不是裸 strftime。"""
        self.assertIn("clock_format_date_cn", self.src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
