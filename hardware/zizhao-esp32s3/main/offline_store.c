#include "offline_store.h"
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include "esp_log.h"
#include "esp_vfs_fat.h"
#include "driver/sdmmc_host.h"
#include "sdmmc_cmd.h"

static const char *TAG = "offline";
static bool s_inited = false;
static sdmmc_card_t *s_card = NULL;

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
    /* 本板 Micro SD 是 4 线 SDMMC，不是 SPI。官方 05_SD_Test 引脚：
     * CLK16 CMD17 D0=15 D1=7 D2=8 D3=18，且例程按 1-bit 模式挂载。
     * 之前按 SDSPI 用 39/40/41/42 既挂不上（NO_MEM），又把 41/42 抢成 MISO/CS——
     * 而 41/42 是 AXP2101 的 SDA/SCL，墨水屏电轨因此永远开不起来。 */
    sdmmc_host_t host = SDMMC_HOST_DEFAULT();
    host.flags = SDMMC_HOST_FLAG_1BIT;
    sdmmc_slot_config_t slot_config = SDMMC_SLOT_CONFIG_DEFAULT();
    slot_config.clk = 16;
    slot_config.cmd = 17;
    slot_config.d0 = 15;
    slot_config.d1 = 7;
    slot_config.d2 = 8;
    slot_config.d3 = 18;
    slot_config.width = 1;
    slot_config.flags |= SDMMC_SLOT_FLAG_INTERNAL_PULLUP;
    esp_err_t e = esp_vfs_fat_sdmmc_mount(MOUNT, &host, &slot_config, &mount_config, &card);
    if (e != ESP_OK) {
        ESP_LOGW(TAG, "SD mount fail %s — offline text only in NVS/RAM", esp_err_to_name(e));
        return false;
    }
    s_inited = true;
    s_card = card;
    ESP_LOGI(TAG, "SD mounted (%s, %u KB)", card->cid.name,
             (unsigned)(card->csd.capacity * card->csd.sector_size / 1024));
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
    if (!s_inited || !day_key || !out || out_len < 2) return false;  /* out_len==0 会让下面变 SIZE_MAX 越界写 */
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

void offline_store_flush(void)
{
    /* 深睡/重启前调用：unmount 会做一次最终 sync 并释放 SDMMC 总线（本卡走 1-bit SDMMC，
     * 不再占用 SPI），避免卡仍在写时断电产生半截文件。幂等：未挂载/已卸载直接返回。 */
    if (!s_inited || !s_card) return;
    esp_err_t e = esp_vfs_fat_sdcard_unmount(MOUNT, s_card);
    s_card = NULL;
    s_inited = false;
    if (e != ESP_OK) ESP_LOGW(TAG, "SD unmount %d", e);
    else ESP_LOGI(TAG, "SD unmounted (flushed)");
}
