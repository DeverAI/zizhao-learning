#include "volume_guard.h"
#include <stdbool.h>
#include "esp_timer.h"

static int s_def_vol = 12;
static int s_idle_vol = 1;
static int s_idle_sec = 600;
static int s_vol = 12;
static int64_t s_last = 0;

void volume_guard_init(int default_vol, int idle_vol, int idle_sec)
{
    s_def_vol = default_vol;
    s_idle_vol = idle_vol;
    s_idle_sec = idle_sec > 0 ? idle_sec : 600;
    s_vol = s_def_vol;
    s_last = esp_timer_get_time();
}

void volume_guard_mark_activity(void)
{
    s_last = esp_timer_get_time();
    s_vol = s_def_vol;
}

int volume_guard_tick(void)
{
    int64_t idle = (esp_timer_get_time() - s_last) / 1000000LL;
    if (idle >= s_idle_sec && s_vol > s_idle_vol) {
        s_vol = s_idle_vol; /* 防上课误触社死 */
    }
    return s_vol;
}

bool volume_guard_should_mute(void)
{
    return volume_guard_tick() <= s_idle_vol;
}
