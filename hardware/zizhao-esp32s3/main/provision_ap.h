#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* SoftAP Zizhao-Setup-XXXX + 极简 HTTP 门户写 WiFi/server_url（PassKey 已在 NVS） */
bool provision_ap_start(void);
bool provision_ap_wait_done(int timeout_sec);

#ifdef __cplusplus
}
#endif
