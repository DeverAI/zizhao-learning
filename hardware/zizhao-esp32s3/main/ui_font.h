/* 生成文件，勿手改：由 tools/gen_ui_font.py 生成（点阵字库）。 */
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
