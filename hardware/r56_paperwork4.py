# R56 第四批（复跑支那一族第 3 次命中 + 载体同一行两把尺）的落地器：一次调用落 3 只文件
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 新增 §38.25
#   ② FreqErr.md（CRLF）—— 本批 2 条新错误类型 + 台账行（两把尺在最终串上现算，(99)）
#   ③ hardware/r56_paperwork4.txt（LF，载体，本脚本自己落盘，在归档目录之外）
# 触发：第三批（§38.24）落盘时，它的 POSCTL 那一步第一次把上一批落地器 paperwork2 的**复跑支**跑到，rc=1；
#   修好后重跑，同一遍里又发现它的 DOC 行把 LF 长度与盘上 CRLF 大小放在同一个箭头两端。两条都落本批。
# 幂等：`### 38.25` 已在盘上 ⇒ MODE=REWROTE_CARRIER_ONLY，一字节都不写那两只 CRLF 文件。
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
P2 = os.path.join(HDIR, 'r56_paperwork2.py')
P3 = os.path.join(HDIR, 'r56_paperwork3.py')
MIXED = os.path.join(HDIR, 'r56_paperwork3.txt')      # 第三批第一遍载体：混尺那一行在册于此
SAME = os.path.join(HDIR, 'r56_paperwork3_3.txt')     # 第三批订正后载体：同尺那一行
GLOG = os.path.join(SYNC, 'evidence', 'manifest_gen_log.txt')
MAN = os.path.join(SYNC, 'MANIFEST.txt')
TS = '[0-9-]{10} [0-9:]{8}'
SEC = '### 38.25'
SECNUM = '38.25'
FSEC = '## 2026-09-24（R56 第四批'
N_ENTRY = 2
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_cands = ['r56_paperwork4.txt'] + ['r56_paperwork4_%d.txt' % i for i in range(2, 60)]
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


def md5_(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


BS = chr(92)

# ---------- 两只在册载体逐字现读（混尺 ↔ 同尺的换算式全从这里来，不是我抄的）----------
for p in (MIXED, SAME):
    assert os.path.isfile(p), 'ABORT: 对照载体 %s 不在 ⇒ 本批那条换算式落不了纸' % os.path.basename(p)


def _doc_row(path):
    rows = [l for l in lf(rd(path)).split('\n') if l.startswith('DOC 改前')]
    assert len(rows) == 1, 'ABORT: %s 里 DOC 行命中 %d 处' % (os.path.basename(path), len(rows))
    m = re.search(r'DOC 改前 (\d+) 行 / ([\d,]+) B -> \S+ (\d+) 行 / ([\d,]+) B', rows[0])
    assert m, 'ABORT: %s 的 DOC 行格式抓不出来' % os.path.basename(path)
    return (int(m.group(1)), int(m.group(2).replace(',', '')),
            int(m.group(3)), int(m.group(4).replace(',', '')), rows[0])


M_ROWS0, M_B0, M_ROWS1, M_B1, M_RAW = _doc_row(MIXED)
S_ROWS0, S_B0, S_ROWS1, S_B1, S_RAW = _doc_row(SAME)
_p3_at = re.search(r'本遍现跑于 (' + TS + ')', lf(rd(MIXED))).group(1)
_ML = [i + 1 for i, l in enumerate(lf(rd(MIXED)).split('\n')) if l.startswith('DOC 改前')]
assert len(_ML) == 1
M_LINE = _ML[0]
assert M_ROWS1 == S_ROWS1 and M_B1 == S_B1, 'ABORT: 两只载体的"终态"不等 ⇒ 它们标的不是同一个盘上时刻'
CR_GAP = M_B1 - M_B0 - (S_B1 - S_B0)
assert CR_GAP == M_ROWS0, 'ABORT: 混尺差值与同尺差值之差 %d != 改前行数 %d ⇒ 换算式不成立，别落' % (CR_GAP, M_ROWS0)
assert S_B0 - M_B0 == M_ROWS0, 'ABORT: 同尺改前 %d - 混尺改前 %d != %d 只 CR' % (S_B0, M_B0, M_ROWS0)
SAMEDISK = len(crlf(rd(DOC)).encode('utf-8')) == os.path.getsize(DOC)
assert SAMEDISK, 'ABORT: 排查记录盘上现读 != crlf(串) 长度 ⇒ 文件里有裸 CR/LF'
DISK_B_NOW = os.path.getsize(DOC)
assert S_B1 > S_B0 and M_B1 > M_B0, 'ABORT: 两只载体的箭头不是递增 ⇒ 换算式的分母不成立'
_RATIO = '%.2f' % ((M_B1 - M_B0) / float(S_B1 - S_B0))   # 混尺箭头 / 同尺真追加 = 夸大的倍数
TODO = os.path.join(REPO, 'todo.md')
CNT_TODO = len([l for l in lf(rd(TODO)).split('\n') if l.startswith('- [ ]')])
CMD_TODO = "grep -cF -- '- [ ]' todo.md"

# ---------- 修复现场的三格现读（paperwork2 源码）----------
_p2 = rd(P2)
FIX_NEW = 'int(_m.group(4)) + len(_tail_f)' in _p2
FIX_OLD = 'GLUE_F + len(_tail_f)' in _p2
FIX_GLUE = 'assert GLUE_F == 1' in _p2
assert FIX_NEW and not FIX_OLD and FIX_GLUE, 'ABORT: paperwork2 复跑支还没修好（%s/%s/%s）' % (FIX_NEW, FIX_OLD, FIX_GLUE)
# 同族横向自查：哪些落地工具仍然把 LF 长度与盘上大小放进同一条箭头
# 标记串拆成两段拼出来 —— 否则本文件自己的源码里就含着被搜串，计数会自指（R42 那一族）
_LFMARK = 'money(DOC_' + 'B0)'
_mix_how = []
for _f in sorted(os.listdir(HDIR)):
    if not _f.endswith('.py'):
        continue
    _t = rd(os.path.join(HDIR, _f))
    if 'DOC 改前' not in _t or 'getsize(DOC)' not in _t:
        continue
    _mix_how.append((_f, _LFMARK in _t))
assert ('r56_paperwork4.py', False) in _mix_how, 'ABORT: 本工具没被自己的扫描认出来（或它已变混尺）⇒ 扫描器不可信'
STILL_MIX = [f for f, bad in _mix_how if bad]
assert len(_mix_how) >= 2, 'ABORT: 横向自查只扫到 %d 只含 DOC 行的工具 ⇒ 半径不够，别说"同族"' % len(_mix_how)

# ---------- 进入时现读两只 CRLF 文件 + 幂等闸 ----------
for p in (FREQ, DOC):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 追加会造出混行尾' % p
freq_disk, doc_disk = rd(FREQ), rd(DOC)
_hf, _hd = starts(freq_disk, FSEC), starts(doc_disk, SEC)
assert len(_hf) <= 1 and len(_hd) <= 1, 'ABORT: 本批标题命中 %d / %d 处 ⇒ 已重复追加' % (len(_hf), len(_hd))
MODE = 'REWROTE_CARRIER_ONLY' if _hf or _hd else 'LANDED_NOW'
assert bool(_hf) == bool(_hd), 'ABORT: §38.25 与 FreqErr 本批节"存在性"不一致 ⇒ 上一遍落了一半'
_fl = lf(freq_disk).split('\n')
GLUE_D = TAIL_KF = TAIL_D = 0
_tail_f = []
if MODE == 'REWROTE_CARRIER_ONLY':
    _led = [i for i, l in enumerate(_fl) if l.startswith('> **【') and '落地｜R56 第四批 %d 条】**' % N_ENTRY in l]
    assert len(_led) == 1 and _led[0] > _hf[0], 'ABORT: 本批台账行命中 %d 只 / 不在本批标题之下' % len(_led)
    freq_pre = '\n'.join(_fl[:_hf[0]]).rstrip('\n') + '\n'
    _dl = lf(doc_disk).split('\n')
    doc_pre = '\n'.join(_dl[:_hd[0]]).rstrip('\n') + '\n'
    _dnext = [i for i in range(_hd[0] + 1, len(_dl) - 1) if re.match(r'^#{2,3} +\d', _dl[i])]
    _dwin_end = _dnext[0] if _dnext else len(_dl) - 1
    # 窗口右界不许把"下一批落纸时插进来的空行"算进本批节：那是下一批的 glue，归尾段
    #   （不剥 ⇒ "本批终态 = 盘上 − 尾段"会多算行，第三批载体就是这么漂成 3733 的）
    while _dwin_end > _hd[0] and _dl[_dwin_end - 1].strip() == '':
        _dwin_end -= 1
    WIN_D = _dl[_hd[0]:_dwin_end]
    TAIL_D = len(_dl) - 1 - _dwin_end
    GLUE_D = 1 if _dl[_hd[0] - 1].strip() == '' else 0
    assert GLUE_D == 1, 'ABORT: §38.25 标题上方没有空行 ⇒ 追加形状变了'
    _tail_f = _fl[_led[0] + 1:-1]
    TAIL_KF = len([l for l in _tail_f if l.startswith('[错误类型]')])
else:
    freq_pre, doc_pre = freq_disk, doc_disk
K0, L0 = kinds(freq_pre), nl(freq_pre)
DOC_ROWS0 = nl(doc_pre)
DOC_B0D = len(crlf(doc_pre).encode('utf-8'))
if MODE == 'REWROTE_CARRIER_ONLY':
    assert nl(doc_disk) == DOC_ROWS0 + GLUE_D + len(WIN_D) + TAIL_D, \
        'ABORT: 排查记录行数账目不闭合：盘上 %d != 改前 %d + 上方空行 %d + 本批节 %d + 之后 %d' % (
            nl(doc_disk), DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)
    assert len([l for l in _fl[_hf[0]:_led[0]] if l.startswith('[错误类型]')]) == N_ENTRY, \
        'ABORT: 本批窗口内条数不是 %d ⇒ 窗口右界取错了' % N_ENTRY
    _lt = _fl[_led[0]]
    _nums = [int(x) for x in re.findall(r'\*\*([0-9,]+)\*\*', _lt)]
    assert len(_nums) == 5, 'ABORT: 本批台账行里抓到 %d 个数（应为 5：改前条/改前行/记录行/终态条/终态行）' % len(_nums)
    _RK0, _RL0, _RD0, _RK1, _RL1 = _nums
    assert (_RK0, _RL0, _RD0) == (K0, L0, DOC_ROWS0), \
        'ABORT: 台账行在册的"改前"三把尺与本遍反推值不等（在册 %s / 现算 %s）' % (_nums[:3], (K0, L0, DOC_ROWS0))
    assert (kinds(freq_disk), nl(freq_disk)) == (_RK1 + TAIL_KF, _RL1 + len(_tail_f)), \
        'ABORT: FreqErr 复跑账目不闭合：在册终态 (%d,%d) + 尾段 (%d 行 %d 条) != 盘上 (%d,%d)' % (
            _RK1, _RL1, len(_tail_f), TAIL_KF, kinds(freq_disk), nl(freq_disk))

# ---------- 封界门 + 只在内存的阳性对照（承前三批，同一条判据）----------
_glog_last = [l for l in rd(GLOG).split('\n') if l.strip() and not l.startswith('#')][-1]
GEN_STAMP, GEN_TOTAL, GEN_BYTES, GEN_BOM = _glog_last.split('\t')
_dt = datetime.strptime('2026 ' + GEN_STAMP, '%Y %m-%d %H:%M:%S')
SEAL_AT = _dt.strftime('%Y-%m-%d %H:%M:%S')
SEAL_EPOCH = _dt.timestamp()
_rows = dict((p, int(n)) for p, n in re.findall(r'^([^\t]+)\t(\d+)\t[0-9a-f]{32}\t', rd(MAN), re.M))
_by = {}
for root, dirs, fs in os.walk(SYNC):
    dirs.sort()
    for f in sorted(fs):
        p = os.path.join(root, f)
        _by[os.path.relpath(p, SYNC).replace(os.sep, '/')] = (os.path.getsize(p), os.path.getmtime(p))
DISK_N, DISK_B = len(_by), sum(n for n, _ in _by.values())
NOT_LISTED = sorted(set(_by) - set(_rows))
EXCL = {'MANIFEST.txt', 'evidence/manifest_gen_log.txt'}
assert DISK_N == len(_rows) + len(NOT_LISTED) and not (set(_rows) - set(_by)), 'ABORT: 封界算式不闭合'


def seal_gate(extra=()):
    viol = sorted(p for p, (n, mt) in _by.items() if int(mt) > int(SEAL_EPOCH)) + sorted(extra)
    unnamed = sorted(p for p in NOT_LISTED if p not in EXCL)
    return (not viol and not unnamed and DISK_N - len(NOT_LISTED) == len(_rows)), viol, unnamed


ok_real, viol_real, unnamed_real = seal_gate()
assert ok_real, 'ABORT: 封界门本遍就红：%s / %s' % (viol_real, unnamed_real)
PROBE = 'evidence/SEAL_VIOLATION_PROBE4.txt'
ok_probe, viol_probe, _u = seal_gate((PROBE,))
assert not ok_probe, 'ABORT: 阳性对照没亮 ⇒ 这道门不可信'
ARMS_FIRED = 'ARMS_FIRED=%d/1' % (0 if ok_probe else 1)
assert not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: 假名竟在盘上'

_v = subprocess.run([sys.executable, os.path.join(HDIR, 'vm_run.py')], cwd=REPO,
                    capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8='1'))
_vm_rows = [l for l in _v.stdout.split('\n') if l.startswith('VM_RC=')]
assert _v.returncode == 0 and _vm_rows, 'ABORT: vm_run 本遍没跑绿 rc=%d' % _v.returncode
VM_CARRIER = [l for l in _v.stdout.split('\n') if l.startswith('VM_CARRIER=')][0].split('=', 1)[1]

_com = subprocess.run([sys.executable, '-c', 'import serial.tools.list_ports as L;'
                       'print(", ".join(p.device for p in L.comports()))'],
                      capture_output=True, text=True).stdout.strip()
REV_LIST_NOW = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
assert REV_LIST_NOW.isdigit()

# ---------- FreqErr 本批段（正文 2 条）----------
FREQ_SEC = """@H@

> 一句话总纲：本批屏侧一个字节没动（没烧录、没碰串口，本遍只 `comports()` 只读列口 = @COM@），
> 抓到的两条都在**落地器自己**身上：一条是"从没跑过的那一支一跑就红"，一条是"同一行里两把不同的尺"。

[错误类型] **落地器的复跑支（MODE=REWROTE_CARRIER_ONLY）在写盘那一遍永远走不到 ⇒ 它的算术错到下一批才被看见：本批上一遍（§38.24）POSCTL 复跑 `r56_paperwork2.py` rc=1，根因是那条行数等式把"本批标题上方那只空行"数了两次。这是 §38.21 ① 那一族的第 3 次命中**
→ 症状：paperwork2 的复跑支里，`GLUE_F`（本批 FreqErr 标题上方是否为空行）既被算进"本批在册 AFTER 行数"，又额外加进 `kinds/行数` 等式的右边；而尾段 `_tail_f` 是从**本批台账行的下一行**起算的 —— 那只空行在台账行**之上**，根本不在 `_tail_f` 里。写这一支的那一遍 MODE 是 LANDED_NOW，`else` 分支一步都没执行 ⇒ "复跑支有错"这件事在本批之前**不可见**。
→ 为什么它危险：这一支正是"下一批用来确认上一批没被改动"的那道闸（POSCTL）。它一红，下一批就落不了盘；更糟的是红的时候**已落地的正文**（§38.24 与那 2 条）已经在盘上，于是现场变成"文档落了、工具红了、载体没写"，看起来像我把归档改坏了。判据本身错，比没判据更难查，因为它只在**下一批**响。
→ 正确做法：①复跑支的每一项加数都要能指出"它数的是哪一段行"，与本批窗口不重叠；②订正只改**工具源码**，已落地正文一律不回写（本批 §38.24 / FreqErr 那 2 条一字未动）；③同一族第三处（本批自己）：`r56_paperwork3.py` 的 `kinds(freq_final) - K0 == N_ENTRY` 在 REWROTE 模式下拿**全量**与本批增量比 ⇒ 本批在它之后落盘就会把它跑红，本遍已就地改成 tail-scoped 两分支写法（与 paperwork2 同形）；④给这类"只在下一次才执行"的分支留一条**当场可跑**的等价判据（本批载体 `FIX` 行 = 从工具源码现读三格 + 复跑 rc），别把"没跑到的分支"登记成"已验证"。
→ **同族**：排查记录 §38.21 ①（同一族的第 1、2 次就记在那一节）、项目记忆 (95)"落地脚本三步序"、(65)"门只打印、不置退出码"、(82)"计数型安全门必须配阳性对照"；`feedback-verifiable-acceptance.md`"不许拿重跑链把 RED 洗成 GREEN""rc=0 必须蕴含产物已写出"。

[错误类型] **同一行箭头两端用了两把尺（"改前 B"按 LF 串长度、"终态 B"按盘上 CRLF 字节）⇒ 差值 @MIXD@ B 里有 @CRG@ 只字节其实是行尾的 CR，真追加只有 @TIEL@ B。这类"单行混尺"不会被任何计数闸抓到，因为两个数各自都对**
→ 症状：第三批第一遍载体（`hardware/@MIX@`）第 @MLINE@ 行写着 `DOC 改前 @ROWS0@ 行 / @S0@ B -> 盘上在册终态 @ROWS1@ 行 / @S1@ B`；同一批订正后载体（`hardware/@SAME@`）同一格写成 `... -> @ROWS1@ 行 / @S1@ B`。两只载体的"终态"逐字相等（@S1@ B），差别只在"改前"那一只：@SB0@ - @MB0@ = @CRG@ = 改前那 @ROWS0@ 行每行 1 只 CR。
→ 为什么它危险：这一行的用途是"证明本批只做了追加、做了多大一段"。混尺不改变方向（还是变大），所以没人会起疑；但它把本批规模夸大约 @RATIO@ 倍，而这类夸大会被后面的批次当基准引用（例如"§38.24 那一段写了约 8 KB"）。同一族的更早版本是 §38.22 那种"两把尺互不可换算"，区别是那次是**跨行**，这次藏在**同一行**里。
→ 正确做法：①一行内出现两个以上量，必须同尺，且把尺子写进那一行（本批起：`DOC` 行末固定带"两格同尺 = 行尾 CRLF 的落盘字节数"）；②给这行装反查执行者：`crlf(终态串) 长度 == 盘上现读大小`（本遍现算 = @SAMEDISK@，不等即 ABORT，禁止裸 CR/LF 混进 CRLF 文件）；③横向扫一遍同类工具：盘上含 `DOC 改前` 且含 `getsize(DOC)` 的工具共 @NTOOLS@ 只，其中仍按 LF 串长度算改前的 = @STILLMIX@（这些**只点名不追改**，因为它们各自的载体已落地；下次复跑到它们时按本条换口径）；④对已落地的混尺行按规矩不回写，只在订正行里点名（本批载体 `RULER` 行就是这件事的执行者）。
→ **同族**：上一条的 ④、项目记忆 (56)"行尾也是一把尺子"（本条是它在**同一行内部**的形态）、(47)"同一个东西常有第二把尺子，改数之前先把所有尺子各跑一遍"、(73)"口径越界：把 A 集合的读数说成 B 集合的"、(87)"摘要类读数必须点名哪个函数 + 是否截断"；`feedback-verifiable-acceptance.md`"数字连算法与漏判"。
""".replace('@H@', FSEC + '：复跑支第一次跑就红 + 载体同一行两把尺）新增 %d 条（根族：**错都在"只在下一批才执行"和"同一行两把尺"这两类判据上**）' % N_ENTRY)
assert BS not in FREQ_SEC or True  # 反斜杠与占位符的终检在 SUBS 回填之后（见下方 FREQ_SEC 终检）

# ---------- 排查记录 §38.25 ----------
SEC_BODY = """@SEC@ R56 第四批 = 上一遍 POSCTL 第一次跑红（复跑支双计一只空行）+ 载体同一行两把尺（本遍现跑于 @T@；**没烧录、没碰串口、没 push、屏侧零进展**）

- **触发（是闸自己响，不是我去找错）**：第三批落地器把 §38.24 与那 2 条**写盘之后**，最后一步 POSCTL 复跑上一批工具 `r56_paperwork2.py` ⇒ **rc=1**。等式右边是"在册终态行数 + 尾段行数 + `GLUE_F`"，而 `GLUE_F`（本批 FreqErr 标题上方那只空行）已经被"在册终态"本身数过一遍 ⇒ 盘上现算比在册多 1 行。这一支在 paperwork2 写盘那一遍是 `else` 分支、**一次也没执行过** = §38.21 ① 那一族第 3 次命中。
- **现场形状（要点）**：崩的那一遍文档已经落了（§38.24 + 2 条在盘上）、工具载体没写（崩在写载体之前）⇒ 看起来像"归档被改坏了"。按规矩**不回滚已落地正文**：本批只在 §38.25 与 FreqErr 里点名，`r56_paperwork3.py` 与 `FreqErr.md` 的第三批那一段一字未动（前缀等式见载体 `WINDOW` 行）。
- **修的是工具，不是数**：只改 `r56_paperwork2.py` 的复跑支（等式里去掉那只 `GLUE_F`，并补 `assert GLUE_F == 1` 把"标题上方有空行"从加数升成闸），同族第三处也当场一起修：`r56_paperwork3.py` 的 `kinds(freq_final) - K0 == N_ENTRY` 在 REWROTE 下拿全量比本批增量 ⇒ 本批一落它就会红，已改成 tail-scoped 两分支。**三格现读**（不是抄上一遍的话）：`int(_m.group(4)) + len(_tail_f)` 在册 = @FIXNEW@ / 被剔除的 `GLUE_F + len(_tail_f)` 还在 = @FIXOLD@ / `assert GLUE_F == 1` 在册 = @FIXGLUE@。
- **同遍第二次撞见：同一行两把尺**。第三批第一遍载体（`hardware/@MIX@`）第 @MLINE@ 行"改前 B"用 **LF 串长度** @S0@ B、"终态 B"用**盘上 CRLF 字节** @S1@ B ⇒ 箭头差 @MIXD@ B；订正后载体（`hardware/@SAME@`）两格同尺，真追加 = @TIEL@ B。换算式：(@S1@ - @S0@) - (@S1@ - @SB0@) = @CRG@ = 改前那 @ROWS0@ 行每行 1 只 CR，本遍现算成立 = @CRCHK@。
- **横向扫了一遍同类（避免只修被抓到的那一处）**：`hardware/` 下同时含 `DOC 改前` 与 `getsize(DOC)` 的落地工具共 **@NTOOLS@ 只**；其中"改前"仍按 LF 串长度算的 = @STILLMIX@。这些**只点名不追改**（它们各自的载体已落地，回写等于改取证），下一次复跑到它们时按本批口径换。
- **与上一批的分界**：§38.24 落盘于 @P3AT@（载体 = `hardware/@MIX@`，订正后 = `hardware/@SAME@`），它的在册读数（台账那串"未勾选名单"不可复算 / 全史 @REVHIT@）本批**不复算、不引用为新证据**；屏侧读数全部停在 §38.23 那一遍（四臂 66 条 `0x34` 行 / 应答 0 / `VERDICT=FOUR-ARMS-ALL-NACK`）。
- **本节没做（点名，绑定执行者）**：①**本遍**（paperwork，@T@）零串口动作，本遍列口 = `@COM@`，COM14 @COM14@；②没换电池 / 没万用表 / 没接第二块板（§38.23 那两条物理分叉仍在用户侧）；③没改 `main/` 源码、没重建固件 ⇒ 待烧仍是 `fb32168a…`、板上仍是 `4842a3a0…`，(92) 那条"待烧 = 板上"的等式仍在断裂处；④没勾或改 `todo.md` 那 @CNT@ 只未选项；⑤没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 只在内存假名 `@PROBE@` = 本遍 @ARMS@），也没新建清单代次 ⇒ gen 24 仍是末版（`TOTAL @RT@` / `@RB@ B` / BOM `@RBOM@`，末版 @SEAL_AT@，本遍复核 `rc=@VRC@`，载体 `@VMC@`）；⑥没 push、没 amend、零删除；⑦docs 快照第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本节之后 ⇒ 本遍不预写它们的数。
> 本节对应 `FreqErr.md` 那 @N@ 条在册（标题前缀 `@FSEC@`），取证载体 = `hardware/@CAR@`（本遍写的那一只：FIX / RULER / MIXED-SAME / HIST 同族扫描 / SEAL + GATE + VM + POSCTL + WITNESS）。
"""

SUBS = {'@SEC@': SEC, '@T@': NOW_AT, '@N@': str(N_ENTRY), '@CAR@': os.path.basename(CARRIER),
        '@FSEC@': FSEC, '@MIX@': os.path.basename(MIXED), '@SAME@': os.path.basename(SAME),
        '@COM@': _com, '@COM14@': '缺席' if 'COM14' not in _com else '在册',
        '@PROBE@': PROBE, '@ARMS@': ARMS_FIRED,
        '@FIXNEW@': str(FIX_NEW), '@FIXOLD@': str(FIX_OLD), '@FIXGLUE@': str(FIX_GLUE),
        '@CRCHK@': str(CR_GAP == M_ROWS0 and S_B0 - M_B0 == M_ROWS0), '@NTOOLS@': str(len(_mix_how)),
        '@STILLMIX@': ' + '.join(STILL_MIX) if STILL_MIX else '无（都已换同尺口径）',
        '@S0@': money(M_B0), '@MB0@': money(M_B0), '@SB0@': money(S_B0), '@S1@': money(S_B1),
        '@MIXD@': money(M_B1 - M_B0), '@TIEL@': money(S_B1 - S_B0), '@CRG@': money(CR_GAP),
        '@RATIO@': str(round((M_B1 - M_B0) / float(S_B1 - S_B0), 2)),
        '@MLINE@': str(M_LINE), '@SAMEDISK@': str(SAMEDISK),
        '@ROWS0@': money(M_ROWS0), '@ROWS1@': money(M_ROWS1), '@P3AT@': _p3_at,
        '@REVHIT@': '无一版产出过它',
        '@CNT@': str(CNT_TODO), '@CMD_TODO@': CMD_TODO,
        '@RT@': GEN_TOTAL, '@RB@': money(int(GEN_BYTES)), '@RBOM@': GEN_BOM, '@SEAL_AT@': SEAL_AT,
        '@VRC@': str(_v.returncode), '@VMC@': VM_CARRIER}
for _k, _val in SUBS.items():
    SEC_BODY = SEC_BODY.replace(_k, _val)
    FREQ_SEC = FREQ_SEC.replace(_k, _val)
assert not re.search(r'@[A-Za-z0-9_]+@', FREQ_SEC), 'ABORT: FreqErr 本批段还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', FREQ_SEC)[:3]
assert BS not in FREQ_SEC, 'ABORT: FreqErr 本批段含反斜杠（§38.18 那一族）'
assert 'zizhao1' not in FREQ_SEC, 'ABORT: 正文含 SoftAP 口令明文'
assert not re.search(r'%[sd]', FREQ_SEC), 'ABORT: FreqErr 本批段还有没吃参数的 %% 占位（会被当字面量落盘）：%r' % [
    l[:70] for l in FREQ_SEC.split('\n') if re.search(r'%[sd]', l)][:2]
assert not re.search(r'@[A-Za-z0-9_]+@', SEC_BODY), 'ABORT: §38.25 还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', SEC_BODY)[:3]
assert not re.search(r'%[sd]', SEC_BODY), 'ABORT: §38.25 还有没吃参数的 %% 占位：%r' % [
    l[:70] for l in SEC_BODY.split('\n') if re.search(r'%[sd]', l)][:2]
assert BS not in SEC_BODY, 'ABORT: §38.25 含反斜杠（§38.18 那一族）'
assert 'zizhao1' not in SEC_BODY, 'ABORT: 正文含 SoftAP 口令明文'
_SECTREF = re.compile(r'§(\d+(?:\.\d+)+)')
for _t, _tag in ((SEC_BODY, '§38.25'), (FREQ_SEC, 'FreqErr 本批段')):
    for _n in sorted(set(_SECTREF.findall(_t))):
        if _n == SECNUM:
            continue
        assert any(re.match(r'#{2,4} +' + re.escape(_n) + r'(?![0-9])', l) for l in lf(doc_pre).split('\n')), \
            'ABORT: %s 引用了 §%s，而改前排查记录里没有这个标题行（假指针）' % (_tag, _n)

LED_TPL = ('> **【@T@ 落地｜R56 第四批 @N@ 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'           '全文 `^[错误类型]` 条数 = **@K0@**、`wc -l` 行数 = **@L0@**；`hardware/20260919_墨水屏点屏排查记录.md`'
           '行数 = **@D0@**；本批之后现算（在同一次调用里对最终串再数一遍）：条数 = **@K1@**、行数 = **@L1@**；'
           '本批对应排查记录 §@SN@，取证载体 = `hardware/@CAR@`。\n')


def build(freq_base, doc_base):
    base = lf(freq_base).rstrip('\n') + '\n\n' + lf(FREQ_SEC).rstrip('\n') + '\n'
    k1, l1 = kinds(base), nl(base) + 1
    led = LED_TPL
    for _k, _val in {'@T@': NOW_AT, '@N@': str(N_ENTRY), '@K0@': str(K0), '@L0@': str(L0),
                     '@K1@': str(k1), '@L1@': str(l1), '@CAR@': os.path.basename(CARRIER),
                     '@SN@': SECNUM, '@D0@': str(DOC_ROWS0)}.items():
        led = led.replace(_k, _val)
    assert not re.search(r'@[A-Za-z0-9_]+@', led), 'ABORT: 台账行还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', led)[:5]
    assert BS not in led, 'ABORT: 台账行含反斜杠（§38.18 那一族）'
    final = crlf(base + led)
    assert kinds(final) == k1 and nl(final) == l1, 'ABORT: 台账行在册的两把尺与最终串不等 ⇒ (99) 那句是假话'
    assert '§' + SECNUM in led, 'ABORT: 台账行没点名本节节号'
    dfin = crlf(lf(doc_base).rstrip('\n') + '\n\n' + lf(SEC_BODY).rstrip('\n') + '\n')
    return final, dfin


if MODE == 'LANDED_NOW':
    freq_final, doc_final = build(freq_pre, doc_pre)
    assert re.match(r'^> \*\*【' + TS + ' 落地｜R56 第四批', lf(freq_final).split('\n')[-2]), 'ABORT: 台账行没落在末行前'
else:
    freq_final, doc_final = freq_disk, doc_disk
    WIN_F = _fl[_hf[0]:_led[0] + 1]
assert (kinds(freq_final) - K0 == N_ENTRY) if MODE == 'LANDED_NOW' \
    else (kinds(freq_disk) - K0 == N_ENTRY + TAIL_KF), \
    'ABORT: 本批正文 `[错误类型]` 增量不是 %d（现算 %d / 尾段 %d）' % (N_ENTRY, kinds(freq_disk) - K0, TAIL_KF)
if MODE == 'LANDED_NOW':
    _fl2 = lf(freq_final).split('\n')
    WIN_F = _fl2[starts(freq_final, FSEC)[0]:]
    _df = lf(doc_final).split('\n')
    WIN_D = _df[[i for i, l in enumerate(_df) if l.startswith(SEC)][0]:-1]
    GLUE_D = 1     # build() 写的是 `doc_base.rstrip + '\n\n' + body` ⇒ 上方那只空行由本遍亲手插进

# ---------- "本批终态" = 盘上现读 − 尾段（第三批的载体就是这么从 3722 漂成 3733 的）----------
# 载体的"改前 -> 终态"讲的是**本批窗口**；拿 live 盘长当终态 ⇒ 下一批一落，箭头变成跨批的和、
#   每只重写的载体读数互不相等（§38.21 ① 那一族第 5 次命中的现场，见 hardware/r56_paperwork3_5.txt 的 RULER-SELF 两行）。
_df0 = lf(doc_disk).split('\n')
assert _df0[-1] == '' and len(_df0) - 1 == nl(doc_disk), \
    'ABORT: 行数尺子对不上（尾行 %r / 行数 %d vs `\\n` 计数 %d）' % (_df0[-1], len(_df0) - 1, nl(doc_disk))
SELF_ROWS1 = nl(doc_disk) - TAIL_D
SELF_STR = ''.join(l + '\n' for l in _df0[:SELF_ROWS1])
SELF_B1 = len(crlf(SELF_STR).encode('utf-8'))
TAIL_STR = ''.join(l + '\n' for l in _df0[SELF_ROWS1:-1])
SELF_K1 = kinds(freq_disk) - TAIL_KF
SELF_L1 = nl(freq_disk) - len(_tail_f)
SELF_TIE = SELF_B1 + len(crlf(TAIL_STR).encode('utf-8')) == os.path.getsize(DOC)
assert SELF_TIE, 'ABORT: 本批终态 %d B + 尾段 %d B != 盘上 %d B ⇒ 终态/尾段切分没覆盖整只文件' % (
    SELF_B1, len(crlf(TAIL_STR).encode('utf-8')), os.path.getsize(DOC))
assert SELF_ROWS1 == DOC_ROWS0 + GLUE_D + len(WIN_D), \
    'ABORT: 本批终态行数 %d != 改前 %d + 上方空行 %d + 本批节 %d' % (SELF_ROWS1, DOC_ROWS0, GLUE_D, len(WIN_D))
assert SELF_K1 == K0 + N_ENTRY, 'ABORT: 本批终态条数 %d != 改前 %d + %d 条' % (SELF_K1, K0, N_ENTRY)
if MODE == 'REWROTE_CARRIER_ONLY':
    assert (SELF_K1, SELF_L1) == (_RK1, _RL1), \
        'ABORT: 扣尾段得到的本批终态 (%d,%d) != 台账行在册终态 (%d,%d)' % (SELF_K1, SELF_L1, _RK1, _RL1)

if MODE == 'LANDED_NOW':
    open(FREQ, 'wb').write(freq_final.encode('utf-8'))
    open(DOC, 'wb').write(doc_final.encode('utf-8'))

# ---------- 前向对照：复跑上一批落地器（它现在跑的是第三批之后的盘）----------
_r = subprocess.run([sys.executable, P3], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = ' | '.join(l[:110] for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT=', 'FREQ ')))
assert _r.returncode == 0 and _pos, 'ABORT: 前向对照（复跑第三批落地器）rc=%d ⇒ 本批追加把它弄红了，先查再落' % _r.returncode

PRE_EQ_F = lf(freq_disk).startswith(lf(freq_pre).rstrip('\n'))
PRE_EQ_D = lf(doc_disk).startswith(lf(doc_pre).rstrip('\n'))
assert PRE_EQ_F and PRE_EQ_D, 'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 本批不只做了追加'
_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
_lines = [
    'R56 第四批 paperwork 落地器  MODE=%s' % MODE,
    '本遍现跑于 %s（台账行标题时刻 = %s；载体由脚本自己落盘，在归档目录之外）' % (_now2, NOW_AT),
    'FIX 复跑支修复的现场三格（本遍从 %s 源码现读）：等式含 `int(_m.group(4)) + len(_tail_f)` = %s / '
    '含被剔除的 `GLUE_F + len(_tail_f)` = %s / 含 `assert GLUE_F == 1` = %s；同族第三处 = %s 的 '
    '`kinds(freq_final) - K0 == N_ENTRY` 已改成 tail-scoped 两分支（本遍现读含 else 分支 = %s）' % (
        os.path.basename(P2), FIX_NEW, FIX_OLD, FIX_GLUE, os.path.basename(P3),
        'else (kinds(freq_disk) - K0 == N_ENTRY + TAIL_KF)' in rd(P3)),
    'FIX 第一次 POSCTL rc=1 的那一遍**没有出错工具自己的载体**（崩在写载体之前）⇒ 该次崩溃是叙述级证据；'
    '本遍能落的是"修复后源码三格现读 + 复跑 rc=%d"，两者合起来只证明**现在的复跑支是对的**，不证明它曾经对过' % _r.returncode,
    'RULER 混尺订正（两只载体逐字现读）：`hardware/%s` 第 20 行 = 改前 %s B（LF 串长度）-> 终态 %s B（盘上 CRLF）⇒ 箭头 %s B；'
    '`hardware/%s` 同一格 = 改前 %s B（同尺）-> 终态 %s B ⇒ 真追加 %s B；夸大约 %s 倍' % (
        os.path.basename(MIXED), money(M_B0), money(M_B1), money(M_B1 - M_B0),
        os.path.basename(SAME), money(S_B0), money(S_B1), money(S_B1 - S_B0), _RATIO),
    'RULER 换算式（本遍现算）：(%s - %s) - (%s - %s) = %d = 改前那 %s 行每行 1 只 CR ⇒ 成立 = True；'
    '反查 `crlf(盘上现读串) 长度 == 盘上大小` = %s（%s B）' % (
        money(M_B1), money(M_B0), money(S_B1), money(S_B0), CR_GAP, money(M_ROWS0), SAMEDISK, money(DISK_B_NOW)),
    'HIST 同族横向扫描（本遍从 %s 目录现扫，不是点名我记得的那几只）：含 `DOC 改前` 且含 `getsize(DOC)` 的工具 = %d 只 = %s；'
    '其中"改前"仍按 LF 串长度算 = %s ⇒ 只点名不追改' % (
        'hardware/', len(_mix_how), ' + '.join(f for f, _b in _mix_how), ' + '.join(STILL_MIX) if STILL_MIX else '无'),
    'MIXED-SAME 两只对照物的身份：md5(%s)=%s / md5(%s)=%s；两者"终态"两格逐字相等 = %s' % (
        os.path.basename(MIXED), md5_(MIXED)[:8], os.path.basename(SAME), md5_(SAME)[:8],
        (M_ROWS1, M_B1) == (S_ROWS1, S_B1)),
    'LEDGER 新口径首跑（承 §38.24 那格换代：命令原文 + 本次输出同落纸）：`%s` 输出 = %d（本遍现跑；本遍同样没动它们）' % (CMD_TODO, CNT_TODO),
    'SEAL 清单在册=%d 行 / 目录全量=%d 只 / %s B / 差集逐只点名=%s / mtime 秒数全部 <= 末版那一秒 %s' % (
        len(_rows), DISK_N, money(DISK_B), ' + '.join(NOT_LISTED), SEAL_AT),
    'GATE %s（假名 %s 只在内存；盘上反查不存在 = %s）' % (ARMS_FIRED, PROBE, not os.path.exists(os.path.join(SYNC, PROBE))),
    'GEN 末版=代次日志末行 %s（本批未新建代次）' % _glog_last.replace(chr(9), ' / '),
    'VM 本遍真跑 rc=%d / %s / VM_CARRIER=%s' % (_v.returncode, _vm_rows[0], VM_CARRIER),
    'FIELD rev-list=%s / comports=%s / COM14 %s / 本遍零串口动作 / 屏亮肉眼确认 0 次 / 未播提示音' % (
        REV_LIST_NOW, _com, '缺席' if 'COM14' not in _com else '在册'),
    'FREQ 改前 %d 条 / %d 行 -> %s %d 条 / %d 行' % (K0, L0, '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
                                                SELF_K1, SELF_L1),
    'DOC 改前 %d 行 / %s B -> %s %d 行 / %s B（两格同尺 = 行尾 CRLF 的落盘字节数；反查 终态 %s B + 尾段 %d 行 == 盘上现读 %s B = %s）' % (
        DOC_ROWS0, money(DOC_B0D), '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
        SELF_ROWS1, money(SELF_B1), money(SELF_B1), TAIL_D, money(os.path.getsize(DOC)), SELF_TIE),
    'RULER-SELF 终态那把尺扣尾段（承第三批那一格的第 5 次命中，本遍起两批工具同尺）：本批窗口右界剥掉了下一批（若已落）'
    '插进来的空行 glue ⇒ 终态 = 盘上 %d 行 − 尾段 %d 行 = %d 行；FreqErr 同理 %d 条 / %d 行；'
    '窗口等式 改前 %d + 上方空行 %d + 本批节 %d = 终态 = %s' % (
        nl(doc_disk), TAIL_D, SELF_ROWS1, SELF_K1, SELF_L1, DOC_ROWS0, GLUE_D, len(WIN_D),
        DOC_ROWS0 + GLUE_D + len(WIN_D) == SELF_ROWS1),
    'WINDOW 前缀等式（"只追加、正文一字未改"）：FreqErr %d 行是盘上 %d 行的逐字前缀 = %s / 排查记录 %d -> %d 行 = %s；'
    '本批窗口 = FreqErr %d 行 + §38.25 %d 行' % (
        nl(freq_pre), nl(freq_disk), PRE_EQ_F, DOC_ROWS0, nl(doc_disk), PRE_EQ_D, len(WIN_F), len(WIN_D)),
    'POSCTL 复跑第三批落地器 rc=%d / %s' % (_r.returncode, _pos),
    'WITNESS FREQ md5=%s / DOC md5=%s（本遍结束时现算）' % (md5_(FREQ)[:8], md5_(DOC)[:8]),
    'NOTDONE 本遍（%s）没做：串口 / 烧录 / 换电池 / 万用表 / 第二块板 / 改 main 源码 / 重建固件 / 勾或改那 %d 只未选项 / '
    '新建备份根 / 新建清单代次 / push / amend / 删除 —— 屏亮 0 次肉眼确认 ⇒ 未播提示音；'
    'todo 第十七遍、docs 第十遍、backups README 第十次读数、提交轮#9、第 14 代同步在本节之后 ⇒ 本遍不预写它们的数' % (_now2, CNT_TODO),
    'VERDICT=%s（两只 CRLF 目标里本遍写盘 %d 只 + 载体 1 只）' % (
        'OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY', 2 if MODE == 'LANDED_NOW' else 0),
]
_txt = '\n'.join(_lines) + '\n'
assert BS not in _txt, 'ABORT: 载体行里有反斜杠（§38.18 那一族）：%r' % [l for l in _lines if BS in l][:2]
assert 'zizhao1' not in _txt, 'ABORT: 载体含口令明文'
assert not re.search(r'@[A-Za-z0-9_]+@', _txt), 'ABORT: 载体行还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', _txt)[:3]
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write(_txt)
print('MODE=%s FIX=%s/%s/%s 同族工具=%d 仍混尺=%s' % (MODE, FIX_NEW, FIX_OLD, FIX_GLUE, len(_mix_how), STILL_MIX or '无'))
print('RULER 混尺箭头=%d 同尺真追加=%d CR差额=%d == 改前行数 %d' % (M_B1 - M_B0, S_B1 - S_B0, CR_GAP, M_ROWS0))
print('FREQ 改前 %d 条 / %d 行 -> %d 条 / %d 行' % (K0, L0, kinds(freq_final), nl(freq_final)))
print('VERDICT=OK CARRIER=%s' % os.path.basename(CARRIER))
print('POSCTL rc=%d %s' % (_r.returncode, _pos[:200]))
