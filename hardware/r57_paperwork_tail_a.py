# R57 收口批 part A = 排查记录 §38.28 + FreqErr 第四批 2 条。
# 派生自 hardware/r57_paperwork1_fix2.py（订正遍），门全继承（空槽 / 前缀等式 / 纯 CRLF / 反斜杠 / 明文 / 哨兵 / 回读等值 / SEAL 两把尺 + 内存假名 / GATE-COUNT 后置 / 完成态数字在 LAND 行现数）。
# 本遍另装两道新执行者，就是本批 FreqErr 那两条的兑现：①开头对**自身源码**跑 ast.parse（那条 `%-格式串收尾再接字面量行` 的语法错，真凶离报错点几百行）；
#   ②同一份字节用两种解码各读一遍、md5 不变而字符数变 ⇒ 证明"控制台乱码"与"文件损坏"是两把尺（本遍现场复跑，不转抄上一遍的话）。
# 口径：崩溃遍 / 补落遍 / 订正遍三只载体一字节不回写，只追加；docs 快照第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数。
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
CAR_E = os.path.join(HDIR, '20260925_R57_E臂判据摘录.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
PWCAR = os.path.join(HDIR, 'r57_paperwork1.txt')
FIXCAR = os.path.join(HDIR, 'r57_paperwork1_fix2.txt')
FIXER = os.path.join(HDIR, 'r57_paperwork1_fix2.py')
LOG_E = os.path.join(HDIR, '20260925_R57_E臂新镜像锂电池在位复位起抓120s.log')
SRC_MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
VMRUN = os.path.join(HDIR, 'vm_run.py')
TOOL = os.path.join(HDIR, 'r57_paperwork_tail_a.py')
CARRIER = os.path.join(HDIR, 'r57_paperwork_tail_a.txt')
SEAL_REF = 'efda29538483bbc73e91941936512a2f'
PROBE = 'evidence/SEAL_VIOLATION_PROBE9.txt'

RUN_AT = datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S')


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def mtime(p):
    return datetime.fromtimestamp(os.path.getmtime(p))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def run(args):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ---- 门 1：自身源码先过 ast.parse（本批 FreqErr 第一条的执行者；写盘之前，不通过就不落任何字节）
self_src = rd(TOOL)
ast.parse(self_src)
assert "' + str(len(OTHER)) + '" in rd(FIXER), 'ABORT: 订正遍工具里那句 + str(len(OTHER)) + 不在，本批第一条的锚就断了'

# ---- 门 2：槽位 —— 本遍载体必须是空槽；§38.28 与"第四批"标题都必须还没出现
assert not os.path.exists(CARRIER), 'ABORT: 本遍载体槽位非空，不覆写'
DOC_T = rd(DOC)
FREQ_T = rd(FREQ)
assert '### 38.28' not in DOC_T, 'ABORT: §38.28 已在册，本遍不覆写已有节'
assert 'R57 第四批' not in FREQ_T, 'ABORT: FreqErr 的 R57 第四批标题已在册（注意：光数"第四批"三个字不成立，那三个字在册已 11 处）'
DOC_L = DOC_T.split('\r\n')
FREQ_L = FREQ_T.split('\r\n')

# ---- 门 3：被引用的件必须都在，且上一遍的三只载体本遍没写过
for _p in (CAR_E, CAR_E2, PWCAR, FIXCAR, FIXER, LOG_E, SRC_MACRO, VMRUN):
    assert os.path.isfile(_p), 'ABORT: 缺件 ' + _p
for _p in (CAR_E2, PWCAR, FIXCAR, LOG_E):
    assert os.path.getmtime(_p) < _T0, 'ABORT: 上一遍那只 ' + os.path.basename(_p) + ' 的 mtime 不早于本遍进入时刻'
assert DOC_T.endswith('\r\n') and FREQ_T.endswith('\r\n'), 'ABORT: 两文件不以外层行尾收尾，追加会劈行'

# ---- 现读：三遍时刻
SEC27 = [i for i, l in enumerate(DOC_L) if l.startswith('### 38.27')]
assert len(SEC27) == 1, 'ABORT: §38.27 标题现读 %d 只，不是 1' % len(SEC27)
_m = re.search(r'paperwork ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})', DOC_L[SEC27[0]])
assert _m, 'ABORT: §38.27 标题里没有 paperwork 那个时刻'
CRASH_AT = _m.group(1)
PW_TXT = rd(PWCAR)
FIX_TXT = rd(FIXCAR).split('\n')
_m = re.search(r'本遍现跑于 ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})', PW_TXT)
assert _m, 'ABORT: 补落遍载体读不到现跑时刻'
FIX1_AT = _m.group(1)
_m = re.search(r'本遍现跑于 ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})', FIX_TXT[1])
assert _m, 'ABORT: 订正遍载体第 2 行没有现跑时刻'
FIX2_AT = _m.group(1)
assert CRASH_AT < FIX1_AT < FIX2_AT < RUN_AT, 'ABORT: 三遍时刻不成序'
assert FIX1_AT in DOC_T and FIX2_AT in DOC_T, 'ABORT: 后两遍的时刻在排查记录里 grep 不到（说明那两遍没落纸）'

# ---- 现读：归属那一格（在册错句 + 真值），并现场复跑"只差一行"
_m = re.search(r'CRASH 崩溃遍证据.*?代落件 = (hardware/vm_run_[0-9]+_[0-9]+)\.txt', PW_TXT, re.S)
assert _m, 'ABORT: 补落遍载体的 CRASH 行读不到被错指那只'
CLAIMED = _m.group(1)
_m = re.search(r'真值[^=]*= (hardware/vm_run_[0-9]+_[0-9]+)\.txt', rd(FIXCAR))
assert _m, 'ABORT: 订正遍载体的 TRUTH 行读不到真值那只'
REAL = _m.group(1)
assert CLAIMED != REAL, 'ABORT: 被错指那只与真值那只同名，归属订正没发生'
SAID = rd(os.path.join(HDIR, CLAIMED.split('/')[-1] + '.txt')).split('\n')
TRUE_ = rd(os.path.join(HDIR, REAL.split('/')[-1] + '.txt')).split('\n')
assert len(SAID) == len(TRUE_) == 22, 'ABORT: 两只代落件行数不是 22，"同形"这句不能沿用'
DIFF_ROWS = [i + 1 for i in range(len(SAID)) if SAID[i] != TRUE_[i]]
assert DIFF_ROWS == [2] and SAID[1].startswith('RUN_AT=') and TRUE_[1].startswith('RUN_AT='), \
    'ABORT: 逐行差异不是第 2 行 RUN_AT ⇒ "只订正归属不动数值"本遍复算不成立'

# ---- 现读：E 臂取证载体的每一格（按整行前缀取，不按"首 token 建字典"——那只载体有四行都以 E 开头，建字典会互相吃掉）
ELINES = [l for l in rd(CAR_E2).split('\n') if l]


def erow(prefix):
    hits = [l for l in ELINES if l.startswith(prefix)]
    assert len(hits) == 1, 'ABORT: E 臂载体前缀 ' + prefix + ' 现读 ' + str(len(hits)) + ' 只，不是 1'
    return hits[0]


E_IDENT = erow('IDENTITY')
E_CNT = erow('E 臂计数')
E_READ = erow('E 臂读数')
_e_cmp = erow('CMP')
_e_ver = erow('VERDICT')
_e_den = erow('DENOM')
_e_pln = erow('PLAIN')
_e_seal = erow('SEAL')
PLN_PAIRS = re.findall(r'([^.（）()/：: ]+\.log)=([0-9]+) 处', _e_pln)
assert len(PLN_PAIRS) == 4, 'ABORT: PLAIN 行现读 ' + str(len(PLN_PAIRS)) + ' 组，不是 4 组（四臂各一）'
PLN_TXT = ' / '.join([a.split('/')[-1] + '=' + b + ' 处' for a, b in PLN_PAIRS])
PLN_E = [b for a, b in PLN_PAIRS if a.strip().startswith('20260925')][0]
BOOT = re.search(r'ELF 指纹 = ([0-9a-f]{16})', E_IDENT).group(1)
PROBE_ROW = [l for l in ELINES if 'hold-on' in l]
assert len(PROBE_ROW) == 1, 'ABORT: hold-on 探针行现读 %d 只' % len(PROBE_ROW)
W_N = int(re.search(r'probe# ([0-9]+) 次', E_CNT).group(1))
ACK_N = int(re.search(r'应答 ([0-9]+) 条', E_CNT).group(1))
WIN = re.search(r'窗口 ([0-9.]+) s', E_CNT).group(1)
DENOM_N = int(re.search(r'我方 = ([0-9]+) 只', _e_den).group(1))
LINES_LOG = re.search(r'非空 ([0-9]+) 行', E_READ).group(1)
assert ACK_N == 0, 'ABORT: E 臂应答数不是 0，本批判读口径要重写'
assert '全 NACK 不定案' in _e_ver and '同形' in _e_cmp, 'ABORT: E 臂 VERDICT/CMP 两行与本批要写的判读不同形'

# ---- 现场态（本遍现跑，不转抄）
COMS = run((sys.executable, '-c',
            'import serial.tools.list_ports as p;'
            'print(", ".join(sorted([x.device for x in p.comports() if x.device.startswith("COM")])))')).stdout.decode('utf-8', 'replace').strip()
HAS14 = 'COM14' in [x.strip() for x in COMS.split(',')]
REV = run(('git', 'rev-list', '--count', 'origin/main..HEAD')).stdout.decode('utf-8', 'replace').strip()
ST = [l for l in run(('git', '-c', 'core.quotePath=false', 'status', '--porcelain')).stdout.decode('utf-8', 'replace').splitlines() if l.strip()]
ST_M = len([l for l in ST if l.startswith(' M')])
ST_Q = len([l for l in ST if l.startswith('??')])

# ---- 归档封界两把尺（定义随读数一起落盘，见载体 SEAL 行）
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
assert S0A[2] == SEAL_REF and S0A[:2] == S0B[:2], 'ABORT: 写盘前 FOLD-A 与在册聚合不等 / 两把尺的只数字节互核失败'
# 阳性对照：假名**只在内存里**进折叠，盘上不得有那只（归档封界不许被本遍动一字节）
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
_probe_red = PA[2] != S0A[2] and PB[2] != S0B[2]
assert _probe_red and not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: SEAL 门没有执行者（假名未使两把尺变红，或假名已落盘）'
_FIRED = (1 if PA[2] != S0A[2] else 0) + (1 if PB[2] != S0B[2] else 0)

# ---- 内层复核器（排在构造正文之前，本遍那只必须严格晚于订正遍那只 —— 上一批那条归属规矩的执行者）
_vm = run((sys.executable, VMRUN))
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=%d' % _vm.returncode
VM_CARRIER = _mc.group(1).split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_CARRIER)).split('\n') if l.startswith('INNER_ROWS=')][0]
NM = re.compile(r'^vm_run_([0-9]{8}_[0-9]{6})\.txt$')


def nm_time(f):
    m = NM.match(f)
    assert m, 'ABORT: 候选名 ' + repr(f) + ' 不匹配整名模式（vm_run_ + 8 位日期 + 下划线 + 恰好 6 位时刻 + .txt）'
    return datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')


assert nm_time(VM_CARRIER).strftime('%Y-%m-%d %H:%M:%S') > FIX2_AT, 'ABORT: 本遍代落件没有严格晚于订正遍那一刻'

# ---- 明文凭据闸：口令只从宏体读出，不打印、不进正文、不进命令文本
_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏，闸无法自证扫的是真口令'
secret = _secret.group(1).encode('utf-8')

# ---- 第二条 FreqErr 的现场复跑：同一份字节，三种读法（md5 不变；严格 cp936 抛错、容错 cp936 产替换符 ⇒ 坏的是解码，不是件）
_b = rb(FIXER)
_u8 = _b.decode('utf-8')
try:
    _b.decode('cp936')
    STRICT_FAIL = -1
except UnicodeDecodeError as e:
    STRICT_FAIL = e.start
MOJI = _b.decode('cp936', 'replace')
MOJI_BAD = MOJI.count(chr(0xFFFD))
assert md5b(_b) == md5b(_u8.encode('utf-8')), 'ABORT: utf-8 往返就不等，文件本体确实坏了'
assert STRICT_FAIL > 0 and MOJI_BAD > 0 and len(MOJI) != len(_u8), 'ABORT: 本批第二条没有现场锚（解码既没抛错也没产替换符）'

# ================= 正文 =================
DOC_TITLE = ('### 38.28 R57 收口批 = 三遍的账（崩溃 ' + CRASH_AT + ' / 补落 ' + FIX1_AT + ' / 订正 ' + FIX2_AT + '）'
             '+ 现场态（本遍现跑于 ' + RUN_AT + '；**零串口动作、没烧录、没 push、屏亮仍 0 次肉眼确认**）')
DOC_ROWS = [
    DOC_TITLE,
    '',
    '- **三遍时刻与本遍复算的出处**：崩溃遍落纸 ' + CRASH_AT + '（现读排查记录第 ' + str(SEC27[0] + 1) + ' 行标题里那句 paperwork）/ '
    '补落遍 ' + FIX1_AT + '（现读 `hardware/r57_paperwork1.txt` 第 2 行）/ 订正遍 ' + FIX2_AT + '（现读 `hardware/r57_paperwork1_fix2.txt` 第 2 行）'
    '⇒ 三格同序且都 grep 得到；三只上一遍的件在本遍进入前 mtime 全部早于本遍进入时刻 = True ⇒ **本遍一字节未回写**。',
    '- **归属那一格收口在哪**：在册错句指的那只 = `' + CLAIMED + '.txt`（现读补落遍载体 CRASH 行），真值 = `' + REAL + '.txt`（现读订正遍载体 TRUTH 行）；'
    '本遍现场复跑"只订正归属、不动数值"那句：两只各 ' + str(len(SAID)) + ' 行、纯 LF，逐行差异行 = ' + str(DIFF_ROWS) + '（正是 `RUN_AT=` 那一行）= True '
    '⇒ 本批**没有任何数值被这两遍改过**，而这句话的可复算锚不在上一遍的载体的话里，在本遍这次重跑里。',
    '- **E 臂那条判读口径没变**：0x34 应答 = ' + str(ACK_N) + ' 条 / probe ' + str(W_N) + ' 次 / 窗口 ' + WIN + ' s / 非空 ' + LINES_LOG + ' 行，'
    '与 C 臂逐格同形（PWR / ACK 读数 / acked 名单 / 全总线扫）⇒ 锂电池在位 + 复位起抓这一格加进来之后仍然**全 NACK**，'
    '按 §14.3「全 NACK 不定案」**不结案、不改判 PMIC 本体**（现读取证载体 CMP / VERDICT 两行，本遍逐字复读）。',
    '- **屏侧分母**：我方 ' + str(DENOM_N) + ' 只（现读 DENOM 行；官方例程 2 只不进分母）/ hold-on 探针在册 ' + str(len(PROBE_ROW)) + ' 行（第一行那句 0x34 仍不应答）。',
    '- **身份等式**：boot ELF 指纹 ' + BOOT + ' == 待烧那只现算 bin[176:184] ⇒ **待烧 = 板上 = fb32168a…**（§38.23 那条分裂在本批之前已合，本遍只是复读它的出处；'
    '更早那两处旧模板句违规在册第 3732、3746 行，本遍仍不回写）。',
    '- **归档封界**：FOLD-A ' + str(S0A[0]) + ' 只 / ' + format(S0A[1], ',') + ' B / `' + S0A[2] + '`，FOLD-B ' + str(S0B[0]) + ' 只 / '
    + format(S0B[1], ',') + ' B / `' + S0B[2] + '`（两把尺各自的定义随读数一起登在载体 SEAL 行）；gen 24 仍是末版，本遍未往 `hardware/ht305_sync/` 落一字节'
    '（内存假名使两把尺双红 = True，盘上无那只 = True）。',
    '- **现场态（本遍现跑）**：串口枚举 = ' + COMS + ' ⇒ COM14 在位 = ' + str(HAS14) + '（订正遍那格是 False，各量各的，不许互相复用）/ '
    'git rev-list origin/main..HEAD = ' + REV + '（未 push）/ status --porcelain = ' + str(len(ST)) + ' 行（' + str(ST_M) + ' 只 M + ' + str(ST_Q) + ' 只 ??）。',
    '- **明文半径（现读 E 臂取证载体 PLAIN 行，逐臂点名）**：' + PLN_TXT + '（口令只从 `provision_ap.c` 的宏体读出做计数，不进本批任何正文、不进命令文本）'
    '⇒ E 臂那只入库件自带明文 ' + PLN_E + ' 处，与 R56 那两臂同案 ⇒ 这几只日志每轮提交逐只点名 DROP、绝不 stage、绝不 push。',
    '- **本批错误类型进 `FreqErr.md` 第四批 2 条**（根族：**量具读数被当成工件状态** —— 一条语法错的真凶离报错点几百行，一段控制台 mojibake 会被读成文件损坏）；'
    '执行者 = 本遍开头那道"对自身源码跑 ast.parse"的门 + 载体 `MOJI` 行那次"同一份字节两种解码、md5 不变而字符数变"的现场复跑。',
    '- **本遍没做（点名）**：没碰串口（只 comports() 只读列口）/ 没烧录 / 没改 `main/` 源码 / 没重建固件 / 没往 `hardware/ht305_sync/` 落一字节 / '
    '没新建清单代次 / 没 push、没 amend / 零删除（含 %TEMP% 里那只 E 臂原件）/ 没回写上一遍三处正文与两只载体 / 屏亮肉眼确认仍 0 次 ⇒ 不播提示音 / '
    'docs 快照第十遍、backups README 第十次读数、todo 第十七遍、done 新节、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数。',
]

FREQ_TITLE = ('## 2026-09-25（R57 第四批：控制台与真凶都离报错点很远）新增 2 条（根族：**量具读数被当成工件状态**）')
FREQ_ROWS = [
    FREQ_TITLE,
    '',
    '[错误类型] **在大段中文正文的字符串拼接里，用"`%`-格式串收尾"再接下一行的裸字面量续写 ⇒ Python 语法直接红，而报错点落在这条语句最早那只左括号那一行（离真凶几百行），'
    '于是排查方向被拽向"文件被工具写坏了"**（本批实测：订正遍工具改稿时出现一处，`ast.parse` 报"括号未闭合"在文件前段，真因是后段某行以 `%` 表达式收尾、下一行又是字面量；'
    '修法 = 那一处改成加号拼 `str(...)`，改完 `ast.parse` 通过）',
    '→ 症状：同一份源码，`grep` 看到的报错行号与实际坏掉的那一行相距几百行；控制台把中文显示成乱码，看起来"像是编码被命令行往返毁了"，'
    '于是第一反应是怀疑**文件本体**，而不是怀疑**语句**。本批还差点据此重抄整只工具（那会覆盖掉已经落地的取证正文引用）。',
    '→ 为什么它危险：它把一次普通的语法错升级成"数据损坏"误判 —— 一旦按误判行动（重写整只文件 / 从备份恢复），就会**真的**破坏取证链，'
    '而破坏的方向恰好是"把上一遍的读数抹掉"。同族更早的形态是"文件名时刻 ≠ 动作时刻"（项目记忆 (48)）与"控制台输出 ≠ 文件内容"，'
    '本条的新形态是：**报错位置 ≠ 错误位置**，而两者都离真凶远。',
    '→ 正确做法：①落地器在**构造正文之前**对**自身源码**跑 `ast.parse`（本批载体 `AST` 行是这件事的执行者：不通过就不落任何字节，本遍实测通过）；'
    '②报错行号只当线索，定位用**前缀二分**（从第 1 行起逐半试 `ast.parse`，红的那一半里再二分）+ `tokenize` 全扫，而不是拿眼睛在几百行中文里找括号；'
    '③大段正文里要插值就用加号拼 `str(...)`，**不要**用"`%` 收尾的行后面紧跟字面量"这种并置续写；'
    '④改完必须把真凶那一行**逐字 grep 一遍**确认已换形（本批现读 `+ str(len(OTHER)) +` 在订正遍工具里 grep 得到 = True，这一句就是本条的锚）。',
    '→ **同族**：项目记忆 (48)"文件名时刻 ≠ 动作时刻"、(59)"崩溃那次的读数不作数"、(88)"订正句本身也是断言载体"、本批第一条（同一处工具，两遍各栽一次）。',
    '',
    '[错误类型] **把控制台的 cp936 mojibake 读成"文件被写坏了"，在没有对文件本体做任何独立证明之前就据显示下结论（量具与工件混同）**'
    '（本批实测：同一只 UTF-8 源码，按 UTF-8 解码得 ' + str(len(_u8)) + ' 字符且往返等值；按 cp936 **严格**解码在第 ' + str(STRICT_FAIL) +
    ' 字节就抛 UnicodeDecodeError，按 cp936 **容错**解码得 ' + str(len(MOJI)) + ' 字符、其中 ' + str(MOJI_BAD) +
    ' 个是替换符；三次读法这只件的 md5 都是同一个 = `' + md5b(_b)[:16] + '…` ⇒ 变的只是解码，字节一位没动）',
    '→ 症状：Git Bash / PowerShell 默认码页不是 UTF-8，Python 的 stdout 也没 `reconfigure` 时，中文整段显示成问号或生僻字；'
    '同一次命令行往返里如果还带 `sed` / `python -c` 写文件，"显示坏"与"写坏"就混在同一个输出里，肉眼分不出来。',
    '→ 为什么它危险：它的代价不是"看到乱码"，而是**据此采取行动** —— 误判损坏会引出重抄、恢复、覆盖，而在归档封界里这些动作才是真的把取证链打断；'
    '本批它是配合前一条把方向拽偏的那只手（语法错报在前段 + 显示乱码 ⇒ "文件坏了"这个假结论看起来很自洽）。',
    '→ 正确做法：①下任何"文件坏了"的结论之前先给三把尺：**同一只件的 md5 / 字节数**（与在册值比）、**`tokenize` 全扫是否通过**、'
    '**`PYTHONIOENCODING=utf-8` 或 `sys.stdout.reconfigure` 之后重打一次**（本批载体 `MOJI` 行 = 本遍现场跑的这三把，且 stdout/stderr 都要 `reconfigure`，见项目记忆 (60) 那一族第 6 次）；'
    '②"两种解码字符数不等"是**显示层**的证据而不是工件层的，必须与 md5 那句一起写，单写会反过来像"文件真变了"；'
    '③若两把尺都过而只有终端坏，登记成"终端显示缺陷"，**不修文件**（本批就是这么处理的：真凶只有第一条那一处语法）。',
    '→ **同族**：项目记忆 (60)"编码守卫 stdout 与 stderr 都要 reconfigure"、(61)"检查动作会污染被检查物"、(95)"落地三步序"、工具自伤那一族（本条是它的孪生：这次坏的不是文件，是我读它的方式）。',
]

LEDGER_REF = '第四批'

payload_text = '\r\n'.join(DOC_ROWS + FREQ_ROWS)
for _t in (payload_text,):
    assert secret not in _t.encode('utf-8'), 'ABORT: 明文口令出现在本批正文里，一个字都不写'
    assert chr(92) not in _t, 'ABORT: 本批正文含 ASCII 反斜杠（会把取证句变成劈行源头）'
    for _s in ('%s', '%d', '@@', 'None', 'BUIL'):
        assert _s not in _t, 'ABORT: 本批正文含未替换哨兵 ' + _s

DOC_NEW = DOC_T + '\r\n'.join([''] + DOC_ROWS) + '\r\n'
FREQ_NEW = FREQ_T + '\r\n'.join([''] + FREQ_ROWS) + '\r\n'
FREQ_LEDGER = ('>'
               ' **【' + RUN_AT + ' 落地｜R57 ' + LEDGER_REF + ' 2 条】** '
               '追加之前现读磁盘（本脚本进入时刻 ' + RUN_AT + '，_T0 取在任何产证动作之前）：'
               '全文 `^[错误类型]` 条数 = **' + str(len([l for l in FREQ_L if l.startswith('[错误类型]')])) + '**、'
               '行数 = **' + str(len(FREQ_L)) + '**、字节 = **' + format(len(FREQ_T.encode("utf-8")), ',') + '**；'
               '本批正文（不含本台账行自己，含上方那只 glue 空行）= **2** 条 / **' + str(len(FREQ_ROWS)) + '** 行 / **' +
               format(len(('\r\n'.join([''] + FREQ_ROWS)).encode('utf-8')), ',') + '** B；'
               '**落盘后的终态三格由载体 `LAND` 行现数**（完成态数字不许在本行里预写，见项目记忆"完成态数字必须在载体落盘后现数"）。'
               '同遍排查记录 改前 **' + str(len(DOC_L)) + '** 行 / **' + format(len(DOC_T.encode('utf-8')), ',') + '** B -> '
               '本批真追加 ' + str(len(DOC_ROWS) + 1) + ' 行（1 只 glue 空行 + ' + str(len(DOC_ROWS)) + ' 行正文），前缀等式成立、纯 CRLF；'
               '三遍的载体与正文一字节未回写。')
FREQ_NEW = FREQ_NEW + FREQ_LEDGER + '\r\n'

# ---- 写盘前最后一道：前缀等式（纯追加）
assert FREQ_NEW.startswith(FREQ_T) and DOC_NEW.startswith(DOC_T), 'ABORT: 前缀等式不成立，本批不是纯追加'
_d0, _b0, _fa0 = fold_a(SYNC)

open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)

# ---- 写盘后独立回读 + 完成态数字在这里现数
d_after = rd(DOC)
f_after = rd(FREQ)
assert d_after == DOC_NEW and f_after == FREQ_NEW, 'ABORT: 回读与内存串不等'
assert '\r' not in d_after.replace('\r\n', ''), 'ABORT: 排查记录写后不再是纯 CRLF'
assert '\r' not in f_after.replace('\r\n', ''), 'ABORT: FreqErr 写后不再是纯 CRLF'
assert secret not in d_after.encode('utf-8') and secret not in f_after.encode('utf-8'), 'ABORT: 明文写进了盘'
DL = d_after.split('\r\n')
FL = f_after.split('\r\n')
DOC_LINES = len(DL) - 1
FREQ_LINES = len(FL) - 1
DOC_BYTES = len(d_after.encode('utf-8'))
FREQ_BYTES = len(f_after.encode('utf-8'))
N_TOTAL = len([l for l in FL if l.startswith('[错误类型]')])
assert N_TOTAL == 216, 'ABORT: 条数现算 = ' + str(N_TOTAL) + '，与"在册 214 + 本批 2"不等'
_d1, _b1, _fa1 = fold_a(SYNC)
S1B = fold_b(SYNC)
assert (_d0, _b0, _fa0) == (_d1, _b1, S1B[2]) == S0B[:2] + (S0B[2],), 'ABORT: SEAL 写盘前后不等，本批动了归档目录'

ROWS = []
ROWS.append('R57 收口批 part A（§38.28 + FreqErr 第四批）  MODE=TAIL-PAPERWORK-A')
ROWS.append('本遍现跑于 ' + RUN_AT + '（进入时刻 _T0 = ' + RUN_AT + '，取在任何产证动作之前）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('AST 自身源码 ast.parse = OK（本批第一条的执行者，排在任何产证动作之前）；订正遍工具里那句 + str(len(OTHER)) + grep 得到 = True')
ROWS.append('MOJI 同一只 UTF-8 源码三次读法（本遍现场跑，不转抄）：UTF-8 ' + str(len(_u8)) + ' 字符且往返等值 = True / cp936 严格解码在第 ' +
            str(STRICT_FAIL) + ' 字节抛 UnicodeDecodeError / cp936 容错解码 ' + str(len(MOJI)) + ' 字符含 ' + str(MOJI_BAD) +
            ' 个替换符；三次读法这只件 md5 同一个 = ' + md5b(_b) + ' ⇒ 显示坏 ≠ 文件坏')
ROWS.append('TIMES 三遍时刻现读：崩溃 ' + CRASH_AT + '（第 ' + str(SEC27[0] + 1) + ' 行标题）/ 补落 ' + FIX1_AT + ' / 订正 ' + FIX2_AT +
            ' ⇒ 同序 + 三格都 grep 得到；三只上一遍的件 mtime 全部早于 _T0 = True')
ROWS.append('BELONG 归属那一格：在册错句指 ' + CLAIMED + '，真值 ' + REAL + '；本遍现场复跑逐行差异 = ' + str(DIFF_ROWS) +
            '（两只各 ' + str(len(SAID)) + ' 行、纯 LF，差异那行以 RUN_AT= 开头 = True）⇒ "只订正归属、不动数值"本遍复核成立')
ROWS.append('E-ARM 判读复读：应答 ' + str(ACK_N) + ' 条 / probe ' + str(W_N) + ' 次 / 窗口 ' + WIN + ' s / 非空 ' + LINES_LOG +
            ' 行 / 我方分母 ' + str(DENOM_N) + ' 只 / boot 指纹 ' + BOOT + '；CMP 与 VERDICT 两行逐字含"同形""全 NACK 不定案" = True')
ROWS.append('VM 本遍现跑内层复核器代落：rc=0 / ' + INNER + ' / 代落件 = hardware/' + VM_CARRIER +
            '；本遍那只名字时刻严格晚于订正遍 = True')
ROWS.append('FIELD 现跑：串口枚举 = COM' + COMS + ' ⇒ COM14 在位 = ' + str(HAS14) + ' / rev-list = ' + REV + '（未 push）/ status --porcelain = ' +
            str(len(ST)) + ' 行（' + str(ST_M) + ' 只 M + ' + str(ST_Q) + ' 只 ??）')
ROWS.append('SEAL 两把尺（定义随读数落盘：FOLD-A = walk 序只折各文件 content 摘要；FOLD-B = 相对路径冒号摘要、排序后以换行连接再折）：'
            'FOLD-A = ' + str(S0A[0]) + ' 只 / ' + str(S0A[1]) + ' B / ' + S0A[2] + '（逐字复现在册 ' + SEAL_REF + ' = True）；'
            'FOLD-B = ' + str(S0B[0]) + ' 只 / ' + str(S0B[1]) + ' B / ' + S0B[2] + '；写盘前后两把尺全等 = True；'
            '内存假名使 FOLD-A/FOLD-B 双红 = ' + str(_probe_red) + '（假名 = ' + PROBE + '，只在内存，盘上无那只文件 = ' +
            str(not os.path.exists(os.path.join(SYNC, PROBE))) + '）'
            + ' ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版')
ROWS.append('LAND 写盘后独立回读现数（完成态数字在这里数，不在台账行里预写）：排查记录 = ' + str(DOC_LINES) + ' 行 / ' + str(DOC_BYTES) +
            ' B / md5 ' + md5b(d_after.encode('utf-8')) + '；FreqErr = ' + str(FREQ_LINES) + ' 行 / ' + str(FREQ_BYTES) +
            ' B / md5 ' + md5b(f_after.encode('utf-8')) + ' / 条数 = ' + str(N_TOTAL) + '（= 在册 214 + 本批 2）；两文件前缀等式 = True、纯 CRLF 写后仍成立 = True')
ROWS.append('WITNESS 本遍现读 md5（前 12 位）：排查记录(改前) ' + md5b(DOC_T.encode('utf-8'))[:12] + ' / FreqErr(改前) ' +
            md5b(FREQ_T.encode('utf-8'))[:12] + ' / 订正遍载体 ' + md5b(rb(FIXCAR))[:12] + ' / 补落遍载体 ' + md5b(rb(PWCAR))[:12] +
            ' / E 臂取证载体 v2 ' + md5b(rb(CAR_E2))[:12] + ' / 本工具 ' + md5b(rb(TOOL))[:12])
ROWS.append('GATE 本遍各道门：空槽 0 破 / §38.28 与"第四批"未在册 0 破 / 缺件 0 / 上一遍件未被本遍写 0 破 / 前缀等式 0 破 / 行尾 0 破 / 反斜杠 0 / '
            '明文 0 / 哨兵 0 / 回读等值 0 破 / SEAL 0 破 / 条数现算 0 破 / 时刻成序 0 破 / 差异行只 RUN_AT 0 破 ⇒ ARMS_FIRED（真红计数）：'
            '内存假名 ' + str(_FIRED) + '（FOLD-A/FOLD-B 各 1，只在内存）+ ast.parse 在写盘前红 ' + str(0) + ' 次（本遍实测通过）= ' + str(_FIRED) + ' 次')
ROWS.append('NOTDONE 本批没做（点名）：没碰串口 / 没烧录 / 没改 main/ 源码 / 没重建固件 / 没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / '
            '没 push、没 amend / 零删除（含 %TEMP% 里那只 E 臂原件）/ 没回写三遍的正文与载体 / 屏亮仍 0 次肉眼确认 ⇒ 不播提示音 / '
            'docs 快照第十遍、backups README 第十次读数、todo 第十七遍、done 新节、dev_log 20260925、updates 新文件、烧录须知换代行、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数')
ROWS.append('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(ROWS)) + ' 行（含本行）')

body = '\n'.join(ROWS) + '\n'
assert secret not in body.encode('utf-8') and chr(92) not in body, 'ABORT: 载体正文含明文/反斜杠'
open(CARRIER, 'w', encoding='utf-8', newline='').write(body)
_c = rd(CARRIER)
assert _c == body and '\r' not in _c, 'ABORT: 载体回读不等或非纯 LF'
print('CARRIER_ROWS', len(_c.rstrip('\n').split('\n')), 'CARRIER_BYTES', len(_c.encode('utf-8')))
print('DOC', DOC_LINES, 'FREQ', FREQ_LINES, 'N_TOTAL', N_TOTAL)
print('SEAL', _d1, _b1, _fa1)
print('VM', VM_CARRIER, 'COM14', HAS14, 'REV', REV)
print('RUN_AT', RUN_AT)
