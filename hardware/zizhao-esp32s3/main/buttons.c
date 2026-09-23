#include "buttons.h"
#include <string.h>
#include "driver/gpio.h"
#include "esp_timer.h"
#include "esp_log.h"

/* 微雪 ESP32-S3-ePaper-3.97 官方例程 08 实引脚（低有效）：
 * 拨轮上=4 功能(按下)=5 下=6，BOOT=0。PWR 走 TG28 电源键、不是 GPIO；
 * 旧骨架里的 3 号脚实为墨水屏 BUSY，占用会产生幻影按键，必须移除。 */
#define PIN_WHEEL_UP     4
#define PIN_WHEEL_DOWN   6
#define PIN_WHEEL_PRESS  5
#define PIN_BOOT         0

static const char *TAG = "btn";
static btn_event_t s_inject = BTN_NONE;
static int64_t s_last_edge[8];

static bool pressed(int pin)
{
    /* 官方 button_bsp：active level = 0 */
    return gpio_get_level(pin) == 0;
}

static bool debounce(int idx)
{
    int64_t now = esp_timer_get_time();
    if (now - s_last_edge[idx] < 200000) return false; /* 200ms */
    s_last_edge[idx] = now;
    return true;
}

void buttons_init(void)
{
    gpio_config_t io = {
        .pin_bit_mask = (1ULL << PIN_WHEEL_UP) | (1ULL << PIN_WHEEL_DOWN) |
                        (1ULL << PIN_WHEEL_PRESS) | (1ULL << PIN_BOOT),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&io);
    ESP_LOGI(TAG, "buttons ready (wheel u/d/press + boot)");
}

void buttons_inject(btn_event_t ev)
{
    s_inject = ev;
}

btn_event_t buttons_poll(void)
{
    if (s_inject != BTN_NONE) {
        btn_event_t e = s_inject;
        s_inject = BTN_NONE;
        return e;
    }
    if (pressed(PIN_WHEEL_PRESS) && debounce(0)) return BTN_PLAY_PAUSE;
    if (pressed(PIN_WHEEL_UP) && debounce(1)) return BTN_VOLUME_UP;
    if (pressed(PIN_WHEEL_DOWN) && debounce(2)) return BTN_VOLUME_DOWN;
    /* 长按上=下一段 / 长按下=上一段 —— 骨架先短按映射；BOOT(0) 复用为换素材键，
     * 注意 0 脚是 strapping：开机瞬间按住它=进下载模式，运行期当按键安全。 */
    if (pressed(PIN_BOOT) && debounce(3)) return BTN_REFRESH_MATERIAL;
    return BTN_NONE;
}
