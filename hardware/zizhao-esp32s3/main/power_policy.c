#include "power_policy.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "esp_timer.h"

void power_policy_defaults(power_policy_t *p)
{
    if (!p) return;
    p->off_hour = 4; p->off_min = 30;
    p->on_hour = 6; p->on_min = 0;
    p->boot_idle_sec = 900;
    p->volume_idle_sec = 600;
}

/* 极简解析，避免再拉 JSON 库依赖；字段来自 /api/device/power */
static bool kv_int(const char *json, const char *key, int *out)
{
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char *s = strstr(json, pat);
    if (!s) return false;
    s = strchr(s, ':');
    if (!s) return false;
    *out = atoi(s + 1);
    return true;
}

static bool parse_hhmm(const char *json, const char *key, int *h, int *m)
{
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char *s = strstr(json, pat);
    if (!s) return false;
    s = strchr(s, ':');
    if (!s) return false;
    s = strchr(s + 1, '"');
    if (!s) return false;
    int a = 0, b = 0;
    if (sscanf(s + 1, "%d:%d", &a, &b) >= 1) {
        *h = a; *m = b;
        return true;
    }
    return false;
}

bool power_policy_parse_json(const char *json, power_policy_t *p)
{
    if (!json || !p) return false;
    parse_hhmm(json, "shutdown_hhmm", &p->off_hour, &p->off_min);
    parse_hhmm(json, "boot_hhmm", &p->on_hour, &p->on_min);
    int v;
    if (kv_int(json, "boot_idle_sec", &v) && v >= 60) p->boot_idle_sec = v;
    if (kv_int(json, "volume_idle_sec", &v) && v >= 60) p->volume_idle_sec = v;
    return true;
}

bool power_policy_should_sleep(const power_policy_t *p, time_t now, int64_t boot_us, int64_t last_act_us)
{
    if (!p) return false;
    struct tm tmv;
    localtime_r(&now, &tmv);
    /* 定点关机：进入 04:30 分钟窗口 */
    if (tmv.tm_hour == p->off_hour && tmv.tm_min == p->off_min) return true;
    /* 开机后长时间无有效活动 */
    int64_t boot_idle = (boot_us > 0) ? (last_act_us - boot_us) : 0;
    int64_t since_act = (last_act_us > 0) ? (esp_timer_get_time() - last_act_us) : 0;
    /* 用 wall 无关逻辑：调用方传入 now 仅用于定点；idle 用 last_act 相对 */
    (void)boot_idle;
    if (last_act_us > 0 && since_act > (int64_t)p->boot_idle_sec * 1000000LL) {
        /* 仅在“已开机过 idle 窗口”时由调用方结合 boot 判断 */
        return true;
    }
    return false;
}

uint64_t power_policy_us_until_boot(const power_policy_t *p, time_t now)
{
    if (!p) return 3600ULL * 1000000ULL;
    struct tm tmv;
    localtime_r(&now, &tmv);
    int now_sec = tmv.tm_hour * 3600 + tmv.tm_min * 60 + tmv.tm_sec;
    int boot_sec = p->on_hour * 3600 + p->on_min * 60;
    int delta = boot_sec - now_sec;
    if (delta <= 0) delta += 24 * 3600;
    return (uint64_t)delta * 1000000ULL;
}
