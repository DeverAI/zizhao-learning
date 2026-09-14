#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <time.h>
#ifdef __cplusplus
extern "C" {
#endif

/* SNTP 校时（Asia/Shanghai UTC+8）。失败不阻塞开机。 */
bool clock_sync_sntp(void);
bool clock_is_synced(void);
void clock_format_hm(char *out, size_t n);
void clock_format_full(char *out, size_t n, time_t t);

#ifdef __cplusplus
}
#endif
