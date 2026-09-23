#include "nvs_creds.h"
#include <string.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"

static const char *TAG = "nvs_creds";
#define NS "zizhao"

static bool get_str(nvs_handle_t h, const char *key, char *out, size_t n)
{
    size_t len = n;
    esp_err_t e = nvs_get_str(h, key, out, &len);
    return e == ESP_OK;
}

bool nvs_creds_load(zizhao_creds_t *out)
{
    if (!out) return false;
    memset(out, 0, sizeof(*out));
    nvs_handle_t h;
    if (nvs_open(NS, NVS_READONLY, &h) != ESP_OK) return false;
    get_str(h, "device_id", out->device_id, sizeof(out->device_id));
    get_str(h, "passkey", out->passkey, sizeof(out->passkey));
    get_str(h, "server_url", out->server_url, sizeof(out->server_url));
    get_str(h, "wifi_ssid", out->wifi_ssid, sizeof(out->wifi_ssid));
    get_str(h, "wifi_pass", out->wifi_pass, sizeof(out->wifi_pass));
    nvs_close(h);
    return true;
}

bool nvs_creds_save(const zizhao_creds_t *in)
{
    if (!in) return false;
    nvs_handle_t h;
    if (nvs_open(NS, NVS_READWRITE, &h) != ESP_OK) return false;
    /* 每个 set 单独判返回：任一失败就中止，别把"半套新凭据 + 半套旧值"存进去。 */
    esp_err_t e;
    bool ok = true;
    ok &= ((e = nvs_set_str(h, "device_id",  in->device_id))  == ESP_OK);
    ok &= ((e = nvs_set_str(h, "passkey",    in->passkey))    == ESP_OK);
    ok &= ((e = nvs_set_str(h, "server_url", in->server_url)) == ESP_OK);
    ok &= ((e = nvs_set_str(h, "wifi_ssid",  in->wifi_ssid))  == ESP_OK);
    ok &= ((e = nvs_set_str(h, "wifi_pass",  in->wifi_pass))  == ESP_OK);
    if (!ok) { ESP_LOGE(TAG, "nvs_set_str failed: %s", esp_err_to_name(e)); nvs_close(h); return false; }
    if (nvs_commit(h) != ESP_OK) { nvs_close(h); return false; }
    nvs_close(h);

    /* 回读校验：nvs_set_str/commit 都成功也可能因空间不足静默丢写；
     * 只有落盘值和来值逐字段相等，才让调用方把设备标记为"已配好并重启"。 */
    zizhao_creds_t rb;
    if (!nvs_creds_load(&rb)) return false;
    return strcmp(rb.device_id, in->device_id) == 0 &&
           strcmp(rb.passkey, in->passkey) == 0 &&
           strcmp(rb.server_url, in->server_url) == 0 &&
           strcmp(rb.wifi_ssid, in->wifi_ssid) == 0 &&
           strcmp(rb.wifi_pass, in->wifi_pass) == 0;
}

bool nvs_creds_has_passkey(const zizhao_creds_t *c)
{
    return c && c->device_id[0] && c->passkey[0];
}

bool nvs_creds_ready_for_sta(const zizhao_creds_t *c)
{
    return nvs_creds_has_passkey(c) && c->wifi_ssid[0] && c->server_url[0];
}
