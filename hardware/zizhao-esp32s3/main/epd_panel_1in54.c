/* Waveshare S3_ePaper_1_54（200x200，SSD16xx 系命令集）墨水屏底层驱动。
 *
 * 【这一只文件是谁、凭什么存在】R33~R57 那一整条"屏为什么不亮"的线，对象是微雪
 * ESP32-S3-ePaper-3.97（800x480、屏电走 AXP2101 的 ALDO3、I2C 在 41/42）。R59 用一只独立的
 * 鉴定固件（`C:/esp/pdiag/main/pdiag_main.c`，v1~v6）在**同一块在机的板子**上实测出：
 *   · 47/48 才是真 I2C 总线（ACK 到 18/38/51/70），41/42 上 112 个地址全 `ESP_FAIL`
 *     ⇒ R24~R43 在 41/42 上测出的"全 NACK"量的是一根不是 I2C 的线；
 *   · **0x34(AXP2101) 在两条总线上都 probe=ESP_FAIL** ⇒ 本板没有 PMIC，
 *     "屏电必须经 ALDO3（I2C 写）"整条前提对本板作废；
 *   · 原厂件把 GPIO[9]/[10]/[11] 配成输出、GPIO[8] 配成输入带上拉，与原厂引脚表
 *     `EPD_RST_PIN=9 / DC=10 / CS=11 / SCK=12 / MOSI=13 / BUSY=8` 同素
 *     ⇒ 旧表（DC9/CS10/SCLK11/MOSI12/RST46/BUSY3）整体错位一格，RST/BUSY 更是两根别的脚；
 *   · 按上表逐字照抄原厂命令序列后，面板第一次给出正样本（载体 `C:/esp/r59f_20260925_174338_run.log`）：
 *     SWRESET 使 BUSY 高→低（`fall=1 ms=1`）、全刷 1761/1761/1762 ms（三次独立）、
 *     局刷 91 + 574 ms、`steps=14 timeouts=0 busy_fall_edges=6`。
 * 本文件就是把那份**实测跑通**的序列搬进本工程，对上 `epd_driver.h` 的 8 个入口，
 * 使 `eink_display.c` 以上各层不需要改动即可换板（换板开关在 `board_profile.h`）。
 *
 * 【与原厂 `epaper_driver_bsp.cpp` 的三处有意差异，逐条给理由】
 *   ① `read_busy()` 原厂是**无上限** `while(gpio_get_level(busy)==1) vTaskDelay(5)`。
 *      这里每一次等待都带上限（`EPD_BUSY_TIMEOUT_MS`），超时清 `s_ready` 交给上层监视任务重来。
 *      理由：本工程整机跑 30s 任务看门狗 + 深睡闸门，一条无上限的等待在面板被关机的那一刻
 *      就是"持锁方永不放锁"（同一条判断在 3.97 档案里已经付过学费，见 `epd_driver.c`
 *      `epd_wait_busy_ms` 上方整段）。
 *   ② 局刷装载 LUT 之前那次硬复位之后，这里**补发** 0x01/0x11/0x44/0x45/0x4E/0x4F
 *      （原厂 `EPD_Init_Partial()` 不补，靠上电默认值）。
 *      理由：全刷那一路是按"0x11=0x01 + Y 窗口 199→0 + 游标 (0,199)"推 5000 字节的；
 *      局刷若不重设同一套，两次写的 RAM 地址序列就不是同一套，而局刷的本质是
 *      `0x24(新) vs 0x26(旧)` 逐像素做差——两张平面若不是同一套地址，差出来的就是花屏。
 *      【未实测】这一处是推理，不是证据：原厂整窗局刷的**行序**对不对，只有肉眼能定，
 *      见排查记录 §38.30 未确立项。
 *   ③ CS 每次传输显式翻转（原厂也是这样，只是 `EPD_Init` 之外没有总线复用问题），
 *      与 3.97 档案保持一致的写法。
 *
 * 【局刷窗口参数为什么"收了不用"】`epd_display_partial()` 的 x0/y0/x1/y1 只进日志，
 * 不拿来缩小 RAM 窗口：R59 实测过的局刷形状是"整帧 5000 字节 + 原厂 partial LUT"，
 * 缩小窗口那一种（0x44/0x45 传非全屏 + 只推行内字节）**一块数据都还没测过**。
 * 代价可忽略：5000B 在 40MHz 硬件 SPI 上是 ~1ms，而真正决定刷多久的 LUT 差分本来就只看
 * "哪些像素与 0x26 不同"，缩小窗口不会让屏少驱动一个像素。见上面 ② 同一条理由。
 *
 * 帧缓冲布局：200x200 1bpp，行主序 stride=25B，MSB 在最左，1=白 0=黑
 * （与原厂 `EPD_DrawColorPixel` 的 `y*25+(x>>3)` 同一条，见该函数）。 */
#include <stdlib.h>
#include <string.h>

#include <stdatomic.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_err.h"
#include "esp_log.h"
#include "esp_timer.h"

#include "board_profile.h"
#include "epd_driver.h"

/* 全文件由这块板的存在与否来取舍：开关只有一处真值（`board_profile.h` 里的
 * `BOARD_EPAPER_1IN54`），CMake 里两只驱动**都**在 SRCS 中，选中的那只编译成实体、
 * 另一只被预处理器整只抹空。这样就不存在"CMake 与头文件两处开关各说一套"的漂移。
 * 与 `epd_driver.c` 顶部那条 `#if !BOARD_EPAPER_1IN54` 成对。 */
#if BOARD_EPAPER_1IN54

static const char *TAG = "epd154";

/* 引脚表来源见文件头。R59 之前本工程的 9/10/11/12 是 DC/CS/SCLK/MOSI，这里全不一样，
 * 换错开关不等于换错脚——两套脚号分别在两只驱动文件里，编译期就互不可见。 */
#define EPD_RST_PIN    9
#define EPD_DC_PIN    10
#define EPD_CS_PIN    11
#define EPD_SCLK_PIN  12
#define EPD_MOSI_PIN  13
#define EPD_BUSY_PIN   8
#define EPD_PWR_PIN   BOARD_EPD_PWR_PIN     /* 6：低=开（原厂 port_power.cpp EPD_ON） */

#define EPD_SPI_HOST        SPI2_HOST       /* 原厂 `EPD_SPI_NUM=SPI2_HOST`；S3 上这是 GPSPI2 */
#define EPD_SPI_HZ          (40 * 1000 * 1000)
#define EPD_LUT_BYTES       153             /* 0x32 后面推的那一段长度 */
#define EPD_LUT_TAIL        6               /* 0x3f/0x03/0x04x3/0x2c 那 6 个散值 */
#define EPD_LUT_LEN         (EPD_LUT_BYTES + EPD_LUT_TAIL)   /* =159，与原厂数组声明一致 */

/* 上限 = 实测最坏值 1762ms 的 4.5 倍。取 8s 而不是 2s：面板刚从断电里醒来那一档的
 * BUSY 时长没有第二个样本，宁可让监视任务多等一轮，也不把好屏判成死屏。
 * 持锁预算：一次全刷最坏 = 本函数一轮 init（含 SWRESET 的 0.5s 判活窗）+ 两次 5000B 写 + 8s
 * = 上限约 9s，仍在 `eink_display.c` 的显示锁闸门（20s）之内，与 3.97 档案同一档。 */
#define EPD_BUSY_TIMEOUT_MS         8000
/* 判活那一段"找上升沿"的最坏时长：v6 实测 SWRESET 后第一拍就读到高（busy_start=1），
 * 这里给 500ms 是为了"读不到高"也能在**本轮**出结论，而不是拖到 8s。 */
#define EPD_LIVENESS_WINDOW_MS      500
/* 连续两拍才算"看到"某一侧：同一根高阻线上单拍尖峰不作为判据（3.97 档案里 R32 P0/R33 P1-1
 * 两条同源结论，推导见 `epd_driver.c` `epd_wait_busy_ms` 体内那两段）。 */
#define EPD_BUSY_CONFIRM_MS         300     /* "一路低"早退：与 3.97 同值 */
#define EPD_TICK_MS                 1       /* CONFIG_FREERTOS_HZ=1000 ⇒ 一拍 1ms */

/* 两条 LUT 逐字抄原厂 `epaper_driver_bsp.cpp`（与 `port_display.cpp` 里那一对同名数组
 * 已用脚本逐值比过：159 个值三处全等）。不要"整理"它们的顺序。 */
static const uint8_t WF_FULL_1IN54[EPD_LUT_LEN] = {
    0x80, 0x48, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x40, 0x48, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0x48, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x40, 0x48, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x01, 0x00, 0x08, 0x01,
    0x00, 0x02, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x00, 0x00, 0x00, 0x22, 0x17, 0x41,
    0x00, 0x32, 0x20,
};
static const uint8_t WF_PARTIAL_1IN54_0[EPD_LUT_LEN] = {
    0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x00, 0x00, 0x00, 0x02, 0x17, 0x41,
    0xB0, 0x32, 0x28,
};

static spi_device_handle_t s_spi;
static volatile bool s_bus_ok;        /* 引脚+SPI 设备已配好（交还时清，见 epd_pins_release） */
static volatile bool s_ready;         /* 最近一次证据说面板在应答 */
static volatile bool s_partial_lut;   /* 局刷 LUT 已在面板里，不用每次局刷前重装载 */
static volatile bool s_cmd_dropped;   /* 本轮有没有任何一笔 SPI 写失败 */
static unsigned s_probe_round;
static atomic_bool s_probing;         /* 认领标记：判活与无锁兜底不能同时动引脚/句柄 */

/* ---------------- 总线原语 ---------------- */

static void cs_low(void)  { gpio_set_level(EPD_CS_PIN, 0); }
static void cs_high(void) { gpio_set_level(EPD_CS_PIN, 1); }
static void dc_cmd(void)  { gpio_set_level(EPD_DC_PIN, 0); }
static void dc_data(void) { gpio_set_level(EPD_DC_PIN, 1); }

/* 单笔写失败只记标记、不 panic：调用方在每个"命令流写完、要触发显示"的关口查这个标记。
 * 半截帧进 0x24/0x26 会被局刷当基准用，那比不刷糟得多（同一条判断见 epd_driver.c
 * `epd_display_full` 里 `s_cmd_dropped` 那一段）。 */
static void spi_write(const uint8_t *buf, size_t len)
{
    if (!s_spi) {
        s_cmd_dropped = true;
        return;
    }
    spi_transaction_t t;
    memset(&t, 0, sizeof(t));
    t.length = 8 * len;
    t.tx_buffer = buf;
    const esp_err_t e = spi_device_polling_transmit(s_spi, &t);
    if (e != ESP_OK) {
        s_cmd_dropped = true;
        ESP_LOGE(TAG, "spi write failed (%d B): %s", (int)len, esp_err_to_name(e));
    }
}

static void epd_cmd(uint8_t c)
{
    cs_low();
    dc_cmd();
    spi_write(&c, 1);
    cs_high();
}

static void epd_data(uint8_t d)
{
    cs_low();
    dc_data();
    spi_write(&d, 1);
    cs_high();
}

/* 整帧/整段 LUT：一次 CS 拉低推完，与原厂 writeBytes 同形（原厂每条数据都翻一次 CS，
 * 只有 writeBytes 不翻；这里保持一致，避免在"CS 每字节翻一次"这件事上造出第三种形状）。 */
static void epd_data_buf(const uint8_t *buf, size_t len)
{
    cs_low();
    dc_data();
    spi_write(buf, len);
    cs_high();
}

/* ---------------- BUSY ---------------- */

/* BUSY：高=忙，低=空闲，脚在面板侧是开漏输出 ⇒ 必须带上拉读（v6 普查里 8 号脚
 * 上下拉都读高，即"被外部驱动"那一档，与原厂把它配成 input+pullup 一致）。
 * `require_high` 为真时判据是"先连续两拍高、再连续两拍低"：只看"读到低"不能证明它应答过
 * （0V 钳位与真空闲读出来一样），这条在 3.97 档案里是 R29 收紧、R31 P0 才修好"判据在采样窗内
 * 可达"的那一档，推导全在 `epd_driver.c` 同名函数上方，这里只保留形状。
 * 两个计时都从**当前这一段**算：读到相反电平就各自复位，否则"低-高-低"会被判成刷完。 */
static bool epd_wait_busy_ms(int timeout_ms, bool require_high)
{
    uint32_t t0 = xTaskGetTickCount();
    int hi_run = 0, lo_run = 0, single_hi = 0;
    int seen_high = -1, first_low = -1, low_start = -1;

    for (;;) {
        uint32_t el = (uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS;
        if (gpio_get_level(EPD_BUSY_PIN) == 0) {
            if (hi_run == 1) single_hi++;
            hi_run = 0;
            lo_run++;
            if (first_low < 0) first_low = (int)el;
            if (low_start < 0) low_start = (int)el;
            if (lo_run >= 2 && (!require_high || seen_high >= 0)) return true;
            if (require_high && el - (uint32_t)low_start >= EPD_BUSY_CONFIRM_MS) {
                ESP_LOGE(TAG, "BUSY never gave a qualified HIGH (>=2 beats): LOW run %dms straight"
                              " (started at %dms, first_low=%dms, unqualified single-beat highs=%d, cap=%dms)",
                         (int)(el - (uint32_t)low_start), low_start, first_low, single_hi, timeout_ms);
                return false;
            }
        } else {
            lo_run = 0;
            low_start = -1;
            if (seen_high < 0 && ++hi_run >= 2) seen_high = (int)el;
        }
        if (el > (uint32_t)timeout_ms) break;
        vTaskDelay(pdMS_TO_TICKS(require_high && seen_high < 0 ? EPD_TICK_MS : 20));
    }
    ESP_LOGE(TAG, "BUSY no accepted end within %dms (本行不下'面板没响应'的结论):"
                  " first_high=%dms first_low=%dms unqualified single-beat highs=%d",
             timeout_ms, seen_high, first_low, single_hi);
    return false;
}

static bool epd_wait_busy(void) { return epd_wait_busy_ms(EPD_BUSY_TIMEOUT_MS, true); }
static bool epd_wait_idle(int ms) { return epd_wait_busy_ms(ms, false); }

/* ---------------- 供电与引脚 ---------------- */

/* 屏电：原厂 `port_power.cpp` 的 EPD_ON 是 `gpio_set_level(6, 0)`（低有效），
 * 且该脚配成 OUTPUT + 内部上拉。上电后原厂再等 10ms 才碰 SPI，这里等 20ms。 */
static void epd_rail_on(void)
{
    gpio_set_direction(EPD_PWR_PIN, GPIO_MODE_OUTPUT);
    gpio_set_pull_mode(EPD_PWR_PIN, GPIO_PULLUP_ONLY);
    gpio_set_level(EPD_PWR_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
}

static void epd_rail_off(void)
{
    gpio_set_level(EPD_PWR_PIN, 1);
    gpio_reset_pin(EPD_PWR_PIN);
}

/* 把通向面板的 5 根脚连同 SPI 设备/总线一起交还。
 * 注意交还后的状态是 `GPIO_MODE_DISABLE` + 约 45K 内部上拉（`gpio_reset_pin` 就是这样，
 * 输入缓冲还是关的）——不是"输入"、不是高阻、更不是断开；口径推导见 epd_driver.c
 * `epd_pins_release` 内那一大段，这里不重抄。 */
static void epd_pins_release(void)
{
    bool spi_down = true;
    const char *bus_s = "SPI 句柄仍在，本轮未释放总线（remove 没成功）";

    if (s_spi == NULL) bus_s = "本轮无 SPI 句柄（上一轮已拆掉或从未建）";
    if (s_spi) {
        const esp_err_t re = spi_bus_remove_device(s_spi);
        if (re == ESP_OK) s_spi = NULL;
        else {
            spi_down = false;
            ESP_LOGW(TAG, "spi_bus_remove_device: %s → 保留句柄，SCLK/MOSI 本轮不复位", esp_err_to_name(re));
        }
    }
    if (spi_down) {
        const esp_err_t fe = spi_bus_free(EPD_SPI_HOST);
        if (fe == ESP_OK) bus_s = "SPI 总线已释放";
        else if (fe == ESP_ERR_INVALID_STATE)
            bus_s = "spi_bus_free 回 INVALID_STATE：总线本就未安装，或还有设备没拆（两种同码）";
        else {
            bus_s = "SPI 总线释放失败";
            ESP_LOGW(TAG, "spi_bus_free: %s → SCLK/MOSI 可能仍被 SPI 占着", esp_err_to_name(fe));
        }
    }
    static const int kPins[] = { EPD_RST_PIN, EPD_DC_PIN, EPD_CS_PIN, EPD_SCLK_PIN, EPD_MOSI_PIN };
    for (size_t i = 0; i < sizeof(kPins) / sizeof(kPins[0]); i++) {
        if (!spi_down && (kPins[i] == EPD_SCLK_PIN || kPins[i] == EPD_MOSI_PIN))
            continue;   /* 控制器还在驱动这两根，复位成输入只会让"交还"这句话变成假的 */
        gpio_reset_pin(kPins[i]);
    }
    s_bus_ok = false;
    ESP_LOGI(TAG, "panel pins released to DISABLE+pull-up(输入缓冲关，别拿 gpio_get_level 读), %s;"
                  " 下一轮 probe 会整套重建", bus_s);
}

static bool epd_bus_setup(void)
{
    if (s_bus_ok) return true;

    spi_bus_config_t buscfg = {
        .miso_io_num = -1,
        .mosi_io_num = EPD_MOSI_PIN,
        .sclk_io_num = EPD_SCLK_PIN,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = EPD_FB_SIZE,   /* 整帧 5000B 一笔推完，与原厂 W*H 的口径同档 */
    };
    spi_device_interface_config_t devcfg = {
        .spics_io_num = -1,               /* CS 手动翻，理由见文件头 ③ */
        .clock_speed_hz = EPD_SPI_HZ,
        .mode = 0,
        .queue_size = 7,
    };
    esp_err_t e = spi_bus_initialize(EPD_SPI_HOST, &buscfg, SPI_DMA_CH_AUTO);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "spi_bus_initialize failed: %s", esp_err_to_name(e));
        return false;
    }
    if (e == ESP_ERR_INVALID_STATE && !s_spi) {
        /* 总线还在但没有句柄：上一轮 remove 掉了设备却没拆成总线。仍然要 add，否则下面全静默失败。 */
        ESP_LOGW(TAG, "spi_bus_initialize: 总线仍在但无句柄 → 重新 add device"
                      "（注意不会重做 SCLK/MOSI 的引脚矩阵连接）");
    }
    if (!s_spi) {
        e = spi_bus_add_device(EPD_SPI_HOST, &devcfg, &s_spi);
        if (e != ESP_OK) {
            ESP_LOGE(TAG, "spi_bus_add_device failed: %s", esp_err_to_name(e));
            return false;
        }
    }

    gpio_config_t out = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << EPD_RST_PIN) | (1ULL << EPD_DC_PIN) | (1ULL << EPD_CS_PIN),
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    if (gpio_config(&out) != ESP_OK) {
        ESP_LOGE(TAG, "gpio_config(RST/DC/CS) failed → 引脚其实没驱动，本轮不认账");
        return false;
    }
    gpio_config_t in = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = 1ULL << EPD_BUSY_PIN,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    if (gpio_config(&in) != ESP_OK) {
        ESP_LOGE(TAG, "gpio_config(BUSY) failed → 判活读不到脚，本轮不认账");
        return false;
    }
    gpio_set_level(EPD_RST_PIN, 1);
    gpio_set_level(EPD_CS_PIN, 1);
    gpio_set_level(EPD_DC_PIN, 0);
    s_bus_ok = true;
    return true;
}

/* ---------------- 面板命令序列（逐字对齐原厂，除文件头点明的三处有意差异） ---------------- */

static void epd_hw_reset(void)
{
    gpio_set_level(EPD_RST_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(50));
    gpio_set_level(EPD_RST_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(EPD_RST_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(50));
}

/* 原厂 EPD_SetWindows(0, W-1, H-1, 0) + EPD_SetCursor(0, H-1) 的同一套寄存器值。
 * 0x44 的两端是**字节**地址（原厂在函数内部 >>3），0x45 是像素且"终点在前、起点在后"。
 * 这个奇怪顺序与 0x11=0x01 + 0x01 第三位一起构成原厂实测跑通的行序，别"顺手纠正"它。 */
static void epd_set_full_frame_window(void)
{
    epd_cmd(0x44);
    epd_data(0);
    epd_data((EPD_WIDTH - 1) / 8);
    epd_cmd(0x45);
    epd_data((EPD_HEIGHT - 1) & 0xFF);
    epd_data((EPD_HEIGHT - 1) >> 8);
    epd_data(0);
    epd_data(0);
    epd_cmd(0x4E);
    epd_data(0);
    epd_cmd(0x4F);
    epd_data((EPD_HEIGHT - 1) & 0xFF);
    epd_data((EPD_HEIGHT - 1) >> 8);
}

static bool epd_set_lut(const uint8_t *lut)
{
    epd_cmd(0x32);
    epd_data_buf(lut, EPD_LUT_BYTES);
    if (!epd_wait_idle(200)) return false;
    epd_cmd(0x3F); epd_data(lut[153]);
    epd_cmd(0x03); epd_data(lut[154]);
    epd_cmd(0x04); epd_data(lut[155]); epd_data(lut[156]); epd_data(lut[157]);
    epd_cmd(0x2C); epd_data(lut[158]);
    return !s_cmd_dropped;
}

/* 全刷用的 init：硬复位 → SWRESET（这一趟就是判活本身）→ 扫描/窗口/游标 → 温度与波形加载 → 全刷 LUT。 */
static bool epd_panel_init(void)
{
    s_cmd_dropped = false;
    epd_hw_reset();
    if (!epd_wait_idle(200)) {
        ESP_LOGW(TAG, "panel still busy after hard reset");
        return false;
    }
    epd_cmd(0x12);                          /* SWRESET */
    if (!epd_wait_busy_ms(EPD_LIVENESS_WINDOW_MS, true)) {
        ESP_LOGW(TAG, "no BUSY high->low after SWRESET: 面板没应答（脚/电/屏三者之一），本轮判死");
        return false;
    }
    epd_cmd(0x01);                          /* driver output control: 199 + 扫描方向位 */
    epd_data((EPD_HEIGHT - 1) & 0xFF);
    epd_data((EPD_HEIGHT - 1) >> 8);
    epd_data(0x01);
    epd_cmd(0x11); epd_data(0x01);          /* data entry mode */
    epd_set_full_frame_window();
    epd_cmd(0x3C); epd_data(0x01);          /* border waveform */
    epd_cmd(0x18); epd_data(0x80);
    epd_cmd(0x22); epd_data(0xB1);          /* load temperature + waveform setting */
    epd_cmd(0x20);
    if (!epd_wait_idle(200)) return false;
    if (!epd_set_lut(WF_FULL_1IN54)) {
        ESP_LOGW(TAG, "full LUT load failed/timed out");
        return false;
    }
    return !s_cmd_dropped;
}

/* 局刷 LUT 装载（原厂 EPD_Init_Partial）。与原厂的唯一差别就是文件头 ②：硬复位之后补发
 * 那三条窗口/方向寄存器，让局刷写的 RAM 地址序列与全刷**同一套**。 */
static bool epd_panel_init_partial(void)
{
    s_cmd_dropped = false;
    epd_hw_reset();
    if (!epd_wait_idle(200)) return false;
    if (!epd_set_lut(WF_PARTIAL_1IN54_0)) {
        ESP_LOGW(TAG, "partial LUT load failed/timed out");
        return false;
    }
    epd_cmd(0x37);                          /* 原厂那 10 个字节，逐字照抄 */
    epd_data(0x00); epd_data(0x00); epd_data(0x00); epd_data(0x00); epd_data(0x00);
    epd_data(0x40); epd_data(0x00); epd_data(0x00); epd_data(0x00); epd_data(0x00);
    epd_cmd(0x3C); epd_data(0x80);          /* partial border waveform */
    epd_cmd(0x01);
    epd_data((EPD_HEIGHT - 1) & 0xFF);
    epd_data((EPD_HEIGHT - 1) >> 8);
    epd_data(0x01);
    epd_cmd(0x11); epd_data(0x01);
    epd_set_full_frame_window();
    epd_cmd(0x22); epd_data(0xC0);
    epd_cmd(0x20);
    if (!epd_wait_idle(200)) return false;
    return !s_cmd_dropped;
}

/* ---------------- 对外 8 个入口（契约见 epd_driver.h） ---------------- */

static bool probe_attempt(void)
{
    /* 计数在**做**这一次尝试之前：上层日志要能对上 `probe #N`，而本函数每一条早退出口
     * 都算"做过一次尝试"（3.97 档案把它放在电轨闸门之后，是因为那里有一个"闸门挡住就不试"
     * 的分支；本板没有 PMIC，没有这一档）。 */
    s_probe_round++;
    epd_rail_on();
    if (!epd_bus_setup()) {
        epd_rail_off();
        return false;
    }
    if (!epd_panel_init()) {
        /* 判死就把通向一块**可能没电**的面板的脚交还：没电时把这些脚钉高，会经面板内部
         * ESD 二极管向 0V 的 EPD_VCC 倒灌（同一条防护见 epd_driver.c epd_pins_release 上方）。
         * 本板的屏电归属本身还没实测（见排查记录 §38.30 未确立项），所以这条更要留着。 */
        ESP_LOGW(TAG, "probe #%u failed → 交还引脚与屏电", s_probe_round);
        epd_pins_release();
        epd_rail_off();
        s_ready = false;
        s_partial_lut = false;
        return false;
    }
    if (!s_bus_ok || s_cmd_dropped) {
        /* 与 3.97 那只的差别：那边这一支只"结论作废"就把引脚留在原样返回，因为它的屏电在 AXP
         * 的 ALDO3 上、下一轮 probe 幂等重开即可；本板的屏电是 GPIO6，留在这里 = 一块**没有
         * 应答证据**的面板被长期通电，而这条分支之后没人再负责断电（`epd_pins_release_if_unverified`
         * 只在深睡时跑）。所以这里就地收口，顺序固定：**先交还引脚、后断电**——反过来就是
         * 把 CS/DC 钉高着去断 6 号脚的电，正好是"向 0V 的 EPD_VCC 倒灌"那一路。 */
        ESP_LOGW(TAG, "probe #%u discarded (s_bus_ok=%d s_cmd_dropped=%d): 命令流不完整，结论作废 → 交还引脚与屏电",
                 s_probe_round, (int)s_bus_ok, (int)s_cmd_dropped);
        epd_pins_release();
        epd_rail_off();
        s_ready = false;
        s_partial_lut = false;
        return false;
    }
    s_ready = true;
    s_partial_lut = false;      /* 刚装的是全刷 LUT */
    ESP_LOGI(TAG, "epd154 init done (PWR%d RST%d DC%d CS%d SCLK%d MOSI%d BUSY%d, %dx%d stride=%d fb=%d B)",
             EPD_PWR_PIN, EPD_RST_PIN, EPD_DC_PIN, EPD_CS_PIN, EPD_SCLK_PIN, EPD_MOSI_PIN,
             EPD_BUSY_PIN, EPD_WIDTH, EPD_HEIGHT, EPD_STRIDE, EPD_FB_SIZE);
    return true;
}

bool epd_panel_probe(void)
{
    if (atomic_exchange(&s_probing, true)) {
        ESP_LOGW(TAG, "probe skipped: 无锁兜底正在交还引脚 → 本轮让开（下一轮重来）");
        return false;
    }
    const bool ok = probe_attempt();
    atomic_store(&s_probing, false);
    return ok;
}

bool epd_init(void) { return epd_panel_probe(); }
bool epd_ready(void) { return s_ready; }
unsigned epd_probe_round(void) { return s_probe_round; }

void epd_display_full(const uint8_t *fb)
{
    if (!s_ready) return;
    /* 每次全刷前重新 init：中途面板被关机时这里就失败，立刻交回上层重来，
     * 不让调用方（app_main、httpd 配网任务）每帧白等一次上限。 */
    if (!epd_panel_init()) {
        ESP_LOGW(TAG, "panel init failed before full update: give up this refresh");
        s_ready = false;
        s_partial_lut = false;
        return;
    }
    epd_cmd(0x24);
    epd_data_buf(fb, EPD_FB_SIZE);          /* 新帧 */
    epd_cmd(0x26);
    epd_data_buf(fb, EPD_FB_SIZE);          /* 基准帧：与原厂 EPD_DisplayPartBaseImage 同形 */
    if (s_cmd_dropped) {
        ESP_LOGE(TAG, "full update aborted: 有 SPI 写失败 → 坏帧不写进基准平面（本轮不刷、下线重来）");
        s_ready = false;
        s_partial_lut = false;
        return;
    }
    epd_cmd(0x22); epd_data(0xC7);          /* 原厂全刷用的那个值（不是 0x3.97 档案的 0xF7） */
    epd_cmd(0x20);
    const int64_t t0 = esp_timer_get_time();
    if (!epd_wait_busy()) {
        ESP_LOGE(TAG, "full update timed out");
        s_ready = false;
        s_partial_lut = false;
        return;
    }
    ESP_LOGI(TAG, "full update done in %d ms (读数按 %dms 轮询量化，只报 20 的整数倍；"
                  "R59 pdiag 那把细粒度尺量到的是 1761~1762ms，两者不是同一把尺，别互相对账)",
             (int)((esp_timer_get_time() - t0) / 1000), 20);
}

bool epd_display_partial(const uint8_t *fb, int x0, int y0, int x1, int y1)
{
    if (!s_ready) return false;
    if (!s_bus_ok) {
        s_ready = false;
        ESP_LOGE(TAG, "partial aborted: 引脚已交还（s_bus_ok=false），本轮不写任何命令");
        return false;
    }
    s_cmd_dropped = false;
    if (!s_partial_lut) {
        if (!epd_panel_init_partial()) {
            ESP_LOGW(TAG, "partial LUT init failed: 下线重来");
            s_ready = false;
            return false;
        }
        s_partial_lut = true;
        ESP_LOGI(TAG, "partial LUT loaded (窗口参数 %d,%d..%d,%d 只进本行，不缩小 RAM 窗口，理由见文件头)",
                 x0, y0, x1, y1);
    }
    epd_cmd(0x24);
    epd_data_buf(fb, EPD_FB_SIZE);
    if (s_cmd_dropped) {
        s_ready = false;
        s_partial_lut = false;
        ESP_LOGE(TAG, "partial aborted: 命令流不完整 → 半截帧不做差分");
        return false;
    }
    epd_cmd(0x22); epd_data(0xCF);
    epd_cmd(0x20);
    const int64_t t0 = esp_timer_get_time();
    if (!epd_wait_busy()) {
        s_ready = false;
        s_partial_lut = false;
        ESP_LOGE(TAG, "partial update timed out");
        return false;
    }
    ESP_LOGI(TAG, "partial update done in %d ms (同样按 20ms 轮询量化；R59 pdiag 细粒度尺的读数是 574ms)",
             (int)((esp_timer_get_time() - t0) / 1000));
    return true;
}

void epd_sleep(void)
{
    /* 三条出口的划分与 3.97 那只同名函数一致（判据看 s_bus_ok 而不是 s_ready，理由抄在那边：
     * "probe 成功 → 刷中途失败"这条路上两个标志会分家，只看 s_ready 就漏掉了"引脚已被我们
     * 配成输出"这一档）。本板多出来的是**硬断电**这一档：屏电在 GPIO6 上，原厂
     * `port_power.cpp` 的 EPD_ON 是拉低，所以每条出口最后都必须把 6 号脚放回"关"。
     * 0x10（deep sleep）在 R59 那份证据里**没有实测过**（v6 的 14 步里没有断电步），
     * 它是可省的一笔：面板真吃了就省一点漏流，没吃我们下面也照样断掉它的电。 */
    if (!s_bus_ok) {
        epd_rail_off();
        s_ready = false;
        s_partial_lut = false;
        ESP_LOGI(TAG, "sleep: 引脚未配过 → 无脚可交还，只确认屏电=关 (PWR%d=1)", EPD_PWR_PIN);
        return;
    }
    if (!s_ready) {
        /* 没有"面板在应答"的证据时不发任何命令：CS/DC 钉高正是对一块可能 0V 的面板倒灌那一路。 */
        epd_pins_release();
        epd_rail_off();
        s_partial_lut = false;
        ESP_LOGW(TAG, "sleep: panel not confirmed alive (never, or lost mid-refresh)"
                      " → 引脚交还 + 屏电关，未发 0x10");
        return;
    }
    epd_cmd(0x10); epd_data(0x01);
    vTaskDelay(pdMS_TO_TICKS(10));      /* 给它把命令吃进去再动引脚 */
    cs_high();
    gpio_set_level(EPD_DC_PIN, 1);
    s_ready = false;                    /* 睡过之后寄存器全丢，下次必须重新判活+init */
    s_partial_lut = false;
    epd_pins_release();
    epd_rail_off();
    ESP_LOGI(TAG, "sleep: 0x10 已发 + 引脚交还 + 屏电关 (PWR%d=1)", EPD_PWR_PIN);
}

/* 拿不到显示锁时的兜底：只在"引脚配过、但没有面板在应答的证据"这一档把 5 根脚连同 SPI 交还。
 * 形状与 epd_driver.c 同名函数一致（原子认领 + 抢不到限时重试），推导在那边，这里只换两个数：
 * 本板一轮 probe 的最坏值 = 屏电 20ms + 硬复位 120ms + 三段 BUSY 上限 200/500/200ms
 * + LUT 那段 200ms ≈ **1.26s**（没有 AXP、没有 I2C 扫，比 3.97 那只的 ≈3.53s 短），
 * 上限取 4000ms ≈ 3 倍余量。 */
#define PANEL154_CLAIM_WAIT_MS 4000

void epd_pins_release_if_unverified(void)
{
    const uint32_t t0 = xTaskGetTickCount();
    bool claimed = !atomic_exchange(&s_probing, true);
    int polls = 0;                       /* 只有 polls>0 时"等了 Nms"这句话才成立 */
    while (!claimed) {
        vTaskDelay(pdMS_TO_TICKS(100));
        claimed = !atomic_exchange(&s_probing, true);
        polls++;
        if ((uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS >= PANEL154_CLAIM_WAIT_MS) break;
    }
    const int waited_ms = (int)((uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS);
    if (!claimed) {
        ESP_LOGW(TAG, "release skipped: 持锁方正走一次点屏尝试，等了 %dms（%d 次轮询）仍未交回令牌"
                      " → 引脚留在当前状态进深睡（本轮倒灌防护未生效）", waited_ms, polls);
        return;
    }
    if (polls) ESP_LOGW(TAG, "release: 等了 %dms（%d 次轮询）才拿到认领令牌", waited_ms, polls);
    if (s_bus_ok && !s_ready) {
        epd_pins_release();
        epd_rail_off();                  /* 3.97 那只没有这一档：本板的电在 GPIO 上，交还脚不断电等于没睡 */
    } else {
        ESP_LOGI(TAG, "release: 拿到令牌但条件不成立，本轮不交还（s_bus_ok=%d s_ready=%d）："
                      "s_ready=1 = 最近有应答证据，此时拆句柄会撞上在途刷屏（令牌只挡 probe，不挡刷新）",
                 (int)s_bus_ok, (int)s_ready);
    }
    atomic_store(&s_probing, false);
}

#endif /* BOARD_EPAPER_1IN54 —— 本文件整只在 3.97 板上被抹空 */
