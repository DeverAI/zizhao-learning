#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 板载 AXP2101 电源管理芯片通过 ALDO3 轨给墨水屏供电；上电默认关闭，
 * 不开这一路面板永远不动。用 I2C(SDA41/SCL42, addr 0x34) 使能，
 * 完成后立即卸载 I2C 驱动并复位这两个引脚，让 41/42 停止驱动（`gpio_reset_pin` 之后是
 * `GPIO_MODE_DISABLE` + 约 45K 内部上拉，**输入缓冲是关的**，所以既不能靠它读脚，也
 * **不是高阻**、更不是"输入"；R41 统一口径，与 `axp_panel_power.c` / `epd_driver.h` 同一条）。
 * SD 是 SDMMC，不占这两个脚；
 * 只有"端口0 确实是我们装上的"才有资格交还，delete 失败时保留所有权、不碰焊盘）。
 * 返回 true=AXP 应答且已开轨；false=没到手（原因待定：整机没开机，或我方 I2C
 * 通路本身不通——每轮日志的 "known 0x18/0x51/0x70/0x6A/0x6B: ACK= NACK= TMO=" 计数就是
 * 用来分开这两条的：有任何 ACK ⇒ 我方通路没问题，全是 TIMEOUT ⇒ 大概率是我方通路问题，
 * 全是 NACK ⇒ 只说明"这些地址没人应答"，既洗不清引脚表也不证明总线上没器件，
 * 判读边界见 axp_panel_power.c 的 bus_verdict 上方注释）。 */
bool axp_enable_panel_rail(void);

/* 最近一次 axp_enable_panel_rail() 是否判定"AXP 完全不应答/轨没回读确认"。
 * 为 true 时屏电没到手（屏电只能经 AXP 开），上层可跳过点屏尝试；
 * 但这条判据本身没在真机走过成功分支，上层每 12 轮仍会做一次真实判活——R26 起那一轮先做
 * **纯被动 BUSY 采样**（只配 GPIO3 输入+上拉，不碰 RST/CS/DC/SPI），抓到"有人在拉低 BUSY"
 * 才升级为主动判活，防止向可能 0V 的面板倒灌（见 epd_driver.c 的 epd_busy_passive_low）。 */
bool axp_panel_off(void);

/* R53：把 PWR_OUT（GPIO1）在 app_main 最早处按住成"输入 + 内部上拉"，等价于官方
 * `esp_gpio_Init()`。官方那次调用排在 `axp_init()` 之前 ⇒ 出厂固件在跟 PMIC 说任何话之前，
 * 先由 ESP 侧给这根开机自锁脚一个确定的高；我们此前从 boot 到第一次探测之间让它是复位默认
 * （悬空），且探测的读法中途还有一档 5ms 内部下拉。返回值：焊盘 `gpio_config` 是否成功。 */
bool axp_pwr_hold_begin(void);

/* 是否有"系统轨没开"的铁证（PWR_OUT 被外部拉低，见 axp_panel_power.c 的读法说明）。
 * 与 axp_panel_off() 的区别：后者可能是我方 I2C 通路的问题（悬空/读不回），
 * 只表示"没确认"；本函数为 true 才是"确定没开机"。上层据此决定是否连面板
 * 引脚都不许碰——向 0V 面板驱动 RST/SCLK/MOSI 会经 ESD 二极管倒灌。
 * 未探测过（首轮之前）恒为 false。 */
bool axp_system_off(void);

#ifdef __cplusplus
}
#endif
