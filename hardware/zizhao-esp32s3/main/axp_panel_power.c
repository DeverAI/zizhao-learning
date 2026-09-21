/* AXP2101（I2C 0x34）ALDO3 轨使能，给墨水屏供电。
 * 用 IDF 5.1 自带的 legacy 硬件 I2C（driver/i2c.h）——本板 GPIO41=SDA/42=SCL 直连 AXP，
 * 官方 demo 用的是 5.2 才有的新 i2c_master 驱动（本机 5.1 无），故改用 legacy 等价实现。
 * 引脚/端口对照官方 08__i2c_bsp.h：ESP32_SDA_NUM 41 / ESP32_SCL_NUM 42 / I2C_MASTER_NUM 0。
 * 用完立即 i2c_driver_delete 交还 41/42，避免与 SD SPI 抢引脚。见 axp_panel_power.h。 */
#include "axp_panel_power.h"

#include <stdio.h>
#include "driver/i2c.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "axp";

/* 最近一次探测：PMIC 是否完全不应答。true = 屏电那一路没到手（原因未定案：整机没开机，
 * 或我方 I2C 通路不通——每轮日志里的 ACK/NACK/TMO 计数就是两者的分界，见 axp_scan_known），
 * 上层据此决定还要不要去碰面板。 */
static bool s_axp_off = true;
static bool s_sys_off;        /* PWR_OUT 被外部拉低 = AXP 系统轨铁定没开（硬件动作才能救） */
static unsigned s_probes;   /* 第几次探测：只用来给日志编号 */
/* 本轮的端口 0 驱动是不是我们亲手装上的。只有是，收尾才有资格 delete 并把 41/42 复位成交还
 * 状态；否则那两个焊盘和总线归别人（同一批线上还挂着 ES8311@0x18），碰一下就是拆别人的资源。 */
static bool s_bus_ours;

#define AXP_SDA_PIN   41
#define AXP_SCL_PIN   42
#define AXP_ADDR      0x34
#define AXP_I2C_PORT  I2C_NUM_0

#define AXP_REG_CHIP_ID     0x03   /* 期望 0x4A */
#define AXP_REG_LDO_ONOFF0  0x90   /* bit2 = ALDO3 使能 */
#define AXP_REG_ALDO3_VOL   0x94   /* [4:0] = (mV-500)/100，保留高 3 位 */
#define AXP_CHIP_ID         0x4A
#define ALDO3_BIT           2

/* 两个寄存器函数都把**原话 esp_err_t** 交给调用方，不收成 bool、也不塞进一个全局槽：
 * 收成 bool 就把"失败成什么样"丢了（那是定案要的量），而一个"最近一次 err"的全局槽在
 * 一次调用里会被后面那次事务覆盖（0x90 读失败、0x94 读成功时，日志会报 0x94 的 OK）。
 * 之前那条 esp_err_to_name 只存在于 ESP_LOGD，而本工程 LOG_DEFAULT_LEVEL=LOG_MAXIMUM_LEVEL=3
 * ⇒ LOGD 整个被编译掉，真机上永远看不到，等于返回值从没被记录过。 */
static esp_err_t axp_read_reg(uint8_t reg, uint8_t *out)
{
    return i2c_master_write_read_device(AXP_I2C_PORT, AXP_ADDR, &reg, 1, out, 1,
                                        pdMS_TO_TICKS(50));
}

static esp_err_t axp_write_reg(uint8_t reg, uint8_t val)
{
    const uint8_t buf[2] = { reg, val };
    return i2c_master_write_to_device(AXP_I2C_PORT, AXP_ADDR, buf, sizeof(buf),
                                      pdMS_TO_TICKS(50));
}

/* 装 legacy 硬件 I2C（每次调用都装，收尾由本文件统一 delete），并把"总线归我们"这件事记下来。
 * clk_speed 从 100kHz 降到 20kHz 的依据（R35，来自 R34 位碰那一行的实测）：SCL 在只靠
 * ~45K 内部上拉时上升沿要 5~10µs 才过阈值，100kHz 的半周期只有 5µs ⇒ 主机自己发出的时钟
 * 高电平在采样点上还没到位，从机看到的就是一片不完整的位流，表现正是"全 NACK、零 TIMEOUT"。
 * 20kHz 把这半周期放宽到 25µs（≈5 倍上升时间）。
 * 这一档的实际代价**已在 R37 真机测到**（40s 日志的时间戳差，别再拿"每笔 20ms"当单价）：
 * 一笔 NACK ≈0.18ms ⇒ 5 个邻居 ≈0.9ms、全地址扫 112 个 ≈20ms、0x34 的 5 次重试
 * ≈5×0.18 + 5×20ms 失败间隔（`axp_enable_panel_rail` 里 0x34 那支重试每次失败都 delay）≈101ms。
 * "每笔 20ms"是**超时上限**不是单价：从机在第 9 拍就把地址
 * NACK 掉、事务当场结束，那 20ms 从没跑过（我 R35 这版注释按 0.6ms/笔推出来的 67ms 全扫
 * 因此偏大 3 倍，而更早各版文档里的 2.24s 偏大约 100 倍）。一笔成功的 1 字节读线上
 * 40 位 = 2ms。稳态监视节奏实测 5.151s，全诊断轮实测 ≈5.48~5.54s，都不受这一档影响
 * （R38 的推挽档再往全诊断轮加 ≈0.12s，且一个上电周期只加一次）。
 * 注意这条只是"把嫌疑最大的软件参数改掉"，它**不能**证明 20kHz 够用；够不够由每轮日志的
 * ACK 计数自己说：仍然全 NACK 时，位碰那几行（fast/slow/全扫/角色对调/推挽）才是分界的证据。 */
static bool axp_bus_install(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = AXP_SDA_PIN,
        .scl_io_num = AXP_SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 20000,
    };
    esp_err_t e = i2c_param_config(AXP_I2C_PORT, &conf);
    if (e != ESP_OK) { ESP_LOGE(TAG, "i2c_param_config: %s", esp_err_to_name(e)); return false; }
    e = i2c_driver_install(AXP_I2C_PORT, I2C_MODE_MASTER, 0, 0, 0);
    if (e != ESP_OK) {
        /* 本机 IDF 5.1 的 legacy 驱动在"端口已被别人装上"时返回 **ESP_FAIL**
         * （i2c.c:380-383 那条 else 分支），不是 ESP_ERR_INVALID_STATE —— 也就是说
         * "借用别人的驱动发包"这条路在这版驱动里根本不存在。装不上就整轮放弃：
         * 不去 delete、不去 gpio_reset_pin，那 41/42 这两个焊盘不归我们管。
         * （旧代码把 INVALID_STATE 当成功放行，会让我们在没装上驱动的情况下走到 delete。） */
        ESP_LOGE(TAG, "i2c_driver_install: %s → 端口0可能被别的驱动占用，本轮不碰总线", esp_err_to_name(e));
        return false;
    }
    s_bus_ours = true;
    return true;
}

/* 总线裁决的核心：对每个地址发一次"1 字节读"事务（START+地址W+指针0x00+RESTART+地址R+读1字节+STOP），
 * 把驱动**原话返回码**归类。返回码才是定案用的量，之前只留 bool"应答/不应答"，把 ESP_FAIL 和
 * ESP_ERR_TIMEOUT 混成一件事，而这两件事的责任方完全相反：
 *   ESP_OK          → 该地址有器件 ACK ⇒ 我方 41/42/端口0/驱动 整条通路是好的
 *   ESP_FAIL        → 发得出波形但没人 ACK（NACK，约 1ms 就返回）⇒ 线上没有活的器件应答这一地址
 *   ESP_ERR_TIMEOUT → SDA/SCL 动不了（被钳住 / 缺上拉 / 引脚或端口表错）⇒ 我方通路问题
 *
 * 探针形状为什么不是"长度 0 的写"（旧写法）：I2C 规范上"只发起始+地址+停止"确实合法，但
 * legacy 驱动不区分它——i2c_master_write(len=0) 照样往硬件命令链表塞一个 byte_num=0 的 WRITE
 * 节点（i2c.c:1252-1273 + 1403-1431：fifo_fill=MIN(0,FIFO)=0、byte_num=0 直接写进 CMD_REG），
 * 而 ESP32-S3 的 FSM 遇到 0 字节的 WRITE 没有文档化行为：**可能停在等中断上，把一个本来健康的
 * 总线读成 ESP_ERR_TIMEOUT**。那样"全 TIMEOUT ⇒ 我方通路坏"这条判读就会反过来错判。
 * 换成 1 字节读：地址相位照常要 ACK（这正是我们要的证据），且发出去的每个 WRITE 节点都带 1 字节。
 * 副作用可控：只把器件内部的寄存器指针指到 0x00，不写任何值。
 *
 * 邻居地址表来自官方 i2c_bsp.h:20-24，与 AXP 共用同一条总线：
 * PCF85063 日历=0x51、SHTC3 温湿度=0x70、QMI8658 六轴=0x6A（SA0 接地，官方 demo 默认档）
 * 或 0x6B（SA0 接 VCC）。0x6A/0x6B 两档都扫，因为没有实测能确认这块板把 SA0 接在哪一头。 */
typedef struct { int total, acks, nacks, timeouts, other; } bus_stats_t;

#define BUS_ACK_LIST_MAX 8

static void axp_probe_addrs(const uint8_t *addrs, size_t n, bus_stats_t *st,
                            uint8_t *ack_addrs, size_t ack_cap, size_t *ack_cnt)
{
    const uint8_t ptr = 0x00;   /* 只是"指到寄存器 0"，不写入器件任何寄存器；放在栈上，
                                 * 免得驱动拿到的是 flash 映射地址 */
    uint8_t val = 0;
    st->total = (int)n;
    st->acks = st->nacks = st->timeouts = st->other = 0;
    for (size_t i = 0; i < n; i++) {
        const esp_err_t e = i2c_master_write_read_device(AXP_I2C_PORT, addrs[i], &ptr, 1,
                                                        &val, 1, pdMS_TO_TICKS(20));
        if (e == ESP_OK) {
            st->acks++;
            if (*ack_cnt < ack_cap) ack_addrs[(*ack_cnt)++] = addrs[i];
        } else if (e == ESP_FAIL)          st->nacks++;
        else if (e == ESP_ERR_TIMEOUT)     st->timeouts++;
        else                               st->other++;
    }
}

/* 把"应答了哪些地址"排进一行日志；装不下就截断，绝不越界，并在行尾留 `..` 标明
 * "这只是前 N 个、不是全集"（否则一次 ACK 20 个的全扫会被读成"就这 8 个器件"）。 */
static void bus_ack_list(const uint8_t *addrs, size_t cnt, int total_acks,
                         char *out, size_t out_sz)
{
    if (!out_sz) return;
    out[0] = 0;
    size_t used = 0;
    size_t i = 0;
    for (; i < cnt; i++) {
        const int w = snprintf(out + used, out_sz - used, "0x%02X ", addrs[i]);
        if (w <= 0 || (size_t)w >= out_sz - used) break;
        used += (size_t)w;
    }
    if ((total_acks > (int)cnt || i < cnt) && out_sz > used)    /* 两种"没列全"：①ACK 比列表长；②缓冲装不完（R39 P1-10） */
        snprintf(out + used, out_sz - used, "..");
}

/* 每轮都做的已知地址扫描：只在 5 个地址上试，上限 5×20ms=100ms，典型 ≈0.9ms（R37 实测），
 * 不会拖住监视任务。
 * 统计口径原话返回给调用方，因为"几个 ACK"和"剩下的是 NACK 还是 TIMEOUT"是三件事。
 * 名单里加 0x18(ES8311 音频 codec) 的理由：这一轮的全部产出就是"能不能把责任分开"，
 * 而**任何一个**应答的器件都够了；ES8311 是同一条线上最可能先开口的一个（它的 DVDD 与
 * AXP 那一路轨的关系未在实板核对，所以它 NACK 同样不定案，见 bus_verdict 上方①）。 */
static void axp_scan_known(bus_stats_t *st, char *out, size_t out_sz)
{
    static const uint8_t kPeerAddrs[5] = { 0x18, 0x51, 0x70, 0x6A, 0x6B };
    uint8_t acked[BUS_ACK_LIST_MAX] = {0};
    size_t acked_cnt = 0;
    axp_probe_addrs(kPeerAddrs, sizeof(kPeerAddrs), st, acked, BUS_ACK_LIST_MAX, &acked_cnt);
    bus_ack_list(acked, acked_cnt, st->acks, out, out_sz);
}

/* 全地址扫（0x08-0x77，112 个）：**典型实测只有 ≈20ms**（R37：0.179ms/地址，NACK 在第 9 拍早退）。
 * 但"每笔吃满 20ms 超时"那种坏法（线根本动不了）上限仍是 112×20ms=2.24s，会把 5s 的监视节奏
 * 拖成"每轮先等 2s"，所以节流照旧：只在头 3 轮和每 60 轮做一次，且**刻意错开 30**（见
 * axp_enable_panel_rail 里的 full_diag）：电轨没确认时每隔 12 轮还有一次真实的 BUSY 判活
 * （1.85s，同样在显示锁里），如果全扫正好撞在第 60/120 轮上，那一轮就是"判活 + 全扫 + 上拉对读"
 * 连续持锁（按上限算 ≈5s，按 R37 实测只有 ≈2s），配网门户的刷屏会被它挡掉。
 * "我方通路好还是坏"这个结论每轮都由上面的 5 地址扫描给出，不依赖这里。 */
static void axp_scan_all(bus_stats_t *st, char *out, size_t out_sz)
{
    uint8_t addrs[0x78 - 0x08];
    for (size_t i = 0; i < sizeof(addrs); i++) addrs[i] = (uint8_t)(0x08 + i);
    uint8_t acked[BUS_ACK_LIST_MAX] = {0};
    size_t acked_cnt = 0;
    axp_probe_addrs(addrs, sizeof(addrs), st, acked, BUS_ACK_LIST_MAX, &acked_cnt);
    bus_ack_list(acked, acked_cnt, st->acks, out, out_sz);
}

/* 电轨判定：分别只开内部上拉 / 只开内部下拉（都约 45K）各读一次，两组读数一起看才有意义。
 * 官方 demo 只用 MCU 内部上拉（i2c_bsp.c: flags.enable_internal_pullup），所以"板上有没有
 * 外部上拉"不能从 demo 推——只测下拉一路时"悬空"和"外部上拉那一轨 0V"读出来都是 0，分不清。
 * 三种组合的判读：
 *   pull-up=1 / pull-down=1  → 线上有强于 45K 的外部驱动源。按图纸口径（原理图 AXP 那一路
 *                               有 4.7K 上拉到 VCC3V3，而 VCC3V3 由 PMIC 的 DCDC1 供给、
 *                                MCU 能跑就说明它有电）这一档才是"正常态"。
 *   pull-up=1 / pull-down=0  → 4.7K 那一档没起作用：要么上拉不存在/没贴，要么上拉那一轨 0V，
 *                               要么**这两个焊盘根本不是 SDA/SCL**（引脚表错）——悬空正是"扫到
 *                               的脚不是通信脚"的预期读数。
 *   pull-up=0               → 线被强拉到地（器件把总线钳住了）
 * gpio_config 的返回值必须查：不查就成了"复位焊盘后浮空读一遍"，那种 1 是假信号。 */
static const char *pull_state(int up_only, int dn_only)
{
    if (up_only == 0) return "被外部钳低";
    if (dn_only == 1) return "外部驱动为高";
    return "悬空(只由内部电阻定电平)";
}

static void axp_bus_pull_compare(int *up_sda, int *up_scl, int *dn_sda, int *dn_scl,
                                 esp_err_t *e_up, esp_err_t *e_dn)
{
    gpio_config_t in = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = (1ULL << AXP_SDA_PIN) | (1ULL << AXP_SCL_PIN),
    };
    in.pull_up_en = GPIO_PULLUP_ENABLE;
    in.pull_down_en = GPIO_PULLDOWN_DISABLE;
    *e_up = gpio_config(&in);
    vTaskDelay(pdMS_TO_TICKS(5));
    /* R39 P2-5：配置没成时出参写 -1，不写一个"看起来有效"的 0/1。判决链有调用方的 `cfg_ok`
     * 兜住，但 `pull compare (cfg err=…): pullUP SDA=%d SCL=%d` 那一行会把假读数原样打出来，
     * 而本文件对"没测到"的口径是打 "-"（R29-3 立的，见 `axp_read_pwr_out` 的 -1 哨兵）。 */
    if (*e_up != ESP_OK) { *up_sda = *up_scl = -1; }
    else {
        *up_sda = gpio_get_level(AXP_SDA_PIN);
        *up_scl = gpio_get_level(AXP_SCL_PIN);
    }

    in.pull_up_en = GPIO_PULLUP_DISABLE;
    in.pull_down_en = GPIO_PULLDOWN_ENABLE;
    *e_dn = gpio_config(&in);
    vTaskDelay(pdMS_TO_TICKS(5));
    if (*e_dn != ESP_OK) { *dn_sda = *dn_scl = -1; }
    else {
        *dn_sda = gpio_get_level(AXP_SDA_PIN);
        *dn_scl = gpio_get_level(AXP_SCL_PIN);
    }
    gpio_reset_pin(AXP_SDA_PIN);
    gpio_reset_pin(AXP_SCL_PIN);
}

/* ---- R34：位碰 I2C 探针（不经过任何 I2C 驱动，也不经过硬件 I2C 状态机） ----
 * 为什么必须有这一条：真机 R33 与"逐字拷原厂驱动"的对照工程给出同一现象（0x34/0x18/0x51/0x70/0x6A
 * 全部 ESP_FAIL），而对照工程跑的是我写的 v2→legacy 兼容层 ⇒ "5.1 的 legacy 与 5.2+ 的 v2 硬件驱动
 * 有别"这一条**当时还没被排除**（R34~R37 跑完后已由位碰排除）。位碰把两个硬件状态机都绕开，
 * 只剩 GPIO 矩阵 + 焊盘 + 线 + 器件，
 * 于是第一次能在"没有万用表/示波器"的条件下回答"SCL 焊盘到底有没有翻转"。
 * R34 首版实测（COM14，probe#1~#3 三轮一致）：`SCL rel=1 low=0 | 9clk SCL_high=0/9`。
 * 这两个数放一起才是要紧的东西：**释放 10µs 后读得到高、高相只有 5µs 时一拍都读不到**
 * ⇒ SCL 的上升时间落在 5~10µs 之间 ⇒ 拉它的只有我们那颗 ~45K 内部上拉（外部 4.7K 那一档
 * 与 pull compare 的"SCL=悬空"对上了：没生效），而 45K + 总线电容在这个速度下**边沿不合格**
 * （I2C 100kHz 规范允许的高电平上升时间只有 1µs）。这一条足以单独解释"全 NACK、零 TIMEOUT"，
 * 且不需要假设板子上有任何损伤——所以 R35 把探针改成**同一套动作跑两档速度**，用速度这一维
 * 去判"边沿太慢"还是"真的没人应答"。
 * 各档各能定什么（括号里是 COM14 真机实测，R35~R37 三轮、每轮 probe#1~#3 读数一致）：
 *   ①线的活动性（开漏 + 内部 45K 上拉）：释放后读 1 ⇒ 线起得来，"线动不了"这一档排除；
 *     释放后读 0 而拉低时也是 0 ⇒ 这一路被外部死死拉住（缺上拉不算——45K 拉不动才说明有低阻负载）。
 *     实测：快慢两档、正常与对调两种角色，全是 `SCL rel=1 low=0 | SDA rel=1 low=0`。
 *   ②9 个时钟 + 再读 SDA：规范里的"总线卡死释放"动作。SDA 仍为 0 ⇒ 有器件扣着数据线不放。
 *     采样点在高相**末尾**，所以 `SCL_high` 就是"半周期之内线到底抬到位没有"；反过来它**只**
 *     证明"≤半周期内过了阈值"，不证明过阈值的时刻满足规范的 1µs —— 这一维只能靠 ④判。
 *     实测：快档 0/9、慢档 9/9，两档 `after9=1`（没有人扣着 SDA）。
 *   ③慢档（≈20kHz）与快档（≈100kHz）同做①②和地址相位：慢档拿到 ACK ⇒ 根因是边沿，
 *     硬件那一路把 clk_speed 降下来就能救（R35 已一并降）。
 *     实测：慢档 5 个已知地址仍 ack=0 ⇒ 边沿不是全部，于是再补 ③'。
 *   ③'慢档 0x08-0x77 全地址位碰扫（R36）：实测 `ACK=0 NACK=112`，整段 ≈116ms。一帧有 **34 段**
 *     25µs 延时（R39 逐行数 `bb_addr_ack` 的 `bb_delay` 调用点：8 个时钟位 ×3 段 = 24，加起始那
 *     一对双延时、START/STOP 前后的建立保持共 10 段），= 0.85ms/帧，112 帧 = 95.2ms 是"排定的"，
 *     余下 ≈21ms（≈0.19ms/帧）是 gpio_set_level/gpio_get_level/
 *     esp_rom_delay_us 调用自身的开销，不是线变慢。
 *     （R35~R38 这段原写"26 段 / 0.65ms / 72.8ms / 余 43ms"，来自一个漏算模型：只按"11 个时钟位
 *     的高低两相 + START/STOP 前后"排，少了每位的 SDA 建立段与首尾那两对双延时。结论方向不变
 *     ——余下那部分仍是软件开销而不是线变慢——但比例是 82%/18%，不是原句读起来的 63%/37%。）
 *   ③''把两脚角色对调（SCL=41、SDA=42）再跑一遍①②③③'（R37）：同样 `9/9` + `ACK=0 NACK=112`
 *     ⇒ **"引脚表把 SDA/SCL 写反了"这一条到此实测排除**（原厂 08__i2c_bsp.h 自己也是 41/42，
 *     两条独立来源同一结论）。R36 那时"只剩两种解释"，对调把前者判死后，软件侧就只留下
 *     ④要判的"上升沿质量"这一维。
 *   ④推挽 SCL 全地址扫（R38 新增）：判的是 R34~R37 唯一没被测过的主机侧维度——**上升沿的形状**。
 *     原门条件是"慢档里 SCL 仍抬不起来"，而本板实测 `SCL rel=1`、慢档 9/9 ⇒ 那一档从未跑过，
 *     也就从没排除过任何东西；R38 把门改成"开漏五档都穷尽 + 线上静默 + 时钟路没被外部钉高"，
 *     见下面风险说明。
 * ④为什么单独交代风险：I2C 规范不允许主机把时钟做成推挽——若某个从机正把 SCL 拉低（时钟拉伸），
 * 推挽高就是两个输出级对顶。代价被五层框住：
 *   (a) SDA **永远**开漏：第 9 拍它是输入，不可能对顶；也绝不能改成推挽——那等于把总线上唯一
 *       能"说话"的方向踩掉，测出来的东西不再有意义（41 那一路实测已被外部驱动为高，
 *       对它推挽更是纯对顶、换不到任何新信息）。
 *   (b) 只在正常角色（SCL=42）上做，42 恰是实测"没有外部上拉"的那一路，也就是唯一需要靠
 *       自己把线顶起来的那一路。
 *   (c) SCL 只在"高电平那几拍"是推挽。一帧 34 段延时 = 低相 20 + **高相 14**（`bb_addr_ack` 逐段
 *       数：开头那一对双延时 2 + START 保持 1 + 8 个时钟位各 1 + 第 9 拍 ACK 1 + STOP 前建立 1 +
 *       STOP 本身 1；13 那个数是 R39 第一版漏了 STOP 那拍 `bb_sda(1); bb_delay()`——漏了它，
 *       20+13=33 就和同一轮自己数出的 34 段对不上，是这条算式自己露的馅）。
 *       ⇒ 14 × 25µs = 350µs/帧，112 帧 = **39.2ms**；再加进入本档前 `bb_release_clocks` 那 9 拍高
 *       （225µs）⇒ **只算排定延时 ≈39.4ms**。
 *       【R40：上界不能停在 39.4ms】`bb_addr_ack` **返回时 SCL 是高**（最后一拍是 STOP，函数里
 *       没有再把时钟拉低），下一帧要到开头第 3 段才拉低 ⇒ 帧与帧之间那段调用开销也在推挽顶高
 *       窗口内。这段开销本文件有实测锚点：慢档 112 帧实测 116~117ms、排定 95.2ms ⇒ ≈0.19ms/帧
 *       ⇒ 诚实上界 112 × (0.35+0.19)ms + 0.225ms ≈ **60.7ms**（R40 三修：本行前一版给的是 60.5，
 *       而它自己这个式子算出来是 60.48+0.225=60.7——"公布的数比自己的算式小"，与"大"那一型同族，
 *       见 `epd_driver.c` 里 R40 三修 3.53/3.55 那一条。**推**：0.19ms 是开漏慢档量的，
 *       推挽档自己的调用开销没测过，同量级是假设不是实测）。取 **≤65ms** 作为对外的安全上界。
 *       旧值链条：R38 "≤31ms"（按 11 段，少算 SDA 建立与首尾双延时）→ R39 "≤37ms"（13 段，
 *       漏 STOP 那拍、且把"排定延时"当"上界"）→ R40 "≤65ms"。
 *       这是全文件唯一"主动顶总线"的安全上界，写小就是风险预算写小。
 *   (d) 驱动能力设成最弱一档并把**返回值与回读值一起进日志**（设不成就是"没设成"，不能假称
 *       已限流）；退出时显式复原，因为 gpio_reset_pin 只做"输入+内部上拉"、不恢复 FUN_DRV
 *       （IDF 5.1.6 components/driver/gpio/gpio.c:434-447），legacy i2c 驱动也不碰驱动能力，
 *       不显式复原就是把这个设置永久留给后面每一轮。
 *   (e) 一个上电周期只跑一次（s_pp_done），且它外面还套着 full_diag 轮（头 3 轮 + 每 60 轮
 *       错开 30）与 pads_free 两道门。
 * 能换到什么：④拿到 ACK ⇒ "SCL 那一路上拉缺失/那一轨 0V"从推断变成实测，且点不亮屏的原因
 * 第一次落到一个软件能绕开的点上（但绕行不合规，只当诊断手段，不当修复）。④仍 0 ACK ⇒
 * 主机侧连边沿质量这一维也实测排除，0 应答只能落在器件侧（没通电 / 没出复位 / 不在这张地址表），
 * 那时"改固件能救这块板"这句话就没有立足点，剩下的全是硬件动作。 */
#define BB_FAST_HALF_US 5     /* ≈100kHz：与 legacy 那一路原先的 clk_speed 同档 */
#define BB_SLOW_HALF_US 25    /* ≈20kHz：只有 45K 内部上拉时，唯一还能让 SCL 在半个周期内过阈值的档 */
#define BB_ADDR_MAX 5

static void bb_delay(unsigned half_us) { esp_rom_delay_us(half_us); }

/* 位碰只用"哪根当数据、哪根当时钟"这两个角色，把角色做成参数而不是全局：
 * R36 的结论（20kHz 位碰、时钟波形 9/9 合格、112 个地址无一应答）当时剩两种解释——
 * 焊盘角色反了，或线上没有通电的器件；R37 就是靠这两个实例把前者判死的（见上面 ③''）。
 * 角色对调档现在已交付结论，但实例必须留着：④的门要拿它的 ACK 计数当"开漏五档都穷尽"的证据，
 * 而同一组函数要能把两种角色摆法都跑到，这一点不能退回硬编码引脚。 */
typedef struct { int sda, scl; } bb_pins_t;
static const bb_pins_t kBBNormal = { AXP_SDA_PIN, AXP_SCL_PIN };
static const bb_pins_t kBBSwapped = { AXP_SCL_PIN, AXP_SDA_PIN };

static void bb_sda(const bb_pins_t *p, int lv) { gpio_set_level(p->sda, lv); }
static void bb_scl(const bb_pins_t *p, int lv) { gpio_set_level(p->scl, lv); }
static int  bb_sda_lvl(const bb_pins_t *p) { return gpio_get_level(p->sda); }
static int  bb_scl_lvl(const bb_pins_t *p) { return gpio_get_level(p->scl); }

/* 装成"输入+输出"：必须是 INPUT_OUTPUT*。本机 `gpio_set_direction` 只在 mode 含
 * GPIO_MODE_DEF_INPUT 时才 `gpio_input_enable`（gpio.c:315-319），而 `gpio_get_level` 走
 * `gpio_hal_get_level` 读焊盘寄存器（gpio.c:243-246）⇒ 只有输入通路同时开着，
 * "我推出去的电平在焊盘上到底是不是那个值"这一读才有意义；纯 OUTPUT 读回来的是自己骗自己。
 * 数据脚恒为开漏（第 9 拍要让器件拉低）；时钟脚由调用方决定开漏还是推挽。 */
static esp_err_t bb_setup(const bb_pins_t *p, bool clk_push_pull)
{
    gpio_config_t c = {
        .intr_type = GPIO_INTR_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    c.pin_bit_mask = 1ULL << p->sda;
    c.mode = GPIO_MODE_INPUT_OUTPUT_OD;
    esp_err_t e = gpio_config(&c);
    if (e != ESP_OK) return e;
    c.pin_bit_mask = 1ULL << p->scl;
    c.mode = clk_push_pull ? GPIO_MODE_INPUT_OUTPUT : GPIO_MODE_INPUT_OUTPUT_OD;
    return gpio_config(&c);
}

/* ①：每根线各读两次——"释放（靠内部 45K 上拉）"和"我们主动拉低"。两读之间等的时间就是
 * 本档的半个周期 ×2，所以"释放后读到的值"天然是"过了两个半周期之后线在哪"。 */
static void bb_line_activity(const bb_pins_t *p, unsigned half_us,
                             int *sda_rel, int *sda_low, int *scl_rel, int *scl_low)
{
    bb_sda(p, 1); bb_scl(p, 1); bb_delay(half_us); bb_delay(half_us);
    *scl_rel = bb_scl_lvl(p);
    *sda_rel = bb_sda_lvl(p);
    bb_scl(p, 0); bb_delay(half_us);       /* 先降时钟再改数据，免得凭空造一个 START/STOP */
    bb_sda(p, 0); bb_delay(half_us);
    *scl_low = bb_scl_lvl(p);
    *sda_low = bb_sda_lvl(p);
    bb_sda(p, 1); bb_scl(p, 1); bb_delay(half_us);
}

/* ②：9 个时钟把可能扣着 SDA 的器件放出来。scl_high_beats 是"这 9 拍里 SCL 在**高相末尾**读到高的
 * 次数"——它就是"半周期之内线抬不抬得起来"的直接读数，不依赖任何驱动返回码。 */
static int bb_release_clocks(const bb_pins_t *p, unsigned half_us, int *scl_high_beats)
{
    int highs = 0;
    bb_sda(p, 1);
    for (int i = 0; i < 9; i++) {
        bb_scl(p, 0); bb_delay(half_us);
        bb_scl(p, 1); bb_delay(half_us);   /* 开漏下"1"=释放，靠内部 45K 上拉起高 */
        if (bb_scl_lvl(p)) highs++;
    }
    *scl_high_beats = highs;
    return bb_sda_lvl(p);
}

/* ③/④：一帧地址相位 = START + 8 bit（addr7<<1|1，读向） + 第 9 拍读 ACK + STOP。到地址为止，
 * 不发寄存器指针、不发数据 ⇒ 对器件的副作用比硬件那条"1 字节读"探针还轻（那条会把寄存器指针写到 0x00）。 */
static bool bb_addr_ack(const bb_pins_t *p, unsigned half_us, uint8_t addr7)
{
    const uint8_t b = (uint8_t)((addr7 << 1) | 1u);
    bb_sda(p, 1); bb_scl(p, 1); bb_delay(half_us); bb_delay(half_us);
    bb_sda(p, 0); bb_delay(half_us);       /* START：SCL 高时 SDA 高→低 */
    bb_scl(p, 0); bb_delay(half_us);
    for (int i = 7; i >= 0; i--) {
        bb_sda(p, (b >> i) & 1); bb_delay(half_us);
        bb_scl(p, 1); bb_delay(half_us);
        bb_scl(p, 0); bb_delay(half_us);
    }
    bb_sda(p, 1); bb_delay(half_us);       /* 释放 SDA：第 9 拍器件拉低=ACK，留高=NACK */
    bb_scl(p, 1); bb_delay(half_us);
    const bool ack = (bb_sda_lvl(p) == 0);
    bb_scl(p, 0); bb_delay(half_us);
    bb_sda(p, 0); bb_delay(half_us);       /* 无论 ACK 与否都把这一拍收干净，别让 SDA 停在别人事务中间 */
    bb_scl(p, 1); bb_delay(half_us);
    bb_sda(p, 1); bb_delay(half_us);       /* STOP：SCL 高时 SDA 低→高 */
    return ack;
}

/* 位碰要打的地址：0x34=AXP2101，0x18=ES8311，0x51=PCF85063，0x70=SHTC3，0x6A=QMI8658。
 * 与硬件那一路 axp_scan_known 的名单同源（官方 i2c_bsp.h:20-24），差别是这里没有 0x6B：
 * 位碰这一段只在 full_diag 轮跑，多一档就多 5 帧，而 QMI8658 挂哪一头这件事由硬件扫描负责。 */
static const uint8_t kBBAddrs[BB_ADDR_MAX] = { 0x34, 0x18, 0x51, 0x70, 0x6A };

typedef struct {
    int acks, scl_rel, scl_low, sda_rel, sda_low, scl_high, sda_after9;
} bb_run_t;

/* 一档速度上把①②③跑完，结果打进一行日志并带出判据要用的那几个数。 */
static void bb_run_at(const bb_pins_t *p, unsigned half_us, const char *spd, const char *role,
                      bb_run_t *r)
{
    char acked[BB_ADDR_MAX * 5 + 3] = {0};

    r->acks = 0;
    bb_line_activity(p, half_us, &r->sda_rel, &r->sda_low, &r->scl_rel, &r->scl_low);
    r->sda_after9 = bb_release_clocks(p, half_us, &r->scl_high);
    /* R39 P1-6：探测与拼串分家。以前两件事在同一个循环里、缓冲装不下就 `break`，那会让**剩下的
     * 地址根本不被试**，而 r->acks 是 ④ 那道门（od_exhausted）的直接输入 ⇒ 一次纯粹的日志格式
     * 问题能静默把"开漏已穷尽"判成成立，把本来该挡住的推挽档放进来。今天 5 个地址还装得下，
     * 所以这条不改结论，改的是"以后动 BB_ADDR_MAX 时不会踩"。 */
    for (size_t i = 0; i < BB_ADDR_MAX; i++) {
        if (bb_addr_ack(p, half_us, kBBAddrs[i])) r->acks++;
    }
    bus_ack_list(kBBAddrs, BB_ADDR_MAX, BB_ADDR_MAX, acked, sizeof(acked));
    ESP_LOGW(TAG, "bitbang %s %s (half=%uus, OD+45K): SCL rel=%d low=%d 9clk_high=%d/9 | SDA rel=%d low=%d after9=%d | probed[%s] ack=%d → %s",
             role, spd, (unsigned)half_us, r->scl_rel, r->scl_low, r->scl_high,
             r->sda_rel, r->sda_low, r->sda_after9, acked, r->acks,
             r->acks > 0 ? "位碰拿到 ACK ⇒ GPIO→焊盘→线→器件整条双向通路是好的，硬件 I2C 驱动（5.1 legacy / 5.2+ v2）与点不亮屏无关"
             : (r->scl_rel == 0 ? "SCL 连释放都起不来 ⇒ 责任在线/负载侧，不在驱动"
             : (r->scl_high == 0 ? "SCL 要 >1 个半周期才抬到位 ⇒ 这一档速度边沿不合格，NACK 不能算器件的账"
                                 : "时钟抬得起来、没人应答 ⇒ 与硬件驱动那一路读到的全 NACK 同型（注意：9/9 是在高相末尾采的，只证明 ≤半周期内过了阈值，不证明 ≤1µs ⇒ 边沿质量仍未排除，看 PP-SCL 那一行）")));
}

/* 位碰全地址扫（0x08-0x77，112 帧）：只在慢档跑。为什么 5 个已知地址之外还要再扫一遍——
 * "0x34/0x18/0x51/0x70/0x6A 都不应答"既可能是"线通了、只是这几个地址上没有活的器件"，
 * 也可能是"我们翻转的这两个焊盘根本不是 PMIC 那对 SCL/SDA"。有任何一个地址 ACK 就直接把后者
 * 判死（线通了、器件在应答，只是地址表要改）。
 * 开销：**R36/R37 真机实测整段 116~117ms**（正常角色 t=774→890，对调角色 905→1022），
 * 即每帧 ≈1.04ms。其中按 34 段 25µs 排定的有 0.85ms/帧（112 帧 = 95.2ms），余下 ≈0.19ms/帧
 * 是 `gpio_set_level`/`gpio_get_level`/`esp_rom_delay_us` 调用自身的开销，不是线变慢了
 * （R39 重数：段数是 34 不是原来写的 26，见本文件位碰头注 ③' 那一条）。
 * 只在 full_diag 轮跑；整段 AXP 诊断的实测锚点见本文件 `axp_enable_panel_rail` 里 `full_diag`
 * 上方那条，别再拿"112×20ms=2.24s"当预算。
 * 返回值 = ACK 数，供 ④ 的门条件用。 */
static int bb_scan_all_slow(const bb_pins_t *p, const char *role)
{
    uint8_t ack_addrs[BUS_ACK_LIST_MAX] = {0};
    size_t ack_cnt = 0;
    char acked[BUS_ACK_LIST_MAX * 5 + 3] = {0};
    int acks = 0, nacks = 0;
    for (uint8_t a = 0x08; a <= 0x77; a++) {
        if (bb_addr_ack(p, BB_SLOW_HALF_US, a)) {
            acks++;
            if (ack_cnt < BUS_ACK_LIST_MAX) ack_addrs[ack_cnt++] = a;
        } else {
            nacks++;
        }
    }
    /* R39 P1-10：改调 `bus_ack_list`。自己拼串时第 9 条 ACK 起 `used` 不再前进，后面的 ACK 全写在
     * 同一个偏移上互相覆盖 ⇒ 日志里那串既不是"前 8 个"也不是"后 8 个"，尾巴还挂着半截 `0x`；
     * "112 个地址全 ACK"正是 `bus_ack_list` 头注举的例子，`..` 就是防它被读成"就这 8 个器件"。 */
    bus_ack_list(ack_addrs, ack_cnt, acks, acked, sizeof(acked));
    ESP_LOGW(TAG, "bitbang %s slow full-scan 0x08-0x77: ACK=%d NACK=%d acked:[%s] → %s",
             role, acks, nacks, acked[0] ? acked : "none",
             acks > 0 ? "位碰层面有器件应答 ⇒ 这两个焊盘就是真总线、线是通的，0x34 沉默是器件/地址问题，不是接线问题"
                      : "不经过任何驱动、角色也试过对调的这条路 112 个地址无一应答 ⇒ 驱动 v2/legacy 之争与焊盘角色都已排除；**仍未**排除的是主机侧上升沿质量（45K 内部上拉的 RC 斜坡），那一维由 PP-SCL 那一行判");
    return acks;
}

/* ④推挽 SCL 全地址扫（R38）：把 SCL 由高电平时改成主动顶到轨，边沿不再受上拉电阻限制。
 * 这是主机侧最后一维，也是唯一有对顶风险的一档，所以进不进来由 bb_probe 里那组门条件决定，
 * 而对顶代价本身由这里三层兜住：SDA 恒开漏（bb_setup 里写死）、驱动能力设最弱一档并回读、
 * 每拍只持续 BB_SLOW_HALF_US。拿到第一个 ACK 就把时钟换回开漏，并**立刻用开漏重跑同一个地址**
 * （R39 P0-2：以前循环单调递增，换回开漏后扫的是 a+1..0x77，真正拿到推挽 ACK 的那个地址从来
 * 没在开漏下被试第二次 ⇒ "OD 那一路能不能复现同一个 ACK"这一列**结构上恒为 0**。一个恒为 0 的
 * 出参被打进判决行、还被注释赋予"能不能长期用"的含义，就是把错误结论印在日志上）。
 * 驱动能力必须在退出时显式复原：`gpio_reset_pin` 只做"输入+内部上拉"，不恢复 FUN_DRV
 * （IDF 5.1.6 gpio.c:434-447），legacy i2c 驱动也不碰驱动能力。
 * R39 P1-9 把"读不到原始驱动能力"也升成一道门（【R40 口径】它在**本函数体内**，不在 `bb_probe()`
 * 那条 `pp_skip` 的六道链里，所以别叫它"第 6 道门"——那个编号已经被 P1-5 的 `swapped_ran` 占了，
 * 同一文件里两个"第 6 道门"是数不出来的那种写法）：读不到原值就没法复原，不猜一个值写回去，
 * 这一档直接不跑（把焊盘留在 CAP_0 上会让之后每一轮硬件 I2C 都跑在一个我们没设过的档位上，
 * 那是在给后续取证掺变量）。 */
static void bb_pp_scan_all(const bb_pins_t *p, const char *role)
{
    int pp_acks = 0, pp_nacks = 0, od_acks = 0, od_nacks = 0;
    int high_beats = 0;
    int first_pp_ack = -1;
    int od_same = -1;        /* 1=同一地址开漏下也 ACK，0=只有推挽应答，-1=没测成 */
    bool switched = false;
    gpio_drive_cap_t cap_before = GPIO_DRIVE_CAP_DEFAULT, cap_tmp = GPIO_DRIVE_CAP_DEFAULT;
    int cap_after = -1;      /* R39 P1-8：-1 = 没回读过。以前这里放 GPIO_DRIVE_CAP_DEFAULT(=2)，
                              * 设档失败那一轮会打出"回读=cap2"，给一个从没测过的数贴上"回读"标签。 */

    const esp_err_t cap_get_e = gpio_get_drive_capability(p->scl, &cap_before);
    if (cap_get_e != ESP_OK) {
        ESP_LOGE(TAG, "bitbang %s PP-SCL 跳过：读不到 SCL 原始驱动能力 (%s) ⇒ 设完没法复原，本档不跑 → 主机侧「上升沿质量」这一维仍未实测",
                 role, esp_err_to_name(cap_get_e));
        return;
    }
    const esp_err_t cap_set_e = gpio_set_drive_capability(p->scl, GPIO_DRIVE_CAP_0);
    if (cap_set_e == ESP_OK && gpio_get_drive_capability(p->scl, &cap_tmp) == ESP_OK) cap_after = (int)cap_tmp;
    const esp_err_t e = bb_setup(p, true);
    if (e != ESP_OK) {
        /* 这条出口以前把复原的返回值 `(void)` 丢掉、打完日志就 return ⇒ 走了异常出口的那一轮
         * "驱动能力到底复原没复原"永久无记录（R39 P1-9）。此刻 SCL 还没被配成推挽，遗留的只有档位。 */
        const esp_err_t early_e = gpio_set_drive_capability(p->scl, cap_before);
        ESP_LOGE(TAG, "bitbang %s PP-SCL: GPIO 配置失败 (%s) → 跳过推挽档 | 驱动能力复原=%s",
                 role, esp_err_to_name(e), esp_err_to_name(early_e));
        return;
    }
    (void)bb_release_clocks(p, BB_SLOW_HALF_US, &high_beats);
    for (uint8_t a = 0x08; a <= 0x77; a++) {
        if (!bb_addr_ack(p, BB_SLOW_HALF_US, a)) {
            if (switched) od_nacks++; else pp_nacks++;
            continue;
        }
        if (switched) { od_acks++; continue; }   /* 已换回开漏：后面的 ACK 只统计，不再动配置 */
        pp_acks++;
        first_pp_ack = a;
        if (bb_setup(p, false) != ESP_OK) {
            ESP_LOGE(TAG, "bitbang %s PP-SCL: 换回开漏失败 → 本段提前结束（推挽段已 ACK=%d，同址复现没测成）", role, pp_acks);
            break;
        }
        switched = true;
        od_same = bb_addr_ack(p, BB_SLOW_HALF_US, a) ? 1 : 0;
    }
    /* 无论有没有拿到 ACK，退出前都必须把时钟换回开漏：不换来的话，函数外面那两行"释放 SDA/SCL
     * 再 gpio_reset_pin"是在推挽状态下把线主动顶高 25µs，而调用方随后还要把这两个焊盘交还总线。 */
    if (bb_setup(p, false) != ESP_OK)
        ESP_LOGE(TAG, "bitbang %s PP-SCL: 退出时换回开漏失败 → 收尾的复位动作会替我们兜住，但本轮这一段状态不干净", role);
    const esp_err_t cap_res_e = gpio_set_drive_capability(p->scl, cap_before);
    /* `caprd` 16 字节不是随手给的：`cap%d` 里 `%d` 的最坏输出是 **11** 个字符（负号 + `INT_MIN`
     * 的 10 位），加 "cap" 与 NUL = **15**（R40 补负号：R39 那句"10 位 + NUL = 14"把负号漏了，
     * 结论没错但推导不成立 ⇒ 16 也不是这条理由推出来的最小值，15 就够，多留一格是给格式串的余量）。
     * 给 12 会被 `-Werror=format-truncation` 直接拦下（R39 首次构建就是这么失败的）。
     * `cap_after` 实际只会是 0~3，但编译器不知道，所以按它的静态范围算。 */
    char caprd[16], first_str[12];
    if (cap_after >= 0) snprintf(caprd, sizeof(caprd), "cap%d", cap_after);
    else snprintf(caprd, sizeof(caprd), "未测");
    if (first_pp_ack >= 0) snprintf(first_str, sizeof(first_str), "0x%02X", first_pp_ack);
    else snprintf(first_str, sizeof(first_str), "none");
    ESP_LOGW(TAG, "bitbang %s PP-SCL(原=cap%d→设成=%s 回读=%s 复原=%s, half=%uus, 9clk_high=%d/9): 推挽段 ACK=%d NACK=%d 首ACK=%s | 同址开漏复现=%s | OD 段(该地址之后) ACK=%d NACK=%d → %s",
             role, (int)cap_before,
             cap_set_e == ESP_OK ? "已设最弱档" : esp_err_to_name(cap_set_e), caprd,
             cap_res_e == ESP_OK ? "OK" : esp_err_to_name(cap_res_e),
             (unsigned)BB_SLOW_HALF_US, high_beats, pp_acks, pp_nacks, first_str,
             od_same < 0 ? "没测" : (od_same == 1 ? "ACK" : "NACK"),
             od_acks, od_nacks,
             cap_set_e != ESP_OK ? "驱动能力没设成最弱档（见上），这一段的限流假设不成立，判决照读但代价核算要重算"
             : (pp_acks == 0
                 ? (high_beats < 9
                     ? "推挽档自己都没把 SCL 抬满 9 拍（见前面 9clk_high）⇒ 线上有比最弱驱动档更强的下拉（对顶或钳地）。这一档测不出'上升沿质量'的结论，0 应答也不能记到器件头上"
                     : "把时钟主动推高、边沿不再受上拉限制，112 个地址仍无一应答 ⇒ 主机侧连边沿质量这一维也实测排除；0 应答只剩器件侧解释（没通电 / 没出复位 / 不在这张地址表）")
                 : (od_same == 1
                     ? "推挽拿到 ACK，**同一个地址换回开漏也拿到 ACK** ⇒ 这不是'只有推挽能救'：③' 那几路开漏扫描当时 0 应答必有另一个原因（前面那 9 拍释放时钟把某个从机的时钟拉伸解除了？器件在慢档上需要更多时间？）。这一档只排除到'线是通的'，SCL 上升沿缺失那条**不能**据本轮下定论"
                     : (od_same == 0
                         ? "只有把时钟主动推高才有应答、同一个地址换回开漏就 NACK ⇒ 根因落在 SCL 那一路的上升沿（外部 4.7K 那一档没生效，只剩内部 45K）。引脚表与驱动层无罪。注意：I2C 规范不允许主机推挽 SCL，这是诊断绕行手段、不当修复"
                         : "推挽段拿到 ACK，但换回开漏的 GPIO 配置失败 ⇒ 同址复现没测成，这一档只交付'推挽下有人应答'半条结论，'能不能长期用'仍未测"))));
}

/* 推挽档一个上电周期只付一次对顶风险：它跑在 full_diag 轮里（头 3 轮 + 每 60 轮），
 * 不加这个标志的话头 3 轮就是三次，而每次都是 112 帧主动顶时钟。
 * 标志在进入前就置位，探针内部 GPIO 配置失败也算"跑过一次"：宁可不重试，也不在一轮里多顶一次线。 */
static bool s_pp_done;

/* 一整段位碰诊断。调用前提：端口0 已交还（pads_free），且 41/42 此刻归我们支配。
 * scl_ext_high/pull_readable 由调用方从 pull compare 带进来：前者是"这一路有没有强于 45K 的
 * 外部驱动源"的唯一实测证据，推挽档必须躲开被外部钉高的那一路（否则就是和强驱动源对顶）；
 * 后者说明这份证据到不到手——gpio_config 都没成时"没证据"不等于"没有强驱动源"，那种情况下
 * 顶时钟是盲顶，只能跳过。不在本函数里重读一次——重读要再 gpio_config 两个脚，等于把刚交还的
 * 状态又搅一遍。
 * 数据路的外部上拉状态**不进参数**：SDA 在本探针里恒为开漏，它被不被钉高都不改变对顶风险。
 * 自己负责收尾（gpio_reset_pin 两根），不留状态给下一轮。 */
static void bb_probe(bool scl_ext_high, bool pull_readable)
{
    bb_run_t fast, slow, swapped = { 0 };
    int all_norm = 0, all_swap = 0;
    bool swapped_ran = false;   /* R39 P1-5：区分"对调档跑过且无应答"与"对调档根本没跑成" */

    esp_err_t e = bb_setup(&kBBNormal, false);
    if (e != ESP_OK) {
        ESP_LOGE(TAG, "bitbang: GPIO 配置失败 (%s) → 本轮位碰探针无输出", esp_err_to_name(e));
        gpio_reset_pin(AXP_SDA_PIN);
        gpio_reset_pin(AXP_SCL_PIN);
        return;
    }
    /* 先快后慢：快档是"复现硬件那一路的速度"，慢档是"给 45K 上拉留够上升时间"。
     * 两档只差速度，其余动作一模一样 ⇒ 若只有慢档拿到 ACK，差别就只可能出在边沿上。 */
    bb_run_at(&kBBNormal, BB_FAST_HALF_US, "fast~100kHz", "sda41/scl42", &fast);
    bb_run_at(&kBBNormal, BB_SLOW_HALF_US, "slow~20kHz", "sda41/scl42", &slow);
    /* 慢档已经证明时钟波形在焊盘上是合格的（9/9），此时"5 个地址没人应答"仍分不开
     * "线不通/踩错焊盘"与"线上没有活的器件"，所以再补一档位碰全地址扫。 */
    all_norm = bb_scan_all_slow(&kBBNormal, "sda41/scl42");

    /* 角色对调再跑一遍：这一档专门判"引脚表把 SDA/SCL 写反了"。它同时是那条不对称读数
     * （41 有强上拉、42 只跟内部电阻走）的另一半解释——如果反了，"缺上拉的那一脚"其实是
     * 时钟脚该由器件侧/对端上拉，而不是我们。判读：
     *   对调档拿到 ACK ⇒ 引脚表反了，改表就能救，这是能直接落地成修复的一条。
     *   两档都 9/9 且都无 ACK ⇒ 两根线都能被正常驱动、角色怎么摆都没人应答，"焊盘角色"排除。
     * **R37 真机走的是后者**：`swapped … 9clk_high=9/9 … ACK=0 NACK=112`，与正常角色同型，
     * 所以这一档已经交付了它的结论；留着是因为门条件④要拿它的 ACK 计数当"开漏五档都穷尽"的证据。 */
    e = bb_setup(&kBBSwapped, false);
    if (e != ESP_OK) {
        ESP_LOGE(TAG, "bitbang swapped: GPIO 配置失败 (%s) → 跳过对调档（④的门会因此直接不放行：swapped 全 0 是"
                      "「没跑成」，不是「没人应答」，见下面 !swapped_ran 那一条）",
                 esp_err_to_name(e));
    } else {
        bb_run_at(&kBBSwapped, BB_SLOW_HALF_US, "slow~20kHz", "swapped sda42/scl41", &swapped);
        if (swapped.acks == 0) all_swap = bb_scan_all_slow(&kBBSwapped, "swapped sda42/scl41");
        swapped_ran = true;
    }

    /* ④推挽 SCL（R38）：门从 R34 那版的"SCL 抬不起来"改成"开漏五档都穷尽 + 线上静默 +
     * 时钟路没被外部钉高"（R39 P1-14：这里原文写的是"四路"，而下面的求和项是
     * fast/slow/正常全扫/对调 slow/对调全扫 **五项**，叫"四路"会让人怀疑多算了一档）。
     * 理由：R35~R37 的实测里 `slow.scl_rel` 一直是 1，老门从未成立，
     * 于是"上升沿质量"这一维到现在都没被测过——而它是主机侧剩下的最后一维。
     * 不再要求 `scl_high==9`：0/9 那种坏法（线被负载压着）同样该由推挽判，老门的那个场景
     * 不能因为改写门而被丢掉。 */
    const bool od_exhausted = (fast.acks + slow.acks + swapped.acks + all_norm + all_swap) == 0;
    const bool bus_quiet = (slow.sda_after9 == 1 && slow.sda_low == 0);
    const char *pp_skip =
        !swapped_ran ? "对调档那一路 gpio_config 就没成 ⇒ 开漏五档里少了一档的证据，「穷尽」这句话此刻缺最后一维（R39 P1-5：以前这一档失败只是日志少一行，门却照开，而同一个「没证据」在 pull compare 那一路是按『不跑』处理的——两套口径不能并存）" :
        !od_exhausted ? "开漏那几路已经有 ACK，推挽只会多冒一次对顶风险，换不到新信息" :
        s_pp_done ? "本上电周期已跑过一次" :
        !bus_quiet ? "SDA 不干净（after9=0 ⇒ 9 拍后器件仍把数据线上扣着；或 sda_low=1 ⇒ 我们主动拉低却读回高，线上有比内部 45K 更强的驱动源）⇒ 事务不在静止态，此刻顶时钟最危险" :
        !pull_readable ? "pull compare 那两次 gpio_config 至少一次失败 ⇒ 不知道时钟路上有没有强驱动源，推挽就成了盲顶" :
        scl_ext_high ? "SCL 那一路已被外部驱动为高 ⇒ 推挽=与强驱动源对顶（该由它自己抬，不该我们顶）" : NULL;
    if (pp_skip == NULL) {
        s_pp_done = true;
        bb_pp_scan_all(&kBBNormal, "sda41/scl42");
    } else {
        ESP_LOGW(TAG, "bitbang sda41/scl42 PP-SCL 跳过（原因=%s）→ 主机侧「上升沿质量」这一维本轮仍未实测", pp_skip);
    }
    bb_sda(&kBBNormal, 1); bb_scl(&kBBNormal, 1); bb_delay(BB_SLOW_HALF_US);
    gpio_reset_pin(AXP_SDA_PIN);
    gpio_reset_pin(AXP_SCL_PIN);
}

/* 扫描结果的判读口径。只按"计数怎么分布"给结论，不掺任何电源假设：
 * ACK>0 与 全 TIMEOUT 是两种完全相反的坏法，前者是我们的驱动/引脚没问题，
 * 后者是波形根本没发出去，改软件的方向都不一样，所以每轮的日志都自带这句判读。
 * 两句"能排除什么"必须写清边界，否则这句判读会被当成免检结论用：
 * ①全 NACK **不能**洗清引脚表——扫的若是别的焊盘、且它们被我们的内部上拉钉高，读出来同样是
 *   NACK（这一档要和 pull compare 那一行一起看，但**即便配上 pull compare 也仍然不可分案**：
 *   "引脚表错、踩到另一条同样被 4.7K 上拉的网络"与"引脚对、器件没电"会打出完全相同的
 *   `ACK=0 NACK=5` + `pu/pd=1/1`；配得上对读只是排除了"扫错脚且那双脚悬空"这一种）。
 *   邻居里 SHTC3 在休眠、QMI8658
 *   挂另一路轨时同样 NACK，所以"全 NACK"也不等于"整条总线没有器件"。
 * ②NACK 与 TIMEOUT 不互相独立，而且**我们的计数不是纯被动观测**：本机 S3 的
 *   `SOC_I2C_SUPPORT_HW_CLR_BUS=1`（soc/esp32s3/include/soc/soc_caps.h:189），所以 i2c.c 里
 *   那段"GPIO 打 9 个脉冲"的软件清总线**被编译掉**，实际走 `i2c_ll_master_clr_bus()`
 *   （硬件自己发时钟）；调用点在 `i2c_hw_fsm_reset`（i2c.c:663-688）。触发条件有**四处**：
 *   每一次超时都复位一次（:1565、:1586），**每累计 10 次连续 ACK 错误**复位一次
 *   （:1569-1572，`I2C_ACKERR_CNT_MAX=10`），以及**每一笔新事务的入口**（:1514-1518）——上一次
 *   状态仍是 TIMEOUT，或 `i2c_ll_is_bus_busy()` 读到位忙，就先复位再发。我们走的是 legacy 支路
 *   （`i2c_master_write_read_device` → `i2c_master_cmd_begin`，i2c.c:1095/:1487，R32 本机核过），
 *   所以这条也在路上；但因为我们每轮先 `i2c_driver_delete` 再 install，`p_i2c->status` 是新的，
 *   入口那一档只能靠"线读起来是忙的"触发 ⇒ 它恰恰在**线真的被钳住**时才会动手，而这正是我们要它做的。
 *   计数器 `clear_bus_cnt[]` 是文件级 static，
 *   `i2c_driver_delete` 不清零 ⇒ 它跨我们每一轮累加：一轮里 5 次 0x34 重试 + 5 个邻居地址
 *   全是 NACK 就已经到 10，于是**下一轮第一笔事务之前**驱动就动过一次手。
 *   两个后果：①"全 TIMEOUT ⇒ 线动不了"仍然成立，但**别写成"连驱动的硬件清总线都没救回来"**
 *   （R32 复查第 10 条，本机已核实其代码形状：`i2c_hw_fsm_reset` 的三步顺序是
 *   `i2c_hw_disable`(:675) → `i2c_master_clear_bus`(:676) → `i2c_hw_enable`(:677)，而第一步里的
 *   `periph_module_disable`（:239 → `periph_ctrl.c:37 periph_ll_disable_clk_set_rst`；S3 那支
 *   `clk_gate_ll.h:259-263` 是**清 clk_en 并置复位**，不只是关时钟），
 *   第三步才重新开 ⇒ 中间那笔 `i2c_ll_master_clr_bus()`(:654) 是往一个"时钟已关 + 复位仍拉住"的块
 *   写寄存器（它写的三个位见 `i2c_ll.h:644-649`：`scl_rst_slv_num=9`、`scl_rst_slv_en=1`、
 *   `ctr.conf_upgate=1`）。这笔写在硬件上到底有没有真的发出 9 个 SCL 时钟，本机没有仪器、
 *   也没查到 S3 手册对"复位期间寄存器写"的口径，**未证实**；
 *   所以这一档只能读到"这笔事务在**它自己的上限**内没做成（扫描那支 20ms、`axp_read_reg` 那支 50ms，
 *   见上面 `:46`/`:115`），驱动试图自救但自救是否生效未知"）；
 *   ②被钳住的总线**不指望**靠我们自己的 delete/install 复原，因为它根本没用软件位敲。 */
static const char *bus_verdict(const bus_stats_t *st)
{
    if (st->total <= 0)         return "本轮未扫描，无任何总线证据";
    if (st->acks > 0)           return "有器件 ACK ⇒ 我方通路是好的";
    if (st->timeouts == st->total) return "全部超时 ⇒ 线动不了：引脚/端口表错，或线被钳住（我方通路问题）";
    if (st->nacks == st->total)    return "全部 NACK ⇒ 波形发得出去、这些地址无人应答（不洗清引脚表，也不等于总线上没器件，见 §13.4）";
    return "读数混合 ⇒ 见上面计数，别照单全收任何一句结论";
}

/* AXP2101 的 PWR_ON 状态脚：官方 08 demo 里叫 PWR_OUT（pcf85063_bsp.h: PWR_OUT_PIN = 1，
 * 配成输入 + 内部上拉）。它是"系统是否已开机"的硬件判据，不需要 I2C 就能读，
 * 因此能在"没有万用表/示波器"的条件下把责任分清。和总线一样要两路对读：
 *   pu=0            → 被外部强拉到低 = AXP 系统轨没开（没按电源键）→ 0 ACK 是必然，固件改不动它
 *   pu=1 且 pd=1    → 外部把它驱动为高 = 系统轨已开，此时仍 0 ACK 才指向我方 I2C 通路
 *   pu=1 且 pd=0    → 电平只是内部电阻决定的悬空值，说明 AXP 根本没驱动这个脚，不能判"已开机"
 * 这条判据和图纸口径互相矛盾，别当铁证用：图纸说 VCC3V3 = PMIC 的 DCDC1 输出，而 MCU 现在
 * 正在跑 ⇒ PMIC 有电、DCDC1 开着 ⇒ 这个脚不该是悬空。真读到悬空只剩两种解释：①这个脚不是
 * STATUS（脚号只来自官方 demo 的写法，未在实板核对）；②图纸那句读错了。两种都定不了"没供电"，
 * 所以这里仍只把 pu=0 当"确定没开机"，其余一律不定案、让上层继续放行真实判活。
 * （GPIO1 在 S3 上是 XTAL_32K_P；本工程 RTC 用内部 RC，未启用外部 32k 晶振，所以可安全当 GPIO 读。） */
#define AXP_PWR_OUT_PIN 1

static void axp_read_pwr_out(int *pu, int *pd)
{
    gpio_config_t in = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = 1ULL << AXP_PWR_OUT_PIN,
    };
    in.pull_up_en = GPIO_PULLUP_ENABLE;      /* 与官方 demo 一致的读法 */
    in.pull_down_en = GPIO_PULLDOWN_DISABLE;
    if (gpio_config(&in) != ESP_OK) { *pu = -1; *pd = -1; return; }
    vTaskDelay(pdMS_TO_TICKS(5));
    *pu = gpio_get_level(AXP_PWR_OUT_PIN);

    in.pull_up_en = GPIO_PULLUP_DISABLE;     /* 换成只开下拉：浮空脚会被拉低，真被外电路拉高的脚不会 */
    in.pull_down_en = GPIO_PULLDOWN_ENABLE;
    if (gpio_config(&in) != ESP_OK) { *pd = -1; gpio_reset_pin(AXP_PWR_OUT_PIN); return; }
    vTaskDelay(pdMS_TO_TICKS(5));
    *pd = gpio_get_level(AXP_PWR_OUT_PIN);
    gpio_reset_pin(AXP_PWR_OUT_PIN);
}

bool axp_enable_panel_rail(void)
{
    /* 轮次计数放在最前面：上层（epd_driver.c 的 s_probe_round）按"每次尝试"计一轮，
     * 这里若只在"装上了驱动之后"+1，一次 install 失败就让两个计数器永久错开 1，
     * "全量诊断刻意错开判活轮"那条算术随之失效（R24 复查抓到的 P2）。 */
    s_probes++;
    /* 不再在入口 gpio_reset_pin(41/42)：焊盘的 iomux/方向/上下拉全部由 install 内部的
     * `i2c_hw_enable → i2c_set_pin`（gpio_hal_iomux_func_sel(PIN_FUNC_GPIO) +
     * gpio_set_direction(INPUT_OUTPUT_OD) + connect + set_pull_mode）自己做完，提前复位
     * 对功能无用；而"端口0 归别人持有"的那一轮，这两行会抽走别人的焊盘——正是本文件
     * 立 `s_bus_ours` 要禁止的动作（R24 复查抓到的 P1：自相矛盾）。 */
    if (!s_bus_ours && !axp_bus_install()) {
        /* 驱动都没装上 = 本轮一条总线证据都没有，绝不能沿用上一轮的"确定没开机"。
         * s_sys_off 若停在 true，上层会连面板引脚都不许碰，就成了自己把自己锁死的闸门。 */
        ESP_LOGE(TAG, "I2C driver install failed → 本轮无任何总线证据，按未知处理（不判定开机状态）");
        s_axp_off = true;
        s_sys_off = false;
        return false;
    }

    /* "0x34 有没有应答"和"应答的是不是 AXP"必须分开：事务成功（有 ACK 且读回 1 字节）就往
     * ALDO3 走。把 id 不等也当成不可达，会漏掉一种真能救回屏的情况——器件在、只是 id 寄存器
     * 读回脏值（上电时序/总线偏弱），此时写 ALDO3 仍可能成功。id 只用于日志，不当闸门。 */
    uint8_t id = 0;
    bool acked = false;
    esp_err_t id_err = ESP_FAIL;
    for (int attempt = 0; attempt < 5 && !acked; attempt++) {
        id_err = axp_read_reg(AXP_REG_CHIP_ID, &id);
        acked = (id_err == ESP_OK);
        if (!acked) vTaskDelay(pdMS_TO_TICKS(20));
    }

    bus_stats_t known = {0, 0, 0, 0, 0};
    char known_ack[56] = {0};
    bus_stats_t all = {0, 0, 0, 0, 0};
    char all_ack[56] = {0};
    /* 头 3 轮 + 每 60 轮，且偏移 30 错开 PANEL_PROBES_PER_LIVENESS=12 的判活轮（见 axp_scan_all 上方）。
     * 一轮 full_diag 的 AXP 段实测锚点（R37 真机 t 值，COM14，日志 `20260921_R37位碰角色对调COM14_清洗版.log`
     * 第 66~77 行）。R39 按代码执行顺序重新归属过这些 t 值——原来那句把"邻居扫 + 全扫 + PWR 读"算进了
     * 687→1033 这一段，而那三件事的结果**就印在 t=687 那一行里**（`axp_scan_known`/`axp_scan_all`/
     * `axp_read_pwr_out` 三个调用全在那条 `ESP_LOGW` 之前），它们的耗时只可能落在 687 之前：
     *   t=518 MAC 行 → t=687 `AXP@0x34 no reply`：install + 0x34 的 5 次重试（典型
     *                  ≈101ms = 5×0.18 事务 + 5×20ms 失败间隔，那五次 20ms 见下面重试循环）+
     *                  邻居扫 ≈0.9ms + 硬件全扫 ≈20ms + PWR_OUT 读 10ms（两次 5ms 延时）
     *                  ≈132ms 排得出来，余下 ≈37ms 是 install/日志/未分段的部分——这一段没有
     *                  逐调用打点，所以只能说"落在同一量级"，别拿它当分项对账的凭据。
     *   t=687 → t=707 打印硬件全扫结果，中间只有 `i2c_driver_delete` ⇒ 卸载驱动 ≈20ms。
     *   t=707 → t=737 上拉对读（排定的只有两次 5ms 延时，余下是 gpio_config，没再分段测）。
     *   t=737 → t=746 位碰装 GPIO + fast 那档跑完（9ms）→ t=774 slow（28ms）→ t=890 正常角色
     *                  全地址扫（116ms）→ t=905 对调 slow（15ms）→ t=1022 对调全地址扫（117ms）
     *                  ⇒ **位碰那五档 = 737→1022 = 285ms**（R39 改用这一对锚点；`epd_driver.c`
     *                  持锁链那节原来记的"t=746→1033 ≈0.28s"两头都偏了一档——左边少了 fast 自己
     *                  那 9ms，右边多算了收尾的 11ms，数值凑巧也是 0.28s 才没被发现）。
     *   t=1022 → t=1033 `panel rail not confirmed`：释放两脚 + `gpio_reset_pin` + 回到上层 ≈11ms。
     * 整轮：full_diag→full_diag ≈5.48~5.54s，稳态 → 稳态 5151ms，差值就是这一段。④推挽档（R38）
     * 按同一实测口径再加 ≈117ms（R39 重算：34 段 ×25µs ×112 = 95.2ms 排定 + ≈21ms 调用开销），
     * 且一个上电周期只加一次。
     * 上限那一头按各段的超时上计算（`epd_driver.c` 的 `RELEASE_CLAIM_WAIT_MS` 注释），
     * 别再拿"112×20ms=2.24s"当整段预算——那是全地址扫一支的上限。 */
    const bool full_diag = (s_probes <= 3 || s_probes % 60 == 30);

    if (!acked) {
        /* 每轮都扫 5 个已知邻居地址（R39 改：原来写"4 个"，而 `kPeerAddrs` 是 5 个、`no reply`
         * 那行日志枚举的也是 0x18/0x51/0x70/0x6A/0x6B 五个）：只要有一个 ACK，"我方通路坏了"这条就排除掉了。 */
        axp_scan_known(&known, known_ack, sizeof(known_ack));
        if (full_diag) axp_scan_all(&all, all_ack, sizeof(all_ack));
        s_axp_off = true;   /* 屏电只能经 AXP 开，它不应答就点不亮面板 */
        int pwr_pu = -1, pwr_pd = -1;
        axp_read_pwr_out(&pwr_pu, &pwr_pd);
        /* 只有"被外部拉低"才是铁证；悬空(pu=1,pd=0)与配置失败(-1)都定不了案，
         * 保持 false 让上层每 12 轮放行一次 BUSY 判活，防止我方闸门本身出错。 */
        s_sys_off = (pwr_pu == 0);
        const char *pwr_s =
            pwr_pu < 0 || pwr_pd < 0 ? "PWR_OUT 配置失败，读数无效" :
            pwr_pu == 0  ? "PWR_OUT 被外部拉低 = PMIC 系统轨没开：按住电源键 2 秒后松开，没反应再按满 4 秒（硬件动作，改固件无用）" :
            pwr_pd == 1  ? "PWR_OUT 被外部驱动为高 = 系统轨已开，0 ACK 指向我方 I2C 通路"
                         : "PWR_OUT 悬空（PMIC 没驱动这个脚，定不了案）";
        ESP_LOGW(TAG, "AXP@0x34 no reply (probe#%u err=%s id=0x%02X) | known 0x18/0x51/0x70/0x6A/0x6B: ACK=%d NACK=%d TMO=%d other=%d [%s] → %s | PWR_OUT pu=%d pd=%d → %s",
                 (unsigned)s_probes, esp_err_to_name(id_err), id,
                 known.acks, known.nacks, known.timeouts, known.other,
                 known_ack[0] ? known_ack : "none", bus_verdict(&known),
                 pwr_pu, pwr_pd, pwr_s);
        if (known.acks > 0)
            ESP_LOGE(TAG, "I2C path is ALIVE (%d device(s) ACK on the same bus) → 0x34 silence is the PMIC side, not our SDA/SCL/driver",
                     known.acks);
    } else {
        if (id == AXP_CHIP_ID)
            ESP_LOGI(TAG, "AXP2101 detected (chip id 0x%02X, probe#%u)", id, (unsigned)s_probes);
        else
            ESP_LOGW(TAG, "0x34 replied but chip id=0x%02X != 0x4A (probe#%u) → 仍按 AXP 写 ALDO3；这一行本身就是疑点",
                     id, (unsigned)s_probes);
        s_axp_off = false;
        s_sys_off = false;   /* 会应答 I2C = 系统轨肯定有电 */
        /* 设 ALDO3 = 3.3V：(3300-500)/100 = 28 = 0x1C，保留高 3 位。
         * 每一条事务的返回码各自留一份：全挤进一个"最近一次 err"的槽里，0x90 那次失败会被
         * 0x94 那次的成功覆盖掉，日志就指错地方（这正是这轮复查抓到的 P1）。 */
        /* 初值**必须**是"这笔写没发起"而不是 ESP_OK：读失败时下面两个 if 根本不执行，
         * 留 ESP_OK 就成了 `0x94 rd=ESP_ERR_TIMEOUT wr=ok` —— 把责任从"我这条事务没做成"
         * 推到"写成功了但芯片没生效"，而这正是本轮唯一交付物（能自己分案的日志）说谎。 */
        esp_err_t vol_rd_e = ESP_ERR_INVALID_STATE, vol_wr_e = ESP_ERR_INVALID_STATE;
        esp_err_t en_rd_e = ESP_ERR_INVALID_STATE, en_wr_e = ESP_ERR_INVALID_STATE;
        uint8_t v = 0;
        vol_rd_e = axp_read_reg(AXP_REG_ALDO3_VOL, &v);
        if (vol_rd_e == ESP_OK)
            vol_wr_e = axp_write_reg(AXP_REG_ALDO3_VOL, (uint8_t)((v & 0xE0) | 0x1C));
        v = 0;
        en_rd_e = axp_read_reg(AXP_REG_LDO_ONOFF0, &v);
        if (en_rd_e == ESP_OK)
            en_wr_e = axp_write_reg(AXP_REG_LDO_ONOFF0, v | (1 << ALDO3_BIT));
        vTaskDelay(pdMS_TO_TICKS(100));   /* 等轨稳定 */
        /* 回读验证：写完不回读就成了"我以为开了"。真机上如果屏判活失败，
         * 分不清是"ALDO3 位没写进去"还是"面板本身坏了"，这一行就是两者的分界。 */
        uint8_t on = 0, vol = 0;
        const esp_err_t e_on = axp_read_reg(AXP_REG_LDO_ONOFF0, &on);
        const esp_err_t e_vol = axp_read_reg(AXP_REG_ALDO3_VOL, &vol);
        if (e_on != ESP_OK || !(on & (1 << ALDO3_BIT))) {
            ESP_LOGE(TAG, "panel rail (ALDO3) NOT verified: 0x94 rd=%s wr=%s | 0x90 rd=%s wr=%s | readback 0x90=%s/0x%02X 0x94=%s/0x%02X",
                     esp_err_to_name(vol_rd_e), esp_err_to_name(vol_wr_e),
                     esp_err_to_name(en_rd_e), esp_err_to_name(en_wr_e),
                     e_on == ESP_OK ? "ok" : esp_err_to_name(e_on), on,
                     e_vol == ESP_OK ? "ok" : esp_err_to_name(e_vol), vol);
            s_axp_off = true;   /* 轨没开成 = 面板必然无电，按"没电"处理，别去白等判活 */
        } else {
            ESP_LOGI(TAG, "panel rail (ALDO3) enabled: 0x90=0x%02X (bit2=1) 0x94=0x%02X → %dmV, wr 0x94=%s 0x90=%s",
                     on, vol, ((vol & 0x1F) * 100) + 500,
                     esp_err_to_name(vol_wr_e), esp_err_to_name(en_wr_e));
        }
    }

    /* 交还 41/42：卸载驱动并复位焊盘（SD 已改走 SDMMC，不再抢这两个脚）。 */
    /* delete 的返回值决定"这一轮到底是不是交还成功"。若失败还照旧清 s_bus_ours +
     * gpio_reset_pin，得到的是"端口里留着一个没人负责的死驱动、焊盘被我们改成输入+内部上拉"，
     * 下一轮 install 永远 ESP_FAIL，我们从此每轮都在"以为归自己"的状态下放弃总线，
     * 再也拿不到任何证据。所以失败时**保留所有权**：下一轮跳过 install 直接重试事务
     * （端口还在我们手里），并且在真删掉之前不碰这两个焊盘。 */
    if (s_bus_ours) {
        const esp_err_t de = i2c_driver_delete(AXP_I2C_PORT);
        if (de == ESP_OK) {
            s_bus_ours = false;
            gpio_reset_pin(AXP_SDA_PIN);
            gpio_reset_pin(AXP_SCL_PIN);
        } else {
            ESP_LOGE(TAG, "i2c_driver_delete: %s → 端口0仍记在我们名下，下一轮跳过 install 直接重试事务（41/42 不交还）",
                     esp_err_to_name(de));
        }
    }
    /* 焊盘此时是否归我们支配 = 端口0 已经不装了。上拉对读要 gpio_config 这两个脚，
     * 端口还装着的时候读出来的是驱动持有的电平，不是"线上有没有上拉"，那种数会编出一个
     * 假判读，所以它比"没打上这一行"贵得多。 */
    const bool pads_free = !s_bus_ours;

    /* 全地址扫描的结果**必须无条件打**：那一扫在本函数上面就已经付过钱了（R37 实测典型 ≈20ms，
     * 每笔都吃满 20ms 超时的坏法上限才是 2.24s），把它跟 pull compare 一起关进 `pads_free`
     * 闸门，等于 delete 失败那一轮"钱照付、证据全丢"，而这轮的产出就只有证据
     * （R27 复查抓到，排查记录 §十六）。 */
    if (!acked && full_diag && all.total)
        ESP_LOGW(TAG, "bus scan 0x08-0x77: ACK=%d NACK=%d TMO=%d other=%d acked:[%s] → %s",
                 all.acks, all.nacks, all.timeouts, all.other,
                 all_ack[0] ? all_ack : "none", bus_verdict(&all));

    /* 装不上驱动已经在上面 return 了；走到这里要么本轮装上了、要么端口仍归我们，
     * 两种情况下做上拉对读的前提都是 pads_free。 */
    if (!acked && full_diag && !pads_free)
        ESP_LOGW(TAG, "本轮跳过 pull compare：端口0 仍记在我们名下（i2c_driver_delete 没成），"
                      "这时读到的电平是驱动持有的，不是'线上有没有上拉'");
    if (!acked && full_diag && pads_free) {
        int up_sda = 0, up_scl = 0, dn_sda = 0, dn_scl = 0;
        esp_err_t e_up = ESP_OK, e_dn = ESP_OK;
        axp_bus_pull_compare(&up_sda, &up_scl, &dn_sda, &dn_scl, &e_up, &e_dn);
        ESP_LOGW(TAG, "pull compare (cfg err=%s/%s): pullUP SDA=%d SCL=%d | pullDOWN SDA=%d SCL=%d",
                 esp_err_to_name(e_up), esp_err_to_name(e_dn), up_sda, up_scl, dn_sda, dn_scl);
        /* 判读必须逐路给：两路不对称（例如 SDA 有外部驱动而 SCL 悬空）时，
         * 一句笼统结论会把"其中一路悬空"说成"整条总线悬空"，反过来误导下一次排查方向。
         * 每一路只会落在"钳低 / 外部驱动为高 / 悬空"三种之一 ⇒ 成对是 3×3=9 种，其中"任一路钳低"
         * 那几档被下面第一条分支合流，剩下两档对称（两路都外部高 / 两路都悬空）+ 两档不对称
         * （外部高落在 SDA 还是 SCL），一共**五种**收尾，每种必须有结论：
         * R35~R37 真机走的是"一路外部高、一路悬空"，而原版的收尾句只在**两路都悬空**时才触发
         * （条件里那一串 && 把不对称档整个漏掉），于是那三轮打出来的是没有结论的裸读数。 */
        const bool sda_ext = up_sda && dn_sda, sda_flt = up_sda && !dn_sda;
        const bool scl_ext = up_scl && dn_scl, scl_flt = up_scl && !dn_scl;
        /* 只有配置成功时的读数才能定"外部驱动为高"；否则一律按"没有证据说这一路被钉高"处理，
         * 因为 bb_probe 的推挽档要拿这个当"别和强驱动源对顶"的闸门。 */
        const bool cfg_ok = (e_up == ESP_OK && e_dn == ESP_OK);
        if (!cfg_ok) {
            ESP_LOGW(TAG, "pull verdict: GPIO 配置失败，读数无效");
        } else {
            const char *tail =
                (!up_sda || !up_scl)
                    ? " → 有一路被外部钳低：这与'缺上拉'无关，是低阻负载/对地短路，上拉和推挽都救不了"
                : (sda_ext && scl_ext)
                    ? " → 两路都有强于 45K 的外部驱动源 = 外部上拉在生效（图纸的正常态）"
                : (sda_flt && scl_flt)
                    ? " → 两路都只靠内部电阻撑着 = 4.7K 外部上拉没生效（没贴/那一轨 0V/这两个焊盘不是 SDA-SCL）"
                : (sda_ext && scl_flt)
                    ? " → 不对称：只有 SDA 那一路被外部驱动为高，SCL 只跟内部 45K 走 ⇒ '缺上拉'这一件事只落在 SCL 那一路。这一行**不**证明板上没有 4.7K：它只证明该路此刻没有强于 45K 的上拉源，'4.7K 在但那一轨 0V'与'这一根不是 SCL'仍分不开（后者由位碰的角色对调档判）"
                : (scl_ext && sda_flt)
                    ? " → 不对称：只有 SCL 那一路被外部驱动为高，SDA 只跟内部 45K 走 ⇒ '缺上拉'只落在 SDA 那一路（同上，不证明没有 4.7K）"
                : " → 逻辑上到不了这里（R39 补这句：每脚 3 态 ×2 脚 = 9 种，第一条吃掉'任一路钳低'5 种，"
                  "剩下 4 种由这四条收尾；以前这里是一条空串，读代码的人会去找'第六种没结论的情形'）";
            ESP_LOGW(TAG, "pull verdict: SDA=%s | SCL=%s%s",
                     pull_state(up_sda, dn_sda), pull_state(up_scl, dn_scl), tail);
        }
        /* 位碰探针紧跟 pull compare：它收尾已把 41/42 复位成交还状态，与本段共用同一前提
         * （pads_free）。pull compare 只回答"线上有没有上拉"，回答不了"我们动它的时候它动不动"，
         * 那正是位碰各档判读要分开的两件事。
         * 推挽那一档还要知道"时钟路是不是已经被外部钉高"，钉高就不许我们再去顶，所以把这一段的
         * 结论作为**两个**入参传下去：结论本身（`scl_ext` = SCL 那一路"外部驱动为高"）与
         * 这份证据到不到手（`cfg_ok`）。配置失败时"没有证据"绝不能读成"没有强驱动源"，
         * 所以第二参走的是 cfg_ok 而不是把 false 当成放行。 */
        bb_probe(cfg_ok && scl_ext, cfg_ok);
    }

    /* 以"轨是否真的被回读确认"为准，而不是"我发过使能命令"为准。 */
    return !s_axp_off;
}

bool axp_panel_off(void) { return s_axp_off; }

bool axp_system_off(void) { return s_sys_off; }
