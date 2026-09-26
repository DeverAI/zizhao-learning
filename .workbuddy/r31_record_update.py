# -*- coding: utf-8 -*-
"""R31 归档：往排查记录插入 §二十、给两处旧"已核实"段落加同轮指路、加一条 R31 指纹。
只改 hardware/20260919_墨水屏点屏排查记录.md 这一个文件；原文一律保留不删。"""
import io
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, "..", "hardware", "20260919_墨水屏点屏排查记录.md")
p = os.path.normpath(p)

s = io.open(p, encoding="utf-8").read()
before_len = len(s)

SECTION = u"""## 二十、R31 = R30 复查（第十轮对抗审查）落地，构建 `0x113b60`

R30 定稿后补走了 §19.5 第⑦条那道空上下文复查。专员给的仍是**未定稿代码**上的报告：**1 条 P0 + 3 条 P1 + 4 条 P2 + 2 条“不确定” + 7 条“做对了”**。
按 §18.1 的规矩逐条核实（先回代码 grep 它逐字引的那几行，涉及 IDF 行为的去本机 `C:\\esp\\esp-idf`（`v5.1.6`）读实际源码）：
**P0/P1 全部成立并落地；P2 四条全采纳，但它自己有一处引用错了，当场驳回**（见 20.3）。
更重大的一件事：它**推翻了我从 R28 起在四处反复引用的一条“已核实事实”**（`spi_bus_free` 不数设备），见 20.2。

### 20.1 逐条处置（行号对 R31 构建 `0x113b60` 成立）

| 编号 | 专员的说法（核实结论） | 核实依据 | R31 落地 |
| --- | --- | --- | --- |
| **P0** | `epd_busy_activity()` 两段都允许“没见过高就因连续低而 break” ⇒ 活屏可被**恒判**成 0V 钳位签名 | 逐字对 R30 版 `:194-200` 与 `:214-218`：密采 `low_run>=20`（1ms）未见过高就 `break`，慢采 `low && prev_low` 在**第 2 拍（≈20ms）**又 `break`。发 `0x12` 前面板空闲、BUSY 本就是低 ⇒ 高分辨率（50µs）那段只活了 1ms，之后只剩 10ms 采样去找一个“几毫秒宽”的高沿，而 R30 刚把判据收成“高也要连续两拍”（2×10ms=20ms > 脉宽），**数学上凑不齐** | 两处 `break` 删掉：低凑满只记 `seen_low`，密采跑满自己的 50ms，慢采走到 1800ms 上限才定案（`:214-224`、`:236-246`）。判失败的轮从 ≈21ms 变成 ≈1.85s —— 这正是 §十一-4 持锁时长表**本来就按 1.85s 预算**的那一段，20s 锁等待的算术不变，只是失败轮第一次真花满它 |
| **P1-1** | `passive BUSY sample (rail unconfirmed, …)` 在**电轨已确认**时也照打，恰好在“电池接上、闸门第一次真打开”那天起每轮朝“电轨没到手”打一行 | 逐字对 `:478`（R30 版）无条件字面量 + 调用点 `:564` 在 `rail_off==false` 时每轮执行；而【〇】第 53-54 行**教的正是按这两行的出现频率判案** | `epd_busy_passive_low(bool rail_off)`（`:491`），括号分两档：`rail unconfirmed` / `rail confirmed-by-readback（仅指 0x90 那一位回读一致，不等于 ALDO3 已证实）`（`:516-521`） |
| **P1-2** | “不重复 add device”这句话的**下一行**就是 add device | 逐字对 R30 版 `:352`（无条件打）与 `:354`（`if (!s_spi)` 再 add）；`spi_bus_add_device` 的 nomem 分支 `free(dev); return ESP_ERR_NO_MEM` 在本机 `gpspi/spi_master.c:485-493` ⇒ “总线在、句柄 NULL”是可达状态 | 该行按 `s_spi` 拆两档（`:352-366`），第二档明说“下面重新 add device + 复用未拆掉的总线不会重做 SCLK/MOSI 引脚矩阵连接” |
| **P1-3** | 兜底释放抢不到认领令牌时**直接 return**，而调用方紧接着就深睡 ⇒ “等它结束”没人兑现，倒灌防护在最坏那一窗静默跳过 | 逐字对 R30 版 `:802-806` + `eink_display.c:509-511`（20s 超时分支唯一一次机会）；对面那次认领覆盖整轮 probe（最坏 ≈5s），恰好是把 CS/DC/RST 配成输出驱动的那段 | 改成最多再等 `RELEASE_CLAIM_WAIT_MS`=6000ms（`:31-38`、`:866-879`）：等到打 `release: 等了 %dms 才拿到认领令牌`，等不到才放弃并把“本轮倒灌防护未生效”写进行为描述。**顺带查出我原来的立论写错了**：注释说“20s 小于 Task WDT 30s 否则喂不到狗”，而本机 `CONFIG_ESP_TASK_WDT_CHECK_IDLE_TASK_CPU0/1=y`（构建树 sdkconfig:982/983）且全仓库无 `esp_task_wdt_add` ⇒ 狗由 idle 喂，`vTaskDelay` 永远不会触发它；那句“看门狗”因果是假的，已在 `eink_display.c:506-510` 改成真实理由（深睡前愿意等多项） |
| P2-1 | 第二条 `panel silent after SWRESET` 括号里枚举“一直是高 / 单拍尖峰”**覆盖不全** | 成立：`saw_low=1` 且 50ms 之后才来成对的高、到 1800ms 仍高 ⇒ `low_no_high=false` 走这一行，两种都不是 | 两条合并成一条格式串 + 行尾 `(saw_low=%d saw_high=%d)`（`:279-282`），散文不再负责枚举；【〇】里给了 1/0、0/1、1/1、0/0 四档读法 |
| P2-2 | `epd_pins_release()` 上方那段“`spi_bus_free` 不数设备”的“5.1.6 实读”**引用与结论都不准**；另称 `check_trans_valid` 的调用点在 `:1045` 而非 `:1044` | **主结论成立、附带的一条引用不成立**：`spi_bus_free` 本体在 `gpspi/spi_common.c:875`（旧注释写 `spi_master.c:300`，那是**另一个函数** `spi_master_deinit_driver`，:295-300），它 :885-887 调 `destroy_func`，SPI 主机在 `spi_master.c:270` 注册的正是它，后者 :297 `SPI_CHECK(host->device[x]==NULL, "not all CSses freed", ESP_ERR_INVALID_STATE)`，返回值直接 `return err`（:906）⇒ **确实数设备**。但本机 `:1044` 逐字就是 `ret = check_trans_valid(handle, trans_desc);`（`:1043` 才是 `ticks_to_wait == portMAX_DELAY`）⇒ 它这条改议错了 | 注释整段重写（`:803-813`），`bus_s` 的 `INVALID_STATE` 档改成把**两种**来源都念出来（`:816`）。它错的 `:1045` 不采纳，我的调用链保留 |
| P2-3 | “只把 GPIO3 配成输入 + 上拉，SPI/CS/DC/RST 一根都不碰”与同函数 `:495` 的 `epd_pins_release()` 矛盾；`epd_driver.h:27` 的“幂等地备好 SPI/GPIO”也不再成立 | 成立：旁证阶段确实先把 5 根脚交还（每根仍留 ≈58µA 上拉漏电），probe 也可能以“已交还”收尾 | 注释改成“本函数自己只配 GPIO3、**不驱动**任何一根；旁证阶段是先整套交还再借上拉读”（`:460-464`）；头文件补“调用过一次≠引脚还配着”（`epd_driver.h:26-28`） |
| P2-4 | `if (i >= 3 && !wit_spi)` 用魔数 3 表达“后两根是 SCLK/MOSI”，与 `kWit[]` 的**排列**隐式耦合 | 成立：重排数组就会把仍归控制器的两根配成输入，重演 §19.1 P1-2 那个“再也接不回 SPI”的静默故障 | 改成按脚号判：`if (!wit_spi && (kWit[i]==EPD_SCLK_PIN \\|\\| kWit[i]==EPD_MOSI_PIN))`（`:541-546`） |

### 20.2 它推翻了我一条“已核实的事实”（这一条比上面所有都贵）

从 R28 起我在**四处**写着“`spi_bus_free` 在这版**不**数还有几个设备挂着，`INVALID_STATE` 只代表这台控制器本来没装总线”，并把它列进“已在本机 5.1.6 源码核过”的清单（§17.4 表 P1-5 行、§19.3 第 2 段、`updates/20260921_墨水屏收尾R29.md:29`、`dev_log/20260921.md:184/:208`、以及 `烧录须知` 的 ②）。
**错在只看了一个函数**：外层 `spi_bus_free` 的入口检查确实只有 `bus_ctx==NULL`，但它把“拆设备”这件事交给了自己注册的 `destroy_func`，那条检查在**下一层**。这次是专员去读 `spi_master.c:270/297` 才揪出来的。
⇒ 更正后的口径（已写进 `epd_driver.c:803-813` 与【〇】②）：`spi_bus_free` 的 `ESP_ERR_INVALID_STATE` 有**两种**来源；且失败那条路径上它照样 free `bus_ctx` 并置 NULL（:904-905），却不 free 主机驱动自己的 `bus_driver_ctx` ⇒ “半个拆干净”状态。我们今天走不到第二种（只有 `spi_bus_remove_device` 回 `ESP_OK` 才让它跑）⇒ **行为不变，判读口径变了**。旧四处原文一律保留不删，本节是指路。

### 20.3 报告自己也有一处错（就地驳回，不采纳）

它写“另：`:796` 的 `check_trans_valid`(:1044) 实为 `:1045`（:1044 是 `ticks_to_wait == portMAX_DELAY` 那句）”。本机逐行读数：`:1040` 是 `spi_device_polling_start` 函数头，**`:1043`** 才是 `SPI_CHECK(ticks_to_wait == portMAX_DELAY, …)`，**`:1044`** 逐字是 `ret = check_trans_valid(handle, trans_desc);`，`:1045` 是 `if (ret!=ESP_OK) return ret;` ⇒ 我原有的 `:1118 → :1121 → :1044 → :767` 调用链**是对的**，它这条改议不采纳。
这是“报告每条都要核实”的又一次实际收益：本轮它 12 条里 11 条成立、1 条错；那条错的照改就会把一段正确引用改歪。

### 20.4 它 7 条“做对了”里我重算过的部分（不照单全收）

它独立复核并给了本机行号的：① 引号奇偶扫描全部命中在注释里（本轮我又跑了一遍 `awk`，`main/*.c *.h` 无字面量截断）；② `CONFIG_FREERTOS_HZ=1000`、`TASK_WDT_TIMEOUT_S=30` 取自**构建树** `C:/esp/zproj/sdkconfig:1156/981`（不是 defaults）；③ `BUSY never went high … low for %dms straight` 那句“没说谎”（`seen_high<0` 分支要求此前每拍都是低）；④ 认领令牌两条路径都“抢不到就 return、抢到则无条件 `store(false)`”，`probe_attempt` 内无 `ESP_ERROR_CHECK`/assert ⇒ 不存在拿了不还的路径。
**其中 ④ 在本轮加了 6s 重试之后必须重算**（这是 P1-3 自己新引入的风险面）：失败那次 `atomic_exchange` 也会把令牌**写成 true**，会不会留一个没人清的 true？不会——只有在对侧仍持有（读到 true）时我们的写才改变不了它的含义，对侧收尾必 `store(false)`；若对侧已先放开，则我们那次 exchange 返回 false ⇒ 当场认领成功、由我们自己 `store(false)` 收尾。两条都不留悬挂 ⇒ `probe skipped` 不会变成永久自锁（已写进 `epd_panel_probe()` 上方注释 `:657-661`）。①②③复核一致，采纳。

### 20.5 R31 构建与状态（诚实版）

- 构建 `0x113b60`（**0 warning / 0 error**；R30 `0x113790`、R29 `0x113500`），md5 `1e28be5890eaffb0a6924628ce17e77a`（**拷贝后重跑**：`backups/r31_20260921_033823/` 与 `C:\\esp\\zproj\\build` 两处一致，备份内 `main/` 与仓库 `diff -r` 无差异），构建日志 `C:\\esp\\build_r31.log`。
- 本轮我自己引进、被编译器当场抓住的一处：新格式串写了 `%d … %d` 却只传了三元表达式，漏两个实参 ⇒ `-Werror=format=` 直接失败（`build_r31.log` 第一次跑）。同类（改了签名/文案却没回头核实参）已第 4 次，见 FreqErr。
- **仍未烧录**：03:38 第十一次复查 `ports.ps1` 仍只有 COM3/4/5/6 ⇒ **R23~R31 一律未进过板子，屏亮不亮至今没有一次肉眼确认**，本轮不播完成提示音。
- R31 新改的分支同样**一条都没走过**：`rail confirmed-by-readback` 档、`总线仍在但**无句柄**` 档、`release: 等了 Nms 才拿到认领令牌`、`release skipped … 等了 6000ms`、带 `(saw_low=… saw_high=…)` 的 `panel silent`。连同前几轮，未经执行的“防假成功/防误判”出口现在 **12 行**。
- 仍未做（点名）：①`bit2↔ALDO3` 映射未证实（第 51 条）；②`other=%d` 不点名具体错误（第 52 条）；③`eink_show_*` 的 `portMAX_DELAY` 未改（第 54 条）；④`ENABLE_EINK_PARTIAL` 仍 0，局刷两道闸走不到；⑤全部时间门限（20s/6s/40ms/1ms/2ms/5ms/10ms/20ms/50ms/100ms/300ms/1.8s/8s）**无一条硬件数据**；⑥`RELEASE_CLAIM_WAIT_MS`=6s 照“一轮 probe 最坏 ≈5s”推，而那个 5s 自己也没实测；⑦`epd_sleep()` 里那次 `epd_pins_release()` 仍**不**走认领令牌（专员把它列进“不确定”，与我 todo 第 60 条同源：今天两个 `eink_sleep()` 调用点都在 app_main 单任务里 —— `main.c:173`（`graceful_shutdown()`，全仓唯一调用点在 `main.c:388` 主循环内）与 `main.c:302` ⇒ 凑不出第二个并发方；将来若有任何别的任务调 `eink_sleep()`，两条 `spi_bus_remove_device` 会撞 `spi_master.c:521` 的 assert）；⑧R31 自身尚未经下一轮空上下文复核（本轮末尾补走）。

"""

anchor = u"## 附：目前已就绪的软件能力"
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(anchor, SECTION + anchor)

# 同轮指路（原文保留）
a2 = u"| **P1-5** `spi_bus_free` 的 `INVALID_STATE` 语义与我们的判据相反"
assert s.count(a2) == 1
s = s.replace(a2, u"| **P1-5**（**本行的“不数设备”已被 §20.2 推翻，原文保留**） `spi_bus_free` 的 `INVALID_STATE` 语义与我们的判据相反")

a3 = u"6 处 5.1.6 行为（pull 枚举同值、`spi_bus_free` 不数设备"
assert s.count(a3) == 1
s = s.replace(a3, u"6 处 5.1.6 行为（pull 枚举同值、`spi_bus_free` 不数设备（**这一条 R31 复查推翻，见 §20.2**）")

# R31 指纹一条，插在 R30 指纹那条之后
lines = s.split(u"\n")
idx = [i for i, ln in enumerate(lines) if ln.startswith(u"- **R30 又改了三处指纹**")]
assert len(idx) == 1, idx
R31_BULLET = (u"- **R31 再改四处指纹 + 推翻一条既有事实**（认版本以本节为准，§20.1）："
              u"`passive BUSY sample (rail unconfirmed|rail confirmed-by-readback…, 其余脚未驱动)`（括号分两档，旧版一律印 unconfirmed）、"
              u"`spi_bus_initialize: 总线仍在（上一轮未拆）→ 复用句柄，不重复 add device` 与 `…但**无句柄** → 下面重新 add device…`（同一返回码的两档）、"
              u"`release skipped: … 等了 6000ms 仍未交回认领令牌 → 引脚留在当前状态进深睡（本轮倒灌防护未生效）` 与新增的 `release: 等了 Nms 才拿到认领令牌`、"
              u"`panel silent after SWRESET: … (saw_low=%d saw_high=%d)`（取代括号里的散文枚举）。"
              u"判活本身也变硬：两段采样都不再“没见过高就提前退出”⇒ 这一行现在意味着“看了整整 1.85s 都没有合格的高”。"
              u"**另：本文件 R28~R30 反复引用的“`spi_bus_free` 不数设备”是错的，见 §20.2。**")
lines.insert(idx[0] + 1, R31_BULLET)
s = u"\n".join(lines)

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("record updated: %d -> %d chars" % (before_len, len(s)))
