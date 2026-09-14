#include "ota_bg.h"
#include <string.h>
#include <stdio.h>
#include "esp_http_client.h"
#include "esp_ota_ops.h"
#include "esp_https_ota.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "ota_bg";
static bool s_pending_reboot = false;
static char s_err[96];

const char *ota_bg_last_error(void) { return s_err; }
bool ota_bg_pending_reboot(void) { return s_pending_reboot; }

/*
 * 策略：
 * - 无任何 UI 入口（不映射按键、不暴露菜单）
 * - 仅在：已登录 + 空闲 + 电量/网络可接受时后台拉 version
 * - 服务端约定 GET /api/device/firmware/latest
 *   {"version":"1.2.0","url":"https://.../firmware.bin","sha256":"..."}
 * - 骨架：对比 NVS 中 version，不同则 HTTPS OTA；失败记 s_err，不打断播放
 */
static bool fetch_latest_version(const char *sid, const char *server, char *ver, size_t n, char *url, size_t un)
{
    char u[192];
    snprintf(u, sizeof(u), "%s/api/device/firmware/latest", server);
    esp_http_client_config_t cfg = {
        .url = u,
        .timeout_ms = 15000,
    };
    esp_http_client_handle_t c = esp_http_client_init(&cfg);
    char cookie[160];
    snprintf(cookie, sizeof(cookie), "zsid=%s", sid ? sid : "");
    esp_http_client_set_header(c, "Cookie", cookie);
    esp_err_t e = esp_http_client_perform(c);
    int st = esp_http_client_get_status_code(c);
    bool ok = false;
    if (e == ESP_OK && st == 200) {
        char buf[512] = {0};
        int r = esp_http_client_read(c, buf, sizeof(buf) - 1);
        if (r > 0) {
            const char *v = strstr(buf, "\"version\"");
            const char *uu = strstr(buf, "\"url\"");
            if (v) {
                v = strchr(v + 9, '"');
                if (v) {
                    const char *e2 = strchr(v + 1, '"');
                    if (e2) {
                        size_t ln = (size_t)(e2 - v - 1);
                        if (ln >= n) ln = n - 1;
                        memcpy(ver, v + 1, ln);
                        ver[ln] = 0;
                    }
                }
            }
            if (uu) {
                uu = strchr(uu + 4, '"');
                if (uu) {
                    const char *e2 = strchr(uu + 1, '"');
                    if (e2) {
                        size_t ln = (size_t)(e2 - uu - 1);
                        if (ln >= un) ln = un - 1;
                        memcpy(url, uu + 1, ln);
                        url[ln] = 0;
                    }
                }
            }
            ok = ver[0] && url[0];
        }
    }
    esp_http_client_cleanup(c);
    return ok;
}

bool ota_bg_check_and_update(const char *sid, const char *server)
{
    s_err[0] = 0;
    if (!sid || !server) {
        snprintf(s_err, sizeof(s_err), "not_logged_in");
        return false;
    }
    char ver[32] = {0};
    char url[160] = {0};
    if (!fetch_latest_version(sid, server, ver, sizeof(ver), url, sizeof(url))) {
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
        return false;
    }
    ESP_LOGW(TAG, "bg OTA %s -> %s (no user UI)", desc.version, ver);
    esp_http_client_config_t http = {
        .url = url,
        .cert_pem = NULL, /* 内网 HTTP 可接受；公网应钉证书 */
        .timeout_ms = 60000,
        .keep_alive_enable = true,
    };
    esp_https_ota_config_t ota = { .http_config = &http };
    esp_err_t e = esp_https_ota(&ota);
    if (e != ESP_OK) {
        snprintf(s_err, sizeof(s_err), "ota_fail_%d", (int)e);
        ESP_LOGE(TAG, "bg OTA failed %d", e);
        return false;
    }
    s_pending_reboot = true;
    ESP_LOGW(TAG, "bg OTA ok, rebooting");
    esp_restart();
    return true;
}
