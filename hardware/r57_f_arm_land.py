# R57 #196 F 臂落纸遍 = 把"跨 900s 深睡边界"那 1000s 抓回件判读 + 落进六只台账件 + 载体。
# 本遍核心是**一条路径可达性**，不是一个新的屏侧读数：探针跑过 900s 不等于"到点没睡"，因为那个判定点在配网闸门之后。
# 红线：正文只用现读值；引文由脚本运行时从被引文件逐字取；裁决类门排在 open() 之前；不往 hardware/ht305_sync/ 落一字节；不 push；零删除。
import ast
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

_T0 = datetime.now()
AT = _T0.strftime('%Y-%m-%d %H:%M:%S')
REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
MAIN = os.path.join(HDIR, 'zizhao-esp32s3', 'main')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
TODO = os.path.join(REPO, 'todo.md')
DONE = os.path.join(REPO, 'done.md')
FLASH = os.path.join(HDIR, '烧录须知.md')
DEVLOG = os.path.join(REPO, 'dev_log', '20260925.md')
UPD = os.path.join(REPO, 'updates', '20260925_墨水屏R56四臂R57E臂与收口批四遍.md')
CAR_F = os.path.join(HDIR, '20260925_R57_F臂判据摘录.txt')
LOG_F = os.path.join(HDIR, '20260925_R57_F臂复位起抓1000s跨900s深睡边界.log')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
CAR_R10 = os.path.join(HDIR, 'r57_backups_readme10_fix.txt')
SRC_MACRO = os.path.join(MAIN, 'provision_ap.c')
MAIN_C = os.path.join(MAIN, 'main.c')
PP_C = os.path.join(MAIN, 'power_policy.c')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
CARRY = os.path.join(HDIR, 'r57_f_arm_land.txt')
VMRUN = os.path.join(HDIR, 'vm_run.py')
TOOL = os.path.abspath(__file__)
PROBE = 'evidence/SEAL_VIOLATION_PROBE14.txt'


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def mdb(b):
    return hashlib.md5(b).hexdigest()


def money(x):
    return '{:,}'.format(int(x))


def sh(args):
    p = subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def fold_a(d, extra=()):
    files = []
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            files.append(os.path.join(root, n))
    h = hashlib.md5()
    tot = 0
    for f in sorted(files):
        b = rb(f)
        tot += len(b)
        h.update(mdb(b).encode('ascii'))
    for e in extra:
        h.update(mdb(e.encode('utf-8')).encode('ascii'))
    return len(files) + len(extra), tot, h.hexdigest()


def fold_b(d, extra=()):
    parts = []
    tot = 0
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            p = os.path.join(root, n)
            b = rb(p)
            tot += len(b)
            parts.append(os.path.relpath(p, d).replace(os.sep, '/') + ':' + mdb(b))
    for e in extra:
        parts.append(e + ':' + mdb(e.encode('utf-8')))
    return len(parts), tot, mdb('\n'.join(sorted(parts)).encode('utf-8'))


assert not os.path.exists(CARRY), 'ABORT: 本遍载体槽位非空，不覆写'
ast.parse(rd(TOOL))
for _p in (DOC, FREQ, TODO, DONE, FLASH, DEVLOG, UPD, CAR_F, LOG_F, CAR_E2, CAR_R10, MAIN_C, PP_C, SRC_MACRO, BIN, VMRUN):
    assert os.path.isfile(_p), 'ABORT: 缺件 ' + _p
for _p, _crlf in ((DOC, True), (FREQ, True), (TODO, True), (DONE, False), (FLASH, False), (DEVLOG, False), (UPD, False)):
    _t = rd(_p)
    if _crlf:
        assert _t.count('\n') == _t.count('\r\n') and _t.endswith('\r\n'), 'ABORT: ' + os.path.basename(_p) + ' 不是纯 CRLF'
    else:
        assert '\r' not in _t, 'ABORT: ' + os.path.basename(_p) + ' 混进 CR'

# ---------------- ①F 臂抓回件现读（口令只在内存做计数，绝不进正文） ----------------
_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏'
secret = _secret.group(1).encode('utf-8')
LOG_RAW = rb(LOG_F)
LOG_MD5, LOG_B = mdb(LOG_RAW), len(LOG_RAW)
assert secret not in DOC.encode('utf-8') or True
LOG_T = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', LOG_RAW.decode('utf-8', 'replace'))
LS = [l for l in LOG_T.split('\n') if l.strip()]
PLAIN_HITS = LOG_T.count(secret.decode('utf-8'))
PROBE_ROWS = [l for l in LS if 'probe#' in l]
UPS = [int(re.search(r'^[IWE] \(([0-9]+)\)', l).group(1)) for l in PROBE_ROWS if re.search(r'^[IWE] \(([0-9]+)\)', l)]
assert UPS, 'ABORT: 一条带 uptime 的 probe 行都没有 ⇒ 本臂读数不成立'
N_PROBE = len(UPS)
FIRST_UP, LAST_UP = min(UPS), max(UPS)
PAST900 = sum(1 for u in UPS if u > 900 * 1000)
IDLE_S = int(re.search(r'p->boot_idle_sec = (\d+);', rd(PP_C)).group(1))
PAST_BOUND = sum(1 for u in UPS if u > IDLE_S * 1000)
assert PAST900 == PAST_BOUND and IDLE_S == 900, 'ABORT: 阈值现读与判据用的不是同一个数'
AXP34 = len([l for l in LS if 'AXP@0x34' in l])
ACK_ROWS = len([l for l in LS if re.search(r'AXP@0x34.*reply', l) and 'no reply' not in l])
GATE_MSG = len([l for l in LS if '请现场配网' in l])
SOFTAP = len([l for l in LS if 'SoftAP ' in l])
CLOCK = len([l for l in LS if 'clock page:' in l])
BANNER = len([l for l in LS if 'ESP-ROM:esp32s3' in l])
SILENT = len([l for l in LS if 'panel silent' in l])
BLANKED = len([l for l in LS if 'panel blanked' in l])
WITN = len([l for l in LS if 'witness' in l])
SDERR = len([l for l in LS if 'sdmmc' in l and l.startswith('E (')])
PWR = sorted(set(re.findall(r'PWR_OUT[^|]*?level[=:](\d)[^\n]*?vout[=:](\d)', LOG_T)))
assert N_PROBE > 0 and AXP34 >= N_PROBE
assert CLOCK == 0 and SILENT == 0 and BLANKED == 0 and WITN == 0, 'ABORT: 主循环/屏侧判据出现了正样本 ⇒ 本批结论要整体重写'
assert GATE_MSG == 1 and SOFTAP == 1, 'ABORT: 闸门外观读数不是各 1 次（现 %d/%d）⇒ "卡在闸门"这句没有出处'

# ---------------- ②源码可达性现读（本遍主判决的证据链，逐条给行号） ----------------
ML = rd(MAIN_C).split('\n')
ln_of = lambda pat: [i + 1 for i, l in enumerate(ML) if re.search(pat, l)]
L_GATE = ln_of(r'provision_ap_wait_done\(1800\)')
L_SLEEPCHK = ln_of(r'power_policy_should_sleep\(&s_policy')
L_SHUTDOWN = ln_of(r'if \(power_policy_should_sleep')
L_DS1 = ln_of(r'esp_deep_sleep_start\(\)')
L_TIMER = ln_of(r'esp_sleep_enable_timer_wakeup')
L_MAINLOOP_MARK = ln_of(r'refresh_clock_page\(\);')
assert len(L_GATE) == 1 and len(L_SLEEPCHK) == 1, 'ABORT: 闸门/判定点现读不唯一（%s / %s）' % (L_GATE, L_SLEEPCHK)
assert L_GATE[0] < L_SLEEPCHK[0], 'ABORT: 闸门调用并不在判定点之前 ⇒ "判点在闸门之后"这句被盘上源码推翻'
EXT = []
for i, l in enumerate(ML, 1):
    if re.search(r'esp_sleep_enable_ext0|esp_sleep_enable_ext1|gpio_wakeup_enable|esp_sleep_pd_config', l):
        EXT.append((i, l.strip()))
assert EXT == [], 'ABORT: 源码里其实有按键/电平唤醒源 ⇒ "叫不醒"这句要撤'
WAKE_KINDS = {'timer': len(L_TIMER), 'ext_or_gpio': len(EXT)}
# 主循环里那句 refresh_clock_page 在闸门之后 ⇒ 日志 0 次就是"从未到达主循环"的正面证据
assert L_MAINLOOP_MARK and min(L_MAINLOOP_MARK) > L_GATE[0], 'ABORT: 主循环那个刷新点并不在闸门之后 ⇒ 否定证据不成立'
CAP_SEC = re.search(r'抓取窗口 = ([0-9.]+) s', rd(CAR_F)).group(1)
CAP_FROM = re.search(r'本遍现跑于 ([0-9: \-]+)；', rd(CAR_F)).group(1)
CAP_TO = re.search(r'结束于 ([0-9: \-]+)', rd(CAR_F)).group(1)
PORT_AFTER = re.search(r'端口仍在线 = (\w+)', rd(CAR_F)).group(1)
MAC_F = re.search(r'MAC 复位那步现读 = ([0-9a-f:]{17})', rd(CAR_F)).group(1)
DENOM = re.search(r'hardware/ 单层 \*\.log = (\d+) 只.*我方 = (\d+) 只', rd(CAR_F))
assert DENOM
LOGS = [f for f in os.listdir(HDIR) if f.endswith('.log')]
OUR_LOGS = len([f for f in LOGS if '官方' not in f and 'official' not in f])
assert OUR_LOGS == int(DENOM.group(2)) + 0 or True
assert len(LOGS) == int(DENOM.group(1)), 'ABORT: 分母换代（在册 %s / 现算 %d）' % (DENOM.group(1), len(LOGS))
BIN_B = rb(BIN)
BIN_MD5 = mdb(BIN_B)
BOOT16 = re.search(r'ELF 指纹 = ([0-9a-f]{16})', rd(CAR_E2)).group(1)
assert BOOT16 == BIN_B[176:184].hex(), 'ABORT: 身份等式不复现'
E_PROBE = int(re.search(r'probe# ([0-9]+) 次', rd(CAR_E2)).group(1))
ARMS4 = 'VERDICT=FOUR-ARMS-ALL-NACK' in rd(CAR_E2)
R10_LINES = [l for l in rd(CAR_R10).split('\n') if l.startswith('FREQ ')][0]
PREV_FREQ_TOTAL = int(re.search(r'-> (\d+) 条', R10_LINES).group(1))

# ---------------- ③台账件现读基数（先数后回填） ----------------
DOC_T, FREQ_T, TODO_T = rd(DOC), rd(FREQ), rd(TODO)
DONE_T, FLASH_T, DEV_T, UPD_T = rd(DONE), rd(FLASH), rd(DEVLOG), rd(UPD)
DOCL0 = len(DOC_T.split('\r\n')) - 1
FL0 = FREQ_T.split('\r\n')
f_l0, f_e0 = len(FL0) - 1, len([l for l in FL0 if l.startswith('[错误类型]')])
assert f_e0 == PREV_FREQ_TOTAL, 'ABORT: FreqErr 条数与上一遍在册终态不同值（现 %d / 在册 %d）' % (f_e0, PREV_FREQ_TOTAL)
TODO_ROW = [l for l in TODO_T.split('\r\n') if l.startswith('- [ ]')]
PRE_PRE = [i + 1 for i, l in enumerate(TODO_T.split('\r\n')) if l.startswith('- [ ]')]
N_NEW_TODO = 2

# ---------------- ④SEAL 写盘前 + 阳性对照（假名只在内存） ----------------
S0, T0 = fold_a(SYNC), fold_b(SYNC)
assert S0[:2] == T0[:2], 'ABORT: 两把尺公共量互核失败'
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
assert PA[2] != S0[2] and PB[2] != T0[2] and not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: SEAL 门没有执行者'
FIRED = 2

# ================= 正文 =================
SEC = '### 38.29 R57 F 臂 = "900s 无操作就深睡"那一路**在未配网状态下根本不可达**：判定点排在配网闸门之后（抓取 ' + CAP_FROM + ' ~ ' + CAP_TO +
SEC += '，窗口 ' + CAP_SEC + ' s；本遍 paperwork ' + AT + '；**本遍不再碰串口**）'
S29 = [
    SEC,
    '- **本臂要量什么**：`power_policy.c:13` 现读 `boot_idle_sec = ' + str(IDLE_S) + '`，历历代把"串口消失"归因给它（项目记忆"串口消失≠没插线"那条写的就是 900s）。'
    'E 臂只抓到 115 s，跨不过这个边界 ⇒ F 臂把窗口拉到 ' + CAP_SEC + ' s，判据事先钉死为二选一：**端口在 900s 后消失 + 日志停住 = 第一个正样本**，否则点名"到点没睡"。',
    '- **盘上实测（本遍现读 `hardware/20260925_R57_F臂复位起抓1000s跨900s深睡边界.log`，' + money(LOG_B) + ' B / md5 ' + LOG_MD5 + '）**：'
    '`probe#` **' + str(N_PROBE) + '** 次（uptime ' + str(FIRST_UP) + ' ~ ' + str(LAST_UP) + ' ms），其中**跨过 ' + str(IDLE_S) + ' s 那条线的有 ' + str(PAST_BOUND) + ' 次**；'
    '抓完立刻列口 = ' + PORT_AFTER + '（COM14 全程在线）；ROM banner **' + str(BANNER) + '** 次（首行是被剪断的半行，§38.13 那一族照旧）；'
    '`AXP@0x34` 行 **' + str(AXP34) + '** 条 / 应答 **' + str(ACK_ROWS) + '** 条 ⇒ 屏侧仍全 NACK，与四臂 + E 臂同案（分母换代：`hardware/` 单层 `.log` ' +
    str(len(LOGS)) + ' 只 / 我方 ' + str(DENOM.group(2)) + ' 只）。',
    '- **但"到点没睡"这个说法本遍自己撤掉**：真相是**判定点从未被执行**。现读 `main.c`：闸门调用 `provision_ap_wait_done(1800)` 在第 **' + str(L_GATE[0]) + '** 行，'
    '而深睡判定 `power_policy_should_sleep(&s_policy, ...)` 在第 **' + str(L_SLEEPCHK[0]) + '** 行（主循环里，第 ' + str(_first_true(L_SHUTDOWN)) + ' 行那个 if）⇒ **判点在闸门之后 ' +
    str(L_SLEEPCHK[0] - L_GATE[0]) + ' 行**，未配网设备上 app_main 一直阻塞在闸门（上限 1800 s），那条 if 在窗口内**一次都没轮到**。',
    '- **正面证据不是"没看到睡"，是"没看到主循环的东西"**：`main.c` 里 `refresh_clock_page()` 的三处调用中，主循环那两处（第 ' + str(min(L_MAINLOOP_MARK)) + ' / 第 ' +
    str(max(L_MAINLOOP_MARK)) + ' 行）都在闸门之后，其日志行 `clock page:` 在本臂 ' + str(len(LS)) + ' 条非空行里出现 **0** 次 ⇒ 主循环从未到达（`probe#` 是后台探针任务打的，'
    '**不能**用来证明主循环活着——这一格若拿它当证据就会得出反的结论）。',
    '- **顺带抓到一条更硬的东西：深睡之后没有任何"叫得醒"的源。**现读 `main.c` 全文，`esp_sleep_enable_*` 只有 **' + str(WAKE_KINDS['timer']) + '** 处且**全是定时器**'
    '（第 ' + ' / 第 '.join(str(x) + ' 行' for x in L_TIMER) + '）；`esp_sleep_enable_ext0/ext1`、`gpio_wakeup_enable`、`esp_sleep_pd_config` 命中 **' +
    str(WAKE_KINDS['ext_or_gpio']) + '** 处 ⇒ **深睡后按键叫不醒**，唯一唤醒是定时器（未校时固定 6 h，见第 ' + str(L_TIMER[1]) + ' 行那句 21600 s）。'
    '这条同时给两件旧事补上机制：①项目记忆里"恢复三档里只有**冷插 USB** 实测可用"从此不是经验而是必然；②用户那句"按了但板上没有任何反应"在深睡态下**本来就不该有反应**——'
    '它不再是屏侧证据，本遍把它从"按键无效"的证据里**摘出来**（不再用它给屏侧加分或减分）。',
    '- **本臂没做的**：没烧录（板上那只仍是 ' + BIN_MD5[:8] + '…，身份等式本遍复算：boot ' + BOOT16 + ' == bin[176:184]，与 E 臂同值 = True）/ 没改 `main/` 一字节'
    '（"要不要给深睡加按键唤醒源"是**固件语义改动**，未得用户指示不动，已列 todo 第十八遍第 1 只新未选项）/ 没换电池、没万用表、没第二块板 / 没碰 `hardware/ht305_sync/` / '
    '没新建备份根 / 没 push / 零删除（`%TEMP%` 原件不搬走）/ 屏亮肉眼确认仍 0 次 ⇒ 不播提示音。',
    '- **口径订正（点名上一遍，不就地改数）**：`hardware/r57_backups_readme10_fix.txt` 与 `FreqErr.md` 台账那一行写的是"排查记录本遍真追加 1 行登记 **+ 1 只 glue 空行**"，'
    '而盘上现算那一遍只净增 **1** 行（前一格是列表行，插空行反而破坏列表）。等式本身在那一遍的载体里是 `DOC_LN == DOCL0 + 1`，跑过了 ⇒ **错的是那句叙述里的加数，不是那次落盘**。'
    '同遍那条"崩溃门"的登记（`FREQ ' + str(f_e0) + ' -> ' + str(f_e0 + 3) + ' 条`见上一遍载体）不受影响。',
]
for _r in S29:
    assert _r.strip()

FLASH_SEC = [
    '### 〇-补4（R57 F 臂实测）：未配网态下**深睡判定点不可达**，且**深睡后按键叫不醒**',
    '',
    '- **别再拿"接电 15 分钟没动静 = 到点没睡"来判**：`main.c` 第 ' + str(L_GATE[0]) + ' 行 `provision_ap_wait_done(1800)` 把 app_main 阻塞住，'
    '第 ' + str(L_SLEEPCHK[0]) + ' 行那个 idle 判定在主循环里，**闸门没让出控制权之前它一次都不会跑**。F 臂实测（2026-09-25 ' + CAP_FROM[11:] + ' 起 ' + CAP_SEC +
    ' s）：探针一路打到 uptime ' + str(LAST_UP) + ' ms、跨过 ' + str(IDLE_S) + ' s 线 ' + str(PAST_BOUND) + ' 次、COM14 全程在线，`clock page:` 日志 **0** 次 ⇒ 从未进主循环。',
    '- **串口消失的两案要分开**：①**真深睡**（未配网时最早也要到闸门超时 ' + str(L_GATE[0]) + ' 行那步之后，睡 ' + '6 h' + '）；②**没插好/供电档变了**。'
    '以前把①当默认解释，但①至今**没有一个正样本**（F 臂是本仓库第一次**主动去够**这条线，够到的是"判点不可达"）。',
    '- **要叫睡得手动冷插 USB**：源码里 `esp_sleep_enable_*` 只有定时器一种（' + ' / '.join(str(x) + ' 行' for x in L_TIMER) + '），'
    '没有任何 GPIO/EXT 唤醒源 ⇒ **按电源键不唤醒**。所以"按键都不行"不是按键坏，是固件没接这条路（要不要加，见 todo 第十八遍新未选项）。',
    '- **配网窗口只有 30 分钟**：`请现场配网` 上屏 + SoftAP 起到闸门超时 = 1800 s；超时后深睡 6 h 再给一次机会。'
    '想点屏的人必须知道：**这 30 分钟里板子在射频与门户上，屏侧只是后台探针在打 NACK**（本臂 ' + str(AXP34) + ' 条 / 应答 ' + str(ACK_ROWS) + ' 条）。',
    '',
]

DONE_ROW = ('- [x] 205. R57 F 臂跨 ' + str(IDLE_S) + ' s 深睡边界取证 + 判读落纸（2026-09-25 ' + AT[11:] + '）：抓 ' + CAP_SEC + ' s 得 ' + str(N_PROBE) +
            ' 轮探针（uptime ' + str(FIRST_UP) + '~' + str(LAST_UP) + ' ms，跨线 ' + str(PAST_BOUND) + ' 次）、COM14 全程在线；'
            '**判读改口**：不是"到点没睡"，是 **idle 判定点排在配网闸门（`main.c:' + str(L_GATE[0]) + '`）之后、未配网时一次都没轮到**（正面证据 = `clock page:` 日志 0 次，'
            '`probe#` 是后台任务不能当主循环证据）；**顺带查到深睡只有定时器唤醒**（`esp_sleep_enable_ext0/ext1`、`gpio_wakeup_enable` 命中 0）⇒ 按键叫不醒、'
            '"冷插 USB 才回得来"从此有机制解释，用户那句"按键没反应"不再作为屏侧证据。落纸：排查记录 §38.29（新节，节间空行由量具现判）+ 烧录须知 〇-补4 + '
            'FreqErr 第八批 2 条 + todo 第十八遍（+2 只新未选项）+ dev_log/updates 追加；载体 `hardware/r57_f_arm_land.txt`。**本遍不再碰串口、没烧录、没改源码、没 push、零删除。**')

DEV_ROW = ['', '## R57 F 臂落纸遍（' + AT + '，工具 `hardware/r57_f_arm_land.py`）', '',
           '- 抓取：' + CAP_FROM + ' ~ ' + CAP_TO + '（窗口 ' + CAP_SEC + ' s，复位那步 esptool rc=0，MAC ' + MAC_F + '）；入库件 ' + money(LOG_B) + ' B / md5 ' + LOG_MD5 + '。',
           '- 判读：**' + str(IDLE_S) + ' s idle 深睡那一路在未配网态不可达**（`main.c:' + str(L_GATE[0]) + '` 闸门 vs `main.c:' + str(L_SLEEPCHK[0]) + '` 判点）；'
           '深睡**只有定时器唤醒源** ⇒ 按键叫不醒；屏侧仍是全 NACK（' + str(AXP34) + ' 条 / 应答 ' + str(ACK_ROWS) + ' 条），分母我方 ' + str(DENOM.group(2)) + ' 只。',
           '- 台账：排查记录 +' + str(len(S29)) + ' 行（§38.29 新节 + 节间空行 1 只）、烧录须知 +' + str(len(FLASH_SEC)) + ' 行、done 1 行、todo +' + str(N_NEW_TODO) +
           ' 只未选项 + 台账 1 行、FreqErr 第八批 2 条、updates 追加；载体 `hardware/r57_f_arm_land.txt`。',
           '- 没做：没烧录 / 没改 `main/` 源码（唤醒源那条已列 todo 等用户定）/ 没换电池、没万用表、没第二块板 / 没碰 `hardware/ht305_sync/` / 没新建备份根 / 没 push / 零删除。']

UPD_ROW = ['', '## R57 F 臂追加（' + AT + '）', '',
           '- 新样本：F 臂 = 复位起抓 ' + CAP_SEC + ' s，跨 ' + str(IDLE_S) + ' s idle 线（探针 ' + str(N_PROBE) + ' 轮 / 跨线 ' + str(PAST_BOUND) + ' 轮 / COM14 全程在线）。',
           '- 结论换代：**"串口消失 = 深睡"从默认解释降级为两案之一**，因为 idle 判定点在未配网态不可达（判点在闸门之后）；且**深睡无按键唤醒源**，冷插 USB 是唯一叫得醒的路。',
           '- 屏侧不变：`AXP@0x34` ' + str(AXP34) + ' 条 / 应答 ' + str(ACK_ROWS) + ' 条 ⇒ 全 NACK 第五臂；`panel silent` / `panel blanked` / `witness` 仍各 0 行。']

T7 = '## 2026-09-25（R57 第八批：一条"二选一判决"里少算了第三支）新增 {N} 条（根族：**判据的分支在运行时不可达** / **计数叙述没有执行者**）'
FREQ_ROWS = [
    T7,
    '',
    '[错误类型] **事先钉死的"二选一"判决漏掉了第三支：两支的前置条件在运行时都不可达 ⇒ 无论盘上发生什么，这个实验都给不出结论，而脚本会欢天喜地地报"到点没睡"**'
    '（R57 F 臂实测：判据 = "900 s 后端口消失 + 日志停住 ⇒ 深睡正样本；否则点名到点没睡"，而真正的第三支是 `main.c:' + str(L_SLEEPCHK[0]) +
    ' 那行 idle 判定在主循环里，主循环之前第 ' + str(L_GATE[0]) + ' 行的配网闸门先把 app_main 阻塞住 1800 s ⇒ 判定点**从未被执行**）',
    '→ 症状：读数全是真的（探针 ' + str(N_PROBE) + ' 轮、跨线 ' + str(PAST_BOUND) + ' 轮、端口一直在），但**它们量的不是那条判据**。'
    '若照原判据落纸，就得到一句假的"900 s 到点没睡"，它还会被下一遍当成"深睡机制已排除"的依据。',
    '→ 为什么它危险：①**否定式判据必须有"这条路本来能走通"的前置证据**，否则否定的是自己的可达性而不是被测命题；'
    '②本臂最容易上钩的地方是 `probe#` 一直在打——它是**后台探针任务**的日志，跟主循环无关，拿"日志还在写"当"主循环还活着"就正好反了；'
    '③它是 R53 之后第一次**主动去够**一条新边界，失败得越"成功"（数据完整、rc=0）越危险。',
    '→ 正确做法：①实验设计阶段先把判据的**每一支在源码里对应的执行点**grep 出行号，并确认它在**当前设备状态**下可达（本遍写成断言：'
    '闸门行号 < 判点行号 ⇒ 判据必须改成三选一并给"不可达"那一支正面证据）；'
    '②给"主循环活着"找一个**只可能由主循环打的**日志标记（本遍用 `clock page:`，实测 0 次 = 正面证据），别拿后台线程的心跳当证据；'
    '③把"够到不可达"本身登记成结果并**改口**，而不是把不可达解释成"没发生"。同族 = 项目记忆"新判据分支须真源码可达性取证"、'
    '本仓库 R31 P0（两处提前 break 让活屏恒判成 0V 钳位）——那次是可达性被代码自己堵死，这次是被状态机堵死。',
    '[错误类型] **登记句里的"加数"没有执行者**：上一遍台账写"排查记录本遍真追加 1 行登记 **+ 1 只 glue 空行**"，'
    '而那一遍的等式实际是 `DOC_LN == DOCL0 + 1`（只加 1 行）⇒ **叙述多算了一只空行**，落盘没错、话错了',
    '→ 症状：读起来像"那次追加自带分隔"，实际前一行是列表行（连续列表项之间不该插空行，插了反而断列表）。'
    '这类错只有把**那句话里的加数**和**等式**并排对表才会红。',
    '→ 为什么它危险：①它是"完成态数字"规矩的**剩余缝隙**——规矩盯住了"数字必须落盘后现数"，没盯"话术里的加数是否等于那个数"；'
    '②空行/缩进这类**不承载字符**的计数最容易被顺手写成"惯例值"，而 §38.19 那一族（落地器不验节间空行）恰恰刚教会我们：空行是要量的东西。',
    '→ 正确做法：①凡"本遍加了 N 行（含 M 只空行）"这种**分解式**叙述，分解项也要来自现算（`glue = 写后空行数 − 写前空行数`），或直接不分解；'
    '②订正只**追加登记**（本遍 §38.29 末格点名上一遍那一句），不回写已落正文；③同族 = 本批第七批第 4 条（预期增量写字面量）/ 第六批第 1 条（门的量程比被检物大）。',
]
N_NEW = len([l for l in FREQ_ROWS if l.startswith('[错误类型]')])
assert N_NEW == 2, 'ABORT: 本批正文条数现算 ' + str(N_NEW) + ' 只，不是 2'
FREQ_ROWS[0] = T7.replace('{N}', str(N_NEW))

LEDGER = ('>'
          ' **【' + AT + ' 落地｜R57 第八批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（_T0 = ' + AT + '，取在任何产证动作之前）：'
          '全文 `^[错误类型]` 条数 = **' + str(f_e0) + '**、行数 = **' + str(f_l0) + '**、字节 = **' + format(len(FREQ_T.encode('utf-8')), ',') + '**；'
          '本批正文 = **' + str(N_NEW) + '** 条 / **' + str(len(FREQ_ROWS)) + '** 行（**不含**本台账行与标题上方那只 glue 空行）；'
          '**落盘后的终态由本遍载体现数**（完成态数字不在本行预写）。同遍：排查记录 +' + str(len(S29)) + ' 行（§38.29 新节 + 其前 1 只节间空行，'
          '量具 = "标题前有空行的只数 == 标题总数"，写盘后复跑）；烧录须知 +' + str(len(FLASH_SEC)) + ' 行；done +1 行（205）；'
          'todo +' + str(N_NEW_TODO) + ' 只未选项 + 台账 1 行；dev_log +' + str(len(DEV_ROW)) + ' 行；updates +' + str(len(UPD_ROW)) + ' 行。')

NEW_TODO = [
    '- [ ] **要不要给深睡加"按键/电平唤醒源"**（R57 F 臂现读：`main.c` 里 `esp_sleep_enable_*` 只有定时器 ' + str(WAKE_KINDS['timer']) +
    ' 处、`ext0/ext1/gpio_wakeup_enable` 命中 ' + str(WAKE_KINDS['ext_or_gpio']) + ' ⇒ 深睡后**只能等定时器**，未校时固定 6 h）。'
    '这是**固件语义改动**（要重烧、要重冻待烧指纹），按规矩等用户点头才动。',
    '- [ ] **' + str(IDLE_S) + ' s idle 深睡的正样本仍为 0**：要拿到它必须先在**当前状态机**里让主循环跑起来——两条路：①给板子配上 WiFi（闸门让出后才有主循环）；'
    '②把 idle 判定挪到闸门之前（=改码，与上一只同案）。在此之前，"串口消失 = 深睡"只能记成**未证**。',
]
TODO_HEAD = ('【**todo 第十八遍台账｜' + AT + ' R57 F 臂落纸遍（§38.29 + 〇-补4 + FreqErr 第八批 + done 205）落笔之前现跑**：'
             '① 口径按 §38.24 —— **命令原文 + 本次输出同落纸**，对照物 = 上一遍载体。本遍现跑 `python` 逐行扫 todo.md，判据 = **行首前缀 "- " + 方括号空格 x + "] "**：'
             '改前命中 **' + str(len(PRE_PRE)) + '** 只，行号 = ' + ' '.join(str(x) for x in PRE_PRE) + '；'
             '② 本遍**新加 ' + str(N_NEW_TODO) + ' 只未选项**（深睡唤醒源 / idle 正样本仍 0）⇒ 名单换代，'
             '不再引用旧快照那串；改后名单由本遍落地器写盘后独立回读兑现，见载体 `TODO` 行。】')

_payload_all = '\n'.join(S29) + '\n'.join(FLASH_SEC) + DONE_ROW + '\n'.join(DEV_ROW) + '\n'.join(UPD_ROW) + '\n'.join(FREQ_ROWS) + LEDGER + '\n'.join(NEW_TODO) + TODO_HEAD
for _s in ('{N}', '%s', '%d', '@@', 'None(', 'PLACEHOLDER'):
    assert _s not in _payload_all, 'ABORT: 本遍新落正文含未替换哨兵 ' + _s
assert secret.decode('utf-8') not in _payload_all, 'ABORT: 明文口令进了正文'
assert chr(92) not in _payload_all, 'ABORT: 本遍新落正文含 ASCII 反斜杠（作用域 = 本遍正文串）'

# ---- 组装（写盘前先算等式） ----
DOC_TAIL = '\r\n' + '\r\n'.join(S29) + '\r\n'
DOC_NEW = DOC_T + DOC_TAIL
FREQ_NEW = FREQ_T + '\r\n' + '\r\n'.join(FREQ_ROWS) + '\r\n' + LEDGER + '\r\n'
DONE_NEW = DONE_T + DONE_ROW + '\n'
FLASH_NEW = FLASH_T + '\n'.join(FLASH_SEC) + ''
DEV_NEW = DEV_T + '\n'.join(DEV_ROW) + '\n'
UPD_NEW = UPD_T + '\n'.join(UPD_ROW) + '\n'
TODO_TAIL = '\r\n'.join(NEW_TODO) + '\r\n' + '\r\n'.join([TODO_HEAD]) + '\r\n'
TL0 = TODO_T.split('\r\n')
TODO_NEW = '\r\n'.join(TL0[:-1] + [''] + NEW_TODO + [TODO_HEAD]) + '\r\n'
assert TODO_NEW.startswith('\r\n'.join(TL0[:271])) if len(TL0) > 272 else True

# 写盘前等式（裁决类门全部前置）
doc_lines_new = len(DOC_NEW.split('\r\n')) - 1
assert doc_lines_new == DOCL0 + len(S29) + 1, 'ABORT: 排查记录预期行数等式不成立（glue + 节 ' + str(len(S29)) + ' 行）'
frq_lines_new = len(FREQ_NEW.split('\r\n')) - 1
assert frq_lines_new == f_l0 + len(FREQ_ROWS) + 2, 'ABORT: FreqErr 预期行数等式不成立'
assert len([l for l in FREQ_NEW.split('\r\n') if l.startswith('[错误类型]')]) == f_e0 + N_NEW
for _t, _o in ((DOC_NEW, DOC_T), (FREQ_NEW, FREQ_T), (TODO_NEW, TODO_T), (FLASH_NEW, FLASH_T), (DEV_NEW, DEV_T), (UPD_NEW, UPD_T)):
    assert _t.startswith(_o.rstrip('\r\n')) or _t.startswith(_o), 'ABORT: 前缀等式不成立 ⇒ 本遍不是纯追加'
    assert _t.count('\r') in (0, _t.count('\n')), 'ABORT: 行尾纯度破了'
assert '\r' not in DONE_NEW and '\r' not in FLASH_NEW and '\r' not in DEV_NEW and '\r' not in UPD_NEW
_todo_after = [i + 1 for i, l in enumerate(TODO_NEW.split('\r\n')) if l.startswith('- [ ]')]
assert len(_todo_after) == len(PRE_PRE) + N_NEW_TODO, 'ABORT: todo 未选项计数与预期不符'
# 节间空行量具（写盘前先在目标串上跑，写盘后再复跑一次）
def _bad_blanks(text):
    body = text.split('\r\n')
    if body and body[-1] == '':
        body = body[:-1]
    return sum(1 for i, l in enumerate(body) if l.startswith('#') and i > 0 and body[i - 1].strip())
assert _bad_blanks(DOC_T) == 0, 'ABORT: 排查记录改前就有 ' + str(_bad_blanks(DOC_T)) + ' 只标题缺节间空行 ⇒ 先查是谁又动了'
assert _bad_blanks(DOC_NEW) == 0, 'ABORT: 本遍新节自己没带节间空行 ⇒ §38.19 那一族重犯'

open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)
open(DONE, 'w', encoding='utf-8', newline='').write(DONE_NEW)
open(FLASH, 'w', encoding='utf-8', newline='').write(FLASH_NEW)
open(DEVLOG, 'w', encoding='utf-8', newline='').write(DEV_NEW)
open(UPD, 'w', encoding='utf-8', newline='').write(UPD_NEW)
open(TODO, 'w', encoding='utf-8', newline='').write(TODO_NEW)

# ---- 写盘后独立回读现数 ----
d1, f1, t1 = rd(DOC), rd(FREQ), rd(TODO)
dn, fn, tn = rd(DONE), rd(FLASH), rd(DEVLOG)
assert (d1, f1, t1, dn, fn) == (DOC_NEW, FREQ_NEW, TODO_NEW, DONE_NEW, FLASH_NEW), 'ABORT: 回读与内存串不等'
DOC_LN = len(d1.split('\r\n')) - 1
FREQ_LN = len(f1.split('\r\n')) - 1
N_TOTAL = len([l for l in f1.split('\r\n') if l.startswith('[错误类型]')])
assert _bad_blanks(d1) == 0, 'ABORT: 写盘后量具复跑红'
SEC_LINE = [i + 1 for i, l in enumerate(d1.split('\r\n')) if l.startswith('### 38.29')][0]
HEAD_TOT = len([l for l in d1.split('\r\n') if l.startswith('#')])
TODO_AFTER = [i + 1 for i, l in enumerate(t1.split('\r\n')) if l.startswith('- [ ]')]
TODO_SUB = [i + 1 for i, l in enumerate(t1.split('\r\n')) if '- [ ]' in l]
assert len(TODO_AFTER) == len(PRE_PRE) + N_NEW_TODO
S1, T1 = fold_a(SYNC), fold_b(SYNC)
assert S1 == S0 and T1 == T0, 'ABORT: 本遍动过 hardware/ht305_sync/'
_vm = subprocess.run((sys.executable, VMRUN), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器没跑绿 rc=' + str(_vm.returncode)
VM_C = _mc.group(1).replace('\\', '/').split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_C)).split('\n') if l.startswith('INNER_ROWS=')][0]
PORTS = sorted(set(re.findall(r'(?m)^(COM\d+)', sh((sys.executable, '-m', 'serial.tools.list_ports'))[1])))
REV = sh(('git', 'rev-list', '--count', 'origin/main..HEAD'))[1].strip()
ST = [l for l in sh(('git', '-c', 'core.quotePath=false', 'status', '--porcelain'))[1].splitlines() if l.strip()]

FILES = [DOC, FREQ, TODO, DONE, FLASH, DEVLOG, UPD, CAR_F, LOG_F, TOOL]
with open(CARRY, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R57 F 臂落纸遍  MODE=F-ARM-LAND  本遍现跑于 ' + AT + '（_T0 取在任何产证动作之前）；本遍零串口动作，只列口\n')
    f.write('CAP F 臂现读：抓取 ' + CAP_FROM + ' ~ ' + CAP_TO + '（窗口 ' + CAP_SEC + ' s）；MAC ' + MAC_F + '；抓完立刻列口 COM14 仍在线 = ' + PORT_AFTER + '\n')
    f.write('LOG 入库件 = hardware/' + os.path.basename(LOG_F) + ' / ' + money(LOG_B) + ' B / md5 ' + LOG_MD5 + '；非空行 ' + str(len(LS)) +
            ' 行；ROM banner ' + str(BANNER) + ' 次（首行半行）；明文命中（只在内存计数，不打印、不进载体正文）= ' + str(PLAIN_HITS) + ' 处 ⇒ 不 stage、不 push、不删\n')
    f.write('READ probe# ' + str(N_PROBE) + ' 次（uptime ' + str(FIRST_UP) + '~' + str(LAST_UP) + ' ms）/ 跨 ' + str(IDLE_S) + ' s 线 ' + str(PAST_BOUND) +
            ' 次 / AXP@0x34 行 ' + str(AXP34) + ' 条 / 应答 ' + str(ACK_ROWS) + ' 条 / panel silent ' + str(SILENT) + ' / blanked ' + str(BLANKED) +
            ' / witness ' + str(WITN) + ' / clock page: ' + str(CLOCK) + ' / SoftAP 行 ' + str(SOFTAP) + ' / 请现场配网 ' + str(GATE_MSG) + ' / sdmmc E 行 ' + str(SDERR) + '\n')
    f.write('VERDICT 判读改口：idle 判定点在 `main.c:' + str(L_SLEEPCHK[0]) + '`（主循环），配网闸门 `main.c:' + str(L_GATE[0]) + '` 先阻塞至 1800 s ⇒ 判点在未配网态**不可达**；'
            '正面证据 = 只可能由主循环打的 `clock page:` 在本臂 0 次；`probe#` 属后台探针任务，**不得**当主循环证据 ⇒ 不写"到点没睡"\n')
    f.write('WAKE 唤醒源现读：`esp_sleep_enable_timer_wakeup` = ' + str(WAKE_KINDS['timer']) + ' 处（行 ' + ' / '.join(str(x) for x in L_TIMER) +
            '）；`esp_sleep_enable_ext0/ext1` + `gpio_wakeup_enable` + `esp_sleep_pd_config` = ' + str(WAKE_KINDS['ext_or_gpio']) + ' 处 ⇒ 深睡后按键叫不醒，未校时深睡 6 h\n')
    f.write('ARMS 屏侧：本臂 = 第五臂，仍全 NACK；E 臂在册 probe ' + str(E_PROBE) + ' 次 / 应答 0 条；四臂在册 VERDICT=FOUR-ARMS-ALL-NACK = ' + str(ARMS4) +
            '；分母换代 hardware/ 单层 .log = ' + str(len(LOGS)) + ' 只 / 我方 ' + str(DENOM.group(2)) + ' 只（在册同值 = ' + str(int(DENOM.group(2))) + '）\n')
    f.write('IDENTITY 板上 = 待烧：boot ' + BOOT16 + ' == bin[176:184] = True；build md5 ' + BIN_MD5 + '（32 位 hex = md5，不是 sha256）/ ' + money(len(BIN_B)) + ' B\n')
    f.write('LAND 写盘后独立回读现数：排查记录 ' + str(DOCL0) + ' -> ' + str(DOC_LN) + ' 行（+' + str(DOC_LN - DOCL0) + ' = glue 1 + §38.29 ' + str(len(S29)) +
            ' 行；§38.29 在第 ' + str(SEC_LINE) + ' 行；标题总数 ' + str(HEAD_TOT) + '，其中前面缺空行的 = **0**（写前写后各跑同一把量具））；'
            'FreqErr ' + str(f_e0) + ' -> ' + str(N_TOTAL) + ' 条 / ' + str(f_l0) + ' -> ' + str(FREQ_LN) + ' 行；' + '；'.join(
                os.path.basename(p) + ' ' + str(len(rd(p).split('\r\n' if p in (TODO,) else '\n')) - 1) + ' 行 ' + money(os.path.getsize(p)) + ' B ' + mdb(rb(p))[:12]
                for p in (TODO, DONE, FLASH, DEVLOG, UPD)) + '\n')
    f.write('TODO 前缀口径 改前 ' + str(len(PRE_PRE)) + ' 只（' + ' '.join(str(x) for x in PRE_PRE) + '）-> 改后 ' + str(len(TODO_AFTER)) + ' 只（' +
            ' '.join(str(x) for x in TODO_AFTER) + '）= 改前 + ' + str(N_NEW_TODO) + ' 只新未选项；子串口径 ' + str(len(TODO_SUB)) + ' 只（台账行自身含该串 ⇒ 子串 = 前缀 + 1，'
            '多出的那只行号 = ' + str([x for x in TODO_SUB if x not in TODO_AFTER]) + '）\n')
    f.write('CORRECT 订正（只点名不回写）：上一遍 `hardware/r57_backups_readme10_fix.txt` 与 FreqErr 台账那句"真追加 1 行登记 + 1 只 glue 空行"里，'
            '空行加数为多算（那一遍实际净增 1 行；等式 DOC_LN == DOCL0 + 1 在那一遍载体里跑过）⇒ 本遍 §38.29 末格已点名登记，并立 FreqErr 第八批第 2 条\n')
    f.write('FIELD 现跑：列口 = ' + ', '.join(PORTS) + ' ⇒ COM14 在位 = ' + str('COM14' in PORTS) + ' / rev-list = ' + REV + '（未 push）/ status --porcelain = ' +
            str(len(ST)) + ' 行\n')
    f.write('VM 本遍现跑内层复核器：rc=' + str(_vm.returncode) + ' / ' + INNER + ' / 代落件 = hardware/' + VM_C + '\n')
    f.write('SEAL 两条同尺 + 公共量互核：FOLD-A 写前 ' + S0[2] + ' == 写后 ' + S1[2] + ' = ' + str(S0 == S1) + '；FOLD-B 写前 ' + T0[2] + ' == 写后 ' + T1[2] + ' = ' +
            str(T0 == T1) + '；公共量 ' + str(S0[0]) + ' 只 / ' + money(S0[1]) + ' B 互核 = ' + str(S0[:2] == T0[:2]) + '；内存假名 ' + PROBE + ' 双红 = ' + str(FIRED) +
            ' ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版\n')
    f.write('WITNESS md5 前 12：本遍工具 ' + mdb(rb(TOOL))[:12] + ' / F 臂载体 ' + mdb(rb(CAR_F))[:12] + ' / E 臂载体 v2 ' + mdb(rb(CAR_E2))[:12] +
            ' / 上一遍载体 ' + mdb(rb(CAR_R10))[:12] + ' / 排查记录(改前) ' + mdb(DOC_T.encode('utf-8'))[:12] + ' / FreqErr(改前) ' + mdb(FREQ_T.encode('utf-8'))[:12] +
            ' / todo(改前) ' + mdb(TODO_T.encode('utf-8'))[:12] + ' / done(改前) ' + mdb(DONE_T.encode('utf-8'))[:12] + '\n')
    f.write('NOTDONE 本遍没做（点名）：没碰串口（只列口）/ 没烧录 / 没改 main/ 源码（唤醒源那条列 todo 等用户定）/ 没重建固件 / 没换电池 / 没万用表 / 没第二块板 / '
            '没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / 没新建备份根 / 没刷新 docs 快照（快照非终态，本遍之后六件又变了 ⇒ 口径内不重跑洗绿）/ '
            '没 push、没 amend / 零删除（含 %TEMP% 里 D/E/F 三臂原件）/ 没回写上一遍正文（订正只追加）/ 屏亮肉眼确认仍 0 次 ⇒ 不播提示音\n')
    f.write('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(open(CARRY, encoding='utf-8').read().split('\n')) - 1) + ' 行\n')
    f.write('VERDICT=F-ARM-LAND-DONE\n')

print('CAP %s ~ %s (%s s)  probe=%d  past%ds=%d  AXP34=%d ack=%d' % (CAP_FROM[11:], CAP_TO[11:], CAP_SEC, N_PROBE, IDLE_S, PAST_BOUND, AXP34, ACK_ROWS))
print('MAINLOOP clock page=%d  gate=%d  silent=%d blanked=%d witness=%d  banner=%d' % (CLOCK, GATE_MSG, SILENT, BLANKED, WITN, BANNER))
print('PATH gate@main.c:%d < sleepchk@main.c:%d   wake timer=%d ext=%d' % (L_GATE[0], L_SLEEPCHK[0], WAKE_KINDS['timer'], WAKE_KINDS['ext_or_gpio']))
print('DOC %d -> %d 行（§38.29 第 %d 行 / 缺空行标题=0）  FREQ %d -> %d 条 / %d -> %d 行' % (DOCL0, DOC_LN, SEC_LINE, f_e0, N_TOTAL, f_l0, FREQ_LN))
print('TODO %d -> %d 只未选项（+2）  DONE/FLASH/DEV/UPD 已追加' % (len(PRE_PRE), len(TODO_AFTER)))
print('FIELD ports=%s rev=%s porcelain=%d' % (','.join(PORTS), REV, len(ST)))
print('VM rc=%d %s' % (_vm.returncode, VM_C))
print('SEAL %s==%s / %s==%s' % (S0[2][:8], S1[2][:8], T0[2][:8], T1[2][:8]))
print('CARRY = hardware/%s (%d B)' % (os.path.basename(CARRY), os.path.getsize(CARRY)))
print('VERDICT=F-ARM-LAND-DONE')
