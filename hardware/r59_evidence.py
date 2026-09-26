#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 R59 那批板型鉴定串口日志转成**可入库**的取证件（同族件见 r61_evidence.py）。

为什么要这只：排查记录 §38.30 那句"在机的板是 S3_ePaper_1_54、整板没有 panel PMIC"
是本项目影响最大的一条改判，而它的原始日志 `C:/esp/r59*_run.log` 里带 SoftAP 明文口令，
永远不能进仓库 ⇒ 没有落库载体 = 那句话只有转抄、没有证据。

口径（都是本脚本现跑现数，不手抄）：
  · 口令的值运行时从 provision_ap.c 现读，逐处替换成 [REDACTED]，对**输出**再断言一次不含明文；
  · 每一类被认领的行都同时打印"认领了多少 / 该类总共有多少"——只打印被认领的那些
    是 FreqErr 登记过的半截取证形态；
  · 判据行按消息形状整类抽取，不做人工挑选。

用法：python r59_evidence.py <输出取证件>
输入日志名单在下面 FILES 里（写死盘上路径；不存在即 ABORT，不静默少一类）。
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "zizhao-esp32s3", "main")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# 输入名单（版本自称取自各日志里 `PDIAG2-BEGIN board-census gen=` 那一行，见本件正文）
# 盘上另两只不进本件：r59_（v1，只有 EPDPROBE，被 v3 的矩阵取代）、r59b_（v2，439 次复位的
# assert 环遍，3.7 MB，本件的判据不依赖它）。
FILES = [
    ("r59c_20260925_171315_run.log", "360 组 MAP 矩阵（跑完一整轮）"),
    ("r59d_20260925_173434_run.log", "断电/供电对照臂第一版（OFF-CTRL 门 + OFF-STEP）"),
    ("r59e_20260925_173940_run.log", "对照臂第二版（OFF-WATCH 双臂窗口）"),
    ("r59f_20260925_174338_run.log", "对照臂第三版（arm-B-power-on 那一格 tr=1 在这里）"),
    ("r59z_20260925_183248_run.log", "移植后首刷（epd154 init done + 全刷 + panel blanked）"),
    ("r59z_20260925_184018_run.log", "移植后第二刷（同一只镜像）"),
]

# 每只日志认领哪些消息（子串匹配，整类抽，不人工挑行）
CLASSES = [
    ("PDIAG2-BEGIN", "本遍版本自称（gen= 后面那串）"),
    ("PDIAG-BEGIN",  "本遍版本自称（v1 写法）"),
    ("MAP",          "矩阵行（en/clk/cs/dc/mosi/rst + tr + 首变毫秒）"),
    ("OFF-STEP",     "对照臂的每一步（busy_start/busy_end/fall/ms）"),
    ("OFF-WATCH",    "对照臂窗口（arm-A 断电 / arm-B 供电，读数 tr）"),
    ("OFF-CTRL",     "对照臂门（off_arm_tr / on_arm_tr 判读句）"),
    ("CID",          "读寄存器对照（总线对/地址/probe 结果）"),
    ("CSCAN",        "总线扫描（ack/nack_fail/timeout 分类）"),
    ("PAD",          "对上/对下拉读脚"),
    ("EPDPROBE",     "屏判活探针行"),
]
RUNTIME = ("epd154:", "paging", "panel blanked", "full update", "init done",
           "ELF file SHA256", "Project name")


def pass_value():
    src = io.open(os.path.join(MAIN, "provision_ap.c"), encoding="utf-8").read()
    m = re.search(r"#define\s+PROV_PASS\s+\"([^\"]+)\"", src)
    if not m:
        raise SystemExit("ABORT: provision_ap.c 里找不到 PROV_PASS 宏")
    return m.group(1)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = sys.argv[1]
    if os.path.exists(out):
        raise SystemExit("ABORT: 输出件已存在，不覆盖（%s）" % out)
    pwd = pass_value()
    if len(pwd) < 4:
        raise SystemExit("ABORT: PROV_PASS 宏的值短得可疑（%d 字符），不做替换" % len(pwd))
    src_hits = 0

    body = ["R59 板型鉴定取证（本件由 hardware/r59_evidence.py 生成）",
            "输入日志在 C:\\esp\\，全部含明文口令 ⇒ 原始日志永不入库；本件运行时现读口令并逐处替换",
            "脱敏口径：只替换口令的值本身，其余行按消息形状整类认领，不人工挑行", ""]
    tally = []
    for name, label in FILES:
        raw = os.path.join("C:\\esp", name)
        if not os.path.exists(raw):
            raise SystemExit("ABORT: 输入日志不存在 %s" % raw)
        text = ANSI.sub("", io.open(raw, encoding="utf-8", errors="replace").read())
        src_hits += text.count(pwd)
        text = text.replace(pwd, "[REDACTED]")          # 逐处替换，末尾再断言一次不含明文
        lines = text.splitlines()
        body.append("== %s ｜ %s ｜ 原文件 %d B / %d 行 ==" % (name, label, os.path.getsize(raw), len(lines)))
        claimed = set()
        for token, desc in CLASSES:
            hit = [(i, l) for i, l in enumerate(lines) if token in l and i not in claimed]
            if not hit:
                continue
            body.append("--- %s（%s）认领 %d 条 ---" % (token, desc, len(hit)))
            body += [l.strip() for i, l in hit]
            claimed.update(i for i, l in hit)
        run = [(i, l) for i, l in enumerate(lines)
               if i not in claimed and any(k in l for k in RUNTIME)]
        if run:
            body.append("--- 运行期判据行（init/全刷/blanked/boot 指纹）认领 %d 条 ---" % len(run))
            body += [l.strip() for i, l in run]
            claimed.update(i for i, l in run)
        rest = [l for i, l in enumerate(lines) if i not in claimed and l.strip()]
        shapes = collections.Counter(re.sub(r"0x[0-9a-f]+|\d+", "#", l[:64]) for l in rest)
        body.append("--- 未认领的其余非空行 %d 条，形状直方图（前 12 类，丢弃的是这些）---" % len(rest))
        for k, v in shapes.most_common(12):
            body.append("%5d  %s" % (v, k))
        blank = sum(1 for l in lines if not l.strip())
        tally.append("%s: 原 %d 行 / 认领 %d / 非空未认领 %d / 空行 %d / 分区闭合=%s（恒等式，只防脚本自己数错，不是判据）"
                     % (name, len(lines), len(claimed), len(rest), blank,
                        len(claimed) + len(rest) + blank == len(lines)))
        body.append("")

    body.append("== 认领账 ==")
    body += tally
    text_out = "\n".join(body) + "\n"
    n_red = text_out.count("[REDACTED]")
    body.append("口令在输入日志里出现 %d 次 ⇒ 输出件里 [REDACTED] 出现 %d 次；"
                "两数不必相等（直方图行会把一次替换算两次），安全判据是"
                "「输出件不含明文」那条断言" % (src_hits, n_red))
    text_out = "\n".join(body) + "\n"
    if pwd and pwd in text_out:
        raise SystemExit("ABORT: 输出件里仍含明文口令，不落盘")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="\n").write(text_out)
    print("WROTE %s (%d B)" % (out, os.path.getsize(out)))
    for t in tally:
        print(t)
    print("PLAINTEXT_OCCURRENCES_IN_INPUT=%d  REDACTED_MARKS_IN_OUTPUT=%d  PLAINTEXT_IN_OUTPUT=0"
          % (src_hits, text_out.count("[REDACTED]")))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
