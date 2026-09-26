#include "provision_ap.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_mac.h"
#include "esp_http_server.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_creds.h"
#include "eink_display.h"
#include "buttons.h"          /* R61：配网窗口那 30 分钟里按键只有这里在读 */

static const char *TAG = "prov";
static volatile bool s_done = false;
static httpd_handle_t s_server = NULL;
static bool s_ap_started = false;

/* 配网热点口令：仅供现场配网临时使用；设备绑定仍需 device_id+passkey，
 * 光连上热点没有 passkey 也拿不到任何素材。口令串口会打印一次。 */
#define PROV_PASS "zizhao1234"

static int hexval(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* application/x-www-form-urlencoded 解码：'+'→空格，%XX→字节。
 * 密码里的 & % = # 等都以 %XX 传入，故按 '&' 切分字段是安全的。 */
static void url_decode(const char *src, size_t slen, char *dst, size_t dcap)
{
    size_t o = 0;
    for (size_t i = 0; i < slen && src[i]; i++) {
        char c = src[i];
        if (c == '+') c = ' ';
        else if (c == '%' && i + 2 < slen) {
            int h = hexval(src[i + 1]), l = hexval(src[i + 2]);
            if (h >= 0 && l >= 0) { c = (char)((h << 4) | l); i += 2; }
        }
        if (o + 1 >= dcap) break;
        dst[o++] = c;
    }
    dst[o] = 0;
}

/* 从 body 里取某字段（URL 解码进 out）。返回 true=找到且非空。 */
static bool form_get(const char *body, const char *key, char *out, size_t n)
{
    if (n == 0) return false;   /* 否则下面 strncpy(out,tmp,n-1) 与 out[n-1] 会越界写到 out[-1] */
    size_t klen = strlen(key);
    const char *p = body;
    out[0] = 0;
    while (p && *p) {
        if (!strncmp(p, key, klen) && p[klen] == '=') {
            const char *val = p + klen + 1;
            const char *amp = strchr(val, '&');
            size_t vlen = amp ? (size_t)(amp - val) : strlen(val);
            char tmp[192];
            if (vlen >= sizeof(tmp)) vlen = sizeof(tmp) - 1;
            url_decode(val, vlen, tmp, sizeof(tmp));
            if (tmp[0]) {
                strncpy(out, tmp, n - 1);
                out[n - 1] = 0;
                return true;
            }
            return false;
        }
        const char *next = strchr(p, '&');
        if (!next) break;
        p = next + 1;
    }
    return false;
}

static const char *FORM_HTML =
    "<!doctype html><meta charset=utf-8><title>自招学习 配网</title>"
    "<meta name=viewport content='width=device-width,initial-scale=1'>"
    "<h3>自招学习 · 现场配网</h3><form method=POST action=/save>"
    "WiFi 名称 <input name=ssid><br>WiFi 密码 <input name=pass type=password><br>"
    "服务器地址 <input name=server placeholder='http://192.168.1.10:8010'><br>"
    "设备号 device_id <input name=device_id><br>"
    "口令 passkey <input name=passkey><br>"
    "<br><button type=submit>保存并联网</button></form>"
    "<p style='color:#888;font-size:12px'>留空的字段保持原值；配网完成后设备自动重启。</p>";

static esp_err_t root_get(httpd_req_t *req)
{
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    httpd_resp_send(req, FORM_HTML, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

static esp_err_t save_post(httpd_req_t *req)
{
    char body[1024];
    int cap = (int)sizeof(body) - 1;
    int off = 0;
    while (off < cap) {
        int r = httpd_req_recv(req, body + off, cap - off);
        if (r <= 0) { off += (r < 0) ? 0 : r; break; }  /* r<0：超时/错误，保留已读字节后退出 */
        off += r;
    }
    body[off] = 0;

    /* 必须拿到完整 body 再解析：Content-Length 比读到的多，说明最后一个字段（passkey）
     * 被截断，存进去就是错凭据，还会让闸门误判"已配好"而永久关闭自救入口。
     * 用"正向断言"：只有 clen>0 且正好读满 clen 且没撑爆缓冲才算完整。
     * httpd 对无 body/chunked 会把 content_len 归一为 0，此时一律视为不完整并拒绝，
     * 绝不在拿不准时把残 body 当成品写进 NVS。 */
    int clen = (int)req->content_len;   /* esp_http_server 无 getter，长度在 req->content_len */
    bool truncated = !(clen > 0 && off == clen && clen < (int)sizeof(body));

    zizhao_creds_t c;
    nvs_creds_load(&c); /* 先读旧值，提交里留空的字段保持原值 */
    char f[160];
    bool touched = false;
    if (!truncated) {
        if (form_get(body, "ssid", f, sizeof(f))) { strncpy(c.wifi_ssid, f, sizeof(c.wifi_ssid) - 1); touched = true; }
        if (form_get(body, "pass", f, sizeof(f))) { strncpy(c.wifi_pass, f, sizeof(c.wifi_pass) - 1); touched = true; }
        if (form_get(body, "server", f, sizeof(f))) { strncpy(c.server_url, f, sizeof(c.server_url) - 1); touched = true; }
        if (form_get(body, "device_id", f, sizeof(f))) { strncpy(c.device_id, f, sizeof(c.device_id) - 1); touched = true; }
        if (form_get(body, "passkey", f, sizeof(f))) { strncpy(c.passkey, f, sizeof(c.passkey) - 1); touched = true; }
    } else {
        ESP_LOGW(TAG, "portal body truncated (got %d, clen %d) — reject", off, clen);
    }

    httpd_resp_set_type(req, "text/html; charset=utf-8");
    if (touched && nvs_creds_save(&c)) {
        s_done = true;
        ESP_LOGI(TAG, "creds saved via portal");
        httpd_resp_sendstr(req, "<meta charset=utf-8>已保存，设备即将重启联网…");
    } else {
        httpd_resp_sendstr(req, "<meta charset=utf-8>未收到完整字段或保存失败，请重试。");
    }
    return ESP_OK;
}

static bool portal_start(void)
{
    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    /* 手机连 captive AP 会并发开多个 socket（页面 + favicon + 系统连通性探测），
     * 槽满且无 LRU 时会拒绝新连接 → 门户彻底打不开。开 LRU 淘汰并多给两个槽。 */
    cfg.max_open_sockets = 5;
    cfg.lru_purge_enable = true;
    cfg.stack_size = 6144;
    s_server = NULL;
    if (httpd_start(&s_server, &cfg) != ESP_OK) {
        ESP_LOGE(TAG, "httpd_start failed (OOM?)");
        return false;
    }
    httpd_uri_t root = { .uri = "/", .method = HTTP_GET, .handler = root_get };
    httpd_uri_t save = { .uri = "/save", .method = HTTP_POST, .handler = save_post };
    /* 注册失败要如实报错：否则门户"起得来但什么都不应答"，还会白占 30 分钟射频。 */
    if (httpd_register_uri_handler(s_server, &root) != ESP_OK ||
        httpd_register_uri_handler(s_server, &save) != ESP_OK) {
        ESP_LOGE(TAG, "uri handler register failed");
        httpd_stop(s_server);
        s_server = NULL;
        return false;
    }
    return true;
}

bool provision_ap_start(void)
{
    if (s_ap_started) return true; /* 幂等：重复调用不重建 netif/httpd */

    /* WiFi 驱动必须先 init，AP netif 的 glue 会注册 RX handler；
     * 反过来（先建 netif 再 init）会返回 ESP_ERR_INVALID_STATE 并 panic。 */
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t e = esp_wifi_init(&cfg);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "esp_wifi_init failed: %s", esp_err_to_name(e));
        return false;
    }
    if (!esp_netif_create_default_wifi_ap()) {
        ESP_LOGE(TAG, "create ap netif failed");
        return false;
    }

    wifi_config_t ap = {0};
    uint8_t mac[6] = {0};
    if (esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP) != ESP_OK)
        esp_wifi_get_mac(WIFI_IF_AP, mac);
    snprintf((char *)ap.ap.ssid, sizeof(ap.ap.ssid), "Zizhao-Setup-%02X%02X", mac[4], mac[5]);
    ap.ap.ssid_len = strlen((char *)ap.ap.ssid);
    ap.ap.channel = 6;
    ap.ap.max_connection = 4;
    ap.ap.authmode = WIFI_AUTH_WPA2_PSK; /* 不再是开放网络 */
    strncpy((char *)ap.ap.password, PROV_PASS, sizeof(ap.ap.password) - 1);

    /* AP 路径也不许 panic：这条正是"救回一台没配过网设备"的唯一自救通道，
     * 一旦 abort 就是复位循环，只能拆机重烧。失败返回 false，交给闸门深睡退避兜。 */
    if ((e = esp_wifi_set_mode(WIFI_MODE_AP)) != ESP_OK) { ESP_LOGE(TAG, "ap set_mode: %s", esp_err_to_name(e)); return false; }
    if ((e = esp_wifi_set_config(WIFI_IF_AP, &ap)) != ESP_OK) { ESP_LOGE(TAG, "ap set_config: %s", esp_err_to_name(e)); return false; }
    if ((e = esp_wifi_start()) != ESP_OK) { ESP_LOGE(TAG, "ap start: %s", esp_err_to_name(e)); return false; }
    /* WiFi/AP 与 netif 已建：先置位，之后即使 portal_start 失败也不允许同一 boot 内
     * 再跑一遍 esp_netif_create_default_wifi_ap（内含 assert/ESP_ERROR_CHECK，会 abort）。 */
    s_ap_started = true;

    if (!portal_start()) {
        ESP_LOGE(TAG, "portal down; SoftAP up but no portal");
        return false;
    }
    ESP_LOGW(TAG, "SoftAP %s / pwd %s — 配网页 http://192.168.4.1/", ap.ap.ssid, PROV_PASS);
    /* 现场无串口时，面板是唯一能告诉用户"连哪个热点、口令多少"的地方；
     * SSID 由 MAC 派生、口令写死，光靠串口日志在野外（电池、深睡、没电脑）拿不到。 */
    char disp[128];
    /* 标签后那两个空格不是排版习惯，是给换行引擎留的**断点**：1.54 只有 188px 正文宽，
     * "热点:"+SSID 连排要 228px，硬切会把 SSID 从中间劈开（用户照屏敲的名字）。
     * 有空格可退，引擎就在空格处断行 ⇒ 每格字段整只上屏。 */
    snprintf(disp, sizeof(disp), "热点: %s 密码: %s 打开 192.168.4.1", (char *)ap.ap.ssid, PROV_PASS);
    eink_show_message(disp);
    return true;
}

bool provision_ap_wait_done(int timeout_sec)
{
    if (!s_server) return false;   /* 门户根本没起来：别白等 30 分钟射频空转 */
    int ticks = timeout_sec * 2; /* 每 tick 500ms */
    for (int t = 0; t < ticks && !s_done; t++) {
        vTaskDelay(pdMS_TO_TICKS(500));
        /* R61：这个循环以前是纯睡觉。它是开机后最长的一段（配网窗口默认 1800s），
         * 而唯一读按键的主循环 `for(;;) handle_button(buttons_poll())` 排在它**后面**
         * ⇒ 在这半小时里按 BOOT 没有任何代码在看，而屏上此刻恰好只有配网提示那一页。
         * 用户 2026-09-25 报「只能看当前页面」的直接原因就是这一格，不是版面。 */
        if (buttons_poll() != BTN_NONE) ui_browse_next();
    }
    return s_done;
}

void provision_ap_stop(void)
{
    if (s_server) { httpd_stop(s_server); s_server = NULL; }
    /* 复位全部门户状态：只 httpd_stop 会留下 s_ap_started=true，
     * 将来若有第二次 start（唤醒后重进门户）会被幂等守卫短路成"看似在跑其实没门户"的死锁。 */
    if (s_ap_started) {
        esp_wifi_stop();
        s_ap_started = false;
    }
    s_done = false;
}
