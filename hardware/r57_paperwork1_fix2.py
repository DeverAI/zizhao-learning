# R57 第三批（订正遍）：补落遍 13:30:12 那一只载体与它落的登记句里，"崩溃遍代落件"取的是
#   `sorted(候选)[-1]`，而候选池在挑选之前已被本遍自己刚跑的 vm_run 污染 ⇒ 把本遍的产物指给了上一遍。
# 规矩：已落地的正文与已落的载体都不回写，本遍只做三件事 ——
#   ①用带"时刻上界"的定义现读真正的崩溃遍代落件；②追加一条订正句 + FreqErr 1 条；③本遍自己现跑并落新载体。
import hashlib
import os
import re
import subprocess
import sys
import time
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

_T0 = time.time()                                    # 本遍进入时刻：所有"上一遍产物"的 mtime 上界
REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
CAR_E = os.path.join(HDIR, '20260925_R57_E臂判据摘录.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
PWCAR = os.path.join(HDIR, 'r57_paperwork1.txt')
CARRIER = os.path.join(HDIR, 'r57_paperwork1_fix2.txt')
FIXER = os.path.join(HDIR, 'r57_paperwork1_fix.py')
VMRUN = os.path.join(HDIR, 'vm_run.py')
MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
STALE = '板上仍是 `4842a3a0…`'


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def mtime(p):
    return datetime.fromtimestamp(os.stat(p).st_mtime)


NM = re.compile(r'^vm_run_(\d{8}_\d{6})\.txt$')


def nm_time(f):
    m = NM.match(f)
    assert m, 'ABORT: 候选名 %r 不匹配 vm_run_YYYYMMDD_HHMMSS.txt ⇒ 按位切片认时刻会把秒数截半，本遍不猜' % f
    return datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')


def fold_a(d, extra=None):
    n, tot, agg = 0, 0, hashlib.md5()
    for root, _ds, fs in os.walk(d):
        for f in sorted(fs):
            b = open(os.path.join(root, f), 'rb').read()
            n += 1
            tot += len(b)
            agg.update(hashlib.md5(b).hexdigest().encode('ascii'))
    if extra:
        agg.update(hashlib.md5(b'x').hexdigest().encode('ascii'))
        n += 1
    return (n, tot, agg.hexdigest())


def fold_b(d, extra=None):
    n, tot, hs = 0, 0, []
    for root, _dirs, fs in os.walk(d):
        for f in fs:
            bb = open(os.path.join(root, f), 'rb').read()
            n += 1
            tot += len(bb)
            hs.append(f + ':' + hashlib.md5(bb).hexdigest())
    if extra:
        hs.append(extra + ':deadbeef')
        n += 1
    return (n, tot, hashlib.md5('|'.join(sorted(hs)).encode('utf-8')).hexdigest())


def stale_bad(lines):
    return [i + 1 for i, l in enumerate(lines) if STALE in l and not l.startswith('- **订正（')]


def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, env=dict(os.environ, PYTHONUTF8='1'))


# ---------------- 入口：缺件即 ABORT，本遍要产的载体必须是空槽 ----------------
for _p in (DOC, FREQ, CAR_E, CAR_E2, PWCAR, FIXER, VMRUN):
    assert os.path.isfile(_p), 'ABORT: 前置件不存在 ' + _p
assert not os.path.exists(CARRIER), 'ABORT: 订正遍载体已存在 ⇒ 不许覆写自己该产出的那只'
assert mtime(PWCAR).timestamp() < _T0, 'ABORT: 上一遍载体在本遍进入后被改过 ⇒ 本遍不能声称它一字节未动'
_mm = re.search(r'\s*#define\s+PROV_PASS\s+"([^"]*)"', rd(MACRO))
assert _mm and _mm.group(1), 'ABORT: 读不到 PROV_PASS 宏'
SECRET = _mm.group(1).encode('utf-8')

DOC_T, FREQ_T = rd(DOC), rd(FREQ)
DL, FL = DOC_T.split('\r\n'), FREQ_T.split('\r\n')
N_DOC0, N_FREQ0 = DOC_T.count('\n'), FREQ_T.count('\n')
assert DOC_T.count('\n') == DOC_T.count('\r\n') and FREQ_T.count('\n') == FREQ_T.count('\r\n'), 'ABORT: 行尾不再纯 CRLF'
assert DOC_T.endswith('\r\n') and FREQ_T.endswith('\r\n'), 'ABORT: 文件末尾无行尾 ⇒ 追加会粘行'

# ---------------- ① 被订正那格：正文与载体各读一遍，先证两处同名 ----------------
_landed = [l for l in DL if l.startswith('- **登记（§38.27 落纸遍崩在写载体之前')]
assert len(_landed) == 1, 'ABORT: 补落遍那条登记句现算 %d 处 ⇒ 上一遍到底落了没有，先查盘' % len(_landed)
LAND = _landed[0]
LAND_N = DL.index(LAND) + 1
PW_TXT = rd(PWCAR)
_m = re.search(r'｜(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) 补落遍现跑', LAND)
assert _m, 'ABORT: 补落遍那条登记句里的时刻读不到 ⇒ 本遍的"上一遍"没有出处'
FIX_AT = datetime.strptime(_m.group(1), '%Y-%m-%d %H:%M:%S')
_pw_at = re.search(r'订正（§38.25 第 3732 行③句｜([\d\- :]+)', DL[3764])
assert _pw_at, 'ABORT: 崩溃遍落纸时刻读不到 ⇒ 双侧窗口没有下界'
assert len([l for l in DL if l.startswith('- **订正（§38.25 第 3732 行③句')]) == 1, 'ABORT: 崩溃遍那条订正句不唯一 ⇒ 下界取自哪一遍说不清'
_m = re.search(r'代落件 = `hardware/(vm_run_\d+_\d+)\.txt` 属那一遍', LAND)
assert _m, 'ABORT: 在册那句没有指名代落件 ⇒ 本遍订正的对象不存在'
CLAIMED = _m.group(1)
_m = re.search(r'CRASH 崩溃遍证据.*?代落件 = (hardware/vm_run_\d+_\d+)\.txt', PW_TXT, re.S)
assert _m, 'ABORT: 上一只载体里读不到 CRASH 那行的代落件名'
assert CLAIMED == _m.group(1).split('/')[-1], 'ABORT: 正文与载体各指一只代落件（%s vs %s）⇒ 缺陷比登记的还大一格' % (CLAIMED, _m.group(1))
PW_CRASH = [l for l in PW_TXT.split('\n') if l.startswith('CRASH ')][0]

# ---------------- ② 真值现读：崩溃遍的代落件只能落在"崩溃遍落纸 → 崩溃遍已落盘那只件"这格双侧窗口里 ----------------
CRASH_AT = _pw_at.group(1)
CRASH_T = datetime.strptime(CRASH_AT, '%Y-%m-%d %H:%M:%S')
CRASH_LAND = mtime(CAR_E2)                       # 崩溃遍真正落盘的那一只 = 那一遍的"最后已知写入时刻"
CRASH_TOP = CRASH_LAND.replace(microsecond=0)    # 名字只到秒，比较必须在同一精度上做（否则 .432 这类小数会把真值筛掉）
assert CRASH_T <= CRASH_TOP < FIX_AT, 'ABORT: 崩溃遍两格时刻不成序（正文 %s / 落盘件 %s / 补落遍 %s）⇒ 双侧窗口没有上界' % (
    CRASH_AT, CRASH_TOP.strftime('%Y-%m-%d %H:%M:%S'), FIX_AT.strftime('%Y-%m-%d %H:%M:%S'))
CAND = sorted([f for f in os.listdir(HDIR) if f.startswith('vm_run_') and '20260925' in f], key=nm_time)
assert CAND, 'ABORT: 现算 0 只候选 ⇒ 归属断言没有池子可查，本遍不落订正'
REAL = [f for f in CAND if CRASH_T <= nm_time(f) <= CRASH_TOP and mtime(os.path.join(HDIR, f)).timestamp() < _T0]
assert len(REAL) == 1, 'ABORT: 双侧窗口筛出 %d 只（%s）⇒ 归属没有唯一真值，本遍不落订正' % (len(REAL), REAL)
REAL_ONE = REAL[0]
LATE = [f for f in CAND if CRASH_TOP < nm_time(f) < FIX_AT]      # 补落遍自己中止那一次产的，单侧上界会把它端出去
assert nm_time(CLAIMED + '.txt') >= FIX_AT, 'ABORT: 在册那格的时刻早于补落遍 ⇒ 它不是本遍产的，归因要重写'
assert CLAIMED + '.txt' not in REAL and CLAIMED + '.txt' in CAND, 'ABORT: 在册那格通过了双侧窗口 ⇒ 补落遍那句根本不错，本遍不该落订正'
# 第四格 = 本订正遍自己在写盘前中止的那些尝试产的代落件（名字必然晚于补落遍）；不承认这一格，池子就分不完
OTHER = [f for f in CAND if f not in REAL + LATE + [CLAIMED + '.txt']]
assert all(nm_time(f) > FIX_AT for f in OTHER), 'ABORT: 池里有"名字早于补落遍却没被前两格吃掉"的只 ⇒ 归属没查清，本遍不落订正'
assert sorted(REAL + LATE + OTHER + [CLAIMED + '.txt']) == sorted(CAND), 'ABORT: 候选池四格未分完 ⇒ 有第五只没被点名'

FORE = rd(CAR_E)
# 同形证明：被错指那只在补落遍载体里逐字在册（正文与载体两处同名），且它与真值那只只差 RUN_AT 一行
SAID = rd(os.path.join(HDIR, CLAIMED + '.txt')).split('\n')
TRUE_ = rd(os.path.join(HDIR, REAL_ONE)).split('\n')
assert len(SAID) == len(TRUE_), 'ABORT: 两只代落件行数不等 ⇒ "内容同形"这句要重写'
DIFF_ROWS = [i + 1 for i in range(len(SAID)) if SAID[i] != TRUE_[i]]
assert DIFF_ROWS == [2] and SAID[1].startswith('RUN_AT=') and TRUE_[1].startswith('RUN_AT='), \
    'ABORT: 两只差异行现算 %s（应只有第 2 行 RUN_AT）⇒ 本遍不能声称"只订正归属、不动数值"' % DIFF_ROWS
assert '\r' not in rd(os.path.join(HDIR, CLAIMED + '.txt')), 'ABORT: 代落件行尾不纯 LF ⇒ 上面那把按 LF 切行的尺不可信'
assert CLAIMED + '.txt' in PW_CRASH and REAL_ONE not in PW_CRASH, 'ABORT: 载体 CRASH 行里的名字与本遍现读不符'
STALE_HITS = stale_bad(DL)
assert STALE_HITS == [3732, 3746], 'ABORT: 违规旧等式句位置现算 %s（应 [3732, 3746]）' % STALE_HITS
CORR = [i + 1 for i, l in enumerate(DL) if l.startswith('- **订正（') and STALE in l]
N_TOTAL = len([l for l in FL if l.startswith('[错误类型]')])
assert N_TOTAL == 213, 'ABORT: FreqErr 条数现算 %d（应 213 = 209 + 第二批 4）⇒ 第二批到底落没落' % N_TOTAL
FSEC2 = [i for i, l in enumerate(FL) if l.startswith('## 2026-09-25（R57 第二批')]
assert len(FSEC2) == 1, 'ABORT: 第二批那节现算 %d 处' % len(FSEC2)
N_SEC2 = len([l for l in FL[FSEC2[0]:] if l.startswith('[错误类型]')])
assert N_SEC2 == 4, 'ABORT: 第二批正文条数现算 %d（应 4）' % N_SEC2
assert os.path.getsize(CAR_E) == os.path.getsize(CAR_E2), 'ABORT: 判据摘录两只尺寸不等 ⇒ 崩溃遍落的 v2 不是同一取证件的复跑'

S0A, S0B = fold_a(SYNC), fold_b(SYNC)
_m = re.search(r'SEAL 写盘前 hardware/ht305_sync/ = .*?聚合 md5 ([0-9a-f]{32})', FORE)
assert _m, 'ABORT: 取证载体里的聚合 md5 读不到'
SEAL_REF = _m.group(1)
assert S0A[2] == SEAL_REF, 'ABORT: FOLD-A 本遍不复现在册值 ⇒ 归档可能真被改过，立刻停'
PROBE = 'evidence/SEAL_VIOLATION_PROBE8.txt'
assert not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: 内存对照名字在盘上存在 ⇒ 对照泄漏成文件'
assert fold_a(SYNC, extra=PROBE)[2] != S0A[2] and fold_b(SYNC, extra=PROBE)[2] != S0B[2], 'ABORT: SEAL 门无执行者'

_vm = run((sys.executable, VMRUN))
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器代落件本遍没跑绿 rc=%d' % _vm.returncode
VM_CARRIER = _mc.group(1).split('/')[-1]
_vm_txt = rd(os.path.join(HDIR, VM_CARRIER))
assert 'INNER_VERDICT=VERDICT=MANIFEST_STILL_TRUE' in _vm_txt, 'ABORT: 内层裁决不是 MANIFEST_STILL_TRUE ⇒ 封界已漂'
INNER_ROWS = [l for l in _vm_txt.split('\n') if l.startswith('INNER_ROWS=')][0]
assert nm_time(VM_CARRIER) > FIX_AT, 'ABORT: 本遍代落件名不晚于被订正那格 ⇒ "时刻上界"这把尺没长出来'
assert nm_time(VM_CARRIER) > nm_time(CLAIMED + '.txt'), 'ABORT: 本遍那只不晚于在册那格 ⇒ 新装的执行者不成立'

_pp = run((sys.executable, '-m', 'serial.tools.list_ports'))
PORTS = sorted(set(re.findall(r'(?m)^(COM\d+)', _pp.stdout.decode('utf-8', 'replace'))))
REV = run(('git', 'rev-list', '--count', 'origin/main..HEAD')).stdout.decode('utf-8', 'replace').strip()
ST = [l for l in run(('git', '-c', 'core.quotePath=false', 'status', '--porcelain')).stdout.decode('utf-8', 'replace').splitlines() if l.strip()]

# ---------------- ③ 构造追加正文 ----------------
POOL = ' / '.join('%s（%s）' % (f[:-4], nm_time(f).strftime('%H:%M:%S')) for f in CAND)
DOC_ADD = ('- **订正（§38.27 补落遍那条登记句｜' + RUN_AT + '）**：补落遍（' + FIX_AT.strftime('%Y-%m-%d %H:%M:%S') + '）那条登记句（现读第 ' + str(LAND_N) + ' 行）'
           '与它落的载体 `hardware/r57_paperwork1.txt` 的 `CRASH` 行都写着「崩溃遍代落件 = `hardware/' + CLAIMED + '.txt`」，'
           '**那只其实是补落遍自己在同一刻产的代落件**（本遍现读它的名字时刻与 mtime 都是 ' + nm_time(CLAIMED + '.txt').strftime('%H:%M:%S') +
           '，与补落遍那一刻同秒）—— 错的成因：候选只按"名字含崩溃日期"筛、取 `sorted()[-1]` 当"上一遍那只"，'
           '而落地器固定顺序里 `vm_run.py` 排在构造正文**之前**，本遍那只当时已进池且是池里最大的名字。'
           '真正的崩溃遍代落件由本遍现读，尺子是**双侧窗口**：名字时刻不早于崩溃遍落纸 ' + CRASH_AT +
           '、不晚于崩溃遍那只已落盘件（判据摘录 v2）的 mtime ' + CRASH_TOP.strftime('%H:%M:%S') +
           '，且 mtime 早于本遍进入时刻 ' + datetime.fromtimestamp(_T0).strftime('%H:%M:%S') + ' ⇒ 唯一命中 = `hardware/' + REAL_ONE +
           '`（名字时刻 ' + nm_time(REAL_ONE).strftime('%H:%M:%S') + '）。池子逐格点名（2026-09-25 的 `vm_run_*` 共 ' + str(len(CAND)) + ' 只：' + POOL +
           '）：' + REAL[0][:-4] + ' = 崩溃遍产的，' + (LATE[0][:-4] if LATE else '（无）') + ' = 补落遍**中止那一次**产的，' + CLAIMED +
           ' = 补落遍成功那一次产的；' + (' / '.join(f[:-4] for f in OTHER) if OTHER else '（无）') +
           ' = 本订正遍自己在写盘前中止的那 ' + str(len(OTHER)) + ' 次尝试产的 ⇒ 四格分完候选池（第四格必须点名，否则"分完"就是漏了一只没查）。' +
           '顺带点名一处本遍自己差点犯的：订正遍第一稿的筛子写成"名字时刻 **早于补落遍**"这一**单侧**上界，实测它会端出 ' +
           (LATE[0][:-4] if LATE else '（无）') + ' 那只（补落遍中止那一次的产物，同样不属于崩溃遍）⇒ 单侧上界不够，真尺子必须有下界；'
           '本遍载体 `TRUTH` 行那句"四格分完候选池"就是这件事的执行者（第五只进池又落不进任何一格即 ABORT）。'
           '崩溃遍三格时刻互核：正文 ' + CRASH_AT + ' / 代落件名字时刻 ' + nm_time(REAL_ONE).strftime('%Y-%m-%d %H:%M:%S') +
           ' / 判据摘录 v2 mtime ' + mtime(CAR_E2).strftime('%Y-%m-%d %H:%M:%S') + ' ⇒ 三格同遍。'
           '本遍只订正那一只代落件的**归属**，不动任何数值：被错指那只与真值那只逐行只差第 ' + str(DIFF_ROWS[0]) +
           ' 行（`RUN_AT=`，本遍现读两只各 ' + str(len(TRUE_)) + ' 行、纯 LF）⇒ "内容同形、只名字不同"这句是现算的，不是推测；'
           '补落遍其余读数本遍复算不变（违规旧等式句仍 = ' + str(STALE_HITS) + '、订正句仍 ' + str(CORR) + '、FreqErr 条数仍 = ' + str(N_TOTAL) +
           '、FOLD-A 仍复现在册聚合 `' + S0A[2][:8] + '…`）。错误类型进 `FreqErr.md` 本批 1 条（根族："上一遍的那只"要双侧窗口才认得出）；'
           '执行者 = 本遍的双侧窗口 + 池子四格划分 + 载体 `VM` 行那两句"本遍那只必须严格晚于被订正那格"。')

F0 = ['',
      '## 2026-09-25（R57 第三批：把本遍刚产的代落件指给了上一遍）新增 1 条（根族：**"上一遍的那只"要双侧窗口才认得出**）',
      '',
      '[错误类型] **在同一目录里挑"上一遍产的那只"时按名字排序取末位，而候选池在挑选之前已被本遍自己污染的步骤产脏 ⇒ 把本遍刚产的凭证指给上一遍（自指落在"归属"而不是"计数"上）**'
      '（本批实测：补落遍那句「崩溃遍代落件 = `hardware/' + CLAIMED + '.txt`」的名字时刻 = ' + nm_time(CLAIMED + '.txt').strftime('%H:%M:%S') +
      ' 就是补落遍自己那一刻；真值 = `hardware/' + REAL_ONE + '`；同一天同前缀的候选池有 ' + str(len(CAND)) + ' 只，三格分属三遍）',
      '→ 症状：候选定义只写了"名字含崩溃日期"，没写窗口；'
      '而落地器的固定顺序是「先跑内层复核器（它必然产一只新代落件）→ 再构造正文」，于是构造正文时**本遍那只已是池里最大的名字**，`sorted()[-1]` 恰好把它端出去当"上一遍的证据"。'
      '同一句归属在正文与载体里各写一次 ⇒ 同一个错在盘上留下两格，而两格彼此"互证"，看起来反而更可信。',
      '→ 为什么它危险：这条错**不改变任何数值** —— 两只代落件实测逐行只差 `RUN_AT=` 一行（本批现算：各 ' + str(len(TRUE_)) + ' 行、差异行 = ' + str(DIFF_ROWS) +
      '），裁决同为 `MANIFEST_STILL_TRUE`，所以所有数值型门全绿；它改的是"哪一遍跑过"，而"引用即复跑"整条纪律靠的正是归属。'
      '归属一错，查案的人会去核一只根本没参与那一遍的文件，**而且核得过**。'
      '同族更早的形态是"文件名时刻 ≠ 动作时刻"（项目记忆 (48)(49)）与"凭证写的时刻 ≠ 它标的那一刻"（(70)），本条是它们的孪生：**用文件名排序去认"上一遍"，而排序里混着本遍**。',
      '→ 正确做法：①凡"上一遍的那只"必须用**双侧窗口**：下界 = 那一遍落纸时刻（本批从崩溃遍那条订正句现读），上界 = **那一遍已落盘的那只件的 mtime**（本批 = 判据摘录 v2），'
      '再加"mtime 早于本遍进入时刻"（`_T0` 要在任何产证动作之前取）；**单侧上界不够**——本遍订正稿第一稿写的是"名字时刻早于补落遍"，'
      '实测它端出的是补落遍**中止那一次**产的 ' + (LATE[0][:-4] if LATE else '（无）') + '，与错的那格同一族；'
      '②挑完立刻装正向对照：本遍自己产的凭证名必须**严格大于**被订正那格（本遍载体 `VM` 行两句断言是执行者），否则 ABORT；'
      '③同一份归属断言在正文与载体各写一次时，要断言两处**逐字同名**（本遍现读两处并相等），不然连"错得一致"都不能保证；'
      '④候选池为 0 必须 ABORT（不许让"没找到上一遍"长得像"上一遍没跑过"），并把池子**逐格分完**：本批载体 `TRUTH` 行断言"崩溃遍 + 补落遍中止那次 + 补落遍成功那次 + 本订正遍中止的那几次 = 整个池"，'
      '把每一只都落进某一格（本批四格：崩溃遍 / 补落遍中止那次 / 补落遍成功那次 / **本订正遍自己中止的那几次**）—— 第五只落不进任何一格即红。'
      '只筛出"唯一命中"而不证明池被分完，等于没证明；本遍第一次跑这条判据时就是因为没给"自己中止的尝试"留格子，池子必然分不完。'
      '⑤已落地的错句不回写、错的载体不重写，只追加订正句并新落一只载体（本遍没碰 `hardware/r57_paperwork1.txt`，它的 mtime 早于本遍进入时刻是这件事的断言）；'
      '⑥配套工具自己的"按位切片认时刻"要换成整模式匹配：本遍第一稿写 `f[7:21]` 配 `%H%M%S`，把 13:10:49 截成 13104 → 解成 13:10:04（秒被吃掉一位），'
      '实测它在写盘前红在"双侧窗口 0 命中"那一格而没落任何错句 —— 换成整名匹配（`vm_run_` + 8 位日期 + 下划线 + 恰好 6 位时刻 + `.txt`，不匹配即 ABORT）之后，同一遍才拿到唯一真值。',
      '→ **同族**：项目记忆 (48)"文件名时刻 ≠ 动作时刻"、(49)"别把文件 birth 当本只动作时刻"、(70)"凭证写的时刻 ≠ 它标的那一刻（三型）"、(56)"行尾也是一把尺子"、'
      '§38.21 ①（"只在下一批才执行"那一族）、本批第二条根族（我写过 ≠ 我跑过）。',
      ]
FREQ_BODY = '\r\n'.join(F0) + '\r\n'
LEDGER = ('> **【' + RUN_AT + ' 落地｜R57 第三批 1 条】** 追加之前现读磁盘（本脚本进入时刻 ' + datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S') +
          '，_T0 取在任何产证动作之前）：全文 `^[错误类型]` 条数 = **' + str(N_TOTAL) + '**、行数 = **' + str(N_FREQ0) + '**、字节 = **' + money(len(FREQ_T.encode('utf-8'))) + '**；'
          '本批正文（不含本台账行自己，含上方那只 glue 空行）= **1** 条 / **' + str(len(F0) + 1) + '** 行 / **' + money(len(FREQ_BODY.encode('utf-8'))) + '** B；'
          '**落盘后的终态三格由载体 `LAND` 行现数**（完成态数字不许预写）。同遍排查记录 改前 **' + str(N_DOC0) + '** 行 / **' + money(len(DOC_T.encode('utf-8'))) +
          '** B -> 本批真追加 2 行（1 只 glue 空行 + 1 行订正句），前缀等式成立、纯 CRLF；补落遍那条登记句与崩溃遍正文、上一遍载体均一字节未回写。')

DOC_NEW = DOC_T + '\r\n' + DOC_ADD + '\r\n'
FREQ_NEW = FREQ_T + '\r\n' + FREQ_BODY + LEDGER + '\r\n'
for _nm, _blk in (('DOC', DOC_ADD), ('FREQ', '\n'.join(F0 + [LEDGER]))):
    assert '\\' not in _blk, 'ABORT: ' + _nm + ' 正文含反斜杠'
    assert SECRET.decode('utf-8', 'replace') not in _blk, 'ABORT: ' + _nm + ' 正文含 PROV_PASS 明文'
    for _s in ('%s', '%d', '@@', 'None', 'BUIL'):
        assert _s not in _blk, 'ABORT: ' + _nm + ' 正文含未替换哨兵 ' + _s
assert DOC_NEW.startswith(DOC_T) and FREQ_NEW.startswith(FREQ_T), 'ABORT: 前缀等式不成立 ⇒ 不是纯追加'
open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)

_dt, _ft = rd(DOC), rd(FREQ)
assert _dt == DOC_NEW and _ft == FREQ_NEW, 'ABORT: 回读不等于写入串'
_ftl = _ft.split('\r\n')
N_TOTAL_END = len([l for l in _ftl if l.startswith('[错误类型]')])
assert N_TOTAL_END == N_TOTAL + 1, 'ABORT: 写盘后条数不等于 在册 + 1'
assert stale_bad(_dt.split('\r\n')) == STALE_HITS, 'ABORT: 订正遍自己复抄了旧等式句'
assert mtime(PWCAR).timestamp() < _T0, 'ABORT: 上一遍载体在本遍被写过 ⇒ 本遍不许声称它未动'
S1A, S1B = fold_a(SYNC), fold_b(SYNC)
assert S1A == S0A and S1B == S0B, 'ABORT: 归档目录被本遍改动 ⇒ gen 24 末版被亲手降级'
PW_MD5 = hashlib.md5(open(PWCAR, 'rb').read()).hexdigest()

ROWS = []
ROWS.append('R57 第三批（订正遍）  MODE=CORRECT-PASS')
ROWS.append('本遍现跑于 ' + RUN_AT + '（进入时刻 _T0 = ' + datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S') + '，取在任何产证动作之前）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('SUBJECT 被订正那格：补落遍时刻 = ' + FIX_AT.strftime('%Y-%m-%d %H:%M:%S') + '（现读那条登记句，它在排查记录第 ' + str(LAND_N) + ' 行）；'
            '正文与载体两处逐字同名 = True；在册断言 =「崩溃遍代落件 = hardware/' + CLAIMED + '.txt」')
ROWS.append('FALSE 本遍现读证伪：那只 mtime = ' + mtime(os.path.join(HDIR, CLAIMED + '.txt')).strftime('%Y-%m-%d %H:%M:%S') + '、名字时刻 = ' +
            nm_time(CLAIMED + '.txt').strftime('%H:%M:%S') + ' ⇒ 与补落遍同秒，是补落遍自己产的；在册载体那行逐字 = PW_CRASH 行（本遍现读，见 WITNESS）')
ROWS.append('TRUTH 真值（**双侧窗口**：名字时刻 ∈ [%s, %s] 且 mtime < _T0；候选池 %d 只）= hardware/%s（名字时刻 %s）；'
            '池子四格分完 = True：%s（崩溃遍）+ %s（补落遍中止那一次）+ %s（补落遍成功那一次，即被错指那只）+ 本遍此前中止的尝试 %d 只 [%s]；'
            '崩溃遍三格互核：正文 %s / 代落件 %s / 判据摘录 v2 %s ⇒ 同遍；池为 0 或窗口多命中本遍即 ABORT（现算 %d / 1）' % (
                CRASH_AT[-8:], CRASH_TOP.strftime('%H:%M:%S'), len(CAND), REAL_ONE, nm_time(REAL_ONE).strftime('%H:%M:%S'),
                ', '.join(f[:-4] for f in REAL), ', '.join(f[:-4] for f in LATE) or '无', CLAIMED,
                len(OTHER), ', '.join(f[:-4] for f in OTHER) or '无', CRASH_AT,
                nm_time(REAL_ONE).strftime('%Y-%m-%d %H:%M:%S'), mtime(CAR_E2).strftime('%Y-%m-%d %H:%M:%S'), len(CAND)))
ROWS.append('SHAPE 只订正归属不动数值的证据：被错指那只与真值那只各 %d 行、纯 LF，逐行差异行 = %s（正是 `RUN_AT=` 那一行）⇒ "内容同形、只名字不同"是现算不是推测' % (
    len(TRUE_), DIFF_ROWS))
ROWS.append('UNCHANGED 上一遍其余读数本遍复算不变：违规旧等式句 = %s / 订正句 = %s / FreqErr 条数 = %d（= 209 + 第二批 %d）/ '
            '判据摘录两只尺寸相等 = True / FOLD-A 复现在册聚合 = True ⇒ 本遍只订正归属，不动数值' % (STALE_HITS, CORR, N_TOTAL, N_SEC2))
ROWS.append('VM 本遍现跑内层复核器代落：rc=0 / %s / 代落件 = hardware/%s；本遍那只名字时刻严格晚于补落遍 = True，且严格晚于在册被订正那格 = True（这两句就是新装的执行者）' % (INNER_ROWS, VM_CARRIER))
ROWS.append('FIELD 现跑：串口枚举 = %s ⇒ COM14 在位 = %s（补落遍那格也是 False，两遍同形但各量各的，不许复用）/ rev-list = %s（未 push）/ '
            'status --porcelain = %d 行（%d 只 M + %d 只 ??）' % (
                ', '.join(PORTS), str('COM14' in PORTS), REV, len(ST),
                len([l for l in ST if l[:2] == ' M']), len([l for l in ST if l[:2] == '??'])))
ROWS.append('SEAL 写盘前后两把尺全等：FOLD-A = %d 只 / %s B / %s；FOLD-B = %d 只 / %s B / %s；两把尺只数字节互核 = %s；'
            '内存假名 %s 使两把尺双红 = True，盘上无那只文件 = True ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版' % (
                S0A[0], money(S0A[1]), S0A[2], S0B[0], money(S0B[1]), S0B[2], str(S0A[0] == S0B[0] and S0A[1] == S0B[1]), PROBE))
ROWS.append('GATE 本遍各道门：空槽 0 破 / 缺件 0 / 上一遍载体未被本遍写 0 破 / 行尾 0 破 / 前缀等式 0 破 / 反斜杠 0 / 明文 0 / 哨兵 0 / 回读等值 0 破 / '
            '归属双侧窗口（含"池子四格分完"）0 破 / 两只代落件同形（差异只 RUN_AT 一行）0 破 / SEAL 0 破 ⇒ ARMS_FIRED（真红计数）：'
            '证伪在册归属 1 + 内存假名 2（FOLD-A/FOLD-B 各 1）= 3 次；另点名本遍自己写盘前的两处自纠（都不落盘、不算真红）：'
            '订正稿第一稿用单侧上界（名字时刻 < 补落遍）会端出 %s 那只，改双侧窗口；'
            '同一稿的名字切片把秒数吃掉一位（13:10:49 解成 13:10:04），实测红在"窗口 0 命中"，改整名匹配' % (LATE[0][:-4] if LATE else '无'))
ROWS.append('LAND 写盘后独立回读现数：排查记录 = %d 行 / %s B / md5 %s；FreqErr = %d 行 / %s B / md5 %s / 条数 = %d（= 在册 %d + 本批 1）；'
            '上一遍载体 hardware/r57_paperwork1.txt 本遍未碰：md5 %s / mtime %s（早于 _T0 = True）' % (
                _dt.count('\n'), money(len(_dt.encode('utf-8'))), hashlib.md5(_dt.encode('utf-8')).hexdigest(),
                _ft.count('\n'), money(len(_ft.encode('utf-8'))), hashlib.md5(_ft.encode('utf-8')).hexdigest(),
                N_TOTAL_END, N_TOTAL, PW_MD5, mtime(PWCAR).strftime('%Y-%m-%d %H:%M:%S')))
ROWS.append('WITNESS 本遍现读 md5（前 12 位）：上一遍载体 %s / 订正遍工具 %s / 补落遍工具 %s / 取证载体 %s / 其 v2 %s' % (
    PW_MD5[:12],
    hashlib.md5(open(__file__, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(FIXER, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(CAR_E, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(CAR_E2, 'rb').read()).hexdigest()[:12]))
ROWS.append('NOTDONE 本批没做（点名）：没碰串口 / 没烧录 / 没改 main/ 源码 / 没重建固件 / 没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / 没 push、没 amend / 零删除 / '
            '没回写补落遍那条登记句、没重写上一遍载体、没改崩溃遍正文（只追加订正句）/ 屏亮仍 0 次肉眼确认 ⇒ 不播提示音 / '
            'docs 快照第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数')
_j = next(k for k, l in enumerate(ROWS) if l.startswith('GATE '))
ROWS.insert(_j + 1, 'GATE-COUNT 本载体行数（所有行追加完之后才求值，避开补落遍点名过的那个自指缺陷）= %d 行（含本行）' % (len(ROWS) + 1))
TXT = '\n'.join(ROWS) + '\n'
assert '\\' not in TXT and SECRET.decode('utf-8', 'replace') not in TXT, 'ABORT: 载体含反斜杠或明文'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(TXT)
_rb = open(CARRIER, 'rb').read()
assert _rb.decode('utf-8') == TXT and _rb.count(b'\r') == 0, 'ABORT: 载体回读不等于写入串或非纯 LF'
print('CARRIER=%s  ROWS=%d  BYTES=%d' % (os.path.basename(CARRIER), TXT.rstrip('\n').count('\n') + 1, len(_rb)))
print('CLAIMED=%s（补落遍自己产的）/ REAL=%s（崩溃遍产的）' % (CLAIMED, REAL_ONE))
print('DOC %d 行 / FREQ %d 行 / 条数 %d -> %d' % (_dt.count('\n'), _ft.count('\n'), N_TOTAL, N_TOTAL_END))
print('VERDICT=R57-CORRECT-PASS-LANDED')
