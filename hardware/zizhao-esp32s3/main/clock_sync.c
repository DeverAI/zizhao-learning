#include "clock_sync.h"
#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include "esp_sntp.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "clock";
static bool s_synced = false;

static void on_sync(struct timeval *tv)
{
    s_synced = true;
    ESP_LOGI(TAG, "SNTP synced");
}

bool clock_sync_sntp(void)
{
    setenv("TZ", "CST-8", 1);
    tzset();
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "ntp.aliyun.com");
    esp_sntp_set_time_sync_notification_cb(on_sync);
    esp_sntp_init();
    for (int i = 0; i < 40 && !s_synced; i++) {
        vTaskDelay(pdMS_TO_TICKS(250));
    }
    return s_synced;
}

bool clock_is_synced(void)
{
    return s_synced;
}

void clock_format_hm(char *out, size_t n)
{
    time_t now = time(NULL);
    struct tm tmv;
    localtime_r(&now, &tmv);
    snprintf(out, n, "%02d:%02d", tmv.tm_hour, tmv.tm_min);
}

void clock_format_full(char *out, size_t n, time_t t)
{
    struct tm tmv;
    localtime_r(&t, &tmv);
    snprintf(out, n, "%04d-%02d-%02d %02d:%02d:%02d",
             tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday,
             tmv.tm_hour, tmv.tm_min, tmv.tm_sec);
}
