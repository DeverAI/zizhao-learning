#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主机侧复算 1.54 消息页的换行/分页表，用来和真机 "msg paging" 日志对账。

为什么要有这只：真机那条 map=[...] 只有一个读数源；同一条消息在主机上按
**同一套宽度口径**再算一遍，两边逐字同值才算证明这是算法行为而不是运气
（R61 首验：真机 map 与本脚本输出逐字节同值，版面修复才算立住）。

本脚本**不打印任何消息内容**，只打印字节数/页号/y —— 在册消息里带配网口令。
消息正文与断点空格都是从 provision_ap.c 现场读的格式串，避免两边各写一份漂掉。

用法：python r61_wrap_sim.py [LAY_MSG_Y=10] [EPD_HEIGHT-LAY_MSG_PAGE_BOT=18]
"""
import io
import os
import re
import sys

MAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zizhao-esp32s3", "main")
if not os.path.isdir(MAIN):                       # 允许从别处调用
    MAIN = r"C:\Users\david\Documents\all_projects\自招学习\hardware\zizhao-esp32s3\main"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FACE_RE = re.compile(r"^const uif_glyph_t (ASCII16|LATIN32|CJK32|DIGIT96)_g[0-9A-Fa-f]+ "
                     r"=\s*\{0x([0-9A-Fa-f]+),\s*(\d+),\s*(\d+),", re.M)
FMT_RE = re.compile(r'snprintf\(\s*\w+\s*,\s*sizeof\([^)]*\)\s*,\s*"([^"]+)"\s*,\s*\(char\s*\*\s*\)\s*ap\.ap\.ssid\s*,\s*PROV_PASS')
PASS_RE = re.compile(r'#define\s+PROV_PASS\w*\s+"([^"]*)"')


def read(name):
    return io.open(os.path.join(MAIN, name), encoding="utf-8", errors="replace").read()


def load_faces():
    faces = {}
    for name, cp, w, h in FACE_RE.findall(read("ui_font.c")):
        faces.setdefault(name, {})[int(cp, 16)] = (int(w), int(h))
    return faces


FACES = load_faces()
EPD_W = 200
EPD_H = 200
# 版面常数默认取 3.97 那一版；1.54 的真机口径（y0=6、页底=EPD_HEIGHT-16）由 CLI 覆盖。
# argv 只在**命令行直跑**时解析：本文件被 r61_evidence.py 当库 import 时，argv 是那只脚本的
# 参数，在这里 int() 会直接 ValueError（实测撞过一次），故从模块顶层挪进 main()。
LAY_MSG_Y = 10
LAY_MSG_W = EPD_W - 12
LAY_MSG_H = 44
PAGE_BOT = EPD_H - 18
IND_Y = EPD_H - 16                   # 页码起画 y；ASCII16 那档高 16


def pick(cp):
    return "ASCII16" if cp < 0x80 else "CJK32"


def glyph_width(cp):
    if cp == 0x20:
        return 12
    g = FACES[pick(cp)].get(cp)
    return g[0] + 1 if g else (33 if cp >= 0x80 else 18)


def cps(b):
    return [ord(c) for c in bytes(b).decode("utf-8", "replace")]


def measure(s):
    return sum(glyph_width(c) for c in (cps(s) if isinstance(s, (bytes, bytearray)) else s))


def seg_height(s):
    hs = [FACES[pick(c)][c][1] for c in (cps(s) if isinstance(s, (bytes, bytearray)) else s)
          if c in FACES[pick(c)]]
    return max(hs) if hs else 0


def wrap(msg, maxw=LAY_MSG_W):
    """逐字照 eink_display.c 的 wrap_lines 四条断点规则：
    ①踩在空格上 overflow ⇒ 就地断、空格不给任何一方；②行尾就是空格 ⇒ 去掉它；
    ③回退到行内最后一个空格（下标 0 不算）；④没空格才硬切。
    返回 [(该行绘制的字节串, 从源里吃掉的字节数)]。"""
    lines, cur = [], b""
    for cp in cps(msg):
        nb = chr(cp).encode("utf-8")
        fits = len(cur) + len(nb) < 256           # WRAP_LINE_BYTES
        if cur and (not fits or measure(cur) + (glyph_width(cp) if fits else 0) > maxw):
            li = len(cur)
            k, adv, drop = li, li, False
            if cp == 0x20 and fits:
                drop = True
            elif li >= 2 and cur[-1:] == b" ":
                k, adv = li - 1, li
            else:
                sp = cur.rfind(b" ", 1)
                if sp > 0:
                    k, adv = sp, sp + 1
            if k < 1:
                k, adv, drop = li, li, False
            lines.append((cur[:k], adv))
            cur = cur[adv:]
            if drop:
                continue
        cur += nb
    if cur:
        lines.append((cur, len(cur)))
    return lines


def paginate(lines):
    rows, pg, y = [], 0, LAY_MSG_Y
    for i, (seg, adv) in enumerate(lines):
        pitch = max(LAY_MSG_H, seg_height(seg))
        if i and y + pitch > PAGE_BOT:
            pg += 1
            y = LAY_MSG_Y
        rows.append((i, pg, y, len(seg), adv))
        y += pitch
    return rows, pg + 1


def main():
    global LAY_MSG_Y, PAGE_BOT
    if len(sys.argv) > 1:
        LAY_MSG_Y = int(sys.argv[1])
    if len(sys.argv) > 2:
        PAGE_BOT = EPD_H - int(sys.argv[2])
    fmt = FMT_RE.search(read("provision_ap.c"))
    pwd = PASS_RE.search(read("provision_ap.c"))
    if not fmt or not pwd:
        print("FMT_OR_MACRO_NOT_FOUND fmt=%s pass=%s" % (bool(fmt), bool(pwd)))
        return 1
    ssid = "Zizhao-Setup-758D"          # 与真机日志里那只 SoftAP 名同案（由 MAC 派生）
    msg = fmt.group(1) % (ssid, pwd.group(1))
    msg = msg.encode("utf-8")

    miss = sorted({c for c in cps(msg) if c >= 0x80 and not FACES["CJK32"].get(c)})
    lines = wrap(msg)
    rows, pages = paginate(lines)
    print("MSG_BYTES=%d PWD_BYTES=%d glyphs=%d" % (len(msg), len(pwd.group(1).encode()), len(cps(msg))))
    print("CJK32_MISSING=%d %s" % (len(miss), [hex(c) for c in miss]))
    print("clause_widths=[%s] maxw=%d" %
          (" ".join("%dpx" % measure(c) for c in msg.split(b" ")), LAY_MSG_W))
    print("bytes=%d sum_adv=%d lines=%d pages=%d" %
          (len(msg), sum(r[4] for r in rows), len(lines), pages))
    print("map=[%s]" % " ".join("%d:%d+%d/%dB " % r[:4] for r in rows))
    print("widths=[%s]" % " ".join("%dpx" % measure(s) for s, _ in lines))
    bottoms = [y + max(0, seg_height(s)) - 1 for (i, pg, y, n, adv), (s, _) in zip(rows, lines)]
    print("lay: y0=%d page_bot=%d ind_y=%d" % (LAY_MSG_Y, PAGE_BOT, IND_Y))
    print("max_bottom=%d overlap_indicator=%s" % (max(bottoms), max(bottoms) >= IND_Y))
    print("per_page_lines=%s per_page_bytes=%s" %
          ([sum(1 for r in rows if r[1] == p) for p in range(pages)],
           [sum(r[3] for r in rows if r[1] == p) for p in range(pages)]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
