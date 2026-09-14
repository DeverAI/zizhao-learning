#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 固件只允许后台静默更新，禁止用户在 UI 直接触发。 */
bool ota_bg_check_and_update(const char *sid, const char *server);
/* 是否刚完成 OTA（用于重启前刷屏提示） */
bool ota_bg_pending_reboot(void);
const char *ota_bg_last_error(void);

#ifdef __cplusplus
}
#endif
