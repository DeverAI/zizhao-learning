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

/* ---- 消息页分页（R61：墨水屏没有滚动，装不下的内容必须能翻出来） ----
 * 本模块只管"这条消息共几页""第 k 页画成什么样"；按键往哪走是 app 的事
 * （main.c 的 ui_browse_next：消息各页 → 时钟页 → 状态页 → 回第 1 页）。 */
int eink_msg_pages(void);       /* 屏上当前这条消息共几页；0 = 现在没有消息 */
int eink_msg_page(void);        /* 当前在第几页，0 起 */
void eink_msg_goto_page(int page);   /* 画第 page 页（越界自动钳到首/末页） */
/* 按键浏览：把"消息各页 → 时钟页 → 状态页"走一格。实现在 main.c（页面环的内容归 app），
 * 放在这只头里是因为配网窗口也要用它：provision_ap_wait_done 里读到的按键同样要能翻页。 */
void ui_browse_next(void);

#ifdef __cplusplus
}
#endif
