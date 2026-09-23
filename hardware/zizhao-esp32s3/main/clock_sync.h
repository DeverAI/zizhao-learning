#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 校时（Asia/Shanghai UTC+8）。失败不阻塞开机：
 *   1) SNTP（UDP 123）——校园网常封，先试；
 *   2) 服务端 /api/system/time HTTP 兜底（走 80/8010，封 UDP 也能对时）。
 * 顺序：clock_sync_sntp() → 失败再 clock_sync_http(server_url)。
 * 注意必须先 clock_tz_init()，否则本地时间按 UTC 算，页面日期会差 8 小时/一天。 */
void clock_tz_init(void);
bool clock_sync_sntp(void);
bool clock_sync_http(const char *server_url);
bool clock_is_synced(void);

/* 板的 RTC 掉电会丢时间。这两个值在 SNTP/HTTP 成功后缓存，
 * 用于「重启后先按上次时间显示，后台再校准」，避免凌晨 00:00 白页。 */
void clock_stash_save(time_t t);
time_t clock_stash_load(void);

void clock_format_hm(char *out, size_t n);
void clock_format_full(char *out, size_t n, time_t t);
/* 「2026年09月16日 周三」——墨水屏日期行。未校时时返回占位。 */
void clock_format_date_cn(char *out, size_t n, time_t t);

#ifdef __cplusplus
}
#endif
