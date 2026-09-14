# 自招学习板固件（微雪 ESP32-S3-ePaper-3.97）

## 按键（无升级入口）

| 动作 | 事件 |
|------|------|
| 拨轮按下 | 播放/暂停 |
| 拨轮上/下 | 音量 ± |
| PWR | 换素材 |

**没有「检查更新 / 升级固件」按钮或菜单。**

## 时钟

SNTP（`ntp.aliyun.com`，UTC+8）→ 每分钟刷新 `HH:MM` + 日期（墨水屏静态，断电仍可见）。

## 固件更新（仅后台静默）

- 约每 6h 拉 `GET /api/device/firmware/latest`（需已登录）  
- 有新版本才 OTA；失败只记日志  
- 服务端：`storage/firmware/manifest.json` + `firmware.bin`  
- `policy: background_only_no_user_ui`

## 编译

```powershell
cd hardware/zizhao-esp32s3
# 已安装 ESP-IDF 5.x 并 export 环境后：
idf.py set-target esp32s3
idf.py build
idf.py -p COMx flash monitor
```

## 产线 NVS（勿提交 git）

```text
namespace=zizhao
device_id=dev_xxxxxxxx
passkey=<网页「设备」页签发>
server_url=http://<服务器IP>:8010
wifi_ssid=...
wifi_pass=...
```

也可板端 AP：`Zizhao-Setup-XXXX` → 门户（门户 HTTP 实现见 `provision_ap.c` 注释，待补 esp_http_server）。

## 已实现骨架

| 模块 | 作用 |
|------|------|
| `nvs_creds.c` | 凭据读写 |
| `net_http.c` | login / bundle / progress / power |
| `power_policy.c` | 04:30 关、06:00 开、idle 再关 |
| `volume_guard.c` | 10 分钟无操作音量最小 |
| `offline_store.c` | SD 缓存 bundle |
| `provision_ap.c` | 现场 AP |
| `main.c` | 串起主流程 |

## 待硬件联调

1. ePaper 驱动（分段刷，官方例程）  
2. ES8311 + I2S MP3（`esp_player` / helix）  
3. 双麦 AEC（若板为单麦则外接）  
4. 拨轮 GPIO  
5. captive 门户完整 HTML  
6. RTC 跨日唤醒实测  

## 引脚

SD SPI 默认写在 `offline_store.c`（39/40/41/42），**必须按微雪 wiki 核对**。
