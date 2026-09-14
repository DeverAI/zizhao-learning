#include "offline_store.h"
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include "esp_log.h"
#include "esp_vfs_fat.h"
#include "sdmmc_cmd.h"

static const char *TAG = "offline";
static bool s_inited = false;

#define MOUNT "/sdcard"

bool offline_store_init(void)
{
    if (s_inited) return true;
    esp_vfs_fat_sdmmc_mount_config_t mount_config = {
        .format_if_mount_failed = false,
        .max_files = 5,
        .allocation_unit_size = 16 * 1024,
    };
    sdmmc_card_t *card = NULL;
    /* 引脚按微雪 ePaper-3.97 原理图；联调用 menuconfig 覆盖 */
    sdmmc_host_t host = SDSPI_HOST_DEFAULT();
    spi_bus_config_t bus_cfg = {
        .mosi_io_num = 40,
        .miso_io_num = 41,
        .sclk_io_num = 39,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4000,
    };
    sdspi_device_config_t slot = SDSPI_DEVICE_CONFIG_DEFAULT();
    slot.gpio_cs = 42;
    slot.host_id = host.slot;
    esp_err_t e = spi_bus_initialize(host.slot, &bus_cfg, SDSPI_DEFAULT_DMA);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "spi_bus init %d", e);
    }
    e = esp_vfs_fat_sdspi_mount(MOUNT, &host, &slot, &mount_config, &card);
    if (e != ESP_OK) {
        ESP_LOGW(TAG, "SD mount fail %d — offline text only in NVS/RAM", e);
        return false;
    }
    s_inited = true;
    ESP_LOGI(TAG, "SD mounted");
    return true;
}

static void path_for(const char *day, const char *name, char *out, size_t n)
{
    snprintf(out, n, "%s/offline", MOUNT);
    mkdir(out, 0777);
    snprintf(out, n, "%s/offline/%s_%s", MOUNT, day, name);
}

bool offline_store_save_text(const char *day_key, const char *json, size_t len)
{
    if (!s_inited || !day_key || !json) return false;
    char path[128];
    path_for(day_key, "bundle.json", path, sizeof(path));
    FILE *f = fopen(path, "wb");
    if (!f) return false;
    size_t w = fwrite(json, 1, len, f);
    fclose(f);
    return w == len;
}

bool offline_store_load_text(const char *day_key, char *out, size_t out_len)
{
    if (!s_inited || !day_key || !out) return false;
    char path[128];
    path_for(day_key, "bundle.json", path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (!f) return false;
    size_t n = fread(out, 1, out_len - 1, f);
    fclose(f);
    out[n] = 0;
    return n > 0;
}

bool offline_store_has_audio(const char *day_key)
{
    if (!s_inited) return false;
    char path[128];
    path_for(day_key, "audio_ready.flag", path, sizeof(path));
    struct stat st;
    return stat(path, &st) == 0;
}

bool offline_store_read_audio_ready_flag(const char *day_key)
{
    return offline_store_has_audio(day_key);
}
