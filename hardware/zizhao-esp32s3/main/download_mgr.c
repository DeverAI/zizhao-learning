#include "download_mgr.h"
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "esp_http_client.h"
#include "esp_log.h"
#include "nvs_creds.h"
#include "net_http.h"
#include "offline_store.h"
#include "ota_bg.h"

static const char *TAG = "dl";
#define BASE "/sdcard"

void dl_mgr_init(void)
{
    offline_store_init();
    dl_mgr_cleanup_partial();
}

void dl_mgr_cleanup_partial(void)
{
    /* 启动时丢掉所有 *.part，避免把半截当成品 */
    /* 简化：目录枚举可后续补；当前路径固定 */
    unlink(BASE "/offline/bundle.json.part");
    for (int i = 0; i < 64; i++) {
        char p[96];
        snprintf(p, sizeof(p), BASE "/offline/mp3/seg_%03d.mp3.part", i);
        unlink(p);
    }
    unlink(BASE "/offline/firmware.bin.part");
}

static long file_size(const char *path)
{
    struct stat st;
    if (stat(path, &st) != 0) return -1;
    return (long)st.st_size;
}

bool dl_http_get_atomic(const char *sid, const char *url, const char *dest_path, bool allow_resume)
{
    char part[160];
    snprintf(part, sizeof(part), "%s.part", dest_path);
    long have = 0;
    if (allow_resume) {
        have = file_size(part);
        if (have < 0) have = 0;
    } else {
        unlink(part);
    }

    esp_http_client_config_t cfg = {
        .url = url,
        .timeout_ms = 30000,
        .buffer_size = 2048,
        .buffer_size_tx = 1024,
    };
    esp_http_client_handle_t c = esp_http_client_init(&cfg);
    char cookie[160];
    snprintf(cookie, sizeof(cookie), "zsid=%s", sid ? sid : "");
    esp_http_client_set_header(c, "Cookie", cookie);
    if (have > 0) {
        char range[48];
        snprintf(range, sizeof(range), "bytes=%ld-", have);
        esp_http_client_set_header(c, "Range", range);
    }
    esp_err_t e = esp_http_client_open(c, 0);
    if (e != ESP_OK) {
        ESP_LOGW(TAG, "open fail %s %d", url, e);
        esp_http_client_cleanup(c);
        return false;
    }
    int status = esp_http_client_fetch_headers(c);
    (void)status;
    int code = esp_http_client_get_status_code(c);
    if (code != 200 && code != 206) {
        ESP_LOGW(TAG, "GET %s status=%d", url, code);
        esp_http_client_close(c);
        esp_http_client_cleanup(c);
        return false;
    }
    FILE *f = fopen(part, (have > 0 && code == 206) ? "ab" : "wb");
    if (!f) {
        esp_http_client_close(c);
        esp_http_client_cleanup(c);
        return false;
    }
    char buf[2048];
    int n;
    size_t total = (have > 0 && code == 206) ? (size_t)have : 0;
    while ((n = esp_http_client_read(c, buf, sizeof(buf))) > 0) {
        if (fwrite(buf, 1, n, f) != (size_t)n) {
            fclose(f);
            esp_http_client_close(c);
            esp_http_client_cleanup(c);
            return false; /* 磁盘满：保留 .part 以便续传 */
        }
        total += (size_t)n;
    }
    fflush(f);
    fsync(fileno(f));
    fclose(f);
    esp_http_client_close(c);
    esp_http_client_cleanup(c);
    /* 原子提交：rename 后才算完成 */
    if (rename(part, dest_path) != 0) {
        ESP_LOGE(TAG, "rename fail %s", dest_path);
        return false;
    }
    ESP_LOGI(TAG, "ok %s (%u bytes)", dest_path, (unsigned)total);
    return true;
}

static bool sync_bundle_text(const char *sid, const char *server, dl_state_t *st)
{
    char url[192];
    snprintf(url, sizeof(url), "%s/api/offline/bundle", server);
    char dest[96];
    snprintf(dest, sizeof(dest), BASE "/offline/bundle.json");
    mkdir(BASE "/offline", 0777);
    /* JSON 短，整包重下即可；失败保留旧文件 */
    char tmp[96];
    snprintf(tmp, sizeof(tmp), "%s.new", dest);
    if (!dl_http_get_atomic(sid, url, tmp, false)) {
        snprintf(st->last_error, sizeof(st->last_error), "bundle_fail");
        return false;
    }
    /* 旧→bak，new→正式 */
    unlink(dest);
    rename(tmp, dest);
    st->text_done = true;
    /* 粗读 audio_ready */
    FILE *f = fopen(dest, "rb");
    if (f) {
        char head[4096] = {0};
        size_t n = fread(head, 1, sizeof(head) - 1, f);
        (void)n;
        fclose(f);
        st->audio_allowed = (strstr(head, "\"audio_ready\": true") != NULL)
                            || (strstr(head, "\"audio_ready\":true") != NULL);
    }
    return true;
}

/*
 * 音频分段：按 bundle 里的 path 下载；支持 Range。
 * 未 audio_allowed 则直接跳过（审核门控）。
 * 已存在的 seg_XXX.mp3 且大小>0 视为完成。
 */
static int sync_audio(const char *sid, const char *server, const char *day_key, dl_state_t *st)
{
    if (!st->audio_allowed) {
        st->audio_done = false;
        snprintf(st->last_error, sizeof(st->last_error), "audio_not_allowed");
        return 0;
    }
    mkdir(BASE "/offline/mp3", 0777);
    /* 骨架：最多 32 段，按约定 URL 拉；真实 path 来自 bundle 解析后替换 */
    int got = 0;
    for (int i = 0; i < 32; i++) {
        char dest[96];
        snprintf(dest, sizeof(dest), BASE "/offline/mp3/seg_%03d.mp3", i);
        long sz = file_size(dest);
        if (sz > 0) {
            got++;
            continue;
        }
        char url[192];
        snprintf(url, sizeof(url), "%s/api/media/seg/%s/%d", server, day_key, i);
        if (!dl_http_get_atomic(sid, url, dest, true)) {
            /* 单段失败不整轮放弃；下次续传 */
            break;
        }
        got++;
    }
    st->audio_got = got;
    st->audio_total = 32;
    st->audio_done = (got >= 32);
    return got;
}

bool dl_mgr_sync_once(const char *sid, const char *server, dl_state_t *st)
{
    if (!sid || !server || !st) return false;
    st->last_error[0] = 0;
    /* P0 电源策略（极小） */
    char pol[512] = {0};
    if (net_http_get_power_policy(sid, server, pol, sizeof(pol))) {
        /* 已由 main 解析；此处仅确认在线 */
    }
    /* P1 bundle 文本 —— 无网时用旧缓存 */
    if (!sync_bundle_text(sid, server, st)) {
        char tmp[8];
        st->text_done = offline_store_load_text("today", tmp, sizeof(tmp));
        if (!st->text_done) {
            snprintf(st->last_error, sizeof(st->last_error), "no_text_cache");
        }
        return st->text_done;
    }
    {
        FILE *f = fopen(BASE "/offline/bundle.json", "rb");
        if (f) {
            static char body[16384];
            size_t n = fread(body, 1, sizeof(body) - 1, f);
            fclose(f);
            body[n] = 0;
            offline_store_save_text("today", body, n);
        }
    }
    /* P2 音频（可断点） */
    sync_audio(sid, server, st->day_key[0] ? st->day_key : "today", st);
    /* P3 固件：最后、后台 */
    ota_bg_check_and_update(sid, server);
    return st->text_done;
}
