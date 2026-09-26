# R57 收口批 part A 补落遍 = 把崩溃遍（tail_a 第一遍）落了一半的账收完。
# 崩溃遍的形状：正文（排查记录 §38.28 + FreqErr 第四批 2 条）**已落盘**，载体**未落** —— 因为它把 SEAL 写盘前后互核那句 assert 本身写错了，
#   红在写盘之后（三元组左右不同代：左边是 fold_a 的(只数,字节,摘要)，右边混进 fold_b 的摘要与"写盘前"的 fold_b 三元组）。
# 本遍三件事：①**复算"纯追加"**（拿上一遍载体 LAND 行在册的 md5 比盘上前 N 行，不假设）；②落本遍载体（含崩溃遍证据行 + 双侧窗口认它那只代落件）；
#   ③FreqErr 第五批 1 条 + 排查记录 1 行登记（补齐崩溃遍那句指向空文件的"由载体 LAND 行现数"）。
# 门继承 tail_a 第一遍全套（空槽 / 前缀等式 / 纯 CRLF / 反斜杠 / 明文 / 哨兵 / 回读等值 / SEAL 两把尺 + 内存假名 / GATE-COUNT 后置 / 完成态数字在 LAND 行现数）。
import ast
import hashlib
import os
import re
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

_T0 = time.time()

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
FIXCAR = os.path.join(HDIR, 'r57_paperwork1_fix2.txt')
CAR0 = os.path.join(HDIR, 'r57_paperwork1.txt')
TOOL_A = os.path.join(HDIR, 'r57_paperwork_tail_a.py')
TOOL = os.path.join(HDIR, 'r57_paperwork_tail_a_fix.py')
CARRIER = os.path.join(HDIR, 'r57_paperwork_tail_a_fix.txt')
SRC_MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
VMRUN = os.path.join(HDIR, 'vm_run.py')
SEAL_REF = 'efda29538483bbc73e91941936512a2f'
PROBE = 'evidence/SEAL_VIOLATION_PROBE10.txt'

RUN_AT = datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S')
TOOL_M = datetime.fromtimestamp(os.path.getmtime(TOOL_A))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def md5b(b):
    return hashlib.md5(b).hexdigest()


def run(args):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


ast.parse(rd(TOOL))
assert not os.path.exists(CARRIER), 'ABORT: 本遍载体槽位非空，不覆写'
for _p in (DOC, FREQ, CAR_E2, FIXCAR, CAR0, TOOL_A, SRC_MACRO, VMRUN):
    assert os.path.isfile(_p), 'ABORT: 缺件 ' + _p
assert os.path.getmtime(FIXCAR) < _T0 and os.path.getmtime(CAR_E2) < _T0 and os.path.getmtime(CAR0) < _T0, 'ABORT: 被引用的上一遍件 mtime 不早于本遍进入时刻'

DOC_T = rd(DOC)
FREQ_T = rd(FREQ)
DOC_L = DOC_T.split('\r\n')
FREQ_L = FREQ_T.split('\r\n')
assert DOC_T.endswith('\r\n') and FREQ_T.endswith('\r\n'), 'ABORT: 两文件不以外层行尾收尾，追加会劈行'
assert DOC_T.count('\n') == DOC_T.count('\r\n') and FREQ_T.count('\n') == FREQ_T.count('\r\n'), 'ABORT: 行尾不再纯 CRLF'
assert DOC_L.count('### 38.28 R57 收口批 = 三遍的账（崩溃') + len([l for l in DOC_L if l.startswith('### 38.28')]) == 1, 'ABORT: §38.28 不唯一'
N3828 = len([l for l in DOC_L if l.startswith('### 38.28')])
assert N3828 == 1, 'ABORT: §38.28 标题现读 ' + str(N3828) + ' 只'
I3828 = [i for i, l in enumerate(DOC_L) if l.startswith('### 38.28')][0]
NSEC = len([l for l in DOC_L if l.startswith('### 38.')])
assert 'R57 第五批' not in FREQ_T, 'ABORT: FreqErr 的 R57 第五批标题已在册'
assert 'R57 第四批' in FREQ_T, 'ABORT: 崩溃遍的第四批正文竟然不在盘上，本遍无账可补'

# ---- ①纯追加复算：拿上一遍（订正遍）载体 LAND 行在册的两只 md5 与盘上"前 N 行"比
_m = re.search(r'排查记录 = ([0-9,]+) 行 / ([0-9,]+) B / md5 ([0-9a-f]{32})；FreqErr = ([0-9,]+) 行 / ([0-9,]+) B / md5 ([0-9a-f]{32})',
               rd(FIXCAR))
assert _m, 'ABORT: 上一遍载体 LAND 行读不出两只在册 md5，纯追加就没法复算'
PRE_DOC_ROWS = int(_m.group(1).replace(',', ''))
PRE_DOC_MD5 = _m.group(3)
PRE_FREQ_ROWS = int(_m.group(4).replace(',', ''))
PRE_FREQ_MD5 = _m.group(6)
AP_DOC = md5b(('\r\n'.join(DOC_L[:PRE_DOC_ROWS]) + '\r\n').encode('utf-8'))
AP_FREQ = md5b(('\r\n'.join(FREQ_L[:PRE_FREQ_ROWS]) + '\r\n').encode('utf-8'))
assert AP_DOC == PRE_DOC_MD5, 'ABORT: 盘上前 ' + str(PRE_DOC_ROWS) + ' 行与上一遍在册 md5 不等 ⇒ 崩溃遍改过旧行，本遍不许继续'
assert AP_FREQ == PRE_FREQ_MD5, 'ABORT: 盘上前 ' + str(PRE_FREQ_ROWS) + ' 行与上一遍在册 md5 不等 ⇒ 崩溃遍改过旧行，本遍不许继续'
ADDED_DOC = len(DOC_L) - 1 - PRE_DOC_ROWS
ADDED_FREQ = len(FREQ_L) - 1 - PRE_FREQ_ROWS
N_TYPE_PRE = len([l for l in FREQ_L if l.startswith('[错误类型]')])
assert N_TYPE_PRE == 216, 'ABORT: 第四批落盘后条数现读 = ' + str(N_TYPE_PRE) + '，不是 216'

# ---- ②崩溃遍时刻互核：两只正文同一秒（同一遍写的），且严格晚于那只工具的落盘时刻
#      互核一律按秒对齐：那只遍是"先写排查记录、紧接着写 FreqErr"，两次 write 天然差几毫秒，
#      拿微秒级 datetime 判相等是一道**永不成立**的门（本遍第一次跑就红在这里，见载体 CRASH 行）
DOC_W = datetime.fromtimestamp(os.path.getmtime(DOC)).replace(microsecond=0)
FREQ_W = datetime.fromtimestamp(os.path.getmtime(FREQ)).replace(microsecond=0)
DOC_US = os.path.getmtime(DOC) - DOC_W.timestamp()
FREQ_US = os.path.getmtime(FREQ) - FREQ_W.timestamp()
assert DOC_W == FREQ_W, 'ABORT: 两只正文 mtime 不同秒 ⇒ 不是同一遍写的，本遍无账可补'
assert TOOL_M < DOC_W, 'ABORT: 崩溃遍正文 mtime 不晚于工具 mtime ⇒ 那两处正文不是 tail_a 这只工具写的'
CRASH_AT = DOC_W.strftime('%Y-%m-%d %H:%M:%S')
TOOL_W = TOOL_M.strftime('%Y-%m-%d %H:%M:%S')
CRASH_DT = DOC_W

NM = re.compile(r'^vm_run_([0-9]{8}_[0-9]{6})\.txt$')


def nm_time(f):
    m = NM.match(f)
    assert m, 'ABORT: 候选名 ' + repr(f) + ' 不匹配整名模式（vm_run_ + 8 位日期 + 下划线 + 恰好 6 位时刻 + .txt）'
    return datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')


POOL = sorted([f for f in os.listdir(HDIR) if f.startswith('vm_run_') and '20260925' in f], key=nm_time)
for f in POOL:
    nm_time(f)
_m = re.search(r'崩溃遍三格互核：正文 ([0-9\- :]+) /', rd(FIXCAR))
assert _m, 'ABORT: 读不到 §38.27 那一遍的落纸时刻，第一格窗口没有下界'
W0 = datetime.strptime(_m.group(1), '%Y-%m-%d %H:%M:%S')
W1 = datetime.strptime(re.search(r'补落遍时刻 = ([0-9\- :]+)', rd(FIXCAR)).group(1), '%Y-%m-%d %H:%M:%S')
W2 = datetime.strptime(re.search(r'本遍现跑于 ([0-9\- :]+)', rd(FIXCAR)).group(1), '%Y-%m-%d %H:%M:%S')
TOP = datetime.fromtimestamp(os.path.getmtime(os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt'))).replace(microsecond=0)
CELLS = {
    'paperwork 遍（§38.27）': lambda t: W0 <= t <= TOP,
    '补落遍中止那一次': lambda t: TOP < t < W1,
    '补落遍成功那一次': lambda t: t == W1,
    '订正遍中止的尝试': lambda t: W1 < t < W2,
    '订正遍成功那一次': lambda t: t == W2,
    'tail_a 第一遍（崩溃遍）': lambda t: W2 < t < CRASH_DT,
}
ASSIGN = {}
for f in POOL:
    t = nm_time(f)
    hit = [k for k, fn in CELLS.items() if fn(t)]
    assert len(hit) == 1, 'ABORT: 候选 ' + f + ' 落进 ' + str(hit) + ' 格，窗口不唯一或不成立'
    ASSIGN.setdefault(hit[0], []).append(f)
assert len(ASSIGN['tail_a 第一遍（崩溃遍）']) == 1, 'ABORT: 崩溃遍那只代落件不唯一'
CRASH_VM = ASSIGN['tail_a 第一遍（崩溃遍）'][0]
assert nm_time(CRASH_VM) < CRASH_DT, 'ABORT: 崩溃遍代落件的名字时刻不早于它的正文写入时刻 ⇒ 双侧窗口的上界（正文 mtime）没有执行者'
assert TOOL_M < nm_time(CRASH_VM), 'ABORT: 崩溃遍代落件早于本遍所认那只工具的落盘时刻 ⇒ 归属不成立（它是这只工具产的）'
assert len([f for f in POOL if nm_time(f) > CRASH_DT
            and not f.startswith(CRASH_VM)]) == 0, 'ABORT: 崩溃遍之后、本遍之前还有没归格的代落件'

# ---- 现场态
COMS = run((sys.executable, '-c',
            'import serial.tools.list_ports as p;'
            'print(", ".join(sorted([x.device for x in p.comports() if x.device.startswith("COM")])))')).stdout.decode('utf-8', 'replace').strip()
HAS14 = 'COM14' in [x.strip() for x in COMS.split(',')]
REV = run(('git', 'rev-list', '--count', 'origin/main..HEAD')).stdout.decode('utf-8', 'replace').strip()
ST = [l for l in run(('git', '-c', 'core.quotePath=false', 'status', '--porcelain')).stdout.decode('utf-8', 'replace').splitlines() if l.strip()]
ST_M = len([l for l in ST if l.startswith(' M')])
ST_Q = len([l for l in ST if l.startswith('??')])


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
        h.update(md5b(b).encode('ascii'))
    for e in extra:
        h.update(md5b(e.encode('utf-8')).encode('ascii'))
    return len(files) + len(extra), tot, h.hexdigest()


def fold_b(d, extra=()):
    parts = []
    tot = 0
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            p = os.path.join(root, n)
            b = rb(p)
            tot += len(b)
            parts.append(os.path.relpath(p, d).replace(os.sep, '/') + ':' + md5b(b))
    for e in extra:
        parts.append(e + ':' + md5b(e.encode('utf-8')))
    return len(parts), tot, md5b('\n'.join(sorted(parts)).encode('utf-8'))


S0A, S0B = fold_a(SYNC), fold_b(SYNC)
assert S0A[2] == SEAL_REF and S0A[:2] == S0B[:2], 'ABORT: 写盘前 FOLD-A 与在册聚合不等 / 两把尺互核失败'
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
_probe_red = PA[2] != S0A[2] and PB[2] != S0B[2]
assert _probe_red and not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: SEAL 门没有执行者（假名未使两把尺变红，或假名已落盘）'
_FIRED = (1 if PA[2] != S0A[2] else 0) + (1 if PB[2] != S0B[2] else 0)

# ---- ②b 更早两遍那把同名 FOLD-B 的**定义**与**值**，从补落遍载体现读（不转抄、不硬编码）
_mfb = re.search(r'FOLD-B（([^）]*)）= ([0-9,]+) 只 / ([0-9,]+) B / ([0-9a-f]{32})', rd(CAR0))
assert _mfb, 'ABORT: 补落遍载体里读不出带定义的 FOLD-B 三格，命名碰撞这一句就没有出处'
FB_DEF, FB_ROWS, FB_BYTES, FB_OLD = _mfb.group(1), _mfb.group(2), _mfb.group(3), _mfb.group(4)
assert '竖线' in FB_DEF, 'ABORT: 在册 FOLD-B 的定义里读不到分隔符那两个字 ⇒ "两种折法同名"不成立'
assert FB_OLD != S0B[2], 'ABORT: 旧 FOLD-B 与本遍换行折法同值 ⇒ 本遍点名的"命名碰撞"没有证据'
assert (FB_ROWS, FB_BYTES) == (str(S0B[0]), format(S0B[1], ',')), 'ABORT: 两把同名尺的公共量（只数/字节）不等 ⇒ 归档目录真动过'
_mfb2 = re.search(r'FOLD-B = ([0-9,]+) 只 / ([0-9,]+) B / ([0-9a-f]{32})', rd(FIXCAR))
assert _mfb2 and _mfb2.group(3) == FB_OLD, 'ABORT: 订正遍在册的 FOLD-B 与补落遍不同值 ⇒ "更早两遍同值"这一句不成立'

# ---- ③正文自核：§38.28 里那些插值数，逐格回到源件现读，再作为**短语**（不是裸数）grep 那一节
#      裸数（'23' / '0' / '10'）在任何正文里都恒命中，不能当证据 ⇒ 每只 needle 都带上它那一格的单位词
E_TXT = rd(CAR_E2)
NEW_DOC = '\r\n'.join(DOC_L[I3828:])
NEEDLES = (
    ('probe ' + re.search(r'probe# ([0-9]+) 次', E_TXT).group(1) + ' 次', 'probe 次数'),
    ('应答 = ' + re.search(r'应答 ([0-9]+) 条', E_TXT).group(1) + ' 条', '应答条数'),
    ('窗口 ' + re.search(r'窗口 ([0-9.]+) s', E_TXT).group(1) + ' s', '窗口秒数'),
    ('非空 ' + re.search(r'非空 ([0-9]+) 行', E_TXT).group(1) + ' 行', '非空行数'),
    ('我方 ' + re.search(r'我方 = ([0-9]+) 只', E_TXT).group(1) + ' 只', '屏侧分母'),
    ('指纹 ' + re.search(r'ELF 指纹 = ([0-9a-f]{16})', E_TXT).group(1), 'boot ELF 指纹'),
    ('FOLD-A ' + str(S0A[0]) + ' 只 / ' + format(S0A[1], ',') + ' B', 'FOLD-A 只数与字节'),
    ('`' + S0A[2] + '`', 'FOLD-A 摘要'),
    ('FOLD-B ' + str(S0B[0]) + ' 只 / ' + format(S0B[1], ',') + ' B / `' + S0B[2] + '`', 'FOLD-B 三格'),
)
for _n, _src in NEEDLES:
    assert _n in NEW_DOC, 'ABORT: §38.28 里找不到由源件现读推出的那一格 ' + _src + ' = ' + _n

# ---- ④§38.28 在册那句"载体 MOJI 行"的复跑：同一份字节两种解码，md5 不变而字符数变
MOJI_B = NEW_DOC.encode('utf-8')
MOJI_MD5 = md5b(MOJI_B)
MOJI_U = len(MOJI_B.decode('utf-8'))
try:
    MOJI_B.decode('cp936')
    MOJI_ERR = '不抛错'
except UnicodeDecodeError as e:
    MOJI_ERR = '第 ' + str(e.start) + ' 字节抛 ' + e.reason
MOJI_R = MOJI_B.decode('cp936', 'replace')
assert md5b(MOJI_R.encode('utf-8', 'replace')) != MOJI_MD5
MOJI_REPL = MOJI_R.count(chr(0xfffd))
assert MOJI_U > 0 and MOJI_REPL > 0 and MOJI_ERR != '不抛错', 'ABORT: 那一遍的 mojibake 现场复跑不出红，MOJI 行只能记账'
assert chr(92) not in MOJI_ERR and 'ABORT' not in MOJI_ERR

_vm = run((sys.executable, VMRUN))
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=' + str(_vm.returncode)
VM_CARRIER = _mc.group(1).split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_CARRIER)).split('\n') if l.startswith('INNER_ROWS=')][0]
assert nm_time(VM_CARRIER) > nm_time(CRASH_VM), 'ABORT: 本遍代落件没有严格晚于崩溃遍那只（上一批刚登记的规矩，本遍自己先违反）'
ASSIGN['本遍（补落遍 part A）'] = [VM_CARRIER]

_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏，闸无法自证扫的是真口令'
secret = _secret.group(1).encode('utf-8')

# ================= 正文 =================
DOC_ROW = ('- **登记（§38.28 补落遍｜' + RUN_AT + '）**：§38.28 与 FreqErr 第四批由崩溃遍（' + CRASH_AT + '）落盘，那只遍的载体没落 —— 它把 SEAL 写盘前后互核那句 '
           'assert 自己写错了：链式三段 = 写盘前 fold_a 三元组 == (写盘后 fold_a 只数, 写盘后 fold_a 字节, **写盘后 fold_b 摘要**) == 写盘前 fold_b 三元组，'
           '首末两段一把取 A 折一把取 B 折，摘要永不相等 ⇒ 恒红，且那句排在 open() 之后，红在正文已落之后。'
           '本遍复算两件事：①**崩溃遍没改过任何旧行** = 盘上前 ' + str(PRE_DOC_ROWS) + ' 行 md5 ' + AP_DOC + ' 与上一遍载体在册 ' + PRE_DOC_MD5 +
           ' 逐字相等、FreqErr 前 ' + str(PRE_FREQ_ROWS) + ' 行 md5 ' + AP_FREQ + ' 与在册 ' + PRE_FREQ_MD5 + ' 逐字相等（两把尺都是现算，不是假设）；'
           '②崩溃遍那只代落件 = `hardware/' + CRASH_VM + '`，由**双侧窗口**现读（下界 = 订正遍 ' + W2.strftime('%H:%M:%S') + '，上界 = 崩溃遍正文 mtime ' +
           CRASH_DT.strftime('%H:%M:%S') + '，本遍进入 ' + RUN_AT[11:] + ' 更晚），今日 2026-09-25 的 ' + str(len(POOL)) + ' 只候选**逐格分完** = ' + '; '.join(
               [k + ' ' + ','.join(x[:-4] for x in v) for k, v in sorted(ASSIGN.items())]) +
           ' ⇒ 上一批刚登记的"双侧窗口 + 池子分完"本遍就是第一个执行者。本遍补落载体 = `hardware/r57_paperwork_tail_a_fix.txt`；'
           'FreqErr 第五批两条（根族一：**两把尺的读数混装进同一只元组**；根族二：**一道永不成立的门** —— 本遍自己第一次跑就把"同一遍写的"判成两次 write 的 mtime 微秒相等，'
           '实测两者差 1 毫秒 ⇒ 恒红，已就地改按秒对齐并把亚秒差随读数一起登在载体 CRASH 行）。')
FREQ_TITLE_FMT = '## 2026-09-25（R57 第五批：互核两边不是用同一把尺做的 + 一道永不成立的门）新增 {N} 条（根族：**两把尺的读数混装进同一只元组** / **判据不可达**）'
FREQ_BODY = [
    '',
    '',
    '[错误类型] **把"同一目录同一刻各跑一遍的两把尺"写进一只元组比较，左元素来自 A 折法、右元素来自 B 折法 ⇒ 这道互核门恒红；'
    '更糟的是它排在写盘之后，于是正文已落、载体未落，本遍的完成态指针全部指向空文件**'
    '（本批实测：崩溃遍那句是**链式三段** —— 写盘前 fold_a 三元组 ==（写盘后 fold_a 只数, 写盘后 fold_a 字节, **写盘后 fold_b 摘要**）== 写盘前 fold_b 三元组，'
    '首段与末段一把 A 折一把 B 折，摘要永不相等 ⇒ 恒红；它红在第 345 行、两条正文已写完之后）',
    '→ 症状：所有"看起来在互核"的门全绿时才可信，而这条门是**红着**暴露的 —— 它红得很有说服力，读起来像"归档目录被动了"（本批盘上并未动：'
    '两把尺写盘前后各自的值全等，本遍载体 SEAL 行现证），于是要查的假象是"我污染了封存目录"，真要查的只是比较式本身。',
    '→ 为什么它危险：①**假阳性会引向破坏性动作** —— 若我据此去"清理归档目录"，就真的动了 gen 24 封界；②它把这一遍切成"正文已落 / 凭证未落"的半状态，'
    '而半状态里正文已经引用了不存在的载体（那句"终态三格由载体 `LAND` 行现数"），这正是上一批刚登记的"完成态指针指向空文件"的复现；'
    '③同族更早的形态是"汇总行只数对而名单被截断"（项目记忆 (82)）与"打印 ≠ 裁决"（记忆"裁决必须同时落 stdout 与 rc"），本条的新形态是：**互核的两侧必须先同尺，再同代**。',
    '→ 正确做法：①凡"A 尺 vs B 尺"的互核，写成**两条独立的同尺比较**（本遍：fold_a 写前 == fold_a 写后，且 fold_b 写前 == fold_b 写后），'
    '不许在一只元组里混装两把尺的分量；②跨尺只许比**两把尺都定义得到的公共量**（本批 = 只数与字节数，摘要各自只与自己比）；'
    '③**裁决类门一律排在写盘之前**（写盘之后的门只能记账，不能防账）：本遍把这条做成顺序断言 —— SEAL 双尺互核 + 阳性对照都在 open() 之前；'
    '④崩溃遍的正文不回写，只由补落遍追加一行登记并新落载体（本遍就是这么处理的）；'
    '⑤**同名的一把尺换了折法就必须换名字**（本遍现读的第二处同族：更早两遍把 FOLD-B 折成"以竖线连接" = ' + FB_OLD + '，崩溃遍与本遍把同名那把尺折成"以换行连接" = ' + S0B[2] +
    '，两值都对、都只与自己可比，可比的只有只数与字节）：聚合摘要不带分隔符/序定义，读它的人就复算不出来 ⇒ 从本遍起摘要必须与折法同格落盘。',
    '→ **同族**：项目记忆 (82)"汇总行只数对而名单被截断"、(69)"登记已跑完前先跑一次并抄 rc"、(48) 与上一批第一条（归属要双侧窗口）、本批第四批第一条（同一遍内两处顺序缺陷：先写盘后裁决 / 两把尺混装）。',
    '',
    '[错误类型] **拿"两次顺序 write 的 mtime 微秒相等"当"同一遍写的"的判据 ⇒ 这是一道永不成立的门，它红的时候被怀疑的是证据，不是判据本身**'
    '（本遍实测第一次跑就红在这里：那只崩溃遍先写排查记录、紧接着写 FreqErr，两次 write 差 ' + format((FREQ_US - DOC_US) * 1000, '.1f') +
    ' ms，微秒级 datetime 永不相等；同一秒才是"同一遍"的可判口径）',
    '→ 为什么它危险：恒**假**的门比恒真的门更难发现 —— 恒假会红，红会让人以为"证据对不上、这遍不能补"，于是往"正文被改过"的方向查，'
    '而真正错的是我选的量具分辨率。同族反向的那一条是"命中 0 ≠ 干净"（记忆 (69)/(76)），本条是它的镜像：**判据不可达 ⇒ 它的红不携带任何信息**。',
    '→ 正确做法：①凡"同一遍/同一刻"类判据，先问**这个量在物理上可能的最小间隔是多少**（两次 write = 毫秒级；同名文件与它自己的 mtime = 同一次 setattr），'
    '再把比较对齐到那个分辨率（本遍：两侧都 `replace(microsecond=0)` 后判等）；②把被丢掉的亚秒差**随读数一起登进载体**（本遍 CRASH 行现登 ' +
    format((FREQ_US - DOC_US) * 1000, '.1f') + ' ms），这样"按秒对齐"不是放宽判据，而是一个有数据的取舍；'
    '③新写的门第一次跑就红，先怀疑门，再怀疑证据。',
    '→ **同族**：本批上一条（互核两侧先同尺再同代）、项目记忆 (69)"命中 0 不等于干净"、上一批"恒真式判据"（本遍顺手删掉两处 `or True` 与 `X and re.search(...)`）。',
]
N_NEW = len([l for l in FREQ_BODY if l.startswith('[错误类型]')])
assert N_NEW == 2, 'ABORT: 本批正文条数现算 ' + str(N_NEW) + ' 只，不是 2 ⇒ 标题与台账里的"1 条"全要跟着改'
assert len([l for l in FREQ_BODY if l.startswith('→ 正确做法') or l.startswith('→ **同族')]) == 4
FREQ_BODY[0] = FREQ_TITLE_FMT.format(N=N_NEW)
LEDGER = ('>'
          ' **【' + RUN_AT + ' 落地｜R57 第五批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（本脚本进入时刻 ' + RUN_AT + '，_T0 取在任何产证动作之前）：'
          '全文 `^[错误类型]` 条数 = **' + str(N_TYPE_PRE) + '**、行数 = **' + str(len(FREQ_L)) + '**、字节 = **' +
          format(len(FREQ_T.encode('utf-8')), ',') + '**；本批正文（不含本台账行自己，含上方那只 glue 空行与两条之间的空行）= **' + str(N_NEW) + '** 条 / **' +
          str(len(FREQ_BODY)) + '** 行 / **' + format(len(('\r\n'.join([''] + FREQ_BODY)).encode('utf-8')), ',') + '** B；'
          '**落盘后的终态三格由本遍载体 `LAND` 行现数**（完成态数字不许在本行里预写）。'
          '同遍排查记录 改前 **' + str(len(DOC_L)) + '** 行 / **' + format(len(DOC_T.encode('utf-8')), ',') + '** B -> 本批真追加 2 行'
          '（1 只 glue 空行 + 1 行补落遍登记），前缀等式成立、纯 CRLF；崩溃遍那两处正文一字节未回写。')

payload = '\r\n'.join([DOC_ROW] + FREQ_BODY)
assert secret not in payload.encode('utf-8'), 'ABORT: 明文口令在本批正文里'
assert chr(92) not in payload, 'ABORT: 本批正文含 ASCII 反斜杠'
for _s in ('%s', '%d', '@@', 'None', 'BUIL'):
    assert _s not in payload, 'ABORT: 本批正文含未替换哨兵 ' + _s

DOC_NEW = DOC_T + '\r\n' + DOC_ROW + '\r\n'
FREQ_NEW = FREQ_T + '\r\n' + '\r\n'.join(FREQ_BODY) + '\r\n' + LEDGER + '\r\n'
assert DOC_NEW.startswith(DOC_T) and FREQ_NEW.startswith(FREQ_T), 'ABORT: 前缀等式不成立，本批不是纯追加'
_d0, _b0, _fa0 = fold_a(SYNC)
_db0, _bb0, _fb0 = fold_b(SYNC)

open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)

d_after = rd(DOC)
f_after = rd(FREQ)
assert d_after == DOC_NEW and f_after == FREQ_NEW, 'ABORT: 回读与内存串不等'
assert '\r' not in d_after.replace('\r\n', '') and '\r' not in f_after.replace('\r\n', ''), 'ABORT: 写后不再是纯 CRLF'
assert secret not in d_after.encode('utf-8') and secret not in f_after.encode('utf-8'), 'ABORT: 明文写进了盘'
DL = d_after.split('\r\n')
FL = f_after.split('\r\n')
DOC_LINES = len(DL) - 1
FREQ_LINES = len(FL) - 1
DOC_BYTES = os.path.getsize(DOC)
FREQ_BYTES = os.path.getsize(FREQ)
N_TOTAL = len([l for l in FL if l.startswith('[错误类型]')])
assert N_TOTAL == N_TYPE_PRE + N_NEW, 'ABORT: 条数现算 ' + str(N_TOTAL) + ' != 追加前 ' + str(N_TYPE_PRE) + ' + 本批 ' + str(N_NEW)
_d1, _b1, _fa1 = fold_a(SYNC)
_db1, _bb1, _fb1 = fold_b(SYNC)
assert (_d0, _b0, _fa0) == (_d1, _b1, _fa1), 'ABORT: FOLD-A 写盘前后不等（同尺比：只数/字节/摘要 三格各对自己）'
assert (_db0, _bb0, _fb0) == (_db1, _bb1, _fb1), 'ABORT: FOLD-B 写盘前后不等'
assert (_d0, _b0) == (_db0, _bb0), 'ABORT: 两把尺的公共量（只数、字节）互核失败'

ROWS = []
ROWS.append('R57 收口批 part A 补落遍  MODE=TAIL-PAPERWORK-A-FIX')
ROWS.append('本遍现跑于 ' + RUN_AT + '（进入时刻 _T0 = ' + RUN_AT + '，取在任何产证动作之前）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('CRASH 崩溃遍（tail_a 第一遍）证据本遍现读：两只正文同一秒落盘 = ' + CRASH_AT + '（排查记录 mtime 与 FreqErr mtime 按秒对齐后相等 = True，'
            '两者的亚秒差 = ' + format((FREQ_US - DOC_US) * 1000, '.1f') + ' ms ⇒ 互核必须按秒，本遍第一次跑就是拿微秒相等当判据，红在一道永不成立的门上，这一处已就地订正并登记）；'
            '正文那刻严格晚于那只工具的落盘时刻 ' + TOOL_W + ' = True，代落件 ' + CRASH_VM + ' 的名字时刻落在"工具落盘 → 正文落盘"这一区间内 = True ⇒ 三格互核成立；'
            '它红在 SEAL 写盘互核那句链式 assert（写盘前 fold_a 三元组 == (写盘后 fold_a 只数, 写盘后 fold_a 字节, 写盘后 fold_b 摘要) == 写盘前 fold_b 三元组 ⇒ 首末两段一把 A 折一把 B 折，摘要恒不等），'
            '而那句排在 open() 之后 ⇒ 正文 2 处已落、载体未落；本遍不回写它的正文，只追加一行登记')
ROWS.append('APPEND 崩溃遍"没改旧行"本遍复算（不是假设）：盘上前 ' + str(PRE_DOC_ROWS) + ' 行 md5 = ' + AP_DOC + ' vs 上一遍载体在册 ' +
            PRE_DOC_MD5 + ' 相等 = True；FreqErr 前 ' + str(PRE_FREQ_ROWS) + ' 行 md5 = ' + AP_FREQ + ' vs 在册 ' + PRE_FREQ_MD5 +
            ' 相等 = True ⇒ 纯追加成立；本遍之前新增 排查记录 ' + str(ADDED_DOC) + ' 行 / FreqErr ' + str(ADDED_FREQ) + ' 行')
ROWS.append('BELONG 崩溃遍代落件 = hardware/' + CRASH_VM + '（**双侧窗口**：下界 订正遍 ' + W2.strftime('%H:%M:%S') + '，上界 崩溃遍正文 mtime ' +
            CRASH_DT.strftime('%H:%M:%S') + '，本遍进入 ' + RUN_AT[11:] + ' 严格更晚；今日候选池 ' + str(len(POOL)) + ' 只逐格分完 = True：' +
            ' / '.join([k + ' ' + ','.join(x[:-4] for x in v) for k, v in sorted(ASSIGN.items())]) +
            '）；上一批刚登记的"双侧窗口 + 池子分完"，本遍是第一个执行者 = True')
ROWS.append('CONTENT §38.28 正文自核：' + str(len(NEEDLES)) + ' 格逐字回到 E 臂取证载体与归档两把尺现读，再作为带单位词的短语 grep 那一节 = True（名单：' +
            ' / '.join([b for _a, b in NEEDLES]) + '）；本遍不拿裸数当证据（"23""0""10" 在任何正文里恒命中）；'
            '§38.28 标题现读 1 只，位于第 ' + str(I3828 + 1) + ' 行，节体取到文件末尾共 ' + str(len(DOC_L) - I3828) + ' 行；全文 ### 38.x 小节现读 ' + str(NSEC) + ' 只')
ROWS.append('MOJI §38.28 在册那句"载体 MOJI 行"的本遍复跑：那一节 ' + str(len(MOJI_B)) + ' 字节、md5 ' + MOJI_MD5 + ' ；'
            '按 UTF-8 解 = ' + str(MOJI_U) + ' 字符，按 cp936 严格解 = ' + MOJI_ERR + '，按 cp936 容错解 = ' + str(MOJI_REPL) +
            ' 只替换符（再编回 UTF-8 后 md5 变了 = True）⇒ 字节没动、md5 没动，动的是解码器：严格 cp936 那一路抛错、容错那一路成串替换符，"控制台乱码"与"文件坏了"是两件事')
ROWS.append('VM 本遍现跑内层复核器代落：rc=0 / ' + INNER + ' / 代落件 = hardware/' + VM_CARRIER + '；本遍那只名字时刻严格晚于崩溃遍那只 = True')
ROWS.append('FIELD 现跑：串口枚举 = ' + COMS + ' ⇒ COM14 在位 = ' + str(HAS14) + ' / rev-list = ' + REV + '（未 push）/ status --porcelain = ' +
            str(len(ST)) + ' 行（' + str(ST_M) + ' 只 M + ' + str(ST_Q) + ' 只 ??）')
ROWS.append('SEAL 两把尺（定义随读数落盘：FOLD-A = walk 序只折各文件 content 摘要；FOLD-B = 相对路径冒号摘要、排序后以换行连接再折）。'
            '本遍**两条同尺比较 + 一条公共量互核**：FOLD-A 写前 (' + str(_d0) + ', ' + str(_b0) + ', ' + _fa0 + ') == 写后 (' + str(_d1) + ', ' +
            str(_b1) + ', ' + _fa1 + ') = True；FOLD-B 写前 ' + _fb0 + ' == 写后 ' + _fb1 + ' = True；两把尺只数字节互核 = True。'
            'FOLD-A 逐字复现在册 ' + SEAL_REF + ' = True；内存假名（' + PROBE + '，只在内存，盘上无那只 = ' +
            str(not os.path.exists(os.path.join(SYNC, PROBE))) + '）使两把尺双红 = ' + str(_probe_red) + ' ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版。'
            '**本遍现读点出一条命名碰撞**：更早两遍把同名那把尺折成"以竖线连接"（补落遍载体在册定义 = ' + FB_DEF + '，值 ' + FB_OLD +
            '；订正遍在册同值 = True，但那遍没把定义随读数一起落），'
            '而崩溃遍与本遍把同名那把尺折成"以换行连接"（本遍现读 ' + _fb0 + '）⇒ 两个值都对、各自只与自己可比，'
            '可比的是只数与字节（两遍都是 ' + FB_ROWS + ' 只 / ' + FB_BYTES + ' B）；从本遍起 FOLD-B 一律带分隔符一起登记')
ROWS.append('LAND 写盘后独立回读现数（完成态数字在这里数）：排查记录 = ' + str(DOC_LINES) + ' 行 / ' + str(DOC_BYTES) + ' B / md5 ' +
            md5b(d_after.encode('utf-8')) + '；FreqErr = ' + str(FREQ_LINES) + ' 行 / ' + str(FREQ_BYTES) + ' B / md5 ' +
            md5b(f_after.encode('utf-8')) + ' / 条数 = ' + str(N_TOTAL) + '（= 追加前 ' + str(N_TYPE_PRE) + ' + 本批 ' + str(N_NEW) + '）；两文件前缀等式 = True、纯 CRLF 写后仍成立 = True')
ROWS.append('WITNESS 本遍现读 md5（前 12 位）：本遍工具 ' + md5b(rb(TOOL))[:12] + ' / 崩溃遍工具 ' + md5b(rb(TOOL_A))[:12] + ' / 补落遍载体 ' +
            md5b(rb(CAR0))[:12] + ' / 订正遍载体 ' +
            md5b(rb(FIXCAR))[:12] + ' / E 臂取证载体 v2 ' + md5b(rb(CAR_E2))[:12] + ' / 排查记录(本遍改前) ' + md5b(DOC_T.encode('utf-8'))[:12] +
            ' / FreqErr(本遍改前) ' + md5b(FREQ_T.encode('utf-8'))[:12])
ROWS.append('GATE 本遍各道门：空槽 0 破 / 第五批未在册 0 破 / §38.28 唯一 0 破 / 缺件 0 / 上一遍件未被本遍写 0 破 / 纯追加复算 0 破 / '
            '崩溃遍时刻两只正文同秒 0 破 / 正文 ' + str(len(NEEDLES)) + ' 格回核（带单位词短语，不拿裸数当证据）0 破 / MOJI 三种解码复跑 0 破 / 同名 FOLD-B 两种折法 0 破 / 前缀等式 0 破 / 行尾 0 破 / 反斜杠 0 / 明文 0 / 哨兵 0 / 回读等值 0 破 / '
            'SEAL 两条同尺比较 + 公共量互核 0 破 / 条数现算 0 破 / 代落件双侧窗口 0 破 ⇒ ARMS_FIRED（真红计数）：内存假名 ' + str(_FIRED) +
            '（FOLD-A/FOLD-B 各 1）+ ast.parse 写盘前红 0 次 = ' + str(_FIRED) + ' 次；'
            '另点名本遍自己**写盘前的三处自纠**（都不落盘、不算真红）：①第一次跑红在一道恒假门上（拿两次 write 的微秒级 mtime 相等当"同一遍写的"），改按秒对齐；'
            '②两处恒真式删掉（一句 `... or True`、一句 `FIXCAR and re.search(...)`）；③崩溃遍代落件的归属上界原写作"本遍进入时刻"，改为那只遍自己的正文 mtime（否则上界由本遍任意放宽）；'
            '再点名一处本遍**没能自证**的：崩溃遍改前的两只 md5 没有落盘（那只遍没跑到 WITNESS 行），故本遍的"纯追加"证据只能对到**上一遍**在册值，对不到崩溃遍进入时刻')
ROWS.append('NOTDONE 本批没做（点名）：没碰串口 / 没烧录 / 没改 main/ 源码 / 没重建固件 / 没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / '
            '没 push、没 amend / 零删除（含 %TEMP% 里那只 E 臂原件与崩溃遍留下的两只件）/ 没回写崩溃遍正文 / 屏亮仍 0 次肉眼确认 ⇒ 不播提示音 / '
            'docs 快照第十遍、backups README 第十次读数、todo 第十七遍、done 新节、dev_log 20260925、updates 新文件、烧录须知换代行、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数')
ROWS.append('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(ROWS)) + ' 行（含本行）')

body = '\n'.join(ROWS) + '\n'
assert secret not in body.encode('utf-8') and chr(92) not in body, 'ABORT: 载体正文含明文/反斜杠'
open(CARRIER, 'w', encoding='utf-8', newline='').write(body)
_c = rd(CARRIER)
assert _c == body and '\r' not in _c, 'ABORT: 载体回读不等或非纯 LF'
print('CARRIER hardware/' + os.path.basename(CARRIER), len(_c.rstrip('\n').split('\n')), 'rows', os.path.getsize(CARRIER), 'B')
print('DOC', DOC_LINES, 'FREQ', FREQ_LINES, 'N_TOTAL', N_TOTAL)
print('SEAL A', _d1, _b1, _fa1, 'B', _db1, _bb1, _fb1)
print('VM', VM_CARRIER, 'CRASH_VM', CRASH_VM, 'COM14', HAS14, 'REV', REV)
print('RUN_AT', RUN_AT)
