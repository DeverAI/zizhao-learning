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
        /* 值域校验：服务端/明文链路被篡改时可下发 on_hour=1000 → 睡成 41 天的"砖"。
         * 越界一律拒收，保留 defaults（4:30 关 / 6:00 开），绝不让垃圾值进关机时刻。 */
        if (a < 0 || a > 23 || b < 0 || b > 59) {
            return false;
        }
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
    /* 交叉校验：boot 与 shutdown 撞进同一分钟时，should_sleep 一开机即命中定点关机，
     * 而 us_until_boot 又算出 ~24h → 变成"每天唤醒一次、全功率射频、立刻再深睡"的空转。
     * 无法自行判定哪端对，保守把开机时刻退回默认 06:00，保证有一个可工作窗口。 */
    if (p->off_hour == p->on_hour && p->off_min == p->on_min) {
        p->on_hour = 6; p->on_min = 0;
    }
    int v;
    /* idle 阈值同样夹范围：boot_idle_sec 过小会让开机 2 分钟内的 OTA 检查永不触发，
     * 过大（甚至 0/负）则设备几乎不睡。钳到 [180, 3600]。 */
    if (kv_int(json, "boot_idle_sec", &v) && v >= 180 && v <= 3600) p->boot_idle_sec = v;
    if (kv_int(json, "volume_idle_sec", &v) && v >= 180 && v <= 3600) p->volume_idle_sec = v;
    return true;
}

bool power_policy_should_sleep(const power_policy_t *p, time_t now, int64_t boot_us, int64_t last_act_us)
{
    if (!p) return false;
    struct tm tmv;
    localtime_r(&now, &tmv);
    /* 定点关机：进入 04:30 分钟窗口 */
    if (tmv.tm_hour == p->off_hour && tmv.tm_min == p->off_min) return true;
    /* 开机后长时间无有效活动 → 关机
     * boot_us 用于调用方自行判断「刚开机给宽限」；
     * 此处只看 last_act 距今是否超过 idle 阈值。 */
    (void)boot_us;
    int64_t since_act = (last_act_us > 0) ? (esp_timer_get_time() - last_act_us) : 0;
    if (last_act_us > 0 && since_act > (int64_t)p->boot_idle_sec * 1000000LL) {
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
    if (delta < 60) delta = 60;   /* 下限 60s：避免算出极小值导致秒级唤醒空转耗电 */
    return (uint64_t)delta * 1000000ULL;
}
