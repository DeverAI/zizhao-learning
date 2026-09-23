#include "clock_sync.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#include "esp_log.h"
#include "esp_sntp.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"

#include "net_http.h"

static const char *TAG = "clock";

/* 北京时间固定 UTC+8，无夏令时。
 * "CST-8" 的符号是 POSIX 反的：CST-8 表示 UTC+8（东八区）。别改成 "+8"。 */
#define TZ_BEIJING "CST-8"
#define NVS_NS "clock"
#define NVS_KEY_LAST "last_epoch"

static volatile bool s_synced = false;

static const char *WEEKDAY_CN[7] = {"周日", "周一", "周二", "周三", "周四", "周五", "周六"};

static void on_sync(struct timeval *tv)
{
    (void)tv;
    s_synced = true;
    ESP_LOGI(TAG, "SNTP synced");
}

void clock_tz_init(void)
{
    /* 必须在任何 localtime_r 之前调用，否则按 UTC 处理，
     * 北京时间 07:30 会显示成前一天 23:30，日期直接错一天。 */
    setenv("TZ", TZ_BEIJING, 1);
    tzset();
}

bool clock_sync_sntp(void)
{
    clock_tz_init();
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    /* 阿里云 NTP 国内可达性最好；再挂一个腾讯源做备份 */
    esp_sntp_setservername(0, "ntp.aliyun.com");
    esp_sntp_setservername(1, "ntp.tencent.com");
    esp_sntp_set_time_sync_notification_cb(on_sync);
    esp_sntp_init();

    /* 最多等 10 秒。原来 40×250ms=10s 但循环里只判 flag，
     * Wi-Fi 刚起来时容易被判超时而其实后面才成功，这里保留超时但让调用方有兜底。 */
    for (int i = 0; i < 40 && !s_synced; i++) {
        vTaskDelay(pdMS_TO_TICKS(250));
    }
    /* 无论成功/超时都停掉 SNTP：esp_sntp_init 会常驻一个轮询任务，
     * 电池设备不需要持续对时，取一次足够；超时则交给 HTTP 兜底。 */
    esp_sntp_stop();
    if (s_synced) {
        clock_stash_save(time(NULL));
    } else {
        ESP_LOGW(TAG, "sntp timeout, will try http");
    }
    return s_synced;
}

bool clock_sync_http(const char *server_url)
{
    if (!server_url || !server_url[0]) return false;
    clock_tz_init();
    char url[200];
    snprintf(url, sizeof(url), "%s/api/system/time", server_url);

    char resp[512] = {0};
    /* 该接口免鉴权，不需要 sid */
    if (!net_http_get(url, resp, sizeof(resp), NULL)) {
        ESP_LOGW(TAG, "http time fetch failed");
        return false;
    }
    /* 只取 unix 字段，避免为一行 JSON 引 cJSON 依赖（与 power_policy 同风格）。
     * 报文："unix": 1789000000  —— 冒号后可能带空格。 */
    const char *k = strstr(resp, "\"unix\"");
    if (!k) { ESP_LOGW(TAG, "http time: no unix field"); return false; }
    const char *c = strchr(k, ':');
    if (!c) { ESP_LOGW(TAG, "http time: no colon after unix"); return false; }
    /* ESP32 上 long 是 32 位（且 3000000000 字面量会翻负），时间戳一律用 64 位解析。 */
    long long epoch = strtoll(c + 1, NULL, 10);
    /* 下界 2020-01-01；上界取 2038-01-19（xtensa 的 time_t 是 32 位，超过会截断成负数、
     * 污染 NVS stash 与定点关机判断）。挡住解析出 0/垃圾的情况。 */
    if (epoch < 1577836800LL || epoch > 2147483647LL) {
        ESP_LOGW(TAG, "http time out of range: %lld", epoch);
        return false;
    }
    struct timeval tv = {.tv_sec = (time_t)epoch, .tv_usec = 0};
    if (settimeofday(&tv, NULL) != 0) {
        ESP_LOGW(TAG, "http time: settimeofday failed");
        return false;
    }
    s_synced = true;
    clock_stash_save((time_t)epoch);
    ESP_LOGI(TAG, "http time synced: %lld", epoch);
    return true;
}

void clock_stash_save(time_t t)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_i64(h, NVS_KEY_LAST, (int64_t)t);
    nvs_commit(h);
    nvs_close(h);
}

time_t clock_stash_load(void)
{
    nvs_handle_t h;
    int64_t v = 0;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return 0;
    if (nvs_get_i64(h, NVS_KEY_LAST, &v) != ESP_OK) v = 0;
    nvs_close(h);
    return (time_t)v;
}

bool clock_is_synced(void)
{
    return s_synced;
}

void clock_format_hm(char *out, size_t n)
{
    if (!out || n == 0) return;
    time_t now = time(NULL);
    struct tm tmv;
    localtime_r(&now, &tmv);
    if (tmv.tm_year < 120) {  /* <2020：RTC 还没对过，别显示 1970 */
        snprintf(out, n, "--:--");
        return;
    }
    snprintf(out, n, "%02d:%02d", tmv.tm_hour, tmv.tm_min);
}

void clock_format_full(char *out, size_t n, time_t t)
{
    if (!out || n == 0) return;
    struct tm tmv;
    localtime_r(&t, &tmv);
    snprintf(out, n, "%04d-%02d-%02d %02d:%02d:%02d",
             tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday,
             tmv.tm_hour, tmv.tm_min, tmv.tm_sec);
}

void clock_format_date_cn(char *out, size_t n, time_t t)
{
    if (!out || n == 0) return;
    struct tm tmv;
    localtime_r(&t, &tmv);
    if (tmv.tm_year < 120) {
        snprintf(out, n, "未校准（联网后自动对时）");
        return;
    }
    int wd = tmv.tm_wday;
    if (wd < 0 || wd > 6) wd = 0;
    snprintf(out, n, "%04d年%02d月%02d日 %s",
             tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday, WEEKDAY_CN[wd]);
}
