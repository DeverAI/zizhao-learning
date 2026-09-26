# 微雪 ESP32-S3-ePaper-3.97 硬件落地说明

> 【2026-09-25 R59 改判 ⇒ **本文件不再描述在机的那块板**】R58 烧原厂整片固件读出 `Project name: 02_ePaper_1_54_Test`、
> R59 鉴定确认在机板是 **Waveshare S3_ePaper_1_54**（200×200，屏电 GPIO6 低有效，**整板没有 AXP2101**）。
> 当前在机板的档案 = `BOARD_S3_ePaper_1_54.md`；代码里的单一真值 = `zizhao-esp32s3/main/board_profile.h`（`BOARD_EPAPER_1IN54 1`）。
> 本文件保留的理由：R24~R57 几十轮判据（含那条"屏电必须经 PMIC ALDO3"与"GPIO1 是电源自锁脚"）都是**按这里的前提**做的，
> 引用它们时必须带上"对象是 3.97、不是本板"这一句；删掉本文件等于把那几十轮的适用范围抹掉。

> 确认选型（2026-09-13）：**Waveshare ESP32-S3-ePaper-3.97**（黑白双色墨水屏）  
> 固件工程：`hardware/zizhao-esp32s3/`（ESP-IDF 5.x）

## 为什么是这块

| 需求 | 板载 |
|------|------|
| 要屏、要文字、长待机 | 3.97" 800×480 黑白 ePaper，断电保持 |
| 一段一刷 | 双色刷新快于四色 1.54G（那块全刷约 20s 不可用） |
| 外放听素材 | NS4150B 功放 + ES8311 + MX1.25 喇叭口 |
| 锂电 | TG28 充放管理 + 3.7V 接口 |
| 交互 | 三方向拨轮 + PWR/BOOT |
| 存离线包 | Micro SD（离线音频/文本写这里）+ 8MB Flash / 8MB PSRAM（PICO-1 内置，boot 实测 8MB） |
| 传感器 | QMI8658、SHTC3、RTC（便于定时开关机） |

## 待到手实测（写进联调清单）

1. 局刷是否够「一段一刷」体验  
2. **麦克风单/双、有无 AEC**（外放回声）  
3. 中文字库体积 vs 8MB Flash（分区仅 nvs+otadata+phy+双 OTA，flash 无富余；离线包与大字库都指望 Micro SD）  
4. 外壳/3D 打印  

## 与服务端契约（已实现）

| 用途 | API |
|------|-----|
| 设备登录 | `POST /api/auth/device/login` `{device_id,passkey}` → `sid` |
| 离线清单 | `GET /api/offline/manifest` |
| 当日包 | `GET /api/offline/bundle`（**仅 review passed 才有 audio**） |
| 进度 | `POST /api/material/progress` |
| 电源策略 | `GET /api/device/power`（04:30 关 / 06:00 开 / 15min idle 再关） |

## 硬约束（固件必须实现）

1. 未 `audio_ready` **禁止**播 MP3  
2. 10 分钟无操作音量最小  
3. 关机序列：停播 → 存 progress → 关 WiFi → RTC deep sleep（watchdog 兜底）  
4. 配网：烧录 PassKey + 现场 AP `Zizhao-Setup-*`  

## 烧录前准备

- ESP-IDF 5.1+  
- 产线：`device_id` / `passkey` 写入 NVS（勿进 git）  
- 喇叭接 MX1.25；SD 格式化 FAT32  
