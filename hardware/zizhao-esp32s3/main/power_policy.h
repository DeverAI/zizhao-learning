#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int off_hour;
    int off_min;
    int on_hour;
    int on_min;
    int boot_idle_sec;   /* 开机后无活动再关 */
    int volume_idle_sec; /* 无操作降音量 */
} power_policy_t;

void power_policy_defaults(power_policy_t *p);
/* 服务端下发：shut 04:30 / on 06:00 / idle 900 */
bool power_policy_parse_json(const char *json, power_policy_t *p);
bool power_policy_should_sleep(const power_policy_t *p, time_t now, int64_t boot_us, int64_t last_act_us);
/* 到下一次开机时刻的微秒（RTC timer） */
uint64_t power_policy_us_until_boot(const power_policy_t *p, time_t now);

#ifdef __cplusplus
}
#endif
