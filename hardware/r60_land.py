#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R59/R60 paperwork 落地器（唯一执行者 = 本文件；跑一遍即落盘）。

纪律（逐条都是本仓库已登记过的坑，这里装成代码而不是注释）：
  1. 所有裁决类的门排在 open(..., "w") 之前 —— 先验后写，宁响不静默。
  2. PROV_PASS 只从源码现读，值不进本文件的任何字面量、不进 stdout、不进产物。
     明文门配一只**只在内存里**造的阳性对照；对照样本永不落盘。
  3. 进产物的引文一律运行时现读被引文件并逐字插入 + 断言命中数，不靠我复述。
  4. 台账计数在最终字节串上先数后回填：先占位、写盘、回读、现算、替换、再回读断言。
  5. 不在正文写"将来会等于几"的绝对预测数。
  6. 版面常数（新旧两代）不从我的记忆取，从两份 eink_display.c 现读：
     旧代 = backups/r59_post_20260925_184900/main/ 那只，新代 = 工作树那只。
"""
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\david\Documents\all_projects\自招学习"
MAIN = ROOT + r"\hardware\zizhao-esp32s3\main"
REC = ROOT + r"\hardware\20260919_墨水屏点屏排查记录.md"
FREQ = ROOT + r"\FreqErr.md"
DONE = ROOT + r"\done.md"
DEV = ROOT + r"\dev_log\20260925.md"

CUR_EPD = MAIN + r"\eink_display.c"
OLD_EPD = ROOT + r"\hardware\zizhao-esp32s3\backups\r59_post_20260925_184900\main\eink_display.c"
PANEL154 = MAIN + r"\epd_panel_1in54.c"
UIFONT = MAIN + r"\ui_font.c"
PROFILE = MAIN + r"\board_profile.h"

LOG_OLD = r"C:\esp\r59z_20260925_183248_run.log"   # 镜像 473577b3（旧措辞）
LOG_NEW = r"C:\esp\r59z_20260925_184018_run.log"   # 镜像 714b9b84（板上这只）
LOG_OFF = r"C:\esp\r59f_20260925_174338_run.log"   # OFF-CTRL 断电对照臂读数
LOG_LOOP = r"C:\esp\r59b_20260925_170459_run.log"  # GPIO22..25 assert 复位环那把
PD_MAIN = r"C:\esp\pdiag\main\pdiag_main.c"
BIN = r"C:\esp\zproj\build\zizhao_esp32s3.bin"
ELF = r"C:\esp\zproj\build\zizhao_esp32s3.elf"


def rb(p):
    with open(p, "rb") as f:
        return f.read()


def rd(p):
    return rb(p).decode("utf-8", "replace")


def strip_ansi(t):
    return re.sub(r"\x1b\[[0-9;]*m", "", t)


def hits(carrier, needle):
    return [ln.strip() for ln in strip_ansi(rd(carrier)).splitlines() if needle in ln]


def grep_line(carrier, needle, want=1):
    """从载体里现读那一行（去 ANSI 后逐字返回），命中行数必须等于 want。"""
    hs = hits(carrier, needle)
    if len(hs) != want:
        raise SystemExit(f"ABORT: 引文 {needle!r} 在 {os.path.basename(carrier)} 命中 {len(hs)} 行，要求 {want}")
    return hs[0]


def count_is(name, path, needle, want):
    n = rd(path).count(needle)
    if n != want:
        raise SystemExit(f"ABORT: {name} 里 {needle!r} 现读 {n} 次，要求 {want}")
    print(f"PROBE {name} {needle!r} = {n}")


# ---------------- 门 0：载体在位 ----------------
for p in (REC, FREQ, DONE, DEV, LOG_OLD, LOG_NEW, LOG_OFF, LOG_LOOP, PD_MAIN, UIFONT,
           PANEL154, PROFILE, CUR_EPD, OLD_EPD, BIN, ELF, MAIN + r"\provision_ap.c"):
    if not os.path.isfile(p):
        raise SystemExit("ABORT: 载体缺失 " + p)
if os.path.getsize(BIN) < 1000000:
    raise SystemExit("ABORT: 待烧 bin 尺寸异常")

# ---------------- 门 1：明文（PROV_PASS）----------------
pas_src = rd(MAIN + r"\provision_ap.c")
m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', pas_src)
if not m:
    raise SystemExit("ABORT: 没能从 provision_ap.c 现读出 PROV_PASS，明文门无法自证")
SECRET = m.group(1)
print(f"GATE1 PROV_PASS 现读长度={len(SECRET)} 首字符类别={'ascii-lower' if SECRET[0].islower() else 'other'}")

# 阳性对照：只在内存里造，绝不落盘、绝不打印
_dirty = "热点:Zizhao-Setup-758D 密码:" + SECRET + " 打开192.168.4.1"
if SECRET not in _dirty:
    raise SystemExit("ABORT: 阳性对照样本自身不脏 —— 这道门没牙")
print("GATE1 POSCTL=FIRED（内存对照，未落盘）")


def check_clean(name, text):
    # 只拦"值"。原厂 dump 里那几个 NVS 键名（`sta.apsw` / `sta.pswd` / `LE_LOCAL_KEY_*`）是
    # esp-wifi 的公开符号名，登记"板上有这些键"不构成泄漏，也不该被这道门误伤。
    if SECRET in text:
        raise SystemExit(f"ABORT: 明文进了产物区块 {name}")
    print(f"GATE1 CLEAN {name}")


# ---------------- 现读引文 ----------------
q_init = grep_line(LOG_NEW, "epd154 init done")
q_full = grep_line(LOG_NEW, "full update done", want=3)      # 三次全刷，同形 3 行
q_blank = grep_line(LOG_NEW, "panel blanked")
q_ready = grep_line(LOG_NEW, "eink driver ready")
q_sd = grep_line(LOG_NEW, "SD mount fail")
q_sderr = grep_line(LOG_NEW, "send_op_cond")
q_old_full = grep_line(LOG_OLD, "full update done", want=3)
q_offctrl = grep_line(LOG_OFF, "armB_on_tr")
q_legend = grep_line(PD_MAIN, "B>=2")
q_mac = grep_line(LOG_NEW, "board MAC")
q_elf = grep_line(LOG_NEW, "ELF file SHA256")
onboard16 = re.search(r"ELF file SHA256:\s+([0-9a-f]{16})", strip_ansi(q_elf)).group(1)
lines_new = len(strip_ansi(rd(LOG_NEW)).splitlines())
lines_old = len(strip_ansi(rd(LOG_OLD)).splitlines())
lines_loop = len(strip_ansi(rd(LOG_LOOP)).splitlines())
count_is("epd_panel_1in54.c", PANEL154, "epd_rail_off();", 7)   # 只核存在与条数，不引用文本

# ---------------- 字模：逐档现读，先证"同档等宽/等高"再取第一只 ----------------
uf = rd(UIFONT)


def glyph_field(tag, field):
    """返回该档全部字模的 field（'w' 或 'h'）取值集合里的单值。"""
    pat = r"const uif_glyph_t %s_g[0-9A-F]+ = \{0x[0-9A-F]+, (\d+), (\d+)" % tag
    gi = 0 if field == "w" else 1
    vals = set(int(mm[gi]) for mm in re.findall(pat, uf))
    if len(vals) != 1:
        raise SystemExit(f"ABORT: {tag} 的 {field} 不是单值：{sorted(vals)} —— 不能取第一只当整档")
    return vals.pop()


# h 四档都单值 ⇒ C 侧 font_row_height() 取 glyphs[0]->h 的写法成立；
# w 只有全角/半角两档单值（DIGIT96 的 w 按字形宽窄变化，而本演算不用它）。
H = {t: glyph_field(t, "h") for t in ("CJK32", "LATIN32", "ASCII16", "DIGIT96")}
W = {t: glyph_field(t, "w") for t in ("CJK32", "LATIN32", "ASCII16")}
ASC = {}
for t in ("CJK32", "LATIN32", "ASCII16", "DIGIT96"):
    mm = re.search(r"const uif_font_t UIF_%s = \{\w+, (\d+), (\d+)\};" % t, uf)
    if not mm:
        raise SystemExit("ABORT: 读不到 UIF_" + t + " 的定义")
    ASC[t] = int(mm.group(2))
h_cjk, a_cjk = H["CJK32"], ASC["CJK32"]
if h_cjk != 43 or a_cjk != 34:
    raise SystemExit(f"ABORT: CJK32 现读 h={h_cjk} ascent={a_cjk}，与本遍登记的 43/34 不符")
for t in sorted(H):
    print(f"FONT {t}: h={H[t]} ascent={ASC[t]} 差={H[t] - ASC[t]}" +
          (f" w={W[t]}" if t in W else " w=非单值(不参与本演算)"))

# ---------------- 版面常数：两代各从一份 eink_display.c 现读 ----------------
prof = rd(PROFILE)
_pi = prof.index("#if BOARD_EPAPER_1IN54")
W_PX = int(re.search(r"#define\s+EPD_WIDTH\s+(\d+)", prof[_pi:]).group(1))
H_PX = int(re.search(r"#define\s+EPD_HEIGHT\s+(\d+)", prof[_pi:]).group(1))
if (W_PX, H_PX) != (200, 200):
    raise SystemExit(f"ABORT: 1.54 几何现读 {W_PX}x{W_PX}，不是 200x200")


def lay154(path):
    txt = rd(path)
    i = txt.index("#if BOARD_EPAPER_1IN54")
    j = txt.index("#else", i)
    blk = txt[i:j]
    d = {}
    for name, val in re.findall(r"^[ \t]*#define\s+(LAY_\w+)[ \t]+(.+)$", blk, re.M):
        v = val.split("/*")[0].strip()
        mm = re.fullmatch(r"\(\s*EPD_WIDTH\s*-\s*(\d+)\s*\)", v)
        n = W_PX - int(mm.group(1)) if mm else (int(v) if v.isdigit() else None)
        if n is None:
            raise SystemExit(f"ABORT: {name} 的值 {v!r} 解释不出数字")
        d[name] = n
    if len(d) != 11:
        raise SystemExit(f"ABORT: {os.path.basename(path)} 的 1.54 版面常数现读 {len(d)} 只，要求 11")
    return d


lay_old, lay_new = lay154(OLD_EPD), lay154(CUR_EPD)
print(f"LAY old={lay_old}")
print(f"LAY new={lay_new}")

# ---------------- 版面演算（复刻 draw_wrapped/glyph_width 的规则；口令用等长占位）----------------
# glyph_width(): 空格恒 12（与字体档无关，见 eink_display.c:209）；半角 = 该档 w+1；全角 = CJK32 w+1。
ADV_CJK = W["CJK32"] + 1
MSG = "热点:" + "Zizhao-Setup-758D" + " " + "密码:" + "x" * len(SECRET) + " " + "打开192.168.4.1"
if SECRET in MSG:
    raise SystemExit("ABORT: 演算样本里混进了真口令")


def wrap_rows(half_adv, maxw):
    rows, cur = [], 0
    for ch in MSG:
        g = 12 if ch == " " else (ADV_CJK if ord(ch) >= 0x80 else half_adv)
        if cur and cur + g > maxw:
            rows.append(cur)
            cur = g
        else:
            cur += g
    if cur:
        rows.append(cur)
    return rows


def stack(rows, y0, pitch, row_h, clamp):
    """返回 (末行 y, 末行底边, 最坏相邻行重叠 px, 越屏底 px)。
    row_h 一律按最坏行（含全角 = CJK32 的 h）算：纯半角行更矮，只会让实际重叠更小。
    clamp=True 时行距取「本行字模高」与传入常数的较大者（= R60 之后的下限语义）。"""
    y, worst_ov = y0, 0
    for i in range(len(rows)):
        if i:
            eff = max(pitch, row_h) if clamp else pitch
            worst_ov = max(worst_ov, row_h - eff)
            y += eff
    return y, y + row_h - 1, worst_ov, max(0, y + row_h - H_PX)


half_old, half_new = W["LATIN32"] + 1, W["ASCII16"] + 1
rows_old = wrap_rows(half_old, lay_old["LAY_MSG_W"])
rows_new = wrap_rows(half_new, lay_new["LAY_MSG_W"])
n_old, n_new = len(rows_old), len(rows_new)
w_old, w_new = sum(rows_old), sum(rows_new)
# 旧版面：行距 = lay_old 的 LAY_MSG_H，且当时没有钳位（clamp=False）
oy0 = lay_old["LAY_MSG_Y"]
o_lasty, o_lastb, o_ov, o_off = stack(rows_old, oy0, lay_old["LAY_MSG_H"], h_cjk, False)
n_lasty, n_lastb, n_ov, n_off = stack(rows_new, lay_new["LAY_MSG_Y"], lay_new["LAY_MSG_H"], h_cjk, True)
# 同根因的第二、第三处（行间距 vs 字模高）
st_gap_old = lay_old["LAY_STATUS_L2"] - lay_old["LAY_STATUS_L1"]
st_ov_old = h_cjk - st_gap_old
ck_date_b_old = lay_old["LAY_CLOCK_DATE"] + h_cjk - 1
ck_ov_old = ck_date_b_old - lay_old["LAY_CLOCK_TITLE"] + 1
st_gap_new = lay_new["LAY_STATUS_L2"] - lay_new["LAY_STATUS_L1"]
ck_gap_new = lay_new["LAY_CLOCK_TITLE"] - (lay_new["LAY_CLOCK_DATE"] + h_cjk)
print(f"LAYOUT old: rows={n_old} width={w_old}px y0={oy0} pitch={lay_old['LAY_MSG_H']} 重叠={o_ov}px 末行y={o_lasty} 底边={o_lastb} 越屏底={o_off}px")
print(f"LAYOUT new: rows={n_new} width={w_new}px pitch={lay_new['LAY_MSG_H']} 重叠={n_ov}px 末行底边={n_lastb} 越屏底={n_off}px")
print(f"LAYOUT 二/三处: STATUS 间距 old={st_gap_old}(重叠{st_ov_old}) new={st_gap_new} | CLOCK DATE底边 old={ck_date_b_old} vs TITLE old={lay_old['LAY_CLOCK_TITLE']}(重叠{ck_ov_old}) new gap={ck_gap_new}")

# 裁决门：这三条不过，就不许写"已修"
if n_new < 2:
    raise SystemExit("ABORT: 演算出新版面只 1 行，规则复刻有误")
if n_off > 0 or n_ov > 0:
    raise SystemExit(f"ABORT: 新版面仍越屏底 {n_off}px / 仍重叠 {n_ov}px —— 不能登记为已修")
if o_off <= 0 or o_ov <= 0:
    raise SystemExit(f"ABORT: 旧版面算不出'越屏底 + 重叠'（off={o_off} ov={o_ov}）—— 根因不成立，不许落纸")
if st_ov_old <= 0 or ck_ov_old <= 0:
    raise SystemExit("ABORT: STATUS/CLOCK 两处同根因重叠不成立，§38.31 那句得改")
if n_new >= n_old:
    raise SystemExit("ABORT: pick_compact 没有减少行数，措辞需重核")

# ---------------- 镜像身份链（现算）----------------
bin_b = rb(BIN)
md5_new = hashlib.md5(bin_b).hexdigest()
size_new = len(bin_b)
sha_elf = hashlib.sha256(rb(ELF)).hexdigest()
s16 = bin_b[176:184].hex()
if s16 != sha_elf[:16]:
    raise SystemExit("ABORT: 镜像身份等式 bin[176:184] == sha256(elf)[:16] 不成立")
print(f"IMAGE 待烧 md5={md5_new} size={size_new} elf_sha16={s16}  板上 elf16={onboard16}  等式成立={onboard16 == s16}")
if onboard16 == s16:
    raise SystemExit("ABORT: 板上 == 待烧 —— 那 §38.31 '没烧成' 那句话就是假的")

# ---------------- 产物区块 ----------------
TS = "2026-09-25 19:2x"
B3830 = f"""
### 38.30 R59（进入 2026-09-25 17:50:32，取证到 18:40:18）：pdiag 板型鉴定 + 移植进 `main/` ⇒ **全项目第一次屏亮肉眼确认**（本遍**烧了我方自己的新镜像**、屏亮肉眼确认 0 → **1 次**、未 push）

- **队列来源（用户原话，逐字）**：「原厂固件拿到了，爽了。先看看问题，试着烧录，再搞新固件。」⇒ 三件事，本节收第二、三件；第一件在 §38.29。
- **鉴定固件（`C:\\esp\\pdiag`，六版迭代）**：v1 起带三处 IDF 5.1.6 上的编译期/运行期缺陷，逐版修：① `esp_atomic.h` 在 5.1.6 **不存在**（5.2+ 才有）⇒ 改 `<stdatomic.h>`；② GPIO 22..25 不在 `SOC_GPIO_VALID_GPIO_MASK` 内，`gpio_config` 里含它们会 **assert 复位环** —— 那把载体 `{os.path.basename(LOG_LOOP)}` 现读 {lines_loop:,} 行，几乎全是重复 ROM banner；③ 断电对照臂的打印格式在 v4/v5 之间换过一次（`armB_on_fall=` → `armB_on_tr=`），同一判据在两把日志里不同形。
- **为什么 R24~R43 那几十次 360 组探针矩阵必然全空（本遍闭环）**：官方那组是 `EPD_RST=9 / DC=10 / CS=11 / SCLK=12 / MOSI=13 / BUSY=8`，而我方 R33~R57 在册的是 RST=46 / BUSY=3（`epd_driver.c:16-21`）。**官方组合从未作为一组被测过** ⇒ "扫完 360 组都没有屏应答"这句话的正确读法是"扫描器没扫到那一个格子"，不是"屏不应答"。
- **官方引脚表（本遍逐字采入，作为 `board_profile.h` 的唯一依据）**：`EPD_DC=10, CS=11, SCK=12, MOSI=13, RST=9, BUSY=8`；**`EPD_PWR=6` 且低有效**（`EPD_ON = gpio_set_level(6, 0)`）；`Audio_PWR=42`、`VBAT_PWR=17`、`BOOT=0`、`PWR_BUTTON=18`、`LED=3`；I²C `SDA=47 SCL=48`；SD `CLK=39 CMD=41 D0=40`；SPI2_HOST @40 MHz mode0 queue7、`spics_io_num=-1`、`miso=-1`；`W=H=200`、`buffer_len=5000`、LUT 159 字节。
- **移植架构（本轮被证明有效的那一条）**：板型真值**只有一处** —— `main/board_profile.h`；两只 EPD 驱动**都在** CMake 的 SRCS 里，靠整只文件 `#if BOARD_EPAPER_1IN54` 把另一只抹空，AXP 那只靠 `--gc-sections` 掉。
- **构建**：3 次调用 = 1 次失败（`esp_atomic.h`）+ 2 次成功零告警。产物链（本遍现算）：第一只 `473577b386b25d38aa6458575cb7392e` / 1,105,936 B / elf_sha16 `cb960bf791a82825`（就是它第一次让屏亮起来）；措辞修正后 `714b9b84ce05b27f1a665c0fb75ee46a` / 1,106,080 B / `{onboard16}`。
- **首次判活通过（载体 `{os.path.basename(LOG_NEW)}`，本遍现读 {lines_new} 行，逐字四行）**：
  `{q_init}`
  `{q_full}`
  `{q_blank}`
  `{q_ready}`
  同载体另外两行：`{q_mac}`，以及 `{q_sderr}` + `{q_sd}`。
- **1800 ms 这个数不是时长，是量化读数（本遍换掉的措辞）**：驱动里 BUSY 轮询是 `vTaskDelay(20)` ⇒ 只会出现 20 的整数倍。pdiag 那把细粒度尺量到 1761~1762 ms，与 1760 高 → 1780 首低 → 1800 次低算术相容，**两把尺不许互相对账**。`full update done` 那行在这把载体里同形出现 **3 次**（三次全刷），上面引的是第一行。旧载体 `{os.path.basename(LOG_OLD)}`（现读 {lines_old} 行）那把还是修正前的括号文案（`{q_old_full}`），引它等于引上一只镜像的话。
- **「待烧 = 板上」这条等式自 R53 起断了三轮，本遍第一次重新接上**：板 boot 行 `{q_elf}` 的 16 位 == `bin[176:184]` == `sha256(elf)` 的十六进制前 16 位 ⇒ 板上 = 待烧 = `{onboard16}`（该等式本遍现算成立；到 §38.31 又断，方向反过来）。
- **未兑现的那条判据（点名，不猜原因）**：pdiag 的断电对照臂印的判决三条件是 `{q_legend}`；实测那行是 `{q_offctrl}` ⇒ **B=1 < 2 且 C=1 ≠ 0，三条里两条不成立**。同一批里我方移植后的驱动却真判活了（上面那四行）⇒ 该对照臂的失败**只否证它自己的前提**（它在面板尚未 init 的时序下看 BUSY），不能反过来预测移植成败。
- **回滚三件套（本遍全在位，未动用）**：① 烧前整片快照 `C:/esp/r59z_preflash_8mb.bin`（8,388,608 B / md5 `2ffcbd228fd47eef91ff06fb2152f4fa` / 非 FF 1,838,957，其 app@0x10000 的 elf_sha16 `cbdbd1fa580fb479` = pdiag v6）；② 原厂件 `esp32s3_flash_backup_8mb.bin`（md5 `ff48b175522b9a9ab0c97d2b04187dbc`，`write_flash 0x0`）；③ 归档件 `backups/r53_20260924_083929/`（fb32168a…）与 `backups/r43_20260922_131029/`（4842a3a0…）。
- **肉眼确认（本节的标题就是它）**：2026-09-25 18:5x，用户回报屏上出现**我方固件绘制**的配网提示那一行，且补充「屏物理尺寸目测约 1.54 吋、接近正方形」⇒ ① 帧缓冲、点阵字库（CJK+ASCII 混排）、排版、**全刷**整条链第一次被肉眼证实；② 板型定案（200×200 的 1.54）与目测一致；③ 全项目"屏亮肉眼确认"累计 0 → **1 次**。同一句话里带出一个新缺陷，见 §38.31。
- **本遍仍未确立（点名，不猜）**：① 屏的确切控制器/面板型号（只有厂商工程名 `S3_ePaper_1_54`）；② 「GPIO6 = 屏电」仍只有原厂代码依据（本遍只多了间接支持：拉 0 之后判活才第一次通过）；③ 局刷路径无肉眼验证，`ENABLE_EINK_PARTIAL` 仍 0，代码在镜像里但无调用者；④ **SD 在本板挂不上**（上面那两行 `0x107` / `ESP_ERR_TIMEOUT`），所以 39/41/40 那组引脚的【未在本板实测】标记已被证伪为「至少现在这样配挂不上」，未定因（无卡 / 缺 d1..d3 / 还要 VBAT_PWR=17 或 Audio_PWR=42 / 引脚表另有出入）；⑤ 板上 NVS 区 0x9000~0x15000 仍留原厂键（`sta.apsw`/`sta.pswd`/BLE 键、cal_data），我方 NS 命名空间独立（`nvs_creds.c:22/:36`）不会误读，**本遍未擦除**；⑥ boot 日志里 `compile time Sep 19 2026` 是镜像内冻结字段（R43 已登记），不可当本遍证据。
- **明文处置**：`{os.path.basename(LOG_OLD)}` 与 `{os.path.basename(LOG_NEW)}` 两把日志都含 SoftAP 口令明文（MSG 那行），与原厂的 8 MB dump 同属**永不 stage / 永不 push / 永不删除**一类；本节只登记"哪一行有"，值由本遍的明文门现读比对，产物里一个字符都没有。
- **本遍没做（点名）**：没换电池、没上万用表、没接第二块板、没擦 NVS、没做 SD 定位、没开局刷、没把两把含明文日志复制进仓库（因此**证据只在 `C:\\esp\\` 而不在 ht305 载荷里**，这条是明文红线的直接代价，点名不掩盖）、没碰 `hardware/ht305_sync/`（SEAL 仍在 gen 24）、没新建清单代次；原厂两只 .bin 与两把含明文日志一只是不 stage、一只是不删；未 push、未 amend。
"""

B3831 = f"""
### 38.31 R60（进入 2026-09-25 18:49:00）：第一次肉眼确认**当场**翻出的版面缺陷 = 把字模的 ascent 当成了行高（本遍**改了 `main/` 源码并重建**、烧录被 COM14 缺席挡住、未 push）

- **现象（用户原话，逐字）**：「热点、密码、开IP，但是无法下滑这是很严重的问题」⇒ 屏幕在显示**但读不完**。墨水屏本身没有滚动，所以"无法下滑"只能指**内容不在屏内**，不能指交互。
- **先排掉另一层（不拿猜测当结论）**：配网页 `provision_ap.c:79-88` 的 `FORM_HTML` 全文现读，`overflow` / `100vh` / `height:100%` / `position:fixed` / `user-scalable` / `touch-action` / `preventDefault` **各 0 命中**（本遍 grep 现算）⇒ 网页侧没有任何锁滚动的东西；指向面板。
- **根因（一条注释就是证据）**：旧代 `eink_display.c:41` 原文（载体 = `backups/r59_post_20260925_184900/main/eink_display.c`，本遍现读）写着「用到的字模高度：CJK32=**34** / LATIN32≈30 / ASCII16≈16 / DIGIT96=128」。**四条里三条是对的，只有 CJK32 那一条把 ascent 当成了高。**本遍从 `ui_font.c` 逐档现读、且先证「同档内所有字模该字段单值」再取用：h 依次 CJK32={H['CJK32']} / LATIN32={H['LATIN32']} / ASCII16={H['ASCII16']} / DIGIT96={H['DIGIT96']}，ascent 依次 {ASC['CJK32']} / {ASC['LATIN32']} / {ASC['ASCII16']} / {ASC['DIGIT96']}，两列差 {H['CJK32'] - ASC['CJK32']} / {H['LATIN32'] - ASC['LATIN32']} / {H['ASCII16'] - ASC['ASCII16']} / {H['DIGIT96'] - ASC['DIGIT96']}。⇒ 只有全角那一档被压，压掉 **{h_cjk - a_cjk} px/行**。
- **演算（本遍复刻 `draw_wrapped` + `glyph_width` 的断行规则现算：空格恒 12px、半角 = 该档 `w`+1、全角 = {ADV_CJK}px；口令换成等长 `x` 占位，故宽度是**同长不同字**的估计而不是逐字实测）**：配网提示那句用 `pick_body`（半角走 LATIN32，w={W['LATIN32']}）总宽 **{w_old} px**，限宽 {lay_old['LAY_MSG_W']} ⇒ **{n_old} 行**；旧行距常数 `LAY_MSG_H={lay_old['LAY_MSG_H']}` < 字高 {h_cjk} ⇒ 相邻行各**重叠 {o_ov} px**，末行起画 y={o_lasty}、底边 {o_lastb}，其中 **{o_off} px 越出 {H_PX} 的屏底被丢**。换 `pick_compact`（半角降到 ASCII16，w={W['ASCII16']}）后总宽 **{w_new} px**（限宽同为 {lay_new['LAY_MSG_W']}）⇒ **{n_new} 行**，行距取 {lay_new['LAY_MSG_H']}，末行底边 {n_lastb} ⇒ 越屏底 {n_off}px、重叠 {n_ov}px。**"底边"本遍一律取含端点行号**（末行起点 + 字高 − 1）；`eink_display.c` 里 `pick_compact` 上方那条注释写的是不含端点的 185，同一件事的两种数法，不是分歧。
- **同根因的第二、第三处（本遍一并点名，一并改常数）**：STATUS 页两行起点 {lay_old['LAY_STATUS_L1']}/{lay_old['LAY_STATUS_L2']} ⇒ 间距 {st_gap_old} < {h_cjk} ⇒ 全角两行重叠 **{st_ov_old} px**；CLOCK 页 `DATE={lay_old['LAY_CLOCK_DATE']}` 底边 {ck_date_b_old} 而 `TITLE={lay_old['LAY_CLOCK_TITLE']}` ⇒ 重叠 **{ck_ov_old} px**。新代现读：STATUS 间距 {st_gap_new}、CLOCK TITLE 与 DATE 底边之间余量 {ck_gap_new} ⇒ 两处都由负转正。三处都来自同一列常数的同一算法错误。
- **修复四条（前两条是消灭这一类，后两条是消灭这一个）**：① `draw_wrapped` 的行距改为**下限语义** —— 逐行取「本行实际用到的字模最大高」与传入 `line_h` 的较大者，版面常数写小也压不到字；② 消息页改走新增的 `pick_compact`（中文 CJK32 不变、半角 ASCII16），并给 `draw_wrapped` 装上「整行画不完」的 WARN，静默丢字改为日志可见；③ 1.54 那一列常数按真实字高重排（STATUS {lay_new['LAY_STATUS_L1']}/{lay_new['LAY_STATUS_L2']}/{lay_new['LAY_STATUS_L3']}、CLOCK {lay_new['LAY_CLOCK_BIG']}/{lay_new['LAY_CLOCK_DATE']}/{lay_new['LAY_CLOCK_TITLE']}、MSG y={lay_new['LAY_MSG_Y']} 行距 {lay_new['LAY_MSG_H']}）；④ 版面块那段"字模高度"注释改为现读值并写清 ascent≠行高。
- **构建（本遍现算）**：`{os.path.basename(BIN)}` md5 **{md5_new}** / {size_new:,} B / elf_sha16 **{s16}**；等式 `bin[176:184] == sha256(elf)[:16]` 本遍现算成立。
- **烧录没做成（现场态，本遍现跑两次）**：`C:/esp/r60_flash.ps1` 的 MAC 守卫生 `read_mac` 报 `Could not open COM14 ... FileNotFoundError(2)`（`MACLEN=258` ⇒ 那次读回的是错误文本而不是 MAC），随后 `Get-PnpDevice -PresentOnly` 现读全树**没有任何 ESP32-S3 的 USB 实例**（只剩 4 只蓝牙 SPP）。⇒ **屏上此刻仍是 §38.30 那只旧镜像画的重叠画面，本轮修好的镜像未进板**；等式就地再断一次且方向是"待烧超前"：待烧 `{md5_new[:8]}…`（elf16 `{s16}`）≠ 板上 `714b9b84…`（elf16 `{onboard16}`）—— 本遍现算两者不等，故这句可写。恢复按代价排：冷插 USB（唯一实测可用）> 长按 PWR（未验证、会换基线）。
- **顺带量到的一条产品级事实（点名，本遍未改）**：配网门户只活 **1800 s**（`main.c:295` `provision_ap_wait_done(1800)`），超时即 `esp_deep_sleep_start()` 且下次唤醒在 **6 h** 之后（`main.c:313`）。叠加本轮那条版面缺陷 ⇒ 现场拿不到串口的人，只有一次"读得清屏 + 30 分钟内配完"的机会；屏读不清就等 6 小时。**这条与上面那四条修复谁先做，属产品裁决，本遍不擅自扩大改动范围。**
- **本遍没做（点名）**：没重烧（COM14 不在）、没肉眼复核修复后的画面（0 次，需板子回来）、没动 `power_policy.c` 的 900 s 空闲深睡、没开局刷、没擦 NVS、没碰 `hardware/ht305_sync/`、没新建清单代次；未 push、未 amend。**演算与真机之间还差一次同案对照**：上面那 6→{n_new} 行是本遍算出来的，屏上实际是不是 {n_new} 行，只有重烧后肉眼看一次才算闭环。
"""

FE_TAIL_OLD = rd(FREQ)

BFE = """
> **【__TS__ 落地｜R59+R60 第十一批 __N__ 条】** 追加之前现读磁盘：`^[错误类型]` 台账 = __N0__ 条、`wc -l` = __L0__ 行；回填后的终值（同一把尺在最终字节串上现数）= __N__ 条 / __L__ 行。落地器 = `hardware/r60_land.py`（唯一执行者）。

[错误类型] **把点阵字模的 `ascent` 当成了行高**（R60：版面注释写「CJK32=34」，而 34 是 `UIF_CJK32.ascent`，`uif_glyph_t.h` 实为 43；同批四条里其余三条恰好都对，所以没人去核这一条）。
→ 症状：文字"挤在一起/下面看不全"，而墨水屏没有滚动 ⇒ 现场把它读成"这块屏不好用"，而不是"行数超了"。
→ 正确做法：①行高取 `uif_glyph_t.h`（同档内等高，可拿该档第一只字模），**ascent 只用于基线对齐**；②排版类常数要么由代码现算、要么加一道"行距 < 字高就 ABORT"的断言；③**逐档对 `h` 做单值校验再这么取**（本遍落地器 `glyph_field()` 就是这么装的），不要假设。

[错误类型] **版面常数在没有任何肉眼样本的情况下被当成了已校准事实**（1.54 那一列从写下到第一次屏亮隔了整批 R33~R59，期间"屏没亮"这条前提把三处重叠全盖住了）。
→ 为什么危险：排错的东西不会因为"还没看到"而消失，只会在第一次看到时一次爆发三处。
→ 正确做法：新硬件分支的版面常数一律标【未肉眼校准】，并把"第一次肉眼确认"当成一条独立任务排进队列，不许藏在"点屏成功"之后。

[错误类型] **`draw_wrapped` 这类"传进去的高度参数"语义不明**（历史上同一位置有人传框高、有人传行距；R60 的实伤是框高 36 被当行距用）。
→ 正确做法：这类参数必须在函数名或注释里写死语义（本遍定为**下限**），并在函数内钳到实际字模高；同时给"画不完"打 WARN——静默截断等于把缺陷交给用户去发现。

[错误类型] **IDF 小版本间的头文件差异照新文档写**：`esp_atomic.h` 在 **5.1.6 不存在**（5.2+ 才有），照 5.2 的写法直接 `No such file or directory`。
→ 正确做法：跨小版本搬代码时，先 `ls $IDF/components/*/include | grep` 现读该头是否存在；同一仓库里既有写法（`<stdatomic.h>` 放在 `FreeRTOS.h` 之前）就是现成的证据源。

[错误类型] **Edit 的 `old_string` 只覆盖多行语句的第一行** ⇒ 未覆盖的续行与新串里带的续行并存，产出一模一样的重复行（R59 实伤：`heap_caps_get_free_size(...));` 出现两遍，语法会炸，靠 `git diff` 才抓到）。
→ 正确做法：多行语句作锚点必须**整只语句进 `old_string`**；改完 C 文件先 `git diff` 读差异，不看工具回执。

[错误类型] **`read_flash` 在高波特率下"Corrupt data, expected 0x1000 bytes but received 0xbbd/0xfd0"**（921600 与 460800 各红一次，230400 一次绿）。
→ 正确做法：整片快照这类**读**操作默认降速跑；红两次以上先换波特率再谈"这块 flash 读不出来"，更不许拿"读不出来"当回滚件不存在的结论。

[错误类型] **对照臂判据未兑现时被反向使用**（pdiag 的 `B>=2 且 C==0 且 A==0` 实测 `armB_on_tr=1 armC_off_tr=1`，两条不成立；而同一批移植后的驱动真判活了）。
→ 正确做法：一条判据只能裁决**它自己那一路前提**；它不成立时先问"这条臂的前置时序对不对"，不许升级成"移植会失败"的预测。

[错误类型] **引"上一把日志的某一行"时没先确认它是哪只镜像打印的**（`r59z_..._183248` 那把的括号文案在下一只镜像里已被改掉，`r59z_..._184018` 才是板上这只现在会打的话）。
→ 正确做法：引用串口证据必须带**载体文件名 + 该镜像的 elf_sha16**，两者对不上就当新证据重跑。

[错误类型] **用户报"很严重的问题"时不指明层次，直接跳到最顺手的解释**（R60 的第一猜测是网页，但网页侧现读 `FORM_HTML` 无任何锁滚动样式；正确路径是把**面板/网页两层各排查一遍**再定位）。
→ 正确做法：症状跨层时，先对每一层做一次**便宜的排除取证**（grep / 演算），把出局的那层和理由一起写下来。

[错误类型] **落地器自己把"要登记的数"写死在字面量里**（本文件第一版把 CJK 行高写成 43、把 `grep_line` 的命中数写成 `want=99`、把 `full update done` 当 1 行 —— 三处都会在真机上静默 ABORT 或静默放行假数）。
→ 正确做法：产物里每一个数字都要能指回"哪只载体、哪一次现读"；计数用 `count_is()` 现核，常数从两代源码快照各读一份，判据反向装门（新版面若不达标就 ABORT，而不是写一句"应该好了"）。
"""

BFE = BFE.replace("__TS__", TS)

DEV_NEW = f"""

## 第三十一批：**R59 移植首刷 = 全项目第一次屏亮肉眼确认 + R60 版面缺陷（ascent 当行高）修复**（进入 2026-09-25 17:50:32；取证 18:32:48 / 18:40:18；肉眼确认 18:5x；R60 落地 18:49:00 起）

- 详情落纸：排查记录 **§38.30**（pdiag 六版 + 360 组为何必空 + 官方引脚表 + 移植 + 判据四行 + 1800ms 量化口径 + 未兑现的 B>=2 + 回滚三件套 + 肉眼确认）与 **§38.31**（版面缺陷：ascent 当行高 ⇒ 三处重叠 + 末行 {o_off}px 越屏底；四条修复；重建指纹；烧录被 COM14 缺席挡住）。
- 现场态：待烧 md5 `{md5_new}` / {size_new:,} B / elf16 `{s16}` ≠ 板上 `{onboard16}`（714b9b84…）⇒ 「待烧 = 板上」第三次断裂，方向 = 待烧超前。
- 屏亮**肉眼确认累计 1 次**（内容 = 我方绘制的配网提示行；同一次确认带出"读不完"缺陷）。本遍**未播提示音**，因为交付未完成（新镜像没进板、修复画面没复核）。
- 备份：`backups/r59_post_20260925_184900/` 与 `hardware/zizhao-esp32s3/backups/r59_post_20260925_184900/` 双根各 **35 只**（`main/` 30 + `.bin` + `.elf` + `.map`），两根内 `zizhao_esp32s3.bin` md5 现读 **714b9b84ce05b27f1a665c0fb75ee46a**（= 板上那只，不是本轮新构建的 {md5_new[:8]} —— 备份做的是"已进板并被肉眼看过"那一代，新那一代等重烧后再补一根）。旧代版面常数的取证源就是这一根里的 `main/eink_display.c`。
"""

DONE_NEW = f"""

## R59 + R60 批（2026-09-25）

- [x] **R59-1..R59-7**：pdiag 板型鉴定固件 v1..v6（修 `esp_atomic.h` 缺失、GPIO 22..25 assert 复位环、断电对照臂格式）→ 板型定案 `S3_ePaper_1_54`（{W_PX}×{H_PX}，无 AXP）→ 移植进 `main/`（`board_profile.h` 单一真值 + 整只文件 `#if` 互斥 + `--gc-sections`）→ 零告警构建 → 烧 COM14 → **首次判活通过**（`{q_init}` + 三次全刷 + `panel blanked`），载体 `C:/esp/{os.path.basename(LOG_OLD)}`（{lines_old} 行）与 `C:/esp/{os.path.basename(LOG_NEW)}`（{lines_new} 行）（两把含明文口令，永不 stage）。
- [x] **R59 口径修正（进镜像）**：`full update done in 1800 ms` 的括号从"实测 1761~1762 ms"换成"读数按 20ms 轮询量化、两把尺不得互相对账"；`probe_attempt()` 第三条出口的屏电泄漏（命令流不完整时不断 GPIO6）改为"先交还引脚、后断电"（`epd_panel_1in54.c` 里 `epd_rail_off();` 现读 7 处）。
- [x] **里程碑：屏亮肉眼确认 0 → 1 次**（2026-09-25 18:5x，屏上是我方绘制的配网提示行；同一次回答确认屏目测约 1.54 吋，与定案一致）。
- [x] **R60-1 版面缺陷定位与修复**：根因 = 把 `ascent`({a_cjk}) 当字模高（实为 {h_cjk}）⇒ 消息页 {n_old} 行重叠 {o_ov}px/行、末行 {o_off}px 越屏底；STATUS 与 CLOCK 另有两处同根因重叠（{st_ov_old}px / {ck_ov_old}px）。修：`draw_wrapped` 行距钳到本行真实字模高 + 新增 `pick_compact` + 1.54 列常数按 {h_cjk} 重排 + "画不完"打 WARN。演算新版面 {n_new} 行 / 底边 {n_lastb} ≤ {H_PX}。重建 `{md5_new}` / {size_new:,} B / elf16 `{s16}`。
- [x] **移植后双根备份**：`backups/r59_post_20260925_184900/` 与 `hardware/zizhao-esp32s3/backups/r59_post_20260925_184900/`，各 35 只，两根 bin md5 现读 714b9b84…。
- [ ] **R60-2 重烧 + 肉眼复核**（阻塞：COM14 从 USB 总线消失，`read_mac` FileNotFoundError + `Get-PnpDevice` 无 ESP32-S3 实例 ⇒ 需冷插 USB）。
- [ ] R60-3 提交轮 #9（明文门 + 逐只点名，DROP 含明文两把日志与原厂两只 .bin）+ ht305 第 14 代同步 + 项目记忆换代。
"""

check_clean("B3830", B3830)
check_clean("B3831", B3831)
check_clean("DEV_NEW", DEV_NEW)
check_clean("DONE_NEW", DONE_NEW)
for name, blk in (("B3830", B3830), ("B3831", B3831), ("DEV", DEV_NEW), ("DONE", DONE_NEW)):
    if "__" in blk:
        raise SystemExit(f"ABORT: {name} 里残留双下划线占位符")

# ---------------- 幂等落盘：每一步都先算出"目标字节串"，一致就 SKIP，不一致才写 ----------------
# 为什么必须可重入：本落地器第三遍跑到 FreqErr 回填门时 ABORT 了，而那时 REC 与 FreqErr
# 已经写下去 —— 若"已存在"一律当事故，这只文件就永远停在半截状态，重跑反而更危险。
def append_blk(path, marker, blk, probes, label):
    cur = rd(path)
    tgt = cur.rstrip("\n") + "\n\n" + blk.lstrip("\n").rstrip("\n") + "\n"
    if marker in cur:
        region = cur[cur.index(marker):]
        miss = [s for s in probes if s not in region]
        if miss:
            raise SystemExit(f"ABORT: {label} 该段已在册但关键数对不上，缺 {miss}")
        print(f"SKIP {label} 已在册且关键数与本轮现算一致")
        return False
    if any(s in cur for s in probes):
        raise SystemExit(f"ABORT: {label} 里有半截痕迹（marker 不在但正文关键数在）")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(tgt)
    return True


def fix_blank_before_headings(path, pat):
    """节间空行：标题上一行必须是空行。R55 已登记过"纯插入式落地器不验节间空行"这一族，
    本落地器第三遍就是那样把 §38.30/§38.31 直接贴在上一段正文后面的，所以这里补一道归一化。"""
    lines = rd(path).split("\n")
    out, fixed = [], 0
    for ln in lines:
        if re.match(pat, ln) and out and out[-1].strip():
            out.append("")
            fixed += 1
        out.append(ln)
    if fixed:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))
    after = rd(path).split("\n")
    left = [i + 1 for i in range(1, len(after)) if re.match(pat, after[i]) and after[i - 1].strip()]
    if left:
        raise SystemExit(f"ABORT: {os.path.basename(path)} 仍有标题贴着上一段正文，行号 {left}")
    print(f"SPACING {os.path.basename(path)} 补空行 {fixed} 处，复查 0 残留")
    return fixed


BANNER = "R59+R60 第十一批"
SNAP = os.path.join(os.environ.get("TEMP", r"C:\Users\david\AppData\Local\Temp"), "r60_pre_FreqErr.md")
n_add = len(re.findall(r"^\[错误类型\]", BFE, re.M))
if n_add != 10:
    raise SystemExit(f"ABORT: 本批 FreqErr 条目数 {n_add} != 10")

fe_txt = rd(FREQ)
bn = [i for i, ln in enumerate(fe_txt.split("\n")) if BANNER in ln]
if len(bn) > 1:
    raise SystemExit(f"ABORT: FreqErr 台账行出现 {len(bn)} 次")
if bn:
    base = "\n".join(fe_txt.split("\n")[:bn[0]]).rstrip("\n") + "\n"
else:
    base = fe_txt
if base != FE_TAIL_OLD and not bn:
    raise SystemExit("ABORT: FreqErr 在勘察与落笔之间变了")
n0 = len(re.findall(r"^\[错误类型\]", base, re.M))
l0 = base.count("\n")
if bn and os.path.isfile(SNAP) and hashlib.md5(rb(SNAP)).hexdigest() != hashlib.md5(base.encode()).hexdigest():
    raise SystemExit("ABORT: 从在册文件反推的 base != 落笔前快照，台账前两数不可信")
fe_tgt = base.rstrip("\n") + "\n\n" + BFE.lstrip("\n").rstrip("\n") + "\n"
n_final = len(re.findall(r"^\[错误类型\]", fe_tgt, re.M))
l_final = fe_tgt.count("\n")
if n_final != n0 + n_add:
    raise SystemExit(f"ABORT: 台账数不闭合 n0={n0} +{n_add} != {n_final}")
fe_filled = (fe_tgt.replace("__N__ 条", f"{n_final} 条")
                   .replace("__N0__", str(n0))
                   .replace("__L0__", str(l0))
                   .replace("__L__ 行", f"{l_final} 行"))
left = sorted(set(re.findall(r"__(?:N|N0|L0|L)__", fe_filled)))
if left:
    raise SystemExit("ABORT: FreqErr 回填后仍有占位符未解析: " + repr(left))
print(f"GATE2 FreqErr base n0={n0} l0={l0} -> 终值 n={n_final} l={l_final} 本批新增 {n_add} 条")
if fe_filled != fe_txt:
    with open(FREQ, "w", encoding="utf-8", newline="\n") as f:
        f.write(fe_filled)
    print("WROTE FREQ")
else:
    print("SKIP FREQ 已是目标字节串")

rec_written = append_blk(REC, "### 38.30", B3830 + "\n\n" + B3831,
                         ["### 38.31", md5_new, f"**{n_old} 行**", f"**{n_new} 行**"], "REC")
append_blk(DONE, "## R59 + R60 批", DONE_NEW, ["R60-2 重烧 + 肉眼复核"], "DONE")
append_blk(DEV, "## 第三十一批", DEV_NEW, ["旧代版面常数的取证源"], "DEV")
fix_blank_before_headings(REC, r"^### 38\.3[01] ")
fix_blank_before_headings(DONE, r"^## R59 \+ R60 批$")
fix_blank_before_headings(DEV, r"^## 第三十一批：")
fix_blank_before_headings(FREQ, "^> \\*\\*【" + re.escape(TS) + " 落地｜R59\\+R60 第十一批")

# ---------------- 落盘后独立回读 ----------------
for p, needles in ((REC, ["### 38.30", "### 38.31", '屏亮肉眼确认"累计 0 → **1 次**']),
                   (FREQ, ["ascent` 当成了行高"]),
                   (DONE, ["屏亮肉眼确认 0 → 1 次"]),
                   (DEV, ["第三十一批"])):
    tt = rd(p)
    for nd in needles:
        if nd not in tt:
            raise SystemExit(f"ABORT: 回读缺针 {p} :: {nd}")
disk2 = rd(FREQ)
n2 = len(re.findall(r"^\[错误类型\]", disk2, re.M))
l2 = disk2.count("\n")
bl = [ln for ln in disk2.splitlines() if BANNER in ln]
if len(bl) != 1:
    raise SystemExit(f"ABORT: FreqErr 台账行应为 1，现读 {len(bl)}")
g = re.search(r"第十一批 (\d+) 条】.*?台账 = (\d+) 条、`wc -l` = (\d+) 行.*?= (\d+) 条 / (\d+) 行", bl[0])
if not g:
    raise SystemExit("ABORT: FreqErr 台账行格式解析不出五个数: " + bl[0][:120])
if (int(g.group(1)), int(g.group(4))) != (n2, n2) or int(g.group(2)) != n0 or int(g.group(3)) != l0 or int(g.group(5)) != l2:
    raise SystemExit(f"ABORT: FreqErr 回填值与最终字节串不符 登记={g.groups()} 实测 n={n2} l={l2} n0={n0} l0={l0}")
print("READBACK OK  REC/FREQ/DONE/DEV 四只全部有针 + FreqErr 五数自核 OK")
print(f"GATE3 FreqErr n={n2} lines={l2}")
print(f"LINES REC={rd(REC).count(chr(10))} FREQ={l2} DONE={rd(DONE).count(chr(10))} DEV={rd(DEV).count(chr(10))} REC_WROTE_THIS_RUN={rec_written}")
print("SEAL 本遍未新建清单代次、未碰 hardware/ht305_sync/ ；未 push、未 amend")
raise SystemExit(0)
