#include "net_http.h"
#include <stdio.h>
#include <string.h>
#include "esp_http_client.h"
#include "esp_log.h"

static const char *TAG = "net";

/* esp_http_client_perform() 会在内部读完 body 并以 HTTP_EVENT_ON_DATA 回调；
 * perform 之后再 esp_http_client_read() 只会拿到 0（体已被读空）。
 * 因此响应体必须在这里累积进调用方缓冲，out 为空时不收集。 */
typedef struct {
    char  *buf;
    size_t cap;
    size_t len;
} http_buf_t;

static esp_err_t http_event(esp_http_client_event_t *evt)
{
    if (evt->event_id == HTTP_EVENT_ON_DATA && evt->user_data && evt->data_len > 0) {
        http_buf_t *hb = (http_buf_t *)evt->user_data;
        size_t avail = (hb->cap > hb->len + 1) ? (hb->cap - hb->len - 1) : 0;
        size_t n = ((size_t)evt->data_len < avail) ? (size_t)evt->data_len : avail;
        if (n > 0) {
            memcpy(hb->buf + hb->len, evt->data, n);
            hb->len += n;
            hb->buf[hb->len] = 0;
        }
    }
    return ESP_OK;
}

static bool http_post_json(const char *url, const char *body, char *out, size_t out_len, const char *sid)
{
    http_buf_t hb = { .buf = out, .cap = out_len, .len = 0 };
    esp_http_client_config_t cfg = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .event_handler = http_event,
        .user_data = (out && out_len) ? &hb : NULL,
        .timeout_ms = 20000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) { ESP_LOGE(TAG, "POST init fail %s", url); return false; }
    esp_http_client_set_header(client, "Content-Type", "application/json");
    if (sid && sid[0]) {
        char cookie[160];
        snprintf(cookie, sizeof(cookie), "zsid=%s", sid);
        esp_http_client_set_header(client, "Cookie", cookie);
    }
    esp_http_client_set_post_field(client, body, strlen(body));
    esp_err_t err = esp_http_client_perform(client);
    int status = esp_http_client_get_status_code(client);
    if (err != ESP_OK || status < 200 || status >= 300) {
        ESP_LOGW(TAG, "POST %s -> err=%d status=%d", url, err, status);
    }
    esp_http_client_cleanup(client);
    return err == ESP_OK && status >= 200 && status < 300;
}

bool net_http_get(const char *url, char *out, size_t out_len, const char *sid)
{
    http_buf_t hb = { .buf = out, .cap = out_len, .len = 0 };
    if (out && out_len) out[0] = 0;
    esp_http_client_config_t cfg = {
        .url = url,
        .method = HTTP_METHOD_GET,
        .event_handler = http_event,
        .user_data = (out && out_len) ? &hb : NULL,
        .timeout_ms = 20000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) { ESP_LOGE(TAG, "GET init fail %s", url); return false; }
    if (sid && sid[0]) {
        char cookie[160];
        snprintf(cookie, sizeof(cookie), "zsid=%s", sid);
        esp_http_client_set_header(client, "Cookie", cookie);
    }
    esp_err_t err = esp_http_client_perform(client);
    int status = esp_http_client_get_status_code(client);
    bool ok = (err == ESP_OK && status >= 200 && status < 300);
    esp_http_client_cleanup(client);
    return ok;
}

bool net_http_login(const zizhao_creds_t *c, char *sid_out, size_t sid_len)
{
    if (!c || !sid_out) return false;
    char url[192];
    snprintf(url, sizeof(url), "%s/api/auth/device/login", c->server_url);
    char body[200];
    snprintf(body, sizeof(body), "{\"device_id\":\"%s\",\"passkey\":\"%s\"}", c->device_id, c->passkey);
    char resp[512] = {0};
    if (!http_post_json(url, body, resp, sizeof(resp), NULL)) return false;
    /* {"ok":true,"sid":"...."} */
    const char *s = strstr(resp, "\"sid\"");
    if (!s) return false;
    s = strchr(s, ':');
    if (!s) return false;
    s = strchr(s + 1, '"');
    if (!s) return false;
    const char *e = strchr(s + 1, '"');
    if (!e) return false;
    size_t n = (size_t)(e - (s + 1));
    if (n >= sid_len) n = sid_len - 1;
    memcpy(sid_out, s + 1, n);
    sid_out[n] = 0;
    return true;
}

bool net_http_get_bundle(const char *sid, const char *server, char *buf, size_t buf_len)
{
    char url[192];
    snprintf(url, sizeof(url), "%s/api/offline/bundle", server);
    return net_http_get(url, buf, buf_len, sid);
}

bool net_http_report_progress(const char *sid, const char *server, int material_id_hash, int seg, int offset_ms)
{
    char url[192];
    snprintf(url, sizeof(url), "%s/api/material/progress", server);
    char body[160];
    snprintf(body, sizeof(body),
             "{\"material_id\":\"%08x\",\"segment_index\":%d,\"offset_ms\":%d,\"finished\":false}",
             material_id_hash, seg, offset_ms);
    return http_post_json(url, body, NULL, 0, sid);
}

bool net_http_get_power_policy(const char *sid, const char *server, char *buf, size_t buf_len)
{
    char url[192];
    snprintf(url, sizeof(url), "%s/api/device/power", server);
    return net_http_get(url, buf, buf_len, sid);
}
