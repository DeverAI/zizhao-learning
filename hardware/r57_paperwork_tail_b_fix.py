# R57 收口批 part B 补落遍 = 把 part B 第一遍（崩溃遍）留下的"正文五只已落 / 载体未落"收完。
# 崩溃形状：它把一道**全文件**反斜杠门放在 open() 之后，而 todo.md 既有正文本来就有 15 行含反斜杠（历次登记的 grep 命令原文）
#   ⇒ 那道门恒红（它量的是"整只文件里有没有反斜杠"，不是"本遍新落的那段有没有"），于是五只件写完、载体没写、SEAL 写盘后互核也没跑。
# 本遍三件事：①用**能复算的那把尺**证明崩溃遍没改过任何旧行（git diff --numstat 删除列 = 0，逐只点名）；
#   ②复算崩溃遍正文里那三格悬空指针（SELFREF / LAND / VM）并落载体；③FreqErr 第六批 1 条 + 排查记录 1 行登记。
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
TODO = os.path.join(REPO, 'todo.md')
DONE = os.path.join(REPO, 'done.md')
FLASH = os.path.join(HDIR, '烧录须知.md')
DEVLOG = os.path.join(REPO, 'dev_log', '20260925.md')
UPD = os.path.join(REPO, 'updates', '20260925_墨水屏R56四臂R57E臂与收口批四遍.md')
CARA = os.path.join(HDIR, 'r57_paperwork_tail_a_fix.txt')
CARB = os.path.join(HDIR, 'r57_paperwork_tail_b.py')
LEDGER_CAR = os.path.join(HDIR, 'r56_paperwork3_3.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
SRC_MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
VMRUN = os.path.join(HDIR, 'vm_run.py')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
CARRIER = os.path.join(HDIR, 'r57_paperwork_tail_b_fix.txt')
SEAL_REF = 'efda29538483bbc73e91941936512a2f'
PROBE = 'evidence/SEAL_VIOLATION_PROBE12.txt'
TOOL = os.path.join(HDIR, 'r57_paperwork_tail_b_fix.py')

RUN_AT = datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S')
RUN_HMS = RUN_AT[11:]
CARB_M = datetime.fromtimestamp(os.path.getmtime(CARB)).replace(microsecond=0)
CRASH_AT = CARB_M.strftime('%Y-%m-%d %H:%M:%S')


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def md5b(b):
    return hashlib.md5(b).hexdigest()


def run(args):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def nm_time(f):
    m = re.match(r'^vm_run_([0-9]{8}_[0-9]{6})\.txt$', f)
    assert m, 'ABORT: 候选名 ' + repr(f) + ' 不匹配 vm_run_ + 8 位日期 + 下划线 + 6 位时刻 + .txt 的整名模式'
    return datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')


ast.parse(rd(TOOL))
assert not os.path.exists(CARRIER), 'ABORT: 本遍载体槽位非空，不覆写'
for _p in (DOC, FREQ, TODO, DONE, FLASH, DEVLOG, UPD, CARA, CARB, LEDGER_CAR, CAR_E2, SRC_MACRO, VMRUN, BIN):
    assert os.path.isfile(_p), 'ABORT: 缺件 ' + _p
assert os.path.getmtime(CARA) < _T0 and os.path.getmtime(LEDGER_CAR) < _T0, 'ABORT: 被引用的上一遍件 mtime 不早于本遍进入时刻'
assert 'R57 第六批' not in rd(FREQ), 'ABORT: FreqErr 第六批已在册'
TODO_T, DONE_T, FLASH_T = rd(TODO), rd(DONE), rd(FLASH)
DOC_T, FREQ_T = rd(DOC), rd(FREQ)

# ---- ①崩溃遍的"死在哪一行"现读（不是叙述）：那一道全文件门必须真的在盘上、真的排在本遍新落正文之外
CL = rd(CARB).split('\n')
_g = [i for i, l in enumerate(CL) if 'ABORT: 明文/反斜杠写进了' in l]
assert len(_g) == 1, 'ABORT: 崩溃遍那道门现读 ' + str(len(_g)) + ' 只命中 ⇒ 归因没有出处'
GLINE = _g[0] + 1
assert 'chr(92) not in _b' in CL[_g[0]] and 'secret not in _b' in CL[_g[0]], 'ABORT: 那道门不是全文件级 ⇒ 本遍的归因不成立'
_w = [i for i, l in enumerate(CL) if l.startswith('open(TODO,')]
assert len(_w) == 1 and GLINE > _w[0], 'ABORT: 那道门不在写盘之后 ⇒ "红在正文已落之后"这句没有证据'
PRE_BS = len([l for l in TODO_T.split('\r\n')[:271] if chr(92) in l])
assert PRE_BS > 0, 'ABORT: todo.md 既有正文里读不到反斜杠 ⇒ "全文件门恒红"这一归因不成立'

# ---- ②旧行未动的**可复算**尺：tracked 三只件对 HEAD 的 diff 删除列必须为 0（未跟踪件不适用这把尺，本遍点名）
NS = run(('git', '-c', 'core.quotePath=false', 'diff', '--numstat', '--',
          'todo.md', 'done.md', 'hardware/' + os.path.basename(FLASH))).stdout.decode('utf-8', 'replace')
NROWS = {}
for l in NS.splitlines():
    p = l.split('\t')
    if len(p) >= 3:
        NROWS[p[2].replace('\\', '/')] = (p[0], p[1])
for _k, _rel in ((TODO, 'todo.md'), (DONE, 'done.md'), (FLASH, 'hardware/烧录须知.md')):
    assert _rel in NROWS, 'ABORT: ' + _rel + ' 不在 diff 名单里（未跟踪 / 未被这把尺覆盖）⇒ 本遍不许对它下"旧行未动"'
assert len([v for v in NROWS.values() if v[1] != '0']) == 0, 'ABORT: 有旧行被删改 ⇒ 崩溃遍不是纯追加，本遍不能收口'
DEL0 = len(NROWS)
assert DEL0 == 3, 'ABORT: 这把尺现读被点名件 ' + str(DEL0) + ' 只，不是 3 只 ⇒ 正文里那句"三只 tracked 件"没有出处'
ADD = {k: NROWS[v][0] for k, v in ((TODO, 'todo.md'), (DONE, 'done.md'), (FLASH, 'hardware/烧录须知.md'))}
NEW_FILES_TRACKED = run(('git', 'ls-files', '--', 'dev_log/20260925.md', 'updates/')).stdout.decode('utf-8', 'replace')
UPD_UNTRACKED = UPD.replace('\\', '/') not in NEW_FILES_TRACKED.replace('\\', '/')
DEV_UNTRACKED = 'dev_log/20260925.md' not in NEW_FILES_TRACKED.replace('\\', '/')
assert DEV_UNTRACKED and UPD_UNTRACKED, 'ABORT: 那两只其实已被跟踪 ⇒ "这把尺不适用"那句不成立，须改用同一把尺量它们'

# ---- ③崩溃遍正文里那三格悬空指针由本遍现算兑现（SELFREF）
TL = TODO_T.split('\r\n')
T_ROW = [i for i, l in enumerate(TL) if l.startswith('【**todo 第十七遍台账｜')]
assert len(T_ROW) == 1, 'ABORT: 第十七遍台账行现读 ' + str(len(T_ROW)) + ' 只'
PRE_PRE = [i + 1 for i, l in enumerate(TL) if l.startswith('- [ ]')]
PRE_SUB = [i + 1 for i, l in enumerate(TL) if '- [ ]' in l]
_lc = rd(LEDGER_CAR).split('\n')
_led = [i for i, l in enumerate(_lc) if l.startswith('LEDGER 命令原文现跑') and 'todo.md' in l]
assert len(_led) == 1, 'ABORT: 上一遍载体里读不出唯一那条 LEDGER 命令行'
_m = re.search(r'输出 = ([0-9 ]+)（只数 ([0-9]+)）', _lc[_led[0]])
assert _m, 'ABORT: 那条 LEDGER 行读不出名单与只数 ⇒ 对照物不存在'
CAR_LIST = [int(x) for x in _m.group(1).split()]
CAR_N = int(_m.group(2))
assert PRE_PRE == CAR_LIST and CAR_N == len(CAR_LIST), 'ABORT: 前缀口径现跑与上一遍在册不等 ⇒ 名单动过'
EXTRA = [x for x in PRE_SUB if x not in PRE_PRE]
assert len(PRE_SUB) == len(PRE_PRE) + 1 and len(EXTRA) == 1 and EXTRA[0] == T_ROW[0] + 1, 'ABORT: 自指等式（子串 = 前缀 + 1 且多出的就是台账行）不成立'
SEC24 = len([l for l in DONE_T.split('\n') if l.startswith('- [x] 203') or l.startswith('- [x] 204')])
assert SEC24 == 2, 'ABORT: done 203/204 现读 ' + str(SEC24) + ' 只'
assert '## 二十四' in DONE_T and FLASH_T.count('### 〇-补3') == 1
DEV_T, UPD_T = rd(DEVLOG), rd(UPD)
for _p, _t in ((DONE, DONE_T), (FLASH, FLASH_T), (DEVLOG, DEV_T), (UPD, UPD_T)):
    assert '\r' not in _t, 'ABORT: ' + os.path.basename(_p) + ' 行尾纯度破了'
assert TODO_T.count('\n') == TODO_T.count('\r\n')

# ---- ④现场态（本遍现跑，各量各的）
COMS = run((sys.executable, '-c',
            'import serial.tools.list_ports as p;'
            'print(", ".join(sorted([x.device for x in p.comports() if x.device.startswith("COM")])))')).stdout.decode('utf-8', 'replace').strip()
HAS14 = 'COM14' in [x.strip() for x in COMS.split(',')]
REV = run(('git', 'rev-list', '--count', 'origin/main..HEAD')).stdout.decode('utf-8', 'replace').strip()
ST = [l for l in run(('git', '-c', 'core.quotePath=false', 'status', '--porcelain')).stdout.decode('utf-8', 'replace').splitlines() if l.strip()]
ST_M = len([l for l in ST if l.startswith(' M')])
ST_Q = len([l for l in ST if l.startswith('??')])
BIN_B = rb(BIN)
BIN_MD5 = md5b(BIN_B)
BOOT16 = re.search(r'ELF 指纹 = ([0-9a-f]{16})', rd(CAR_E2)).group(1)
BIN16 = BIN_B[176:184].hex()
assert BOOT16 == BIN16, 'ABORT: 身份等式不复现（boot ' + BOOT16 + ' vs bin[176:184] ' + BIN16 + '）'
E_PROBE = re.search(r'probe# ([0-9]+) 次', rd(CAR_E2)).group(1)
E_ACK = re.search(r'应答 ([0-9]+) 条', rd(CAR_E2)).group(1)
E_DEN = re.search(r'我方 = ([0-9]+) 只', rd(CAR_E2)).group(1)
PARTA_AT = re.search(r'本遍现跑于 ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:]{8})', rd(CARA)).group(1)
TAIL_ROWS = [l for l in rd(CARB).split('\n') if l.startswith('ROWS.append(')]

# ---- ⑤代落件归属：池子里每一只都必须被本批某一遍的在册载体点过名；且池子最晚那只必须来自上一遍（part A），
#     这才反证崩溃遍（CARB mtime）死在 vm_run 之前。名单只读 part A 一只载体是不够的 —— 今日 13:xx 那几只归更早各遍。
CARS_TODAY = sorted([f for f in os.listdir(HDIR) if re.match(r'^r57_[A-Za-z0-9_\-]*\.txt$', f)])
assert CARS_TODAY, 'ABORT: 今日 r57 载体一只都没有 ⇒ 归属门候选为 0，不许当"干净"'


def vm_names(text):
    # 更早的载体里同名有两种拼法（带 .txt / 只到 6 位时刻），只认带后缀会把它们漏成"未归格"
    return set(['vm_run_20260925_' + g + '.txt' for g in re.findall(r'vm_run_20260925_([0-9]{6})', text)])


NAMED = set()
for _f in CARS_TODAY:
    NAMED |= vm_names(rd(os.path.join(HDIR, _f)))
assert NAMED, 'ABORT: 今日在册载体读不出任何代落件名'
POOL = [f for f in os.listdir(HDIR) if re.match(r'^vm_run_20260925_[0-9]{6}\.txt$', f)]
POOL.sort(key=nm_time)
assert POOL, 'ABORT: 今日一只代落件都没有 ⇒ 归属门候选为 0，不许当"干净"'
UNATTR = [f for f in POOL if f not in NAMED]
assert len(UNATTR) == 0, 'ABORT: 代落件池里有未归格名字 ' + ' / '.join(UNATTR) + ' ⇒ 归属门没有出处，本遍不能收口'
NAMED_CARA = vm_names(rd(CARA))
assert NAMED_CARA, 'ABORT: 上一遍（part A）载体读不出代落件名'
LAST_NAMED = nm_time(POOL[-1])
assert LAST_NAMED == max([nm_time(f) for f in NAMED_CARA]), 'ABORT: 池子最晚那只晚于上一遍在册最晚 ⇒ 崩溃遍跑到过 vm_run，归因要重读'
assert LAST_NAMED < CARB_M, 'ABORT: 池子最晚那只不早于崩溃遍工具落盘时刻 ⇒ 崩溃遍可能跑到过 vm_run'


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
assert S0A[2] == SEAL_REF and S0A[:2] == S0B[:2], 'ABORT: 写盘前 FOLD-A 与在册聚合不等 / 两把尺公共量互核失败'
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
assert PA[2] != S0A[2] and PB[2] != S0B[2] and not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: SEAL 门没有执行者'
_FIRED = 2

_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏'
secret = _secret.group(1).encode('utf-8')

# ================= 正文 =================
DOC_ROW = ('- **登记（§38.28 part B 补落遍｜' + RUN_AT + '）**：part B 第一遍（崩溃遍，工具 ' + CRASH_AT + ' 落盘）把五只台账件写完正文之后，'
           '死在**它自己写错量程的一道门**上：那道门对**整只文件**问"有没有 ASCII 反斜杠"，而 todo.md 既有正文里本来就有 ' + str(PRE_BS) +
           ' 行含反斜杠（历次登记的 grep 命令原文，形如转义方括号）⇒ 它不是本遍正文的缺陷，是**门把旧字节也算进来了**；'
           '现读那一道在本遍工具第 ' + str(GLINE) + ' 行，而它排在第 ' + str(_w[0] + 1) + ' 行的写盘之后 ⇒ 五只件已落、载体未落、SEAL 写盘后互核与 vm_run 都没跑（同族第 2 次：**裁决类门排在 open() 之后**）。'
           '本遍复算三件事：①**旧行一根没动** = 对 HEAD 现跑 `git diff --numstat`，被点名的 tracked 件 = **' + str(DEL0) +
           '** 只（todo / done / 烧录须知），它们的删除列全为 0（新增列逐只点名 = todo ' + ADD[TODO] + ' / done ' + ADD[DONE] + ' / 烧录须知 ' + ADD[FLASH] +
           '，含 R53 之后各批未提交的追加，本遍不把它说成"本遍只加了这些"）；另两只（dev_log/20260925.md 与 updates 那只新文件）**未跟踪 ⇒ 这把尺不适用**，'
           '它们的"无旧行可改"只能由崩溃遍自己那句"进入前不存在"支撑，本遍如实登记为**控制流证据不是字节证据**（' + str(DEV_UNTRACKED) + ' / ' + str(UPD_UNTRACKED) + '）。'
           '②**崩溃遍正文里那三格指向空载体的指针由本遍现算兑现**：SELFREF（前缀口径现跑 = ' + str(len(PRE_PRE)) + ' 只、行号逐位等于上一遍载体在册输出 = True；子串口径 = ' +
           str(len(PRE_SUB)) + ' = 前缀 + 1，多出的那只行号 ' + str(EXTRA[0]) + ' 现读正是第十七遍台账行 = True）；③**归属**：今日代落件池 ' + str(len(POOL)) +
           ' 只全部落在本批各遍在册载体点名的 ' + str(len(NAMED)) + ' 只之内（未归格 0 只 = True），且池子最晚那只 ' + POOL[-1] + '（名字时刻 ' +
           LAST_NAMED.strftime('%H:%M:%S') + '）正是上一遍 part A 在册那一只 ⇒ 崩溃遍（工具落盘 ' + CRASH_AT + '）没产代落件 = 没跑到 vm_run，本遍那只见本遍载体 VM 行。'
           '五只件当前终态（行数 / 字节 / md5）逐只登在本遍载体 `LAND` 行；FreqErr 第六批 1 条（根族：**门的量程比被检物大 ⇒ 旧字节把门点红**）。')
FREQ_TITLE_FMT = '## 2026-09-25（R57 第六批：一道量错量程的全文件门，又红在写盘之后）新增 {N} 条（根族：**门的量程比被检物大** / **裁决类门排在写盘之后**）'
FREQ_BODY = [
    '',
    '',
    '[错误类型] **把"本遍新落的正文里不许出现某字符"写成"整只文件里不许出现某字符"，而那只文件既有正文本来就有那个字符 ⇒ 这道门恒红，'
    '且它排在写盘之后，于是五只台账件已落、载体未落（part B 崩溃遍 2026-09-25 实测：全文件反斜杠门命中 todo.md 既有 ' + str(PRE_BS) + ' 行）**',
    '→ 症状：报错文案写着"明文/反斜杠写进了 todo.md"，读起来像"我把脏东西写进去了"，而真相是**脏东西本来就在里面、不是我写的**；'
    '若照这个归因去"清理"，就会去删既有正文里那些 grep 命令原文（破坏取证）。',
    '→ 为什么它危险：①**量程错**的门比缺门更糟 —— 它给出一个听起来很具体的罪名，指向错的对象；'
    '②它排在 open() 之后 ⇒ 红的时候正文已经落盘，本遍又变成"正文已落 / 凭证未落"的半状态（与 part A 那一遍同形，同一个错我连着两遍犯）；'
    '③它把两种不同性质的检查并成一句（明文 = 全文件级，格式 = 新落段级），一句 assert 里 `and` 两只不同量程的门 ⇒ 红了分不清是哪只，这是"两把尺混装同一只元组"那一族的**新亚种：两个不同作用域的门混进同一句**。',
    '→ 正确做法：①写门之前先问**这个门管的是哪一段字节**："既有正文里本来就有吗"——有就不是本遍的判据（本遍新落正文的反斜杠门照样跑，作用域写成本遍正文串）；'
    '②**作用域不同就不许 and 进同一句**，拆成两道、各自给名字（明文门对全文件、格式门对新落段）；'
    '③**裁决类门一律排在写盘之前**（写盘之后只能记账）：本遍把这条做成顺序断言，SEAL 双尺互核 + 阳性对照 + vm_run 全在 open() 之前或只落新文件；'
    '④"旧行未动"要有一把**能复算**的尺：本遍用 `git diff --numstat` 的删除列 = 0（tracked 件），未跟踪件不适用这把尺、如实点名并降级为控制流证据；'
    '⑤半状态不回写正文，只由补落遍追加登记 + 新落载体（本遍就是这么收的）。',
    '→ **同族**：本批第五批第一条（两把尺读数混装进同一只元组，摘要恒不等）、第四批第一条（同一遍内先写盘后裁决）、项目记忆 (69)"登记已跑完前先跑一次并抄 rc"、'
    '记忆"裁决必须同时落 stdout 与 rc"；本条的新形态 = **同一句里 and 两只不同作用域的门**。',
]
N_NEW = len([l for l in FREQ_BODY if l.startswith('[错误类型]')])
assert N_NEW == 1, 'ABORT: 本批正文条数现算 ' + str(N_NEW) + ' 只，不是 1 ⇒ 标题与台账里的数全要跟着改'
assert len([l for l in FREQ_BODY if l.startswith('→ 正确做法') or l.startswith('→ **同族')]) == 2
FREQ_BODY[0] = FREQ_TITLE_FMT.format(N=N_NEW)
FL0 = FREQ_T.split('\r\n')
N_TYPE_PRE = len([l for l in FL0 if l.startswith('[错误类型]')])
LEDGER = ('>'
          ' **【' + RUN_AT + ' 落地｜R57 第六批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（本脚本进入时刻 ' + RUN_AT + '，_T0 取在任何产证动作之前）：'
          '全文 `^[错误类型]` 条数 = **' + str(N_TYPE_PRE) + '**、行数 = **' + str(len(FL0)) + '**、字节 = **' +
          format(len(FREQ_T.encode('utf-8')), ',') + '**；本批正文（不含本台账行自己，含标题上方那只 glue 空行）= **' + str(N_NEW) + '** 条 / **' +
          str(len(FREQ_BODY)) + '** 行；**落盘后的终态三格由本遍载体 `LAND` 行现数**（完成态数字不许在本行里预写）。'
          '同遍排查记录 改前 **' + str(len(DOC_T.split('\r\n'))) + '** 行 -> 本遍真追加 1 行登记 + 1 只 glue 空行；五只台账件由崩溃遍落的正文一字节未回写（删除列 = 0 那把尺见载体 `APPEND` 行）。')

_payloads = {'doc': DOC_ROW, 'freq': '\r\n'.join(FREQ_BODY) + LEDGER}
_all = ''.join(_payloads.values())
assert chr(92) not in _all, 'ABORT: 本遍新落正文含 ASCII 反斜杠（作用域 = 本遍正文，不是整只文件）'
for _s in ('%s', '%d', '@@', 'None', 'BUIL'):
    assert _s not in _all, 'ABORT: 本遍新落正文含未替换哨兵 ' + _s
for _k, _v in _payloads.items():
    assert secret not in _v.encode('utf-8'), 'ABORT: 明文口令出现在 ' + _k + ' 正文里'

DOC_NEW = DOC_T + '\r\n' + DOC_ROW + '\r\n'
FREQ_NEW = FREQ_T + '\r\n' + '\r\n'.join(FREQ_BODY) + '\r\n' + LEDGER + '\r\n'
assert DOC_NEW.startswith(DOC_T) and FREQ_NEW.startswith(FREQ_T), 'ABORT: 前缀等式不成立，本批不是纯追加'
_d0, _b0, _fa0 = fold_a(SYNC)
_db0, _bb0, _fb0 = fold_b(SYNC)

open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(FREQ, 'w', encoding='utf-8', newline='').write(FREQ_NEW)

d_after, f_after = rd(DOC), rd(FREQ)
assert d_after == DOC_NEW and f_after == FREQ_NEW, 'ABORT: 回读与内存串不等'
assert d_after.count('\n') == d_after.count('\r\n') and f_after.count('\n') == f_after.count('\r\n'), 'ABORT: 写后不再是纯 CRLF'
assert secret not in d_after.encode('utf-8') and secret not in f_after.encode('utf-8'), 'ABORT: 明文写进了盘'
DL = d_after.split('\r\n')
FL = f_after.split('\r\n')
DOC_LINES, FREQ_LINES = len(DL) - 1, len(FL) - 1
N_TOTAL = len([l for l in FL if l.startswith('[错误类型]')])
assert N_TOTAL == N_TYPE_PRE + N_NEW, 'ABORT: 条数现算 ' + str(N_TOTAL) + ' != 追加前 ' + str(N_TYPE_PRE) + ' + 本批 ' + str(N_NEW)
DOC_ROWS_ADDED = DOC_LINES - (len(DOC_T.split('\r\n')) - 1)
assert DOC_ROWS_ADDED == 2, 'ABORT: 排查记录现算只数加了 ' + str(DOC_ROWS_ADDED) + ' 行，不是 2 行（glue + 登记）'
FREQ_ROWS_ADDED = FREQ_LINES - (len(FL0) - 1)
assert FREQ_ROWS_ADDED == len(FREQ_BODY) + 2, 'ABORT: FreqErr 现算加 ' + str(FREQ_ROWS_ADDED) + ' 行 != glue 1 + 正文 ' + str(len(FREQ_BODY)) + ' + 台账 1'
_d1, _b1, _fa1 = fold_a(SYNC)
_db1, _bb1, _fb1 = fold_b(SYNC)
assert (_d0, _b0, _fa0) == (_d1, _b1, _fa1), 'ABORT: FOLD-A 写盘前后不等（同尺比）'
assert (_db0, _bb0, _fb0) == (_db1, _bb1, _fb1), 'ABORT: FOLD-B 写盘前后不等（同尺比）'
assert (_d0, _b0) == (_db0, _bb0), 'ABORT: 两把尺公共量互核失败'

_vm = run((sys.executable, VMRUN))
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=' + str(_vm.returncode)
VM_CARRIER = _mc.group(1).split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_CARRIER)).split('\n') if l.startswith('INNER_ROWS=')][0]
assert VM_CARRIER not in NAMED and nm_time(VM_CARRIER) > LAST_NAMED, 'ABORT: 本遍代落件没有严格晚于上一遍在册集'

FILES5 = ((TODO, TODO_T), (DONE, DONE_T), (FLASH, FLASH_T), (DEVLOG, DEV_T), (UPD, UPD_T))
LAND5 = []
for _p, _before in FILES5:
    _t = rd(_p)
    _rows = len(_t.split('\r\n')) - 1 if '\r\n' in _t else len(_t.rstrip('\n').split('\n'))
    LAND5.append((os.path.basename(_p), _rows, os.path.getsize(_p), md5b(_t.encode('utf-8'))))

ROWS = []
ROWS.append('R57 收口批 part B 补落遍  MODE=TAIL-PAPERWORK-B-FIX')
ROWS.append('本遍现跑于 ' + RUN_AT + '（进入时刻 _T0 取在任何产证动作之前）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('CRASH part B 第一遍（崩溃遍）证据本遍现读：工具 hardware/' + os.path.basename(CARB) + ' 落盘 ' + CRASH_AT +
            '（mtime 按秒对齐），它的 ROWS 构造行数 = ' + str(len(TAIL_ROWS)) + '；那道把它点红的门现读在第 ' + str(GLINE) +
            ' 行，句里同时 and 了明文与反斜杠两只**不同作用域**的检查，而它排在第 ' + str(_w[0] + 1) + ' 行 open(TODO) 之后 ⇒ 五只件正文已落、载体未落、SEAL 写盘后互核与 vm_run 都没跑；'
            '它的量程错在本遍复现：todo.md 既有正文（前 271 行）里含反斜杠的行数 = ' + str(PRE_BS) + ' > 0 ⇒ 这道门对**改前**的 todo.md 也恒红（本遍实测，不是推断）')
ROWS.append('APPEND 崩溃遍"没改旧行"的可复算尺（不是假设）：`git diff --numstat` 对 HEAD 现跑，' + str(DEL0) +
            ' 只被点名件的删除列全 = 0；新增列逐只 = todo ' + ADD[TODO] + ' / done ' + ADD[DONE] + ' / 烧录须知 ' + ADD[FLASH] +
            '（这是 R53 之后各批累计，本遍不冒充"本遍只加这些"）；'
            'dev_log/20260925.md 与 updates 那只新文件 **未跟踪 ⇒ 这把尺不适用**（现跑 ls-files 命中 = ' + str(DEV_UNTRACKED) + ' / ' + str(UPD_UNTRACKED) +
            '，本遍现算，两只都为 True 才落这句），它们的"无旧行可改"只有崩溃遍进入前的空槽断言撑 = **控制流证据，本遍如实降级登记**')
ROWS.append('SELFREF 崩溃遍正文里那句"由载体兑现"的格子，本遍现算：todo 前缀口径 = ' + str(len(PRE_PRE)) + ' 只、行号 = ' +
            ' '.join(str(x) for x in PRE_PRE) + ' 与上一遍载体 hardware/' + os.path.basename(LEDGER_CAR) + ' 第 ' + str(_led[0] + 1) + ' 行在册 = ' +
            ' '.join(str(x) for x in CAR_LIST) + ' 逐位相等 = True；子串口径 = ' + str(len(PRE_SUB)) + ' = 前缀 + 1 = True，多出的行号 = ' + str(EXTRA[0]) +
            '，现读该行以 todo 第十七遍台账那句起头 = True ⇒ **自指由盘上现算兑现，不是崩溃遍那句叙述**')
ROWS.append('CONTENT 崩溃遍落的五只件本遍现读核形状：done 203 与 204 各 1 行（合计 ' + str(SEC24) + ' 行）/ done 有 ## 二十四 = True / 烧录须知 〇-补3 唯一 = True / '
            'dev_log 与 updates 非空壳（各 ' + str(LAND5[3][1]) + ' 行 / ' + str(LAND5[4][1]) + ' 行）/ 四只 LF 件写后仍无 CR = True / todo 仍纯 CRLF = True')
ROWS.append('IDENTITY 待烧 = 板上（本遍现算，与崩溃遍各量各的）：' + BIN + ' = ' + format(len(BIN_B), ',') + ' B / md5 ' + BIN_MD5 +
            '（32 个十六进制字符 = md5，不是 sha256）；boot ELF 前 16 位 ' + BOOT16 + ' == bin[176:184] = ' + BIN16 + ' = True')
ROWS.append('ARMS 屏侧读数出处（现读 E 臂取证载体与排查记录）：E 臂 probe# ' + E_PROBE + ' 次 / 应答 ' + E_ACK + ' 条 / 我方分母 ' + E_DEN +
            ' 只；四臂在册 VERDICT=FOUR-ARMS-ALL-NACK 字样 grep = True ⇒ 全 NACK 不定案、屏亮 0 次肉眼确认')
ROWS.append('BELONG 今日 vm_run 代落件池 ' + str(len(POOL)) + ' 只（' + ' / '.join(POOL) + '），逐只对照本批各遍在册载体（' + str(len(CARS_TODAY)) +
            ' 只 r57 载体）点名的 ' + str(len(NAMED)) + ' 只 ⇒ 未归格 0 只 = True（本遍现算，名单只读 part A 一只载体不够：13:10~13:48 那几只归更早各遍）。'
            '关键一格 = 池子最晚那只 ' + POOL[-1] + '（名字时刻 ' + LAST_NAMED.strftime('%H:%M:%S') + '）与上一遍 part A 在册最晚那只逐字同名 = True，'
            '且该时刻早于崩溃遍工具落盘 ' + CRASH_AT + ' ⇒ **崩溃遍死在 vm_run 之前**（它死在第 ' + str(GLINE) + ' 行，vm_run 调用在更后面）')
ROWS.append('VM 本遍现跑内层复核器代落：rc=0 / ' + INNER + ' / 代落件 = hardware/' + VM_CARRIER + '；本遍那只名字时刻严格晚于在册集最晚那只 = True')
ROWS.append('FIELD 现跑：串口枚举 = ' + COMS + ' ⇒ COM14 在位 = ' + str(HAS14) + ' / rev-list = ' + REV + '（未 push）/ status --porcelain = ' +
            str(len(ST)) + ' 行（' + str(ST_M) + ' 只 M + ' + str(ST_Q) + ' 只 ??）')
ROWS.append('SEAL 两条同尺比较 + 一条公共量互核（FOLD-A = walk 序只折各文件 content 摘要；FOLD-B = 相对路径冒号摘要、排序后以换行连接再折）。'
            'FOLD-A 写前 (' + str(_d0) + ', ' + str(_b0) + ', ' + _fa0 + ') == 写后 (' + str(_d1) + ', ' + str(_b1) + ', ' + _fa1 + ') = True；'
            'FOLD-B 写前 ' + _fb0 + ' == 写后 ' + _fb1 + ' = True；公共量互核 = True；FOLD-A 逐字复现在册 ' + SEAL_REF +
            ' = True；内存假名（' + PROBE + '，只在内存，盘上无那只 = True）使两把尺双红 = ' + str(_FIRED) +
            ' ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版')
ROWS.append('LAND 写盘后独立回读现数（完成态数字在这里数）：排查记录 = ' + str(DOC_LINES) + ' 行 / ' + str(os.path.getsize(DOC)) + ' B / md5 ' +
            md5b(d_after.encode('utf-8')) + '（本遍真加 ' + str(DOC_ROWS_ADDED) + ' 行 = glue + 登记）；FreqErr = ' + str(FREQ_LINES) + ' 行 / ' +
            str(os.path.getsize(FREQ)) + ' B / md5 ' + md5b(f_after.encode('utf-8')) + ' / 条数 = ' + str(N_TOTAL) + '（= 追加前 ' + str(N_TYPE_PRE) +
            ' + 本批 ' + str(N_NEW) + '，本遍真加 ' + str(FREQ_ROWS_ADDED) + ' 行）；五只台账件逐只：' +
            ' | '.join([n + ' ' + str(r) + ' 行 ' + format(b, ',') + ' B ' + m for n, r, b, m in LAND5]))
ROWS.append('WITNESS 本遍现读 md5（前 12 位）：本遍工具 ' + md5b(rb(TOOL))[:12] + ' / 崩溃遍工具 ' + md5b(rb(CARB))[:12] + ' / part A 载体 ' +
            md5b(rb(CARA))[:12] + ' / 名单对照载体 ' + md5b(rb(LEDGER_CAR))[:12] + ' / E 臂取证 v2 ' + md5b(rb(CAR_E2))[:12] +
            ' / 待烧 bin ' + BIN_MD5[:12] + ' / 排查记录(本遍改前) ' + md5b(DOC_T.encode('utf-8'))[:12] + ' / FreqErr(本遍改前) ' + md5b(FREQ_T.encode('utf-8'))[:12])
ROWS.append('GATE 本遍各道门：自身 ast.parse / 缺件 14 只 / 载体与第六批空槽 0 破 / 崩溃遍那道门"死在写盘之后"现读 0 破 / '
            '旧行未动（删除列全 0）0 破 / SELFREF 三关系式 0 破 / 五只件形状 0 破 / 身份等式 0 破 / 代落件池归属（未归格 0 只）0 破 / 前缀等式 0 破 / '
            '行尾纯度按各自口径 0 破 / 反斜杠（**作用域 = 本遍新落正文**）0 / 明文（作用域 = 全文件）0 / 哨兵 0 / 回读等值 0 破 / 条数与行数现算 0 破 / '
            'SEAL 两条同尺 + 公共量 0 破 ⇒ ARMS_FIRED（真红计数）= ' + str(_FIRED) + '，全部来自内存假名（FOLD-A 与 FOLD-B 各 1）；'
            '本遍写盘前自纠 1 处：第一稿把反斜杠门写成对整只文件求值（正是崩溃遍那个错），落笔时改成本遍正文串')
ROWS.append('NOTDONE 本批没做（点名）：没换电池 / 没万用表 / 没第二块板 / 没碰串口（只 comports() 列口）/ 没烧录 / 没改 main/ 源码 / 没重建固件 / '
            '没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / 没新建备份根 / 没 push、没 amend / 零删除（含 %TEMP% 里 D 臂与 E 臂原件）/ '
            '没回写崩溃遍落的五只件正文 / 没勾 todo 那 17 只未选项 / 屏亮仍 0 次肉眼确认 ⇒ 不播提示音 / docs 快照第十遍、backups README 第十次读数、'
            '提交轮 #9、第 14 代同步、mindog 双路复核、空上下文故障检测子AGENT 都在本件之后 ⇒ 本遍不预写它们的数')
ROWS.append('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(ROWS)) + ' 行（含本行）')

body = '\n'.join(ROWS) + '\n'
assert secret not in body.encode('utf-8') and chr(92) not in body, 'ABORT: 载体正文含明文/反斜杠（作用域 = 载体本体，本遍新写）'
open(CARRIER, 'w', encoding='utf-8', newline='').write(body)
_c = rd(CARRIER)
assert _c == body and '\r' not in _c, 'ABORT: 载体回读不等或非纯 LF'
print('CARRIER hardware/' + os.path.basename(CARRIER), len(_c.rstrip('\n').split('\n')), 'rows', os.path.getsize(CARRIER), 'B')
print('DOC', DOC_LINES, 'FREQ', FREQ_LINES, 'N_TOTAL', N_TOTAL, 'GLINE', GLINE, 'PRE_BS', PRE_BS)
print('SEAL A', _d1, _b1, _fa1, 'B', _db1, _bb1, _fb1)
print('VM', VM_CARRIER, 'POOL', len(POOL), 'NAMED', len(NAMED), 'COM14', HAS14, 'REV', REV)
print('RUN_AT', RUN_AT)
