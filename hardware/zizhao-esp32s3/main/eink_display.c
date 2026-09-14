#include "eink_display.h"
#include <stdio.h>
#include "esp_log.h"

static const char *TAG = "eink";

void eink_init(void)
{
    /* TODO: SPI + 面板复位/DC/CS；微雪 3.97 例程 */
    ESP_LOGI(TAG, "eink stub — replace with Waveshare driver");
}

void eink_show_status(const char *line1, const char *line2, const char *line3)
{
    ESP_LOGI(TAG, "STATUS | %s | %s | %s",
             line1 ? line1 : "", line2 ? line2 : "", line3 ? line3 : "");
}

void eink_show_clock(const char *hhmm, const char *date_line, const char *title)
{
    /* 大号 HH:MM + 日期 + 标题；墨水屏静态显示，断电仍可见 */
    ESP_LOGI(TAG, "CLOCK %s  %s  %s",
             hhmm ? hhmm : "--:--", date_line ? date_line : "", title ? title : "");
}

void eink_show_message(const char *msg)
{
    ESP_LOGI(TAG, "MSG %s", msg ? msg : "");
}
