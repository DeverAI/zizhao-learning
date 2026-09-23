/* 自招学习板 · 微雪 ESP32-S3-ePaper-3.97 主程序 v2
 *
 * 按键 / 时钟 / 后台静默 OTA（无用户升级入口）/ 离线包 / 电源 / 音量
 */
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "esp_mac.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_sleep.h"
#include "esp_ota_ops.h"

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

/* 恢复性看门狗：凭据"存在但不可用"（WiFi 连不上 / server_url 填错 / 密码改过）时，
 * 只看 ready_for_sta 的闸门永远不会再打开 = 现场不可恢复，只能拆机重烧。
 * 用 NVS 记连续登录失败次数，到阈值就强制回到配网门户。登录成功即清零。 */
#define GATE_NS         "gate"
#define GATE_KEY_BAD    "badlogin"
#define GATE_BAD_MAX    3

static int load_bad_login(void)
{
    nvs_handle_t h;
    if (nvs_open(GATE_NS, NVS_READONLY, &h) != ESP_OK) return 0;
    int32_t v = 0;
    nvs_get_i32(h, GATE_KEY_BAD, &v);
    nvs_close(h);
    return (int)v;
}

static void bump_bad_login(void)
{
    nvs_handle_t h;
    if (nvs_open(GATE_NS, NVS_READWRITE, &h) != ESP_OK) return;
    int32_t v = 0;
    nvs_get_i32(h, GATE_KEY_BAD, &v);
    if (v < 100) v++;   /* 防溢出，够用即可 */
    nvs_set_i32(h, GATE_KEY_BAD, v);
    nvs_commit(h);
    nvs_close(h);
}

static void clear_bad_login(void)
{
    nvs_handle_t h;
    if (nvs_open(GATE_NS, NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_i32(h, GATE_KEY_BAD, 0);
    nvs_commit(h);
    nvs_close(h);
}

static void mark_act(void)
{
    s_last_act_us = esp_timer_get_time();
    volume_guard_mark_activity();
}

static bool s_sta_netif_added = false;
static volatile bool s_sta_got_ip = false;
static volatile int s_sta_retry = 0;
#define STA_RETRY_MAX 8

static void wifi_sta_ip_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg; (void)base; (void)data;
    if (id == IP_EVENT_STA_GOT_IP) {
        s_sta_got_ip = true;
        s_sta_retry = 0;
    }
}

static void wifi_sta_event_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg; (void)base; (void)data;
    if (id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (id == WIFI_EVENT_STA_DISCONNECTED) {
        s_sta_got_ip = false;
        /* 绝不能在回调里 vTaskDelay：default event loop 任务栈只有 2304B 且所有
         * netif/IP handler 共用它，阻塞会饿死 GOT_IP 等事件、丢事件、断线重连失效。
         * 退避交给 esp_wifi_connect 自身的关联超时节奏；只统计次数、到顶即放弃。 */
        if (s_sta_retry < STA_RETRY_MAX) {
            s_sta_retry++;
            esp_err_t ce = esp_wifi_connect();
            if (ce != ESP_OK) ESP_LOGW(TAG, "reconnect #%d: %s", s_sta_retry, esp_err_to_name(ce));
        } else {
            /* 放弃：让驱动状态干净，主循环随后按离线走（缓存/时钟页仍可用）。 */
            esp_wifi_disconnect();
            ESP_LOGW(TAG, "STA reconnect give up after %d tries", STA_RETRY_MAX);
        }
    }
}

static bool wifi_sta_start(const zizhao_creds_t *c)
{
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    /* 配网 AP 可能已初始化 WiFi 驱动；重复 init 返回 INVALID_STATE 是正常的。
     * STA netif 同样依赖驱动已 init，故先 init 后建。 */
    esp_err_t e = esp_wifi_init(&cfg);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "esp_wifi_init failed: %s", esp_err_to_name(e));
        return false;
    }
    if (!s_sta_netif_added) {
        if (!esp_netif_create_default_wifi_sta()) {
            ESP_LOGE(TAG, "create sta netif failed");
            return false;
        }
        s_sta_netif_added = true;
    }
    /* 若 AP 已启动，先停掉再切 STA */
    e = esp_wifi_stop();
    if (e != ESP_OK && e != ESP_ERR_WIFI_NOT_STARTED) {
        ESP_LOGW(TAG, "esp_wifi_stop: %s", esp_err_to_name(e));
    }
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_sta_event_handler, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_sta_ip_handler, NULL);

    wifi_config_t wc = {0};
    strncpy((char *)wc.sta.ssid, c->wifi_ssid, sizeof(wc.sta.ssid) - 1);
    strncpy((char *)wc.sta.password, c->wifi_pass, sizeof(wc.sta.password) - 1);
    /* 这些调用任一失败都只记日志并返回 false，绝不 ESP_ERROR_CHECK panic：
     * 密码错 / NO_MEM / WPA3 不匹配都会让 esp_wifi_* 返错，网络抖动时
     * panic 会直接触发复位循环（设备每天自启，一次异常不能变砖）。 */
    if ((e = esp_wifi_set_mode(WIFI_MODE_STA)) != ESP_OK) { ESP_LOGE(TAG, "set_mode: %s", esp_err_to_name(e)); return false; }
    if ((e = esp_wifi_set_config(WIFI_IF_STA, &wc)) != ESP_OK) { ESP_LOGE(TAG, "set_config: %s", esp_err_to_name(e)); return false; }
    if ((e = esp_wifi_start()) != ESP_OK) { ESP_LOGE(TAG, "start: %s", esp_err_to_name(e)); return false; }
    if ((e = esp_wifi_connect()) != ESP_OK) { ESP_LOGW(TAG, "first connect: %s", esp_err_to_name(e)); }
    return true;
}

static void graceful_shutdown(void)
{
    eink_show_message("按时关机");
    net_http_report_progress(s_sid, s_creds.server_url, 0, s_seg, 0);
    esp_wifi_stop();
    offline_store_flush(); /* 深睡前把 FATFS 写缓存落盘，避免半截文件 */
    uint64_t us = power_policy_us_until_boot(&s_policy, time(NULL));
    if (!clock_is_synced()) us = 21600ULL * 1000000ULL; /* 未校时：定时唤醒无意义，固定 6h 后再试 */
    esp_sleep_enable_timer_wakeup(us);
    eink_sleep(); /* 进 deep sleep 前让墨水屏进 sleep 态，避免面板长时间带电 */
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
    char hm[8], date_cn[48], full[32];
    time_t now = time(NULL);
    clock_format_hm(hm, sizeof(hm));
    /* 日期行用中文星期，板子上比 "2026-09-16 07:30:00" 好认；
     * 未校时时函数自带「未校准」占位，不会出现 1970 年。 */
    clock_format_date_cn(date_cn, sizeof(date_cn), now);
    clock_format_full(full, sizeof(full), now);
    eink_show_clock(hm, date_cn, "自招学习");
    ESP_LOGI(TAG, "clock page: %s %s (%s)", hm, date_cn, full);
}

void app_main(void)
{
    /* 每轮点屏探测都会 gpio_config 一次 41/42 与 GPIO1，GPIO 驱动把这 6 个焊盘的
     * 完整状态打成 INFO，5s 一轮会把真正的诊断行（axp/epd）冲掉。压到 WARN。 */
    esp_log_level_set("gpio", ESP_LOG_WARN);
    /* NVS 撑满/版本变更时 IDF 不自动擦，直接 panic 会让屏/闸门全跑不起来=无条件变砖。
     * 先擦 nvs 分区（不碰 ota）重试；仍失败也不 panic，后面 ready_for_sta 为假自然进配网闸门。 */
    esp_err_t nvs_e = nvs_flash_init();
    if (nvs_e == ESP_ERR_NVS_NO_FREE_PAGES || nvs_e == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "nvs full/old, erasing nvs partition");
        /* 擦除本身也不能 ESP_ERROR_CHECK：分区表日后调整/扇区磨损/半烧设备时
         * nvs_flash_erase_partition 会返错，此处在 eink_init 之前 panic = 黑屏复位循环，
         * 正是这轮要消灭的变砖类。擦失败就带着未初始化 NVS 继续，后面闸门兜底。 */
        esp_err_t ee = nvs_flash_erase_partition("nvs");
        if (ee != ESP_OK) ESP_LOGE(TAG, "nvs erase failed: %s (proceeding without NVS)", esp_err_to_name(ee));
        else nvs_e = nvs_flash_init();
    }
    if (nvs_e != ESP_OK) ESP_LOGE(TAG, "nvs_flash_init failed: %s (proceeding to provisioning gate)", esp_err_to_name(nvs_e));
    /* 网络栈与默认事件循环必须先建，STA/AP 的 esp_netif_create_default_wifi_* 依赖它们 */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    s_boot_us = esp_timer_get_time();
    s_last_act_us = s_boot_us;

    /* 两块同款板同时在机时 COM 号会漂，日志必须先自证身份（MAC 不变）。 */
    uint8_t mac[6] = {0};
    if (esp_read_mac(mac, ESP_MAC_WIFI_STA) == ESP_OK)
        ESP_LOGI(TAG, "board MAC %02X:%02X:%02X:%02X:%02X:%02X",
                 mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    /* 回滚确认必须在点屏之前。深睡唤醒即复位，bootloader 会把 PENDING_VERIFY 镜像
     * 回滚掉；确认点若落在 eink_init 之后，一旦面板没电/无响应（BUSY 死等 8s 才返回），
     * 这 8s + 前置初始化会逼近 bootloader 回滚超时（默认约 10s），恰好在新镜像最需要
     * 活下来的那一开机把它丢弃。能跑到 app_main 且网络栈已起 = 保命证据，先确认再点屏。 */
    esp_err_t rollback_e = esp_ota_mark_app_valid_cancel_rollback();
    if (rollback_e != ESP_OK) ESP_LOGW(TAG, "mark app valid failed: %s", esp_err_to_name(rollback_e));

    eink_init();  /* 之后任何故障都能在面板留痕 */

    volume_guard_init(12, 1, 600);
    power_policy_defaults(&s_policy);
    offline_store_init();
    buttons_init();

    /* 现场配网闸门：三种"没有可用 WiFi 凭据"都进门户，绝不能死循环卡在屏前——
     *   ①完全没配过（无 passkey）②只配了 passkey 没配 WiFi/server（半截配置）
     *   ③有 passkey 但 ready_for_sta 为假 → 若不进 AP 又不跑 STA，会既无门户外观也无网络，静默死锁。
     * 门户等待有超时；超时后深睡，等定时/按键唤醒再试，不空转烧电。 */
    nvs_creds_load(&s_creds);
    /* 恢复性：连续登录失败到阈值，即便凭据看起来齐全也强制回到门户，
     * 否则"凭据存在但不可用"会让设备每天白跑一轮却再也进不了配网（现场不可救）。 */
    bool force_gate = nvs_creds_ready_for_sta(&s_creds) && load_bad_login() >= GATE_BAD_MAX;
    if (force_gate) eink_show_message("联网连续失败，请重新配网");
    if (!nvs_creds_ready_for_sta(&s_creds) || force_gate) {
        if (!force_gate) eink_show_message("请现场配网");
        if (provision_ap_start()) {
            if (provision_ap_wait_done(1800)) {   /* 最多等 30 分钟现场配网 */
                provision_ap_stop();
                clear_bad_login();                /* 新凭据已保存，给一次干净尝试 */
                offline_store_flush();            /* 重启前落盘，别留脏 FATFS 窗口 */
                esp_restart();                    /* 重启走正常 STA 流程 */
            }
            /* 超时未配网：停门户、落盘、深睡，等待唤醒重试 */
            provision_ap_stop();
        } else {
            /* 门户起不来（WiFi 驱动异常）：不能无限等，深睡后重来 */
            ESP_LOGE(TAG, "provision_ap_start failed");
        }
        /* 消抖：强制闸门（因连续登录失败触发）在超时后把计数清零，下次唤醒改用
         * 现有凭据重试 STA。否则一次 router 重启/一晚服务器维护把 badlogin 顶到阈值，
         * 而闸门分支又永远走不到登录代码去清零 → 永久锁死配网、再也不用时有效凭据。
         * 真凭据坏了也只是回到"每 6h 试一次→失败 3 次→再开门户"的自愈节奏。 */
        clear_bad_login();
        offline_store_flush();
        esp_sleep_enable_timer_wakeup(21600ULL * 1000000ULL); /* 6h 后再给一次机会 */
        eink_sleep(); /* 深睡前锁帧并让墨水屏进 sleep，配网提示靠双稳态留在屏上 */
        esp_deep_sleep_start();
    }

    clock_tz_init();  /* 先把时区设对，后面 localtime_r 才是北京时间 */

    if (wifi_sta_start(&s_creds)) {
        /* 先等 IP，最多 ~15s。没拿到 IP 属纯射频/热点故障（router 重启、AP 不在范围），
         * 绝不能记成凭据错误去 bump_bad_login，否则网络抖一抖就把设备锁进配网。 */
        bool got_ip = s_sta_got_ip;
        for (int i = 0; i < 30 && !got_ip; i++) {
            vTaskDelay(pdMS_TO_TICKS(500));
            got_ip = s_sta_got_ip;
        }
        if (got_ip) {
            /* 校时：SNTP 优先；校园网常封 UDP 123，失败立刻走 HTTP 兜底。
             * 校园网里 SNTP 失败的几率不低，这一步不能省，否则日期会是 1970 或错一天。 */
            if (!clock_sync_sntp()) {
                clock_sync_http(s_creds.server_url);
            }
            if (!clock_is_synced()) {
                time_t stash = clock_stash_load();
                if (stash > 0) {
                    struct timeval tv = {.tv_sec = stash, .tv_usec = 0};
                    settimeofday(&tv, NULL);
                    ESP_LOGW(TAG, "using stashed time (may be stale)");
                }
            }
            if (net_http_login(&s_creds, s_sid, sizeof(s_sid))) {
                clear_bad_login();
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
            } else {
                bump_bad_login();   /* 拿到 IP 却登录失败=口令/服务器问题：计入，达阈值后下次开机回门户 */
            }
        } else {
            ESP_LOGW(TAG, "no IP after connect, staying offline (not charged as cred failure)");
        }
    } else {
        /* 本地射频起不来（驱动/PHY 异常）：凭据看着齐全却永远进不了门户也连不上，
         * 计入坏登录让下次强制回门户，避免"有凭据+射频死"每天白跑却不可恢复。 */
        bump_bad_login();
    }

    refresh_clock_page();
    int last_min = -1;
    {
        time_t seed = time(NULL);
        struct tm seedtm;
        localtime_r(&seed, &seedtm);
        last_min = seedtm.tm_min;
    }
    int64_t last_eink_us = esp_timer_get_time();
    bool ota_checked_this_boot = false;

    for (;;) {
        handle_button(buttons_poll());
        s_vol = volume_guard_tick();

        time_t now = time(NULL);
        struct tm tmv;
        localtime_r(&now, &tmv);
        int64_t now_us = esp_timer_get_time();
        bool minute_changed = (tmv.tm_min != last_min);
        /* 未校时阶段也要刷（校准后能立刻换成真实日期），但节流到 ≥30s 一次：
         * 循环尾只有 200ms，未校时若无条件刷 = 每 200ms 全刷，真驱动会压垮面板且秒级阻塞主循环。 */
        bool unsync_due = (!clock_is_synced() && (now_us - last_eink_us) > 30LL * 1000000LL);
        if (minute_changed || unsync_due) {
            last_min = tmv.tm_min;
            last_eink_us = now_us;
            refresh_clock_page();
        }

        if (power_policy_should_sleep(&s_policy, now, s_boot_us, s_last_act_us)) {
            graceful_shutdown();
        }

        /* 每次开机查一次固件（设备每日定时唤醒 → 天然形成每日检查节奏）。
         * 不能按“连续运行 6h”判：深睡唤醒后 esp_timer 归零，那样永远不触发。
         * 开机 2 分钟后再查，避开初始同步；正在播放时不打扰。 */
        if (s_sid[0] && !ota_checked_this_boot && !s_playing &&
            (esp_timer_get_time() - s_boot_us) > 120LL * 1000000LL) {
            ota_checked_this_boot = true;
            ota_bg_check_and_update(s_sid, s_creds.server_url);
        }

        if (s_playing && s_audio_ready) {
            mark_act();
            /* TODO: I2S 下一段 MP3 */
        }
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}
