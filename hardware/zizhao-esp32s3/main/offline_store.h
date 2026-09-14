#pragma once
#include <stdbool.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

/* SD/FAT 离线缓存：/sdcard/offline/YYYY-MM-DD.json + mp3/seg_N.mp3 */
bool offline_store_init(void);
bool offline_store_save_text(const char *day_key, const char *json, size_t len);
bool offline_store_load_text(const char *day_key, char *out, size_t out_len);
bool offline_store_has_audio(const char *day_key);
/* audio_ready 必须来自服务端 bundle；本地仅存事实文件 */
bool offline_store_read_audio_ready_flag(const char *day_key);

#ifdef __cplusplus
}
#endif
