#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 墨水屏：只做「一段一刷」的文字页；骨架用 UART 日志占位，
 * 到货后换成微雪 GDEY042T81 / UC8179 等官方驱动。 */
void eink_init(void);
void eink_show_status(const char *line1, const char *line2, const char *line3);
void eink_show_clock(const char *hhmm, const char *date_line, const char *title);
void eink_show_message(const char *msg);

#ifdef __cplusplus
}
#endif
