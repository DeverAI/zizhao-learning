/*
 * ESP32-S3 自招板 — 控制流骨架 v2
 * 音频门控 / 10min 音量 / 04:30关 06:00开 / 开机15min无活动再关 / AP配网
 * 伪代码，勿直接编译；见 esp32s3_firmware_skeleton.md
 */
#if 0
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include "esp_sleep.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#define VOL_IDLE_SEC     600
#define BOOT_IDLE_SEC    900
#define DEFAULT_VOL      12
#define IDLE_VOL         1

static int  s_volume = DEFAULT_VOL;
static int64_t s_last_activity_us;
static int64_t s_boot_us;
static int  s_audio_allowed = 0; /* 来自 bundle.audio_ready */

void mark_activity(void) {
    s_last_activity_us = esp_timer_get_time();
}

void volume_guard(void) {
    int64_t idle = esp_timer_get_time() - s_last_activity_us;
    if (idle > (int64_t)VOL_IDLE_SEC * 1000000LL && s_volume > IDLE_VOL) {
        s_volume = IDLE_VOL;          /* 10 分钟无操作 → 最小音量 */
        dac_set_volume(s_volume);
    }
}

int should_reboot_poweroff(void) {
    /* 按 RTC 策略：默认 04:30 关、06:00 开 */
    rtc_time_t t;
    rtc_get_time(&t);
    if (t.hour == 4 && t.min == 30) return 1;
    /* 开机后 15 分钟无有效活动再关 */
    if (esp_timer_get_time() - s_boot_us > (int64_t)BOOT_IDLE_SEC * 1000000LL) {
        int64_t act = esp_timer_get_time() - s_last_activity_us;
        if (act > (int64_t)BOOT_IDLE_SEC * 1000000LL) return 1;
    }
    return 0;
}

void graceful_shutdown(void) {
    player_stop();
    http_report_progress();           /* 断点 */
    eink_show("按时关机");
    wifi_stop();
    esp_sleep_enable_timer_wakeup(us_until_next_boot());
    esp_deep_sleep_start();           /* 不依赖任务锁，防死锁 */
}

void onsite_ap_portal(void) {
    /* SoftAP Zizhao-Setup-xxxx + captive 表单 wifi/server_url
       PassKey 从 NVS，不重新采集 */
    wifi_start_ap("Zizhao-Setup-XXXX");
    http_serve_portal();
}

void boot_flow(void) {
    s_boot_us = esp_timer_get_time();
    s_last_activity_us = s_boot_us;
    nvs_load_credentials();
    if (!has_passkey()) { onsite_ap_portal(); return; }
    wifi_connect_or_offline_cache();
    if (device_login() == 0) {
        offline_pull_manifest_bundle();
        s_audio_allowed = bundle_audio_ready(); /* 未过审则 0，禁播 MP3 */
    }
}

void app_main(void) {
    boot_flow();
    for (;;) {
        volume_guard();
        if (should_reboot_poweroff()) graceful_shutdown();
        if (playing && s_audio_allowed) { mark_activity(); play_next_seg(); }
        if (button_pressed()) { mark_activity(); s_volume = DEFAULT_VOL; }
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
#endif
