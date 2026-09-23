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

- 每次开机（登录后约 2 分钟）查一次 `GET /api/device/firmware/latest`（带 `zsid` Cookie）；设备每日定时唤醒 → 天然每日检查。不能用“连续运行 6h”判：深睡唤醒后 `esp_timer` 归零，那样永不触发  
- 版本比对用 `esp_app_desc.version`，其来源是顶层 `CMakeLists.txt` 的 `set(PROJECT_VER "x.y.z")`（**不是** `VERSION` 文件，IDF 5.1 不认）；与 manifest `version` 不同才 OTA，避免每轮重下  
- manifest 的 `url` 可写相对路径 `/api/device/firmware/bin`，固件会用 `server_url` 补成绝对地址  
- 发版流程：改 `CMakeLists.txt` 的 `PROJECT_VER` → `idf.py build` → 把 **`build/zizhao_esp32s3.bin`**（别拷错成 bootloader/partition_table）拷成 `storage/firmware/firmware.bin` → 更新 `manifest.json` 的 `version`/`sha256`  
- 失败只记日志；`policy: background_only_no_user_ui`（无用户升级入口）  
- 服务端：`storage/firmware/manifest.json` + `firmware.bin`

## 编译

> 从零到烧录 + NVS 配网的保姆级步骤见 [`hardware/FIRST_FLASH_GUIDE.md`](../FIRST_FLASH_GUIDE.md)。

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
