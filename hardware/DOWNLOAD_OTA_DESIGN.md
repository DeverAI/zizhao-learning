# 下载 / 断点 / OTA —— 工程设计

## 1. 连上 WiFi 后优先下什么

顺序固定，**小而关键先，大而可延后**：

| 优先级 | 内容 | 为什么 |
|--------|------|--------|
| P0 | `device/login` → sid | 没会话什么都下不了 |
| P1 | `/api/device/power` | 几百字节，立刻决定关机/音量策略 |
| P2 | `/api/offline/bundle` **文本部分** | 无音频也能读/看；最大收益/体积比 |
| P3 | MP3 分段 | 体积大；**仅 `audio_ready=true` 才下** |
| P4 | 固件 manifest/bin | 最后、后台静默；可跳过不影响今日学习 |

原则：**先保证「今天能学」再追「学得舒服」**。

## 2. 没下完断了怎么办

### 通用规则
1. **原子落盘**：写 `xxx.part` → `fsync` → `rename` 成正式文件  
   - 正式文件名永远完整；半截只会出现在 `.part`  
2. **开机清理** `*.part`（或保留给音频续传，见下）  
3. **旧文件不删**：新 bundle 下载失败时继续用昨天的缓存（`offline/bundle.json` 仍在）  
4. **JSON 不续传**：包小，整包重下；失败保留旧文件  

### 音频分段
- 每段独立文件 `seg_000.mp3`  
- 请求头 `Range: bytes=N-`，服务器 `206`  
- 已存在且 size>0 → 跳过  
- 单段失败：**不整轮放弃**，下轮接着下  
- 未 `audio_allowed`：**根本不发起音频请求**（审核门控）  

### 状态
`dl_state_t`：`text_done` / `audio_got` / `audio_total` / `last_error`  
墨水屏可显示「已缓存 3/32 段」。

## 3. 烧固件断了怎么办

### 分区（已改 `partitions.csv`）
```
ota_0 (3M) + ota_1 (3M) + otadata
```
- 运行在 A，OTA 写 B  
- **写完且校验通过** 才 `esp_ota_set_boot_partition(B)`  
- 中途断电：仍从 A 启动，**不变砖**  
- `esp_https_ota` 内建此流程；失败不改 boot  

### 固件策略
- **禁止**用户 UI 升级  
- 仅登录后、约 6h 一次后台检查  
- 无 manifest → 404 → 静默跳过  
- 有版本差异才拉 bin；失败记 `s_err`，继续听素材  

### 写 .part 的固件
`firmware.bin.part` 若中断可续传（Range）；rename 前不参与 OTA 解析。

## 4. 服务端配合

| 接口 | 要求 |
|------|------|
| `GET /api/media/{id}/download` | 支持 `Range` / `206` |
| `GET /api/device/firmware/bin` | 同上 |
| `GET /api/offline/bundle` | 可整包；带 `etag` 便于跳过 |

## 5. 实现落点

- `main/download_mgr.c`：优先级 + 原子写 + Range 续传  
- `partitions.csv`：双 OTA  
- `ota_bg.c`：后台静默 OTA  
- `main.c`：登录后 `dl_mgr_sync_once`  
