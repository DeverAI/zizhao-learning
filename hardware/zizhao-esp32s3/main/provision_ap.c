#include "provision_ap.h"
#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "nvs_creds.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "prov";
static bool s_done = false;

bool provision_ap_start(void)
{
    esp_netif_create_default_wifi_ap();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    wifi_config_t ap = {0};
    uint8_t mac[6];
    esp_wifi_get_mac(WIFI_IF_AP, mac);
    snprintf((char *)ap.ap.ssid, sizeof(ap.ap.ssid), "Zizhao-Setup-%02X%02X", mac[4], mac[5]);
    ap.ap.ssid_len = strlen((char *)ap.ap.ssid);
    ap.ap.channel = 6;
    ap.ap.max_connection = 4;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_LOGW(TAG, "SoftAP %s — portal http://192.168.4.1/ (HTTP stub in http_server)", ap.ap.ssid);
    /* 生产：挂 esp_http_server captive 门户；骨架阶段串口/工具补全 */
    return true;
}

bool provision_ap_wait_done(int timeout_sec)
{
    int t = 0;
    while (t < timeout_sec && !s_done) {
        vTaskDelay(pdMS_TO_TICKS(500));
        t += 1;
    }
    return s_done;
}
