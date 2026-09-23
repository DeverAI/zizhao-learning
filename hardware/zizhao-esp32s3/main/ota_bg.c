#include "ota_bg.h"
#include <string.h>
#include <stdio.h>
#include "esp_http_client.h"
#include "esp_ota_ops.h"
#include "esp_https_ota.h"
#include "esp_log.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "net_http.h"
#include "offline_store.h"

static const char *TAG = "ota_bg";
static bool s_pending_reboot = false;
static char s_err[96];

const char *ota_bg_last_error(void) { return s_err; }
bool ota_bg_pending_reboot(void) { return s_pending_reboot; }

/* 退避：每个目标版本单独计数，累计尝试（含下载成功但版本仍不匹配的情况）到上限后冻结，
 * 避免"版本永远追不平 → 每次唤醒重下 3MB"把 flash 寿命和电池耗光。
 * namespace "otafail"，键 = 'c'+版本 crc32 十六进制（≤9 字符，NVS 上限 15）。
 * 只有当前镜像版本已等于服务端版本（up-to-date）才清掉该版本自己的计数。 */
#define OTA_FAIL_NS   "otafail"
#define OTA_FAIL_MAX  3

static uint32_t ota_crc32(const char *s)
{
    uint32_t crc = 0xFFFFFFFFu;
    for (; *s; s++) {
        crc ^= (uint8_t)*s;
        for (int i = 0; i < 8; i++)
            crc = (crc >> 1) ^ (0xEDB88320u & (uint32_t)(-(int32_t)(crc & 1)));
    }
    return ~crc;
}

static void ota_fail_key(const char *ver, char *out, size_t n)
{
    snprintf(out, n, "c%08lx", (unsigned long)ota_crc32(ver));
}

static int ota_fail_count_for(const char *ver)
{
    char key[16];
    ota_fail_key(ver, key, sizeof(key));
    nvs_handle_t h;
    if (nvs_open(OTA_FAIL_NS, NVS_READONLY, &h) != ESP_OK) return 0;
    int32_t cnt = 0;
    nvs_get_i32(h, key, &cnt);
    nvs_close(h);
    return (int)cnt;
}

/* 在下载真正开始前调用：无论这轮 esp_https_ota 成功与否，都算"对这个版本试过一次"。 */
static void ota_fail_bump(const char *ver)
{
    char key[16];
    ota_fail_key(ver, key, sizeof(key));
    nvs_handle_t h;
    if (nvs_open(OTA_FAIL_NS, NVS_READWRITE, &h) != ESP_OK) return;
    int32_t cnt = 0;
    nvs_get_i32(h, key, &cnt);
    cnt++;
    nvs_set_i32(h, key, cnt);
    nvs_commit(h);
    nvs_close(h);
}

/* 清掉"当前正在跑的这个版本"的退避计数。up-to-date 分支每次开机都会走到，
 * 用 nvs_erase_key 命中已存在的键才 commit：命名空间为空时不产生任何 flash 写，
 * 避免"每天一开机就 erase_all+commit"白白磨损 NVS。 */
static void ota_fail_clear_for(const char *ver)
{
    char key[16];
    ota_fail_key(ver, key, sizeof(key));
    nvs_handle_t h;
    if (nvs_open(OTA_FAIL_NS, NVS_READWRITE, &h) != ESP_OK) return;
    if (nvs_erase_key(h, key) == ESP_OK) nvs_commit(h);
    nvs_close(h);
}

/*
 * 策略：
 * - 无任何 UI 入口（不映射按键、不暴露菜单）
 * - 仅登录后台拉 version（每次开机查一次，见 main.c 触发节奏）
 * - 服务端契约 GET /api/device/firmware/latest（带 zsid Cookie）
 *   {"version":"1.2.0","url":"/api/device/firmware/bin","sha256":"..."}
 *   url 允许相对路径，本模块用 server_url 补成绝对地址。
 * - 版本比对用镜像 esp_app_desc.version（来自 CMake 的 PROJECT_VER），
 *   与 manifest 不同才 OTA；发版须同步改 PROJECT_VER 与 manifest。
 * - esp_https_ota 内部自己 init/cleanup client，本模块不得再持有句柄。
 */

/* esp_https_ota 的 client 由它内部 init；v5.1 的 init_cb 无 user_ctx，
 * 故 Cookie 串放 file-static，在 cb 里注入（这是唯一能加自定义头的钩子）。 */
static char s_ota_cookie[176];
static esp_err_t ota_http_init_cb(esp_http_client_handle_t client)
{
    if (s_ota_cookie[0]) esp_http_client_set_header(client, "Cookie", s_ota_cookie);
    return ESP_OK;
}

/* 从扁平 JSON 里取字符串字段（与 power_policy 同风格，不引 cJSON）。 */
static bool json_str_field(const char *buf, const char *key, char *out, size_t n)
{
    char pat[40];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char *k = strstr(buf, pat);
    if (!k) return false;
    const char *c = strchr(k, ':');
    if (!c) return false;
    const char *s = strchr(c, '"');
    if (!s) return false;
    const char *e = strchr(s + 1, '"');
    if (!e) return false;
    size_t ln = (size_t)(e - s - 1);
    if (ln >= n) ln = n - 1;
    memcpy(out, s + 1, ln);
    out[ln] = 0;
    return true;
}

static bool fetch_latest_version(const char *sid, const char *server, char *ver, size_t n, char *url, size_t un)
{
    char u[192];
    snprintf(u, sizeof(u), "%s/api/device/firmware/latest", server);
    char buf[512] = {0};
    /* 复用 net_http_get：带 zsid Cookie，且 body 累积正确
     * （不能 esp_http_client_perform 后再 read，那样恒空）。 */
    if (!net_http_get(u, buf, sizeof(buf), sid)) {
        ESP_LOGW(TAG, "latest fetch failed (net/401/404)");
        return false;
    }
    if (!json_str_field(buf, "version", ver, n)) return false;
    if (!json_str_field(buf, "url", url, un)) return false;
    return ver[0] && url[0];
}

bool ota_bg_check_and_update(const char *sid, const char *server)
{
    s_err[0] = 0;
    s_ota_cookie[0] = 0;
    if (!sid || !sid[0] || !server || !server[0]) {
        snprintf(s_err, sizeof(s_err), "not_logged_in");
        return false;
    }
    char ver[32] = {0};
    char raw_url[160] = {0};
    if (!fetch_latest_version(sid, server, ver, sizeof(ver), raw_url, sizeof(raw_url))) {
        snprintf(s_err, sizeof(s_err), "no_firmware_manifest");
        return false; /* 服务端未开 OTA 接口时静默跳过 */
    }
    const esp_partition_t *run = esp_ota_get_running_partition();
    esp_app_desc_t desc;
    if (esp_ota_get_partition_description(run, &desc) != ESP_OK) {
        snprintf(s_err, sizeof(s_err), "no_app_desc");
        return false;
    }
    if (strncmp(desc.version, ver, sizeof(desc.version)) == 0) {
        ESP_LOGI(TAG, "firmware up to date %s", desc.version);
        ota_fail_clear_for(ver);   /* 已跑上目标版本，清掉它自己的退避计数 */
        return false;
    }
    /* 当前镜像仍是 PENDING_VERIFY（开机那次 mark_valid 没成/还没到稳态）：
     * 说明上一次 OTA 的新镜像尚未被确认，此时再叠一次 OTA 可能把设备堆到
     * 连续回滚，跳过本轮，等下次稳态确认后再比版本。 */
    esp_ota_img_states_t st;
    if (esp_ota_get_state_partition(run, &st) == ESP_OK && st == ESP_OTA_IMG_PENDING_VERIFY) {
        snprintf(s_err, sizeof(s_err), "ota_pending_verify");
        ESP_LOGW(TAG, "running image still PENDING_VERIFY, skip OTA");
        return false;
    }
    /* 同一目标版本已连续失败到上限：冻结，等版本再变（下次服务端发新 ver 自动解锁）。 */
    if (ota_fail_count_for(ver) >= OTA_FAIL_MAX) {
        snprintf(s_err, sizeof(s_err), "ota_backoff");
        ESP_LOGW(TAG, "OTA to %s frozen after %d fails", ver, OTA_FAIL_MAX);
        return false;
    }
    /* 相对 url 补成绝对：esp_http_client 需要带 scheme+host。拼不下就放弃，
     * 别拿被截断的坏 URL 去 OTA。 */
    char full_url[224];
    int wr;
    if (raw_url[0] == '/') {
        wr = snprintf(full_url, sizeof(full_url), "%s%s", server, raw_url);
    } else {
        wr = snprintf(full_url, sizeof(full_url), "%s", raw_url);
    }
    if (wr < 0 || wr >= (int)sizeof(full_url)) {
        snprintf(s_err, sizeof(s_err), "url_too_long");
        ESP_LOGE(TAG, "OTA url too long (%d)", wr);
        return false;
    }
    if (snprintf(s_ota_cookie, sizeof(s_ota_cookie), "zsid=%s", sid) >= (int)sizeof(s_ota_cookie)) {
        s_ota_cookie[0] = 0;
        snprintf(s_err, sizeof(s_err), "sid_too_long");
        return false;
    }
    ESP_LOGW(TAG, "bg OTA %s -> %s (no user UI): %s", desc.version, ver, full_url);

    esp_http_client_config_t http = {
        .url = full_url,
        .cert_pem = NULL, /* 内网 HTTP 可接受（CONFIG_ESP_HTTPS_OTA_ALLOW_HTTP=y）；公网应钉证书 */
        .timeout_ms = 60000,
        .keep_alive_enable = true,
    };
    esp_https_ota_config_t ota = {
        .http_config = &http,
        .http_client_init_cb = ota_http_init_cb, /* 注入 zsid Cookie，否则 /firmware/bin 会 401 */
    };
    /* 下载开始前先计一次尝试：即便 esp_https_ota 返回成功但新镜像版本仍不匹配，
     * 下个唤醒周期也会因该计数到顶而冻结，杜绝"版本追不平 → 无限重下 3MB"。 */
    ota_fail_bump(ver);
    esp_err_t e = esp_https_ota(&ota); /* 内部完成 client init + cleanup */
    s_ota_cookie[0] = 0;
    if (e != ESP_OK) {
        snprintf(s_err, sizeof(s_err), "ota_fail_%s", esp_err_to_name(e));
        ESP_LOGE(TAG, "bg OTA failed %s (attempts for %s now %d)", esp_err_to_name(e), ver, ota_fail_count_for(ver));
        return false;
    }
    s_pending_reboot = true;
    /* 注意：这里故意不清计数。下载成功≠新镜像版本已对上；
     * 新镜像起来后若真 up-to-date，会在上面那条分支里 clear_all。 */
    ESP_LOGW(TAG, "bg OTA ok, rebooting");
    offline_store_flush();  /* 重启前把 SD 写缓存落盘，避免半截文件 */
    esp_restart();
    return true;
}
