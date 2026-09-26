#include "epd_driver.h"
#include "board_profile.h"

/* 本文件是 **3.97 那一套脚号**（SCLK11/MOSI12/CS10/DC9/RST46/BUSY3）+ AXP 屏电。
 * 与 `epd_panel_1in54.c` 顶部那条 `#if BOARD_EPAPER_1IN54` 成对：开关只有一处真值
 * （`board_profile.h`），两只驱动都常驻 SRCS，没被选中的那只被预处理器整只抹空，
 * 所以既不会重复定义那 8 个 `epd_*` 入口，也不会"看起来编过了、脚全是错的"。 */
#if !BOARD_EPAPER_1IN54

#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "axp_panel_power.h"

static const char *TAG = "epd";

#define EPD_SCLK_PIN 11
#define EPD_MOSI_PIN 12
#define EPD_CS_PIN   10
#define EPD_DC_PIN   9
#define EPD_RST_PIN  46
#define EPD_BUSY_PIN 3

/* BUSY 等待上限：本屏一次全刷**按官方/手册口径**约 2-4s（**从未实测过**，两块板至今没在
 * USB 上，见 todo 第 47 条）。给 8s 足够宽裕，又能让"面板没电/无响应"
 * 在 8s 内快速失败返回，而不是把开机流程卡死 30s（会拖累 OTA 确认窗口）。 */
#define EPD_BUSY_TIMEOUT_MS 8000
/* 发完 `0x20` 后，"BUSY **这一段**连续这么久而从未翻过高"才作废这一轮刷新（见 epd_wait_busy_ms 里
 * 那段：0x20 之后它多久翻高、一次高电平有多长，都没有实测数据，不能拿第一拍读数定生死）。
 * R33 P0-1 把它的语义从"距第一次低"收紧成"当前这段连续低"：同一根线在毫秒尺度翻高翻低时，
 * 旧口径会把"高低各半"打成"连续低 300ms"。收紧的方向是**变严**（更难作废本轮），代价写在下面。 */
#define BUSY_ACCEPT_CONFIRM_MS 300
/* 发 `0x12` SWRESET **之前**最多花多久等 BUSY 回低（R33 P0-2）。
 * 官方给这一步的预算是"进 `EPD_ReadBusy()` 先无条件睡 100ms，然后 20ms 一轮询直到低、**无上限**"
 * （`ESP-IDF/08_ESP32-S3_e-Paper-3.97/components/epaper_port/epaper_port.c:165-176`），
 * 且它把这次等待放在 `EPD_Reset()` 与 `0x12` **之间**（同文件 `:238-242`）——也就是说厂商认为
 * "复位之后线可能还高着"是通则，不能假定 50ms 够。
 * 500ms 这个数**依然是我拍的**（复位自身的 BUSY 脉宽无实测，todo 第 62 条）：它 ≥ 官方那 100ms
 * 起步预算的 5 倍，又比官方的"无上限"便宜，任何有限值都比死等好。
 * 等不到**不拦**：仍然照发 `0x12`，只把 `pre_high` 记成 1（R32 立的"只观察不当闸门"语义保持不变，
 * 免得又造出一个"判据在采样窗内不可达"的永久锁）。 */
#define EPD_PRE_RESETTLE_WAIT_MS 500
/* `epd_busy_activity()` 慢采段的窗口上限（R39 P2-3 从字面量提出来）。密采段 1000 拍 × 50µs
 * 名义 ≈50ms，加慢采段这一段 = 判活那 ≈1.85s 的全部来源，而 `RELEASE_CLAIM_WAIT_MS` 上方和
 * `eink_display.c` 的持锁链都按"1800ms"这一档算预算。以前它只以裸字面量出现在 `(now−t0)>1800`
 * 和十几行散文里 ⇒ 改这个数的人看不见另一头有预算依赖它（这条口径的原文见
 * `20260919_墨水屏点屏排查记录.md` §21.6 末尾那条"改一个常数时 grep 要覆盖所有 .md + 全部 main/"）。它**不是**超时保护，是判据的一部分：跑满它才意味着"这段时间里确实没有合格的高沿"。 */
#define EPD_LIVENESS_SLOW_WINDOW_MS 1800
/* 深睡前的兜底交还最多等多久才认"这一轮拿不到令牌"（R31 复查 P1-3 立的这个等待，
 * R32-P1 复查把它自己的**推导重写了一遍**——旧版那句"AXP 段(0.5s)"是凭印象写的，差了 5 倍；
 * R33 又因为 `EPD_PRE_RESETTLE_WAIT_MS` 这一档把 `epd_panel_init()` 抬高，重算了一次）。
 * 持锁方一轮的最坏值，逐段按代码里能读到的上限加。
 * 【R39 P2-8：每段末尾的口径标签，决定这个数还能不能再加余量】
 *   `[上限]` = 从代码里的延时常数或事务超时读出来的，只会低估不会高估 ⇒ 想加余量先重算它；
 *   `[实测]` = 真机日志两个 t 值之差，含调用开销，是这一轮实际花掉的 ⇒ 不能再当"保守值"放大；
 *   `[推]`   = 从返回码/分支形状估的典型值，两头都不靠 ⇒ 只有它允许被就地修正。
 *   以前这几段混在一个"最坏"标签下（本注释开头那句说"按代码里能读到的上限加"、位碰那一段却又说
 *   "按真机实测记"），下一轮加余量的人不知道自己在放大哪一类。
 *   `axp_enable_panel_rail()`  0x34 重试 5×(50ms 事务上限 + 20ms 间隔)=0.35s **[上限]**
 *                              （事务上限是 50ms 那一支，
 *                               `axp_read_reg()` 与 `axp_write_reg()` 各一份；**别拿扫描那支的 20ms 顶替**——
 *                               R32 第一版这里写的就是 20ms，被 R32 复查第 5 条的 5×70ms 对出来）
 *                              + 已知邻居扫 5×20ms=0.1s **[上限]**
 *                              + 全地址扫 112×20ms=2.24s **[上限]**（`axp_panel_power.c` 里
 *                                `axp_enable_panel_rail()` 那个 `if (!acked) vTaskDelay(20)` 只在 0x34 重试里，
 *                                扫描本体在 `axp_probe_addrs` 里没有额外 sleep，所以这一段只吃事务超时）
 *                              + 上拉对读 2×5ms + PWR_OUT 2×5ms ≈ 合计 ≈2.7s **[上限]**
 *                                （两条互斥，谁都不能拿对方的数相加：
 *                                 ·`!acked` 轮才有那三行全扫 ⇒ 上限 ≈2.7s；
 *                                 ·`acked` 轮走"id 读 + 6 笔 0x90/0x94 读写"= 7 笔，每笔同样吃
 *                                  50ms 那支 ⇒ 7×50ms=0.35s + 100ms 稳压等待 ≈**0.45s**
 *                                  （R33 P1-3：这一行原先按 20ms/笔 算成 0.14s/0.25s，
 *                                   犯的正是上面那句"别拿扫描那支顶替"。
 *                                   【R40 口径】这个 0.45s 只能标"典型"不能标"[上限]"：重试循环的
 *                                   条件是 `attempt<5 && !acked`，前 4 次失败、第 5 次成功仍然是
 *                                   `acked` 轮 ⇒ 上限 11 笔 = 0.55s + 4×20ms + 100ms ≈ **0.73s**，
 *                                   即下面 B2 那一个子案。这一格 R33~R40 第一版都写着"[上限] 0.45s"，
 *                                   是"标签写错方向"而不是"数加错"，所以之前没被抓到。）
 *                                  【R41 P1 补一句，防它被读成"[实测]"：0.45s 是 **[推] 的典型值**，
 *                                   不是实测——`acked` 那一支在**现存我方固件日志**里一次都没有，
 *                                   这条链上没有任何一段真机走过 `acked`。】
 *                                  【R43 收口：上一版在这里写死了"4 份日志 / 3 次上电 / 六只全 0 /
 *                                   其中两只是官方例程"四个数。它们落笔时为真，但都属于"多抓一份日志
 *                                   就 +1"的那一类，而且没带可复跑命令 ⇒ 按本轮规则换成命令口径：
 *                                   要现值就自己跑 `grep -c "AXP2101 detected" hardware/2026*_*.log`
 *                                   ——**分母必须由这只 glob 点名**："hardware 目录下那几只 `.log`"
 *                                   是无界的（18:13:43 复跑 `find hardware -name "*.log"` = 14 只，其中
 *                                   7 只在备份根里、是构建日志不是真机日志，另 1 只是散在
 *                                   `zizhao-esp32s3/C:espbuild_r22.log` 的历史事故件）。顶层 glob 不递归 ⇒ 天然
 *                                   排掉那 8 只（7 + 1）；剩下 6 只里去掉文件名含"官方例程"的 2 只 ⇒
 *                                   分母 4 只（同刻逐只读数全 = 0）。**官方例程的固件里根本没有这条打印，
 *                                   把它算进分母会把"没测"读成"测了是 0"**——这条判据与上一轮相同，
 *                                   本轮补的是"分母怎么写才有界"。注意块注释里不能写"hardware 斜杠星号"
 *                                   那种 glob：星号前面带斜杠就是块注释的起手式，会触发
 *                                   `-Werror=comment`，R42 那次编译失败正是这么来的。】
 *   位碰那几段（R34~R38 新增，只在 `!acked` 的 full_diag 轮、且引脚已交还时才跑）：
 *                              它的耗时全是软件延时，没有"事务超时"这种上限可推，
 *                              所以按**真机实测**记：开漏那五档 ≈0.285s **[实测]**（R37：t=737→1022，
 *                              R39 改用这一对锚点并逐行核过归属，见 `axp_enable_panel_rail`
 *                              里 `full_diag` 上方那张 t 值表），
 *                              ④推挽全扫 = 112 帧 × ≈1.04ms ≈0.12s **[推]**（1.04ms/帧 是按 34 段
 *                              25µs 延时 + 调用开销估的，本机还没有 PP 档的实测行——板子需要冷插才能拿到），
 *                              且一个上电周期至多跑一次（R43 口径：这里说的是一个上电周期
 *                              内的**上限**，不是"必然跑满一次"——门挡下的轮次不计数）
 *                              ⇒ 合计 ≈**0.4s**（R38 之前这一项整个没进预算，是漏的）。
 * ⇒ 全诊断轮（`!acked` + full_diag）的 AXP 段最坏 ≈3.1s **[2.7 上限 + 0.4 实测/推，混合值]**。
 *   `epd_busy_passive_low()`   被动 40ms + 旁证（交还 + 5ms 建立 + 读）≈ 0.05s **[推]**
 *   `epd_panel_init()`         复位 102ms + 发 `0x12` 前等低 ≤0.5s（R33 P0-2 新增；线本已低时只花 ≈2ms）
 *                              + 判活 50ms+1800ms ≈1.85s + 等空闲 300ms ≈ 合计 ≤**2.75s [上限]**
 *                              （典型 ≈2.25s **[推]**：把 0.5s 那一档换成线本已低的 ≈2ms。
 *                              【R40 P2 口径】这个"≤"不是纯上界：那 1.85s 里的 50ms 密采段自己
 *                              只是**下限**（见 `epd_busy_activity()` 里 R39 P2-4 那句"1000 拍
 *                              × 50µs = 下限 50ms"），慢采段那 1800ms 才是真上限 ⇒ 母项应读作
 *                              "2.75s + 密采段超出 50ms 的那部分"，超出量没测过，故本文件所有
 *                              由它推出来的链（14.3s / 20s / 14s）都还留着这一格未量。）
 *   `epd_bus_setup()`          毫秒级 **[推，未单独测]**
 * ⇒ 【R39 P1-4 提出、R40 修正："最坏一轮"必须分两支，不能把互斥的数加在一起】
 *   全诊断轮那一支：**AXP ≈3.1s，到此为止 ≈3.1s**——它**既进不了** `epd_panel_init()`，
 *       **也进不了被动判活/旁证那 0.05s**：`probe_attempt()` 里电轨闸门
 *       `if (rail_off && (s_probe_round % PANEL_PROBES_PER_LIVENESS) != 0) return false;`
 *       在 `epd_busy_passive_low()` 那一句**之前**就 return，而"full_diag 轮"按定义就是
 *       `!acked` 轮（全地址扫与位碰两道门都写死 `!acked`），`!acked` 又置 `s_axp_off` ⇒ `rail_off`
 *       为真 ⇒ 闸门生效。放行判活还要 `s_probe_round % 12 == 0`，而 full_diag 的轮号是 30+60k，
 *       60 是 12 的倍数 ⇒ 恒余 6，两集合不交（1/2/3 轮同理），这正是当初给 full_diag 挑"偏移 30"
 *       的理由。【R40：R39 这一支多算了 0.05s，把走不到的段的数记了进来——正是同一段注释
 *       指责 R33~R38 的那个错，我改完互斥相加又犯了它的另一半】`eink_display.c` 那条持锁链
 *       对这一支取的是更宽读数 ≈3.3s。
 *   判活放行轮那一支（`rail_off` 且 `s_probe_round % 12 == 0`）：闸门只看 `axp_panel_off()`，
 *       而 `s_axp_off` 有**三个**置位点（都在 `axp_enable_panel_rail()` 里：`axp_bus_install()` 失败、
 *       `!acked`、以及"AXP 应答了但 ALDO3 回读没确认"），所以这一支还要再分子案：
 *       【R41 P1 口径：本行上一版写"两个置位点"，把 install 失败那一支从枚举里抹掉了——
 *        它同样让 `rail_off` 为真、同样落在"只有 %12==0 才放行"那一侧。数值不动（见该支的 AXP 段），
 *        但本轮 §26.3 立的正是"分支划分要做到二级"，它自己停在一级半。】
 *       ·B0 `axp_bus_install()` 失败：一条总线事务都不发就 `return false` ⇒ **AXP 段 ≈0**，
 *          是四支里最便宜的 ⇒ 并入 B1 取宽，现行一轮 probe 最坏 3.53s 不受它影响；
 *       ·B1 `!acked`、非 full_diag：AXP ≈ 0x34 重试 0.35 + 邻居扫 0.1 + PWR 读 0.01 ≈ **0.46s**
 *          （全扫与位碰都被 `!acked && full_diag` 那两道门挡在外面。【R41 P2 口径】这一格先前印
 *          **0.47s**，而它自己给的分项和是 **0.46** —— 正是下面 B2 那一格"算式与它自己给的结果不等"
 *          的第三个实例；要么把 PWR 读补成含一次 `gpio_config` 的 0.02，要么全族改 0.46。
 *          下面 B1 支最坏因此是 0.46+0.05+2.75 = **3.26s**（旧版 3.27s）。）；
 *       ·B2 `acked` 但回读没确认：id 重试 ≤5 笔×50ms + 4 次失败后的 20ms 间隔 = **0.33s**
 *          （R40 三修：这一格上一版写成 `5×(50+20)=0.33`，那个式子按字面算是 **0.35**，与它自己给的
 *           结果差一个间隔。差的那一档正是"最后一次必须成功 ⇒ 它后面没有 `vTaskDelay(20)`"：
 *           循环是 `attempt<5 && !acked`、延时只在 `if (!acked)` 里（按符号指：`axp_enable_panel_rail()`
 *           里读 `AXP_REG_CHIP_ID` 的那个 for 循环，`vTaskDelay(pdMS_TO_TICKS(20))` 写在它体内最后一行
 *           ——【R41 P1 口径】本行上一版给的是裸区间 `axp_panel_power.c:754-758`，而它要支撑的两句
 *           分别在 756（循环条件）和 **759**（那句 `if (!acked) vTaskDelay`）：**窗正好把证据行排除在
 *           外面**。这正是本轮 §26.4-③ 刚立的规矩（"行号会被本轮自己加的一行注释推漂 ⇒ 按符号指"）
 *           被我自己在同一轮里破了一次），
 *           所以 `acked` 轮最多 4 个间隔 0.33s，而上面 B1/`!acked` 那一支 5 个间隔才是 0.35s。
 *           结果 0.73s 没变，变的是这个算式的写法——同族错误"**算式与它自己给的结果不等**"）
 *          + 0x94/0x90 各一读一写 4×50ms=0.2
 *          + 稳压 100ms + 两次回读 2×50ms=0.1 ≈ **0.73s**（这一支**没有**邻居扫/PWR 读/全扫/位碰，
 *          它们全在 `!acked` 里）——**上限按这一支取**。
 *       + **被动判活/旁证 0.05s**（R40：这一支才轮到它，R39 从这一支漏了）+ init ≤2.75s
 *       ≈ **3.53s**（B2）。【R40 二修】本注释上一版把这一支写成"只有 ≈0.47s ⇒ 3.27s"（R41 按分项和
 *       把 B1 订正为 0.46s / 3.26s，见上面 B1 那格），那是
 *       **只把 B1 当成整支**：`rail_off` 不等于 `!acked`，回读失败那一支带着 0.27s（R41 按
 *       0.73−0.46 重算；旧版写 0.26s 是按 0.73−0.47 来的）的写/稳压/回读
 *       回来，而邻居扫和 PWR 读反而是 B1 独有的——同族错误的**第六种形态**（拿一个子案的形状
 *       当整支的上限），记进 `FreqErr.md`。
 *   ⇒ **一轮 probe 最坏 ≈3.53s**（取两支宽的那头：B2 的 3.53s vs A 的宽读 3.3s。
 *      【R41 P2 口径】"一轮最坏"这四个字在本仓库指过两个对象（一轮 probe ≈3.53s / 一次持锁 ≈14.3s），
 *      自 R41 起写死：说 3.53s 必须带 "probe"，说 14.3s 必须写"一次持锁最坏"，裸的"一轮最坏"不再用）。
 *      【R40 三修】本行上一版
 *       印的是 **3.55s**，比它自己给出的推导大 0.02s，而那 0.02s **没有来源**（既不是某一段的数，
 *       也不是写明的进格规则）——"公布的数比自己的算式大"是同族错误的又一种形态，改回 3.53s。
 *       R33~R38 这段写的
 *       "≈5.9s"是把两支互斥的数加在一起（3.1 + 2.75 + 0.05），**虚高约 67%**（(5.9−3.53)/3.53）；
 *       R39 那句"≈84%"没有交代母数，能反推出来的是 ≈3.20s，而它自己公布的 3.25s 只能给出 ≈82%，
 *       R40 第一版按 3.3s 给的是 79%。母数只能是本行刚给出的那个现行值；
 *       它不会让任何防护失效（等得越久越宽），但下一轮再有人"按最坏一轮加余量"就会在这个数上
 *       继续放大，所以必须改。
 * （**这里只算到"一轮 probe"，不含刷白**；`eink_display.c` 那条 20s 显示锁要盖的是"probe 过了还要
 *   刷白"的整轮，R39 一起重算过：能走到刷白的那一轮按上面第二支，AXP 取 B2 的 ≈0.73s，加
 *   **被动判活 0.05s**、加两次 `epd_panel_init()`（probe 一次、`epd_display_full()` 里再一次）
 *   各 ≤2.75s，再加两帧 ≈0.05s 与 `EPD_BUSY_TIMEOUT_MS`=8s ⇒ ≈**14.3s**（0.73+0.05+2.75+2.75+0.05+8
 *   = 14.33；【R42 订正】R40 第一版那个 14.07 的缺项**只有一个**：AXP 记成了 B1 档。
 *   上面两个 0.05s 它都在（0.47+0.05+2.75+2.75+0.05+8 = 14.07 本身就成立），
 *   【R43 订正归属】"漏了一个 0.05s"这句假账是 **R40 定稿自己**写下的（`73cbbfc`），不是 R41 写的；
 *   R41 原样携带、没碰这一行。【R43 复查 P0-2 落地】上一版这里写"`git log -S` 只指向那只 R40 提交"——
 *   那是一句**没限定文件的命令**被当成了限定结论来引用：17:16 现跑同一条不带 `--` 的 = **3 只**
 *   （`3c37af3`/`489baad`/`73cbbfc`，多出的 `489baad` 是 R42 在文档里改写过这句话）。限定到本文件才闭合：
 *   `git log --oneline -S"漏了一个 0.05s" -- hardware/zizhao-esp32s3/main/epd_driver.c` = 2 只
 *   （`73cbbfc` 引入 + `3c37af3` 改写过这句话），加 `--reverse | head -1` 取到的第一只就是 `73cbbfc`。
 *   另一处 `eink_display.c` 里同一句话**最早出现在 R43 自己**（限定该文件 = 只有 `3c37af3`）⇒ 归属类
 *   断言的锚必须同时写"提交号 + 命令的文件范围"，只写提交号还会被下一轮的同短语新增打脸。
 *   缺多少看基数：0.47 那一版 ⇒ 差 **0.26**；现行基数（B1=0.46 / B2=0.73）⇒ 差 0.27。
 *   【R43 说清那 0.01】两个数不是"两个世代的母数"，是同一条链上的两处：物理缺额 = B2−B1(现行) = 0.27，
 *   而 14.07 这个历史字串里**多含 0.01**（当年 B1 记成 0.47、R41 已订到 0.46）⇒ 0.27 − 0.01 = 0.26。
 *   ⇒ 谁要"补 14.07"只能用 0.26（14.07+0.26=14.33 闭合）；拿 0.27 去补会得 14.34，
 *   那是把"已订正的 B1"和"未订正的 14.07"混在一支加法里。R39 那版 14.0s 才是真的少了一个 0.05s。），
 *   那边现在按这个数读、余量 ≈5.7s（仍写作"≈6s"）。以前那版把
 *   "全诊断轮才有的 AXP ≈3.3s"和"要刷白才有的两次 init + 8s"串成 16.8s 一条链，犯的是上面
 *   第一条同样的互斥分支相加，**虚高约 2.5s**。）
 * R32 曾取 10s；R33 加了那 0.5s 后按"两轮 11s > 10s"提到 **12s**；R38 又按（虚高的）5.9s 算成
 * "两轮 ≈11.8s，12s 只剩 0.2s"而提到 **14s**。R40 重算后一轮 probe 最坏 ≈3.53s ⇒ 两轮 ≈7.06s（读作 ≈7.1s）。
 * 【R41 P2 口径：本段上一版一句里写"14s 实际是'约 4.0 个最坏轮'，余量 ≈6.9s"，两处都得改】
 *   ①作"装得下几个"读必须**向下取整**：14 ÷ 3.53 = **3.97，不足 4**（4 个最坏轮要 14.12s > 14.00s，
 *     "约 4.0 个"把不成立的那一档说成了成立）⇒ 正确说法是"容得下 **3 个完整最坏轮**
 *     （3×3.53 = 10.59s，还剩 3.41s）"；②那个"余量 ≈6.9s"（14 − 7.06 = 6.94）是**两轮之后**剩的，
 *     不是"4 轮"的余量（按 4 轮算是 −0.12s）—— 一句里混了两个量，读者分不清哪个是结论 ⇒ 分三句写。
 *   R39 那版"4.3 个 / 7.5s"按 3.25s 算，R40 第一版"4.2 个 / 7.4s"按 3.3s 算——两个数都因为把 B2
 *   漏了而偏乐观，方向与①同族。
 * 没有把 14s 降回去：这个上限真正的对手不是
 * "一轮 + 一点余量"，是"本轮剩余时间 + 一次 unlucky 的让位"：
 * 等到的那一瞬间还要**抢在下一轮认领之前**拿到令牌，而持锁方两轮之间只有监视任务那个 5s 间隔是
 * 空的（100ms 轮询在这个窗口里赢得了一场只需赢一次的赛跑）。旧值 6s 只留 **1.0s** 余量
 * （6s − 一轮 ≈5.0s；R32 复查那版按它自己的 5.15s 算，给的是 0.85s——两个数都是推的，
 * **取宽的那头也仍然是"不够"**），恰好在最坏那一窗内被用完——
 * 而输掉一次的代价是"倒灌防护整个深睡周期都没跑"，几小时。多等的这几秒板子马上就要睡了，
 * 没有别的代价。
 * 全程在 `vTaskDelay` 里，让出 CPU，因此**不会**碰 Task WDT：本机
 * `CONFIG_ESP_TASK_WDT_CHECK_IDLE_TASK_CPU0/1=y`（构建树 sdkconfig:982/983）意味着狗是
 * 由 idle 喂的，只有"不让 idle 跑"才会触发超时，而这里恰恰相反。
 * 上面这些段里，除位碰那一段是按 R37 真机 t 值记的外，其余都是按返回码/延时上限推的；
 * 也就是说"一轮 probe 具体多久"仍然没有逐段的真机计时。要留的余量是推出来的，
 * 但"要不要等"不是。 */
#define RELEASE_CLAIM_WAIT_MS 14000

static spi_device_handle_t s_spi;
/* `volatile` 的口径（R33 P2-7）：这两个标志的**写**侧唯一的同步是显示锁，但
 * `epd_pins_release_if_unverified()` 是在**锁外**读它们的（拿不到锁才走那条兜底），
 * 所以按同文件 `s_cmd_dropped` 的写法一致标成 volatile——不是"修一个已证的坏交错"
 * （那条论证在 `epd_pins_release_if_unverified` 上方），只是把口径统一。 */
static volatile bool s_bus_ok = false;
/* s_ready 的语义是"**最近一次证据显示面板在应答**"：probe 成功置位，任何一次刷屏的
 * BUSY 超时清位。深睡前"该不该发 0x10、该不该继续驱动引脚"就看这一位——
 * 曾经活过后来又超时，正是"面板可能已经掉电"的表征，此时钉高 CS/DC 就是倒灌那一路。
 * （R25 曾另立一个只会能 true 的 s_ever_alive，被复查指出是粘滞假凭证：见排查记录 §十五。） */
static volatile bool s_ready = false;
static unsigned s_probe_round;   /* epd_panel_probe 被调过的次数（电轨闸门的放行节律用） */
/* 认领标记（不是"状态"）：**谁把它从 false 换成 true，谁就拥有"接下来可以动面板引脚/SPI"
 * 的这段时间**。用 `atomic_exchange` 认领，两边（点屏那侧 = epd_panel_probe，兜底释放那侧
 * = epd_pins_release_if_unverified）都是同一个动作，所以"读→判断→动手"不再能被对侧插进来
 * （R30 复查 P0-2：拆成两步的 `if (s_probing) … / s_probing = true;` 中间正好有一次完整窗口，
 * 兜底方能在事务在途时 `spi_bus_remove_device` → `free(handle)`）。见同两个函数里的说明。 */
static atomic_bool s_probing;
/* 本轮 init/刷新里有没有任何一笔 SPI 写失败（含"s_spi 已被兜底释放拆走"）。
 * 由 spi_write 置位，由 epd_panel_init 清零，probe 收尾与两条刷新路径各自检查——
 * 目的只有一个：命令流残缺时不许把结论记成"面板活着/刷成功了"（R27 复查 P1-4）。 */
static volatile bool s_cmd_dropped = false;

static void epd_pins_release(void);   /* 定义在后面，被动采样的旁证阶段要借它交还焊盘 */

static void pin_set(int pin, int lvl) { gpio_set_level(pin, lvl); }

static void cs_low(void)  { pin_set(EPD_CS_PIN, 0); }
static void cs_high(void) { pin_set(EPD_CS_PIN, 1); }
static void dc_cmd(void)  { pin_set(EPD_DC_PIN, 0); }
static void dc_data(void) { pin_set(EPD_DC_PIN, 1); }

static void spi_write(const uint8_t *buf, size_t len)
{
    spi_transaction_t t = {0};
    t.length = len * 8;
    t.tx_buffer = buf;
    esp_err_t e = spi_device_polling_transmit(s_spi, &t);
    if (e != ESP_OK) {
        /* 一笔没出去 = 命令流从这里起整体残缺。以前只打一行日志就继续往下发，
         * 结果是"半个 init 序列 + 错位的一帧"照样等 BUSY、照样判成功（R27 复查 P1-4）。
         * 置一位让本轮/本次刷新作废，代价由上层的全刷重试承担。 */
        s_cmd_dropped = true;
        ESP_LOGE(TAG, "spi write failed: %s", esp_err_to_name(e));
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

/* 连续数据流：CS 保持拉低、DC=数据，分块发出（≤100B/行，20MHz 下瞬间完成）。 */
static void epd_data_buf(const uint8_t *buf, size_t len)
{
    if (!len) return;
    cs_low();
    dc_data();
    const size_t chunk = 4096;
    for (size_t i = 0; i < len; i += chunk) {
        size_t n = (i + chunk > len) ? (len - i) : chunk;
        spi_write(buf + i, n);
    }
    cs_high();
}

/* BUSY 极性与"怎么才算面板活着"——这块屏的三条一手证据钉死了口径，改这里之前先读它：
 *   ① 官方 `ESP-IDF/01_E-Paper_Example/components/epaper_port/epaper_port.c:161` 函数注释
 *      "Wait until the busy_pin goes LOW" + 同文件 `:170`
 *      `if(!ReadBusy){break;}` → **高=忙，低=空闲**（放行等到低）。
 *   ② 同一份 `01_E-Paper_Example/components/epaper_port/epaper_port.c:25-30` 把 BUSY 配成输入
 *      + `.pull_up_en = GPIO_PULLDOWN_ENABLE`（:29），而 IDF 5.1.6 里
 *      `GPIO_PULLUP_ENABLE`（hal/gpio_types.h:373）== `GPIO_PULLDOWN_ENABLE`（:378）== 0x1、
 *      `gpio_config()` 只判真假（driver/gpio/gpio.c:392 `if (pGPIOConfig->pull_up_en)`）
 *      → 官方**实际生效的是内部上拉**，本驱动显式写对上拉，与官方一致。
 *   ③ 合起来的判据：上拉下，掉电/未接的面板不驱动线路 → **恒读高**（既不是"空闲"也
 *      不是"忙"，就是悬空）；所以"看到持续 ≥1ms 的低"= 面板在主动推低 = 活着。
 *      反过来"恒读低"不可能是悬空，只能是有东西在真驱动（面板活着）或线路被短到地。
 *
 * require_high：刷新后（发过 0x20）必须传 true。"先看到高、再看到低"才是"面板受理了
 * 这次刷新并做完了"的唯一证据；只看"读到一次低"的话，面板当时若还在忙，会把
 * 0x24/0x26/0x22/0x20 整段忽略掉，随后它忙完放低 → 我们判"刷新成功"而屏上什么都没有，
 * 且 s_ready 恒真、probe 早返回，这个假成功会一直留到下次重启。
 * init 尾部那种"确认它空闲"的用法传 false：SWRESET 之后寄存器写入不一定再触发 BUSY
 * 脉冲，那里要求"必须高过"等于赌一个面板没承诺过的沿。
 *
 * 超时上限按场景给：一次刷新要等几秒，刚复位/刚判活只需要几百毫秒——写死 8s 会把最坏
 * 阻塞叠到 ~18s，全在显示锁里，拖累配网门户与主循环。
 * tick 差值全程按 uint32 环绕语义做：本机 `CONFIG_FREERTOS_HZ=1000`（tick=1ms），
 * 收成 int 后连续跑 24.8 天差值就变负 → 永不超时并长期持锁。 */
static bool epd_wait_busy_ms(int timeout_ms, bool require_high)
{
    /* R30 复查 P1-1：旧写法进循环前先睡 100ms（一段盲窗），第一拍读到低又拿不到"高过"就直接
     * 判"panel did not accept this update"。而 0x20 之后 BUSY 多久翻高、一次高电平持续多长，
     * 本板**一条实测数据都没有**（todo 第 49 条同一类）。两头都可能冤枉好屏：翻高慢于 100ms
     * ⇒ 第一拍读低即误判；整段高电平短于 100ms ⇒ 落在盲窗里同样误判。
     * 现在改成：不睡盲窗，从 t=0 就以 1ms 步长找上升沿；只有当"低"**连续**够到
     * BUSY_ACCEPT_CONFIRM_MS 才作废本轮。真受理的刷新高电平要持续秒级，不受影响。
     * 【计时口径（R33 P0-1 改，R33 P1-1 补）】原来这句"上限时间也没变大（300ms ≪ 8s），
     * 最坏持锁时长只多 200ms"把两种失败混成了一句，而且那个 200ms 是旧口径下的数：
     *  · "从没给出合格的高 + 线**一直**是低" ⇒ 走到 `BUSY_ACCEPT_CONFIRM_MS` 早退，≈300ms，
     *    与收紧前一样（死屏/0V 钳位那一档不受本次改动影响）；
     *  · "线在毫秒尺度翻高翻低" ⇒ 旧的"距第一次低"会立刻凑满 300ms 早退，改成"当前这段低"后
     *    **每来一次高就重新计时** ⇒ 这一档现在会走到 `timeout_ms` 上限（刷新那支 = 8s）。
     *    8s 本来就在 `eink_display.c` 那条持锁链的预算里（那一段就是按 `EPD_BUSY_TIMEOUT_MS`
     *    算的），所以锁的算术不变；变的是"失败轮第一次真花满 8s"这件事更容易在日志里出现。
     * 低侧（R33 P1-1）：宣布"刷完了"也要连续两拍低，理由与高侧两拍同源——同一根高阻线、
     * 同一个串扰源，判据不能一松一紧；松的那一头直接决定 `s_ready` 与 `panel blanked`。
     * 代价：每一次**成功**的刷新多等一拍（`finding_edge` 已经 false ⇒ 20ms 那一拍）。 */
    uint32_t t0 = xTaskGetTickCount();
    int first_low = -1;        /* 本轮第一次读到低的时刻（只进日志，不参与判据） */
    int cur_low_start = -1;    /* **这一段**连续低的起点：读到高就作废重来（R33 P0-1） */
    int seen_high = -1;
    int hi_run = 0;            /* R32 P0：读到高要连续两拍 */
    int lo_run = 0;            /* R33 P1-1：低同样要连续两拍 */
    int hi_single = 0;         /* R33 P0-1：被两拍判据丢掉的"单拍高"次数——现场靠它分案"一直低"与"在翻转" */
    for (;;) {
        uint32_t el = (uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS;
        int lvl = gpio_get_level(EPD_BUSY_PIN);
        if (lvl == 0) {
            if (hi_run == 1) hi_single++;
            hi_run = 0;
            lo_run++;
            if (first_low < 0) first_low = (int)el;
            if (cur_low_start < 0) cur_low_start = (int)el;
            if (lo_run >= 2 && (!require_high || seen_high >= 0)) return true;
            if (el - (uint32_t)cur_low_start >= BUSY_ACCEPT_CONFIRM_MS) {
                /* 这里必须打**这一段低有多长**（el − 本段起点），不是上限，也不是"距第一次低"：
                 * 低电平只连续了 300ms 时打 "idle the whole 8000ms" 是把"没等到高"说成"等了 8 秒
                 * 都是低"；而线在翻转时打"straight"是把高低各半说成一路低。
                 * 排查的人会照那一句去推断面板行为，而它压根没发生过。 */
                ESP_LOGE(TAG, "BUSY never gave a qualified HIGH (>=2 beats): LOW run %dms straight (started at %dms,"
                              " first_low=%dms, unqualified single-beat highs=%d, cap=%dms): panel did not accept this update",
                         (int)(el - (uint32_t)cur_low_start), cur_low_start, first_low, hi_single, timeout_ms);
                return false;
            }
        } else {
            /* R39 P0-1：这两句复位必须在**整个 else** 里，不能只在 `seen_high < 0` 那一支里。
             * 原来的写法让"见过高之后读到的高"什么都不复位 ⇒ 判据 `lo_run >= 2` 允许两段低之间
             * 夹任意多个高，于是"低-高(置 seen_high)-低-高-低"就 return true —— 而这一句 return
             * 是"这一刷成没成"的唯一判据：BUSY 还在翻转就被判"刷完了"，上层不清 `s_ready`、把
             * 命令流写进一块仍在忙的 SSD16xx（下面 `epd_display_full` 里那句"仍在忙的时候
             * SSD16xx 会把后面的 0x24/0x26/0x22/0x20 整段忽略掉"就是这个后果），屏上什么都没有
             * 而日志记成功，一直留到下次重启。`epd_wait_idle()`（require_high=false，写 RAM 前
             * 那道空闲确认）同一支失效，而且更早命中。
             * 这正是 R33 P1-1 自己立的规矩（"宣布'刷完了'也要连续两拍低，理由与高侧两拍同源——
             * 同一根高阻线、同一个串扰源，判据不能一松一紧"）——修的时候只修了高侧，低侧这条
             * 在唯一会 return true 的时间段里没被强制。同类错误第四次（R30 P0-1、R31 P0、
             * R32 P0、R33 P1-1）都出在"改一个判据时没枚举读同一根线的每一个判断点"。 */
            lo_run = 0;
            cur_low_start = -1;   /* R33 P0-1：这段连续低到此为止，下一次低重新起算。
                                   * R39 跟着 `lo_run` 一起提到 else 主体：留在下面那个
                                   * `if (seen_high < 0)` 里的话，"见过高以后"的高电平就不再作废
                                   * 这段低的起点，300ms 早退那句 `LOW run %dms straight` 会打成
                                   * "从第一次低到现在"，正是 R33 P0-1 要堵的形状。 */
            if (seen_high < 0) {
                /* R32-P0（R32 复查第 1 条）：这一处也必须"连续两拍"才算见过高。
                 * 旧写法一拍即算，而同一只文件里
                 * `epd_busy_activity()`（主动判活）自 R30 P0-1 起要求两拍——同一根线、同一个串扰源，
                 * 两处判据一松一紧，而松的这一处代价更大：本函数是"这一刷成没成"的唯一判据，
                 * 且它是在 `epd_cmd(0x20)` **刚翻过 CS/DC** 的下一拍开始采的（`epd_cmd` 末尾就有一次
                 * `cs_high()`），正是 R30 P0-1 认定的那个容性尖峰来源。尖峰一旦被记成"高过"，
                 * 随后的低 ⇒ return true ⇒ 上层不清 `s_ready`、把这一刷记成成功（`panel blanked …`），
                 * 而屏上什么都没有，这个假成功要留到下次重启。
                 * 两拍 = 2ms（下面的 1ms 步长），真受理的刷新把 BUSY 钉高是秒级，不构成新门槛。 */
                if (++hi_run >= 2) seen_high = (int)el;
            }
        }
        if (el > (uint32_t)timeout_ms) break;
        const bool finding_edge = require_high && seen_high < 0;
        vTaskDelay(pdMS_TO_TICKS(finding_edge ? 1 : 20));
    }
    /* R40 P1：这条超时出口在**线正在毫秒尺度翻高翻低**时也到得了：上面那条 300ms 早退要求"这一段
     * 连续低"，而 R39 P0-1 恰恰把 `cur_low_start` 提到"每次读到高就复位" ⇒ 一条翻转中的线永远凑不满
     * 300ms；`return true` 又要求"两拍低 且 已见过合格的高"。两条都不满足就只能把 8s 跑满落到这里。
     * 旧文案 `(panel not responding)` 断言的正是这一行自己否掉的东西：同一行印的 `first_high` 是
     * "连续两拍的合格高"（≠-1 = 实测到面板应答过一次），`single-beat highs>0` = 线在翻转。
     * R39 P0-1 立的规矩（失败行不得断言从未测过的事）在同一函数的上面那条出口改了、这一条没改——
     * 一只函数里两条失败出口改一留一，还是"改一处没扫全该改的地方"这一族。
     * ⇒ 现在只报"这一轮没等到收尾"，定性交给后面那 3 个字段（`first_high`/`first_low`/
     * `unqualified single-beat highs`；这条出口只有 3 个，另一条 `never gave a qualified HIGH` 才是 5 个）。
     * 旧名 `BUSY stuck > %dms (panel not responding)` 的引用点已就地加指针（排查记录 §22.3 U-1、
     * §22.7 R33 指纹表、烧录须知【〇】那条 R33 段）。⇒ 这块注释唯一想留下的断言是那句
     * **不随引用漂移的**：当前代码里没有任何 `ESP_LOG*` 打印旧名，它只剩注释与文档里的指针。
     * 【R42 收口：把"数命中"那一整套从代码注释里拿掉，只留判据与命令。R40/R41 两版在这里写死过
     *  7/9/63/65/16/72 与"两只口径差值恒 56"，R42 复查当场打穿三处，细节在排查记录 §28.1】
     *  ① **自指计数永不为真**：上一版写"`grep -n` 只剩本注释的两行"，而说出这句话的那一行自己就是
     *    一次命中。⇒ 这类"我这注释里有 N 处"的句子一律禁写。
     *  ② 两种"排除备份"的写法**不等价**：`--exclude-dir=backups` 按路径排，`| grep -v "/backups/"`
     *    按**整行内容**排 ⇒ 仓库里那只存档报告的命令行本身含 `/backups/` 字样，被后者误杀。
     *    ⇒ 这里只准认 `--exclude-dir=backups` 那一条口径。
     *  ③ **命中数不是常量，是时刻的函数**：【R43 订正】上一版这里写"每归档一次就给备份根一侧添一批命中
     *    （R41 那批添了 20 行）"——方向对、范围写窄了：**两侧都涨**，而涨得更凶的是仓库正文那一侧
     *    （归档一只带旧名的复查报告原文就是 +20~40 行，`--exclude-dir=backups` 排不掉它）。
     *    实测链条在排查记录 §28.1-②。⇒【R43 复查 P1-2 落地】上一版这里写"要问代码里还有几处在用旧名，
     *    用 `grep -rn` 那条 `ESP_LOG` + 旧名同行的口径（现值 0）"——两处口径错：
     *    (a) 那只尺只回答"同一行里既有 `ESP_LOG` 又含旧名"，而旧名当年就是**跨行拼接**的格式串 ⇒ 真打印
     *        它一样看不见；(b) "现值 0" ≠ "旧名 0 处"：17:13:46 现测 `grep -rn` 只取旧名第一条日志串
     *        （`BUSY` 空格 `stuck`，本文件注释里就有）= **2 处**，全部在注释、没有一处是打印。
     *    ⇒ 不漂的判据改成**读代码不读计数**：看 `epd_wait_busy_ms()` 那两条失败出口的实际打印文本
     *    （`BUSY no accepted end within` 与 `BUSY never gave a qualified HIGH`），两条都不是旧名
     *    ⇒ "没有任何打印在用旧名"的证据是这两个调用点的实参，与注释、文档里被引用多少次无关。
     *    【R43 复查 P1-1 落地】同时打掉上一版那句"`[ ]` 是刻意的：普通空格版命中 1、`[ ]` 版命中 0"：
     *    `[ ]` 与普通空格在正则里等价 ⇒ 对同一段文本两只口径必然同一个数（17:13:46 复跑**都是 0**）。
     *    当年那个 1 vs 0 量的不是"写法"，是**当时那一行注释自己写成了哪种字面**：文本里真是"BUSY 空格
     *    stuck"时两只都命中它，写成 `BUSY[ ]stuck` 时两只都不命中。⇒ "钦定命令原样写进注释就会自己命中
     *    自己"这条仍然成立（与上面 ① 同族），但换 pattern 里的空格救不了它，只有让注释文本不含那段
     *    连续字串才行——本行就是按这个改的，所以这里刻意不写那只 grep 命令的原文。
     *  要旧名在文档里的分布就自己重跑（并自己记时刻，别引用上一轮的数）：`date` +
     *  `grep -rn --exclude-dir=backups "BUSY stuck" . | wc -l`。 */
    ESP_LOGE(TAG, "BUSY no accepted end within %dms (本行不下'面板没响应'的结论，定性看后面 3 个字段):"
                  " first_high=%dms first_low=%dms unqualified single-beat highs=%d",
             timeout_ms, seen_high, first_low, hi_single);
    return false;
}

static bool epd_wait_busy(void) { return epd_wait_busy_ms(EPD_BUSY_TIMEOUT_MS, true); }
static bool epd_wait_idle(int timeout_ms) { return epd_wait_busy_ms(timeout_ms, false); }

/* 判断面板是否"活着"。R29 起判据收紧为**先看到高、再看到持续 ≥1ms 的低**（R27 复查 P1-2）：
 * 只认"看到一次低"与本文件 §十六-2 的旁证自相矛盾——轨真是 0V 时，我们自己那颗 45K 上拉的
 * 约 73uA 经 BUSY 脚的 ESD 二极管就能把它钉在 VIL 以下，那同样是一段"持续低"。
 * 而 `0x12` SWRESET 之后活面板一定会把 BUSY 推高几毫秒再放低（官方序列承诺的就是这个沿），
 * 我们从命令落棒起就以 50us 步长密采，抓不到沿只能是它根本没推。
 * 收紧会不会把好屏挡在外面？不会：本函数放行后的每一次真刷新走的都是 `epd_wait_busy()`
 * （require_high=true），那条判据本来就要求"先高后低"；给不出 SWRESET 高脉冲的面板同样过不了
 * 任何一次刷新，早一轮在这里判失败只是把"init done 但其实啥也没有"这个假成功提前戳破。
 * `*low_no_high` 出来告诉调用方"看到了持续低、但从头到尾没见过合格的高"——那是 0V 漏电的签名，
 * 与"全程高 = 没电"是两种不同的故障，日志必须分开，否则调用方那句 "likely unpowered" 会说谎。
 * R30 复查在这同一只函数上又改了两处：
 * ① P0-1：**"见过高"也要连续两拍**（密采段 2×50us，慢采段 2×10ms）。旧写法低要连续 20 拍、
 *    高只要 1 拍，而采样前 20 行刚由我们自己翻过 RST/CS/DC/SCLK/MOSI——平行走线上的容性尖峰
 *    打进高阻抗的 BUSY 只需一拍就能读成高。单拍尖峰一旦算数，"先高后低"这道判据就退化回
 *    R27 想堵的那个洞（0V 漏电 + 一次串扰 ⇒ 判"活着" ⇒ 去驱动 5 根脚）。
 *    代价：真活着的面板在 SWRESET 后要把 BUSY 钉高好几毫秒（官方序列承诺的就是这个沿），
 *    连续两拍 = 100us/20ms 都在它的高电平窗口内，不构成新的门槛。
 * ② P0-3：`*low_no_high` 必须在**出口**算，不能在密采段 break 之前先写死。旧写法 break 进
 *    慢采段后仍可能看到高，而它一路带着 true 走到 return false ⇒ 日志打出"全程没见过高"，
 *    而"全程"是假的。本轮唯一交付物就是这条分案日志，它自己说胡话就等于定案定错。
 * R31 复查（R30 的 P0-1/P0-3 修完之后的新形状）又抓到同一只函数上的一处：
 * ③ R31 P0：**两段都不许在"还没见过高"时提前 break**。面板发完 `0x12` 之前是空闲的，BUSY
 *    本来就是低 ⇒ 密采从第 1ms 起就凑满 20 拍低并跳出，"必须抓到的那个高沿"只剩下慢采段
 *    10ms 分辨率的窗口；而它自己承诺的是"钉高**好几毫秒**"（上面 ①），比 10ms 窄，
 *    连续两拍高在 10ms 采样下**物理上不可能同时命中** ⇒ 一块活面板被恒判成"0V 钳位签名"，
 *    电轨未确认期间每 12 轮唯一的主动判活通道永远过不去。修法：低凑满只记 `seen_low`，
 *    **不 break**，把有 50us 分辨率的密采段跑满它自己的 50ms，再让慢采段跑到 1800ms 上限。
 *    代价：判失败的轮从原来约 21ms 变成跑满 ≈1.85s —— 这正是 §R27 持锁时长表里**本来就按
 *    1.85s 预算**的那一段，所以 20s 锁等待的算术不变，只是失败轮第一次真花满它。
 * ④ R31 P2-1：出口的两个"为什么失败"不能只靠散文列举。`saw_low/saw_high` 两位一起打出来。
 * ⑤ R33 P1-2 之后，①里"慢采段 2×10ms"和它末尾"连续两拍 = 100us/20ms"两处的**慢采段那一半**
 *    只对 R32 及以前成立：现在慢采段每次 10ms 醒来后补采 40×50µs（≈2ms），**高**侧是"段内连续两拍"
 *    （=100µs 尺度，与密采段同口径），**低**侧仍是"相邻两段全程为低"（≈一个 12ms 周期尺度）。
 *    ③的论证（"几毫秒宽的沿在 10ms 分辨率下物理上采不到"）没有被推翻——它被按方向解决了：
 *    分辨率回到 50µs，代价是那段 2ms 忙等（见下面慢采段的【代价】）。 */
static bool epd_busy_activity(bool *saw_low, bool *saw_high)
{
    int hi_run = 0;
    int low_run = 0;
    bool seen_high = false;
    bool seen_low = false;
    *saw_low = false;
    *saw_high = false;
    for (int i = 0; i < 1000; i++) {   /* 1000 拍 × 50µs 延时 = **下限** 50ms：每拍还要 `gpio_get_level`
                                        * + 分支的开销，真实墙钟只会比 50ms 长（R39 P2-4：以前这里直接
                                        * 写"≈50ms"，与位碰段那条"排定延时 ≠ 实测耗时，余下是调用开销"
                                        * 是同一类口径，只是窗更短）。方向对判据无害——窗只会更宽。
                                        * 本段是全程唯一有 50µs 分辨率的窗口。 */
        if (gpio_get_level(EPD_BUSY_PIN) == 0) {
            hi_run = 0;
            if (++low_run >= 20) {                /* 连续 1ms 为低 */
                seen_low = true;
                if (seen_high) {                  /* 高过再放低 = 面板受理并做完了软复位 */
                    *saw_low = *saw_high = true;
                    return true;
                }
                /* 没见过高：**不 break**，继续把密采段跑完（R31 P0）。low_run 往后只增不减，
                 * seen_low 已定，这里什么都不做，靠循环底部的延时继续采样。 */
            }
        } else {
            low_run = 0;
            if (++hi_run >= 2) seen_high = true;
        }
        esp_rom_delay_us(50);
    }
    uint32_t t0 = xTaskGetTickCount();
    int prev_low = 0;   /* R33 P1-2 之后高侧不再需要"上一段也高"（两拍已在那 40 拍里判完），所以只留低侧的 */
    for (;;) {
        if ((uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS > EPD_LIVENESS_SLOW_WINDOW_MS) break;
        vTaskDelay(pdMS_TO_TICKS(10));
        /* R33 P1-2：慢采段原来只用 10ms 分辨率找那个"几毫秒宽"的上升沿——连续两拍高在 10ms
         * 步长下要求脉宽 ≥10ms，而 R31 P0 的整段论证（上面 ③）说的就是"它承诺的沿比 10ms 窄，
         * 物理上不可能同时命中"。R31 只拿这条论证删掉了提前 break，没回答"那 50ms 之后呢"：
         * 密采段跑完 50ms 之后，判据仍然要 10ms 尺度上的两拍 ⇒ 一个 `0x12` 之后 50ms 才翻高、
         * 高只持续几毫秒的**活面板**永远给不出合格的 `seen_high` ⇒ 被按"0V 漏电签名"定案。
         * 修法不动判据，只把"一拍"的时间尺度换回来：每次 10ms 醒来后用 50µs 步长补采 40 拍
         * （≈2ms），段内凑出连续两拍高即算"高"（与密采段同口径），整段 40 拍都低才算"低"。
         * 代价：每次唤醒多花 ≈2ms **忙等**（`esp_rom_delay_us` 不让出 CPU）。一个 1800ms 窗口里
         * 每次循环 ≈10ms 睡 + 2ms 忙 ⇒ 约 150 次唤醒 ⇒ 合计 ≈**300ms 忙等**（不是"36ms"，
         * 我第一版把 180×2ms 写掉了个数量级，R33 自查改回）。
         * **总墙钟时长不变**（还是 `EPD_LIVENESS_SLOW_WINDOW_MS` 上限，由循环开头那道
         * `(now−t0)>EPD_LIVENESS_SLOW_WINDOW_MS` 守住），
         * 所以 `RELEASE_CLAIM_WAIT_MS` 上方与 `eink_display.c` 那条持锁链的算术都不用重算；
         * 变的是这 1.85s 里 CPU 的占用形状：idle 每 12ms 才有 10ms 可跑（本任务优先级 1，
         * 压着 idle 的那 2ms ⇒ idle 被让位的**频率变低**、两次喂狗之间的最大间隔从 10ms 变成 12ms，
         * 即窗口变**疏**不是变密（R39 P1-13：我原先写的"变密"把因果说反了，和上一句"每 12ms 才有
         * 10ms 可跑"自相矛盾）。12ms ≪ Task WDT 的 5s，结论不变：不构成饿死。 */
        int burst_hi = 0;                 /* 这 2ms 里出现过"连续两拍高"（100µs 尺度） */
        int burst_all_low = 1;            /* 这 2ms 全程为低 */
        int br = 0;
        for (int i = 0; i < 40; i++) {
            if (gpio_get_level(EPD_BUSY_PIN) != 0) {
                burst_all_low = 0;
                if (++br >= 2) burst_hi = 1;
            } else {
                br = 0;
            }
            esp_rom_delay_us(50);
        }
        const int low = burst_all_low;
        const int high = burst_hi;
        if (low && prev_low) {                    /* 相邻两段的 2ms 都全程为低：真实驱动而非噪声 */
            seen_low = true;
            if (seen_high) {
                *saw_low = *saw_high = true;
                return true;
            }
            /* 同样不 break：没有高沿时把这段走到 1800ms 上限，好让"没抓到高"真的意味着
             * "这段时间里没有合格的高"，而不是"我只看了 20ms"。 */
        }
        if (high) seen_high = true;     /* "两拍"已经在那 40 拍里满足了，不再要求相邻两段都高（P0-1/R33 P1-2） */
        prev_low = low;
    }
    *saw_low = seen_low;
    *saw_high = seen_high;
    return false;
}

static void epd_reset(void)
{
    pin_set(EPD_RST_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(50));
    pin_set(EPD_RST_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(2));
    pin_set(EPD_RST_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(50));
}

/* 官方 EPD_Init 寄存器序列（0x12 SWRESET + 面板参数 + 全屏窗口）。
 * 返回 true 仅当面板对软复位有 BUSY 反应（先高后低，真活着）；否则 false 让上层重试。
 * 顺带清 `s_cmd_dropped`：本函数自己发的那一串命令若有任何一笔没出去，probe 那边要把本轮作废。 */
static bool epd_panel_init(void)
{
    bool low_no_high = false, saw_low = false, saw_high = false;
    s_cmd_dropped = false;
    epd_reset();
    /* R32-P1（R32 复查第 2 条）在这里立了 `pre_high` 这个观察位；R33 复查第 2 条把它脚下的地
     * 挖开了一块，两条都成立，所以这一段整个重写：
     * ① 旧立论"每一条升级到主动判活的路径都在几毫秒前刚通过 `epd_busy_passive_low()`"**是假的**。
     *    进 `epd_panel_init()` 的路径有两条：`probe_attempt()` 那条有预检，
     *    `epd_display_full()` 那条**没有**（它在门口只看 `s_ready`）。
     * ② 即使在有预检的那条上，预检证明的是 `epd_reset()` **之前**线是低的，它不排除"复位自己
     *    打出一个高"这个变体——我当初写那句"到不了"，为的是否证报告，而同一轮我又在别处承认过
     *    这个沿会落进采样窗（`烧录须知.md` 的 `pre_high` 节）。
     *    官方恰恰在这两步之间专门插了一次等待：`EPD_Reset()` → `EPD_ReadBusy()` → `0x12`
     *    （`ESP-IDF/08_ESP32-S3_e-Paper-3.97/components/epaper_port/epaper_port.c:238-242`），
     *    而那个函数进门先无条件睡 100ms（同文件 `:165-176`）⇒ 厂商给"复位余高"的预算是 **≥100ms 起**，
     *    本驱动当时只给了 `epd_reset()` 末尾那 50ms + 1.5ms 的看一眼。
     * ⇒ 现在把"看一眼"换成**有界等低**（上限 `EPD_PRE_RESETTLE_WAIT_MS`，1ms 步长、要连续两拍低）：
     *    `epd_busy_activity()` 抓到的第一个合格高沿由此只可能来自 `0x12`，与官方同形。
     *    仍然**不是闸门**：等不到低也照发 `0x12`，只把 `pre_high=1`（+ `pre_low_ms=-1`）打出来——
     *    拿"发 0x12 前必须是低"去挡 = 用一个未证实的推断屏蔽唯一的实证通道，R31 P0 那类
     *    "判据在采样窗内不可达"不能再犯。
     * 报告原来那个"残余电荷经我们自己那颗 45K 上拉做 RC 上升、再被漏电平回去"的变体**仍然排除不掉**
     * （节点电容 C 无实测，τ = 45K × C 从 ns 到 ms 都排除不掉：几十 pF~几 nF 只给到 µs 级，
     * 要毫秒级需 C≈20nF，没依据说它不是），所以 `pre_high` 这一位留着，现场读法不变：
     * "pre_high=1 时这一轮的"先高后低"不能算应答证据**（收紧之处：现在它的含义是
     * "等了 `EPD_PRE_RESETTLE_WAIT_MS` 都没凑齐连续两拍低"，比原来的"三拍里有一拍是高"窄）。
     * 顺带交付一个观测量：`pre_low_ms` = 从 `epd_reset()` 末尾那 50ms **之后**到线稳住低用了多久
     * （-1 = 上限内没等到）⇒ 复位自身 BUSY 脉宽的下界估计 = 50 + `pre_low_ms`，这回答 todo 第 62 条。 */
    int pre_high = 0;
    int pre_low_ms = -1;
    {
        int rt_lo_run = 0;
        const uint32_t rt0 = xTaskGetTickCount();
        for (;;) {
            const uint32_t el = (uint32_t)(xTaskGetTickCount() - rt0) * portTICK_PERIOD_MS;
            if (gpio_get_level(EPD_BUSY_PIN) == 0) {
                if (++rt_lo_run >= 2) { pre_low_ms = (int)el; break; }
            } else {
                rt_lo_run = 0;
            }
            if (el >= (uint32_t)EPD_PRE_RESETTLE_WAIT_MS) { pre_high = 1; break; }
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
    epd_cmd(0x12);  /* SWRESET：活面板会拉高 BUSY 数毫秒再放低 */
    if (!epd_busy_activity(&saw_low, &saw_high)) {
        low_no_high = saw_low && !saw_high;
        /* 四位一起打出来（R31 P2-1 起两位，R32 加 `pre_high`，R33 加 `pre_low_ms`）：光靠括号里
         * 列举"一直是高 / 单拍尖峰"枚举不全——"先持续低、50ms 之后才来成对的高、到 1800ms 仍高"
         * 同样走到这一行，而它两种都不是。现场是按这几行分案的，形状必须自己说话。 */
        ESP_LOGW(TAG, "panel silent after SWRESET: %s (pre_high=%d pre_low_ms=%d saw_low=%d saw_high=%d)",
                 low_no_high ? "看到持续低但没有任何成对的高 = 0V 轨被自家上拉钳低的签名（判不应答，见 epd_busy_activity 上方；密采 50ms + 慢采 1800ms 全程都没高）"
                             : "BUSY 没给出【先连续高、再持续低】的软复位应答：likely unpowered",
                 pre_high, pre_low_ms, (int)saw_low, (int)saw_high);
        return false;
    }
    if (pre_high) {
        /* 通过的那一轮也要把"存疑"说出来：这一行出现 = 判活形状凑齐了，但 BUSY 在发 0x12 之前
         * 等了 `EPD_PRE_RESETTLE_WAIT_MS` 都没凑齐**连续两拍低** ⇒ 那个高沿不能归因给 SWRESET（可能来自
         * epd_reset() 的硬件复位脉冲余高，也可能来自 45K 上拉下节点电容的 RC 上升）。
         * 注意这一位的准确含义是"没凑齐两拍低"，**不是**"末拍读到高"（R39 P2-2：原来的英文句
         * "busy was HIGH before 0x12" 比判据强——一个"低-高-低"序列在 500ms 上限处置位，
         * 而最后一次采样读到的就是低）⇒ 措辞改成 NOT stably LOW，别让现场按"钉高"读。
         * 本轮仍按"活着"处理（挡掉它 = 用一个未证实的推断去屏蔽唯一的实证通道），
         * 但现场要把这一行和 `init done` 一起看。 */
        ESP_LOGW(TAG, "busy NOT stably LOW before 0x12 (等连续两拍低 %dms 没等到，末拍不一定为高): 判活形状通过但那个高沿无法归因给 SWRESET"
                      " ⇒ 存疑活屏（pre_high=1 saw_low=%d saw_high=%d）",
                 EPD_PRE_RESETTLE_WAIT_MS, (int)saw_low, (int)saw_high);
    }
    if (s_cmd_dropped) {   /* 上面那笔 0x12 就没出去：BUSY 的反应不是我们触发的，别记成"活着" */
        ESP_LOGE(TAG, "SWRESET 本身没发出去（spi_write 失败）→ 本轮判活作废");
        return false;
    }

    epd_cmd(0x18); epd_data(0x80);

    epd_cmd(0x0C);
    epd_data(0xAE); epd_data(0xC7); epd_data(0xC3); epd_data(0xC0); epd_data(0x80);

    epd_cmd(0x01);  /* driver output control */
    epd_data((EPD_HEIGHT - 1) % 256);
    epd_data((EPD_HEIGHT - 1) / 256);
    epd_data(0x02);

    epd_cmd(0x3C); epd_data(0x01);  /* border waveform */

    epd_cmd(0x11); epd_data(0x01);  /* data entry mode */

    epd_cmd(0x44);  /* RAM X window (像素地址，官方即如此) */
    epd_data(0x00); epd_data(0x00);
    epd_data((EPD_WIDTH - 1) % 256); epd_data((EPD_WIDTH - 1) / 256);

    epd_cmd(0x45);  /* RAM Y window */
    epd_data((EPD_HEIGHT - 1) % 256); epd_data((EPD_HEIGHT - 1) / 256);
    epd_data(0x00); epd_data(0x00);

    epd_cmd(0x4E); epd_data(0x00); epd_data(0x00);  /* x counter = 0 */
    epd_cmd(0x4F); epd_data(0x00); epd_data(0x00);  /* y counter = 0 */
    /* 写 RAM 前必须确认面板空闲——仍在忙的时候 SSD16xx 会把后面的 0x24/0x26/0x22/0x20
     * 整段忽略掉，而那串"看起来全都发成功了"。上限压到 300ms（不用 8s：判活刚看到 BUSY
     * 放低，这里正常只花两拍 ≈20ms（R33 P1-1 起"低"也要连续两拍，这一支步长 20ms，见
     * `epd_wait_busy_ms` 上方）；8s 会把开机时的配网门户同样时长推后）。
     * 超时一律判失败：宁可不刷这一帧，由上层清 s_ready → 监视任务重新判活重来。 */
    if (!epd_wait_idle(300)) {
        ESP_LOGW(TAG, "panel still busy 300ms after init: skip this refresh");
        return false;
    }
    return true;
}

/* 局刷窗口寄存器（官方 Display_Partial 前半段，坐标为像素）。
 * 与官方有意不同的一处：官方把 Xend 先折算成字节再 `Xend-=1`、又乘回 8，
 * 于是窗口终点落在 8 的整数倍上，比它自己随后写入的字节数少最多 7 列（官方口径的
 * 自相矛盾）。这里按"写入多少字节就开多大窗"取 px1=b1*8-1，与 epd_write_fb_rows
 * 每行推 (b1-b0) 字节严格自洽。0x45 与官方一致是"终点在前、起点在后"。 */
static void epd_set_window(int px0, int py0, int px1, int py1)
{
    epd_cmd(0x44);
    epd_data(px0 % 256); epd_data(px0 / 256);
    epd_data(px1 % 256); epd_data(px1 / 256);
    epd_cmd(0x45);
    epd_data(py1 % 256); epd_data(py1 / 256);
    epd_data(py0 % 256); epd_data(py0 / 256);
    epd_cmd(0x4E);
    epd_data(px0 % 256); epd_data(px0 / 256);
    epd_cmd(0x4F);
    epd_data(py0 % 256); epd_data(py0 / 256);
}

/* 把 fb 中窗口部分的每一行连续写入当前 RAM 平面（X 计数器自动回卷到窗口起点） */
static void epd_write_fb_rows(const uint8_t *fb, int byte0, int byte1, int y0, int y1)
{
    int w = byte1 - byte0;
    cs_low();
    dc_data();
    for (int y = y0; y < y1; y++) {
        spi_write(fb + (size_t)y * EPD_STRIDE + byte0, w);
    }
    cs_high();
}

/* SPI 总线 + 面板控制脚：只做一次，幂等（监视任务反复 probe 不会重复占用）。 */
static bool epd_bus_setup(void)
{
    if (s_bus_ok) return true;

    spi_bus_config_t buscfg = {
        .miso_io_num = -1,
        .mosi_io_num = EPD_MOSI_PIN,
        .sclk_io_num = EPD_SCLK_PIN,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4096,
    };
    spi_device_interface_config_t devcfg = {
        .spics_io_num = -1,  /* CS 手动翻：官方全程拉低，这里每条命令显式框定 */
        .clock_speed_hz = 20 * 1000 * 1000,
        .mode = 0,
        .queue_size = 1,
    };
    esp_err_t e = spi_bus_initialize(SPI3_HOST, &buscfg, SPI_DMA_CH_AUTO);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "spi_bus_initialize failed: %s", esp_err_to_name(e));
        return false;
    }
    if (e == ESP_ERR_INVALID_STATE) {
        /* 5.1.6 口径：这个返回码只表示"这台控制器上总线还装着"（上一轮 `spi_bus_remove_device`
         * 失败时我们是**故意**不拆总线的），不是失败，也不是"我刚装好了"。不打这行就成了
         * 静默吞掉一个状态，将来若真出现"句柄丢了但总线还在"，这里会直接变成漏一套 device/队列
         * 而日志上一片空白（R27 复查 P1-5 指的就是这种"钱照付证据全丢"）。
         * R31 复查 P1-2：这句话原来无条件印"不重复 add device"，可紧接着的 `if (!s_spi)` 有时
         * **真的**会再 add 一个（`spi_bus_add_device` 走 nomem 分支时 `free(dev); return
         * ESP_ERR_NO_MEM;`，本机 gpspi/spi_master.c:485-493 ⇒ 总线在、句柄为 NULL）。现场按
         * 【烧录须知】读这行会得出"句柄还挂着、没新设备"的错误结论 ⇒ 文案必须分两档。 */
        if (s_spi) {
            ESP_LOGW(TAG, "spi_bus_initialize: 总线仍在（上一轮未拆）→ 复用句柄，不重复 add device");
        } else {
            ESP_LOGW(TAG, "spi_bus_initialize: 总线仍在但**无句柄** → 下面重新 add device"
                          "（注意：复用未拆掉的总线不会重做 SCLK/MOSI 的引脚矩阵连接，那只发生在 spi_bus_initialize 里）");
        }
    }
    if (!s_spi) {
        e = spi_bus_add_device(SPI3_HOST, &devcfg, &s_spi);
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
    /* 两处 gpio_config 的返回值必须查：配置失败时引脚其实没驱动/没输入，
     * 后面 s_bus_ok=true 就是"我以为总线ready了"，刷屏会静默变成空操作。 */
    if (gpio_config(&out) != ESP_OK) {
        ESP_LOGE(TAG, "panel output pins (RST/DC/CS) config failed");
        return false;
    }
    gpio_config_t in = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = (1ULL << EPD_BUSY_PIN),
        /* BUSY 用内部上拉：活面板是推挽输出，强弱不受 45K 上拉影响；面板没电时这根脚
         * 无论"板上本来就有外部上拉"还是"只有我们的内部上拉"都会被钉在高电平。
         * 判活只认"持续 ≥1ms 的低电平"，于是"没电/浮空"一律判没电，绝不会把噪声
         * 当成应答去刷一张永远不亮的屏。
         * 注意：官方 demo 写的 .pull_up_en = GPIO_PULLDOWN_ENABLE 是笔误，枚举值同为 1
         * 且 gpio_config 只判真假，实际生效的是上拉——这里显式写对上拉。 */
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    if (gpio_config(&in) != ESP_OK) {
        ESP_LOGE(TAG, "BUSY pin (GPIO%d) config failed", EPD_BUSY_PIN);
        return false;
    }
    cs_high();
    pin_set(EPD_DC_PIN, 1);
    pin_set(EPD_RST_PIN, 1);
    s_bus_ok = true;
    return true;
}

/* 一次点屏尝试：best-effort 开 ALDO3 轨 → 面板判活。
 * 屏电只能由 PMIC 的 ALDO3 出——这条**在 R33 从"照官方抄、本板未证实"升级成"芯片侧映射已证实"**，
 * 依据是随板例程本身（不需要仪器）：
 *   `ESP-IDF/08_ESP32-S3_e-Paper-3.97/components/epaper_port/epaper_port.c:182-186`
 *     `EPD_Power_ON(){ enapwrstate(ALDO3); }`（那句在 `:184`），而它在 `EPD_Init()` 的第一条语句（同文件 `:236`）
 *     ⇒ 威发给这块 3.97 板写的点屏流程就是"先开 ALDO3"；
 *   `enapwrstate` 只是随板 wrapper：`…/08_…/components/axpPower/axp_prot.cpp:197-213`，
 *     `case ALDO3: return axp2101.enableALDO3();` 在 `:206-207`；同一只文件的初始化里
 *     `:57` = `axp2101.setALDO3Voltage(3300)` ⇒ 官方给这一路的目标电压就是 3.3V（对得上下面的 0x1C）
 *   `…/08_…/components/axpPower/src/XPowersAXP2101.tpp:1840-1842`
 *     `enableALDO3() = setRegisterBit(XPOWERS_AXP2101_LDO_ONOFF_CTRL0, 2)`
 *   `…/08_…/components/axpPower/src/REG/AXP2101Constants.h:117` (`…_LDO_ONOFF_CTRL0 = 0x90`)、
 *     `:121` (`…_LDO_VOL2_CTRL = 0x94`)、`:205-207` (ALDO3 量程 500/3500/步进 `…_VOL_STEPS = 100u`)、`:5` (chip id 0x4A)
 *   ⇒ 本驱动 `axp_panel_power.c` 的 `AXP_REG_LDO_ONOFF0 0x90` / `AXP_REG_ALDO3_VOL 0x94` /
 *     `ALDO3_BIT 2` / `(v & 0xE0) | 0x1C`（0x1C = (3300−500)/100，落在 500~3500 量程内）逐条对得上；
 *     编码形状也不是我推的：`tpp:1863-1864` 就是 `read(0x94)&0xE0 | (mV−500)/100`，读回那边用 `&0x1F`（`:1870-1871`）。
 * **仍然没有证实的是"物理那一跳"**：ALDO3 的引脚在本板上是否真的接到屏的 EPD_VCC（图纸口径 +
 * 万用表才能定，见 todo 第 51 条半关），以及"回读一致"是否等于"轨上真有 3.3V"。
 * 而开这一路必须 I2C 写成功；PMIC 不应答时这里返回 false，由 eink 层的监视任务稍后再
 * probe —— 用户任何时刻让 PMIC 上电/开机，屏都会在下一轮亮起。
 * 注意"PMIC 不应答 = 整机没开机"只是推测，不是已证实的因果：按图纸口径 VCC3V3 本身就是
 * PMIC 的 DCDC1 输出，MCU 现在能跑就说明 PMIC 有电，那 0x34 沉默更可能是我方通路问题。
 * 每轮日志里的 ACK/NACK/TMO 计数就是两者的分界（见 axp_panel_power.c 的 axp_scan_known）。
 *
 * "AXP 回读没确认置位"同样不能当成永久否决：那一次 I2C 读超时、或"ALDO3 输出接到屏"这一跳
 * 猜错，都会把好屏永久锁在闸门后面（接上电池也照样不亮），而这条判据至今没在
 * 真机走过成功分支。所以每 PANEL_PROBES_PER_LIVENESS 轮放它过去做一次真实的 BUSY 判活：
 * 判活本身不依赖 AXP，是最下层的证据。代价有界（1.85s / 12 轮），换来"假设错也不盲"。 */
#define PANEL_PROBES_PER_LIVENESS 12

/* 概率性闸门的兜底（R27 复查 P0-1/P0-3）：下面两条闸门——旁证 `highs==0`、PWR_OUT 读成
 * 【系统轨未开】——都**从没在实板上验证过**，而它们挡下的是同一份被动证据："面板自己在
 * 驱动 BUSY"。永久否决就成了"用一个没证实的推断，把唯一能拿到的实证堵死"，好屏会被自己的
 * 固件锁死一整个上电周期（`highs>0` 原先是绝对判据，一旦某轨残余电荷把 5 根脚都吃低，
 * 就再也翻不回来）。所以：同一份证据累计被挡 3 次（≈36 轮 ≈3 分钟）就不再拦，照样放行一次
 * 主动判活。代价有界且写清：向可能 0V 的面板轨多驱动一轮 5 根引脚，走的正是那条未证实的
 * ESD 倒灌路径。
 * 契约（这条必须写死，不然两条闸门叠加时又会变成永久否决）：返回 true = "别再拦了"；
 * 计数**只由调用方在真正升级的那一刻清零**（probe_attempt 里那句 s_passive_veto = 0），
 * 命中阈值时本函数**不**自己清零——否则 witness 先归零、PWR_OUT 永远数不到 3。 */
#define PASSIVE_VETO_OVERRIDE 3
static unsigned s_passive_veto;
/* 本轮（同一个 `s_probe_round`）是否已经为这份证据计过户。R32-P2（R32 复查第 6 条）：
 * 一轮里有两个以上的闸门可以命中——最直白的一条是 `witness highs=0` 走到 `veto_reached`
 * 返回 true（第 3 次）之后，本轮并没有 return，接着 `sys_off` 那一道又调一次 ⇒ 一份证据记两笔，
 * "累计 3 次 ≈36 轮"的实际节律变成最快 18 轮，且那条"最近一次：〈闸门〉"日志会把同轮的两道闸
 * 说成两次独立否决。以轮号去重，不改"3 次"这条判据本身的物理含义。 */
static unsigned s_veto_round;

static bool veto_reached(const char *gate)
{
    if (s_veto_round != s_probe_round) {
        s_veto_round = s_probe_round;
        ++s_passive_veto;
    }
    if (s_passive_veto < PASSIVE_VETO_OVERRIDE) return false;
    ESP_LOGW(TAG, "被动证据（BUSY 被驱动）已累计被闸门挡下 %u 次，最近一次：%s → 未实测的闸门不许永久否决判活，"
                  "本轮起不再拦（代价：向可能 0V 的轨再驱动一轮 5 根脚，ESD 倒灌路径未证实）",
             (unsigned)s_passive_veto, gate);
    return true;
}

/* 电轨没确认时那"每 12 轮一次"的放行，先做**纯被动** BUSY 采样：本函数自己只把 GPIO3 配成
 * 输入 + 内部上拉（RST/DC/CS/SCLK/MOSI 一根都不**驱动**）。若这根脚读出"持续低"，接着要做
 * 一次旁证读（下面 `epd_pins_release()` + 输入上拉读 5 根）——那时是**先整套交还**再借上拉
 * 电流读，仍然不驱动任何一根（R31 P2-3 更正：旧注释写"一根都不碰"是过头的话）。理由：
 * BUSY 是面板的**输出**，内部上拉下
 * "看到持续低"只能是有东西在真驱动它 = 面板有电（口径见 epd_busy_activity 前的三条证据），
 * 这是"敢去驱动其余引脚"的唯一凭证；反过来一直读高 = 面板没电，此时做
 * epd_bus_setup()+epd_reset()+SWRESET 就是把 RST/CS/DC/SCLK/MOSI 推向一个可能 0V 的
 * 面板、经它内部 ESD 二极管倒灌——那才是主倒灌路径（R24 放松闸门后一直开着，
 * R25 只堵了深睡那一路，属自己引进的回归，见排查记录 §十五）。
 * 被动采样还更早发现电：电一到位，空闲面板立刻把 BUSY 拉低，不用等下一次主动判活。
 * 代价：面板若正在刷新中（BUSY 高）会被判"没电"，但只有本驱动会发起刷新，而发起刷新
 * 的前提是 s_ready 已为真、probe 早在上面 return 了，所以这一档在本固件里不会发生。
 *
 * **但"读到低"不是"面板有电"的铁证（R27 复查 §十六-2）**：面板那一轨真是 0V 时，我们这根
 * 45K 上拉约 73uA 的电流会经 BUSY 脚自身的 ESD 二极管灌进 0V 轨，把脚钳在 VIL(0.825V) 以下
 * ⇒ 静态读出来同样是"持续低"，而它紧接着要求的正是"去驱动其余 5 根脚"——本轮要防的倒灌
 * 就这么被放行。钳位电压到底会不会低到 VIL 以下**未证实**（无仪器，见 todo 第 49 条同类）。
 * 用一个不需要仪器的旁证把它分开：真活着的面板只会把 BUSY 这一根**输出**拉低，
 * RST/DC/CS/SCLK/MOSI 对它是高阻输入、会被我们自己的上拉读成高；整轨 0V 时这些脚各有各的
 * ESD 二极管，同样被吃成低 ⇒ "BUSY 低 + 至少一根旁证脚高"才升级为主动判活。
 * 旁证只是概率性证据（残余电荷/漏电通路都可能让它偏），所以两条日志都把"未证实"写全，
 * 而且它**没有永久否决权**：同一份被动证据累计被挡 3 次就由 veto_reached() 照样放行一次。 */
static bool epd_busy_passive_low(bool rail_off)
{
    gpio_config_t in = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = 1ULL << EPD_BUSY_PIN,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    if (gpio_config(&in) != ESP_OK) {
        ESP_LOGW(TAG, "passive BUSY sample: gpio_config failed → 本轮无任何判活证据");
        return false;
    }
    bool alive = false;
    int low_run = 0;
    for (int i = 0; i < 400 && !alive; i++) {        /* 400 × 100us ≈ 40ms，不阻塞别的事件 */
        if (gpio_get_level(EPD_BUSY_PIN) == 0) {
            if (++low_run >= 10) { alive = true; break; }   /* 连续 1ms 低 = 真在驱动 */
        } else {
            low_run = 0;
        }
        esp_rom_delay_us(100);
    }
    /* 括号里必须按 `rail_off` 分两种说法（R31 复查 P1-1）：这一行在**电轨已确认**时也是每轮都打
     * （`rail_off==false` 表示"0x34 会应答 + 0x90 那一位写得进且回读一致"，见 probe_attempt 上方），
     * 旧写法固定印 "rail unconfirmed" ⇒ 恰好在电池接上、闸门第一次真打开那天起，每轮朝
     * "电轨没到手"打一行，而【烧录须知】里 `passive BUSY sample` 那两档教现场按这两行的**出现频率**判案
     * （交叉引用不写裸行号：那份文档一轮能涨几十行）。
     * 第二档仍然不能读成"面板有电"（R33 改口径）：`0x90`↔bit2↔ALDO3 这一层**芯片侧映射已由盘中
     * 官方文件证实**（推导写在 `probe_attempt()` 上方），没证实的是"ALDO3 引脚在本板上接到屏的
     * EPD_VCC"这一跳，以及"回读一致 = 轨上真有电"。 */
    ESP_LOGW(TAG, "passive BUSY sample (%s, 其余脚未驱动): %s",
             rail_off ? "rail unconfirmed"
                      : "rail confirmed-by-readback（仅指 0x90 那一位回读一致；ALDO3→屏电轨那一跳仍未证实）",
             alive ? "sustained LOW → 有人在拉低（面板驱动 或 0V 轨漏电，见旁证行）"
                   : "stayed HIGH (40ms) → 面板没在驱动这根脚，本轮不碰任何其他引脚");
    if (!alive) return false;

    /* 旁证读（§十六-2 + R27 复查 P1-4）：先把可能还挂着的驱动整套交还（含 SPI），再把面板脚
     * 配成"输入 + 内部上拉"读一遍——只借上拉电流，一根都不驱动。
     * 顺序必须在 release 之后：release 之前 SCLK/MOSI 还挂在 SPI 控制器的 GPIO 矩阵输出上，
     * `gpio_get_level` 读到的是控制器自己 driving 的电平，不是面板轨的电平。
     * **但"交还之后这个问题就消失了"是 R29 说错的（R30 复查 P1-2）**：`epd_pins_release()`
     * 在 `spi_bus_remove_device` 失败那一刻是**故意**留着 SCLK/MOSI 归控制器的（否则"交还"
     * 这句话变成假的），所以那两根仍然只能按 `s_spi` 是否还在来决定读不读。R29 无条件配 5 根
     * 除了读到无意义的电平，还有个更坏的后果：把这两根从控制器上拆下来，而
     * `epd_bus_setup()` 复用一条没拆掉的总线时不会重新 add_device（引脚连接是在
     * `spi_bus_initialize` 里做的），于是它们**永远接不回 SPI** —— 之后每一笔 `spi_write`
     * 照样返回 ESP_OK（`s_cmd_dropped` 恒 0）、线上根本没有时钟，屏从此再也点不亮，
     * 而日志看着一切正常。没句柄才读；读不到就打 "-"、不进分母。 */
    epd_pins_release();
    const bool wit_spi = (s_spi == NULL);
    static const int kWit[] = { EPD_RST_PIN, EPD_DC_PIN, EPD_CS_PIN, EPD_SCLK_PIN, EPD_MOSI_PIN };
    enum { KWIT_N = sizeof(kWit) / sizeof(kWit[0]) };
    uint64_t wit_mask = (1ULL << EPD_RST_PIN) | (1ULL << EPD_DC_PIN) | (1ULL << EPD_CS_PIN);
    if (wit_spi) wit_mask |= (1ULL << EPD_SCLK_PIN) | (1ULL << EPD_MOSI_PIN);
    gpio_config_t w = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = wit_mask,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    if (gpio_config(&w) != ESP_OK) {
        ESP_LOGW(TAG, "witness: gpio_config failed → BUSY 低无法二次分案，本轮不定案");
        /* R32-P2（R32 复查第 8 条后半）：这一档同样进那个 3 次计数，但它和 `highs=0` **不是一回事**——
         * 那里是"读到了、读数指向 0V 轨"，这里是"本轮一条旁证都没读出来"。R30 P2-4 已决定不拆
         * 计数器（拆成三个就把放行节律变成三套，超出这条判据该承担的复杂度），代价是计数值会
         * 混着两种含义：日志里的 `最近一次：〈闸门〉` 只说明**最后那一次**是哪道闸，前面两次各是
         * 哪种看不出来。所以现场读到"已累计 3 次"时不能反推"三次都是旁证读高=0"。 */
        return veto_reached("witness 读不出（gpio_config 失败）");
    }
    vTaskDelay(pdMS_TO_TICKS(5));            /* 上拉建立，与 pull compare 同一读法 */
    char ss[KWIT_N][4];
    int highs = 0, read_n = 0;
    for (int i = 0; i < KWIT_N; i++) {
        /* 按**脚号**判"这两根仍归 SPI 控制器"，不按数组下标（R31 P2-4）：写 `i >= 3` 等于把
         * 正确性押在 kWit[] 的排列顺序上，日后有人重排数组就会把仍归控制器的两根配成输入，
         * 重演上面那段"永远接不回 SPI"的静默故障。 */
        if (!wit_spi && (kWit[i] == EPD_SCLK_PIN || kWit[i] == EPD_MOSI_PIN)) {
            ss[i][0] = '-';
            ss[i][1] = 0;
            continue;
        }
        const int lvl = gpio_get_level(kWit[i]);
        snprintf(ss[i], sizeof(ss[i]), "%d", lvl);
        read_n++;
        if (lvl) highs++;
    }
    ESP_LOGW(TAG, "witness (pullUP only, 不驱动): RST=%s DC=%s CS=%s SCLK=%s MOSI=%s | highs=%d/%d%s → %s",
             ss[0], ss[1], ss[2], ss[3], ss[4], highs, read_n,
             read_n == KWIT_N ? "" : "（SCLK/MOSI 仍归 SPI 控制器，刻意未读）",
             highs ? "至少一根读高 = 那一轨不是 0V，BUSY 的低更像面板在驱动（旁证，未实测）"
                   : "读到的脚全被拉低 = 更像 0V 轨经各脚 ESD 二极管吃掉上拉 ⇒ 不定案、不升级、不驱动任何脚");
    if (highs) return true;
    return veto_reached("witness highs=0");
}

/* 一次点屏尝试的**本体**：只在 epd_panel_probe() 里认领到 s_probing 之后调用。 */
static bool probe_attempt(void)
{
    if (s_ready) return true;
    /* 轮次计在早退**之后**：`s_probes`（axp_panel_power.c）只在 `axp_enable_panel_rail()` 里 +1，
     * 而那个调用点在下面，屏一亮起来两边就一起冻结、永远同步。R28 曾把这行提到早退之前，
     * 理由是"旧写法永久错开一格"——那是错的（旧写法两边同进同退），实际效果相反：屏亮期间
     * 每轮只加 epd 侧的号，两号错位 D 后，D≡6 (mod 12) 时 2.24s 的全量扫描会和 1.85s 的判活
     * 撞进同一次持锁（`%60==30` 那个偏移就是为了避开它而选的），并且两条 `probe#` 日志对不上。 */
    s_probe_round++;
    /* 先问电源再碰引脚：向 0V 面板驱动 RST/CS/SCLK/MOSI 会经面板内部的 ESD 二极管
     * 倒灌，所以把 AXP 判定放在 epd_bus_setup() 之前。 */
    axp_enable_panel_rail();
    const bool rail_off = axp_panel_off();
    const bool sys_off = rail_off && axp_system_off();
    /* 电轨判据只决定"非放行轮要不要先歇着"，**不**决定"要不要先做被动预检"（R27 复查 P0-2）：
     * `rail_off==false` 的全部含义是"0x34 会应答 + 那一位写得进且回读一致"——它既没证明那一位
     * 就是 ALDO3（§十六-7 的 P1-6 至今未修），也没证明 EPD_VCC 真的从 Q2/SI2301 那级负载开关
     * 出得来。R28 之前只有 rail_off 那条分支有预检，等于"越像是确认有电的那条路，越不设防地
     * 每轮直接驱动 5 根脚"，比被严加看守的 12 轮一次宽得多。
     * 预检对真有电的空闲面板零代价：空闲时 BUSY 本来就是低，而下面 epd_panel_init 要的同一段
     * 低（外加 SWRESET 那个高沿）——预检挡掉的轮，init 自己也会失败。 */
    if (rail_off && (s_probe_round % PANEL_PROBES_PER_LIVENESS) != 0) {
        /* 屏电没到手时复位/SWRESET 全是空操作，BUSY 不会有任何跳变，
         * 不必每轮都去做那 1.85s 的判活采样（那只会白等，并把噪声当答案）。 */
        ESP_LOGW(TAG, "panel rail not confirmed (AXP unreachable or ALDO3 off): 接电池 + 按住电源键 2 秒后松开（没反应再按满 4 秒）；再看 axp 行的 ACK/NACK/TMO 定案%s",
                 sys_off ? " | PWR_OUT 读成被外部拉低，暂按【系统轨未开】待着（该判据未实测，见放行轮的 passive BUSY 行）" : "");
        return false;
    }
    if (!epd_busy_passive_low(rail_off)) return false;
    /* sys_off 拦的是"要不要主动驱动引脚"这一步（R27 复查 P0-3）：被动采样只把 GPIO3 配成输入
     * + 上拉、不驱动任何一根脚，是整套里最便宜的实证，而 PWR_OUT 那条判据自己也没实测过
     * （GPIO1 与 XTAL_32K_P 复用、脚号只来自 demo 写法）。让它连"看一眼 BUSY"都执行不了，
     * 等于用未证实的推断去屏蔽唯一能证伪它的证据。 */
    /* 注意这里必须带 `!`：veto_reached 返回 true = "已经挡了 3 次，别再拦"，
     * 那时才继续往下升级；没到阈值（false）才拦下本轮。写反就变成"第 3 次否决恰好
     * 把唯一的自救机会也否决掉"，又是一次自己造出来的永久锁。 */
    if (sys_off && !veto_reached("PWR_OUT=【系统轨未开】")) return false;
    s_passive_veto = 0;
    if (rail_off)
        ESP_LOGW(TAG, "probe #%u: rail still unconfirmed but BUSY is driven → 电轨闸门可能猜错，升级为主动判活",
                 (unsigned)s_probe_round);
    if (!epd_bus_setup()) return false;
    if (!epd_panel_init()) return false;
    if (!s_bus_ok || s_cmd_dropped) {
        /* "这一轮的命令流不完整"，两个检查点：
         * ①`s_bus_ok`：本轮 setup 失败时上面 `if (!epd_bus_setup()) return false;` 已经先挡掉了，
         *   所以自 R30 的原子认领起，"做到一半被兜底释放拆走"这条路径理论上到不了这里。留着它
         *   是防线不是装饰：一旦这行日志里 `s_bus_ok=0`，说明有人新增了绕过认领就动引脚/总线的
         *   路径，这个报警器比任何注释都先响。
         * ②`s_cmd_dropped`：SWRESET 之后那串寄存器写里有任一笔 `spi_write` 失败（含 `s_spi`
         *   被交还成 NULL 后 IDF 回 INVALID_ARG —— 5.1.6 不会崩，只是静默失败，见
         *   epd_pins_release_if_unverified 上方那段）。
         * 两种都不许把结论记成"面板活着"：命令流残缺的面板可能把后面整段忽略掉。交给监视任务重来。
         * （R29 之前这里还写着第三种"兜底释放与点屏撞上"：那种情形自 R30 起由 `s_probing` 的
         *   原子认领挡在门外，谁抢不到谁放弃本轮，不再是"撞上了靠这里兜"。） */
        ESP_LOGW(TAG, "probe discarded (s_bus_ok=%d s_cmd_dropped=%d): 本轮命令流不完整，结论作废，下一轮重来",
                 (int)s_bus_ok, (int)s_cmd_dropped);
        return false;
    }
    s_ready = true;
    ESP_LOGI(TAG, "epd init done (SCLK%d MOSI%d CS%d DC%d RST%d BUSY%d)",
             EPD_SCLK_PIN, EPD_MOSI_PIN, EPD_CS_PIN, EPD_DC_PIN, EPD_RST_PIN, EPD_BUSY_PIN);
    return true;
}

bool epd_panel_probe(void)
{
    /* 认领失败 = 无锁兜底方正在交还引脚（它先换到位、拆完再放开）。这一轮直接让开，
     * 由监视任务 5s 后重来。这里不会自锁：那一方只有两种收尾——抢到就 `store(false)`，
     * 没抢到就原样返回（它对令牌的那次写 true 写在**持有者仍然持有**期间，所以持有者放开后
     * 令牌回到 false；R31 给它加的那段"抢不到就轮询等"同理（上限 `RELEASE_CLAIM_WAIT_MS`），
     * 逐步推导见 `epd_pins_release_if_unverified`）。 */
    if (atomic_exchange(&s_probing, true)) {
        ESP_LOGW(TAG, "probe skipped: 无锁兜底正在交还引脚 → 本轮让开（下一轮重来）");
        return false;
    }
    const bool ok = probe_attempt();
    atomic_store(&s_probing, false);
    return ok;
}

bool epd_ready(void) { return s_ready; }

/* 已经做过多少次"点屏尝试"。上层汇总日志必须引用它，才能和驱动侧的 `probe #N` 对上——
 * 监视任务自己那个 i 从 1 起，而 eink_init 已经先消耗过轮号，两套号数永远错着。 */
unsigned epd_probe_round(void) { return s_probe_round; }

bool epd_init(void) { return epd_panel_probe(); }

void epd_display_full(const uint8_t *fb)
{
    if (!s_ready) return;
    /* 每次全刷前重新初始化面板。init 失败说明面板已经不再应答（中途掉电/被关机），
     * 必须立即返回：否则后面的 BUSY 等待会让调用方（main 循环、httpd 配网任务）
     * 每次刷新都白等 8s。 */
    if (!epd_panel_init()) {
        ESP_LOGW(TAG, "panel init failed before full update: give up this refresh");
        s_ready = false;
        return;
    }

    epd_cmd(0x24);  /* new frame */
    epd_data_buf(fb, EPD_FB_SIZE);
    epd_cmd(0x26);  /* old/base frame：局刷对比基准与当前帧同步 */
    epd_data_buf(fb, EPD_FB_SIZE);

    if (s_cmd_dropped) {
        /* 有一笔没出去 = 0x24 或 0x26 里已经有一张是错位/残缺的。这时候再发 0x22=0xF7
         * 就等于"把坏帧锁进基准平面"，之后每一次局刷都在错基准上做差分（R27 复查 P1-4
         * 说的那条后果）。宁可这一屏不刷、下线重来：下一轮 probe + 全刷会把两张平面一起重写。 */
        ESP_LOGE(TAG, "full update aborted: 有 SPI 写失败（笔数见上面 spi write failed 行），坏帧不写进基准平面（本轮不刷、下线重来）");
        s_ready = false;
        return;
    }

    epd_cmd(0x22); epd_data(0xF7);  /* full update */
    epd_cmd(0x20);
    if (!epd_wait_busy()) {
        ESP_LOGE(TAG, "full update timed out");
        s_ready = false;   /* 交给监视任务重新判活，避免每帧都卡 8s */
    }
}

bool epd_display_partial(const uint8_t *fb, int x0, int y0, int x1, int y1)
{
    if (!s_ready) return false;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > EPD_WIDTH) x1 = EPD_WIDTH;
    if (y1 > EPD_HEIGHT) y1 = EPD_HEIGHT;
    if (x1 <= x0 || y1 <= y0) return true;
    int b0 = x0 / 8;
    int b1 = (x1 + 7) / 8;   /* 独占上界，按字节对齐 */

    /* 本函数自己发的那串命令要单独记账：局刷**不**走 epd_panel_init()（见下面那段"刻意不复位"），
     * 所以没人替它清 `s_cmd_dropped`——不清就会拿上一轮遗留的位置判断这一轮，要么误杀要么漏判。
     * 同时先确认焊盘还归 SPI：`s_bus_ok` 为假说明中途有人交还过引脚（epd_sleep 那条路径），
     * 这时候再写就是把命令流打在没人持有的引脚上。 */
    s_cmd_dropped = false;
    if (!s_bus_ok) {
        s_ready = false;
        ESP_LOGE(TAG, "partial aborted: 引脚已交还（s_bus_ok=false），本轮不写任何命令");
        return false;
    }

    /* 这里刻意不做硬复位（官方 Display_Partial 里那句 EPD_Reset 不照抄）：
     * 复位会把 0x01(栅极扫描)/0x11(数据入射方向)/0x0C(DC-DC) 打回上电默认值，
     * 而官方局刷又不补发它们——本驱动的 epd_write_fb_rows 是按全刷 init 设的
     * "Y 递增 + 行序"推数据的，寄存器一变默认值就成了"刷新成功但行序错位/花屏"。
     *
     * 补发这三条而不是照抄官方：断电重启后面板仍会正常应答 BUSY，"超时→清
     * s_ready→全刷自愈"这条链在局刷里**不成立**（掉电的是面板，不是它在装死）。
     * 补发后行序至少跟着 init 的设定走；真正无法在这里补救的是 0x26 基准平面
     * 随断电丢失——那一次局刷会花，由上层 FULL_EVERY_N_PARTIAL 周期性全刷兜住。 */
    epd_cmd(0x0C); epd_data(0xAE); epd_data(0xC7); epd_data(0xC3); epd_data(0xC0); epd_data(0x80);
    epd_cmd(0x01); epd_data((EPD_HEIGHT - 1) % 256); epd_data((EPD_HEIGHT - 1) / 256); epd_data(0x02);
    epd_cmd(0x11); epd_data(0x01);

    epd_cmd(0x18); epd_data(0x80);
    epd_cmd(0x3C); epd_data(0x80);  /* partial border waveform */

    epd_set_window(b0 * 8, y0, b1 * 8 - 1, y1 - 1);
    epd_cmd(0x24);
    epd_write_fb_rows(fb, b0, b1, y0, y1);

    /* 局刷只写 0x24（新帧），绝不重写 0x26。0x22=0xFF 是 DIFF 模式：靠 0x24 vs
     * 0x26（旧/基准帧）逐像素差决定翻转哪些点。若把同一帧同时塞进 0x24 和 0x26，
     * 两平面相等→DIFF=零变化→局刷恒为"看着刷新了其实啥也没变"。基准帧由全刷建立。 */
    if (!s_bus_ok || s_cmd_dropped) {
        /* 发 0x20 之前最后一道闸：这一轮的 0x24 可能只进去半截，DIFF 模式会拿半截帧和
         * 基准平面做差 → 屏幕上出现谁也没画的条纹，而且下一次局刷还在错数据上做差。
         * 下线重来（清 s_ready → 全刷重建两张平面）比刷一张错帧便宜。 */
        s_ready = false;
        ESP_LOGE(TAG, "partial aborted: 本轮命令流不完整（s_bus_ok=%d s_cmd_dropped=%d，笔数见上面 spi write failed 行）",
                 (int)s_bus_ok, (int)s_cmd_dropped);
        return false;
    }
    epd_cmd(0x22); epd_data(0xFF);  /* mode-2 partial update */
    epd_cmd(0x20);
    if (!epd_wait_busy()) {
        s_ready = false;   /* 同上：局刷超时说明面板已不应答，别每帧再卡 8s */
        return false;
    }
    return true;
}

/* 把通向面板的 5 根驱动脚（RST/DC/CS/SCLK/MOSI）连同 SPI 总线一起交还给"`GPIO_MODE_DISABLE` +
 * 内部上拉"（R33 P2-5 改的口径：`gpio_reset_pin` 并不把脚配成输入，见函数体内那段）：
 * 不再主动放高也不再主动放低，但**不是断开**（`gpio_reset_pin` 留 45K 上拉到 3V3，见函数体内
 * 那段）。用在哪：从没被证实活着的面板，其电轨可能就是 0V——继续驱动这些脚会经
 * 面板内部的 ESD 二极管向 0V 的 EPD_VCC 倒灌（和 epd_panel_probe 里"先问电源再碰引脚"是
 * 同一条约束）。BUSY(GPIO3) 不在此列：它是 `gpio_config` 显式配的输入 + 内部上拉，不参与驱动。但别把它读成
 * "BUSY 那条没有倒灌路径"——上拉朝 3V3、经 BUSY 脚自己的 ESD 二极管进 0V 轨正是 §十六-2
 * 那条"低电平不等于有电"的机制本身，量级同样约 73uA。这里不拆它，是因为**判活全靠读它**，
 * 拆了就没证据了；它和上面 5 根的区别只是"没人要求它输出电平"，不是"它不漏电"。 */
static void epd_pins_release(void)
{
    /* SCLK/MOSI 挂在 SPI 控制器的 GPIO 矩阵输出上，`gpio_config` 那三根 GPIO 管不到它们，
     * 所以必须先拆设备/总线，再复位焊盘（R26 只归前三根 = 同一约束的半截防护）。
     * `s_bus_ok` 必须跟着清：不清就成了"我把脚交还了，但下一轮 probe 见 s_bus_ok=true
     * 直接短路返回、永远不会把它们配回输出"——释放一次，本上电周期内屏就再也点不亮了
     * （R27 复查抓到的自锁，见排查记录 §十六）。 */
    bool spi_down = true;
    /* 初值分两档写死，不能让"句柄还在、只是没拆掉"读到"无句柄"这句话（R32-P1，R32 复查第 3 条）：
     * 旧初值 `SPI 无句柄，未拆设备` 会被下面 `!spi_down` 那条日志原样打出来，而能走到那一档的
     * 前提恰恰是 `s_spi != NULL` 且 `spi_bus_remove_device` 回了错 —— 有句柄，只是拆不掉。
     * 现场按这条日志决定"要不要再去 probe"，把它读成"本来就没东西要拆"就正好读反了。
     * 只在 `remove` 成功时才会落到 `spi_bus_free` 分支并被那里覆盖。 */
    const char *bus_s = "SPI 句柄仍在，本轮未释放总线（remove 没成功）";
    if (s_spi == NULL) bus_s = "本轮无 SPI 句柄（上一轮已拆掉或从未建）";
    if (s_spi) {
        const esp_err_t re = spi_bus_remove_device(s_spi);
        if (re == ESP_OK) {
            s_spi = NULL;                      /* 只有真拆掉了才置空；先置空再看返回值会漏设备 */
        } else {
            spi_down = false;                  /* 句柄还挂在总线上：总线拆不掉，焊盘也不能复位 */
            ESP_LOGW(TAG, "spi_bus_remove_device: %s → 保留句柄，SCLK/MOSI 本轮不复位", esp_err_to_name(re));
        }
    }
    if (spi_down) {
        /* 5.1.6 实读，且**结论比 R30 那条更严**（R31 复查 P2-2 推翻了我原先写在注释和排查记录里的
         * "`spi_bus_free` 不数设备"）：`spi_bus_free` 本体在 `components/driver/spi/gpspi/spi_common.c:875`
         * （我旧注释写的是 `spi_master.c:300`，那是**另一个函数**，`spi_master_deinit_driver` 的函数头
         * 在 `gpspi/spi_master.c:287`）。
         * 它自己确实只看 `bus_ctx[host]==NULL`（:877），但接着调 `ctx->destroy_func`（:885-887），而 SPI 主机驱动
         * 在 `gpspi/spi_master.c:270` 注册的正是 `spi_master_deinit_driver`，后者 :297 逐槽
         * `SPI_CHECK(host->device[x]==NULL, "not all CSses freed", ESP_ERR_INVALID_STATE)`
         * ⇒ **它还真的数设备**，且它的返回值就是 `spi_bus_free` 的返回值（:905 `return err;`）。
         * 更要注意：那条失败路径上 `spi_bus_free` 照样把 `bus_ctx` free 掉并置 NULL（:903-904），
         * 却不会 free 主机驱动自己的 `bus_driver_ctx` —— 也就是"半个拆干净"的状态。我们今天走不到它
         * （只有 `spi_bus_remove_device` 回了 `ESP_OK` 才让 `spi_down=true`，且全工程只 add 一个设备），
         * 但 `INVALID_STATE` 因此有**两种**来源，日志不许只挑一种说。 */
        const esp_err_t fe = spi_bus_free(SPI3_HOST);
        if (fe == ESP_OK) bus_s = "SPI 总线已释放";
        else if (fe == ESP_ERR_INVALID_STATE) bus_s = "spi_bus_free 回 INVALID_STATE：总线本就未安装，或还有设备没拆（两种同码，见上方注释）";
        else {
            bus_s = "SPI 总线释放失败";
            ESP_LOGW(TAG, "spi_bus_free: %s → SCLK/MOSI 可能仍被 SPI 占着", esp_err_to_name(fe));
        }
    }

    static const int kPanelPins[] = { EPD_RST_PIN, EPD_DC_PIN, EPD_CS_PIN, EPD_SCLK_PIN, EPD_MOSI_PIN };
    int failed = 0;
    for (size_t i = 0; i < sizeof(kPanelPins) / sizeof(kPanelPins[0]); i++) {
        if (!spi_down && (kPanelPins[i] == EPD_SCLK_PIN || kPanelPins[i] == EPD_MOSI_PIN))
            continue;   /* 控制器还在驱动这两根，复位成输入只会让"交还"这句话变成假的 */
        if (gpio_reset_pin(kPanelPins[i]) != ESP_OK) failed++;
    }
    s_bus_ok = false;     /* 下一轮 epd_bus_setup() 会重建：设备拆成就重新 add，没拆成就复用句柄 */
    /* 别把这里读成"引脚断开了"：`gpio_reset_pin()`（5.1.6 `gpio/gpio.c:434-447`）内部就是
     * 一份 `gpio_config_t{ .mode = GPIO_MODE_DISABLE, .pull_up_en = true }`（`:439`/`:441`）再交给
     * `gpio_config()`，留下的状态是 **`GPIO_MODE_DISABLE` + 内部上拉到 3V3**，
     * **不是"输入 + 上拉"**：`gpio_config()` 只在 mode 含 `GPIO_MODE_DEF_INPUT` 时才开输入缓冲
     * （同一份 `gpio.c:371-373`，else 分支 `gpio_input_disable()`）⇒ DISABLE 之后
     * `gpio_get_level()` 读的是关掉的输入缓冲，**不保证能读出面板拉不拉低**（会恒读 0）。
     * 所以本文件里所有"读脚"的地方都自己 `gpio_config` 成 `GPIO_MODE_INPUT`
     * （旁证读和 BUSY 采样都在 `epd_busy_passive_low()` 里，另一处 BUSY 输入在 `epd_bus_setup()`），
     * 没有一个靠 `gpio_reset_pin` 的残留态去读。
     * 上面那个 `failed` 计数在 5.1.6 永远不会响，理由不是"`gpio_config` 只 assert 引脚合法、
     * 固定 `return ESP_OK`"（那是错的：`gpio.c:347-351`、`:353-357` 两处会回
     * `ESP_ERR_INVALID_ARG`），而是 **`gpio_reset_pin` 把 `gpio_config` 的返回值丢掉、
     * 自己无条件 `return ESP_OK`（`:445-446`）**。留着当语义变化的报警器。
     * 也就是说它停止主动驱动（不再 output 高电平），但每根脚仍会经自己的 ESD 二极管向 0V 轨
     * 漏 (3.3-0.7)/45K ≈ 58uA（算上不计二极管压降的上界是 3.3/45K ≈ 73uA —— 本文件另有几处按
     * 73uA 口径写，两者是**同一路电流的下界与上界**，都没测过，别当成两个数在打架）。
     * 方向正确（比钉着驱动小两个数量级），但"交还"≠"断开"，
     * 日志与注释都不许再说成高阻。 */
    if (failed)
        ESP_LOGW(TAG, "panel pins release: %d 根脚 gpio_reset_pin 失败，可能仍在驱动 (%s)", failed, bus_s);
    else if (!spi_down)
        ESP_LOGW(TAG, "panel pins partly released (RST/DC/CS → DISABLE+内部上拉; SCLK/MOSI 仍归 SPI 控制器), %s", bus_s);
    else
        ESP_LOGI(TAG, "panel pins released to DISABLE+pull-up(输入缓冲关，别拿 gpio_get_level 读), 不再驱动 (RST/DC/CS/SCLK/MOSI), %s; 下一轮 probe 会整套重建", bus_s);
}

/* 拿不到显示锁时的兜底：只在"引脚配过、但没有面板在应答的证据"这一档把 5 根脚连同 SPI 交还。
 * 为什么这一档可以绕过锁：epd_display_full/partial 都在 `!s_ready` 时直接返回，
 * 所以 s_ready=false 意味着**不可能有在途刷屏**。判活那一段则靠下面的 `s_probing` 认领挡掉
 * ——它**不是**"撞上了也无所谓"：拆一个正在用的 handle 是 use-after-free，见函数体内那段。
 * 而 s_bus_ok=true 说明有人（就是本驱动）把这些脚配成了输出——若面板没电，
 * 它们会带着高电平进几小时的深睡，那正是 epd_pins_release 要堵的倒灌态。 */
void epd_pins_release_if_unverified(void)
{
    /* 认领不到 = 持锁方正走一次点屏尝试。为什么这一条必须是原子认领（R30 复查 P0-2）：
     * 旧写法 `if (s_probing) return;` 只是"读"，读完到真的把 s_spi 拆掉之间还有一次完整窗口，
     * 对侧可以正好开始一轮并发起 SPI 事务；本方紧接着的 `spi_bus_remove_device()` 会走到
     * `free(handle)`（本机 5.1.6 `components/driver/spi/gpspi/spi_master.c:495` 起那个函数，
     * 它自己的注释就写着 "These checks aren't exhaustive; another thread could sneak in a
     * transaction inbetween"，末尾 `free(handle)` 在 :523）⇒ 对侧那次在途轮询事务用的就是
     * 已释放内存。**这一档才是真正会崩的**；而"s_spi 已经被置成 NULL、事务再发出去"那一档
     * 不崩：`spi_device_polling_transmit`(:1118) 在 :1121 调 `spi_device_polling_start`（函数头 :1041），
     * 后者 :1045 调 `check_trans_valid`，第一件事就是 :767 的
     * `SPI_CHECK(handle!=NULL, "invalid dev handle", ESP_ERR_INVALID_ARG)`（SPI_CHECK =
     * ESP_RETURN_ON_FALSE_ISR，不受任何 CONFIG 开关裁剪）。R29 把这两档混成一句"只是状态被打乱"，
     * 说轻了。
     * 刷新路径（epd_display_full/partial）不在本标记的覆盖范围内，但它俩全程 `s_ready==true`，
     * 下面那道 `!s_ready` 已经把这种时刻排除了。
     * R31 复查 P1-3：**抢不到要等，不能直接放弃**。本函数是 `eink_sleep()` 拿不到显示锁那条
     * 分支上**唯一**一次交还机会，调用方紧接着就 `esp_deep_sleep_start()`；而对面那一次认领覆盖
     * 整轮 probe（最坏 ≈3.53s，逐段推导在 `RELEASE_CLAIM_WAIT_MS` 上方。R39 P1-4 之前这里写的是
     * ≈5.9s（R32 5.0s → R33 5.5s → R38 5.9s），那是把"全诊断轮"和"判活放行轮"两段**互斥**的
     * 耗时加在了一起：全诊断轮的轮号 ≡30 (mod 60)、放行判活要 ≡0 (mod 12)，两者永不同轮。
     * R39 改完互斥相加后这里是 3.25s；R40 在这一格里改了三次：3.3s（那 0.05s 的被动判活被记到了
     * 走不到的那一支、又从走得到的那一支漏掉，两支各错一次、方向相反）→ 3.55s（放行轮只按"AXP
     * 不应答"那个子案算，漏了"应答但回读没确认"那个带 0.27s 写/稳压/回读 的子案，分项见上面那段
     * （R41：这一格旧版印 0.26s，那是照 B1 的旧数 0.47 减出来的；B1 按它自己的分项和是 0.46 ⇒ 0.73−0.46）
     * → **3.53s**（3.55 比它自己的推导大 0.02s，那 0.02s 没有来源，见上面【R40 三修】）。
     * 数值只是"要不要等"的依据，改小它不改变结论，但 14s 的余量是从这个数推出来的，
     * 留着虚高值等于给下一次"再加一轮"留了个放大器），恰好是把
     * CS/DC/RST 配成输出并驱动的那一段。旧写法在这里印一句"等它结束"就 return，而**没有任何人会等**
     * （下一次机会是监视任务 5s 之后，那时板子已经在睡了）⇒ 倒灌防护在最坏的那一窗被静默跳过。
     *
     * R32 复查第 4 条建议的是另一种顺序："先判 `s_bus_ok && !s_ready` 这个 no-op，再认领"，
     * 免得"压根没东西要交还"的轮次白等（它看到的是 R31 的 6s 上限；R32 按推导改成 10s、R33 又因
     * `EPD_PRE_RESETTLE_WAIT_MS` 那一档改成 12s、R38 把位碰段补进预算后再改成 14s，但"要不要先判再认领"这个问题与上限是多少无关）。**这条不采纳，理由要留在这里**：
     * 抢不到令牌本身就是"有一轮点屏尝试正在进行"的确证——全工程只有 `epd_panel_probe()` 和本函数
     * 会把它换成 true，所以等到的那一轮**结束时的状态才是我们要判的状态**。本轮开始时
     * `s_bus_ok` 还是 false（上一轮已交还、这一轮刚进到 `epd_bus_setup()`）恰恰是最需要等的情形：
     * 提前 return 就是把"持锁方即将驱动 5 根脚"这件事留在身后，而那正是本函数存在的唯一理由。
     * 也就是说这里不是"先判贵的还是先判便宜的"，是**判早了就读不到要判的那个状态**。
     * 这份报告里另有两条落在同一个函数上，一并落地。**第 5 条**：`waited_ms += 100` 是计数不是
     * 计时——本任务优先级低于配网/HTTP 时每次 `vTaskDelay` 都可能晚醒，打出来的"等了 Nms"是假的
     * ⇒ 改成按 tick 差算，并把"到底轮询过没有"（`polls`）单独打出来。
     * **第 7 条**：条件不成立那条出口**一条日志都不打**，而 `eink_display.c` 的
     * `eink_sleep()` 那句（R39 核过其现原话）"eink_sleep: 显示锁 20s 拿不到，跳过面板归位；
     * 引脚是否交还、按哪个条件交的，看上一行驱动侧的 release 日志"会把读者指到一条不相干的
     * 日志上 ⇒ 下面补一行 LOGI。
     * （R32 当时写下的理由是"防那句'已按需把 5 根面板脚 + SPI 交还'说谎"。那句话后来在上游被
     * 改写成了上面这种疑问式措辞、不再断言已交还，所以**说谎这个前提已经不存在**；这一行 LOGI
     * 仍然留着，但理由换成"让本函数三条出口（抢到并交还 / 抢到但 no-op / 没抢到）都有回执"，
     * 否则第二条出口在日志里是空白的，而它恰恰是"引脚到底谁在管"最容易被问的那一条。） */
    const uint32_t t0 = xTaskGetTickCount();
    bool claimed = !atomic_exchange(&s_probing, true);
    int polls = 0;                       /* 真的轮询过没有：只有 >0 时"等了 Nms"这句话才成立 */
    while (!claimed) {
        vTaskDelay(pdMS_TO_TICKS(100));
        claimed = !atomic_exchange(&s_probing, true);
        polls++;
        /* 用 tick **差**（和 `epd_wait_busy_ms` 同一口径）而不是把每轮的 100ms 累加：
         * 差值形式天然抗 32 位 tick 回绕，而累加出来的那个数只是"名义延时"，
         * 本任务被更高优先级的活挤后时会比真实墙钟小，日志里的 Nms 就成了假的。 */
        if ((uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS >= RELEASE_CLAIM_WAIT_MS) break;
    }
    const int waited_ms = (int)((uint32_t)(xTaskGetTickCount() - t0) * portTICK_PERIOD_MS);
    if (!claimed) {
        ESP_LOGW(TAG, "release skipped: 持锁方正走一次点屏尝试，等了 %dms（%d 次轮询）仍未交回认领令牌"
                      " → 引脚留在当前状态进深睡（本轮倒灌防护未生效）", waited_ms, polls);
        return;
    }
    if (polls) ESP_LOGW(TAG, "release: 等了 %dms（%d 次轮询）才拿到认领令牌（持锁方已结束一轮 probe）",
                       waited_ms, polls);
    /* 这一行是**锁外**读两个普通 bool（拿不到显示锁才走到这里），R33 复查 P2-7 要我说清它凭什么够用：
     * 要出事故必须是"这里读到 `s_ready==false`，而对侧此刻还在发 SPI 事务"。写侧把 `s_ready`
     * 清成 false 的一共**七处**（`epd_display_full()` 三处、`epd_display_partial()` 三处、`epd_sleep()` 一处），
     * 我逐处对过：每一处都排在**该条路径自己最后一次 SPI 写之后**（init 失败那处是 `epd_panel_init()`
     * 已经返回；超时那两处在 `epd_wait_busy()` 之后；`s_cmd_dropped` 那两处在发 `0x20` 之前、命令流已停；
     * `epd_sleep()` 那处在 `0x10` + 10ms 之后）⇒ "false 已可见 + 还在写"这个组合不存在；`s_ready==true` 时这里根本不进分支（走上面那条
     * 出口日志），也不碰句柄 ⇒ 挡住 use-after-free 的是**这个条件**，不是令牌（todo 第 61 条）。
     * 剩下唯一的形式风险是编译器把这两个全局的读**提升**到那次 `atomic_exchange` 之前——循环体里调过
     * 外部函数 `vTaskDelay`，5.1.6/GCC13 默认优化下我构造不出可达的坏结果；标成 `volatile`（宏定义
     * 上方那条口径注释）之后连这个形式风险也没有了。**代价**：读到的可能是上一轮的旧值，
     * 而那只让本函数多做/少做一轮，不构成新的危险状态。 */
    if (s_bus_ok && !s_ready) {
        epd_pins_release();
    } else {
        /* 拿到令牌却什么都不做，也必须留一行。R39 P1-12 改口径：这句理由原先写的是"防 `eink_sleep()`
         * 那句'已按需把 5 根脚 + SPI 交还'说谎"，而 `eink_display.c` 现在那句已经改成疑问式措辞
         * （`eink_sleep: 显示锁 20s 拿不到，跳过面板归位；引脚是否交还、按哪个条件交的，看上一行驱动侧的
         * release 日志`），不再断言已交还 ⇒ "防它说谎"这个前提没了。这一行仍然要留，理由是**三条出口
         * 都有回执**：抢到并交还（`epd_pins_release()` 自己打）、抢到但 no-op（本行）、没抢到（上面那条
         * `release skipped`）。少了本行，第三条那句"看上一行"就会指到一条不相干的 AXP 日志上。 */
        ESP_LOGI(TAG, "release: 拿到令牌但条件不成立，本轮不交还（s_bus_ok=%d s_ready=%d）："
                      "s_ready=1 = 最近有应答证据，此时拆句柄会撞上在途刷屏（令牌只挡 probe，不挡刷新）",
                 (int)s_bus_ok, (int)s_ready);
    }
    atomic_store(&s_probing, false);
}

void epd_sleep(void)
{
    /* 判据必须是 s_bus_ok 而不是 s_ready：两者会在"probe 成功 → 刷白中途失败"这条路径上
     * 分家（刷白失败会把 s_ready 清掉，但 SPI/GPIO 已经配起来了）。只看 s_ready 的话，
     * 这条命令会打在未配置的焊盘上（gpio_set_level 返回 ESP_ERR_INVALID_STATE，我们吞了），
     * 而 esp_deep_sleep_start() 照样执行 → 引脚留在"上次运行的末尾状态"，休眠电流不定的
     * 隐患就留下了。总线没配过就没有任何引脚可交还，直接返回即可。 */
    if (!s_bus_ok) return;
    if (!s_ready) {
        /* 引脚配过、但**当前没有"面板在应答"的证据**（从没判活成功，或上一次刷新 BUSY 超时
         * 说明面板掉电了）：0x10 不会有人吃，而把 CS/DC 钉高正是对 0V 面板倒灌的那一路。
         * 交还引脚，不发命令。 */
        epd_pins_release();
        ESP_LOGW(TAG, "panel not confirmed alive (never, or lost mid-refresh): pins released to DISABLE+pull-up, no 0x10 sent");
        return;
    }
    epd_cmd(0x10); epd_data(0x01);   /* deep sleep，带参数（官方同款） */
    vTaskDelay(pdMS_TO_TICKS(10));    /* 给它把命令吃进去再拉 RST */
    pin_set(EPD_RST_PIN, 0);
    /* 官方 EPD_Sleep 到这里还留了 cs_0/dc_0（把片选一直按住）。0x10 已经锁进面板、
     * 且 RST 已拉低，接口状态对睡眠本身没影响；这里改回释放，少一路静态漏电。 */
    cs_high();
    pin_set(EPD_DC_PIN, 1);
    s_ready = false;   /* 深度睡眠后寄存器全丢，下次必须先重新判活+初始化 */
    ESP_LOGI(TAG, "panel deep sleep");
}

#endif /* !BOARD_EPAPER_1IN54 —— 本文件整只在 1.54 板上被抹空 */
