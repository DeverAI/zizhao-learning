/* 板型档案：一块固件只认一块板，切换在这里。
 *
 * 【为什么需要这一层】R59 真机鉴定（C:/esp/r59f_20260925_174338_run.log）确认在机的那块板
 * 不是本工程 R24~R57 一路按 3.97 图纸写的板，而是 **Waveshare S3_ePaper_1_54**：
 * 屏 200x200、引脚表 RST9/DC10/CS11/SCK12/MOSI13/BUSY8、屏电是 GPIO6（低=开）一只 GPIO 开关、
 * **整板没有 AXP2101**（0x34 在 47/48 与 41/42 两条总线上都 probe=ESP_FAIL）
 * ⇒ 那一整条"屏电必须经 PMIC ALDO3（I2C 写）"的前提对本板不成立，而引脚表整体错位一格
 * （旧表 DC9/CS10/SCLK11/MOSI12/RST46/BUSY3）。
 *
 * 【开关口径】与本仓库既有的 `ENABLE_*` 模块开关同族：改这一只常量即可换板，
 * 换板时 `main/CMakeLists.txt` 里的源集合会跟着换（3.97 的 `epd_driver.c` + `axp_panel_power.c`
 * 与 1.54 的 `epd_panel_1in54.c` 互斥，两边都叫 `epd_*` 那 8 个入口，同时编进镜像会重复定义）。
 *
 * 【本文件不含屏命令序列】那些在驱动里：3.97 = `epd_driver.c`，1.54 = `epd_panel_1in54.c`。
 * 引脚表在驱动文件里各自定义（沿用 `epd_driver.c:16-21` 的排布），这里只放**跨模块共用**的东西：
 * 几何、有没有 PMIC、按键脚、SD 脚。 */
#ifndef ZIZHAO_BOARD_PROFILE_H
#define ZIZHAO_BOARD_PROFILE_H

/* 1 = Waveshare S3_ePaper_1_54（200x200，无 PMIC，R59 实测）
 * 0 = 微雪 ESP32-S3-ePaper-3.97（800x480，屏电走 AXP2101 ALDO3，R33~R57 那一整条线的对象） */
#define BOARD_EPAPER_1IN54 1

#if BOARD_EPAPER_1IN54

#define EPD_WIDTH   200
#define EPD_HEIGHT  200

/* 板上没有 PMIC ⇒ 本工程所有 AXP 通路（含 GPIO1 电源自锁）在本板不存在。
 * main.c 的 `axp_pwr_hold_begin()` 与 epd 驱动里的开轨步骤都按这一只走。 */
#define BOARD_HAS_PANEL_PMIC 0

/* 屏电：原厂 `port_power.cpp` 的 EPD_ON 是 `gpio_set_level(6, 0)` ⇒ **低=开**。
 * 归属未确立：v6 实测"拉高 6 之后 BUSY 仍然翻转"（断电臂 tr=1），所以"6 = 屏电"这条
 * 只到原厂代码口径，没到本板实测口径，见排查记录 §38.30 未确立项。 */
#define BOARD_EPD_PWR_PIN 6

/* 本板可当按键用的脚：BOOT=0（strapping，运行期按下安全）、PWR 键=18。
 * 3.97 那套"拨轮 up/down/press"在本板没有对应物，见 buttons.c。 */
#define BOARD_BTN_A_PIN   0
#define BOARD_BTN_B_PIN   18

/* SD 走 1-bit SDMMC 控制器：本板原厂引脚表 CLK=39 / CMD=41 / D0=40（无 D1..D3）。
 * 未在本板实测过挂载（R59 只做了屏与总线的鉴定），见 offline_store.c 里同一条注释。 */
#define BOARD_SD_CLK 39
#define BOARD_SD_CMD 41
#define BOARD_SD_D0  40

#else /* ---- 微雪 ESP32-S3-ePaper-3.97 ---- */

#define EPD_WIDTH   800
#define EPD_HEIGHT  480

#define BOARD_HAS_PANEL_PMIC 1
/* 3.97 的屏电不是 GPIO，是 AXP2101 的 ALDO3（I2C 写寄存器）；PWR_OUT=GPIO1 是电源自锁脚。
 * 具体脚号在 axp_panel_power.c / epd_driver.c 里。 */
#define BOARD_EPD_PWR_PIN (-1)
/* 拨轮 up=4 / press=5 / down=6，BOOT=0；PWR 走 TG28 电源键、不是 GPIO。 */
#define BOARD_BTN_A_PIN   0
#define BOARD_BTN_B_PIN   (-1)
/* 官方 05_SD_Test 的 4 线 SDMMC：CLK16 CMD17 D0=15 D1=7 D2=8 D3=18。 */
#define BOARD_SD_CLK 16
#define BOARD_SD_CMD 17
#define BOARD_SD_D0  15

#endif /* BOARD_EPAPER_1IN54 */

#define EPD_STRIDE  (EPD_WIDTH / 8)            /* 1.54: 25 字节/行；3.97: 100 */
#define EPD_FB_SIZE (EPD_STRIDE * EPD_HEIGHT)  /* 1.54: 5000 字节；3.97: 48000 */

#endif
