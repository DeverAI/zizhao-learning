# ESP32-S3 自招学习板 —— 固件骨架 v2（审核门控 + 开关机 + 现场配网）

## 硬约束

1. **音频门控**：仅当 `bundle.audio_ready=true`（素材 `review_status=passed`）才下载/播放 MP3  
2. **音量保护**：连续 10 分钟无有效交互 → 音量降到 `idle_level`（防上课误触）  
3. **自动开关机**：默认 04:30 关、06:00 开；开机后 15 分钟无播放/按键/下载 → 再关  
4. **配网双通道**  
   - 线上：`POST /api/auth/device/login`（烧录 PassKey）  
   - 现场：AP `Zizhao-Setup-<chipid>` →  captive 门户填 WiFi + server_url（PassKey 已在 NVS）  
5. **防死锁**：关机流程固定顺序，超时强制 deep sleep；开机只依赖 RTC 定时，不依赖上次任务锁

## 关机序列（必须顺序执行，总超时 20s）

```
1. 标记 shutdown_requested
2. 停止播放 / 关 I2S
3. POST /api/material/progress（保存断点）
4. 刷屏提示「按时关机」
5. 关 WiFi
6. esp_sleep_enable_timer(到下次 boot 时刻)
7. esp_deep_sleep_start()
```

若 2–5 任一步卡住：watchdog 咬 → 直接 6–7。

## 开机序列

```
1. NVS 读 device_id/passkey/server_url
2. 若无配置 → 启动 AP 配网门户
3. WiFi 连接（失败则仅用 SD 离线缓存，不阻塞开机）
4. login（成功则刷新 offline bundle）
5. boot_idle 计时开始
```

## 有效活动（重置 idle / boot_idle）

- 播放中（每 5s 心跳）
- 拨轮/按键
- 音量调节
- 成功下载 bundle/mp3 分段

## 最小 API

| 方法 | 路径 |
|------|------|
| POST | `/api/auth/device/login` |
| GET | `/api/offline/manifest` |
| GET | `/api/offline/bundle` |
| GET | `/api/media/{id}/download` |
| POST | `/api/material/progress` |
| GET | `/api/device/power`（策略，可缓存） |

## 现场配网

- SoftAP SSID：`Zizhao-Setup-XXXX`  
- 门户：`http://192.168.4.1/` 表单：wifi_ssid / wifi_pass / server_url  
- PassKey **不**在门户重新输入（已在 NVS）；若未烧录则串口 `prov set passkey ...`  
- 保存后 STA 重连；连不上则继续离线缓存模式

## 待补工程文件

- `CMakeLists.txt` / `main/main.c` 完整 IDF 工程  
- RTC 唤醒跨 4:30→次日 6:00 的计算  
- 双麦 AEC、OTA  

见同目录 `esp32_main_skeleton.c` 控制流。
