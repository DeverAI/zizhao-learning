# R57 补落遍（崩溃遍的下一遍）：崩在 ROWS 自指那一遍已把两处正文落盘、paperwork 载体没落。
# 规矩（沿用 R55/R56/R57）：已落纸的内容**不回写、不洗绿**，本遍只做三件事 ——
#   ①把已落纸的 §38.27 用本遍现算逐字回核（四臂重新解析 + 在册句里的数逐个现算比对）；
#   ②追加一条登记句（点名崩溃遍、点名那句指向不存在载体的完成态指针、点名两把聚合尺）；
#   ③本遍自己现跑 vm_run / SEAL / FIELD / POSCTL，再落那只缺失的载体 hardware/r57_paperwork1.txt。
# 红线：正文不含反斜杠、不含明文凭据、不含未替换哨兵；两个目标文件都只纯追加（前缀等式）；
#   归档目录 hardware/ht305_sync/ 写盘前后两把折法各扫一遍并互核；阳性对照只进内存不落盘。
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
CAR_E = os.path.join(HDIR, '20260925_R57_E臂判据摘录.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
FLASH = os.path.join(HDIR, 'r57_flash1.py')
LANDER = os.path.join(HDIR, 'r57_paperwork1.py')
VMRUN = os.path.join(HDIR, 'vm_run.py')
CARRIER = os.path.join(HDIR, 'r57_paperwork1.txt')
MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
LOGS = {
    'B': os.path.join(HDIR, '20260924_R56外部供电复位起抓45s_板上4842a3a0.log'),
    'C': os.path.join(HDIR, '20260924_R56fb32168a首烧复位起抓90s.log'),
    'D': os.path.join(HDIR, '20260924_R56按键窗口150s纯读_新镜像fb32168a.log'),
    'E': os.path.join(HDIR, '20260925_R57_E臂新镜像锂电池在位复位起抓120s.log'),
}
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

ANSI = re.compile(r'\x1b\[[0-9;]*m')
UP = re.compile(r'[IWE] \((\d+)\)')
PRB = re.compile(r'probe#(\d+)')
PWR = re.compile(r'PWR_OUT pu=(-?\d) pd=(-?\d)')
ACKT = re.compile(r'[^N]ACK=(\d+)')
ACKED = re.compile(r'acked:\[([^\]]*)\]')
BUS = re.compile(r'bus scan 0x08-0x77: ACK=(\d+) NACK=(\d+)')
ELF = re.compile(r'ELF file SHA256:\s+([0-9a-f]{16})')
STALE = '板上仍是 `4842a3a0…`'


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def parse(p):
    raw = open(p, 'rb').read()
    txt = ANSI.sub('', raw.decode('utf-8', 'replace'))
    lines = [l.rstrip('\r') for l in txt.split('\n') if l.strip()]
    ups = [int(m.group(1)) for m in UP.finditer(txt)]
    return dict(bytes=len(raw), md5=hashlib.md5(raw).hexdigest(), rom=txt.count('ESP-ROM'),
                n34=sum(1 for l in lines if 'AXP@0x34' in l),
                replies=sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' not in l),
                probe=len(PRB.findall(txt)), pwr=sorted(set(PWR.findall(txt))),
                ack=sorted(set(ACKT.findall(txt))), acked=sorted(set(ACKED.findall(txt))),
                bus=sorted(set(BUS.findall(txt))),
                up0=ups[0] if ups else -1, up1=ups[-1] if ups else -1,
                win=(ups[-1] - ups[0]) / 1000.0 if ups else -1.0,
                elf=[m.group(1) for l in lines for m in [ELF.search(l)] if m])


def fold_a(d, extra=None):
    """与 hardware/r57_flash1.py 的 scan_dir 同折法：walk 序，只喂 md5(content) 的 hex。"""
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
    """与 hardware/r57_paperwork1.py 的 scan_dir 同折法：name:md5 名单排序后用竖线连接再折。"""
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


# ---------------- 入口前置：缺件即 ABORT；本遍即将产出的载体必须是空槽 ----------------
for _p in (CAR_E, DOC, FREQ, LOGS['B'], LOGS['C'], LOGS['D'], LOGS['E'], FLASH, LANDER, VMRUN):
    assert os.path.isfile(_p), 'ABORT: 前置件不存在 ' + _p
assert not os.path.exists(CARRIER), 'ABORT: paperwork 载体已存在 ⇒ 本工具不许覆写自己该产出的那只（槽位口径见载体 CRASH 行）'
assert os.path.exists(CAR_E2), 'ABORT: 崩溃遍的 POSCTL 副产物（判据摘录 v2）不在 ⇒ 崩溃痕迹与本遍叙述不同，先查盘'

_mm = re.search(r'\s*#define\s+PROV_PASS\s+"([^"]*)"', rd(MACRO))
assert _mm and _mm.group(1), 'ABORT: 读不到 PROV_PASS 宏 ⇒ 明文闸无法自证扫的是真口令'
SECRET = _mm.group(1).encode('utf-8')

P = {k: parse(v) for k, v in LOGS.items()}
for k in P:
    P[k]['pp'] = P[k]['win'] / P[k]['probe'] if P[k]['probe'] else -1.0

FORE = rd(CAR_E)
DOC_T = rd(DOC)
FREQ_T = rd(FREQ)
DL = DOC_T.split('\r\n')
FL = FREQ_T.split('\r\n')
assert DOC_T.count('\n') == DOC_T.count('\r\n'), 'ABORT: 排查记录行尾不再纯 CRLF'
assert FREQ_T.count('\n') == FREQ_T.count('\r\n'), 'ABORT: FreqErr 行尾不再纯 CRLF'
assert DOC_T.endswith('\r\n') and FREQ_T.endswith('\r\n'), 'ABORT: 目标文件末尾无行尾 ⇒ 追加会粘行'
N_DOC0 = DOC_T.count('\n')
N_FREQ0 = FREQ_T.count('\n')
B_DOC0 = len(DOC_T.encode('utf-8'))
B_FREQ0 = len(FREQ_T.encode('utf-8'))

# ---------------- ① 已落纸内容回核：本遍现算的数必须逐字出现在已落纸的那几行里 ----------------
head_i = [i for i, l in enumerate(DL) if l.startswith('### 38.27')]
assert len(head_i) == 1, 'ABORT: §38.27 标题现算 %d 处（应唯一）⇒ 落纸形状与叙述不同' % len(head_i)
H = head_i[0] + 1                                     # 1-based
tail_i = [i for i, l in enumerate(DL) if l.startswith('- **订正（§38.26 第 3746 行③句')]
assert len(tail_i) == 1, 'ABORT: §38.26 那条订正句现算 %d 处 ⇒ 崩溃遍落的两条订正句不在册' % len(tail_i)
T = tail_i[0] + 1
SEC_LINES = T - H + 1
sec = '\r\n'.join(DL[H - 1:T])
assert '锂电池在位 + 复位起抓那一格' in sec, 'ABORT: §38.27 标题句与登记内容不符'

ARM_LINE = [l for l in DL[H - 1:T] if l.startswith('- **四臂节奏对照')]
E_LINE = [l for l in DL[H - 1:T] if l.startswith('- **E 臂读数')]
assert len(ARM_LINE) == 1 and len(E_LINE) == 1, 'ABORT: §38.27 里四臂行/E 臂行各应唯一（现 %d/%d）' % (len(ARM_LINE), len(E_LINE))
PHRASES = [
    'C 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s' % (P['C']['win'], P['C']['probe'], P['C']['pp']),
    'D 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s' % (P['D']['win'], P['D']['probe'], P['D']['pp']),
    'E 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s' % (P['E']['win'], P['E']['probe'], P['E']['pp']),
    '现算窗口 = %.3f s、每 probe = %.3f s' % (P['B']['win'], P['B']['pp']),
    'uptime %d→%d ms ⇒ 窗口 %.3f s / probe# %d 次' % (P['E']['up0'], P['E']['up1'], P['E']['win'], P['E']['probe']),
    '0x34` 行 %d 条' % P['B']['n34'],
    'banner 1 次' if P['B']['rom'] == 1 else 'B 臂 banner 现算 %d 次与在册不同' % P['B']['rom'],
]
CHECKS = [('sec', i, v, v in sec) for i, v in enumerate(PHRASES)]
for k in ('B', 'C', 'D', 'E'):
    assert P[k]['replies'] == 0, 'ABORT: %s 臂本遍现算出现 0x34 应答 %d 条 ⇒ 全 NACK 判读整体作废' % (k, P[k]['replies'])
bad = [c for c in CHECKS if not c[3]]
assert not bad, 'ABORT: 本遍现算的逐字句没出现在已落纸的 §38.27 里：' + str(bad)
assert P['E']['md5'] in sec, 'ABORT: E 臂 md5 未在 §38.27 在册'
for _frag in ('窗口 %.3f s' % P['E']['win'], '每 probe 秒数 = %.3f s' % P['E']['pp'],
              'probe# %d 次' % P['E']['probe'], 'AXP@0x34 行 %d 条' % P['E']['n34'],
              'uptime %d→%d ms' % (P['E']['up0'], P['E']['up1'])):
    assert _frag in FORE, 'ABORT: 取证载体在册的 E 臂那格与本遍现算不同形：' + _frag
for k in 'BCD':
    assert P[k]['md5'][:8] in FORE, 'ABORT: 取证载体在册的 %s 臂 md5 前缀与本遍现算不等' % k
for k in 'CD':
    assert ('%.3f s / probe %d 次' % (P[k]['win'], P[k]['probe'])) in FORE, 'ABORT: 对照臂 %s 在册窗口/probe 与本遍现算不同形' % k
    assert ('每 probe %.3f s' % P[k]['pp']) in FORE, 'ABORT: 对照臂 %s 在册每 probe 单价与本遍现算不等' % k
assert ('窗口 %.3f s' % P['B']['win']) in FORE and ('每 probe %.3f s' % P['B']['pp']) in FORE, \
    'ABORT: B 臂那两只负数在册值与本遍现算不同形 ⇒ §38.27 判废的正是这两个数，出处要现读'

assert P['B']['up0'] > P['B']['up1'] and P['B']['rom'] == 1, \
    'ABORT: B 臂负窗口的成因（首行 uptime %d > 末行 %d、banner=%d）与登记不符 ⇒ 判废句要重写' % (P['B']['up0'], P['B']['up1'], P['B']['rom'])
SAME = (P['E']['pwr'] == P['C']['pwr'] and P['E']['ack'] == P['C']['ack']
        and P['E']['acked'] == P['C']['acked'] and P['E']['bus'] == P['C']['bus'])
assert SAME, 'ABORT: E vs C 同形判据本遍现算为 False ⇒ §38.27 的"逐格相等"是假的'

# ---------------- ② 现场态模板句门 + 完成态指针 + §14.3 行号 ----------------
def stale_bad(lines):
    return [i + 1 for i, l in enumerate(lines) if STALE in l and not l.startswith('- **订正（')]

STALE_HITS = stale_bad(DL)
assert STALE_HITS == [3732, 3746], 'ABORT: 违规旧等式句现算位置 %s（应 [3732, 3746]）⇒ 订正对象要重认' % STALE_HITS
CORR = [i + 1 for i, l in enumerate(DL) if l.startswith('- **订正（') and STALE in l]
assert CORR == [3765, 3766], 'ABORT: 订正句现算位置 %s（应 [3765, 3766]）' % CORR
PC_GATE = stale_bad(DL[:H - 1] + ['- 假句：' + STALE] + DL[H:])
assert len(PC_GATE) == len(STALE_HITS) + 1, 'ABORT: 模板句门的内存阳性对照没被打红（门无执行者）'

PTR = [l for l in DL[H - 1:T] if l.startswith('> 本节对应')]
assert len(PTR) == 1, 'ABORT: §38.27 的"本节对应"行现算 %d 处' % len(PTR)
CARNAME = 'hardware/r57_paperwork1.txt'
assert CARNAME in PTR[0], 'ABORT: 在册指针句里没有指向本遍要产出的载体名 ⇒ 登记句要重写'
PTR_LINE_N = DL.index(PTR[0]) + 1

assert '14.3' in DL[379], 'ABORT: §14.3 标题行现算不在第 380 行（现读第 380 行 = %r）⇒ §38.27 那句引用是假的' % DL[379][:40]

FSEC = [i for i, l in enumerate(FL) if l.startswith('## 2026-09-25（R57 第一批')]
assert len(FSEC) == 1, 'ABORT: FreqErr R57 第一批那节现算 %d 处' % len(FSEC)
FS = FSEC[0] + 1
N_TOTAL = len([l for l in FL if l.startswith('[错误类型]')])
N_PRE = len([l for l in FL[:FS - 1] if l.startswith('[错误类型]')])
assert N_TOTAL == 209 and N_PRE == 205, 'ABORT: FreqErr 条数现算 总%d/节前%d（应 209/205）⇒ 本批正文条数要重认' % (N_TOTAL, N_PRE)
N_SEC = len([l for l in FL[FS:] if l.startswith('[错误类型]')])
assert N_SEC == 4, 'ABORT: R57 第一批正文条数现算 %d（应 4）' % N_SEC

# ---------------- ③ 两把聚合尺：同一目录同一刻各跑一遍，并回核两处在册值 ----------------
S0A, S0B = fold_a(SYNC), fold_b(SYNC)
_m1 = re.search(r'聚合 md5 ([0-9a-f]{32})', FORE)
_m2 = re.search(r'聚合 md5 `([0-9a-f]{32})`', sec)
assert _m1 and _m2, 'ABORT: 两处在册聚合 md5 读不到（取证载体/§38.27 现场态）⇒ 本遍那条"两把尺"句没有出处'
SEAL_IN_CAREER, SEAL_IN_DOC = _m1.group(1), _m2.group(1)
assert S0A[2] == SEAL_IN_CAREER and S0B[2] == SEAL_IN_DOC, \
    'ABORT: 归档聚合两把尺本遍不复现在册值（A %s/%s B %s/%s）⇒ 归档可能真被改过，立刻停' % (
        S0A[2][:8], SEAL_IN_CAREER[:8], S0B[2][:8], SEAL_IN_DOC[:8])
assert SEAL_IN_CAREER != SEAL_IN_DOC, 'ABORT: 两把尺同值 ⇒ "折法不同"那条登记是假的，本遍不写这一句'
PROBE_NAME = 'evidence/SEAL_VIOLATION_PROBE7.txt'
assert not os.path.exists(os.path.join(SYNC, PROBE_NAME)), 'ABORT: 内存阳性对照的名字在盘上存在 ⇒ 对照泄漏成文件'
PC_A = fold_a(SYNC, extra=PROBE_NAME)
PC_B = fold_b(SYNC, extra=PROBE_NAME)
assert PC_A[2] != S0A[2] and PC_B[2] != S0B[2], 'ABORT: SEAL 门对内存假名无反应 ⇒ 这道门没有执行者'

# ---------------- ④ 现场态现跑 ----------------
def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True,
                          env=dict(os.environ, PYTHONUTF8='1'))

_pp = run((sys.executable, '-m', 'serial.tools.list_ports'))
PORTS = sorted(set(re.findall(r'(?m)^(COM\d+)', _pp.stdout.decode('utf-8', 'replace'))))
COM14 = 'COM14' in PORTS
REV = run(('git', 'rev-list', '--count', 'origin/main..HEAD')).stdout.decode('utf-8', 'replace').strip()
ST = [l for l in run(('git', '-c', 'core.quotePath=false', 'status', '--porcelain')).stdout.decode('utf-8', 'replace').splitlines() if l.strip()]
MOD_N = len([l for l in ST if l[:2] == ' M'])
UN_N = len([l for l in ST if l[:2] == '??'])
assert REV.isdigit(), 'ABORT: rev-list 读数不是数字'

_vm = run((sys.executable, VMRUN))
VM_RC = _vm.returncode
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert VM_RC == 0 and _mc, 'ABORT: 内层复核器代落件本遍没跑绿（rc=%d）:\n%s\n%s' % (VM_RC, _vm_out[-400:], _vm.stderr.decode('utf-8', 'replace')[-400:])
VM_CARRIER = _mc.group(1)
_vm_txt = rd(os.path.join(REPO, VM_CARRIER.replace('/', os.sep)))
assert 'INNER_VERDICT=VERDICT=MANIFEST_STILL_TRUE' in _vm_txt, 'ABORT: 代落件里的内层裁决不是 MANIFEST_STILL_TRUE ⇒ 封界已漂，本批不许落纸'
_vm_v = [l for l in _vm_txt.split('\n') if l.startswith('INNER_VERDICT=')][0]
_vm_r = [l for l in _vm_txt.split('\n') if l.startswith('INNER_ROWS=')][0]

_before = set(os.listdir(HDIR))
_fl = run((sys.executable, FLASH))
FL_RC = _fl.returncode
_fl_err = _fl.stderr.decode('utf-8', 'replace')
_after = set(os.listdir(HDIR))
NEW_ONES = sorted(_after - _before)
assert FL_RC != 0, 'ABORT: 复跑取证器 rc=0 ⇒ 它写出了新载体 = 拒绝覆写门失效（本遍叙述整体作废，立刻停）'
assert not NEW_ONES, 'ABORT: 复跑取证器新增了 hardware/ 里的东西 %s ⇒ 那道门不只是拒绝覆写，还落了别的东西' % NEW_ONES
_ab = [l for l in _fl_err.splitlines() if 'ABORT:' in l]
assert _ab, 'ABORT: 复跑取证器 rc=%d 却打不出 ABORT 行 ⇒ 它崩在别的异常上，本遍不能把那次崩当对照' % FL_RC
FL_MSG = _ab[-1].split('ABORT:')[-1].strip()[:120]
FL_GATE = ('槽位门（判据摘录载体已存在）' if '判据摘录载体已存在' in FL_MSG
           else '身份门（本遍列口里没有 COM14）' if 'COM14' in FL_MSG else '')
assert FL_GATE, 'ABORT: 复跑取证器红在不认识的 ABORT 句（现 %r）⇒ 本遍不能把它当任何门的对照' % FL_MSG
SLOTS_ON_DISK = (os.path.exists(CAR_E), os.path.exists(CAR_E2))
assert all(SLOTS_ON_DISK), 'ABORT: 两只判据摘录槽位不齐 ⇒ 崩溃遍的 POSCTL 副产物与叙述不符'
_src = rd(FLASH).splitlines()
_g = [i + 1 for i, l in enumerate(_src) if '不许覆写取证原件' in l]
assert len(_g) == 1, 'ABORT: 槽位门那行在取证器源码里现算 %d 处 ⇒ 它被改写或被复制，本遍不能引用它' % len(_g)
SLOT_GATE_LINE, SLOT_GATE_SRC = _g[0], _src[_g[0] - 1].strip()

# ---------------- ⑤ 构造追加正文（崩溃时刻、在册引文一律运行时现读） ----------------
_crash_at = re.search(r'订正（§38.25 第 3732 行③句｜([\d\- :]+)', DL[3764])
assert _crash_at, 'ABORT: 订正句里的落纸时刻读不到 ⇒ 崩溃遍时刻没有出处'
CRASH_AT = _crash_at.group(1)
_cap = re.search(r'原件 mtime ([\d\-]+ [:\d]+)', FORE)
assert _cap, 'ABORT: 取证载体里没有 E 臂原件 mtime ⇒ 深睡时长那格没有出处'
CAP_AT = datetime.strptime(_cap.group(1), '%Y-%m-%d %H:%M:%S')
SINCE_CAPTURE = int((datetime.now() - CAP_AT).total_seconds())
_vm2 = [f for f in os.listdir(HDIR) if f.startswith('vm_run_') and CRASH_AT[:10].replace('-', '') in f]
CRASH_VM = sorted(_vm2)[-1] if _vm2 else '(崩溃遍的代落件按日期现算为 0 只)'

DOC_ADD = (
    '- **登记（§38.27 落纸遍崩在写载体之前｜' + RUN_AT + ' 补落遍现跑）**：'
    '§38.27 那 ' + str(SEC_LINES) + ' 行（第 ' + str(H) + '~' + str(T) + ' 行，含两条订正句）落在 **' + CRASH_AT + '** 那一遍，'
    '而那一遍**崩在 paperwork 载体写盘之前**（rc=1，`NameError: name \'ROWS\' is not defined` —— 台账性质的 GATE 行在自己的列表字面量里引用了尚未绑定的 `ROWS`），'
    '于是第 ' + str(PTR_LINE_N) + ' 行逐字写着「' + PTR[0][:56] + '…」的那只载体 `hardware/r57_paperwork1.txt`，在**写下它那一句的那一遍并不存在** —— '
    '这是"预写完成态"在文档侧的同族，本行是它的收尾订正：**那只载体由补落遍（本遍，' + RUN_AT + '）写出**；'
    '本遍把已落纸的四臂数重新解析并逐字回核（窗口 ' + ', '.join('%.3f' % P[k]['win'] for k in 'BCDE') +
    ' s、每 probe ' + ', '.join('%.3f' % P[k]['pp'] for k in 'BCDE') + ' s，全部现算 == 在册，见载体 `REPARSE` 行），不回写它一字节；'
    '崩溃遍那一遍的 FIELD/VM/POSCTL/SEAL 读数**一律不作数**，本遍自己现跑（代落件 = `hardware/' + CRASH_VM + '` 属那一遍，本遍新落一只，名字见载体 `VM` 行）。'
    '现场态另有换代一处（本遍现量，不复用上一遍的话）：本遍列口 = ' + ', '.join(PORTS) + ' ⇒ **COM14 又缺席**（距 E 臂抓取 ' + str(SINCE_CAPTURE) +
    ' s，与项目记忆"深睡 900 s 无按键则原生 USB 从总线消失"那条口径同向，但本遍没有仪器证据把它定成深睡）；'
    '§38.27 那句"COM14 在位 = True"量的仍是 12:53 那一遍，本遍既不推翻也不复用。连带一处对照失效：复跑 `hardware/r57_flash1.py` 因身份门排在槽位门之前而红在列口那一句'
    '（rc=' + str(FL_RC) + '，' + FL_MSG + '），所以本遍**不能**拿它当"拒绝覆写"门的阳性对照，槽位用尽改由盘上两只载体 + 该工具源码第 ' + str(SLOT_GATE_LINE) +
    ' 行逐字现读证明（载体 `POSCTL` 行把它登记成静态证明，不冒充跑出来的红）。'
    '另点名一处两把尺：E 臂取证载体在册的归档聚合 md5 `' + SEAL_IN_CAREER[:8] + '…` 与 §38.27 现场态那格 `' + SEAL_IN_DOC[:8] + '…` **不是同一把尺** —— '
    '两处同名函数 `scan_dir` 折法不同（walk 序只折 content 摘要 vs 把 文件名:摘要 排序后用竖线连接再折），'
    '本遍对同一目录同一刻把两把尺各跑一遍 = `' + S0A[2][:8] + '…` / `' + S0B[2][:8] + '…`，**各自逐字复现在册值**，'
    '而只数与字节两把尺同为 ' + str(S0A[0]) + ' 只 / ' + money(S0A[1]) + ' B ⇒ 两格都对，缺的是"引用摘要时把折法定义一起写上"（载体 `SEAL` 行按 FOLD-A/FOLD-B 分别登记）。'
)

DOC_NEW = DOC_T + '\r\n' + DOC_ADD + '\r\n'

F0 = [
    '',
    '## 2026-09-25（R57 第二批：崩在写载体之前的那一遍把正文落了 + 同名聚合摘要两把尺）新增 4 条（根族：**"我写过" 与 "我跑过" 不是同一件事**）',
    '',
    '> 一句话总纲：本批屏侧一个字节没动（没烧录、没碰串口，本遍只 `comports()` 只读列口 = ' + ', '.join(PORTS) + '），'
    '抓到的四条全在落地器自己身上：那一遍崩在哪一行、它崩之前已经改了哪两个文件、它留下的两处在册句各自量的是什么。',
    '',
    '[错误类型] **落地器把"汇总自己行数"的那一行写进它自己的列表字面量 ⇒ `NameError` 崩在两次正文写盘之后 = 正文已落、paperwork 载体未落**（本批实测：崩点那遍留下排查记录第 '
    + str(H) + '~' + str(T) + ' 行与 FreqErr R57 第一批那 ' + str(N_SEC) + ' 条，却一只载体也没落；`hardware/r57_paperwork1.txt` 直到补落遍才存在）',
    '→ 症状：脚本在构造行列表的那一句里引用了尚未绑定的自身名字（`ROWS`），Python 在求值该字面量时当场抛 `NameError`；'
    '同一遍此前还有一次同族崩溃（台账行引用 `F` 自身），两个样本都是"自指统计进了自己的容器字面量"。崩点位置在所有 ABORT 之后、`open(CARRIER)` 之前 ⇒ 改盘的动作已经做完。',
    '→ 为什么它危险：盘上留下一段**没有载体配套的正文**：正文里每句"本遍现算"的证据文件不存在，下一个读它的人（包括我）只能重跑落地器才能核，'
    '而重跑要用的取证器槽位已被那一遍的 POSCTL 消耗掉（见本批第 4 条）。它比"没跑"更险的一半是**它看起来已经跑完**（正文里带着完成态时刻 ' + CRASH_AT + '）。',
    '→ 正确做法：①自指统计一律**后置**：先把行 append 完，再对最终列表求值（补落遍把 `TOTAL_ROWS` 行排在所有行之后，表达式里的长度求值发生在追加之后）；'
    '②落地器写盘顺序固定为「入口前置检查 → 所有能失败的独立复跑（vm_run / SEAL / FIELD / POSCTL）→ 写正文 → 写载体」，'
    '凡能失败的断言不许排在第一次正文写盘之后；本批把这一条写成了构造规矩而不是事后修补；'
    '③"崩在写盘之后"必须有**补落遍**这个执行者：它进正文前先核已落纸内容（本遍的 `REPARSE`/`QUOTE`/`BOARDGATE` 三行就是它），不许回写、不许洗绿；'
    '④补落遍必须明写"崩溃遍的同类读数不作数"并自己现跑（本遍载体 `VM`/`POSCTL` 行的时刻晚于 `CRASH` 行点名的那一只代落件）。',
    '→ **同族**：项目记忆 (59)"崩溃那次的读数不作数"、(71)"改了脚本 ≠ 跑了脚本"、(74)"登记已跑完/已冻结前先跑一次并抄 rc"、(95)落地三步序、§38.21 ①（"只在下一批才执行"那一族）、本批第 2 条。',
    '',
    '[错误类型] **正文里点名"本遍写的那一只载体"，而崩溃让那只载体没被写 ⇒ 在册指针指向不存在的文件（"预写完成态"的文档侧同族，且这次连 grep 都得到句子、只是打不开文件）**'
    '（本批实测：§38.27 第 ' + str(PTR_LINE_N) + ' 行逐字含 `hardware/r57_paperwork1.txt`，补落遍进入时该路径 `os.path.exists` = False）',
    '→ 症状：按那句去开文件 → 没有；按它列举的行名（REPARSE / B-ARM / BOARDGATE / QUOTE / DENOM / PLAIN / SEAL / GATE / VM / POSCTL / WITNESS / FIELD）去 grep → 一只都对不上；'
    '而那句自己的措辞是完成态（"本遍写的那一只"），没有任何一处写着"待落"。',
    '→ 为什么它危险：文档侧的指针是"引用即复跑"的入口，入口指向空 = 整节读数变成不可核；'
    '比"没写载体"更严重的是它**留下了一个看起来可核的假象**，于是查案的人会先怀疑载体被人删了（本批零删除，删的是不存在的东西）。',
    '→ 正确做法：①凡**完成态措辞**的产物指针，写下它的那一刻产物必须已在盘上；同一遍稍后才产出的，措辞必须显式写"待本遍落盘后由 `…` 登记"并配补落遍；'
    '②落地器入口把"本遍即将产出的路径"断言为空槽（本遍第 1 道门），并在登记句里点名"那一遍是否真的产出过"；'
    '③已在册那行**不回写**，只以追加的登记句收尾（它落在排查记录第 ' + str(N_DOC0 + 2) + ' 行，本遍写，行数由本遍现读）。',
    '→ **同族**：项目记忆 (85)"提交信息不许有将来式锚点"、(71)、(74)、(59)、本批第 1 条、R56 那族"凭证写的时刻 ≠ 它标的那一刻"（三型）。',
    '',
    '[错误类型] **两个工具里同名函数 `scan_dir` 用两种折法 ⇒ 同一目录同一刻两只都"合法"的聚合摘要，跨引用时读成"归档被人改过"**'
    '（本批实测：取证载体在册 `' + SEAL_IN_CAREER[:8] + '…`、§38.27 现场态在册 `' + SEAL_IN_DOC[:8] + '…`；补落遍同一刻把两把尺各跑一遍，各自逐字复现各自那格）',
    '→ 症状：函数名、变量名、输出行的文字（`聚合 md5 `）全同，只有折叠输入不同 —— FOLD-A 按 walk 序只喂 content 摘要的 hex，FOLD-B 把 `文件名:摘要` 排序后用竖线连接再喂一次 md5。'
    '同一目录两把尺的只数与总字节一致，摘要必然不同。',
    '→ 为什么它危险：归档封界（gen 24 之后零字节）就是靠聚合摘要自证的；一旦出现两个不同值，下一个查案的人会先怀疑**归档被改**，'
    '而真相只是引用没带定义 —— 这一族的代价是"把一次正确的复算读成一次事故"，比反过来更费时间。',
    '→ 正确做法：①登记聚合摘要必须把**折法定义**（是否含文件名、是否排序、用什么分隔、是否含字节数）与数值一起写；'
    '②跨工具比对前先逐字比两把尺的定义，定义不同就分别命名（本遍载体 `SEAL` 行按 FOLD-A/FOLD-B 各记两格，并各自回核一处在册值）；'
    '③把"两把尺在同刻各自复现在册值"当作**正向证据**登记，而不是当作矛盾删掉其中一格。',
    '→ **同族**：项目记忆 (47)"同一个东西常有第二把尺子，改数之前先把所有尺子各跑一遍"、(73)口径越界、(87)"摘要类读数必须点名哪个哈希函数 + 是否截断"、§38.25/§38.26 那族"同一行两把尺"。',
    '',
    '[错误类型] **把"引用即复跑"当成永久能力，而取证器既吃一次性槽位、又吃现场硬件 ⇒ 在册那句"本节每个数都能由它现算"这一遍根本跑不到那道门**'
    '（本批实测：复跑 `hardware/r57_flash1.py` ⇒ rc=' + str(FL_RC) + '，红在**身份门**那一句 = ' + FL_MSG + '，`hardware/` 目录名集合新增 ' + str(len(NEW_ONES)) + ' 只）',
    '→ 症状：本遍列口 = ' + ', '.join(PORTS) + '，**COM14 缺席**（§38.27 那句"COM14 在位 = True"量的是 12:53 那一遍，与 R53~R56 那些"缺席"句同族：各自那一遍）；'
    '取证器把"列口里有 COM14"排在槽位门之前，于是板一掉线，连"确认拒绝覆写门还在、槽位已用尽"这件事都跑不出来 —— '
    '而它俩明明一个只读盘、一个只读现场。槽位用尽本遍改由**盘上现读**证明：两只判据摘录都在（原件 + `_v2`），且源码第 ' + str(SLOT_GATE_LINE) + ' 行逐字 = `' + SLOT_GATE_SRC[:70] + '…`。',
    '→ 为什么它危险："引用即复跑"是给抄来的数设的唯一防，它的可信度取决于**复跑是否在任意时刻可达**；把复跑挂在现场硬件上 ⇒ 复跑能力随插拔涨落，'
    '查案的人会把"跑不动"误读成"数有问题"，或反过来把某一次跑得动当成永久跑得动。同一族的另一半是槽位池：崩溃遍已把第二格占掉，'
    '所以这道门从此每次复跑必红，而这句话本身若不落纸，下一遍会重新踩一次。',
    '→ 正确做法：①取证器内部的门要按**代价与依赖**排序：只读盘的门（槽位、载体形状）排在依赖现场状态的门（列口、串口）之前，让"拒绝覆写"这类纪律在任何现场都能自证；'
    '②"引用即复跑"要指名**仍在槽位内、且不依赖现场**的执行件，已耗尽的登记成"只读凭证"（只能引用它落的载体，不许承诺复跑）；'
    '③对照样本可以是**盘上现读 + 源码逐字**这种静态形状，不许因为没有跑出红就把门当成没自证过（本遍 `POSCTL` 行分别登记"跑出来的红"与"静态证明的槽位"）；'
    '④COM14 的在位/缺席每遍现量各记各的，不许把上一遍的"回归"当成 permanent 状态。',
    '→ **同族**：项目记忆 (59)"崩溃那次的读数不作数"、(64)"记录取证那步自己没落盘"、(47)"同一个东西常有第二把尺子"、`hardware/vm_run.py` 头部注释（复核器槽位用尽后的第二把尺）、'
    '项目记忆"串口消失≠没插线"（深睡 900 s 无按键 ⇒ 原生 USB 从总线消失；本遍距 E 臂抓取那刻（取证载体在册原件 mtime ' + _cap.group(1) + '）已 ' + str(SINCE_CAPTURE) + ' s，与该口径同向）、§38.21 ①。',
]

FREQ_BODY = '\r\n'.join(F0) + '\r\n'
LEDGER = ('> **【' + RUN_AT + ' 落地｜R57 第二批 4 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'
          '全文 `^[错误类型]` 条数 = **' + str(N_TOTAL) + '**、行数 = **' + str(N_FREQ0) + '**、字节 = **' + money(B_FREQ0) + '**；'
          '本批正文（不含本台账行自己，含上方那只 glue 空行）= **4** 条 / **' + str(len(F0) + 1) + '** 行 / **' + money(len(FREQ_BODY.encode('utf-8'))) + '** B，'
          '本台账行排在正文之后第 1 行 ⇒ 判"追加了多少"以 **正文** 那组数为准；'
          '**落盘后的终态三格由载体 `LAND` 行现数**（完成态数字不许在本行里预写，见项目记忆"完成态数字必须在载体落盘后现数"）。'
          '同遍排查记录 改前 **' + str(N_DOC0) + '** 行 / **' + money(B_DOC0) + '** B -> 本批追加 1 只 glue 空行 + **1** 行登记句 = **'
          + str(N_DOC0 + 2) + '** 行 / **' + money(len(DOC_NEW.encode('utf-8'))) + '** B（真追加 2 行，纯追加、前缀等式成立、纯 CRLF；'
          '本遍是补落遍，两处已落纸正文一字节未回写）。')

# 三道正文门：反斜杠 / 明文 / 未替换哨兵
for _nm, _blk in (('DOC', DOC_ADD), ('FREQ', '\n'.join(F0 + [LEDGER]))):
    assert '\\' not in _blk, 'ABORT: ' + _nm + ' 正文含反斜杠（落盘正文禁，见 §38.18 那一族）'
    assert SECRET.decode('utf-8', 'replace') not in _blk, 'ABORT: ' + _nm + ' 正文含 PROV_PASS 明文'
    for _s in ('%s', '%d', '@@', 'BUIL', 'None'):
        assert _s not in _blk, 'ABORT: ' + _nm + ' 正文含未替换哨兵 ' + _s

# ---------------- ⑥ 写盘（只纯追加） ----------------
FREQ_NEW = FREQ_T + '\r\n' + FREQ_BODY + LEDGER + '\r\n'
assert DOC_NEW.startswith(DOC_T) and FREQ_NEW.startswith(FREQ_T), 'ABORT: 前缀等式不成立 ⇒ 不是纯追加'
open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)

# ---------------- ⑦ 写盘后独立回读复核（失败即点名，不静默） ----------------
_dt = rd(DOC)
_ft = rd(FREQ)
assert _dt == DOC_NEW, 'ABORT: 排查记录回读不等于写入串'
assert _ft == FREQ_NEW, 'ABORT: FreqErr 回读不等于写入串'
_dtl = _dt.split('\r\n')
_ftl = _ft.split('\r\n')
assert stale_bad(_dtl) == STALE_HITS, 'ABORT: 写盘后违规旧等式句位置变了（现 %s）⇒ 新追加的行不带订正前缀却复抄了旧句' % stale_bad(_dtl)
assert len([l for l in _ftl if l.startswith('[错误类型]')]) == N_TOTAL + 4, 'ABORT: 写盘后 FreqErr 条数不等于 在册 + 4'
S1A, S1B = fold_a(SYNC), fold_b(SYNC)
assert S1A == S0A and S1B == S0B, 'ABORT: 归档目录被本遍改动（' + str(S0A) + ' -> ' + str(S1A) + '）⇒ gen 24 末版被亲手降级'
DOC_LINES, DOC_BYTES = _dt.count('\n'), len(_dt.encode('utf-8'))
FREQ_LINES, FREQ_BYTES = _ft.count('\n'), len(_ft.encode('utf-8'))
FREQ_HITS = len([l for l in _ftl if l.startswith('[错误类型]')])
DOC_MD5 = hashlib.md5(_dt.encode('utf-8')).hexdigest()
FREQ_MD5 = hashlib.md5(_ft.encode('utf-8')).hexdigest()

# ---------------- ⑧ 载体 ----------------
ROWS = []
ROWS.append('R57 补落遍（崩溃遍的下一遍）  MODE=FIX-PASS-CARRIER-FIRST-WRITE')
ROWS.append('本遍现跑于 ' + RUN_AT + '；载体由脚本自己在同一次运行里落盘，落在 hardware/（ht305_sync 之外）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('REPARSE 四臂同遍现算（B/C/D/E 逐臂 窗口s / 每probe s / probe数 / 0x34行 / 应答）= '
            + ' | '.join('%s %.3f/%.3f/%d/%d/%d' % (k, P[k]['win'], P[k]['pp'], P[k]['probe'], P[k]['n34'], P[k]['replies']) for k in 'BCDE')
            + '；本遍现算的每个数逐字出现在已落纸的 §38.27 第 ' + str(H) + '~' + str(T) + ' 行里 = '
            + str(all(c[3] for c in CHECKS)) + '（比对 ' + str(len(CHECKS)) + ' 格，全过）')
ROWS.append('REPARSE md5 回核（盘上现算 vs §38.27 在册）= ' + ' / '.join('%s %s' % (k, P[k]['md5']) for k in 'BCDE')
            + '；与取证载体在册的 E 臂窗口/每probe 两格逐字相等 = True（口径出处：载体第 ' + str(H) + '~' + str(T) + ' 行区间）')
ROWS.append('B-ARM 负窗口成因本遍现算：首行 uptime ' + str(P['B']['up0']) + ' ms > 末行 ' + str(P['B']['up1'])
            + ' ms，ROM banner ' + str(P['B']['rom']) + ' 次 ⇒ 复位起抓那份日志的第一行是上次开机被剪断的半行；'
            '两格派生数（窗口 %.3f s / 每 probe %.3f s）本遍判废，与 §38.27 的判废句同形；切段后可用读数只剩 banner=%d / 0x34 行 %d 条 / 应答 %d 条' % (
                P['B']['win'], P['B']['pp'], P['B']['rom'], P['B']['n34'], P['B']['replies']))
ROWS.append('SAME_SHAPE E vs C 逐格（PWR %s / ACK %s / acked %s / 全总线扫 %s）相等 = %s；两臂 boot 指纹 %s / %s' % (
    P['E']['pwr'], P['E']['ack'], P['E']['acked'], P['E']['bus'], SAME, P['E']['elf'][0], P['C']['elf'][0]))
ROWS.append('BOARDGATE 现场态模板句门（判据 = 含「' + STALE + '」且该行不以订正前缀开头）：'
            '写盘前违规 %s / 订正句 %s / 写盘后违规 %s（应等）；内存阳性对照 = 在 §38.27 之前插一条假句 ⇒ 命中数 +1 = True ⇒ 这道门有执行者' % (
                STALE_HITS, CORR, stale_bad(_dtl)))
ROWS.append('QUOTE 三行运行时现读（长度 = 字符数 / md5 = 该行逐字）：'
            + ' | '.join('第%d行 %d chars md5 %s' % (n, len(DL[n - 1]), hashlib.md5(DL[n - 1].encode('utf-8')).hexdigest()[:12])
                         for n in (3732, 3746, PTR_LINE_N)))
ROWS.append('CRASH 崩溃遍证据（本遍现读目录，不转抄）：判据摘录原件 = %d B / 其 v2 = %d B（两者 md5 见 WITNESS 行）/ 崩溃遍代落件 = hardware/%s；'
            'paperwork 载体在本遍进入前存在 = False ⇒ 第 %d 行那句完成态指针当时指向空文件，由本遍补齐' % (
                os.path.getsize(CAR_E), os.path.getsize(CAR_E2), CRASH_VM, PTR_LINE_N))
ROWS.append('DENOM 屏侧分母本遍现算：hardware/ 单层 *.log = %d 只 / 其中"官方例程"对照 %d 只不进分母 / 我方 = %d 只（与 §38.27 在册同值 = %s）' % (
    len([f for f in os.listdir(HDIR) if f.endswith('.log')]),
    len([f for f in os.listdir(HDIR) if f.endswith('.log') and '官方例程' in f]),
    len([f for f in os.listdir(HDIR) if f.endswith('.log') and '官方例程' not in f]),
    str(len([f for f in os.listdir(HDIR) if f.endswith('.log') and '官方例程' not in f]) == 10)))
_PLAIN = {k: open(v, 'rb').read().count(SECRET) for k, v in LOGS.items()}
ROWS.append('PLAIN 明文半径（口令只从 provision_ap.c 的宏体读出做计数，不打印、不进本载体正文）：'
            + ' / '.join('%s臂 %d 处' % (k, _PLAIN[k]) for k in 'BCDE')
            + ' ⇒ 每轮提交逐只点名 DROP 这几只日志，绝不 stage、绝不 push')
ROWS.append('FIELD 现跑（%s）：串口枚举 = %s ⇒ COM14 在位 = %s（这是本遍那一遍：§38.27 在册的"COM14 在位 = True"量的是 12:53 那一遍，本遍既不推翻也不复用）/ '
            'git rev-list origin/main..HEAD = %s（未 push）/ git status --porcelain = %d 行（%d 只 M + %d 只 ??）/ 距 E 臂抓取 %d s' % (
                RUN_AT, ', '.join(PORTS), COM14, REV, len(ST), MOD_N, UN_N, SINCE_CAPTURE))
ROWS.append('LAND 写盘后独立回读现数（完成态数字在此处数，不在台账行里预写）：'
            '排查记录 = %d 行 / %s B / md5 %s；FreqErr = %d 行 / %s B / md5 %s / 全文 [错误类型] 条数 = %d（= 在册 %d + 本批 4）；'
            '两文件前缀等式（纯追加）= True / 行尾纯 CRLF 写后仍成立 = %s / 本批正文之外零改写' % (
                DOC_LINES, money(DOC_BYTES), DOC_MD5, FREQ_LINES, money(FREQ_BYTES), FREQ_MD5, FREQ_HITS, N_TOTAL,
                str(_dt.count('\n') == _dt.count('\r\n') and _ft.count('\n') == _ft.count('\r\n'))))
ROWS.append('SEAL 归档封界两把尺（同一目录同一刻各跑一遍，写盘前后互核）：'
            'FOLD-A（walk 序只折 content 摘要，与 hardware/r57_flash1.py 同折法）= %d 只 / %s B / %s（逐字复现在册取证载体那格 = %s）；'
            'FOLD-B（文件名:摘要 排序后以竖线连接再折，与崩溃遍落地器同折法）= %d 只 / %s B / %s（逐字复现 §38.27 现场态那格 = %s）；'
            '两把尺的只数与字节互核 = %s；写盘前后 FOLD-A/FOLD-B 全等 = %s ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版' % (
                S0A[0], money(S0A[1]), S0A[2], str(S0A[2] == SEAL_IN_CAREER),
                S0B[0], money(S0B[1]), S0B[2], str(S0B[2] == SEAL_IN_DOC),
                str(S0A[0] == S0B[0] and S0A[1] == S0B[1]), str(S1A == S0A and S1B == S0B)))
assert S0A[0] == S0B[0] and S0A[1] == S0B[1], 'ABORT: 两把尺的只数/字节都不等 ⇒ 有一把漏扫，聚合值不可比'
ROWS.append('GATE 本遍各道门命中数：槽位空槽 0 / 缺件 0 / 行尾纯 CRLF 0 破 / 前缀等式 0 破 / 反斜杠 0 / 明文 0 / 未替换哨兵 0 / '
            '模板句门违规 %d（= 在册订正对象，非本批新增）/ 回读等值 0 破 / SEAL 0 破 ⇒ ARMS_FIRED（真红计数）：内存假句 1 + 内存假名 2（FOLD-A/FOLD-B 各 1）'
            '+ 复跑取证器 1（红在%s）= 4 次；另槽位门本遍为静态证明，不计入真红' % (len(STALE_HITS), FL_GATE))
ROWS.append('VM 内层复核器代落：hardware/vm_run.py 本遍 rc=%d / %s / %s / 代落件 = %s（本遍新产，位于归档目录之外 ⇒ 不动 gen 24 封界）' % (
    VM_RC, _vm_r, _vm_v, VM_CARRIER))
ROWS.append('POSCTL 四类对照：①复跑取证器 = 跑出来的红：rc=%d，红在%s（逐字 ABORT = %s），hardware/ 名集合新增 %d 只 ⇒ 它没落任何新东西；'
            '②拒绝覆写槽位门 = 静态证明（本遍没跑到它，因为它排在身份门之后）：源码第 %s 行逐字 + 盘上两只槽位 %s ⇒ 用尽为真；'
            '③模板句门 = 内存假句命中数 +1；④SEAL 门 = 内存假名 %s 使 FOLD-A/FOLD-B 双红（对照全程只在内存，盘上没有那只文件 = %s）' % (
                FL_RC, FL_GATE, FL_MSG, len(NEW_ONES), str(SLOT_GATE_LINE), str(SLOTS_ON_DISK), PROBE_NAME,
                str(not os.path.exists(os.path.join(SYNC, PROBE_NAME)))))
ROWS.append('WITNESS 关键件本遍现读 md5：取证载体 %s / 其 v2 %s / 落地器 %s / 本工具 %s / E 臂日志 %s' % (
    hashlib.md5(open(CAR_E, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(CAR_E2, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(LANDER, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(__file__, 'rb').read()).hexdigest()[:12],
    hashlib.md5(open(LOGS['E'], 'rb').read()).hexdigest()[:12]))
ROWS.append('NOTDONE 本批没做（点名）：没换电池 / 没万用表 / 没第二块板（§38.23 那两条物理分叉仍在用户侧）/ 没改 main/ 源码、没重建固件（板上那只就是 fb32168a…）/ '
            '没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / 没 push、没 amend / 零删除（含 %TEMP% 那只 E 臂原件与崩溃遍两只副产物）/ '
            '屏亮肉眼确认仍 0 次 ⇒ 不播提示音 / 崩溃遍落的两处正文一字未回写 / docs 快照第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数')
_i = next(k for k, l in enumerate(ROWS) if l.startswith('GATE '))
ROWS.insert(_i + 1, 'GATE-COUNT 本载体行数（本行由所有行追加完之后才求值，避开崩溃遍那个自指缺陷）= %d 行（含本行）' % (len(ROWS) + 1))
TXT = '\n'.join(ROWS) + '\n'
assert '\\' not in TXT.replace('\\n', ''), 'ABORT: 载体正文含反斜杠'
assert SECRET.decode('utf-8', 'replace') not in TXT, 'ABORT: 载体含明文'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(TXT)
_rb = open(CARRIER, 'rb').read()
assert _rb.decode('utf-8') == TXT, 'ABORT: 载体回读不等于写入串'
assert _rb.count(b'\r') == 0, 'ABORT: 载体不是纯 LF'
ROWS_N = TXT.rstrip('\n').count('\n') + 1

print('CARRIER=%s  ROWS=%d  BYTES=%d' % (os.path.basename(CARRIER), ROWS_N, len(_rb)))
print('DOC %d 行 / %s B / FREQ %d 行 / %s B / 条数 %d -> %d' % (DOC_LINES, money(DOC_BYTES), FREQ_LINES, money(FREQ_BYTES), N_TOTAL, FREQ_HITS))
print('SEAL FOLD-A %s / FOLD-B %s / 复现在册 = %s' % (S0A[2][:8], S0B[2][:8], str(S0A[2] == SEAL_IN_CAREER and S0B[2] == SEAL_IN_DOC)))
print('VERDICT=' + ('R57-PAPERWORK-CARRIER-LANDED-BY-FIX-PASS' if ROWS_N >= 18 else 'R57-ROWS-SHORT'))
