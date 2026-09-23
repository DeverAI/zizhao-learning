#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* SoftAP Zizhao-Setup-XXXX (WPA2) + 极简 HTTP 门户写 WiFi/server/device/passkey 进 NVS */
bool provision_ap_start(void);
/* 等待门户保存完成，timeout_sec 秒；返回是否配网成功 */
bool provision_ap_wait_done(int timeout_sec);
/* 停门户（配网成功/超时后调用，释放 httpd socket） */
void provision_ap_stop(void);

#ifdef __cplusplus
}
#endif
