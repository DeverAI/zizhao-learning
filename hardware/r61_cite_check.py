#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§38.32 的落地门：把那一节里**每一条真机读数**拿去和它的载体逐字比对，全中才追加到排查记录。

为什么要有这只（本遍就是它拦下来的）：写文档时最容易犯的_not_抄错、而是**在没有载体的时候
写下一个"真机读数"**。所以这里不做人眼复核，逐条 assert：
  - 引文级：本节引用的每条 msg paging / PREDICT / MATCH / browse / VERDICT 行，必须逐字出现在
    仓库内取证件里（`r61_evidence.py` 的产物，不含明文）；
  - 复算级：翻页间隔、六只镜像的 ELF16、出厂 bin 的 md5 与尺寸、六只源码的 md5，本脚本**现算**
    一遍再和本节文本比，本节写的是算出来的数、不是抄来的数；
  - 结构级：写盘前后各查一次 —— 只允许在 EOF 追加，原有字节必须一字不动，且 `### 38.32` 全文只 1 处；
  - 明文级：本节与两只载体都不得含 `PROV_PASS` 的值（值运行时现读，本脚本也不打印它）。

输入件缺失一律 ABORT，不静默通过：原始串口日志带口令，永远只在本机 `C:\\esp\\` 一类目录里，
换机器跑不动这只门是**预期行为**（静默跳过 = 假装验过）。

用法：python r61_cite_check.py <待追加的那一节.md> [构建目录，默认 C:\\esp]
"""
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "zizhao-esp32s3", "main")
REC = os.path.join(HERE, "20260919_墨水屏点屏排查记录.md")
CDIAG = os.path.join(HERE, "r61_evidence_diag_full_20260926_110814.txt")
CSHIP = os.path.join(HERE, "r61_evidence_ship_full_20260926_111313.txt")
LOGS = ["r61z_20260926_103120_run.log", "r61z_20260926_103732_run.log",
        "r61z_20260926_104515_run.log", "r61z_20260926_105748_run.log",
        "r61z_20260926_110814_run.log", "r61z_20260926_111313_run.log"]
SRCS = ["eink_display.c", "main.c", "provision_ap.c", "buttons.c", "buttons.h", "eink_display.h"]

fails = []


def chk(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)


def rd(p, text=False):
    b = io.open(p, "rb").read()
    return b.decode("utf-8", "replace") if text else b


def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", s)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    sec_path = sys.argv[1]
    esp = sys.argv[2] if len(sys.argv) > 2 else r"C:\esp"

    # --- 前置：所有输入件必须在位（缺件 = ABORT，不是"跳过这项检查"） -----------
    need = {"section": sec_path, "record": REC, "carrier_diag": CDIAG, "carrier_ship": CSHIP,
            "bin": os.path.join(esp, "zproj", "build", "zizhao_esp32s3.bin"),
            "elf": os.path.join(esp, "zproj", "build", "zizhao_esp32s3.elf")}
    for f in LOGS:
        need["log_" + f] = os.path.join(esp, f)
    for f in SRCS + ["ui_font.c"]:
        need["src_" + f] = os.path.join(MAIN, f)
    missing = sorted(k for k, v in need.items() if not os.path.isfile(v))
    if missing:
        print("ABORT: 输入件缺失 %d 只（这只门不许在缺件时静默通过）" % len(missing))
        for k in missing:
            print("  - %s -> %s" % (k, need[k]))
        return 1
    print("INPUTS_PRESENT=%d" % len(need))

    sec = rd(sec_path, True)
    diag = rd(CDIAG, True)
    ship = rd(CSHIP, True)
    both = diag + ship

    # --- 1. 哨兵：本节不得残留占位符 -------------------------------------------
    for tok in ["%s", "%d", "XXX", "PLACEHOLDER", "TBD", "???", "{k}", "{N}"]:
        chk(tok not in sec, "sentinel_absent:%r" % tok)

    # --- 2. 引文级：本节引用的每条读数都要在载体里逐字命中 ---------------------
    quotes = [
        "bytes=63 sum_adv=62 lines=4 pages=1 clipped=0 req_page=0 shown_page=0 "
        "map=[0:0+6/7B 1:0+50/17B 2:0+94/18B 3:0+138/18B",
        "bytes=141 sum_adv=141 lines=10 pages=3",
        "4:1+6/11B", "8:2+6/11B",
        "PREDICT bytes/sum_adv/lines/pages = ('63', '62', '4', '1') map=4",
        "PREDICT bytes/sum_adv/lines/pages = ('141', '141', '10', '3') map=10",
        "MATCH = True（1 条真机行全部命中预测）",
        "MATCH = True（4 条真机行全部命中预测）",
        "MATCH = False（0 条真机行全部命中预测）",
        "req_page 取值 = []", "shown_page 取值 = []",
        "BROWSE_HITS = 5", "BROWSE_HITS = 0",
        "VERDICT: RING_CLOSED (末态 msg_page=0，一圈 5 步)",
        "bytes=15 sum_adv=15 lines=1 pages=1",
        "PAGING_TOTAL=6 归类=1+4 其余=1 配平=True",
        "PAGING_TOTAL=2 归类=1+0 其余=1 配平=True",
    ]
    for q in quotes:
        chk(q in both, "quote_in_carrier:%s" % q[:46])

    # --- 3. 复算级：翻页间隔 / ELF16 / bin / 源码 md5 --------------------------
    dt = strip_ansi(rd(os.path.join(esp, LOGS[4]), True))
    st = strip_ansi(rd(os.path.join(esp, LOGS[5]), True))

    def ts(t):
        return [int(m) for m in re.findall(r"\((\d+)\) eink: msg paging", t)]

    td, tsv = ts(dt), ts(st)
    diffs = [td[i + 1] - td[i] for i in range(len(td) - 1)]
    print("RECOMPUTED diag_ts=%s diffs=%s ship_ts=%s" % (td, diffs, tsv))
    chk(len(td) == 6 and dt.count("msg paging: bytes=141") == 4, "diag_6_paging_4_selftest")
    chk(len(tsv) == 2, "ship_2_paging")
    for d in (2082, 2065, 2096, 2226):
        chk(d in diffs, "interval_in_log:%d" % d)
    chk(6231 in diffs, "mixed_interval_6231_present")
    chk(tsv[1] - tsv[0] == 2223, "ship_interval_2223")
    chk("2082 / 2065 / 2096 / 2226" in sec, "section_lists_4_intervals")

    elf16 = []
    for f in LOGS:
        m = re.search(r"ELF file SHA256:\s+([0-9a-f]{16})", strip_ansi(rd(os.path.join(esp, f), True)))
        elf16.append(m.group(1) if m else "MISSING")
    print("RECOMPUTED elf16=%s" % elf16)
    chk(len(set(elf16)) == 6 and "MISSING" not in elf16, "six_distinct_images")
    for v in elf16:
        chk(v in sec, "elf16_in_section:%s" % v)

    b = rd(need["bin"])
    e = rd(need["elf"])
    mdbin, shaelf = hashlib.md5(b).hexdigest(), hashlib.sha256(e).hexdigest()
    print("RECOMPUTED bin_md5=%s size=%d elf16=%s" % (mdbin, len(b), shaelf[:16]))
    chk(mdbin in sec, "bin_md5_in_section")
    chk("{:,}".format(len(b)) in sec, "bin_size_in_section")
    chk(b[176:184].hex() == shaelf[:16], "identity_eq_bin176_184")
    chk(b[176:208].hex() == shaelf, "identity_eq_bin176_208")
    chk(shaelf[:16] == elf16[-1], "shipping_bin_eq_last_log")

    for f in SRCS:
        a = hashlib.md5(rd(os.path.join(MAIN, f))).hexdigest()
        cp = os.path.join(esp, "zproj", "main", f)
        chk(os.path.isfile(cp) and hashlib.md5(rd(cp)).hexdigest() == a, "repo_eq_build_tree:%s" % f)
        chk(a in sec, "src_md5_in_section:%s" % f)

    esrc = rd(os.path.join(MAIN, "eink_display.c"), True)
    chk("#define MSG_CAP 256" in esrc and "#define WRAP_CAP 40" in esrc, "wrap_constants_as_quoted")
    chk("ENABLE_EINK_PARTIAL" in esrc, "partial_macro_present")
    mlines = rd(os.path.join(MAIN, "main.c"), True).splitlines()
    chk("#define EINK_PAGE_SELFTEST 0" in "\n".join(mlines), "selftest_macro_off_now")
    chk("请现场配网" in mlines[383], "main_c_384_is_the_15B_msg")
    palines = rd(os.path.join(MAIN, "provision_ap.c"), True).splitlines()
    chk("buttons_poll() != BTN_NONE" in palines[231], "provision_ap_232_key_poll")
    chk(rd(os.path.join(MAIN, "ui_font.c"), True).count("const uif_glyph_t CJK32_g") == 193, "cjk32_193")

    for p in (CDIAG, CSHIP):
        n = os.path.basename(p)
        chk(n in sec, "carrier_named_in_section:%s" % n)
        chk("{:,}".format(os.path.getsize(p)) in sec, "carrier_size_in_section:%s" % n)

    # --- 4. 明文级：本节与载体都不许含口令值（值现读，不打印） -----------------
    m = re.search(r'#define\s+PROV_PASS\w*\s+"([^"]*)"', rd(os.path.join(MAIN, "provision_ap.c"), True))
    chk(bool(m), "PROV_PASS_macro_readable")
    if m and m.group(1):
        chk(m.group(1) not in sec, "section_has_NO_plaintext")
        chk(m.group(1) not in both, "carriers_have_NO_plaintext")

    # --- 5. 结构级：只在 EOF 追加一次，原有字节不动 ---------------------------
    rec = rd(REC)
    chk(b"### 38.32" not in rec, "record_lacks_38_32_before")
    if fails:
        print("ABORT: %d gate(s) failed -> 不写盘" % len(fails))
        for x in fails:
            print("  - " + x)
        return 1

    secb = rd(sec_path)
    before = rec.count(b"\n")
    io.open(REC + ".tmp", "wb").write(rec + secb)
    os.replace(REC + ".tmp", REC)

    new = rd(REC)
    txt = new.decode("utf-8")
    after = new.count(b"\n")
    print("APPENDED lines %d -> %d (+%d) bytes %d -> %d (+%d)"
          % (before, after, after - before, len(rec), len(new), len(new) - len(rec)))
    print("HEADINGS_38_x=%d  HAS_38_31=%s  COUNT_38_32=%d"
          % (len(re.findall(r"^### 38\.\d+", txt, re.M)), "### 38.31 R60" in txt, txt.count("### 38.32")))
    chk(new.startswith(rec), "prefix_bytes_untouched")
    chk(after - before == secb.count(b"\n"), "line_delta_equals_section")
    chk(txt.count("### 38.32") == 1 and "### 38.31 R60" in txt, "single_new_heading_old_intact")
    if fails:
        print("POSTCHECK_FAILED=%s" % fails)
        return 2
    print("VERDICT=LANDED rc=0")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
