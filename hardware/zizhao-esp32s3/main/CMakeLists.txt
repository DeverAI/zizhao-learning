# 板型开关**只有一处真值**：`board_profile.h` 里的 `BOARD_EPAPER_1IN54`。
# 两只墨水屏驱动都留在 SRCS 里，没被选中的那只由文件顶部的 `#if` 整只抹空
# （`epd_panel_1in54.c` 要 =1，`epd_driver.c` 要 =0），所以既不会重复定义那 8 个
# `epd_*` 入口，也不会出现"CMake 与头文件各说一套"的漂移。
# `axp_panel_power.c` 同理常驻：1.54 板上没人调它，链接期 `--gc-sections` 会丢掉。
idf_component_register(
    SRCS
        "main.c"
        "net_http.c"
        "power_policy.c"
        "volume_guard.c"
        "offline_store.c"
        "provision_ap.c"
        "nvs_creds.c"
        "buttons.c"
        "clock_sync.c"
        "ota_bg.c"
        "eink_display.c"
        "epd_driver.c"
        "epd_panel_1in54.c"
        "axp_panel_power.c"
        "ui_font.c"
        "download_mgr.c"
    INCLUDE_DIRS "."
    REQUIRES
        nvs_flash
        esp_wifi
        esp_http_client
        esp_http_server
        esp_https_ota
        esp_app_format
        esp_timer
        esp_event
        esp_netif
        fatfs
        sdmmc
        driver
        esp_rom
        lwip
        app_update
)
