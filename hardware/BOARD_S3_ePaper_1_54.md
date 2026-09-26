# 微雪 Waveshare **S3_ePaper_1_54** 硬件落地说明（= 在机的那块板）

> 定案时间 2026-09-25（R58 烧原厂整片固件读出板名 + R59 pdiag 矩阵鉴定）。
> 本文件取代 `BOARD_ePaper397.md` 成为**当前在机板**的档案；3.97 那份保留，它记的是
> R24~R57 那条线当初按图纸建立的前提（那些前提对本板不成立，见下）。
> 单一真值在代码里：`hardware/zizhao-esp32s3/main/board_profile.h`（`BOARD_EPAPER_1IN54 1`）。
> 本文件每一行都标了它的出处；**没出处的那条一律写"未确立"**。

## 一、板是怎么定下来的（两条独立证据）

| 证据 | 读数 | 出处 |
|------|------|------|
| 原厂固件自己报板名 | boot banner `Project name: 02_ePaper_1_54_Test` | `hardware/20260925_R58_原厂1_54固件启动120s.log`；读法表见 `烧录须知.md` 〇-补4 |
| 我方鉴定固件的 GPIO 矩阵 | 360 组 `MAP` 行**全部** `tr=0/-1`（没有一组让 BUSY 翻转）⇒ 逐脚试出来的不是"哪组能用"，而是 3.97 那套脚在本板根本不动 | 载体 `hardware/20260925_R59板型鉴定判据摘录.txt`（本遍现跑 `grep -c "MAP en="` = 360、`grep -c "tr=0/-1"` = 360） |
| 鉴定固件的总线对照 | `I2CID bus=47/48 addr=34 probe=ESP_FAIL` 与 `bus=41/42 addr=34 probe=ESP_FAIL` 四遍同形 | 同一只载体（`0x34` 那 8 行）；结论叙述见排查记录 §38.30 |
| 移植后首刷 | `epd154 init done (PWR6 RST9 DC10 CS11 SCLK12 MOSI13 BUSY8, 200x200 stride=25 fb=5000 B)` + `panel blanked (200x200)` | 同一只载体第 688/690 与 711/713 行（两遍） |

**结论的强度**：板名那条是**别人固件打印的**，属正面事实；引脚表那条是我方实测。两者互相独立。

## 二、几何与帧缓冲（代码现读，非图纸）

| 项 | 值 | 出处 |
|----|----|------|
| 屏分辨率 | 200 × 200，1 bpp | `board_profile.h`（`EPD_WIDTH/EPD_HEIGHT`，`BOARD_EPAPER_1IN54` 分支） |
| 行距 / 帧缓冲 | stride 25 B/行、fb 5,000 B | 同文件 `EPD_STRIDE` / `EPD_FB_SIZE`；开机行 `epd154 init done (... 200x200 stride=25 fb=5000 B)` |
| 屏的确切型号（控制器料号） | **未确立** —— 只到"Waveshare 1.54 吋 200×200"这一级 | 点名：整条 R58~R61 线没有读过控制器 ID |

## 三、引脚表（与 3.97 的旧表整体差一格，这是 R24~R57 判据作废的直接原因）

| 功能 | 本板 | 旧 3.97 表 | 出处 |
|------|------|-----------|------|
| RST | **9** | 46 | `epd_panel_1in54.c:69` |
| DC | **10** | 9 | `:70` |
| CS | **11** | 10 | `:71` |
| SCLK | **12** | 11 | `:72` |
| MOSI | **13** | 12 | `:73` |
| BUSY | **8** | 3 | `:74` |
| 屏电 | **6**，低=开 | 无（走 AXP2101 ALDO3，I²C 写） | `:75` + `board_profile.h`（引原厂 `port_power.cpp` 的 `EPD_ON = gpio_set_level(6, 0)`） |
| 可当按键用的脚 | **只有 BOOT=0** | 拨轮 up4/press5/down6 + BOOT0 | `buttons.c:19`（`PIN_BTN_A = BOARD_BTN_A_PIN`） |
| `PWR_BUTTON=18` | **故意不配** | —（TG28 电源键，不是 GPIO） | `buttons.c:12-17` 两条理由：① 18 号在本板走什么电路**未实测**，配错方向的后果不是读不到键而是把板子关掉；② 6 号已经是屏电，R59 之前把它当"拨轮下"用正是幻影按键的来源 |
| SD（1-bit SDMMC） | CLK=39 CMD=41 D0=40，无 D1..D3 | CLK16 CMD17 D0..D3=15/7/8/18 | `board_profile.h`；**本板从未挂载成功**（卡 `send_op_cond 0x107`，未定位） |

**整板没有 panel PMIC**：`board_profile.h` 里 `BOARD_HAS_PANEL_PMIC 0`，依据是 `0x34` 在 47/48 与 41/42 两条总线上 `probe=ESP_FAIL`（排查记录 §38.30）。
⇒ R33~R57 那一整条"屏电必须经 PMIC ALDO3（I²C 写）"的前提、以及 R53 那条"GPIO1 是电源自锁脚"的根因，**都不适用于本板**；那批位碰探针结论的适用范围要按这个范围重读。

## 四、1.54 版面常数（R60 修过一次重叠，常数按字模真实高度重排）

| 项 | 值 | 出处 |
|----|----|------|
| 消息区顶 y | `LAY_MSG_Y = 6` | `eink_display.c`（`BOARD_EPAPER_1IN54` 分支） |
| 消息区底 | `LAY_MSG_PAGE_BOT = EPD_HEIGHT - 16 = 184` | 同上 |
| 消息区宽 | `LAY_MSG_W = EPD_WIDTH - 12 = 188` | 同上 |
| 页码行 | 右下角、基线 y = `EPD_HEIGHT - 16`，用 ASCII16 | 同上 |
| 字模高 | CJK32 **43** / LATIN32 31 / ASCII16 16 / DIGIT96 128 | `ui_font.c` 各 `uif_glyph_t` 第三字段 |
| 字库子集只数 | ASCII16 95、LATIN32 95、CJK32 **193**、DIGIT96 12 | 现跑 `grep -c "^const uif_glyph_t <族>_g" ui_font.c` |
| R60 那条缺陷 | 把 `ascent`(34) 当字模高 ⇒ 消息页 6 行每行重叠 7px、末行 33px 越屏底 | 排查记录 §38.31；修法是行距钳到本行真实字模高 + `pick_compact` |

## 五、翻页与刷新（R61 补的三段链路）

- 显示侧有"第 k 页"概念：`render_msg_page(page)` 每页打一条结构化行 `msg paging: bytes=… lines=… pages=… req_page=… shown_page=… map=[…]`，判据行见取证件 `hardware/r61_evidence_diag_full_20260926_110814.txt`。
- 页面环：`ui_browse_next()`（`main.c`），环 = 消息第 1..N 页 → 时钟页 → 状态页 → 回第 1 页；一只键只能往前走，因为本板可当按键用的只有 BOOT=0。
- **局刷未开**：`ENABLE_EINK_PARTIAL 0`（`eink_display.c`）⇒ 每次翻页都是全刷；代码在镜像里但没有调用者。
- 分页自检默认关：`EINK_PAGE_SELFTEST 0`（`main.c`）⇒ 出货镜像里没有那段诊断文本（负向对照载体 `hardware/r61_evidence_ship_full_20260926_111313.txt`）。

## 六、现场态（2026-09-26 11:2x 现跑）

- 构建目录 `C:/esp/zproj/build/zizhao_esp32s3.bin`：**1,108,336 B**，md5 `42b6b16fbb34505d083bd9dd0d3f33cb`，`bin[176:184]` = `a23c5df6b46f8293` == `sha256(.elf)` 的 hex 前 16 位（等式本遍现算，全摘要 `bin[176:208] == sha256(elf)` 同遍成立）。
- 板上 == 待烧：本轮 6 烧 6 抓，最后那烧的就是这一只（boot 行 `ELF file SHA256: a23c5df6b46f8293…`，在同一只取证件第 6 行）。
- **肉眼确认过屏亮**（2026-09-25 18:5x，R59 首刷之后），但**"看到第二页"= 0 次**、**用户真按 BOOT = 0 次**（页面环那 5 格是 `buttons_inject` 注入走通的，注入路径跳过 `pressed()`/`debounce()`）。

## 七、本文件没说的、也还没做的事（点名）

屏的确切料号 · SD 挂载从未成功 · 局刷从未实装调用者 · 学习内容那一页从未显示过（`offline_store_load_text` 显示侧 0 个调用者）· 1800 s 配网闸门 + 6 h 深睡这条产品级陷阱仍未改 · 18 号脚走什么电路从未实测。

**GPIO6 的归属为什么仍未确立**：`board_profile.h` 那句"低=开"来自原厂 `port_power.cpp` 的 `EPD_ON = gpio_set_level(6, 0)`，属**代码口径**。v6 那遍的供电/断电对照臂实测是
`OFF-CTRL armA_idle_tr=0 armB_on_tr=1 armC_off_tr=1`（载体第 627 行），而它自己印的判决三条件是 `B>=2 且 C==0 且 A==0`
⇒ **B=1 < 2、C=1 ≠ 0，三条里两条不成立**（详见 §38.30 那条"未兑现的判据"）。同一批里我方移植后的驱动倒是真判活了
（`epd154 init done` + `panel blanked`，载体第 688/690 行）⇒ 对照臂那次失败只否证它自己的前提，不能反过来预测移植成败，
也就**没能把 6 号脚钉死成"屏电"**。
