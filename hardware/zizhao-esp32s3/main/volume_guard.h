#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

void volume_guard_init(int default_vol, int idle_vol, int idle_sec);
void volume_guard_mark_activity(void);
int  volume_guard_tick(void); /* 返回当前应使用的音量 0-15 */
bool volume_guard_should_mute(void);

#ifdef __cplusplus
}
#endif
