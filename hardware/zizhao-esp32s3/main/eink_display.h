#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 墨水屏（微雪 ESP32-S3-ePaper-3.97，800x480 黑白）：一段一刷的文字页。
 * 底层 = epd_driver.c（官方引脚/寄存器序列移植），字库 = ui_font.c（tools/gen_ui_font.py 生成）。 */
void eink_init(void);
void eink_show_status(const char *line1, const char *line2, const char *line3);
void eink_show_clock(const char *hhmm, const char *date_line, const char *title);
void eink_show_message(const char *msg);
/* 深睡前调用：面板进 0x10 睡眠省电；画面保持，唤醒后首次刷新自动走全刷。 */
void eink_sleep(void);

#ifdef __cplusplus
}
#endif
