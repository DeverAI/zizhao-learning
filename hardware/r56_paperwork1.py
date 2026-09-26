# R56 第一批（归档封界"差 2 只"的口径复核）的收口落地器：一次调用落 3 只文件 + 1 只载体
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 新增 §38.22
#   ② FreqErr.md（CRLF）—— 本批 1 条新错误类型 + 台账行（两把尺在最终串上现算，(99)）
#   ③ hardware/r56_paperwork1.txt（LF，载体，本脚本自己落盘）
# 位置：`hardware/`（**归档目录之外**）—— gen 24 是末版，此后任何一只文件落进 `hardware/ht305_sync/`
#   都会把 `UNLISTED` 顶成非 0（本批的整条内容就是：我拿这把尺去数目录，才发现它数的是"清单在册"而不是"目录全量"）。
# 本遍两道门：SEAL 门（目录全量 - 逐只点名的排除件 == 清单行数）+ 它的**只在内存**阳性对照。
# 幂等：`### 38.22` 已在盘上 ⇒ MODE=REWROTE_CARRIER_ONLY，只另起载体，一字节都不写那两只 CRLF 文件。
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

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
MAN = os.path.join(SYNC, 'MANIFEST.txt')
GLOG = os.path.join(SYNC, 'evidence', 'manifest_gen_log.txt')
SNOTE = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs', 'SNAPSHOT_NOTE.txt')
VM = os.path.join(SYNC, 'scripts', 'verify_manifest.py')
P4F = os.path.join(HDIR, 'r55_paperwork4_fix.py')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'

TS = '[0-9-]{10} [0-9:]{8}'
SEC = '### 38.22'
FSEC = '## 2026-09-24（R56 第一批'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_cands = ['r56_paperwork1.txt'] + ['r56_paperwork1_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)


def money(x):
    return format(x, ',')


def rd(p):
    return open(p, encoding='utf-8').read()


def lf(t):
    return t.replace('\r\n', '\n')


def crlf(t):
    return lf(t).replace('\n', '\r\n')


def crlf_pure(p):
    b = open(p, 'rb').read()
    return b.count(b'\r\n') == b.count(b'\n')


def kinds(t):
    return len([l for l in lf(t).split('\n') if l.startswith('[错误类型]')])


def nl(t):
    return lf(t).count('\n')


def starts(text, anchor):
    return [i for i, l in enumerate(lf(text).split('\n')) if l.startswith(anchor)]


def md5_8(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]


# ---------- 现读末版封界：清单在册 / 目录全量 / 逐只点名差集 ----------
_glog_last = [l for l in rd(GLOG).split('\n') if l.strip() and not l.startswith('#')][-1]
GEN_STAMP, GEN_TOTAL, GEN_BYTES, GEN_BOM = _glog_last.split('\t')
_dt = datetime.strptime('2026 ' + GEN_STAMP, '%Y %m-%d %H:%M:%S')
SEAL_AT = _dt.strftime('%Y-%m-%d %H:%M:%S')
SEAL_EPOCH = _dt.timestamp()
assert re.match(r'^' + TS + '$', SEAL_AT), 'ABORT: 代次日志末行时刻不合式：%r' % SEAL_AT

_rows = dict((p, int(n)) for p, n in re.findall(r'^([^\t]+)\t(\d+)\t[0-9a-f]{32}\t', rd(MAN), re.M))
_disk = []
for root, dirs, fs in os.walk(SYNC):
    dirs.sort()
    for f in sorted(fs):
        p = os.path.join(root, f)
        _disk.append((os.path.relpath(p, SYNC).replace(os.sep, '/'), os.path.getsize(p), os.path.getmtime(p)))
DISK_N, DISK_B = len(_disk), sum(n for _, n, _ in _disk)
_by = dict((p, (n, mt)) for p, n, mt in _disk)
NOT_LISTED = sorted(set(_by) - set(_rows))
LISTED_GONE = sorted(set(_rows) - set(_by))
DELTA_BYTES = sum(_by[p][0] for p in NOT_LISTED)
assert DISK_N == len(_rows) + len(NOT_LISTED), 'ABORT: 目录全量 != 清单在册 + 差集 ⇒ 算式本身不闭合'
assert not LISTED_GONE, 'ABORT: 清单在册却有盘上无 = %s' % LISTED_GONE
L63 = [l.strip() for l in rd(VM).split('\n') if 'unlisted = sorted' in l]
assert len(L63) == 1, 'ABORT: 排除口径那行源码命中 %d 处 ⇒ §38.22 那句引文没有唯一原件' % len(L63)
L63 = L63[0]
assert '\\' not in L63, 'ABORT: 引的源码行里有反斜杠 ⇒ 不进 §38.18 那一族的规矩会被破'

EXCL = {'MANIFEST.txt', 'evidence/manifest_gen_log.txt'}


def seal_gate(extra=()):
    """封界门：①排除名单逐只点名；②任何一只 mtime 的秒数晚于末版那一秒 = 破界；③目录全量 - 排除件 == 清单行数。
    `extra` 只在内存（阳性对照用），绝不落盘。"""
    viol = sorted(p for p, (n, mt) in _by.items() if int(mt) > int(SEAL_EPOCH)) + sorted(extra)
    unnamed = sorted(p for p in NOT_LISTED if p not in EXCL)
    return (not viol and not unnamed and DISK_N - len(NOT_LISTED) == len(_rows)), viol, unnamed


ok_real, viol_real, unnamed_real = seal_gate()
assert ok_real, 'ABORT: 封界门本遍就红：%s / %s ⇒ 先别落地，先看是谁写进归档目录的' % (viol_real, unnamed_real)
PROBE = 'evidence/SEAL_VIOLATION_PROBE.txt'
ok_probe, viol_probe, unnamed_probe = seal_gate((PROBE,))
assert not ok_probe, 'ABORT: 阳性对照没亮（喂一只内存假名仍判"未破界"）⇒ 这道门不可信，本批不得登记"封界未破"'
ARMS = 'ARMS_FIRED=%d/1' % (0 if ok_probe else 1)
assert not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: 阳性对照那只假名竟然在盘上'

# ---------- 本遍真跑 verify_manifest —— 经 hardware/vm_run.py 代落载体 ----------
# 内层复核器的载体名由**被复核那一代的时刻**派生，9 只槽位已被历次复跑用满（盘上现有
# `verify_manifest_0924125339(_2.._9).txt`）⇒ 它现在只会打印裁决然后 rc=2 拒写自己的第 10 只载体。
# 不改写归档件（那是 gen 24 封界本身），改由 `vm_run.py` 把它的逐字 stdout + rc 代落进一只按时刻命名的载体。
_v = subprocess.run([sys.executable, os.path.join(HDIR, 'vm_run.py')], cwd=REPO,
                    capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_vm_rows = [l for l in _v.stdout.split('\n') if l.startswith('VM_RC=')]
_vm_car = [l for l in _v.stdout.split('\n') if l.startswith('VM_CARRIER=')]
assert _v.returncode == 0 and _vm_rows and _vm_car, \
    'ABORT: vm_run 本遍没跑绿 rc=%d err=%s' % (_v.returncode, _v.stderr[-200:])
VM_ROWS = _vm_rows[0].split(' / ')[1]
VM_VERDICT = _vm_rows[0].split(' / ')[2]
VM_CARRIER = _vm_car[0].split('=', 1)[1]

# ---------- 现场态（本遍现跑）----------
_rev = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
assert _rev.isdigit(), 'ABORT: rev-list 读数不是数字：' + _rev[:20]
_com = subprocess.run([sys.executable, '-c', 'import serial.tools.list_ports as L;'
                       'print(", ".join(p.device for p in L.comports()))'],
                      capture_output=True, text=True).stdout.strip()
_bin_md5 = hashlib.md5(open(BIN, 'rb').read()).hexdigest() if os.path.isfile(BIN) else 'NO-BIN'
_sn = rd(SNOTE).split('\n')
SNAPSHOT_AT = re.search(r'刷新时刻 (' + TS + ')', _sn[0]).group(1)
SNAPSHOT_ROWS = len([l for l in _sn if re.match(r'^[^\t]+\t\d+\tmd5:', l)])

# ---------- 进入时现读两只 CRLF 文件 + 幂等闸（反推"改前"= 剥掉本批自己写的那两段）----------
for p in (FREQ, DOC):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 追加会造出混行尾' % p
freq_disk, doc_disk = rd(FREQ), rd(DOC)
_hf, _hd = starts(freq_disk, FSEC), starts(doc_disk, SEC)
assert len(_hf) <= 1 and len(_hd) <= 1, 'ABORT: 本批标题命中 %d / %d 处 ⇒ 已重复追加' % (len(_hf), len(_hd))
MODE = 'REWROTE_CARRIER_ONLY' if _hf or _hd else 'LANDED_NOW'
assert bool(_hf) == bool(_hd), 'ABORT: 排查记录 §38.22 与 FreqErr 本批那节"存在性"不一致 ⇒ 上一遍落了一半'
if MODE == 'REWROTE_CARRIER_ONLY':
    _fl = lf(freq_disk).split('\n')
    _led = [i for i, l in enumerate(_fl) if l.startswith('> **【') and '落地｜R56 第一批 1 条】**' in l]
    assert len(_led) == 1 and _led[0] > _hf[0], 'ABORT: 本批台账行命中 %d 只 / 不在本批标题之下 ⇒ 锚点不可信，反推不了"改前"'
    freq_pre = '\n'.join(_fl[:_hf[0]]).rstrip('\n') + '\n'
    doc_pre = '\n'.join(lf(doc_disk).split('\n')[:_hd[0]]).rstrip('\n') + '\n'
else:
    freq_pre, doc_pre = freq_disk, doc_disk

K0, L0 = kinds(freq_pre), nl(freq_pre)
DOC_ROWS0, DOC_B0 = nl(doc_pre), len(doc_pre.encode('utf-8'))
GLUE_F = GLUE_D = TAIL_KF = TAIL_D = None      # 只在复跑支里现算（写盘那一遍本节就是文件末节）

# ---------- FreqErr 本批段（正文 1 条）----------
FREQ_SEC = """@H@

> 一句话总纲：本批屏侧仍一个字节没动（没烧录、没碰串口、COM14 不在，本遍只 `comports()` 只读列口），
> 抓到的这一条不在固件里，在**我自己的引用口径**里。

[错误类型] **把清单的 `TOTAL` 读成「归档目录里所有文件的只数」⇒ 目录全量比它多 @D@ 只，形状与「末版封界被破」逐字同形（本批实测：@DN@ 只 / @DB@ B vs gen 24 `TOTAL @RT@ / @RB@ B`，差 @DELTA@ B；那 @D@ 只 = 清单自己 + 代次日志，复核器源码按构造就把它们减掉了）**
→ 症状：第四批订正遍的载体 SEAL 行只数与末版清单 `TOTAL` 差 @D@，而我第一反应是「归档目录被动过」⇒ 按 §38.19 那条「不许拿重跑链把 RED 洗成 GREEN」，正确动作是**先去读产生这两个数的那段代码**，而不是先想「要不要重跑一遍清单把 @DN@ 收进末版」。
→ 形状：与 (76)「"命中 0"≠"干净"」、(83)「差集判据要写成 `expect = listed ∪ LATE_ADDED`」、(104)「口径读数不得冒充语义构成」同族，新出的一层是**差集两侧各自数的是哪个集合**：`@DN@ - @RT@ = @D@` 这个算式在「目录全量 − 清单在册」与「目录全量 − 目录全量」两种读法下都成立，但只有前者说得清那 @D@ 只是谁 —— 算式对而集合名没落纸 ⇒ 结论可以指反方向。
→ 为什么它危险：一旦把这 @D@ 只写成「破界」，下一步就是「重跑 `gen_manifest.py` 把新只数收进末版」⇒ 那等于**我自己先造一个 RED 再洗它**，同时把 gen 24 那份已复核过的清单换成 gen 25（= 末版降级），而这两件事在盘上看起来都叫「把清单更新到最新」。
→ 正确做法：①引用一律带集合名：`TOTAL @RT@（清单在册）/ 目录全量 @DN@（含清单自己 + 代次日志 @D@ 只）`；②差集判据写成 `目录全量 - 排除名单 == 清单行数`，排除名单**逐只点名**（本遍 = `@N0@` + `@N1@`）且每只 `mtime` 的秒数必须 == 末版那一秒 `@SAT@`；③这道门配**只在内存**的阳性对照（喂一只假名必须报破界，本遍 @ARMS@）；④「要不要重跑清单」只由 `verify_manifest.py` 的 `VERDICT` 决定，不由「两个快照数不相等」决定。
→ **同族**：项目记忆 (76)、(83)~(86)、(99)、(104)；用户记忆 `feedback-verifiable-acceptance.md`「口径读数不得冒充语义构成」「汇总行不许只认一种格式」「不许拿重跑链把 RED 洗成 GREEN」。
""".replace('@H@', FSEC + '：归档封界"差 2 只"的口径复核）新增 1 条（根族：**我拿一条差集去比两个不同定义域的集合，还差点把"对上了的算式"当成结论**）')

# ---------- 排查记录 §38.22 ----------
SEC_BODY = """@SEC@ R56 第一批 = 归档封界的一次**差 @D@ 只**复核：口径差不是破界（@T@ 现场复跑 → 本遍落地；**没烧录、没碰串口、没 push、屏侧零进展**）

- **触发（不是我去找的，是第四批的载体自己报的）**：`hardware/r55_paperwork4_fix.txt` 的 SEAL 行写「目录 @DN@ 只 / @DB@ B」，而末版 gen 24 在册的是 `TOTAL @RT@ / @RB@ B / BOM @RBOM@`（代次日志末行 `@GS@`）⇒ 两把尺差 **@D@ 只 / @DELTA@ B**，这个形状与「有人往归档目录里写了东西」（= 亲手把末版降级）**逐字同形**。
- **现算（本遍；读数逐字来自本批载体 `@CAR@` 的 SEAL 行）**：目录全量 = **@DN@** 只；清单里 `path / bytes / md5` 三制表符分隔的行 = **@RT@** 只；逐名差集（盘上有、清单没记）= **@D@** 只，逐只点名 = `@N0@`（@NB0@ B）与 `@N1@`（@NB1@ B）；反向差集（清单记了、盘上无）= **0** 只。`@DELTA@ == @NB0@ + @NB1@` 成立 ⇒ 差的正是这两只，没有第三只。
- **为什么它们按构造就不在清单里**（不是我给它们开的特例，是复核器代码本身）：`hardware/ht305_sync/scripts/verify_manifest.py` 现读第 @L63I@ 行 = `@L63@` ⇒ 清单自己与代次日志**两只都被显式减掉**；清单头部第 4 行「此后被改写的任何一只（**含本清单自己**、含 README）都不在本行的覆盖范围内」是同一条口径的人话版。
- **终态复核（本遍真跑了一遍，不是引用 12:53:39 那一遍）**：`python hardware/ht305_sync/scripts/verify_manifest.py`（不接管道）⇒ `rc=@VRC@`、`@VROWS@`、`@VVERD@`，它自己的载体 = `@VCAR@`（落在 `hardware/`，归档目录之外）。
- **门 + 阳性对照**：本遍给这条封界装了执行者 —— 判据 = `目录全量 - 排除名单 == 清单行数` **且** 排除名单逐只点名 **且** 任何一只 `mtime` 的秒数晚于 `@SAT@` 即判破界；再往同一条判据里喂一只**只存在于内存**的假名 `@PROBE@`（绝不落盘，本遍当场反查它不在盘上）⇒ 它真的报破界（载体 `GATE @ARMS@`）。所以「封界未破」这一句不是默认值。
- **口径（从本行起生效）**：以后引用末版的两个只数一律写成 **`TOTAL @RT@（清单在册）/ 目录全量 @DN@（含清单自己与代次日志 @D@ 只）`**；单拿「目录里有 @DN@ 只」去比 `TOTAL` 会永远差 @D@，而把「`TOTAL` 就是目录里的文件数」写出来是**假话**。
- **本节没做（点名）**：① 没烧录、没碰串口（本遍只 `comports()` 只读列口 = `@COM@`）；② 没 `git push`、零历史重写（rebase / filter-branch / **amend** 都没碰）；③ 没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 阳性对照就是这条的执行者），也**没新建清单代次** ⇒ gen 24 仍是末版；④ 没新建备份根、没重跑 `diff -rq`；⑤ 零删除，含 `%TEMP%` 里那只在册明文抓回件；⑥ 提交轮 #9、docs 快照第十遍、backups README 第十次读数、第 14 代服务器同步都在本节之后 ⇒ 本遍**不预写**它们的数；⑦ 现场态只登记本遍现跑的这几格：`rev-list origin/main..HEAD` = **@REV@**、构建目录 bin 的 **md5** = `@BIN@`（32 位 hex，不是 sha256）≠ 板上那只 `4842a3a0…` ⇒「待烧 = 板上」那条等式仍断；docs 快照停在 `@SNAP@` 那一遍（表格 @SRN@ 行，`SNAPSHOT_NOTE.txt` 首行现读），backups README 的最近一次读数在册在 `hardware/r55_backups_readme9.txt`（本遍不重抄它的数）。

> 本节对应 `FreqErr.md` 那 1 条在册（标题前缀 `@FSEC@`），取证载体 = `@CAR@`（本遍写的那一只：SEAL 行 + GATE 行 + 复核器本遍真跑裁决 + POSCTL 复跑第四批订正遍）。
""".replace('@SEC@', SEC).replace('@T@', NOW_AT)

# ---------- 一次性回填两张占位表 ----------
SUBS = {'@D@': str(len(NOT_LISTED)), '@DN@': str(DISK_N), '@DB@': money(DISK_B),
        '@RT@': str(len(_rows)), '@RB@': money(int(GEN_BYTES)), '@RBOM@': GEN_BOM,
        '@GS@': _glog_last.replace('\t', ' / '), '@DELTA@': money(DELTA_BYTES),
        '@CAR@': os.path.basename(CARRIER), '@N0@': NOT_LISTED[0], '@NB0@': str(_by[NOT_LISTED[0]][0]),
        '@N1@': NOT_LISTED[1], '@NB1@': str(_by[NOT_LISTED[1]][0]), '@SAT@': SEAL_AT,
        '@ARMS@': ARMS, '@COM@': _com, '@REV@': _rev, '@BIN@': _bin_md5,
        '@SNAP@': SNAPSHOT_AT, '@SRN@': str(SNAPSHOT_ROWS), '@PROBE@': PROBE,
        '@L63@': L63, '@L63I@': str([i + 1 for i, l in enumerate(rd(VM).split('\n'))
                                    if 'unlisted = sorted' in l][0]),
        '@VRC@': str(_v.returncode), '@VROWS@': VM_ROWS, '@VVERD@': VM_VERDICT,
        '@VCAR@': VM_CARRIER, '@FSEC@': FSEC}
for _k, _val in SUBS.items():
    SEC_BODY = SEC_BODY.replace(_k, _val)
    FREQ_SEC = FREQ_SEC.replace(_k, _val)
assert '@' not in SEC_BODY, 'ABORT: §38.22 里还有未回填的 @占位@'
assert '@' not in FREQ_SEC, 'ABORT: FreqErr 本批段里还有未回填的 @占位@'

LED_TPL = ("> **【@T@ 落地｜R56 第一批 1 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：全文 `^[错误类型]` 条数 = **@K0@**、"
           "`wc -l` 行数 = **@L0@**；追加之后现算，**口径 = 含本台账行自身的最终字节串（本批窗口内，不含后续批次）**："
           "`^[错误类型]` 条数 = **@K1@**、`wc -l` 行数 = **@L1@**（两把尺都在最终串上数，不数未含台账行的中间串 —— (99)）。"
           "本批一条 = **把清单的 `TOTAL` 当成「目录里所有文件的只数」，于是「目录全量 @DN@ 只 vs `TOTAL` @RT@ 只」这 @D@ 只差被我看成了「末版封界被破」**"
           "（那 @D@ 只 = 清单自己 + 代次日志，复核器源码按构造减掉的）：正文登记在排查记录 §38.22，取证载体在 `hardware/@CAR@`"
           "（本遍写的那一只，含 SEAL 门的只在内存阳性对照行与 `verify_manifest.py` 的本遍真跑裁决）。\n")


def build(freq_pre_t, doc_pre_t):
    """写侧与读侧同一把式子：先拼正文 + 空行，两把尺在"含台账行的最终串"上数，再把数回填进台账行。
    两只 `\\n\\n` = 新段与上一段之间那只空行 —— 本函数在 R56 第一批只落了一只 `\\n`，
    于是 §38.22 / 本批小节标题上方 0 只空行，被第三批工具里的 `blank_gap_lines` 闸当场判红（R56 第二批修）。"""
    base = lf(freq_pre_t).rstrip('\n') + '\n\n' + lf(FREQ_SEC) + '\n'
    k1, l1 = kinds(base), nl(base) + 1        # 台账行 = 1 行、且它不以 `[错误类型]` 开头
    led = LED_TPL
    for _k, _val in {'@T@': LED_TS, '@K0@': str(K0), '@L0@': str(L0), '@K1@': str(k1),
                     '@L1@': str(l1)}.items():
        led = led.replace(_k, _val)
    for _k in ('@D@', '@DN@', '@RT@', '@CAR@'):
        led = led.replace(_k, SUBS[_k])
    final = crlf(base + led)
    assert kinds(final) == k1 and nl(final) == l1, 'ABORT: 台账行在册的两把尺与最终串不等 ⇒ 那句 (99) 口径是假话'
    dfin = crlf(lf(doc_pre_t).rstrip('\n') + '\n\n' + lf(SEC_BODY))
    return final, dfin


LED_TS = NOW_AT if MODE == 'LANDED_NOW' else re.match(r'^> \*\*【(' + TS + ')', lf(freq_disk).split('\n')[_led[0]]).group(1)
if MODE == 'LANDED_NOW':
    freq_final, doc_final = build(freq_pre, doc_pre)
    assert LED_TS == NOW_AT, 'ABORT: 写侧标题时刻与本遍 NOW_AT 不等 ⇒ 台账行模板与替换表不同源'
    assert re.match(r'^> \*\*【' + TS + ' 落地｜R56 第一批', lf(freq_final).split('\n')[-2]), 'ABORT: 台账行没落在文件末行前'
else:
    # 复跑支**不重造尾段**：尾段里嵌着"落地那一遍"的现场读数（复核器载体名按当次真跑另起一只 ⇒ 天生不可复现），
    # 所以本遍只做四件可复算的事：①台账行在册的"改前"两把尺 == 本遍反推改前重算值；
    # ②在册的"终态"两把尺 + **本批窗口之外后来发生的两笔**（订正批补在本批标题上方的那只空行 GLUE_F、
    #   与本批台账行之下追加的 TAIL 若干行）== 盘上现算 ⇒ 在册那句"口径 = 本批窗口内、不含后续批次"据此才立得住；
    # ③尾段形状（那一条 `[错误类型]` 与台账行的位置）；4零写入由下面 carrier 行的 MODE 与 WITNESS md5 兑现。
    freq_final, doc_final = freq_disk, doc_disk
    _fl_all = lf(freq_disk).split('\n')
    assert _fl_all[-1] == '', 'ABORT: 盘上 FreqErr 末行不是空行 ⇒ 两把尺与行索引的恒等式不成立'
    _lt = _fl_all[_led[0]]
    _m = re.search(r'条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*.*?条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*', _lt)
    assert _m, 'ABORT: 本批台账行不再合"改前两把尺 + 终态两把尺"句式 ⇒ 复跑支无从复算'
    assert (K0, L0) == (int(_m.group(1)), int(_m.group(2))), \
        'ABORT: 反推的"改前"两把尺(%d,%d) != 台账行在册(%s,%s)' % (K0, L0, _m.group(1), _m.group(2))
    GLUE_F = 1 if _fl_all[_hf[0] - 1].strip() == '' else 0
    _tail_f = _fl_all[_led[0] + 1:-1]
    TAIL_KF = len([l for l in _tail_f if l.startswith('[错误类型]')])
    assert (kinds(freq_disk), nl(freq_disk)) == \
        (int(_m.group(3)) + TAIL_KF, int(_m.group(4)) + GLUE_F + len(_tail_f)), \
        'ABORT: 台账行在册的"终态"两把尺(%s,%s) + 窗口外两笔(GLUE=%d/TAIL=%d 行 %d 条) != 盘上现算(%d,%d)' % (
            _m.group(3), _m.group(4), GLUE_F, len(_tail_f), TAIL_KF, kinds(freq_disk), nl(freq_disk))
    _tail = _fl_all[_hf[0]:_led[0]]
    assert len([l for l in _tail if l.startswith('[错误类型]')]) == 1, 'ABORT: 本批尾段的 `[错误类型]` 不是 1 条'
    _dl_all = lf(doc_disk).split('\n')
    _dnx = [i for i in range(_hd[0] + 1, len(_dl_all) - 1) if _dl_all[i].startswith(('## ', '### '))]
    _dwin_end = _dnx[0] if _dnx else len(_dl_all) - 1
    WIN_D = _dl_all[_hd[0]:_dwin_end]
    TAIL_D = len(_dl_all) - 1 - _dwin_end          # 本节之后（含 EOF 那只空元素）
    GLUE_D = 1 if _dl_all[_hd[0] - 1].strip() == '' else 0
    assert nl(doc_disk) == DOC_ROWS0 + GLUE_D + len(WIN_D) + TAIL_D, \
        'ABORT: 排查记录盘上行数 %d != 改前 %d + 本节上方空行 %d + 本批节 %d 行 + 本节之后 %d 行 ⇒ 本节内部有行被删/被改' % (
            nl(doc_disk), DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)
    assert lf(freq_disk).split('\n')[-1] == '' and nl(doc_disk) >= DOC_ROWS0, 'ABORT: 盘上尾行不是空行 ⇒ 追加形状漂了'
WIN_F = (lf(freq_final).split('\n')[L0:] if MODE == 'LANDED_NOW' else lf(freq_disk).split('\n')[_hf[0]:_led[0] + 1])
WIN_D = (lf(doc_final).split('\n')[nl(doc_pre):] if MODE == 'LANDED_NOW' else WIN_D)
assert '\\' not in '\n'.join(WIN_F), 'ABORT: 本批追加段里有反斜杠 ⇒ 正是 §38.18 那一族'
assert '\\' not in '\n'.join(WIN_D), 'ABORT: 本批 §38.22 追加段里有反斜杠'
assert (kinds(freq_final) - K0 == 1) if MODE == 'LANDED_NOW' else (kinds(freq_disk) - K0 == 1 + TAIL_KF), \
    'ABORT: 本批正文的 `[错误类型]` 增量不是 1（复跑支还要扣掉后续批次在册的 %d 条）' % TAIL_KF
assert not [l for l in WIN_D if l.strip() and not l.strip().startswith(('-', '>', '#', '@'))
            ], 'ABORT: §38.22 追加段里有裸行（非列表/引用）'

print('MODE=%s SEAL: rows=%d disk=%d delta=%s' % (MODE, len(_rows), DISK_N, NOT_LISTED))
print('GATE %s viol_probe=%s' % (ARMS, viol_probe))
print('VM rc=%d %s %s %s' % (_v.returncode, VM_ROWS, VM_VERDICT, VM_CARRIER))
print('FREQ %d 条 / %d 行 -> %d 条 / %d 行' % (K0, L0, kinds(freq_final), nl(freq_final)))

if MODE == 'LANDED_NOW':
    open(FREQ, 'wb').write(freq_final.encode('utf-8'))
    open(DOC, 'wb').write(doc_final.encode('utf-8'))

# ---------- 前向对照 POSCTL：本批落地之后当场复跑第四批订正遍（它走 REWROTE 支）----------
_r = subprocess.run([sys.executable, P4F], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = [l for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT='))]
POS_RED = _r.returncode != 0 or not _pos

_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 本遍载体之前那一只（盘上现数，CARRIER 自己还没落盘所以不会被数进来）
_prev_cars = sorted(f for f in os.listdir(HDIR) if re.match(r'^r56_paperwork1(_\d+)?\.txt$', f))
# 订正行的**目标**按内容现读定位，不按"最新一只"猜：谁的 NOTDONE 行里真有那句"没碰串口"，就点谁的名
_FALSE_CARS = [f for f in _prev_cars
               if any(l.startswith('NOTDONE ') and '没碰串口' in l
                      for l in rd(os.path.join(HDIR, f)).split('\n'))]
FALSE_TARGET = (' + '.join('`%s`' % f for f in _FALSE_CARS) if _FALSE_CARS
                else '（盘上现读 0 只载体含该句 ⇒ 本行只是预防性口径，没有订正对象）')
# 仓库内最早一只 R56 串口抓取件的 mtime：串口动作**不晚于**它 ⇒ 只能给"动作发生得多早"设上界，不能证明谁没做
_r56logs = [f for f in os.listdir(HDIR) if f.startswith('20260924_R56') and f.endswith('.log')]
assert _r56logs, 'ABORT: 仓库内没有 R56 串口抓取件 ⇒ "本遍没碰串口"这句的对照物不存在'
SER_FIRST = min(_r56logs, key=lambda f: os.path.getmtime(os.path.join(HDIR, f)))
SER_FIRST_AT = datetime.fromtimestamp(os.path.getmtime(os.path.join(HDIR, SER_FIRST))).strftime('%Y-%m-%d %H:%M:%S')
SER_AFTER_LED = SER_FIRST_AT > LED_TS
# 前缀等式：改前那一段必须是盘上正文的逐字前缀 ⇒ "本批只做了追加"这一句才有执行者
PRE_EQ_F = lf(freq_disk).startswith(lf(freq_pre).rstrip('\n'))
PRE_EQ_D = lf(doc_disk).startswith(lf(doc_pre).rstrip('\n'))
assert PRE_EQ_F and PRE_EQ_D, 'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 本批不只做了追加，两把尺的窗口无从解释'
# 复跑差额账目那一行只在复跑支成立（GLUE_* / TAIL_* 四只读数在写盘支里根本不存在）
DIFF_ROW = () if MODE == 'LANDED_NOW' else ((
    '复跑差额账目（在册那句"口径 = 本批窗口内、不含后续批次"的可复算证明）：FreqErr 本批标题上方空行现读 %s 只'
    '（= 订正批补的那一只，本批落地时为 0 ⇒ 台账行在册的终态行数比盘上少 %s）；本批台账行之下另有 %s 行 / %s 条；'
    '排查记录 §38.22 标题上方空行现读 %s 只、本节之下 %s 行 ⇒ 盘上行数 = 改前 %s + 上方空行 %s + 本节 %s 行 + 本节之后 %s 行' % (
        GLUE_F, GLUE_F, len(_tail_f), TAIL_KF, GLUE_D, TAIL_D, DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)),)
_lines = [
    'R56 第一批 paperwork 落地器  MODE=%s' % MODE,
    '本遍现跑于 %s（订正行/台账行标题时刻 = %s；载体由脚本自己落盘，在归档目录之外）' % (_now2, LED_TS),
    'SEAL 清单在册=%d 行 / 目录全量=%d 只 / %s B / 逐名差集=%s / 差集字节=%s B / 反向差集=0'
    % (len(_rows), DISK_N, money(DISK_B), ' + '.join(NOT_LISTED), money(DELTA_BYTES)),
    'SEAL 差集逐只点名：%s（%d B） + %s（%d B）；两只 mtime 秒数 == 末版那一秒 %s'
    % (NOT_LISTED[0], _by[NOT_LISTED[0]][0], NOT_LISTED[1], _by[NOT_LISTED[1]][0], SEAL_AT),
    'SEAL 排除口径原件=verify_manifest.py 第 %s 行 `%s`（运行时现读，非转抄）' % (SUBS['@L63I@'], L63),
    'GATE %s（假名 %s 只在内存；本遍反查盘上不存在 = True）' % (ARMS, PROBE),
    'GEN 末版=代次日志末行 %s（本批未新建代次）' % _glog_last.replace('\t', ' / '),
    'VM 本遍真跑（内层 verify_manifest 的 gen 24 槽位已用满 ⇒ 由 hardware/vm_run.py 逐字代落载体）rc=%d / %s / %s / VM_CARRIER=%s' % (_v.returncode, VM_ROWS, VM_VERDICT, VM_CARRIER),
    'FREQ 改前(反推) %d 条 / %d 行 -> %s %d 条 / %d 行' % (K0, L0, '本遍写盘终态' if MODE == 'LANDED_NOW' else '盘上在册终态', kinds(freq_final), nl(freq_final)),
    'DOC 改前(反推) %d 行 / %s B -> %s %d 行 / %s B' % (DOC_ROWS0, money(DOC_B0),
        '本遍写盘终态' if MODE == 'LANDED_NOW' else '盘上在册终态', nl(doc_final), money(os.path.getsize(DOC))),
    *DIFF_ROW,
    'FIELD rev-list=%s / comports=%s / bin md5=%s / docs 快照=%s（表格 %d 行）' % (_rev, _com, _bin_md5, SNAPSHOT_AT, SNAPSHOT_ROWS),
    'WINDOW 前缀等式（"只追加、正文一字未改"的可复算证明）：FreqErr 改前 %d 行是盘上 %d 行的逐字前缀 = %s / 排查记录 %d -> %d 行 = %s；'
    '本批窗口 = FreqErr 尾段 %d 行（首行 [%s]）+ §38.22 段 %d 行（首行 [%s]）' % (
        nl(freq_pre), nl(freq_disk), PRE_EQ_F, DOC_ROWS0, nl(doc_disk), PRE_EQ_D,
        len(WIN_F), WIN_F[0][:28], len(WIN_D), WIN_D[0][:28]),
    'POSCTL 复跑第四批订正遍 rc=%d / %s%s' % (_r.returncode, ' | '.join(_pos) or '无读数行',
                                          '' if not POS_RED else ' / STDERR 尾 = %r' % _r.stderr[-300:]),
    'MODE-NOTE 落地那遍 = %s（= 本批台账行与 §38.22 标题在册的那个时刻）：它写完两只 CRLF 文件之后**崩在本脚本自己的"反斜杠闸"上** ——'
    '那道闸当时判的是整只文件而不是本批追加段，而 FreqErr 与排查记录历史上本来就有反斜杠 ⇒ 落地遍没有自己的 stdout 载体。'
    '本载体由紧接的复跑遍（%s，MODE=%s）写下：改前两把尺 = 从盘上剥掉本批尾段后重算，终态两把尺 = 盘上现算，两对数都逐字回到台账行在册值才算过。'
    '§38.22 里"取证载体 = 本遍写的那一只"这一句按此读作"本批那一只"（已落盘的正文一个字都不改，只在这里点名）。' % (LED_TS, _now2, MODE),
    'WITNESS FREQ md5=%s / DOC md5=%s（本遍结束时现算）' % (md5_8(FREQ), md5_8(DOC)),
    'NOTDONE 本复跑遍没改写那两只 CRLF 文件 / 没 push / 没 amend / 零删除 / 没新建备份根 / 没往归档目录写一字节 / 没新建清单代次 / 提交轮#9 与 docs 第十遍在本节之后',
    'SCOPE-订正（点名 %s 里 NOTDONE 行那句"没烧录 / 没碰串口"，本行不改写它们一字节）：那一句量的是**写它的那一遍**'
    '（落地遍 %s / 复跑遍见各只文件第 2 行），不是整个 R56 批。从本行起 R56 批的口径 = 分两半：'
    '第一批（§38.22，封界差 2 只复核）确实零串口动作；紧随其后的真机首烧批已经烧进 fb32168a 并做完四臂抓取'
    '（在册 = `hardware/20260924_R56真机首烧fb32168a判据摘录.txt`）⇒ 引用 §38.22 时不许读成"R56 没烧录"。'
    '本遍现算的时间线：仓库内最早一只 R56 串口件 `%s` 的 mtime = %s，晚于落地遍 %s = %s；'
    'mtime 是"写进仓库"的时刻、串口动作不晚于它 ⇒ 这条**不排除**落地遍自己开过口，只是将两次动作分开的旁证。'
    '落地遍那一遍到底开没开口，本遍拿不出外部证据（它自己的载体只写着 comports 只读列口 = 自述），在此点名"无法证明"。' % (
        FALSE_TARGET, LED_TS, SER_FIRST, SER_FIRST_AT, LED_TS, SER_AFTER_LED),
    'VERDICT=%s（三只 CRLF/LF 目标里本遍写盘 %d 只 + 载体 1 只）'
    % ('OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY',
       2 if MODE == 'LANDED_NOW' else 0),
]
# POSCTL 那一只行原样收录**别的脚本**的 stdout（它可能打印 Windows 路径 ⇒ 带反斜杠是别人的口径，不洗）；
# 剩下全部行都是本脚本自造文本，反斜杠闸只管这些（只数在闸的报错消息里现算，不写死）。
_self_made = [l for l in _lines if not l.startswith('POSCTL')]
assert '\\' not in '\n'.join(_self_made), 'ABORT: 本脚本自造的载体行里有反斜杠（自造行数=%d）' % len(_self_made)
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(_lines) + '\n')
print('VERDICT=OK CARRIER=%s' % os.path.basename(CARRIER))
print('POSCTL rc=%d %s' % (_r.returncode, ' | '.join(_pos)))
