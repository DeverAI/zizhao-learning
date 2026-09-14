#pragma once
#include <stdbool.h>
#include "nvs_creds.h"

#ifdef __cplusplus
extern "C" {
#endif

bool net_http_login(const zizhao_creds_t *c, char *sid_out, size_t sid_len);
bool net_http_get_bundle(const char *sid, const char *server, char *buf, size_t buf_len);
bool net_http_report_progress(const char *sid, const char *server, int material_id_hash, int seg, int offset_ms);
bool net_http_get_power_policy(const char *sid, const char *server, char *buf, size_t buf_len);

#ifdef __cplusplus
}
#endif
