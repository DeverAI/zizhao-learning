# R56 第五批 = 第四批那两处修补的**落纸遍**（终态那把尺按分支各取 + 对照物按现算值分组 + 写侧支永假在落盘前先推）
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 新增 §38.26
#   ② FreqErr.md（CRLF）—— 本批 3 条新错误类型 + 台账行（两把尺在最终串上现算，(99)）
#   ③ hardware/r56_paperwork5.txt（LF，载体，本脚本自己落盘，在归档目录之外）
# 触发：§38.25 只订正了 paperwork2/3 的源码，那句"终态扣尾段"没落成判据；本批要真跑写侧支（LANDED_NOW），
#   落盘前把 paperwork4 的等式在纸上推了一遍 ⇒ 它排在写盘之前，在 LANDED_NOW 分支里就是"改前行数"，
#   与同一支的 `assert GLUE_D == 1` 矛盾 ⇒ 永假（§38.21 ① 那一族第 6 次命中，形态与前三次相反）。
#   本工具的改法 = 终态按分支各取 + 等式仍前置于写盘 + 写盘后拿**盘上字节**反查（POSTWRITE）。
# 幂等：`### 38.26` 已在盘上 ⇒ MODE=REWROTE_CARRIER_ONLY，一字节都不写那两只 CRLF 文件。
# 实际经过（两遍）：第一遍真跑写侧支，两只 CRLF 正文**已落盘**，随后死在自己新加的 `assert POSTWRITE`（那一格当时只比
#   rd() 的归一串 vs CRLF 终态串 ⇒ 永假，§38.21 ① 那一族第 7 次命中）。处置：正文不回滚，第二遍走复跑支补载体，
#   反查改为字节比字节，另加"仓库外改前快照"的独立前缀反查（SNAPPREFIX）证明崩的那一遍只做了追加。
import hashlib
import os
import re
import subprocess
import sys
import tempfile
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
P4 = os.path.join(HDIR, 'r56_paperwork4.py')
# 对照载体（三代口径）不在这里写死文件名：MIXED / LIVE / SAME 由下面那段"按现算值分组"点名
GLOG = os.path.join(SYNC, 'evidence', 'manifest_gen_log.txt')
MAN = os.path.join(SYNC, 'MANIFEST.txt')
TS = '[0-9-]{10} [0-9:]{8}'
SEC = '### 38.26'
SECNUM = '38.26'
FSEC = '## 2026-09-24（R56 第五批'
N_ENTRY = 3
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_cands = ['r56_paperwork5.txt'] + ['r56_paperwork5_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)
# 本工具进目录时已在册的**槽位**载体（= 本工具自己写得了的那批名字，减去本遍这一只）⇒ 载体里的 PHOTO 行据此说明"第几张照片 / 哪张权威"。
#   按槽位名单挑、不按 startswith 前缀扫：`r56_paperwork5_fix.txt` 是订正遍那只工具的载体，前缀扫会把它算成本工具的第 N 张照片
_PHOTOS = sorted([f for f in _cands
                  if f != os.path.basename(CARRIER) and os.path.exists(os.path.join(HDIR, f))],
                 key=lambda f: os.path.getmtime(os.path.join(HDIR, f)))


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

# ---------- 本批"进入时刻"的时间界：所有目录扫描用它截断 ----------
#   前向对照（POSCTL）复跑上一批/上上批落地器时，它们会各自往 hardware/ 新增一只载体 ⇒ "在册唯一一只""共 N 只"
#   这类口径若把本遍自己造出来的东西扫进去，就是"检查动作污染被检查物"（R46 (60) 那一族）。
#   界 = 本批台账行标题时刻（已在册 ⇒ 复跑遍稳定）；台账行还没写（写侧支那一遍）⇒ 界 = 那一刻（POSCTL 还没跑）。
_LEDROW = re.search(r'^> \*\*【(' + TS + r') 落地｜R56 第五批', lf(rd(FREQ)), re.M)
BATCH_START = (datetime.strptime(_LEDROW.group(1), '%Y-%m-%d %H:%M:%S').timestamp()
               if _LEDROW else datetime.now().timestamp())


def _pre_batch(f):
    return os.path.getmtime(os.path.join(HDIR, f)) < BATCH_START


_POLL = sorted(f for f in os.listdir(HDIR)
               if re.match(r'^r56_paperwork\d.*\.txt$', f) and not _pre_batch(f))

# ---------- 三代口径：对照物按【本遍现算值】分组点名（既不硬编码文件名，也不扫载体里写着的字样）----------
_C3 = [f for f in sorted(os.listdir(HDIR))
       if f.startswith('r56_paperwork3') and f.endswith('.txt') and _pre_batch(f)]
assert len(_C3) >= 3, 'ABORT: hardware/ 下只扫到 %d 只 r56_paperwork3*.txt ⇒ 三代口径缺代，换算式落不了纸' % len(_C3)


def _doc_row(path):
    rows = [l for l in lf(rd(path)).split('\n') if l.startswith('DOC 改前')]
    assert len(rows) == 1, 'ABORT: %s 里 DOC 行命中 %d 处' % (os.path.basename(path), len(rows))
    m = re.search(r'DOC 改前 (\d+) 行 / ([\d,]+) B -> (\S+) (\d+) 行 / ([\d,]+) B', rows[0])
    assert m, 'ABORT: %s 的 DOC 行格式抓不出来' % os.path.basename(path)
    return (int(m.group(1)), int(m.group(2).replace(',', '')), m.group(3),
            int(m.group(4)), int(m.group(5).replace(',', '')), rows[0])


def _line_of(text, needle):
    hits = [i + 1 for i, l in enumerate(lf(text).split('\n')) if needle in l]
    assert len(hits) == 1, 'ABORT: 源码里 %r 命中 %d 处 ⇒ 那条按行序的推断不成立' % (needle[:28], len(hits))
    return hits[0]


_T = dict((f, _doc_row(os.path.join(HDIR, f))) for f in _C3)
_R0 = sorted(set(v[0] for v in _T.values()))
assert len(_R0) == 1, 'ABORT: %d 只载体的"改前行数"有 %s 种 ⇒ 它们标的不是同一次追加' % (len(_C3), _R0)
M_ROWS0 = _R0[0]
_B0 = sorted(set(v[1] for v in _T.values()))
assert len(_B0) == 2, 'ABORT: "改前 B" 有 %s 种取值 ⇒ 两把"改前"尺没分开' % [money(x) for x in _B0]
assert _B0[1] - _B0[0] == M_ROWS0, 'ABORT: 两种"改前 B"之差 %d != 改前行数 %d ⇒ 它们不是 LF/盘上那两把尺' % (
    _B0[1] - _B0[0], M_ROWS0)
# "终态"那格取的是哪一刻，载体自己用字样登记：`盘上在册终态` = 打印那一刻的盘长；`本批在册终态` = 扣掉尾段。
#   只按 (改前 B, 终态 B) 分不够：同一支脚本、同一个口径，跑的时刻不同读数就不同（②代那两只正是这样）。
_LBL_LIVE = '盘上' + '在册终态'      # 拆两段拼出来：本工具往自己的载体行里也写这五个字（R42 自指那一族）
_LBL_TAIL = '本批' + '在册终态'
_LBL = sorted(set(v[2] for v in _T.values()))
assert set(_LBL) <= set([_LBL_LIVE, _LBL_TAIL]), 'ABORT: 出现了第三种"终态"字样 %s ⇒ 下面按两种取法分的类不再成立' % _LBL


def _key(f):
    v = _T[f]
    return ('LF' if v[1] == _B0[0] else 'CRLF', _LBL_LIVE if v[2] == _LBL_LIVE else _LBL_TAIL)


def _uniform(g, nm):
    for _i, _tag in ((1, '改前 B'), (3, '终态行数'), (4, '终态 B')):
        _s = sorted(set(_T[f][_i] for f in g))
        assert len(_s) == 1, 'ABORT: %s 组的"%s"有 %s 种 ⇒ 拿任何一只当代表都不对' % (nm, _tag, _s)


_G = {}
for f in _C3:
    _G.setdefault(_key(f), []).append(f)
assert set(_G) == set([('LF', _LBL_LIVE), ('CRLF', _LBL_LIVE), ('CRLF', _LBL_TAIL)]), \
    'ABORT: 两把"改前"尺 × 两种"终态"取法切出的组 = %s ⇒ 与本批要落的三代口径不符，别照旧文案落' % sorted(_G)
MIX_F = sorted(_G[('LF', _LBL_LIVE)])       # ①一代：改前按 LF 串长度、终态按 live 盘长
LIVE_F = sorted(_G[('CRLF', _LBL_LIVE)])    # ②二代：两格同尺，终态仍按 live 盘长
SAME_F = sorted(_G[('CRLF', _LBL_TAIL)])    # ③三代：两格同尺，终态扣掉尾段
_uniform(MIX_F, '一代')
_uniform(SAME_F, '三代')
assert len(LIVE_F) >= 2, 'ABORT: ②代口径只有 %d 只 ⇒ "同一支脚本、只是跑的时刻不同"没有对照样本，本批主证落不了纸' % len(LIVE_F)
_BT = sorted(set(_T[f][4] for f in LIVE_F))
assert len(_BT) == 2, 'ABORT: ②代那 %d 只的终态格取值只有 %s ⇒ 漂移没落在纸上' % (len(LIVE_F), [money(x) for x in _BT])
B_EARLY = sorted(f for f in LIVE_F if _T[f][4] == _BT[0])
B_LATE = sorted(f for f in LIVE_F if _T[f][4] == _BT[1])
_uniform(B_EARLY, '②代早')
_uniform(B_LATE, '②代晚')
MIXED, LIVE, SAME = [os.path.join(HDIR, f) for f in (MIX_F[0], B_LATE[0], SAME_F[0])]
_M, _L, _E, _S = _T[MIX_F[0]], _T[B_LATE[0]], _T[B_EARLY[0]], _T[SAME_F[0]]
M_B0, M_LBL, M_ROWS1, M_B1 = _M[1], _M[2], _M[3], _M[4]
L_B0, L_LBL, L_ROWS1, L_B1 = _L[1], _L[2], _L[3], _L[4]
E_B0, E_LBL, E_ROWS1, E_B1 = _E[1], _E[2], _E[3], _E[4]
S_B0, S_LBL, S_ROWS1, S_B1 = _S[1], _S[2], _S[3], _S[4]
assert (E_B0, E_ROWS1, E_B1) == (S_B0, S_ROWS1, S_B1), \
    'ABORT: ②代早那只 (%d,%d,%d) 与③代 (%d,%d,%d) 不等 ⇒ 下面那句"live 取值当时看不出错"不再成立' % (
        E_B0, E_ROWS1, E_B1, S_B0, S_ROWS1, S_B1)
_AT = dict((f, re.search(r'本遍现跑于 (' + TS + ')', lf(rd(os.path.join(HDIR, f)))).group(1)) for f in _C3)
_AT4 = _AT[B_LATE[0]]
# 字样分组 vs 值分组（本批那条"选物自指"判据的证据，全在本遍现算）
_TXTMARK = '两格' + '同尺'          # 同上：拆两段拼出来
_BY_TEXT = sorted(f for f in _C3 if _TXTMARK in _T[f][5])
assert _BY_TEXT, 'ABORT: 按字样一个也没扫到 ⇒ "字样分组"这条反例落不了纸'
assert set(_BY_TEXT) == set(B_EARLY) | set(B_LATE) | set(SAME_F), \
    'ABORT: 字样名单 = %s，而"两格同尺"两种取法的并 = %s ⇒ 本批这条反例的形状变了' % (
        _BY_TEXT, sorted(set(B_EARLY) | set(B_LATE) | set(SAME_F)))
_TXT_SPANS = sorted(set((_T[f][1], _T[f][4]) for f in _BY_TEXT))
assert len(_TXT_SPANS) > 1, 'ABORT: 按字样扫出来的名单恰好只覆盖一种取值 ⇒ "字样 ≠ 取法"这一遍没落在纸上'
CR_GAP = M_B1 - M_B0 - (S_B1 - S_B0)
assert CR_GAP == M_ROWS0, 'ABORT: 混尺差值与同尺差值之差 %d != 改前行数 %d ⇒ 一代↔三代换算式不成立' % (CR_GAP, M_ROWS0)
assert S_B0 - M_B0 == M_ROWS0, 'ABORT: 同尺改前 %d - 混尺改前 %d != %d 只 CR' % (S_B0, M_B0, M_ROWS0)
assert L_B1 > S_B1 and L_ROWS1 > S_ROWS1, 'ABORT: ②代晚的终态没有比③代大 ⇒ "live 盘长"那条错没落在纸上'
DRIFT_ROWS = L_ROWS1 - E_ROWS1                    # 两只同口径载体之间只差了"跑的那一刻盘上有没有第四批"
DRIFT_BYTES = L_B1 - E_B1
TAIL_ROWS = L_ROWS1 - S_ROWS1
TAIL_BYTES = L_B1 - S_B1
assert (DRIFT_ROWS, DRIFT_BYTES) == (TAIL_ROWS, TAIL_BYTES), \
    'ABORT: 同口径漂移 (%d 行, %d B) != 与③代的差 (%d 行, %d B) ⇒ "漂的就是下一批那一段"这条换算式不成立' % (
        DRIFT_ROWS, DRIFT_BYTES, TAIL_ROWS, TAIL_BYTES)
SAMEDISK = len(crlf(rd(DOC)).encode('utf-8')) == os.path.getsize(DOC)
assert SAMEDISK, 'ABORT: 排查记录盘上现读 != crlf(串) 长度 ⇒ 文件里有裸 CR/LF'
DISK_B_NOW = os.path.getsize(DOC)
assert S_B1 > S_B0 and M_B1 > M_B0, 'ABORT: 一代/三代载体的箭头不是递增 ⇒ 换算式的分母不成立'
_RATIO = '%.2f' % ((M_B1 - M_B0) / float(S_B1 - S_B0))   # 混尺箭头 / 同尺真追加 = 夸大的倍数
_MD5S = [md5_(p) for p in (MIXED, LIVE, SAME)]
assert len(set(_MD5S)) == 3, 'ABORT: 三只代表物里有两只内容逐字相同 ⇒ 分出来的"代"其实指同一只，换算式没有对照组'
# 本遍第一版只按两个数 (改前 B, 终态 B) 分组、另外要求组内字样齐 ⇒ 进脚本就 ABORT。
#   这里把它复原一遍当反证：同一取值组里确实混着两种口径。
_SAMEVAL = sorted(f for f in _C3 if _T[f][1] == _B0[1] and _T[f][4] == S_B1)
LBL_OFF = sorted(f for f in _SAMEVAL if _T[f][2] != S_LBL)
assert len(LBL_OFF) >= 1, 'ABORT: 与③代同取值的 %d 只字样全一致 ⇒ "取值相同而口径不同"这条反证没落在纸上' % len(_SAMEVAL)
TODO = os.path.join(REPO, 'todo.md')
CNT_TODO = len([l for l in lf(rd(TODO)).split('\n') if l.startswith('- [ ]')])
CMD_TODO = "grep -cF -- '- [ ]' todo.md"

# ---------- 修复现场的三格现读（paperwork2/3/4 源码；本遍现读，不抄上一遍载体里写的话）----------
_p2 = rd(P2)
FIX_NEW = 'int(_m.group(4)) + len(_tail_f)' in _p2
FIX_OLD = 'GLUE_F + len(_tail_f)' in _p2
FIX_GLUE = 'assert GLUE_F == 1' in _p2
assert FIX_NEW and not FIX_OLD and FIX_GLUE, 'ABORT: paperwork2 复跑支还没修好（%s/%s/%s）' % (FIX_NEW, FIX_OLD, FIX_GLUE)
_p3, _p4 = rd(P3), rd(P4)
F_TRIM3 = "while _dwin_end > _hd[0] and _dl[_dwin_end - 1].strip() == '':" in _p3
F_TRIM4 = "while _dwin_end > _hd[0] and _dl[_dwin_end - 1].strip() == '':" in _p4
F_TERM = 'SELF_ROWS1 = nl(doc_disk) - TAIL_D'
F_TERM3, F_TERM4 = F_TERM in _p3, F_TERM in _p4
assert F_TRIM3 and F_TRIM4 and F_TERM3 and F_TERM4, 'ABORT: 上一批那两个补丁（剥 glue + 终态扣尾段）在源码里不齐（%s/%s/%s/%s）' % (
    F_TRIM3, F_TRIM4, F_TERM3, F_TERM4)
# 本遍落盘前先推的第二格：paperwork4 那条"扣尾段"等式跑在**写盘之前** ⇒ 在 LANDED_NOW 分支里
#   `nl(doc_disk)` 就是改前快照，而同一支把 GLUE_D 钉成 1、WIN_D 又非空 ⇒ 等式两边永不相等。
L4_GLUE = _line_of(_p4, 'GLUE_D = 1     # build()')
L4_TERM = _line_of(_p4, F_TERM)
L4_WRITE = _line_of(_p4, "open(FREQ, 'wb')")
assert L4_GLUE < L4_TERM < L4_WRITE, 'ABORT: paperwork4 里那三件事的先后变了（%d/%d/%d）⇒ 下面那条"永假"推断不再成立，别落' % (
    L4_GLUE, L4_TERM, L4_WRITE)
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
assert ('r56_paperwork5.py', False) in _mix_how, 'ABORT: 本工具没被自己的扫描认出来（或它已变混尺）⇒ 扫描器不可信'
STILL_MIX = [f for f, bad in _mix_how if bad]
assert len(_mix_how) >= 2, 'ABORT: 横向自查只扫到 %d 只含 DOC 行的工具 ⇒ 半径不够，别说"同族"' % len(_mix_how)

# ---------- 进入时现读两只 CRLF 文件 + 幂等闸 ----------
for p in (FREQ, DOC):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 追加会造出混行尾' % p
freq_disk, doc_disk = rd(FREQ), rd(DOC)
_hf, _hd = starts(freq_disk, FSEC), starts(doc_disk, SEC)
assert len(_hf) <= 1 and len(_hd) <= 1, 'ABORT: 本批标题命中 %d / %d 处 ⇒ 已重复追加' % (len(_hf), len(_hd))
MODE = 'REWROTE_CARRIER_ONLY' if _hf or _hd else 'LANDED_NOW'
assert bool(_hf) == bool(_hd), 'ABORT: §38.26 与 FreqErr 本批节"存在性"不一致 ⇒ 上一遍落了一半'
_fl = lf(freq_disk).split('\n')
GLUE_D = TAIL_KF = TAIL_D = 0
_tail_f = []
LED_TS = NOW_AT     # 写侧支那一遍：台账行由本遍亲手写，标题时刻就是进入时刻
if MODE == 'REWROTE_CARRIER_ONLY':
    _led = [i for i, l in enumerate(_fl) if l.startswith('> **【') and '落地｜R56 第五批 %d 条】**' % N_ENTRY in l]
    assert len(_led) == 1 and _led[0] > _hf[0], 'ABORT: 本批台账行命中 %d 只 / 不在本批标题之下' % len(_led)
    LED_TS = re.search(TS, _fl[_led[0]]).group(0)
    assert _LEDROW and LED_TS == _LEDROW.group(1), \
        'ABORT: 盘上台账行标题时刻 %s != 取时间界时读到的 %s ⇒ 两遍之间 FreqErr 又被动过' % (LED_TS, _LEDROW and _LEDROW.group(1))
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
    assert GLUE_D == 1, 'ABORT: §38.26 标题上方没有空行 ⇒ 追加形状变了'
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
PROBE = 'evidence/SEAL_VIOLATION_PROBE5.txt'
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
REV_TOTAL = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], cwd=REPO,
                           capture_output=True, text=True).stdout.strip()
assert REV_TOTAL.isdigit() and int(REV_TOTAL) >= int(REV_LIST_NOW)

# ---------- 上一批（第四批）在册载体：只认本批进入之前那一只（界之后的都是 POSCTL 复跑所造，见 _POLL）----------
_P4C = [f for f in sorted(os.listdir(HDIR))
        if f.startswith('r56_paperwork4') and f.endswith('.txt') and _pre_batch(f)]
assert len(_P4C) == 1, 'ABORT: 上一批在册载体扫到 %d 只（%s）⇒ "上一批在册读数"该引哪一只说不清，别落' % (
    len(_P4C), _P4C)
CARPREV = _P4C[0]
ATPREV = re.search(r'本遍现跑于 (' + TS + ')', lf(rd(os.path.join(HDIR, CARPREV)))).group(1)

# ---------- LEDGER 那格"本口径第几次跑"现算（不凭记忆写"首跑"）----------
_CARN = re.compile(r'^r56_paperwork(\d).*\.txt$')
_LED = dict((f, len([l for l in lf(rd(os.path.join(HDIR, f))).split('\n') if l.startswith('LEDGER')]))
            for f in sorted(os.listdir(HDIR))
            if _CARN.match(f) and f != os.path.basename(CARRIER) and _pre_batch(f))
_LED = dict((f, n) for f, n in _LED.items() if n)
assert _LED, 'ABORT: 目录里没有一只含 LEDGER 行的既有载体 ⇒ "本口径第几次跑"无从现算，只能凭记忆写'
_LED_G = sorted(set(_CARN.match(f).group(1) for f in _LED))
assert _LED_G == ['3', '4'], 'ABORT: 含 LEDGER 行的载体来自代次 %s ⇒ 与"§38.24（第三批）首跑 + 第四批第二次"不符，本遍不能写成第三次' % _LED_G
_LED_MARK = '新口径' + '首跑'      # 拆开拼：本工具这一行自己也含那五个字（R42 自指那一族）
_LED_BAD = sorted(f for f in _LED if _LED_MARK in lf(rd(os.path.join(HDIR, f))))
assert _LED_BAD == [CARPREV], 'ABORT: 写着"新口径首跑"的既有载体 = %s，不是上一批那一只 %s ⇒ 订正句指错了对象' % (
    _LED_BAD, CARPREV)
LEDGER_RUNS = 'LEDGER 本口径第 %d 次落到纸面' % (len(_LED_G) + 1)

# ---------- FreqErr 本批段（正文 3 条）----------
FREQ_SEC = """@H@

> 一句话总纲：本批屏侧一个字节没动（没烧录、没碰串口，本遍只 `comports()` 只读列口 = @COM@），
> 抓到的三条都在**取证尺子本身**：终态那把尺取错了时刻、对照物按字样挑、以及上一遍的订正把写侧那一支修成了永假。

[错误类型] **「本批终态」那把尺取的是"打印那一刻的盘上长度"（live 盘长）⇒ 下一批一追加，上一批载体里的箭头就跨了两批。本遍现算：同一支第三批脚本、同一个"两格同尺"口径，只因跑的时刻不同留下两只载体 —— 早的那只（`hardware/@EARLY@`）终态 @EROWS1@ 行 / @EB1@ B，晚的那只（`hardware/@LIVE@`）终态 @LROWS1@ 行 / @LB1@ B ⇒ 箭头从 @TIEL@ B 漂成 @LD@ B；两个数各自都对，错在它们量的不是同一段时间（§38.21 ① 那一族第 5 次命中的本体）**
→ 症状：晚那只的字面写法是 `DOC 改前 @LB0@ B -> 盘上在册终态 @LROWS1@ 行 / @LB1@ B`。"改前"取的是**本脚本进入时**的快照，"终态"取的却是**打印那一行时**的盘上长度 ⇒ 两格之间夹着"本批之后又落的批"。本遍现算：@LB1@ − @EB1@ = **@DRIFTB@ B / @DRIFTROWS@ 行**，恰好等于第四批（§38.25）追加的那一段（它那节 + 它上方的 glue 空行）⇒ 漂移量可复算，不是猜的。
→ **它最险的一半是"当场看不出错"**：早那只的 (@EB0@, @EROWS1@, @EB1@) 与③代扣尾段后的三格**逐字相等**（本遍现算 = @EQES@，载体 `RULER-2ND` 行就是执行者）⇒ live 取值在"后面还没落东西"那一遍不产生任何错误读数。所以这条判据不能等它跑红，只能靠"终态那一格必须指名它数的是哪一刻"这个构造规矩。
→ 为什么它危险：箭头的作用是"证明本批只做了追加、做了多大一段"。取 live 盘长不改变方向（还是变大），所以不起疑；但它让**同一批的几只载体互相对不上**，于是下一个查案的人（包括我）会先怀疑"归档被人改坏了"，而真正要修的只是自己那行取值。§38.25 登记的是"同一行两把尺"，本条是它的姊妹：**同一行两把"同一把尺、不同时刻"**。
→ 正确做法：①终态 = **本遍产出的最终串**（MODE=LANDED_NOW）或 **盘上现读 − 尾段**（MODE=REWROTE_CARRIER_ONLY），两分支各自指名它数的是哪一刻；②窗口右界必须剥掉"下一批落纸时插进来的那只 glue 空行"（否则尾段少算 1 行，终态多算 1 行）；③给这条切分装反查执行者：`终态 B + 尾段 B == 盘上现读 B`，不等即 ABORT（本遍现算见载体 `RULER-SELF` 行）；④已落地的②代两只载体按规矩**不回写**，只在订正行里点名（本批载体 `RULER-2ND` 行就是这件事的执行者）。
→ **同族**：上一条的姊妹 = §38.25 在册那两条里的第 2 条（同一行两把尺）、项目记忆 (56)"行尾也是一把尺子"、(47)"同一个东西常有第二把尺子，改数之前先把所有尺子各跑一遍"、(73)"口径越界：把 A 集合的读数说成 B 集合的"、(96)"末段须按行区间复核"。

[错误类型] **挑选"对照物"时按载体正文里写着的字样扫（`两格同尺`）= 自指：本工具往每只载体里都写那四个字 ⇒ 从第二遍起只只命中；而把对照物文件名硬编码进脚本 = 换一代就无声失配。本批改成按【本遍现算值】分组点名，名单是分组的结果、不是输入**
→ 症状（本遍现算，两种挑法各跑一遍）：目录 `hardware/` 下 `r56_paperwork3*.txt` 共 @NC@ 只带 `DOC 改前` 行；按字样扫到 **@NTXT@ 只**（@TXTLIST@），它们横跨 **@TXTSPANS@ 种** `(改前 B, 终态 B)` 取值 ⇒ 这份名单把"终态取 live 盘长"与"终态扣尾段"两种口径混在一起（它恰好 = "②+③"之并，等值 = @TXTIS23@ ⇒ 它切开的只是"有没有写那句括注"，不是口径）；按现算的两把尺（改前 B 取 LF 还是盘长 × 终态字样）分组 = @NGRP@ 组：①代 @MIXN@ 只 / ②代 @LIVEN@ 只（早 @EARLYN@ + 晚 @LATEN@）/ ③代 @SAMEN@ 只。
→ 为什么它危险：这类挑法**读起来像取证**（"我扫了目录，不是凭记忆点的名"），实际是拿"我写过什么"当"盘上是什么"。它的失败方向也不是红，而是**默默把不该进对照组的载体拉进组**，然后那条换算式就用被污染的组算出来——上一遍那条换算式（§38.25 在册）就是这么险的：它若用字样名单，"终态"两格里会混进两个不同值，而脚本只取第一只，取到哪只看运气。
→ 正确做法：①输入 = 目录枚举 + 本遍现算的读数，组内还要再核"读数齐不齐"（不齐即 ABORT，禁止拿任何一只当代表）；②把两种挑法的**差集当反例落纸**（就是上面那两个数），别只登记"我现在用的是对的那一种"；③被搜串若在工具自己的正文里出现，仍按 R42 那一族拆开拼（本遍 @TXTMARK@ 就拆成了两段）——此处扫描半径只有载体，拆开是防御性的，不是必需的，这句也说清；④"改前 B 只有两种取值、且差 == 改前行数"这种**换算式前置闸**要写在分组之前，否则分组本身没有判据。
→ **同族**：项目记忆 (42)"自指计数永不'写下即真'"、(96)"取证脚本输入文件不得硬编码"、(85)"阳性对照样本可只在内存"；§38.25 在册第 2 条 ③（横向扫描工具时同一条拆开拼的规矩）。

[错误类型] **上一遍的订正只在复跑支成立 ⇒ 它顺手把"写盘那一支"修成了永假：paperwork4 的 `SELF_ROWS1 = nl(doc_disk) − 尾段` 排在写盘**之前**，而 LANDED_NOW 分支里 `doc_disk` 就是改前快照、同一支又钉 `GLUE_D == 1` 且 `WIN_D` 非空 ⇒ `终态 == 改前 + 空行 + 本批节` 无解。这是 §38.21 ① 的**镜像**：先前是"复跑支从没跑过所以错没被发现"，这次是"写侧支一跑就红"（第 6 次命中，本遍在落盘**前**推出并修好）**
→ 症状（本遍按行序现读 `r56_paperwork4.py` 源码，不靠跑它）：`GLUE_D = 1`（LANDED_NOW 分支内）在第 @L4GLUE@ 行、终态等式在第 @L4TERM@ 行、写盘在第 @L4WRITE@ 行 ⇒ @L4GLUE@ < @L4TERM@ < @L4WRITE@ = @L4ORDER@。等式跑在写盘前 ⇒ 该分支里 `nl(doc_disk)` == 改前行数，尾段又为 0 ⇒ 要求 `GLUE_D + len(WIN_D) == 0`，与 `assert GLUE_D == 1` 直接矛盾。
→ 为什么它危险：这条错**不会**在第四批暴露（它那时已落地 ⇒ 幂等闸只放行复跑支），只在下一个新批次第一次 LANDED_NOW 时暴露；好在它 fail 的方向是"拒绝写盘"（文档不会被改成半截），代价是那一遍什么取证都不产出，现场形如"第五批跑红了、盘上没动"——按上一批的经历，那种现场最容易被误读成"我把归档改坏了"而去回滚。
→ 正确做法：①两分支共用的量必须各自指明"它是哪一刻的盘"：本批把终态改成从**即将写出的最终串**取（LANDED_NOW）/ 从盘上减尾段取（REWROTE），并把等式仍然留在写盘**之前**（校验前置于写盘）；②写盘后**立即重读盘**反查一次（`crlf(最终串) == 盘上现读`），前向判据与事后反查各算一遍；③凡"只在另一条分支被跑过的判据"，落盘前先在纸上把两条分支各推一遍，把推断依据（行序、常数值）一起落纸；④工具修好 ≠ 判据落纸：本批就是第四批那两处修补（剥 glue、终态扣尾段）的落纸遍，`SEC` 里逐格点名。
→ **同族**：§38.21 ①（这一族的正身）、§38.25 在册第 1 条（复跑支第一次跑就红）、项目记忆 (94)"校验必须前置于写盘"、(95)"落地脚本三步序"、(82)"rc=0 必须蕴含产物已写出"。
""".replace('@H@', FSEC + '：终态那把尺取错时刻 + 对照物按字样挑（自指）+ 上一遍订正把写侧支修成永假）新增 %d 条（根族：**尺子各自都对，但量的不是同一段时间 / 同一件事**）' % N_ENTRY)

# ---------- 排查记录 §38.26 ----------
SEC_BODY = """@SEC@ R56 第五批 = 第四批那两处修补的落纸遍（本遍现跑于 @T@；**没烧录、没碰串口、没 push、屏侧零进展**）

- **触发（本遍是"落盘前先推"，不是跑红以后才补）**：§38.25 只订正了两只工具的源码（剥窗口右界的 glue、"本批终态"改成扣尾段），按该节自己那句"本轮按规矩只订正工具源码" ⇒ **判据本身没落纸**。本批要跑同一形状的写侧分支（LANDED_NOW），落盘前把 paperwork4 的等式在纸上推了一遍：`SELF_ROWS1 = nl(doc_disk) − 尾段` 排在写盘之前（源码第 @L4TERM@ 行 vs 第 @L4WRITE@ 行，`GLUE_D = 1` 在第 @L4GLUE@ 行）⇒ 在 LANDED_NOW 分支里它就是"改前行数"，等式要求 `GLUE_D + 本批节行数 == 0`，与同一支的 `assert GLUE_D == 1` 矛盾 ⇒ **永假**。= §38.21 ① 那一族第 6 次命中，形态与前三次相反：先前是"复跑支从没跑过"，这次是"修对了复跑支、把写侧支修死"。
- **本遍怎么修的**：`hardware/r56_paperwork5.py` 里把终态那把尺改成**按分支各取**——写盘那一遍从"即将写出的最终串"取，复跑那一遍仍从"盘上现读 − 尾段"取；等式仍留在写盘**之前**（校验前置），并新增写盘后反查：重读盘 + `crlf(最终串) == 盘上现读 B`（结果见载体 `POSTWRITE` 行）。前两只工具的源码本批一字不动。
- **三代口径（对照物按现算值分组点名，不硬编码文件名、也不扫载体里的字样）**：同一格 `DOC 改前 -> 终态` 在第三批那 @NC@ 只载体里按**两把尺**切开 = 3 组（键 = "改前 B 取 LF 串长还是盘上字节" × "终态字样写 盘上在册 还是 本批在册"）——
  ①代（改前按 LF + 终态取 live）@MB0@ B -> @MB1@ B，箭头 @MIXD@ B = `hardware/@MIX@` 等 @MIXN@ 只；
  ②代（两格同尺、终态仍取 live）@LB0@ B -> @LB1@ B，箭头 @LD@ B = `hardware/@LIVE@`（晚）+ `hardware/@EARLY@`（早）共 @LIVEN@ 只；
  ③代（两格同尺、终态扣尾段）@SB0@ B -> @SB1@ B，真追加 @TIEL@ B = `hardware/@SAME@` 等 @SAMEN@ 只。
  三条换算式本遍现算：①↔③ `(@MB1@ − @MB0@) − (@SB1@ − @SB0@) = @CRG@ = 改前那 @ROWS0@ 行每行 1 只 CR`（= @CRCHK@）；②内两只同口径 `@LB1@ − @EB1@ = @DRIFTB@ B / @EROWS1@ → @LROWS1@ 行` = **第四批追加的那一段**（它那节 + 上方 glue）⇒ "终态漂了"可复算，不是形容词；②早 与 ③ 的三格 (@EB0@,@EROWS1@,@EB1@) 逐字相等 = @EQES@ ⇒ **live 取值在"后面还没落东西"那一遍不产生任何错误读数**，所以这条判据不能等它跑红。
- **两种挑对照物的方法各跑一遍（本批那条自指判据的证据）**：按字样 `两格同尺` 扫 = **@NTXT@ 只**（@TXTLIST@），横跨 @TXTSPANS@ 种 `(改前B, 终态B)` 取值 ⇒ 它把②代和③代混在一起（与"②+③ 之并"逐字等值 = @TXTIS23@）；按现算值分组 = @NGRP@ 组 @NC@ 只，组内读数齐（不齐即 ABORT）。反证一并落纸：本遍第一版只按 `(改前 B, 终态 B)` 两个数分组、又要求组内字样齐 ⇒ 进脚本就 ABORT，因为与③代同取值的 @SAMEVALN@ 只里，字样写"盘上在册"而非"本批在册"的 = @LBL_OFF@ ⇒ **取值相同而口径不同，字样必须进键**。已落地的②代两只（`hardware/@LIVE@`，落盘于 @AT4@）按规矩**不回写**，只在这里点名。
- **与上一批的分界**：§38.25 那一遍现跑于 @ATPREV@（载体 = `hardware/@CARPREV@`，本遍进入时枚举到的唯一一只），它的在册读数本批**不复算、不引用为新证据**；屏侧读数全部停在 §38.23 那一遍（四臂 66 条 `0x34` 行 / 应答 0 / `VERDICT=FOUR-ARMS-ALL-NACK`），本批依旧零串口动作 ⇒ 那条"待烧 = 板上"的断裂（(92)）位置不变。
- **本节没做（点名，绑定执行者）**：①**本遍**（paperwork，@T@）零串口动作，本遍列口 = `@COM@`，COM14 @COM14@；②没换电池 / 没万用表 / 没接第二块板；③没改 `main/` 源码、没重建固件 ⇒ 待烧仍是 `fb32168a…`、板上仍是 `4842a3a0…`；④没勾或改 `todo.md` 那 @CNT@ 只未选项（本遍只现读：`@CMD_TODO@` = @CNT@）；⑤没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 只在内存假名 `@PROBE@` = 本遍 @ARMS@），也没新建清单代次 ⇒ gen 24 仍是末版（`TOTAL @RT@` / `@RB@ B` / BOM `@RBOM@`，末版 @SEAL_AT@，本遍复核 `rc=@VRC@`，载体 `@VMC@`）；⑥没 push、没 amend、零删除；⑦docs 快照第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本节之后 ⇒ 本遍不预写它们的数。
> 本节对应 `FreqErr.md` 那 @N@ 条在册（标题前缀 `@FSEC@`），取证载体 = `hardware/@CAR@`（本遍写的那一只：RULER-3GEN / RULER-2ND / SELFSCAN / FIX / POSTWRITE / SEAL + GATE + VM + POSCTL + WITNESS）。
"""

SUBS = {'@SEC@': SEC, '@T@': NOW_AT, '@N@': str(N_ENTRY), '@CAR@': os.path.basename(CARRIER),
        '@FSEC@': FSEC, '@COM@': _com, '@COM14@': '缺席' if 'COM14' not in _com else '在册',
        '@PROBE@': PROBE, '@ARMS@': ARMS_FIRED,
        '@MIX@': os.path.basename(MIXED), '@LIVE@': os.path.basename(LIVE), '@SAME@': os.path.basename(SAME),
        '@MIXN@': str(len(MIX_F)), '@LIVEN@': str(len(LIVE_F)), '@SAMEN@': str(len(SAME_F)),
        '@EARLYN@': str(len(B_EARLY)), '@LATEN@': str(len(B_LATE)),
        '@NC@': str(len(_C3)), '@NGRP@': str(len(_G)),
        '@NTXT@': str(len(_BY_TEXT)), '@TXTLIST@': ' + '.join(_BY_TEXT), '@TXTSPANS@': str(len(_TXT_SPANS)),
        '@TXTMARK@': _TXTMARK, '@AT4@': _AT4,
        '@CARPREV@': CARPREV, '@ATPREV@': ATPREV,
        '@MB0@': money(M_B0), '@MB1@': money(M_B1), '@LB0@': money(L_B0), '@LB1@': money(L_B1),
        '@SB0@': money(S_B0), '@SB1@': money(S_B1), '@LROWS1@': money(L_ROWS1),
        '@EARLY@': B_EARLY[0], '@EB0@': money(E_B0), '@EB1@': money(E_B1), '@EROWS1@': money(E_ROWS1),
        '@DRIFTB@': money(DRIFT_BYTES), '@DRIFTROWS@': str(DRIFT_ROWS),
        '@EQES@': str((E_B0, E_ROWS1, E_B1) == (S_B0, S_ROWS1, S_B1)),
        '@TXTIS23@': str(set(_BY_TEXT) == set(B_EARLY) | set(B_LATE) | set(SAME_F)),
        '@SAMEVALN@': str(len(_SAMEVAL)), '@LBL_OFF@': ' + '.join(LBL_OFF),
        '@ROWS0@': money(M_ROWS0), '@MIXD@': money(M_B1 - M_B0), '@LD@': money(L_B1 - L_B0),
        '@TIEL@': money(S_B1 - S_B0), '@CRG@': money(CR_GAP),
        '@CRCHK@': str(CR_GAP == M_ROWS0 and S_B0 - M_B0 == M_ROWS0),
        '@L4GLUE@': str(L4_GLUE), '@L4TERM@': str(L4_TERM), '@L4WRITE@': str(L4_WRITE),
        '@L4ORDER@': str(L4_GLUE < L4_TERM < L4_WRITE),
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
assert not re.search(r'@[A-Za-z0-9_]+@', SEC_BODY), 'ABORT: §38.26 还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', SEC_BODY)[:3]
assert not re.search(r'%[sd]', SEC_BODY), 'ABORT: §38.26 还有没吃参数的 %% 占位：%r' % [
    l[:70] for l in SEC_BODY.split('\n') if re.search(r'%[sd]', l)][:2]
assert BS not in SEC_BODY, 'ABORT: §38.26 含反斜杠（§38.18 那一族）'
assert 'zizhao1' not in SEC_BODY, 'ABORT: 正文含 SoftAP 口令明文'
_SECTREF = re.compile(r'§(\d+(?:\.\d+)+)')
for _t, _tag in ((SEC_BODY, '§38.26'), (FREQ_SEC, 'FreqErr 本批段')):
    for _n in sorted(set(_SECTREF.findall(_t))):
        if _n == SECNUM:
            continue
        assert any(re.match(r'#{2,4} +' + re.escape(_n) + r'(?![0-9])', l) for l in lf(doc_pre).split('\n')), \
            'ABORT: %s 引用了 §%s，而改前排查记录里没有这个标题行（假指针）' % (_tag, _n)

LED_TPL = ('> **【@T@ 落地｜R56 第五批 @N@ 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'           '全文 `^[错误类型]` 条数 = **@K0@**、`wc -l` 行数 = **@L0@**；`hardware/20260919_墨水屏点屏排查记录.md`'
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
    assert re.match(r'^> \*\*【' + TS + ' 落地｜R56 第五批', lf(freq_final).split('\n')[-2]), 'ABORT: 台账行没落在末行前'
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

# ---------- "本批终态"那把尺：按分支各取（上一遍两支共用 nl(doc_disk) ⇒ 写盘那一遍永假）----------
# 写盘那一遍 = 从**即将写出的最终串**取；复跑那一遍 = 从"盘上现读 − 尾段"取。窗口右界仍剥下一批的 glue。
_d_src = doc_final if MODE == 'LANDED_NOW' else doc_disk
_f_src = freq_final if MODE == 'LANDED_NOW' else freq_disk
SRC_TAG = '本遍产出的最终串' if MODE == 'LANDED_NOW' else '盘上现读 − 尾段'
_df0 = lf(_d_src).split('\n')
assert _df0[-1] == '' and len(_df0) - 1 == nl(_d_src), \
    'ABORT: 行数尺子对不上（尾行 %r / 行数 %d vs 换行数 %d）' % (_df0[-1], len(_df0) - 1, nl(_d_src))
SELF_ROWS1 = nl(_d_src) - TAIL_D
SELF_STR = ''.join(l + '\n' for l in _df0[:SELF_ROWS1])
SELF_B1 = len(crlf(SELF_STR).encode('utf-8'))
TAIL_STR = ''.join(l + '\n' for l in _df0[SELF_ROWS1:-1])
TAIL_B = len(crlf(TAIL_STR).encode('utf-8'))
SELF_K1 = kinds(_f_src) - TAIL_KF
SELF_L1 = nl(_f_src) - len(_tail_f)
SELF_TIE = SELF_B1 + TAIL_B == (len(crlf(doc_final).encode('utf-8')) if MODE == 'LANDED_NOW'
                                else os.path.getsize(DOC))
assert SELF_TIE, 'ABORT: 本批终态 %d B + 尾段 %d B != 该取的那把尺 ⇒ 终态/尾段切分没覆盖整只文件' % (SELF_B1, TAIL_B)
assert SELF_ROWS1 == DOC_ROWS0 + GLUE_D + len(WIN_D), \
    'ABORT: 本批终态行数 %d != 改前 %d + 上方空行 %d + 本批节 %d' % (SELF_ROWS1, DOC_ROWS0, GLUE_D, len(WIN_D))
assert SELF_K1 == K0 + N_ENTRY, 'ABORT: 本批终态条数 %d != 改前 %d + %d 条' % (SELF_K1, K0, N_ENTRY)
if MODE == 'REWROTE_CARRIER_ONLY':
    assert (SELF_K1, SELF_L1) == (_RK1, _RL1), \
        'ABORT: 扣尾段得到的本批终态 (%d,%d) != 台账行在册终态 (%d,%d)' % (SELF_K1, SELF_L1, _RK1, _RL1)

if MODE == 'LANDED_NOW':
    open(FREQ, 'wb').write(freq_final.encode('utf-8'))
    open(DOC, 'wb').write(doc_final.encode('utf-8'))
    _dq, _fq = rd(DOC), rd(FREQ)
    # 反查一律拿**盘上字节**比，不拿 rd() 的串：rd() 走通用换行，读回来是 LF 归一串，
    #   而 final 串是 CRLF ⇒ 两者永不相等（本工具第一次真跑就崩在这一格上，见载体 POSTWRITE-CRASH 行）
    POSTWRITE = (open(DOC, 'rb').read() == doc_final.encode('utf-8')
                 and open(FREQ, 'rb').read() == freq_final.encode('utf-8')
                 and os.path.getsize(DOC) == len(doc_final.encode('utf-8'))
                 and os.path.getsize(FREQ) == len(freq_final.encode('utf-8'))
                 and crlf_pure(DOC) and crlf_pure(FREQ)
                 and _dq == lf(doc_final) and _fq == lf(freq_final))
    assert POSTWRITE, 'ABORT: 写盘后盘上字节 != 本遍产出的最终串 ⇒ 上面那批终态读数对读者不成立，先查再落'
    doc_disk, freq_disk = _dq, _fq          # 之后的"盘上现读"一律指写盘**之后**那一份
    DISK_B_NOW = os.path.getsize(DOC)
    SAMEDISK = len(crlf(_dq).encode('utf-8')) == DISK_B_NOW
else:
    POSTWRITE = 'NA（本遍没写那两只 CRLF 目标）'

# ---------- 崩过一遍之后的独立反查：进入时的快照（在仓库之外、本遍自己 cp 的）是否是盘上的逐字前缀 ----------
#   复跑支里 doc_pre 是从**当前盘**切出来的 ⇒ PRE_EQ_D 自我成立、量不到"上一遍有没有只追加"。
#   快照是那一只文件在崩的那一遍**进入时**的完整字节，独立于当前盘。
_SNAPD = os.path.join(tempfile.gettempdir(), 'r56_pre_doc.md')
_SNAPF = os.path.join(tempfile.gettempdir(), 'r56_pre_freq.md')
# 订正遍往 §38.26 末尾追加的那几行**也在快照→现在的差集里** ⇒ 那条等式量的是"本批全部落在本节里的行"，不扣除订正遍。
#   （本工具第一版把它写成了 `len(WIN_D) − N_CORR`，于是订正遍一落纸就把这格弄红 —— 订正遍的 POSCTL 实测到，见那张载体。）
#   N_CORR 只用于把"崩的那一遍"与"订正遍"两份贡献分开报数。标记串拆两段拼出来（整串若在源码里，计数会自指）
_CORR = '- **订正' + '（第五批订正遍'
N_CORR = len([l for l in WIN_D if l.startswith(_CORR)]) if MODE == 'REWROTE_CARRIER_ONLY' else 0
# 差集要能拆回"崩的那一遍"与"订正遍"两份贡献，拆的依据不是记忆而是**位置**：订正句由落地器追加在本节末尾 ⇒
#   末 N_CORR 行逐行按前缀现核，任一不中即 ABORT（不核 ⇒ "哪 %d 行归订正遍"是这句脚本自己没执行者的断言）
CORR_TAIL = WIN_D[-N_CORR:] if N_CORR else []
CORR_AT_END = all(l.startswith(_CORR) for l in CORR_TAIL) if N_CORR else 'NA（本遍 §38.26 末尾没有订正句）'
if N_CORR:
    assert CORR_AT_END, 'ABORT: §38.26 末尾 %d 行里有不带头=订正标记的行 ⇒ 追加位置变了，两份贡献拆不开' % N_CORR
# "DOC 现在挂的 mtime 属于订正遍"这句也要有执行者：拿在册那条订正句自己的时刻与 DOC 的 mtime 对表
DOC_T_FIX = 'NA（§38.26 末尾没有订正句，DOC 的 mtime 仍属于崩的那一遍）'
if N_CORR:
    _fx_at = re.search(TS, CORR_TAIL[0]).group(0)
    _doc_mt = datetime.fromtimestamp(os.path.getmtime(DOC)).strftime('%Y-%m-%d %H:%M:%S')
    DOC_T_FIX = _fx_at == _doc_mt
    assert DOC_T_FIX, 'ABORT: 在册订正句的时刻 %s != DOC 的 mtime %s ⇒ "DOC 挂着订正遍那次写盘"这句没有执行者，别落' % (
        _fx_at, _doc_mt)
if MODE == 'REWROTE_CARRIER_ONLY':
    for _p, _nm in ((_SNAPD, '排查记录'), (_SNAPF, 'FreqErr')):
        assert os.path.exists(_p), 'ABORT: %s 的改前快照不在 %s ⇒ 复跑支没有独立于当前盘的前缀证据，别落 SNAPPREFIX 行' % (_nm, _p)
    _sd, _sf = open(_SNAPD, 'rb').read(), open(_SNAPF, 'rb').read()
    _dd, _df2 = open(DOC, 'rb').read(), open(FREQ, 'rb').read()
    SNAP_PRE = (_dd.startswith(_sd) and _df2.startswith(_sf))
    SNAP_D_DELTA, SNAP_F_DELTA = _dd[len(_sd):], _df2[len(_sf):]
    SNAP_ROWS = (SNAP_D_DELTA.count(b'\r\n'), SNAP_F_DELTA.count(b'\r\n'))
    SNAP_BARE = (SNAP_D_DELTA.count(b'\n') - SNAP_ROWS[0]) + (SNAP_F_DELTA.count(b'\n') - SNAP_ROWS[1])
    assert SNAP_PRE and SNAP_BARE == 0, \
        'ABORT: 快照(%s / %s B)不是盘上现读的逐字前缀，或追加段里有裸 LF（裸字节 %d）⇒ 崩的那一遍不只做了追加，先查' % (
            md5_(_SNAPD)[:8], md5_(_SNAPF)[:8], SNAP_BARE)
    assert SNAP_ROWS == (len(WIN_D) + GLUE_D, len(WIN_F) + GLUE_D), \
        'ABORT: 追加段行数 %s != 预期（§38.26 全部在册 %d 行（含订正遍 %d 行）+ glue %d / FreqErr 本批节含台账行 %d 行 + glue %d）⇒ 崩的那一遍落的不是本遍算的这一份' % (
            SNAP_ROWS, len(WIN_D), N_CORR, GLUE_D, len(WIN_F), GLUE_D)
else:
    SNAP_PRE = 'NA（本遍真跑写侧支，无需快照反查）'
    SNAP_ROWS = (0, 0)
    SNAP_BARE = 'NA'
    SNAP_D_DELTA = SNAP_F_DELTA = b''
# 跨遍对照：各张照片在册的"追加段 DOC N 行"一律**从那只载体现读**（不抄本遍记忆，也不硬编码数字）
PREV_SNAP_ROWS = PREV_TIE = 'NA（本遍真跑写侧支，进入时目录里没有本工具的照片）'
if MODE == 'REWROTE_CARRIER_ONLY' and _PHOTOS:
    _ps = []
    for _f in _PHOTOS:
        _pm = re.search(r'追加段 DOC (\d+) 行', rd(os.path.join(HDIR, _f)))
        assert _pm, 'ABORT: 照片 %s 里读不到"追加段 DOC N 行"那句 ⇒ 跨遍对照没有对照物' % _f
        _ps.append(int(_pm.group(1)))
    assert _ps == sorted(_ps), 'ABORT: 各照片在册的差集行数不是单调不减（%s）⇒ 有某遍看到的盘比更早那张还小，先查' % _ps
    PREV_SNAP_ROWS = _ps[0]      # 最早那张 = 崩的那一遍之后第一次落纸的读数，与"本遍差集 − 订正遍行数"同量纲
    PREV_TIE = SNAP_ROWS[0] - N_CORR == PREV_SNAP_ROWS
    assert PREV_TIE, 'ABORT: 本遍差集 %d 行 − 订正遍 %d 行 != 最早那张在册的 %d 行 ⇒ 两段差集对不上，先查是谁又写了盘' % (
        SNAP_ROWS[0], N_CORR, PREV_SNAP_ROWS)
SNAP_DB = os.path.getsize(_SNAPD) if os.path.exists(_SNAPD) else 'NA'
SNAP_FB = os.path.getsize(_SNAPF) if os.path.exists(_SNAPF) else 'NA'
# 快照目录只登记"在不在仓库之外"这个布尔量，不写原始路径 —— 路径带反斜杠，会撞本文件末尾那条 BS 门
SNAP_OUT = not os.path.abspath(os.path.dirname(_SNAPD)).startswith(os.path.abspath(REPO))

# 载体里那句"POSTWRITE 有四条腿"也是断言，得有执行者：从本文件源码现读逐条核对，缺一即 ABORT。
#   被搜串一律拆两段拼出来 —— 否则本文件自己的源码里就含着被搜串，这条核对永真（R42 那一族）
_self_src = rd(os.path.abspath(__file__))


def _j(a, b):
    return a + ' ' + b


_POST_LEGS = (_j("open(DOC, 'rb').read()", "== doc_final.encode('utf-8')"),
              _j('os.path.getsize(DOC)', "== len(doc_final.encode('utf-8'))"),
              _j('crlf_pure(DOC)', 'and crlf_pure(FREQ)'),
              _j('_dq == lf(doc_final)', 'and _fq == lf(freq_final)'))
POST_LEGS = sum(1 for m in _POST_LEGS if m in _self_src)
assert POST_LEGS == len(_POST_LEGS), \
    'ABORT: 本文件里 POSTWRITE 只找到 %d/%d 条腿 ⇒ 载体那句"四条腿"是假陈述：%r' % (
        POST_LEGS, len(_POST_LEGS), [m for m in _POST_LEGS if m not in _self_src])

# 快照早于崩的那一遍写盘，这条顺序也要现算而不是叙述：复跑支不写那两只文件 ⇒ 它们的 mtime 仍停在崩溃那遍
def _hms(p):
    return datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M:%S')


SNAP_T = (_hms(_SNAPD), _hms(_SNAPF))
DOC_T, FREQ_T = _hms(DOC), _hms(FREQ)
SNAP_BEFORE = (os.path.getmtime(_SNAPD) < os.path.getmtime(DOC)
               and os.path.getmtime(_SNAPF) < os.path.getmtime(FREQ))
assert SNAP_BEFORE, 'ABORT: 快照 mtime 不比目标文件早 ⇒ 它不是"崩的那一遍进入前"那一份，前缀证据作废'

# ---------- 前向对照：复跑上一批（第四批）落地器；同趟再复跑第三批，两批都绿才算本遍没踩坏归档 ----------
_r = subprocess.run([sys.executable, P4], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = ' | '.join(l[:110] for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT=', 'FREQ ')))
assert _r.returncode == 0 and _pos, 'ABORT: 前向对照（复跑第四批落地器 paperwork4）rc=%d ⇒ 本批追加把它弄红了，先查再落' % _r.returncode
_r2 = subprocess.run([sys.executable, P3], cwd=REPO, capture_output=True, text=True,
                     env=dict(os.environ, PYTHONUTF8='1'))
assert _r2.returncode == 0, 'ABORT: 复跑第三批落地器 paperwork3 rc=%d ⇒ 本批追加越过上一批把它弄红了' % _r2.returncode
_POLL2 = sorted(f for f in os.listdir(HDIR)
                if re.match(r'^r56_paperwork\d.*\.txt$', f) and not _pre_batch(f))

PRE_EQ_F = lf(freq_disk).startswith(lf(freq_pre).rstrip('\n'))
PRE_EQ_D = lf(doc_disk).startswith(lf(doc_pre).rstrip('\n'))
assert PRE_EQ_F and PRE_EQ_D, 'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 本批不只做了追加'
_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
_lines = [
    'R56 第五批 paperwork 落地器  MODE=%s' % MODE,
    '本遍现跑于 %s（台账行标题时刻 = %s；载体由脚本自己落盘，在归档目录之外。两值不等 ⇒ 本遍是复跑支，'
    '上一批的载体里这两值同形（那是 LANDED/REWROTE 的判别副证））' % (_now2, LED_TS),
    'PHOTO 本工具的第 %d 张照片（进入时在册 %s）⇒ 权威 = 本张（最新那张），前几张的内容不复算、不引用为新证据，只点名它们存在；'
    '本张相对更早各张的累计改动（不区分由哪一张引入）= ①措辞按崩溃事实改口 ②目录扫描加时间界（POSCTL 污染）'
    '③SNAP 等式改按 §38.26 全部在册行取（含订正遍那 %d 行，拆法见 SNAPPREFIX 行）：上一版把差集写成"本批节 − 订正遍"，'
    '于是订正句一落纸就把这格弄红（那条红由订正遍自己的 POSCTL 实测到，不是推的）'
    '④SNAPPREFIX 那格两只目标的 mtime 改成与在册订正句时刻现对表 —— 更早那张把它们一并标成"崩的那遍写盘时刻"，'
    '而 DOC 后来被订正遍写过 ⇒ 那句现在是假话 ⑤遍数改成现算 —— 更早那张硬编码"本遍就是那第三遍"，复跑之后同一句也成了假话。'
    '④⑤两处按规矩不回写，只在这里点名' % (
        len(_PHOTOS) + 1, ' + '.join(_PHOTOS) or '无', N_CORR),
    'FIX 上一批两处修补在源码里在册（本遍从 %s / %s 现读，不抄上一遍载体里写的话）：窗口右界剥 glue 那句 = %s / %s，'
    '"本批终态 = 盘上 − 尾段" 那句 = %s / %s ⇒ 两处修补在两只工具里都在，没只留在被点名的那一只上' % (
        os.path.basename(P3), os.path.basename(P4), F_TRIM3, F_TRIM4, F_TERM3, F_TERM4),
    'FIX 本遍新查（写侧支永假；按行序现读 %s 源码，没跑它）：`GLUE_D = 1`（LANDED_NOW 支内）在第 %d 行 < '
    '终态等式在第 %d 行 < 写盘在第 %d 行 = %s ⇒ 写盘那一遍里 `nl(doc_disk)` 就是改前快照，等式于是要求'
    '"上方空行 + 本批节 == 0"，与同一支的 `assert GLUE_D == 1` 矛盾 ⇒ 上一遍把复跑支修对的同时把写侧支修死'
    '（§38.21 ① 那一族第 6 次命中，形态与前三次相反）。本工具的改法 = 终态按分支各取（写盘那遍取即将写出的最终串 / '
    '复跑那遍取盘上 − 尾段），等式仍前置于写盘，写盘后另加 POSTWRITE 反查' % (
        os.path.basename(P4), L4_GLUE, L4_TERM, L4_WRITE, L4_GLUE < L4_TERM < L4_WRITE),
    'FIX 证据半径（本遍改口，点名）：上一遍"写侧支永假"从来没被执行过（它落完盘之后幂等闸只放行复跑支）'
    '⇒ 本遍第一次真跑那一支，两只 CRLF 正文**已写完盘**，随后死在自己新加的写盘后反查格上（机理见 POSTWRITE-CRASH 行）'
    '⇒ 崩溃那一遍没走到落载体那一步 ⇒ **本载体是第二遍（REWROTE_CARRIER_ONLY）的照片，整批的写侧支没有自己的载体**；'
    '"本载体是本批第一次真跑写侧支的照片"是本遍第一版落笔时的措辞（当时还没跑，属预写），现按事实改口登记，'
    '既有载体不回写、只在这里点名。paperwork4 那次 LANDED_NOW 到底怎么过的仍**没有它自己的载体可查**'
    '（在册那只 %s 记的是 REWROTE 那一遍，现跑于 %s）⇒ 那一段仍是叙述级证据' % (CARPREV, ATPREV),
    'RULER-3GEN 三代口径（对照物 = 本遍按现算的两把尺分组点名：既不硬编码文件名，也不扫载体里写着的字样。'
    '键 = "改前 B 是 LF 长度还是盘上字节" × "终态字样是 盘上在册 还是 本批在册"）：目录里 %d 只 `r56_paperwork3*.txt` 分 %d 组 = '
    '①代 %s（改前按 LF %s B -> live 盘长 %s B，箭头 %s B）/ ②代 %s（同尺 %s B -> live 盘长 %s B，箭头 %s B）/ '
    '③代 %s（同尺 + 扣尾段 %s B -> %s B，真追加 %s B）；混尺那条箭头是同尺真追加的 %s 倍' % (
        len(_C3), len(_G), ' + '.join(MIX_F), money(M_B0), money(M_B1), money(M_B1 - M_B0),
        ' + '.join(LIVE_F), money(L_B0), money(L_B1), money(L_B1 - L_B0),
        ' + '.join(SAME_F), money(S_B0), money(S_B1), money(S_B1 - S_B0), _RATIO),
    'RULER-2ND 三条换算式（本遍现算）：①↔③代 (%s − %s) − (%s − %s) = %d = 改前那 %s 行每行 1 只 CR = %s；'
    '②代两只同口径、只换了跑的时刻 %s − %s = %d B / %d − %d = %d 行 = 第四批已落的那一段（§38.25 那一节 + 其上方 glue）'
    '⇒ "终态漂了"是可复算量，不是形容词；②早那只 (%s, %s) 与③代逐字相等 = %s ⇒ live 取值当场看不出错，这条判据不能等红。'
    '反查 `crlf(盘上现读串) 长度 == 盘上大小` = %s（%s B）；②代两只（%s，现跑于 %s）按规矩不回写，只点名' % (
        money(M_B1), money(M_B0), money(S_B1), money(S_B0), CR_GAP, money(M_ROWS0), CR_GAP == M_ROWS0,
        money(L_B1), money(E_B1), DRIFT_BYTES, L_ROWS1, E_ROWS1, DRIFT_ROWS,
        money(E_ROWS1), money(E_B1), (E_B0, E_ROWS1, E_B1) == (S_B0, S_ROWS1, S_B1),
        SAMEDISK, money(DISK_B_NOW), ' + '.join(B_LATE), _AT4),
    'SELFSCAN 两种挑对照物的方法各跑一遍（本批那条"选物自指"判据的证据）：按字样 %s 扫 = %d 只（%s），'
    '其内部横跨 %d 种 (改前 B, 终态 B) 取值 = %s ⇒ ②代③代被混在一起（与"②+③ 之并"逐字等值 = %s）；'
    '按现算值分组 = %d 只分 %d 组（组内读数不齐即 ABORT）；两种名单的差集 = %s。'
    '反证一条（本遍第一版就是这么栽的）：只按 (改前 B, 终态 B) 两个数分组并要求字样齐 ⇒ 与③代同取值的 %d 只里，'
    '字样不是"本批在册终态"的 = %s ⇒ 取值相同而口径不同，标签必须进分组键。'
    '被搜串在源码里拆两段拼出来（扫描半径只含载体，拆开是防御性的，这句一并说清）' % (
        _TXTMARK, len(_BY_TEXT), ' + '.join(_BY_TEXT), len(_TXT_SPANS),
        ' + '.join('(%s, %s)' % (money(a), money(b)) for a, b in _TXT_SPANS),
        set(_BY_TEXT) == set(B_EARLY) | set(B_LATE) | set(SAME_F), len(_C3), len(_G),
        ' + '.join(sorted(set(_C3) - set(_BY_TEXT))) or '无',
        len(_SAMEVAL), ' + '.join(LBL_OFF)),
    'HIST 同族横向扫描（本遍从 %s 目录现扫，不是点名我记得的那几只）：含 `DOC 改前` 且含 `getsize(DOC)` 的工具 = %d 只 = %s；'
    '其中"改前"仍按 LF 串长度算 = %s ⇒ 只点名不追改' % (
        'hardware/', len(_mix_how), ' + '.join(f for f, _b in _mix_how), ' + '.join(STILL_MIX) if STILL_MIX else '无'),
    'MIX-ALIVE-SAME 四只代表物的身份（本遍现算 md5，三只主代表互不相同 = %s）：①代 %s=%s / ②代晚 %s=%s / '
    '②代早 %s=%s / ③代 %s=%s；它们的 `DOC` 行字样 = ①代 %s / ②代 %s / ③代 %s ⇒ "两格同尺"那句括注两种取法都写，'
    '只有取值能把它们分开。下面三格等式由分组构造保证（是分组的读数、不是新判据）：①与③"终态"两格逐字相等 = %s / '
    '②与③"改前"格逐字相等 = %s / ②晚与③"终态"格不等 = %s' % (
        len(set(_MD5S)) == 3, MIX_F[0], _MD5S[0][:8], B_LATE[0], md5_(os.path.join(HDIR, B_LATE[0]))[:8],
        B_EARLY[0], md5_(os.path.join(HDIR, B_EARLY[0]))[:8], SAME_F[0], _MD5S[2][:8],
        M_LBL, L_LBL, S_LBL, (M_ROWS1, M_B1) == (S_ROWS1, S_B1), L_B0 == S_B0, L_B1 != S_B1),
    LEDGER_RUNS + '。现算名单 = 目录里含 `^LEDGER` 行的既有载体 %d 只（代次 %s；本遍这一只 %s 已排除，否则复跑遍会把自己算成上一批）；'
    '上一批载体 %s 写的是"%s"，而它落笔时 §38.24（第三批）那一族 5 行 LEDGER 已在盘上 ⇒ "首跑"那句不成立，'
    '按规矩不回写、只在这里点名（订正句）' % (
        len(_LED), ' + '.join(_LED_G), os.path.basename(CARRIER), CARPREV, _LED_MARK),
    'LEDGER 本遍现跑（承 §38.24 那格换代：命令原文 + 本次输出同落纸）：`%s` 输出 = %d（本遍同样没动它们）' % (CMD_TODO, CNT_TODO),
    'SEAL 清单在册=%d 行 / 目录全量=%d 只 / %s B / 差集逐只点名=%s / mtime 秒数全部 <= 末版那一秒 %s' % (
        len(_rows), DISK_N, money(DISK_B), ' + '.join(NOT_LISTED), SEAL_AT),
    'GATE %s（假名 %s 只在内存；盘上反查不存在 = %s）' % (ARMS_FIRED, PROBE, not os.path.exists(os.path.join(SYNC, PROBE))),
    'GEN 末版=代次日志末行 %s（本批未新建代次）' % _glog_last.replace(chr(9), ' / '),
    'VM 本遍真跑 rc=%d / %s / VM_CARRIER=%s' % (_v.returncode, _vm_rows[0], VM_CARRIER),
    'FIELD rev-list=%s（口径 = `git rev-list --count origin/main..HEAD`，未推送提交数）/ 全史 `git rev-list --count HEAD` = %s '
    '/ comports=%s / COM14 %s / 本遍零串口动作 / 屏亮肉眼确认 0 次 / 未播提示音' % (
        REV_LIST_NOW, REV_TOTAL, _com, '缺席' if 'COM14' not in _com else '在册'),
    'FREQ 改前 %d 条 / %d 行 -> %s %d 条 / %d 行' % (K0, L0, '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
                                                SELF_K1, SELF_L1),
    'DOC 改前 %d 行 / %s B -> %s %d 行 / %s B（两格同尺 = 行尾 CRLF 的落盘字节数；终态那把尺 = %s；'
    '反查 终态 %s B + 尾段 %d B（%d 行）= 该取的那把尺 %s B = %s）；本批在册终态 %d 行里有 %d 行是订正遍落的（按位置现核 = %s），'
    '台账行在册的那格是"改前 %d"、不含本批终态 ⇒ 两处读数不冲突、不回写' % (
        DOC_ROWS0, money(DOC_B0D), '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
        SELF_ROWS1, money(SELF_B1), SRC_TAG, money(SELF_B1), TAIL_B, TAIL_D,
        money(SELF_B1 + TAIL_B), SELF_TIE, SELF_ROWS1, N_CORR, CORR_AT_END, DOC_ROWS0),
    'RULER-SELF 本批终态按分支各取（承上一批那一格：那一格两支共用 nl(doc_disk)，于是把写侧支修成永假）：'
    '本遍取法 = %s ⇒ 终态行数 %d = 盘上现读 %d 行 − 尾段 %d 行；FreqErr 同理 %d 条 / %d 行；'
    '窗口等式 改前 %d + 上方空行 %d + 本批节 %d 行（含订正遍 %d 行）= 终态 = %s' % (
        SRC_TAG, SELF_ROWS1, nl(doc_disk), TAIL_D, SELF_K1, SELF_L1, DOC_ROWS0, GLUE_D, len(WIN_D), N_CORR,
        DOC_ROWS0 + GLUE_D + len(WIN_D) == SELF_ROWS1),
    'POSTWRITE 写盘后反查（本遍 MODE=%s；复跑遍那一支不写盘，整格记 NA）：判据 = 盘上字节 == 最终串的字节 ∧ '
    '现读大小 == 最终串 CRLF 编码长度 ∧ 纯 CRLF ∧ rd() 读回的归一串 == lf(最终串)，四条同取 = %s / '
    '现读大小 DOC = %s B、FreqErr = %s B' % (
        MODE, POSTWRITE, money(os.path.getsize(DOC)), money(os.path.getsize(FREQ))),
    'POSTWRITE-CRASH 崩溃取证（本遍第一遍 = 真跑写侧支那一遍；修好后的四条腿由本文件源码现读核对 = %d/4，缺一即 ABORT）：那一格的判据当时只有 '
    'rd() 一条腿 —— rd() 走通用换行，把 CRLF 盘件读成 LF 归一串，而即将写出的最终串带 CRLF ⇒ 两条腿不同尺、'
    '在写侧支里永不相等（§38.21 ① 那一族**第 7 次命中**：第 6 次 = 上一行那条"等式排在写盘之前"（paperwork4 源码在册），'
    '第 7 次 = 本遍为补那一格而新加的反查自己用了归一串 ⇒ 同一格里修好的与坏掉的都属于本遍亲手）。'
    '后果点名：assert 在两只目标**已落盘之后**才红 ⇒ 崩溃那遍没跑到落载体，本批写侧支无载体照片；'
    '处置 = 正文不回滚（回滚要覆写用户正文，比重跑更伤），改由第二遍走 REWROTE_CARRIER_ONLY 补载体 + '
    '反查换成字节比字节（见上一格）+ 另立 SNAPPREFIX 一格做独立于当前盘的前缀证据。连锁一条：那一遍死在 `_lines` 之前 ⇒ '
    '载体行拼装从未被执行过，`%%d` 位上喂了 money() 返回值这类格式错要等到 `_lines` 真被拼起来的那一遍才暴露'
    '（本遍是这只工具落纸的第 %d 张、进入时在册 %d 张 ⇒ 更早哪一遍撞的是什么，记在它自己那张照片里，本遍不代答，也不写死遍数）。'
    '本条**没进本批正文**（本批 %d 条已落纸、台账行已钉死，不该就地改数），登记为第六批义务（FreqErr 新条 + 排查记录新节）' % (
        POST_LEGS, len(_PHOTOS) + 1, len(_PHOTOS), N_ENTRY),
    'SNAPPREFIX 独立反查（不许拿当前盘推当前盘：复跑支的改前串是从**当前盘**切出来的，那一条前缀等式自我成立、量不到上一遍）'
    '：改前快照 = 崩的那一遍**运行前**由我手工 cp 的两只完整字节（工具没自己做过这件事，措辞按事实写），'
    '落在仓库之外 = %s；DOC 快照 %s B / md5 %s / mtime %s，FreqErr 快照 %s B / md5 %s / mtime %s，'
    '两目标的 mtime %s / %s 都晚于快照 = %s（谁最后写谁给 mtime：DOC 那一只现在挂着的是订正遍那次写盘、FreqErr 那一只仍是崩的那遍 —— '
    'DOC 的 mtime 与在册订正句的时刻对表 = %s。上一张照片把这两个值一并标成"崩的那遍写盘时刻"，按规矩不回写、在 PHOTO 行点名）；'
    '快照是盘上现读的逐字前缀 = %s / 追加段 DOC %d 行、FreqErr %d 行，与预期（§38.26 全部在册 %d 行（含订正遍 %d 行）+ glue %d / '
    'FreqErr 本批节含台账行 %d 行 + glue %d）相等 = %s / 追加段裸 LF = %s（0 才说明快照之后落下的两段都纯 CRLF）。'
    '差集覆盖两次写盘（崩的那遍 + 订正遍）⇒ 这条量的是"两段合起来只做了追加"，单遍归属靠位置拆：DOC 末 %d 行逐行按订正标记现核 = %s '
    '⇒ 归本遍之前那一遍的 = %d − %d = %d 行；跨遍对照 = 最早那张在册的 %s 行 + 订正遍 %d 行 ⇒ 相等 = %s（那句从 %s 现读，不抄记忆）' % (
        SNAP_OUT, money(SNAP_DB), md5_(_SNAPD)[:8], SNAP_T[0], money(SNAP_FB), md5_(_SNAPF)[:8], SNAP_T[1],
        DOC_T, FREQ_T, SNAP_BEFORE, DOC_T_FIX, SNAP_PRE,
        SNAP_ROWS[0], SNAP_ROWS[1], len(WIN_D), N_CORR, GLUE_D, len(WIN_F), GLUE_D,
        SNAP_ROWS == (len(WIN_D) + GLUE_D, len(WIN_F) + GLUE_D), SNAP_BARE,
        N_CORR, CORR_AT_END, SNAP_ROWS[0], N_CORR, SNAP_ROWS[0] - N_CORR,
        PREV_SNAP_ROWS, N_CORR, PREV_TIE,
        ' + '.join(_PHOTOS) if _PHOTOS else 'NA'),
    'WINDOW 前缀等式（"只追加、正文一字未改"）：FreqErr 改前 %d 行是盘上 %d 行的逐字前缀 = %s / 排查记录 %d -> %d 行 = %s；'
    '本批窗口 = FreqErr %d 行 + §38.26 %d 行。注意口径：复跑支的改前串是从当前盘切的 ⇒ 这两条自我成立、只证本遍没写，'
    '跨遍（崩的那一遍有没有只追加）由 SNAPPREFIX 行的独立快照负责' % (
        nl(freq_pre), nl(freq_disk), PRE_EQ_F, DOC_ROWS0, nl(doc_disk), PRE_EQ_D, len(WIN_F), len(WIN_D)),
    'POSCTL 复跑第四批落地器 paperwork4 rc=%d / %s；同趟复跑第三批 paperwork3 rc=%d（两只都绿才落本批载体）。'
    '副作用点名 = 每复跑一只，它就往 hardware/ 多落一只它自己的载体（载体槽池不许覆写）⇒ 见 POSCTL-POLL 行' % (
        _r.returncode, _pos, _r2.returncode),
    'POSCTL-POLL 检查动作污染被检查物（本遍现算，时间界 = 台账行标题时刻 %s 之前）：界之后在册的 `r56_paperwork*.txt` 进入时 %d 只 '
    '（%s）、落载体前 %d 只（差额 = 本遍这一趟 POSCTL 刚造出来的）；两份名单合起来全是**本批之内**的复跑产物 —— 进入时那批来自本批更早几遍，'
    '差额那批来自本遍自己（复跑一只落地器 = 它自己多落一只载体；本工具更早那遍的载体若已落盘也在其中）⇒ 三处目录扫描（三代口径 %d 只 / 上一批在册唯一一只 = %s / LEDGER 代次 %s）'
    '一律按这条界截断，否则"上一批在册只有 1 只"会在本遍自己的第二次调用里红（R46 (60) 那一族：py_compile 往归档里落 .pyc）。'
    '这些新载体的内容本遍不复算、不引用为新证据，只点名它们存在' % (
        LED_TS, len(_POLL), ' + '.join(_POLL) or '无', len(_POLL2), len(_C3), CARPREV, ' + '.join(_LED_G)),
    'WITNESS FREQ md5=%s / DOC md5=%s（本遍结束时现算）' % (md5_(FREQ)[:8], md5_(DOC)[:8]),
    'NOTDONE 本遍（%s）没做：串口 / 烧录 / 换电池 / 万用表 / 第二块板 / 改 main 源码 / 重建固件 / 勾或改那 %d 只未选项 / '
    '新建备份根 / 新建清单代次 / push / amend / 删除 —— 屏亮 0 次肉眼确认 ⇒ 未播提示音；'
    'todo 第十七遍、docs 第十遍、backups README 第十次读数、提交轮#9、第 14 代同步在本节之后 ⇒ 本遍不预写它们的数。'
    '第六批欠账（点名，不是本遍范围）：①把 POSTWRITE-CRASH 那条（§38.21 ① 第 7 次命中）落成 FreqErr 新条 + 排查记录新节；'
    '②paperwork4 那只在册载体记的是复跑支，写侧支仍无自己的载体' % (_now2, CNT_TODO),
    'VERDICT=%s（两只 CRLF 目标里本遍写盘 %d 只 + 载体 1 只；崩的那一遍写盘 2 只、正文留盘未回滚，见 POSTWRITE-CRASH / SNAPPREFIX）' % (
        'OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY', 2 if MODE == 'LANDED_NOW' else 0),
]
_txt = '\n'.join(_lines) + '\n'
assert BS not in _txt, 'ABORT: 载体行里有反斜杠（§38.18 那一族）：%r' % [l for l in _lines if BS in l][:2]
assert 'zizhao1' not in _txt, 'ABORT: 载体含口令明文'
assert not re.search(r'@[A-Za-z0-9_]+@', _txt), 'ABORT: 载体行还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', _txt)[:3]
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write(_txt)
print('MODE=%s 分组=①%d / ②%d（早 %d 晚 %d）/ ③%d 只 同族工具=%d 仍混尺=%s' % (
    MODE, len(MIX_F), len(LIVE_F), len(B_EARLY), len(B_LATE), len(SAME_F), len(_mix_how), STILL_MIX or '无'))
print('RULER 混尺箭头=%d 同尺真追加=%d CR差额=%d == 改前行数 %d / ②代同口径漂移=%d B %d 行' % (
    M_B1 - M_B0, S_B1 - S_B0, CR_GAP, M_ROWS0, DRIFT_BYTES, DRIFT_ROWS))
print('FREQ 改前 %d 条 / %d 行 -> 终态 %d 条 / %d 行（尺子 = %s）' % (K0, L0, SELF_K1, SELF_L1, SRC_TAG))
print('DOC 改前 %d 行 -> 终态 %d 行 / %s B（尺子 = %s）/ POSTWRITE=%s' % (
    DOC_ROWS0, SELF_ROWS1, money(SELF_B1), SRC_TAG, POSTWRITE))
print('VERDICT=%s CARRIER=%s' % ('OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY',
                                 os.path.basename(CARRIER)))
print('POSCTL paperwork4 rc=%d / paperwork3 rc=%d / %s' % (_r.returncode, _r2.returncode, _pos[:200]))
