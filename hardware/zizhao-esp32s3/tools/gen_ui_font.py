# -*- coding: utf-8 -*-
"""生成墨水屏子集点阵字库 main/ui_font.c/.h（离线开发工具，产物入库）。

字符集来源：自动扫描 ../main/*.c 的字符串字面量收集所有非 ASCII 码点，
另加显式补充字符。渲染：
  - UIF_ASCII16 : Consolas 15px 半角（调试错误串）
  - UIF_LATIN32 : Consolas 30px 半角（正文行内英文/数字，与 CJK32 同高排一行）
  - UIF_CJK32   : 微软雅黑 32px 全角（正文/标题/日期）
  - UIF_DIGIT96 : 微软雅黑 Bold 96px（时钟大数字 0-9 : -）
位语义：bit=1 表示黑点，行主序、MSB 在左、行距 (w+7)//8。
"""
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.normpath(os.path.join(HERE, "..", "main"))
OUT_H = os.path.join(MAIN_DIR, "ui_font.h")
OUT_C = os.path.join(MAIN_DIR, "ui_font.c")

F_CJK = r"C:\Windows\Fonts\msyh.ttc"
F_DIGIT = r"C:\Windows\Fonts\msyhbd.ttc"
F_ASCII = r"C:\Windows\Fonts\consola.ttf"

EXTRA = set("0123456789:，。！？…（）：、·%/-~—") | {chr(c) for c in range(0x20, 0x7F)}


def scan_chars():
    cps = set()
    for fn in sorted(os.listdir(MAIN_DIR)):
        if not fn.endswith((".c", ".h")):
            continue
        try:
            with open(os.path.join(MAIN_DIR, fn), encoding="utf-8") as f:
                src = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        for lit in re.findall(r'"((?:[^"\\\n]|\\.)*)"', src):
            for ch in lit:
                if ord(ch) > 0x7F:
                    cps.add(ord(ch))
    for ch in EXTRA:
        cps.add(ord(ch))
    return cps


def render_glyph(ch, font, force_w=None):
    asc, desc = font.getmetrics()
    w = force_w if force_w else max(1, int(round(font.getlength(ch))))
    h = asc + desc
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    d.text((0, 0), ch, fill=0, font=font)
    px = img.load()
    rows = []
    for y in range(h):
        byte_acc = 0
        row = []
        for x in range(w):
            byte_acc = (byte_acc << 1) | (1 if px[x, y] < 128 else 0)
            if (x & 7) == 7:
                row.append(byte_acc)
                byte_acc = 0
        if w & 7:
            row.append(byte_acc << (8 - (w & 7)))
        rows.extend(row)
    return w, h, rows


def build(tbl, font, cps, force_w=None):
    out = []
    for cp in sorted(cps):
        ch = chr(cp)
        w, h, rows = render_glyph(ch, font, force_w)
        body = ",".join(f"0x{b:02X}" for b in rows)
        out.append(
            f"static const uint8_t {tbl}_g{cp:04X}_bits[] = {{{body}}};\n"
            f"const uif_glyph_t {tbl}_g{cp:04X} = {{0x{cp:04X}, {w}, {h}, {tbl}_g{cp:04X}_bits}};"
        )
    cps = sorted(cps)
    glyph_ptrs = ",\n".join(f"    &{tbl}_g{cp:04X}" for cp in cps)
    asc, _ = font.getmetrics()
    arr = (
        f"static const uif_glyph_t *const {tbl}_glyphs[] = {{\n{glyph_ptrs},\n}};\n"
        f"const uif_font_t UIF_{tbl} = {{{tbl}_glyphs, {len(cps)}, {asc}}};"
    )
    return "\n".join(out) + "\n\n" + arr


def main():
    chars = scan_chars()
    cjk = {cp for cp in chars if cp >= 0x80}
    ascii_cp = {cp for cp in range(0x20, 0x7F)}
    digit_cp = {ord(c) for c in "0123456789:"}

    f_ascii = ImageFont.truetype(F_ASCII, 15)
    f_latin = ImageFont.truetype(F_ASCII, 30)
    f_cjk = ImageFont.truetype(F_CJK, 32)
    f_digit = ImageFont.truetype(F_DIGIT, 96)

    c = [
        "/* 生成文件，勿手改：由 hardware/zizhao-esp32s3/tools/gen_ui_font.py 生成。 */",
        '#include "ui_font.h"',
        "",
        build("ASCII16", f_ascii, ascii_cp),
        build("LATIN32", f_latin, ascii_cp),
        build("CJK32", f_cjk, cjk, force_w=32),
        build("DIGIT96", f_digit, digit_cp | {ord("-")}),
        "",
        "const uif_glyph_t *uif_lookup(const uif_font_t *font, uint32_t cp)",
        "{",
        "    int lo = 0, hi = font->count - 1;",
        "    while (lo <= hi) {",
        "        int mid = (lo + hi) / 2;",
        "        uint32_t m = font->glyphs[mid]->cp;",
        "        if (m == cp) return font->glyphs[mid];",
        "        if (m < cp) lo = mid + 1; else hi = mid - 1;",
        "    }",
        "    return 0;",
        "}",
        "",
    ]
    with open(OUT_C, "w", encoding="utf-8") as f:
        f.write("\n".join(c))

    with open(OUT_H, "w", encoding="utf-8") as f:
        f.write(
            """/* 生成文件，勿手改：由 tools/gen_ui_font.py 生成（点阵字库）。 */
#ifndef ZIZHAO_UI_FONT_H
#define ZIZHAO_UI_FONT_H
#include <stdint.h>

typedef struct {
    uint32_t cp;        /* Unicode 码点 */
    uint16_t w, h;      /* 点阵尺寸（像素） */
    const uint8_t *bits;/* 行主序 MSB 在左，行距 (w+7)/8；bit=1 为墨点 */
} uif_glyph_t;

typedef struct {
    const uif_glyph_t *const *glyphs;  /* 按 cp 升序，可二分 */
    int count;
    int ascent;                        /* 基线距字模顶部的像素 */
} uif_font_t;

extern const uif_font_t UIF_ASCII16;
extern const uif_font_t UIF_LATIN32;
extern const uif_font_t UIF_CJK32;
extern const uif_font_t UIF_DIGIT96;

#ifdef __cplusplus
extern "C" {
#endif
/* 找不到返回 NULL（由调用方画替代框，绝不崩溃）。 */
const uif_glyph_t *uif_lookup(const uif_font_t *font, uint32_t cp);
#ifdef __cplusplus
}
#endif
#endif
"""
        )
    sz = os.path.getsize(OUT_C)
    print(f"CJK chars={len(cjk)} -> {OUT_C} ({sz} bytes) + {OUT_H}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
