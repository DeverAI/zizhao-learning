/* 墨水屏显示层：帧缓冲 + 排版 + 全刷/局刷策略（任务线 R19）。
 *
 * 页面只有三种：时钟（大数字+日期+标题）、状态（按键反馈）、消息（整屏提示）。
 * 换页或每满 5 次局刷一次全刷（消残影）；同页内容变化只局刷脏区。
 * 渲染逻辑与刷新硬件解耦：任何一笔失败只记日志，绝不 panic（屏坏了系统照跑）。 */
#include "eink_display.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"

#include "epd_driver.h"
#include "ui_font.h"
#include "esp_heap_caps.h"

static const char *TAG = "eink";

/* 局刷开关：真机若发现局刷残影/不生效，置 0 即全部走全刷，不用回滚驱动代码。
 * 现在**先置 0**：局刷路径（DIFF 模式、0x24/0x26 平面语义、窗口对齐）一行都还没在
 * 有电的真屏上被肉眼验证过——AXP 至今 0 应答，成功分支从未走过。首轮上电验证要的是
 * "屏上一定出现内容"，而全刷是唯一**逐条对着官方 EPD_Display_Base + EPD_TurnOnDisplay
 * 核过寄存器**的路径；局刷则是我们自己的窗口化实现（官方 Display_Partial 本身有
 * Xend 少 7 列、以及把整幅子数据从缓冲区首开始推的问题，见排查记录），风险更高。
 * 看到全刷内容确认后再置 1 专测局刷与鬼影，出问题时结论也不会和"屏到底有没有电"混在一起。 */
#define ENABLE_EINK_PARTIAL 0
#define FULL_EVERY_N_PARTIAL 5

typedef enum { PAGE_NONE = 0, PAGE_CLOCK, PAGE_STATUS, PAGE_MSG } page_t;

static uint8_t *s_fb;             /* 1=白 0=黑，行主序 stride=EPD_STRIDE */
static SemaphoreHandle_t s_lock;
static volatile bool s_panel_ok = false;
static page_t s_page = PAGE_NONE;
static int s_partial_cnt = 0;
static int s_x0, s_y0, s_x1, s_y1; /* 脏区（像素，左闭右开） */
static int s_px0, s_py0, s_px1, s_py1; /* 上一帧脏区，用于并集刷新消鬼影；空判定 s_px1<=s_px0 */

static bool ensure_fb(void);
static void panel_watch_start(void);
static void rewatch_if_panel_gone(void);

/* ---------- 帧缓冲基元 ---------- */

static void fb_black(int x, int y)
{
    if (x < 0 || y < 0 || x >= EPD_WIDTH || y >= EPD_HEIGHT) return;
    s_fb[(size_t)y * EPD_STRIDE + (x >> 3)] &= (uint8_t)~(0x80 >> (x & 7));
}

static void dirty_add(int x0, int y0, int x1, int y1)
{
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > EPD_WIDTH) x1 = EPD_WIDTH;
    if (y1 > EPD_HEIGHT) y1 = EPD_HEIGHT;
    if (x1 <= x0 || y1 <= y0) return;
    if (x0 < s_x0) s_x0 = x0;
    if (y0 < s_y0) s_y0 = y0;
    if (x1 > s_x1) s_x1 = x1;
    if (y1 > s_y1) s_y1 = y1;
}

static void dirty_reset(void)
{
    s_x0 = EPD_WIDTH; s_y0 = EPD_HEIGHT; s_x1 = 0; s_y1 = 0;
}

/* ---------- UTF-8 ---------- */

static const char *utf8_next(const char *s, uint32_t *cp)
{
    uint8_t b = (uint8_t)*s;
    if (b < 0x80) { *cp = b; return s + 1; }
    if ((b & 0xE0) == 0xC0 && (uint8_t)s[1] >= 0x80 && (uint8_t)s[1] < 0xC0) {
        *cp = ((uint32_t)(b & 0x1F) << 6) | (uint8_t)(s[1] & 0x3F);
        return s + 2;
    }
    if ((b & 0xF0) == 0xE0 && (uint8_t)s[1] >= 0x80 && (uint8_t)s[1] < 0xC0
        && (uint8_t)s[2] >= 0x80 && (uint8_t)s[2] < 0xC0) {
        *cp = ((uint32_t)(b & 0x0F) << 12) | ((uint32_t)(s[1] & 0x3F) << 6) | (uint8_t)(s[2] & 0x3F);
        return s + 3;
    }
    if ((b & 0xF8) == 0xF0 && (uint8_t)s[1] >= 0x80 && (uint8_t)s[1] < 0xC0
        && (uint8_t)s[2] >= 0x80 && (uint8_t)s[2] < 0xC0
        && (uint8_t)s[3] >= 0x80 && (uint8_t)s[3] < 0xC0) {
        *cp = ((uint32_t)(b & 0x07) << 18) | ((uint32_t)(s[1] & 0x3F) << 12)
              | ((uint32_t)(s[2] & 0x3F) << 6) | (uint8_t)(s[3] & 0x3F);
        return s + 4;
    }
    *cp = '?';   /* 坏字节按 '?' 兜底，不死循环 */
    return s + 1;
}

/* ---------- 字模 ---------- */

/* 正文取模：ASCII→30px 半角，其余→32px 全角；缺失画替代框，绝不返回空导致断行错位。 */
typedef const uif_font_t *(*pick_fn)(uint32_t cp);

static const uif_font_t *pick_body(uint32_t cp)
{
    if (cp < 0x80) return &UIF_LATIN32;
    return &UIF_CJK32;
}

static const uif_font_t *pick_ascii(uint32_t cp)
{
    (void)cp;
    return &UIF_ASCII16;
}

static const uif_font_t *pick_digit(uint32_t cp)
{
    if (cp >= 0x80) return &UIF_CJK32;
    return &UIF_DIGIT96;
}

static void draw_glyph(int x, int y, const uif_glyph_t *g)
{
    int stride = (g->w + 7) / 8;
    for (int gy = 0; gy < g->h; gy++) {
        const uint8_t *row = g->bits + (size_t)gy * stride;
        for (int gx = 0; gx < g->w; gx++) {
            if (row[gx >> 3] & (0x80 >> (gx & 7))) fb_black(x + gx, y + gy);
        }
    }
    dirty_add(x, y, x + g->w, y + g->h);
}

static void draw_fallback_box(int x, int y, int w, int h)
{
    for (int i = 0; i < w; i++) { fb_black(x + i, y); fb_black(x + i, y + h - 1); }
    for (int j = 0; j < h; j++) { fb_black(x, y + j); fb_black(x + w - 1, y + j); }
    dirty_add(x, y, x + w, y + h);
}

static int glyph_width(pick_fn pick, uint32_t cp)
{
    if (cp == ' ') return 12;   /* 空格只前进、永不画替代框 */
    const uif_glyph_t *g = uif_lookup(pick(cp), cp);
    if (g) return g->w + 1;   /* 1px 字间距 */
    return cp >= 0x80 ? 33 : 18;
}

/* 返回绘制后 x；行内按最大 ascent 做基线对齐（数字+汉字混排行底线齐）。 */
static int draw_text(int x, int y, const char *s, pick_fn pick)
{
    /* 预扫一遍取行内最大 ascent */
    int max_asc = 0;
    const char *p = s;
    uint32_t cp;
    while (*p) {
        const char *np = utf8_next(p, &cp);
        const uif_font_t *f = pick(cp);
        const uif_glyph_t *g = uif_lookup(f, cp);
        if (!g && cp >= 0x80) g = uif_lookup(&UIF_LATIN32, cp);
        if (g && f->ascent > max_asc) max_asc = f->ascent;
        p = np;
    }
    p = s;
    while (*p) {
        const char *np = utf8_next(p, &cp);
        if (cp == ' ') { x += 12; p = np; continue; }   /* 与 glyph_width 一致，只前进 */
        const uif_font_t *f = pick(cp);
        const uif_glyph_t *g = uif_lookup(f, cp);
        if (!g && cp >= 0x80) { g = uif_lookup(&UIF_LATIN32, cp); f = &UIF_LATIN32; }
        if (g) {
            int gy = y + (max_asc - f->ascent);
            draw_glyph(x, gy, g);
            x += g->w + 1;
        } else {
            draw_fallback_box(x, y, 32, max_asc ? max_asc : 30);
            x += 33;
        }
        p = np;
    }
    return x;
}

static int measure_text(const char *s, pick_fn pick)
{
    int w = 0;
    const char *p = s;
    uint32_t cp;
    while (*p) {
        const char *np = utf8_next(p, &cp);
        w += glyph_width(pick, cp);
        p = np;
    }
    return w;
}

static void draw_centered(int y, const char *s, pick_fn pick)
{
    int w = measure_text(s, pick);
    int x = (EPD_WIDTH - w) / 2;
    if (x < 0) x = 0;
    draw_text(x, y, s, pick);
}

/* 贪心换行渲染：按字符断行（CJK 无空格也排得开），限宽 maxw。
 * 两个不变量：①line 每装一个字符立刻补 NUL，否则 measure_text 会把上一行的
 * 残留字节算进宽度；②y 不越过屏底，画不下的截断（宁截断也不把字形写到帧缓冲
 * 外，也不让 y 无限增长把后面的消息全推没）。 */
static void draw_wrapped(int y0, const char *s, pick_fn pick, int maxw, int line_h)
{
    /* 行缓冲要装得下"限宽内最坏的一整行"，否则宽度优先的换行轮不到生效、
     * 退化成每 N 字硬断一行。按字节最省的是 ASCII16 那档：字模 8px + 1px 间距 = 9px/字节，
     * 两个调用点里最宽的限宽是 740px → 740/9 ≈ 82B 一行；32px 全角更宽（33px/字）但
     * 3B/字，算下来 ≈67B。取 256 是 ≈3 倍余量，代价是这一层多 256B 栈——draw_wrapped
     * 只跑在 app_main(8192B) 和 httpd(6144B) 上，6144B 的监视任务只做判活+刷白，不走这里。 */
    char line[256] = {0};
    int li = 0;
    const char *p = s;
    uint32_t cp;
    int y = y0;
    while (*p && y < EPD_HEIGHT) {
        const char *np = utf8_next(p, &cp);
        int n = (int)(np - p);
        if (n > (int)sizeof(line) - 1) n = (int)sizeof(line) - 1;
        bool fits_buf = (li + n < (int)sizeof(line));
        int curw = measure_text(line, pick);
        int gw = fits_buf ? glyph_width(pick, cp) : 0;
        if (li > 0 && (!fits_buf || curw + gw > maxw)) {
            draw_centered(y, line, pick);
            y += line_h;
            li = 0;
            line[0] = 0;
            if (y >= EPD_HEIGHT) break;
        }
        memcpy(line + li, p, n);
        li += n;
        line[li] = 0;
        p = np;
    }
    if (li > 0 && y < EPD_HEIGHT) {
        draw_centered(y, line, pick);
    }
}

/* ---------- 刷新 ---------- */

static void present(page_t page)
{
    bool need_full = !ENABLE_EINK_PARTIAL || page != s_page || s_partial_cnt >= FULL_EVERY_N_PARTIAL;
    if (need_full) {
        epd_display_full(s_fb);
        s_partial_cnt = 0;
        s_px1 = 0; s_px0 = EPD_WIDTH;   /* 全刷后整屏与 fb 同步，清空上一帧脏区 */
    } else {
        /* 并集刷新：本次要画的字 ∪ 上一帧画过的字。否则同页文字变短/左移时，
         * 被擦成白的旧字形不在本次脏区内，局刷不会清它 → 鬼影残留。 */
        int rx0 = s_x0, ry0 = s_y0, rx1 = s_x1, ry1 = s_y1;
        if (s_px1 > s_px0) {
            if (s_px0 < rx0) rx0 = s_px0;
            if (s_py0 < ry0) ry0 = s_py0;
            if (s_px1 > rx1) rx1 = s_px1;
            if (s_py1 > ry1) ry1 = s_py1;
        }
        if (rx1 > rx0 && ry1 > ry0) {
            if (!epd_display_partial(s_fb, rx0, ry0, rx1, ry1)) {
                ESP_LOGE(TAG, "partial refresh failed, forcing full next time");
                s_page = PAGE_NONE;   /* 基准平面可能已失真，下次全刷重建 */
            }
        }
        s_partial_cnt++;
        /* 记下本帧字形区作为下帧并集的另一半（不是并集本身：并集已把上上帧残留刷掉了） */
        s_px0 = s_x0; s_py0 = s_y0; s_px1 = s_x1; s_py1 = s_y1;
    }
    /* 刷失败（面板中途不应答）时不把页面记成"已显示"：留 PAGE_NONE 让下一次重来，
     * 免得"我以为这页画过了"而下一次走局刷、拿一个失真的基准平面去对比。 */
    s_page = epd_ready() ? page : PAGE_NONE;
    dirty_reset();
    rewatch_if_panel_gone();
}

static void begin_render(void)
{
    memset(s_fb, 0xFF, EPD_FB_SIZE);
    dirty_reset();
}

/* ---------- 公共接口（签名与旧 stub 兼容） ---------- */

/* fb 直接作为 SPI DMA 的 tx_buffer：必须内部 + DMA capable RAM（本板未开 PSRAM 配置，
 * 48KB 是一笔连续内部内存，开机早期最紧张，所以失败后由监视任务按轮次重试分配。 */
static bool ensure_fb(void)
{
    if (s_fb) return true;
    s_fb = heap_caps_malloc(EPD_FB_SIZE, MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA);
    if (!s_fb) ESP_LOGW(TAG, "framebuffer alloc failed (%d B free int DMA=%u)", EPD_FB_SIZE,
                        (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA));
    return s_fb != NULL;
}

/* 刷新后面板不再应答（中途被关机/掉电）：撤下"屏可用"标记并重新起监视，
 * 否则 s_panel_ok 会永远停在 true，之后所有 eink_show_* 静默返回、再也点不亮。 */
static void rewatch_if_panel_gone(void)
{
    if (epd_ready()) return;
    ESP_LOGW(TAG, "panel went silent, arming background watch");
    s_panel_ok = false;
    panel_watch_start();
}

/* 面板刚确认活着：整屏刷白，确立局刷基准平面，同时给出"屏亮了"的肉眼证据。
 * 调用方必须持有 s_lock：驱动层自己没有互斥，两条路径同时翻 CS/DC 会把命令流打乱
 * （监视任务与 eink_init 都已把"判活 + 刷白"整段放进锁里）。 */
static void paint_blank_locked(void)
{
    begin_render();
    epd_display_full(s_fb);
    s_page = PAGE_NONE;
    s_px1 = 0; s_px0 = EPD_WIDTH;
    s_panel_ok = epd_ready();   /* 刷白途中面板掉线就不算点亮，交给监视任务重来 */
    if (s_panel_ok) ESP_LOGI(TAG, "panel blanked (800x480), free int DMA heap=%u",
                             (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA));
}

/* 屏电由板载 PMIC（AXP2101 寄存器口径）的 ALDO3 出，官方 demo 点屏第一步就是
 * 开 ALDO3（`ESP-IDF/08_ESP32-S3_e-Paper-3.97/components/epaper_port/epaper_port.c:182-186` 里一句
 * `enapwrstate(ALDO3)`，wrapper 在 `…/axpPower/axp_prot.cpp:206-207`，
 * 它在 `EPD_Init()` 的第一条语句 `:236`；寄存器位映射见 `epd_driver.c` 中 `probe_attempt()` 上方那段），
 * 所以 I2C 写不进 PMIC 就没有任何路径能让屏亮起来。
 * 真机现状：只插 USB-C 时 PMIC 全程 0 ACK（MCU 这一路 3V3 显然是活的，固件在跑）。
 * 两种解释还没定案——① PMIC 要"开机"后 TWI 才活。按压时长只能给区间：官方 demo 写的是
 * POWERON_1S / POWEROFF_4S（≥1 秒开机、按住 4 秒是**关机**门限；
 * `…/08_…/components/axpPower/axp_prot.cpp:76` / `:61`），但那两句要 I2C 写成功才生效，
 * 我们的固件从没写到过这一步 ⇒ 实板当前的真实门限是芯片默认值，没人核实过。手册口径又是
 * "长按 4 秒开机"。所以操作上：先按住约 2 秒松开，没反应再按满 4 秒，两种都试过一次才算排除；
 * ② 我方 I2C 通路本身不通。图纸读到的口径反而支持 ②（VCC3V3 就是 PMIC 的 DCDC1 输出，
 * MCU 能跑 ⇒ PMIC 有电），但那条图纸读数也还没在实板核对过。
 * axp_panel_power.c 每轮的 0x51/0x70/0x6A/0x6B 扫描 + ACK/NACK/TMO 分类就是专门分开这两条的。
 * 在录到那一行之前，"必须接电池"整句都只是待验证假设，不是结论。
 * 开机顺序天然是固件先跑、人后按键，所以点亮不能只赌开机那一瞬：
 * 这里后台周期性重新判活，用户任何时刻让 PMIC 上电，屏都会在数秒内自己亮起来，无需重烧。
 * 前 30 分钟每 5s 一轮（"刚接上电"的窗口），之后退避到 60s 一轮且不再放弃——
 * 否则半小时后才开机就永远点不亮，只能重启固件。 */
#define PANEL_WATCH_STEP_MS 5000
#define PANEL_WATCH_FAST_TRIES 360   /* 5s × 360 ≈ 30 分钟 */
#define PANEL_WATCH_SLOW_MS   60000

static volatile bool s_watch_running = false;

static void panel_watch_task(void *arg)
{
    (void)arg;
    for (int i = 1; ; i++) {
        int step = (i <= PANEL_WATCH_FAST_TRIES) ? PANEL_WATCH_STEP_MS : PANEL_WATCH_SLOW_MS;
        vTaskDelay(pdMS_TO_TICKS(step));
        if (s_panel_ok) break;                    /* 别处已经把屏点起来了 */
        /* 判活 + 刷白整段持锁：驱动层（SPI/CS/DC）没有自己的互斥，本任务与 main 同优先级
         * 只是按 tick 轮转，仍可能在 main 的一次全刷中途切进来翻 CS → 两边命令流互相
         * 打乱，所以整段都要在锁里。paint_blank_locked 是不带锁的版本，避免不可重入的自锁。 */
        xSemaphoreTake(s_lock, portMAX_DELAY);
        /* 顺序是"先判活、后要帧缓冲"：本轮唯一交付物是那一组诊断日志（ACK/NACK/TMO、
         * passive BUSY、pull compare），48KB 拿不到时必须照样问一遍，否则在最需要证据的
         * 分支上一行都不打，而下面还会照打"panel still off — 接电池+按电源键"，等于误导。 */
        bool alive = epd_panel_probe();
        if (alive) {
            if (ensure_fb()) paint_blank_locked();
            else ESP_LOGE(TAG, "watch: 面板应答但拿不到 %d 帧缓冲，本轮不刷白（下一轮重试）", EPD_FB_SIZE);
        }
        bool lit = s_panel_ok;                    /* probe 过了又在刷白中途掉线 → 下一轮重来 */
        xSemaphoreGive(s_lock);
        if (lit) {
            ESP_LOGI(TAG, "panel came alive on watch try %d", i);
            break;
        }
        const bool fast = (i <= PANEL_WATCH_FAST_TRIES);
        /* 节律用**驱动侧的轮号**，不用本任务的 i：i 从 1 起，而 eink_init 已经先吃掉若干轮，
         * 两套号永远错着——按 i%12 打出来的这条汇总恰好落在"没有被动证据"的那些轮上，
         * 读者拿着它去对 `probe #N` / `witness` / `passive BUSY sample` 一行都对不上（R27 复查 P2-1）。
         * 顺带：这条汇总必须分两种情形说话。R27 复查 P1-3 抓到的是第二种——面板已经应答了
         * 却没刷成（48KB 帧缓冲没拿到，或刷白中途掉线），此时打"panel still off — 接电池+按电源键"
         * 是把用户的动作指向错的方向：电已经通了，缺的是内存。 */
        const unsigned pr = epd_probe_round();
        if ((fast && pr % 12 == 0) || (!fast && pr % 60 == 0)) {
            UBaseType_t hw = uxTaskGetStackHighWaterMark(NULL);
            /* IDF 的实现按 0xa5 逐字节计数，返回的是"剩余字节"，不是字数。 */
            if (alive)
                ESP_LOGW(TAG, "watch %d / probe #%u: 面板应答但没刷上（帧缓冲或刷白这步没过，看上一行），别再按电源键了 → 查内存 (watch stack free=%u/%d B)",
                         i, pr, (unsigned)hw, 6144);
            else
                ESP_LOGW(TAG, "watch %d / probe #%u: panel still off — 接电池 + 按住电源键 2 秒后松开，没反应再按满 4 秒 (watch stack free=%u/%d B)",
                         i, pr, (unsigned)hw, 6144);
        }
    }
    if (!s_panel_ok)
        ESP_LOGE(TAG, "panel never came alive (屏幕不显示，其余功能照常运行)");
    s_watch_running = false;
    vTaskDelete(NULL);
}

static void panel_watch_start(void)
{
    /* 幂等：不能起两个探测任务（它们会同时翻同一组 CS/DC）。今天所有调用点要么在
     * s_lock 内、要么在本任务独占的开机段，所以"检查-后置位"这两步暂时是安全的；
     * 仍用挂起调度器把它们钉在一起，免得将来有人在锁外新增调用点时静默退化。 */
    vTaskSuspendAll();
    if (s_panel_ok || s_watch_running) {
        xTaskResumeAll();
        return;
    }
    s_watch_running = true;
    xTaskResumeAll();
    BaseType_t ok = xTaskCreate(panel_watch_task, "epd_watch", 6144, NULL, 1, NULL);
    if (ok != pdPASS) {
        s_watch_running = false;
        /* R27 复查 P2-3 说"创建失败后没有任何重试点"——不成立，但要说清靠什么重试：
         * 这里把 s_watch_running 放回 false，下一次 `eink_show_*` 走到 rewatch_if_panel_gone()
         * （第 277 行那条路径）就会再试一次；main 循环每分钟要刷时钟，所以"永远不再试"只会
         * 发生在**连一次显示调用都没有**的情形。真正没解决的是：如果堆一路紧，重试也一直失败，
         * 屏就在这一整个上电周期里点不亮（没有更低的代价可以把监视跑起来——它自己要 6KB 栈）。 */
        ESP_LOGE(TAG, "panel watch task create failed (heap?) → 屏这一轮点不亮，等下一次显示调用再试");
    }
}

void eink_init(void)
{
    if (!s_lock) s_lock = xSemaphoreCreateMutex();
    if (!s_lock) { ESP_LOGE(TAG, "mutex create failed, display disabled"); return; }
    /* 与监视任务同样的形状：判活 + 刷白整段在锁内（驱动层无自己的互斥）。
     * 此刻本任务独占显示，但 eink_show_* 已经可能被别的任务调，锁先加上不亏。 */
    xSemaphoreTake(s_lock, portMAX_DELAY);
    /* 48KB 连续内部 DMA 拿不到时不能直接放弃：内部堆会随启动阶段释放，
     * 交给监视任务每轮重试，否则屏永远黑且没有任何恢复路径。
     * 顺序与监视任务一致：**先判活再要帧缓冲**，内存紧张时那一轮的诊断日志照样要出。 */
    bool lit = false;
    if (epd_init()) {
        if (ensure_fb()) {
            paint_blank_locked();
            lit = s_panel_ok;
            if (lit)
                ESP_LOGI(TAG, "eink driver ready (800x480), free int DMA heap=%u",
                         (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA));
        } else {
            ESP_LOGE(TAG, "panel alive but no framebuffer (%d), 交给监视任务重试拿内存", EPD_FB_SIZE);
        }
    } else {
        /* 不在这里死等：开机阻塞 30s 会拖慢配网/OTA，且人在 30s 后按键照样黑屏。 */
        ESP_LOGW(TAG, "panel off at boot, background watch will retry");
    }
    xSemaphoreGive(s_lock);
    if (!lit) panel_watch_start();
}

void eink_show_status(const char *line1, const char *line2, const char *line3)
{
    ESP_LOGI(TAG, "STATUS | %s | %s | %s",
             line1 ? line1 : "", line2 ? line2 : "", line3 ? line3 : "");
    if (!s_panel_ok || !s_lock) return;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    begin_render();
    draw_centered(96, line1 ? line1 : "", pick_body);
    draw_centered(168, line2 ? line2 : "", pick_body);
    if (line3 && line3[0])
        draw_wrapped(248, line3, pick_ascii, EPD_WIDTH - 80, 20);  /* 第三行是调试/错误串，用半角小字 */
    present(PAGE_STATUS);
    xSemaphoreGive(s_lock);
}

void eink_show_clock(const char *hhmm, const char *date_line, const char *title)
{
    ESP_LOGI(TAG, "CLOCK %s  %s  %s",
             hhmm ? hhmm : "--:--", date_line ? date_line : "", title ? title : "");
    if (!s_panel_ok || !s_lock) return;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    begin_render();
    draw_centered(90, hhmm ? hhmm : "--:--", pick_digit);
    draw_centered(286, date_line ? date_line : "", pick_body);
    draw_centered(344, title ? title : "", pick_body);
    present(PAGE_CLOCK);
    xSemaphoreGive(s_lock);
}

void eink_show_message(const char *msg)
{
    ESP_LOGI(TAG, "MSG %s", msg ? msg : "");
    if (!s_panel_ok || !s_lock) return;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    begin_render();
    draw_wrapped(180, msg ? msg : "", pick_body, EPD_WIDTH - 60, 46);
    present(PAGE_MSG);
    xSemaphoreGive(s_lock);
}

void eink_sleep(void)
{
    /* 闸门只看 s_lock，不看 s_panel_ok：屏没点亮时也要走到 epd_sleep()，由它内部按
     * "引脚配过没有(s_bus_ok) + 最近一次证据说它在应答没有(s_ready)"分成三条路：
     *   活过 → 发 0x10 + RST 低 + CS/DC 释放；
     *   配过引脚但从没活过 → 5 根脚（RST/DC/CS/SCLK/MOSI）连同 SPI 一起交还成
     *     "`GPIO_MODE_DISABLE` + 内部上拉"（R33 P2-5 口径：**不**钉高、也**不是**高阻，
     *     但也不是"输入"——输入缓冲是关的，见 epd_driver.c epd_pins_release 内那段）；
     *   引脚没配过 → 什么都不做。
     * 若在这里先用 s_panel_ok 挡掉，后两条就永远执行不到，引脚留在运行末尾的状态进深睡。 */
    if (!s_lock) return;
    /* 有限等待：不能用 portMAX_DELAY，深睡路径上卡死比"引脚没归位"严重。
     * 上限只须盖住**持锁方那一轮的最坏值**（等到锁就行，自己那一轮的时间不计在这里）。
     * 【R39：这一段以前是 3.3 + 2.75 + 2.75 + 8 ≈16.8s 一条链，那条链把两个**不会同轮出现**的
     *  分支串在了一起——`axp_enable_panel_rail()` 里那 2.24s 全地址扫和 ≈0.4s 位碰都只在
     *  `full_diag`（轮号 ≤3 或 30+60k）跑，而 `probe_attempt()` 的电轨闸门
     *  `if (rail_off && (s_probe_round % PANEL_PROBES_PER_LIVENESS) != 0) return false;`
     *  要求 `%12==0` 才放行判活；`s_probes` 与 `s_probe_round` 每轮同进同退（见 `epd_driver.c`
     *  `probe_attempt` 上方那段），30+60k 恒 ≡6 (mod 12)、1/2/3 也不满足 ⇒ 全诊断轮**根本走不到**
     *  `epd_panel_init()`，更走不到刷白。反过来能刷白的那一轮，AXP 段按"0x34 不应答"那个子案只剩
     *  0.35s(五次重试) + 0.1s(邻居扫) + 0.01s(PWR 读) = **0.46s**（【R41 P2】本行旧版印 0.47s，
     *  与它自己的分项和差 0.01 —— 同一条注释指责过的"公布的数 ≠ 自己算式的值"），按"应答但 ALDO3
     *  回读没确认"那个子案是 ≤0.73s（`axp_bus_install()` 失败那第三支一条事务都不发 ⇒ AXP ≈0，
     *  三支都是"轨没确认"，闸门同样放行——见下面分支 B 的 R40 二修 + R41 P1 补）。所以最坏值
     *  必须分两支、再各取宽的那一头：】
     *   分支 A（全诊断轮、`!acked`、不进 init）：AXP 段 ≈3.3s（分项见 `epd_driver.c` 的
     *       `RELEASE_CLAIM_WAIT_MS` 注释，那边记 3.1s，这里沿用 eink 侧一直取的更宽读数）
     *       ⇒ **≈3.3s**，本轮 probe 直接返回 false、不刷白。
     *       【R40 P2：这一支**不含**被动判活/旁证那 0.05s】`probe_attempt()` 里电轨闸门那一句
     *       就排在 `epd_busy_passive_low()` **之前**，而 A 支按定义 `rail_off` 为真 ⇒ 闸门先
     *       return。R39 这里写"3.3 + 0.05 ⇒ 3.35s"是把走不到的段记进来了（同一段注释指责的
     *       互斥相加的另一半），那一族数在 `epd_driver.c` 里也一起改成 A 3.1s / B 3.53s。
     *   分支 B（能刷白的那一轮）：AXP 取子案的宽头 ≈**0.73s**（【R40 二修】上一版这里写的
     *       "≈0.47s"只算了"`!acked`"那个子案；`rail_off` 有**三条**来源（R41 P1：旧版只列两条，
     *       漏了 `axp_bus_install()` 失败——那支 AXP ≈0，是最便宜的 ⇒ 不改宽头），其中"AXP 应答了但
     *       ALDO3 回读没确认"那一支的 0x94/0x90 四笔读写 + 100ms 稳压 + 两次回读 = 0.2+0.1+0.1 = 0.4s，
     *       比 B1 那"邻居扫 + PWR 读"的 0.11s 多 ≈0.29s；重试段两边同量级（0.33 vs 0.35）⇒
     *       合计 0.73 vs 0.46，宽头 0.27s（R41：旧版写"0.47 / 0.26"是按未订正的 B1 算的；
     *       分项见 `epd_driver.c` 的 B2），而它同样落在闸门放行的
     *       那一支里 ⇒ 上限必须按它取。
     *       邻居扫 0.1s 与 PWR 读 0.01s 反而是 `!acked` 子案独有的，两边不能加在一条算式里）
     *       + 被动判活/旁证 ≈0.05s（R40 补：这一支才轮到它）
     *       → `epd_panel_probe()` 的 `epd_panel_init()`
     *       （复位 0.1s + **发 0x12 前等 BUSY 回低 ≤0.5s（`EPD_PRE_RESETTLE_WAIT_MS`，
     *       R33 P0-2 新增）** + 判活 1.85s + 等空闲 0.3s ≤**2.75s**，典型 ≈2.25s。
     *       这 2.75s 里的 50ms 密采段是**下限**不是上界，见 `epd_driver.c` 同名分项那条 R40 注）
     *       → 活了才 `paint_blank_locked()` → `epd_display_full()` 里**还有一次** `epd_panel_init()`
     *       （同样 ≤2.75s，那 0.5s 的等低它也会付）+ 两帧 96KB 经 20MHz SPI ≈0.05s
     *       + 等 BUSY 超时 `EPD_BUSY_TIMEOUT_MS`=8s ⇒ **≈14.3s**（0.73+0.05+2.75+2.75+0.05+8
     *       = 14.33；R39 那版 14.0s 少了一个 0.05s，而【R42 订正】R40 第一版 14.07 缺的**只有**
     *       B2 那 **0.26s**（不是 0.27）：它的两个 0.05s 都在，母数是当年的 AXP=0.47，
     *       0.47+0.05+2.75+2.75+0.05+8 本身就等于 14.07 ⇒ 补到 14.33 只能加 0.26。
     *       0.27 是**现行**基数（B1=0.46）下的 B2−B1，拿它补 14.07 会得 14.34。
     *       【R43 说清那 0.01】0.26 与 0.27 不是"两个世代的母数"，是同一条链上两处：
     *       物理缺额 0.27，而 14.07 这个字串里多含 0.01（当年 B1 记 0.47、R41 已订到 0.46）
     *       ⇒ 0.27 − 0.01 = 0.26。【R43 订正归属】"14.07 漏了一个 0.05s"是 **R40 定稿**写下的假账，
     *       不是 R41 写的（R41 原样携带）。【R43 复查 P0-2 补范围】那句归属的对象是**这句话本身**，
     *       证据要带文件范围跑：`git log --oneline -S"漏了一个 0.05s" -- hardware/zizhao-esp32s3/main/epd_driver.c`
     *       最早那只是 `73cbbfc`；而本文件这一份是 R43（`3c37af3`）才抄进来的（限定本文件 = 只有那一只）
     *       ⇒ 别把"R40 定稿"读成"这只文件里 R40 就有了"。不带 `--` 的同一条命令命中 3 只（`3c37af3`/
     *       `489baad`/`73cbbfc`），它是"这句话在全库出现过几次"，不是归属。），
     *   ⇒ **一次持锁最坏 ≈14.3s**（取 B；【R41 P2 措辞】本行旧版写的是"一轮最坏 ≈14.3s"，而同一个
     *   词在本注释下面"14s 这个值没有降回去"那一段里指的是"一轮 probe ≈3.53s"（同一块注释的另一档）
     *   ——同一个词在一块注释里指两个对象，
     *   跨文件做"四处一致"比对时会被读成自相矛盾。此处量的是"probe 过了还要刷白"的**整次持锁**。）
     *   **20s 的余量是 ≈5.7s**（仍写作"≈6s"），不是旧版那句"现余 3.2s"。
     * 之前几版的 10s / 16s / 15.4s / 16.8s 都是照"只算一次 init"或"AXP 只算 2.7s"或"init 只 2.25s"
     * 或"把全诊断轮和刷白轮加成一条链"给的；而除位碰那一段（R37 真机实测）外，其余段都还没有
     * 真机计时（全部是按返回码上限推的，口径标签见 `RELEASE_CLAIM_WAIT_MS` 上方那段），
     * 所以 20s 这个上限**没有跟着下调**：收窄的是**算术**（原来那个 16.8s 本身就是错的），
     * 不是预算——把预算跟着新算的 14.3s 走，等于在最坏值仍是"推的"这一前提下主动吃掉那 6s 余量。
     * 【口径更正（R31 复查顺带）】原来这句"20s 仍小于 Task WDT 的 30s，否则调用方喂不到狗"
     * 前提是错的：本机狗由 idle 喂（构建树 sdkconfig:982/983 `CHECK_IDLE_TASK_CPU0/1=y`），
     * 且我们的等待全是 `vTaskDelay`（会让出 CPU），永不触发超时；本仓库也没有任何
     * `esp_task_wdt_add()`/`esp_task_wdt_init()` **调用点**（R33 P2-4：全树对该字串的唯一文本命中
     * 就是本行注释自己，"无命中"按字面跑一遍不成立，可核的口径是"无调用点"）。
     * 20s 这个上限真正的理由是"深睡前用户
     * 愿意等多项"，不是看门狗。
     * 拿不到锁时仍要做一件事：把"配过引脚但没有应答证据"那 5 根脚连同 SPI 交还成
     * "`GPIO_MODE_DISABLE` + 内部上拉"，
     * 否则 §十五 要堵的倒灌换一条路还在。该交还内部还要再等认领令牌最多 14s
     * （`RELEASE_CLAIM_WAIT_MS`，见 epd_driver.c 上方那段分项）。【R39 P1-4 口径】这段历史里出现过
     * 的"一轮 ≈5.0s / 5.5s / 5.9s"都不再是本轮的最坏值：5.9s 那版把两条**互斥**的分支加在了一起
     * （全诊断轮才跑的 AXP 位碰+全扫 3.1s，与只有 `s_probe_round % 12 == 0` 才放行的 `epd_panel_init()`
     * 2.75s——`full_diag` 的轮号 30+60k 恒 ≡6 (mod 12)，两集合不交）。R40 重算后：全诊断轮 ≈3.1s
     * （宽读 3.3s，**不含**被动判活那 0.05s，见上面分支 A 的 R40 注）、判活放行轮 ≈3.53s（AXP 取
     * B2 的 0.73s）⇒ **一轮 probe 最坏 ≈3.53s，两轮 ≈7.1s**。【R41 P2】旧版接的那句"14s 是约 4.0 个
     * 最坏轮、余量 ≈6.9s"两处都不成立：14 ÷ 3.53 = **3.97 ⇒ 装得下 3 个完整最坏轮（10.59s，剩 3.41s）、
     * 不足 4**（4 轮要 14.12s > 14s），而 6.94s 是**两轮之后**的余量、不是"4 轮"的（4 轮是 −0.12s）。
     * （这一族数在本轮之内改过**三**次：R39 给的是 3.15 / 3.22 / 3.25 / 4.3 个 / 7.5s，它把被动段的
     *  0.05s 记到了走不到的分支 A 上、又漏记了走得到的分支 B，两支各错 0.05s、方向相反，母数还取在
     *  3.25s；R40 第一版给的是 3.1 / 3.27 / 3.3 / 4.2 个 / 7.4s，它把"放行轮"整个当成"!acked"那个
     *  子案，漏了"应答但回读没确认"那个 0.27s 的子案；R40 第二版给 3.53 却公布 3.55，那 0.02s 没有来源。
     *  前两次是同一族：**分支划分只做到一级、没做到二级**；第三次是**公布的数比自己的算式大**。）
     * 14s 这个值**没有降回去**（理由写在 `RELEASE_CLAIM_WAIT_MS` 上方：真正的对手是"抢在下一轮认领
     * 之前拿到令牌"那场赛跑，不是"一轮 + 一点余量"）。更早的 6s 只留 1.0s 余量（它按一轮 ≈5.0s 算；
     * R32 复查那版按它自己的 5.15s 给的是 0.85s——两个数当时都是推的，取宽的那头仍然不够），
     * 恰好在最坏那一窗内被用完，所以这条分支总预算 ≈34s（20s 等锁 + 14s 等令牌）。
     * 这 34s 只在"锁和令牌同时被占"那一档付，代价换成的是"倒灌防护不会整个深睡周期缺席"。 */
    if (xSemaphoreTake(s_lock, pdMS_TO_TICKS(20000)) != pdTRUE) {
        epd_pins_release_if_unverified();
        /* 这句话必须由驱动侧那三条出口之一来落实：本函数唯一能说的只是"我请求过交还"，
         * 到底交没交、为什么没交，只有 `epd_pins_release_if_unverified()` 打的那一行知道。 */
        ESP_LOGW(TAG, "eink_sleep: 显示锁 20s 拿不到，跳过面板归位；引脚是否交还、按哪个条件交的，看上一行驱动侧的 release 日志");
        return;
    }
    epd_sleep();
    s_page = PAGE_NONE;   /* 睡眠后寄存器丢配置，下次必须全刷 */
    /* 面板已进 sleep，寄存器不再生效：撤下"可用"标记，否则下一次 eink_show_* 会
     * 在沉睡的面板上做一次全刷（肉眼可见的整屏闪烁），并可能顺带把面板从睡眠里
     * 拉回来，白耗一次电。今天两个调用点之后紧跟 esp_deep_sleep_start() 所以看不到，
     * 但这个函数不能只靠"调用者一定会深睡"这个假设。这里刻意不重新挂监视：整机马上就要睡了。 */
    s_panel_ok = false;
    xSemaphoreGive(s_lock);
}
