# 首次烧录保姆级教程 · 微雪 ESP32-S3-ePaper-3.97

> 目标：把 `hardware/zizhao-esp32s3/` 的固件从零烧进一块全新（或空 NVS）的开发板，并判断“烧录是否成功”。
> 适用系统：Windows 10/11。命令以 PowerShell 为准，标注“IDF 终端”的必须在 ESP-IDF 命令行里跑。

---

## 0. 先读这段：当前固件的真实状态（决定你该看到什么）

本仓库固件是**可编译、可启动、可联网跑主流程**的工程，但以下模块仍是串口打日志的骨架，**墨水屏首次烧录不会亮、不会刷新画面**：

| 模块 | 状态 | 首次烧录的表现 |
|------|------|----------------|
| `main.c` 主流程 / 校时 / 登录 / 离线包 | 已实现 | 串口日志正常打印，能联网 |
| `eink_display.c` 墨水屏驱动 | **stub**（只 `ESP_LOG`） | 屏幕不变化属**正常**，别当成烧录失败 |
| `provision_ap.c` AP 配网门户 | **stub**（SoftAP 起，网页未接 esp_http_server） | 能搜到 `Zizhao-Setup-XXXX`，但门户填不了 |

所以本教程用**串口监视器输出**判断烧录成功，配网用**直接预写 NVS**（第 7 步），不走还没做完的 AP 门户。

---

## 1. 准备硬件与识别串口

1. 一根**数据线**（不是只能充电的那种）连接板子的 **USB-C（靠 ESP32-S3 主控那颗口）** 到电脑。
2. 打开“设备管理器 → 端口 (COM 和 LPT)”，记下新出现的 `COMx`：
   - 显示 `USB Serial Device (COMx)` 或 `ESP32-S3 Device` 一类：这是 S3 的**原生 USB（USB-CDC/JTAG）**，一般免驱，直接用。
   - 显示 `Silicon Labs CP210x` / `USB-SERIAL CH343` 一类：这是**外置 USB 转串口芯片**（不是原生 USB）。多数系统已自带驱动；若带感叹号则去装 **CH343** 或 **CP210x/CP2102** 驱动后重插。
   - 拔插 USB 看哪个口消失/出现，即可确认口号。

> 首次拿到板子如果插电脑没任何反应：按住 **BOOT** 不放，再按一下 **RST/EN** 后松开 BOOT，进入下载模式，设备管理器应出现 COM 口。**本仓库只登记了"三方向拨轮 + PWR/BOOT"（`hardware/BOARD_ePaper397.md` 交互那一行），没有登记过独立的 EN/RST 键，也没有肉眼确认过板上有没有** ⇒ 若你的板子上找不到这个键，改用一定有效的"按住 BOOT 的同时把 USB 拔出再插回"来触发下载模式。

---

## 2. 安装 ESP-IDF 5.1.x（离线安装器，最省事）

1. 下载 Espressif 官方 “ESP-IDF Tools Installer (Windows)” 离线包，选 **v5.1.x**（本工程按 5.1 写，5.2/5.3 一般也可）。
2. 安装时路径**全部用英文、无空格**（默认 `C:\Espressif` 即可）。
3. 装完开始菜单会出现 **`ESP-IDF 5.1 PowerShell Prompt`**——这就是“IDF 终端”，后续 `idf.py` 命令都在这里跑。
4. 验证：在 IDF 终端里执行
   ```powershell
   idf.py --version
   ```
   打印出 `ESP-IDF v5.1.x` 即成功。

> 不要在自己普通的 PowerShell 里直接敲 `idf.py`，会报“不是内部或外部命令”——因为环境变量只在 IDF 终端里生效。

---

## 3. 用 IDF 终端进入工程并配置目标芯片

```powershell
# 把 <你的路径> 换成实际路径
cd "<你的路径>\自招学习\hardware\zizhao-esp32s3"
idf.py set-target esp32s3
```

`set-target` 会读取本目录的 `sdkconfig.defaults`，自动应用关键配置：8MB Flash（ESP32-S3-PICO-1 内置，boot 日志 `SPI Flash Size : 8MB` 可核对）、QIO 80MHz、自定义双 OTA 分区表、应用回滚等。**看到成功提示即完成**。

---

## 4. 编译固件

```powershell
idf.py build
```

- 首次编译要几分钟（要编 bootloader + 全部组件）。
- 结尾出现 `Project build complete.` 即成功，产物在 `build/` 下（`bootloader.bin`、`partition_table.bin`、`zizhao_esp32s3.bin`）。
- `main/CMakeLists.txt` 的 `REQUIRES` 用的是真实组件名（SNTP 走 `lwip`、OTA 走 `app_update`）。若仍报“component not found / 头文件找不到”，按报错把对应组件补进 `REQUIRES` 再 `idf.py build`。
- 若已有 `sdkconfig` 文件，`set-target`/`sdkconfig.defaults` 的改动可能被旧配置覆盖：可先删掉 `build/` 与 `sdkconfig` 再重来。

---

## 5. 烧录 + 打开串口监视器

板子插好，确认第 1 步的 `COMx`：

```powershell
idf.py -p COM3 flash monitor
```

把 `COM3` 换成你的实际口号。这条命令会：写入 bootloader/分区表/应用（**注意 `idf.py flash` 只覆盖镜像所在区域，不擦整颗 Flash，也不会清掉你之前写好的 NVS**）→ 自动打开监视器。

看到类似：
```
Wrote N bytes at 0x... (Verify OK)
Hash of data verified.
...
Executing action: monitor
```
即写入完成，接着监视器会打印启动日志——**首烧是否成功以第 6 步的日志判据为准**。退出监视器按 `Ctrl+]`（不是直接关窗口）。

> 只想重烧不重编：`idf.py -p COM3 flash monitor`；只退出/重进监视器另开窗口用 `idf.py -p COM3 monitor`。

---

## 6. 判断“首次烧录成功”：看串口日志

**关键认知**：空 NVS 的全新板子，`main.c` 会停在“等待配网”的死循环里（每 2 秒读一次 NVS，看有没有写进 passkey），**不会进主循环、不会刷新时钟**。这是设计如此，不是卡死。所以首烧成功的标志是“稳定停在这里且不再重启/崩溃”。

`monitor` 里正常应看到（TAG 与顺序按真实代码：`buttons_init` 在 `eink_init` 之前）：
```
I (2) boot: ESP-IDF v5.1.x ...
I (xxx) boot: ... ota:0 ...                       # 分区表加载
I (xxx) btn: buttons ready (wheel u/d/press + pwr)
I (xxx) eink: eink stub — replace with Waveshare driver   # 墨水屏 stub，属正常
I (xxx) eink: MSG 请现场配网
W (xxx) prov: SoftAP Zizhao-Setup-XXXX — portal http://192.168.4.1/ (HTTP stub)
```
然后**没有更多输出**（在等 NVS）。到此即算固件烧录并运行成功。屏幕全程不变化是正常的（驱动是 stub）。

常见“假失败”：
- 反复 `abort()`/`Guru Meditation` 且报分区/flash 相关：多为 Flash 模式不匹配，见第 8 步 DIO 回退。
- `Brownout detector was triggered`：供电不足，换好的数据线/USB 口，别用充电头。
- 一直看不到上面的 `btn/eink/prov` 行、只有 boot 后重启：多半是没真正进主程序，检查是否 `build` 后没重烧、或串口波特率乱码。

> 第 7 步把凭据写进 NVS 后按 RESET（或重开 monitor）重启，板子才会继续往下走：连 WiFi → 校时 → 登录 → 拉离线包 → 进主循环周期刷时钟页（日志里会出现 `clock:` 与 `zizhao:` 的行）。

---

## 7. 让它联网：直接预写 NVS（AP 门户做完前用这个）

固件联网需要 5 个值（命名空间 `zizhao`）：`device_id`、`passkey`、`server_url`、`wifi_ssid`、`wifi_pass`（STA 连接与登录缺一不可，`wifi_pass` 对开放网络可留空串）。
- `device_id` / `passkey`：在**网页“设备”页**签发。
- `server_url`：跑后端的电脑，形如 `http://192.168.1.50:8010`（手机能打开 `http://<该IP>:8010/` 为准，注意 Windows 防火墙放行 8010）。

**步骤 A：在仓库外**（例如 `%TEMP%`）**准备 nvs 内容文件**，不要把含 passkey 的 `nvs.csv`/`nvs.bin` 放在工程目录里——`.gitignore` 没盖它，容易一个 `git add -A` 把产线凭据提交进仓库。下面假设文件放在 `%TEMP%\nvs.csv`。注意列是 `key,type,encoding,value`，先声明命名空间行 `zizhao,namespace,,`，其后每个键都用 `data,string`（键名**不带**命名空间前缀，固件里 `nvs_open("zizhao")` 再按键读）：
```csv
key,type,encoding,value
zizhao,namespace,,
device_id,data,string,dev_xxxxxxxx
passkey,data,string,在这里填网页签发的passkey
server_url,data,string,http://192.168.1.50:8010
wifi_ssid,data,string,你的WiFi名
wifi_pass,data,string,你的WiFi密码
```

> `server_url` 末尾**不要带 `/`**，否则固件拼出 `//api/system/time` 会命中不到路由。

**步骤 B：生成 nvs.bin**（`nvs_partition_gen.py` 在 `components/nvs_flash/nvs_partition_generator/` 下，**不是** `partition_table/`；`generate` 参数顺序是 `输入csv 输出bin 大小`，本分区大小 `0x6000`）：
```powershell
python "$env:IDF_PATH\components\nvs_flash\nvs_partition_generator\nvs_partition_gen.py" generate "$env:TEMP\nvs.csv" "$env:TEMP\nvs.bin" 0x6000
```
> 若提示找不到脚本：`dir "$env:IDF_PATH\components\nvs_flash" -Recurse -Filter nvs_partition_gen.py` 定位实际路径。

**步骤 C：写到 0x9000（`partitions.csv` 里 nvs 的偏移）**：
```powershell
idf.py -p COM3 flash           # 先确保 app 已烧好
python -m esptool --chip esp32s3 -p COM3 -b 460800 --before default_reset --after hard_reset write_flash 0x9000 "$env:TEMP\nvs.bin"
```

**步骤 D：重开监视器验证联网**：
```powershell
idf.py -p COM3 monitor
```
应看到 `clock: SNTP synced` 或 `clock: http time synced: ...`、`zizhao: login ok`、`今日已缓存/离线模式` 等。若 SNTP 超时会自动走服务端 HTTP 对时（`GET /api/system/time`）。

> 配网后想重来：`idf.py -p COM3 erase-flash` 清空整颗 Flash（会连 NVS 一起擦，之后需重烧固件+重写 NVS）。

---

## 8. 疑难速查

| 现象 | 处理 |
|------|------|
| 电脑不出现 COM 口 | 换数据线/换 USB 口；装 CH343/CP210x 驱动；按住 BOOT 点 RESET 进下载模式 |
| `idf.py` 不是命令 | 你用的是普通终端，改开“ESP-IDF 5.1 PowerShell Prompt” |
| build 报 flash/分区大小错 | 确认 `set-target esp32s3` 跑过，`sdkconfig.defaults` 生效 |
| 启动反复重启、报 flash 相关 | 该板若为 DIO 封装：在 IDF 终端 `idf.py menuconfig` → Serial flasher config → Flash SPI mode 改 **DIO**、SPI speed 降一档，再 `idf.py build flash` |
| 连上 WiFi 但 login 失败 | 手机验证能否开 `http://<serverIP>:8010/`；防火墙放行 8010；核对 `server_url/device_id/passkey` |
| OTA 升级后回退 | 已在 `main.c` 稳态处加 `esp_ota_mark_app_valid_cancel_rollback()`，正常不再回退；如自改代码请保留该调用 |
| 想擦干净重来 | `idf.py -p COM3 erase-flash` 后从第 5 步重新开始 |

> 断电保护：分区表为**双 OTA**（`ota_0/ota_1`），烧录中途断电不会变砖，重连重烧即可。

---

## 9. 烧录完成后与后端的配合

1. 后端起来：`cd backend` → `pip install -r requirements.txt` → `python -m uvicorn main:app --host 0.0.0.0 --port 8010`。
2. 网页“设备”页签发 `device_id/passkey`，填入第 7 步的 `nvs.csv`。
3. 板子登录后每 6 小时静默查 `GET /api/device/firmware/latest`（无手动升级入口，符合设计）。
