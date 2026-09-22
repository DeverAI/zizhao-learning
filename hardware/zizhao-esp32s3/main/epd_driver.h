/* 微雪 ESP32-S3-ePaper-3.97 墨水屏底层驱动（SSD16xx 系命令集）
 *
 * 移植自官方例程 ESP-IDF/01_E-Paper_Example/components/epaper_port/epaper_port.c，
 * 引脚一致：SCLK=11 MOSI=12 CS=10 DC=9 RST=46 BUSY=3（SPI3_HOST；SD 卡走 SDMMC 控制器，
 * 与这几根脚无关，也不与 41/42 的 I2C 抢脚）。
 * 【引用口径（R33 P2-6）】官方包 `ESP-IDF/` 下 8 个例程目录里有 **6 份同名** `epaper_port/epaper_port.c`
 * （`01_E-Paper_Example`/`04_SD_Test`/`05_QMI8658A`/`06_I2C_PCF85063`/`07_I2C_SHTC3`/`08_ESP32-S3_e-Paper-3.97`），
 * 且 `08` 那份比 `01` 整体**多 1 行**（多了 `08:6` 的 `#include "axp_prot.h"`）；
 * `EPD_Power_ON()`（函数体里就一句 `enapwrstate(ALDO3)`）**只在 `08` 里有**（`08:182-186`，作为 `EPD_Init()` 第一条语句在 `:236`），
 * `01` 的 `EPD_Init()`（`:222-228`）第一步是 `vTaskDelay(10)` 不是供电 ⇒ 本工程凡是"官方怎么供电"的引用必须落在 `08`，
 * 而"官方怎么等 BUSY"两份都有（`01:225-228` / `08:238-242` 都是 `EPD_Reset()` → `EPD_ReadBusy()` → `0x12`）。
 * 只写"官方 `epaper_port.c:NNN`"不写文件夹名 = 不可核的引用。
 * 与官方差异：CS 每次传输显式翻转（官方全程拉低）；BUSY 等待加上限防死挂。
 * 帧缓冲布局：800x480 1bpp，行主序 stride=100B，MSB 在最左，1=白 0=黑。 */
#ifndef ZIZHAO_EPD_DRIVER_H
#define ZIZHAO_EPD_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

#define EPD_WIDTH   800
#define EPD_HEIGHT  480
#define EPD_STRIDE  (EPD_WIDTH / 8)            /* 100 字节/行 */
#define EPD_FB_SIZE (EPD_STRIDE * EPD_HEIGHT)  /* 48000 字节 */

#ifdef __cplusplus
extern "C" {
#endif

/* 初始化 SPI/GPIO 并把面板寄存器配好（含硬件复位 + SWRESET）。
 * 失败仅返回 false 并记日志，绝不 panic。等价于 epd_panel_probe()。 */
bool epd_init(void);

/* 一次点屏尝试：按需备好 SPI/GPIO（**注意**：判定为"面板没电"时它会在本轮结束时把这些引脚
 * 连同总线一起交还成 `GPIO_MODE_DISABLE` + 约 45K 内部上拉（输入缓冲关，所以**不是"输入"、
 * 也不是高阻**；R41 统一口径，交还动作见 epd_driver.c 的 `epd_pins_release`），
 * 所以"调用过一次"≠"引脚还配着"），
 * best-effort 开 AXP 屏电轨，再判面板是否活着。
 * 面板没电（板子没按 PWR 开机）时返回 false，可反复调用。
 * 返回 true 之后**不是**恒为 true：任何一次刷屏中途 BUSY 超时或面板被关机，都会清掉
 * 就绪状态（见 epd_ready()），由上层监视任务重新 probe——所以调用方必须每帧重新看
 * epd_ready()，不能把"曾经成功"当成"永远可用"。 */
bool epd_panel_probe(void);

/* 面板当前是否已点亮可用（false = 需要重新 epd_panel_probe()）。 */
bool epd_ready(void);

/* 已经做过多少次点屏尝试（驱动侧"每 12 轮放行一次判活"就按这个号数走）。
 * 上层日志要引用它才对得上驱动里的 `probe #N`；自己另数一个循环计数是两回事。 */
unsigned epd_probe_round(void);

/* 全刷：写 BLACK(0x24)+OLD(0x26) 两个平面并触发显示，之后局部刷新以它为对比基准。 */
void epd_display_full(const uint8_t *fb);

/* 局部刷新 fb 中矩形 [x0,y0,x1,y1)（像素坐标，x 自动按字节对齐）。
 * 仅刷新与 OLD 平面不同的像素，不闪屏。返回 false=BUSY 超时（此时就绪状态已清，
 * 调用方下次要走全刷重建基准平面）。前置条件：本上电周期内至少成功全刷过一次
 * （局刷路径不做硬复位，0x01/0x11 等寄存器靠全刷的 init 配好）。 */
bool epd_display_partial(const uint8_t *fb, int x0, int y0, int x1, int y1);

/* 进深睡（0x10）。深睡后画面保持；寄存器配置全丢，再刷屏前必须重新 epd_panel_probe()。
 * 只有"最近一次证据显示面板在应答"时才发 0x10；否则（从未判活成功，或某次刷新 BUSY
 * 超时=面板掉电）不发任何命令，只把通向面板的 5 根脚（RST/DC/CS/SCLK/MOSI）连同 SPI
 * 总线一起交还——那档电轨可能压根没开，钉高会经面板 ESD 二极管向 0V 倒灌。
 * 交还后的状态是 **`GPIO_MODE_DISABLE` + 约 45K 内部上拉到 3V3**（`gpio_reset_pin` 就是这样的：
 * 输入缓冲是**关**的，所以既不能靠这层残留态读脚，也算不上"输入"；见 epd_driver.c
 * `epd_pins_release` 里那段）：不再主动驱动，但仍漏几十 uA，不是"断开/高阻"。
 * R41 统一口径，此前这里写作"输入 + 约 45K 内部上拉"。
 * 交还后 `epd_bus_setup()` 会整套重建（内部靠清掉的 s_bus_ok 标记），不是"释放一次就废"。 */
void epd_sleep(void);

/* 拿不到显示锁时的兜底：若面板引脚已配成输出但当前没有"在应答"的证据，把 5 根脚连同
 * SPI 总线一起交还（此时不可能有在途刷屏）。epd_sleep() 拿锁失败要调它，否则倒灌防护只在
 * "拿得到锁"那一路生效。 */
void epd_pins_release_if_unverified(void);

#ifdef __cplusplus
}
#endif
#endif
