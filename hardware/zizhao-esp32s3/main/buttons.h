#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BTN_NONE = 0,
    BTN_PLAY_PAUSE,
    BTN_NEXT_SEG,
    BTN_PREV_SEG,
    BTN_REFRESH_MATERIAL,
    BTN_VOLUME_UP,
    BTN_VOLUME_DOWN,
    BTN_TALK,
} btn_event_t;

void buttons_init(void);
/* 非阻塞轮询；触发时 volume_guard_mark_activity() 由 main 调用 */
btn_event_t buttons_poll(void);
/* 联调：串口模拟按键 */
void buttons_inject(btn_event_t ev);

#ifdef __cplusplus
}
#endif
