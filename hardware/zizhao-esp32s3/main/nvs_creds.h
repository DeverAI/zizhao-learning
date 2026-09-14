#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char device_id[40];
    char passkey[80];
    char server_url[128];
    char wifi_ssid[64];
    char wifi_pass[64];
} zizhao_creds_t;

bool nvs_creds_load(zizhao_creds_t *out);
bool nvs_creds_save(const zizhao_creds_t *in);
bool nvs_creds_has_passkey(const zizhao_creds_t *c);
bool nvs_creds_ready_for_sta(const zizhao_creds_t *c);

#ifdef __cplusplus
}
#endif
