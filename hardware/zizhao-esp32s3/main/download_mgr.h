#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 有网时下载优先级：小而关键先下；大音频最后且可断点。 */
typedef enum {
    DL_PRIO_LOGIN = 0,      /* sid，必须最先 */
    DL_PRIO_POWER_POLICY,   /* 数百字节，决定关机/音量 */
    DL_PRIO_MANIFEST,       /* 组件清单 + etag */
    DL_PRIO_BUNDLE_TEXT,    /* 素材正文+分段文本（无音频也能用） */
    DL_PRIO_AUDIO_SEG,      /* MP3，最大，Range 续传 */
    DL_PRIO_FIRMWARE,       /* 后台 OTA，最后且可跳过 */
} dl_prio_t;

typedef struct {
    char day_key[16];
    bool text_done;
    bool audio_done;
    bool audio_allowed;   /* 服务端 audio_ready；未过审不下载音频 */
    int audio_total;
    int audio_got;
    char last_error[64];
} dl_state_t;

void dl_mgr_init(void);
/* 上电/重连后按优先级跑一轮；返回 text 是否就绪 */
bool dl_mgr_sync_once(const char *sid, const char *server, dl_state_t *st);
/* 单文件原子下载：.part → fsync → rename；支持 Range 续传 */
bool dl_http_get_atomic(const char *sid, const char *url, const char *dest_path, bool allow_resume);
/* 清理半截文件 */
void dl_mgr_cleanup_partial(void);

#ifdef __cplusplus
}
#endif
