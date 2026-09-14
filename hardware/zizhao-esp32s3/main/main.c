/* 自招学习板 · 微雪 ESP32-S3-ePaper-3.97 主程序 v2
 *
 * 按键 / 时钟 / 后台静默 OTA（无用户升级入口）/ 离线包 / 电源 / 音量
 */
#include <stdio.h>
#include <string.h>
#include <time.h>
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
#include "buttons.h"
#include "clock_sync.h"
#include "ota_bg.h"
#include "eink_display.h"
#include "download_mgr.h"

static const char *TAG = "zizhao";

static zizhao_creds_t s_creds;
static char s_sid[128];
static power_policy_t s_policy;
static int64_t s_boot_us;
static int64_t s_last_act_us;
static bool s_audio_ready = false;
static bool s_playing = false;
static int s_seg = 0;
static int s_vol = 12;

static void mark_act(void)
{
    s_last_act_us = esp_timer_get_time();
    volume_guard_mark_activity();
}

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
    eink_show_message("按时关机");
    net_http_report_progress(s_sid, s_creds.server_url, 0, s_seg, 0);
    esp_wifi_stop();
    uint64_t us = power_policy_us_until_boot(&s_policy, time(NULL));
    esp_sleep_enable_timer_wakeup(us);
    esp_deep_sleep_start();
}

static void handle_button(btn_event_t ev)
{
    if (ev == BTN_NONE) return;
    mark_act();
    switch (ev) {
    case BTN_PLAY_PAUSE:
        s_playing = !s_playing;
        eink_show_status(s_playing ? "播放" : "暂停", s_audio_ready ? "音频就绪" : "仅文字", "");
        break;
    case BTN_NEXT_SEG:
        s_seg++;
        eink_show_status("下一段", "", "");
        break;
    case BTN_PREV_SEG:
        if (s_seg > 0) s_seg--;
        eink_show_status("上一段", "", "");
        break;
    case BTN_REFRESH_MATERIAL:
        eink_show_status("换素材…", "", "");
        /* TODO: POST /api/material/refresh */
        break;
    case BTN_VOLUME_UP:
        if (s_vol < 15) s_vol++;
        eink_show_status("音量", "", "");
        break;
    case BTN_VOLUME_DOWN:
        if (s_vol > 0) s_vol--;
        eink_show_status("音量", "", "");
        break;
    case BTN_TALK:
        eink_show_status("对话…", "", "");
        break;
    default:
        break;
    }
}

static void refresh_clock_page(void)
{
    char hm[8], full[32];
    clock_format_hm(hm, sizeof(hm));
    clock_format_full(full, sizeof(full), time(NULL));
    /* 未校时也显示 RTC 时间，避免白屏 */
    eink_show_clock(hm, full, "自招学习");
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    s_boot_us = esp_timer_get_time();
    s_last_act_us = s_boot_us;
    volume_guard_init(12, 1, 600);
    power_policy_defaults(&s_policy);
    offline_store_init();
    buttons_init();
    eink_init();

    if (!nvs_creds_load(&s_creds) || !nvs_creds_has_passkey(&s_creds)) {
        eink_show_message("请现场配网");
        provision_ap_start();
        while (!nvs_creds_has_passkey(&s_creds)) {
            nvs_creds_load(&s_creds);
            vTaskDelay(pdMS_TO_TICKS(2000));
        }
    }

    if (nvs_creds_ready_for_sta(&s_creds)) {
        wifi_sta_start(&s_creds);
        vTaskDelay(pdMS_TO_TICKS(3000));
        clock_sync_sntp();
        if (net_http_login(&s_creds, s_sid, sizeof(s_sid))) {
            ESP_LOGI(TAG, "login ok");
            dl_mgr_init();
            dl_state_t st = {0};
            snprintf(st.day_key, sizeof(st.day_key), "today");
            if (dl_mgr_sync_once(s_sid, s_creds.server_url, &st)) {
                s_audio_ready = st.audio_allowed;
                eink_show_status("今日已缓存", st.audio_allowed ? "含音频" : "仅文字", st.last_error);
            } else {
                eink_show_status("离线模式", "用上次缓存", st.last_error);
            }
            char pol[512];
            if (net_http_get_power_policy(s_sid, s_creds.server_url, pol, sizeof(pol))) {
                power_policy_parse_json(pol, &s_policy);
            }
        }
    }

    refresh_clock_page();
    int last_min = -1;
    int64_t last_ota_check = esp_timer_get_time();

    for (;;) {
        handle_button(buttons_poll());
        s_vol = volume_guard_tick();

        time_t now = time(NULL);
        struct tm tmv;
        localtime_r(&now, &tmv);
        if (tmv.tm_min != last_min) {
            last_min = tmv.tm_min;
            refresh_clock_page(); /* 每分钟一刷，墨水屏可承受 */
        }

        if (power_policy_should_sleep(&s_policy, now, s_boot_us, s_last_act_us)) {
            graceful_shutdown();
        }

        /* 每 6 小时后台查一次固件（绝不走按键） */
        if (s_sid[0] && (esp_timer_get_time() - last_ota_check) > 6LL * 3600LL * 1000000LL) {
            last_ota_check = esp_timer_get_time();
            ota_bg_check_and_update(s_sid, s_creds.server_url);
        }

        if (s_playing && s_audio_ready) {
            mark_act();
            /* TODO: I2S 下一段 MP3 */
        }
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}
