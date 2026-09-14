#include "nvs_creds.h"
#include <string.h>
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
    nvs_set_str(h, "device_id", in->device_id);
    nvs_set_str(h, "passkey", in->passkey);
    nvs_set_str(h, "server_url", in->server_url);
    nvs_set_str(h, "wifi_ssid", in->wifi_ssid);
    nvs_set_str(h, "wifi_pass", in->wifi_pass);
    esp_err_t e = nvs_commit(h);
    nvs_close(h);
    return e == ESP_OK;
}

bool nvs_creds_has_passkey(const zizhao_creds_t *c)
{
    return c && c->device_id[0] && c->passkey[0];
}

bool nvs_creds_ready_for_sta(const zizhao_creds_t *c)
{
    return nvs_creds_has_passkey(c) && c->wifi_ssid[0] && c->server_url[0];
}
