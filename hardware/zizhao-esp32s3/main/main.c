/* 自招学习板 · 微雪 ESP32-S3-ePaper-3.97 主程序
 *
 * 流程：NVS 凭据 → 无 PassKey 则 AP 配网 → WiFi → device/login
 *      → offline manifest/bundle（仅 review passed 才有音频）
 *      → 播放循环 + volume_guard + power_policy
 *
 * 引脚以官方 wiki 为准；此处 SD SPI 用了常见 39/40/41/42，联调改。
 */
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "esp_sleep.h"

#include "nvs_creds.h"
#include "net_http.h"
#include "power_policy.h"
#include "volume_guard.h"
#include "offline_store.h"
#include "provision_ap.h"

static const char *TAG = "zizhao";

static zizhao_creds_t s_creds;
static char s_sid[128];
static power_policy_t s_policy;
static int64_t s_boot_us;
static int64_t s_last_act_us;
static bool s_audio_ready = false;

static void mark_act(void) { s_last_act_us = esp_timer_get_time(); }

static void wifi_sta_start(const zizhao_creds_t *c)
{
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    wifi_config_t wc = {0};
    strncpy((char *)wc.sta.ssid, c->wifi_ssid, sizeof(wc.sta.ssid) - 1);
    strncpy((char *)wc.sta.password, c->wifi_pass, sizeof(wc.sta.password) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_connect());
}

static void graceful_shutdown(void)
{
    ESP_LOGW(TAG, "graceful shutdown");
    /* 1 停播 2 progress 3 关 WiFi 4 RTC 深睡 */
    net_http_report_progress(s_sid, s_creds.server_url, 0, 0, 0);
    esp_wifi_stop();
    uint64_t us = power_policy_us_until_boot(&s_policy, time(NULL));
    esp_sleep_enable_timer_wakeup(us);
    esp_deep_sleep_start();
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    s_boot_us = esp_timer_get_time();
    s_last_act_us = s_boot_us;
    volume_guard_init(12, 1, 600);
    power_policy_defaults(&s_policy);
    offline_store_init();

    if (!nvs_creds_load(&s_creds) || !nvs_creds_has_passkey(&s_creds)) {
        ESP_LOGW(TAG, "no PassKey — start onsite AP provision");
        provision_ap_start();
        while (!nvs_creds_has_passkey(&s_creds)) {
            nvs_creds_load(&s_creds);
            vTaskDelay(pdMS_TO_TICKS(2000));
        }
    }

    if (nvs_creds_ready_for_sta(&s_creds)) {
        wifi_sta_start(&s_creds);
        vTaskDelay(pdMS_TO_TICKS(3000));
        if (net_http_login(&s_creds, s_sid, sizeof(s_sid))) {
            ESP_LOGI(TAG, "login ok");
            char buf[16384];
            if (net_http_get_bundle(s_sid, s_creds.server_url, buf, sizeof(buf))) {
                offline_store_save_text("today", buf, strlen(buf));
                s_audio_ready = strstr(buf, "\"audio_ready\": true") != NULL
                                 || strstr(buf, "\"audio_ready\":true") != NULL;
                ESP_LOGI(TAG, "bundle cached audio_ready=%d", (int)s_audio_ready);
            }
            char pol[512];
            if (net_http_get_power_policy(s_sid, s_creds.server_url, pol, sizeof(pol))) {
                power_policy_parse_json(pol, &s_policy);
            }
        } else {
            ESP_LOGW(TAG, "login failed — offline cache only");
        }
    }

    /* 主循环骨架：按键/播放/电源 */
    for (;;) {
        int vol = volume_guard_tick();
        (void)vol;
        time_t now = time(NULL);
        if (power_policy_should_sleep(&s_policy, now, s_boot_us, s_last_act_us)) {
            graceful_shutdown();
        }
        /* TODO: I2S 播 MP3；仅 s_audio_ready 时允许 */
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
