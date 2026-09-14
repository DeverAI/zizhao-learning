#include "buttons.h"
#include <string.h>
#include "driver/gpio.h"
#include "esp_timer.h"
#include "esp_log.h"

/* 微雪 ePaper-3.97：三向拨轮 + PWR。引脚以 wiki 为准，联调改。 */
#define PIN_WHEEL_UP     0
#define PIN_WHEEL_DOWN   2
#define PIN_WHEEL_PRESS  1
#define PIN_PWR          3

static const char *TAG = "btn";
static btn_event_t s_inject = BTN_NONE;
static int64_t s_last_edge[8];

static bool pressed(int pin)
{
    /* 假定低有效；按板子改 */
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
                        (1ULL << PIN_WHEEL_PRESS) | (1ULL << PIN_PWR),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&io);
    ESP_LOGI(TAG, "buttons ready (wheel u/d/press + pwr)");
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
    /* 长按上=下一段 / 长按下=上一段 —— 骨架先短按映射 */
    if (pressed(PIN_PWR) && debounce(3)) return BTN_REFRESH_MATERIAL;
    return BTN_NONE;
}
