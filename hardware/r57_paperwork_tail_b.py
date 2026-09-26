# R57 收口批 part B = 台账五只件一次落齐（todo 第十七遍 / done 第 二十四 节 203+204 / dev_log 20260925 / updates 新文件 / 烧录须知 〇-补3 换代节）。
# 门继承前几遍全套：自身 ast.parse / 缺件 / 空槽 / 逐目标行尾纯度 / 追加等式 + 插入等式 / 反斜杠 / 明文 / 哨兵 /
#   名单对照上一遍载体输出（§38.24 换代后的新口径）/ 代落件归属靠上一遍载体逐格点名 / SEAL 两条同尺比较 + 公共量互核 + 内存假名 /
#   裁决门全在 open() 之前 / 完成态数字写盘后现数 / GATE-COUNT 在所有行之后。
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
CARA = os.path.join(HDIR, 'r57_paperwork_tail_a_fix.txt')
LEDGER_CAR = os.path.join(HDIR, 'r56_paperwork3_3.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
SRC_MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
VMRUN = os.path.join(HDIR, 'vm_run.py')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
DEVLOG = os.path.join(REPO, 'dev_log', '20260925.md')
UPDNAME = '20260925_墨水屏R56四臂R57E臂与收口批四遍.md'
UPD = os.path.join(REPO, 'updates', UPDNAME)
CARRIER = os.path.join(HDIR, 'r57_paperwork_tail_b.txt')
SEAL_REF = 'efda29538483bbc73e91941936512a2f'
PROBE = 'evidence/SEAL_VIOLATION_PROBE11.txt'
TOOL = os.path.join(HDIR, 'r57_paperwork_tail_b.py')

RUN_AT = datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S')
RUN_HMS = RUN_AT[11:]


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
for _p in (DOC, TODO, DONE, FLASH, CARA, LEDGER_CAR, CAR_E2, SRC_MACRO, VMRUN, BIN):
    assert os.path.isfile(_p), 'ABORT: 缺件 ' + _p
assert not os.path.exists(CARRIER), 'ABORT: 本遍载体槽位非空，不覆写'
assert not os.path.exists(DEVLOG), 'ABORT: dev_log/20260925.md 已在册，本遍不覆写'
assert not os.path.exists(UPD), 'ABORT: updates 那只新文件已在册，本遍不覆写'
assert os.path.getmtime(CARA) < _T0 and os.path.getmtime(LEDGER_CAR) < _T0, 'ABORT: 被引用的上一遍件 mtime 不早于本遍进入时刻'

TODO_T = rd(TODO)
DONE_T = rd(DONE)
FLASH_T = rd(FLASH)
DOC_T = rd(DOC)
TODO_L = TODO_T.split('\r\n')
assert TODO_T.endswith('\r\n') and TODO_T.count('\n') == TODO_T.count('\r\n'), 'ABORT: todo.md 不是纯 CRLF 收尾'
for _p, _t in ((DONE, DONE_T), (FLASH, FLASH_T)):
    assert _t.endswith('\n') and '\r' not in _t, 'ABORT: ' + os.path.basename(_p) + ' 不是纯 LF'
for _pat, _p, _t in (('todo 第十七遍台账｜', TODO, TODO_T), ('R56~R57（2026-09-25', FLASH, FLASH_T)):
    assert _t.count(_pat) == 0, 'ABORT: 空槽门破 —— ' + _p + ' 里已有 ' + _pat
assert '二十四、R56~R57' not in DONE_T, 'ABORT: done.md 第 二十四 节已在册'
assert '- [ ]' in TODO_T, 'ABORT: todo.md 里连被搜串都没有 ⇒ 名单这一格无从对照（候选为 0 必须响）'
DOC_T2 = DOC_T

# ---- ①名单格（§38.24 换代后的新口径）：命令原文 + 本次输出同落纸，对照物 = 上一遍载体的输出
PRE_PRE = [i + 1 for i, l in enumerate(TODO_L) if l.startswith('- [ ]')]
PRE_SUB = [i + 1 for i, l in enumerate(TODO_L) if '- [ ]' in l]
assert PRE_PRE == PRE_SUB, 'ABORT: 改前两把尺（行首前缀 / 整行子串）已经分叉 ⇒ §38.24 那句"两种口径逐位相等"不再成立，本遍的对照物得先重定义'
_lc = rd(LEDGER_CAR).split('\n')
_led = [i for i, l in enumerate(_lc) if l.startswith('LEDGER 命令原文现跑') and 'todo.md' in l]
assert len(_led) == 1, 'ABORT: 上一遍载体里读不出唯一那条 LEDGER 命令行，命中 ' + str(len(_led)) + ' 只'
_m = re.search(r'输出 = ([0-9 ]+)（只数 ([0-9]+)）', _lc[_led[0]])
assert _m, 'ABORT: 那条 LEDGER 行读不出名单与只数 ⇒ 对照物不存在，宁响不静默'
CAR_LIST = [int(x) for x in _m.group(1).split()]
CAR_N = int(_m.group(2))
assert CAR_LIST == PRE_PRE and CAR_N == len(PRE_PRE), 'ABORT: 上一遍在册名单与本遍现跑不等 ⇒ 名单真的动过，本遍不许写成"未变"'

# ---- ②现场态（现跑，且各量各的，不引用上一遍读数）
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
BIN_SIZE = len(BIN_B)
_m = re.search(r'ELF 指纹 = ([0-9a-f]{16})', rd(CAR_E2))
assert _m, 'ABORT: E 臂载体读不出 boot ELF 指纹 ⇒ 身份等式就没法复算'
BOOT16 = _m.group(1)
BIN16 = BIN_B[176:184].hex()
assert BOOT16 == BIN16, 'ABORT: 身份等式不复现（boot ' + BOOT16 + ' vs bin[176:184] ' + BIN16 + '）⇒ "待烧 = 板上"这句要重读'
E_PROBE = re.search(r'probe# ([0-9]+) 次', rd(CAR_E2)).group(1)
E_ACK = re.search(r'应答 ([0-9]+) 条', rd(CAR_E2)).group(1)
E_DEN = re.search(r'我方 = ([0-9]+) 只', rd(CAR_E2)).group(1)
_m4 = re.search(r'([0-9]+) 条 .0x34. 行，应答 0 条', DOC_T2)
assert _m4, 'ABORT: §38.23 里读不出四臂那条 0x34 计数 ⇒ 四臂读数没有出处'
FOUR_ROWS = _m4.group(1)
assert 'FOUR-ARMS-ALL-NACK' in DOC_T2, 'ABORT: 在册四臂判决字样不见了'
_mpa = re.search(r'本遍现跑于 ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:]{8})', rd(CARA))
assert _mpa, 'ABORT: 上一遍（补落遍 part A）载体读不出它的现跑时刻 ⇒ 本批四遍时刻链断了'
PARTA_AT = _mpa.group(1)
SEC_PRE = [l[3:] for l in DONE_T.split('\n') if l.startswith('## ')][-1]
assert not SEC_PRE.startswith('二十四'), 'ABORT: done.md 末节已经是 二十四 ⇒ 空槽门与这格自相矛盾'
FREQ_PRE = rd(FREQ)
for _ph in ('命令文本含被搜串', '计数自指'):
    assert _ph in FREQ_PRE, 'ABORT: 本遍正文要引用 `FreqErr.md` 里那句 ' + _ph + '，但它不在册 ⇒ 假指针'

TODO_ROW = ('【**todo 第十七遍台账｜' + RUN_AT + ' R57 收口批 part B（§38.28 + 四遍账 + 补落遍载体在册之后）落笔之前现跑**：'
            '① 台账三格一律按 §38.24 换代后的新口径登记 —— **命令原文 + 本次输出同落纸，对照物 = 上一遍载体的输出**，'
            '不再引用那串已降级为"不可复算旧快照"的 `44 46 48 …`。'
            '本遍现跑：按"行首前缀 - [ ]"口径数 = ' + str(len(PRE_PRE)) + ' 只，行号 = ' + ' '.join(str(x) for x in PRE_PRE) +
            '；上一遍载体 `hardware/' + os.path.basename(LEDGER_CAR) + '` 第 ' + str(_led[0] + 1) + ' 行在册输出 = ' +
            ' '.join(str(x) for x in CAR_LIST) + '（只数 ' + str(CAR_N) + '）⇒ **新口径下第 2 次现跑逐位未变 = True**'
            '（第 1 次 = §38.24 那一遍）。旧句式"第 N 次逐字未变"里的序数自 §38.24 起作废，本行不再续编，避免两套序数并存。'
            '② **本遍现算抓到两把尺第一次分叉，且分叉是本行自己造的**：改前"行首前缀"与"整行子串"两种口径逐位相等（都是 ' + str(len(PRE_PRE)) +
            ' 只）；本行正文含命令原文里那只字面串 ⇒ 写盘后前缀口径不变（本行以方括号汉字起头，不匹配前缀）、子串口径 = 改前 + 1。'
            '这是 `FreqErr.md` 里那条"命令文本含被搜串 ⇒ 计数自指"的第三种形态：**被污染的是下一遍的那把尺**。'
            '从本行起 todo 这一格的权威尺 = **前缀口径**；子串口径因为历次登记句会各自 +1，永久不能再当"未变"的对照物。'
            '等式不在本行里下结论，由本遍载体 `SELFREF` 行写盘后独立回读兑现。'
            '③ `grep -n` 之于 done.md：本行之前末节号现读 = **' + SEC_PRE + '**，本遍落的第 二十四 节之后由载体 `LAND` 行现数（本行不预写）。'
            '④ `git rev-list --count origin/main..HEAD` 本遍现跑 = ' + str(REV) + '（**本行不回填**：提交轮 #9 之后会 +1，届时的数以那一轮自己的载体为准）。'
            '⑤ 本遍同时落 done 第 二十四 节 203/204、`dev_log/20260925.md`、`updates/' + UPDNAME + '`、`hardware/烧录须知.md` 〇-补3；'
            '载体 = `hardware/r57_paperwork_tail_b.txt`（上一遍 = ' + PARTA_AT + ' 那只 `r57_paperwork_tail_a_fix.txt`）。】')

# ---- ③代落件归属：本遍那只之外，今日池子里每一只都必须由上一遍载体点名（§38.24/§38.28 那一族的执行者）
_car_a = rd(CARA)
POOL = [f for f in sorted(os.listdir(HDIR)) if re.match(r'^vm_run_20260925_[0-9]{6}\.txt$', f)]
assert POOL, 'ABORT: 今日一只代落件都没有 ⇒ 归属门候选为 0，不许当"干净"'
NAMED = set(re.findall(r'vm_run_20260925_[0-9]{6}\.txt', _car_a))
assert NAMED, 'ABORT: 上一遍载体里读不出任何代落件名 ⇒ 没有对照物'
LAST_NAMED = max([nm_time(f) for f in NAMED])
assert len([f for f in POOL if nm_time(f) > LAST_NAMED and f not in NAMED]) <= 1, 'ABORT: 上一遍之后有多只未归格的代落件'

# ---- ④正文五只
DONE_TAIL = [
    '',
    '## 二十四、R56~R57：新镜像真机首烧 + 四臂与 E 臂把 (91) 那条根因否证一半 + 收口批四遍里的一遍崩溃（抓取 2026-09-24 19:59:57 ~ 2026-09-25 14:20:31，任务 203/204）',
    '',
    '- [x] 203 **R56 真机首烧（' + BIN_MD5[:8] + '… 烧进 COM14）+ 四臂判据 + R57 E 臂进样 = 「锂电池在位 + 复位起抓」那一格补进来之后 0x34 仍然全 NACK**'
    '（§38.23 / §38.27 / §38.28；取证 = `hardware/20260924_R56*.log` 四臂 + `hardware/20260925_R57_E臂新镜像锂电池在位复位起抓120s.log` + 判读载体 `hardware/20260925_R57_E臂判据摘录_v2.txt`）',
    '  ① **身份等式复算（本遍现跑，不抄在册）**：boot 行 `ELF file SHA256` 前 16 位 ' + BOOT16 + ' == 构建目录那只 bin 的 [176:184] = ' + BIN16 +
    ' ⇒ **待烧 = 板上 = ' + BIN_MD5[:8] + '…**（' + format(BIN_SIZE, ',') + ' B；md5 是 32 个十六进制字符，不是 sha256）——§38.23 之前"待烧 ≠ 板上"那条分裂已合，本遍是它第一次在台账里被复算而不是被转抄。',
    '  ② **(91) 那句根因的判词换代**：R53 说"GPIO1 没拉住 ⇒ PMIC 未上电 ⇒ 全 NACK"。R56 补做那一步并真机首烧，四臂合计 ' + FOUR_ROWS +
    ' 条 `0x34` 行、应答 **0** 条 ⇒ `VERDICT=FOUR-ARMS-ALL-NACK`；R57 再把 E 臂（锂电池在位 + 复位起抓，probe ' + E_PROBE + ' 次 / 应答 ' + E_ACK +
    ' 条）加进来，与 C 臂逐格同形、唯一实测差 = 供电档位 ⇒ **充分性被实测否证**（拉住了仍然全 NACK），"GPIO1 是必要的一步"这一半仍在。'
    '按 §14.3「全 NACK 不定案」**不结案、不改判 PMIC 本体**。',
    '  ③ **屏侧分母换代**：我方 ' + E_DEN + ' 只（现读 E 臂载体 DENOM 行；官方例程 2 只不进分母）。`panel blanked` / `witness` / `low_no_high` 在盘上日志里仍 0 行 ⇒ 屏亮肉眼确认 **0 次** ⇒ **不播提示音**。',
    '  ④ 三条物理分叉仍在用户侧：换电池 / 万用表量轨 / 第二块同型号板对读。软件侧判据已尽（位碰探针 + 推挽 SCL + 四臂 + E 臂都跑过）。',
    '',
    '- [x] 204 **R57 收口批四遍 = 一遍崩溃留下的"正文已落 / 凭证未落"半状态收完 + 两处量具缺陷当场登记（两把尺混装进同一只元组 / 一道永不成立的门）**'
    '（§38.28 + `FreqErr.md` 第四批 2 条 + 第五批 2 条；崩溃 2026-09-25 14:01:51 / 补落 part A 2026-09-25 14:20:31 / 本遍 part B ' + RUN_AT + '）',
    '  ① 崩溃遍红在 SEAL 那句**链式三段** assert 上：左边取 FOLD-A 的（只数, 字节, 摘要），中间混进 FOLD-B 的摘要，右边又回到 FOLD-B ⇒ 摘要恒不等 = 恒红，'
    '而那句排在 `open()` 之后，于是排查记录 §38.28 与 FreqErr 第四批**已落盘**、载体未落，正文里"由载体 LAND 行现数"的指针全部指向空文件。'
    '本遍按规矩**不回写已落地正文**，只由补落遍追加一行登记 + 新落载体。',
    '  ② 补落遍（part A）复算"崩溃遍没改过任何旧行"：拿上一遍在册的两只 md5 对盘上"前 N 行"现算相等，纯追加成立；'
    '它同时是上一批刚立的**双侧窗口 + 候选池逐格分完**的第一个执行者（认出崩溃遍那只代落件，并把上界从"本遍进入时刻"收紧为"崩溃遍自己的正文 mtime"）。',
    '  ③ 本遍（part B）抓到并登记的第三处：**自指的那把尺是下一遍的**。todo 台账行正文含命令原文里那只字面串 ⇒ 写盘后"整行子串"口径 = 改前 + 1，"行首前缀"口径不变。'
    '两把尺第一次分叉是本遍自己造的，等式（改后子串 = 改前子串 + 1、改后前缀 = 改前前缀）由本遍落地器写盘后独立回读兑现，见本遍载体 `SELFREF` 行。',
    '  ④ 同名尺的新旧账：更早两遍把 FOLD-B 折成"以竖线连接"，崩溃遍与 part A 折成"以换行连接"，两值都对、各自只与自己可比 ⇒ 从 part A 起**摘要必须与折法同格落盘**。',
    '',
]
DONE_NEW = DONE_T + '\n'.join(DONE_TAIL) + '\n'
assert DONE_NEW.startswith(DONE_T), 'ABORT: done.md 前缀等式不成立 ⇒ 本遍不是纯追加'

FLASH_ANCHOR = '## 一、当前固件的真实状态（决定你该看到什么）'
assert FLASH_T.count(FLASH_ANCHOR) == 1, 'ABORT: 烧录须知插入锚不唯一'
FLASH_TAIL = [
    '### 〇-补3、R56~R57（2026-09-24 19:59:57 抓取 ~ 2026-09-25 ' + RUN_HMS + ' 现跑）：新镜像已真机首烧 + 四臂与 E 臂仍全 NACK ⇒ (91) 那条根因**否证一半**【待烧 = 板上，这一格已换代】',
    '',
    '- **待烧那只 = 板上那只（本遍现读构建目录，不抄在册）**：`' + BIN + '` = **' + format(BIN_SIZE, ',') + ' B**，'
    '指纹 **md5 `' + BIN_MD5 + '`**（32 个十六进制字符 = md5，**不是 sha256**；sha256 全长 64 字符）。'
    '身份等式本遍复算：boot 行 `ELF file SHA256` 前 16 位 `' + BOOT16 + '` == 这只 bin 第 176~183 字节 = `' + BIN16 + '` ⇒ **待烧 = 板上 = ' + BIN_MD5[:8] + '…**；'
    '§38.23 之前"待烧 ≠ 板上"那条分裂已合，旧板上那只 `4842a3a0…` 降级为历史。',
    '- **(91) 那条根因现在只能说一半**：R53 的"GPIO1(PWR_OUT) 没拉住 ⇒ AXP 未上电 ⇒ `0x34` 全 NACK"里，'
    '"补做那一步"已于 R56 落地并真机首烧；但四臂合计 **' + FOUR_ROWS + ' 条 `0x34` 行、应答 0 条**（`VERDICT=FOUR-ARMS-ALL-NACK`），'
    'R57 又把 **E 臂**（锂电池在位 + 复位起抓，probe ' + E_PROBE + ' 次 / 应答 ' + E_ACK + ' 条 / 与 C 臂逐格同形，唯一实测差 = 供电档位）加进来 ⇒ '
    '**充分性被实测否证**：线拉住了仍然全 NACK。必要性那一半仍在（不拉它连上电都没有）。按 §14.3「全 NACK 不定案」——**不结案、不改判 PMIC 本体**。',
    '- **COM14 现场态（本遍现跑，各量各的）**：串口枚举 = **' + COMS + '** ⇒ COM14 在位 = **' + str(HAS14) + '**。'
    'R56 那一烧之后它曾回归（E 臂就是在回归之后抓的），本遍又缺席 ⇒ 这条线随批漂，**任何一轮都不许引用上一轮的那个数**。',
    '- **屏侧分母换代 = 我方 ' + E_DEN + ' 只**（现读 E 臂取证载体 DENOM 行；官方例程那 2 只不进分母）；'
    '`panel blanked` / `panel silent` / `witness` / `low_no_high` 在我方日志里仍 **0 行** ⇒ **屏亮至今零次肉眼确认 ⇒ 提示音不播**。',
    '- **下一轮只剩仪器活（都在用户侧）**：① 换一块电池或外接可调电源到 3.7 V 引脚；② 万用表量 AXP 各轨（屏电 1.8 V / 3.3 V）到底有没有输出；'
    '③ 同型号第二块板对读（同一只 bin、同一套判据）——**判"固件 vs 板"最便宜的手段就是这一条**。软件侧判据（位碰探针 / 推挽 SCL / 四臂 / E 臂）已尽。',
    '',
    '> **本节没做（点名，绑定执行者）**：本遍（part B，paperwork）零串口动作、**没烧录、没换电池、没万用表、没第二块板**；'
    '没改 `main/` 源码、没重建固件 ⇒ 待烧仍由本遍现读、板上那只没动；没往 `hardware/ht305_sync/` 落一字节、没新建清单代次（gen 24 仍是末版）；'
    '没 `git push`、没 amend、零删除（含 `%TEMP%` 里 D 臂与 E 臂原件）；屏亮 0 次肉眼确认 ⇒ 不播提示音。',
    '',
]
_ins = '\n'.join(FLASH_TAIL)
_i = FLASH_T.index(FLASH_ANCHOR)
FLASH_NEW = FLASH_T[:_i] + _ins + FLASH_T[_i:]
assert FLASH_NEW[:_i] == FLASH_T[:_i] and FLASH_NEW[FLASH_NEW.index(FLASH_ANCHOR):] == FLASH_T[_i:]
assert FLASH_NEW.replace(_ins, '', 1) == FLASH_T, 'ABORT: 插入等式不成立 ⇒ 本遍动了 烧录须知 的既有字节'
assert FLASH_ANCHOR in FLASH_NEW and FLASH_NEW.count(FLASH_ANCHOR) == 1

DEV_BODY = [
    '# 开发日志 · 2026-09-25',
    '',
    '## 第三十批：**R56 新镜像真机首烧四臂 + R57 E 臂进样 + 收口批四遍（一遍崩溃留下的半状态）**（抓取 2026-09-24 19:59:57 ~ 2026-09-25 ' + RUN_HMS + '）',
    '',
    '### 本批的性质：把 (91) 那条根因放到真机上量，量出来是"半对"',
    '',
    '- R53 留下的判词是：`PWR_OUT`=GPIO1 是 AXP 的电源自锁线，官方例程开机就拉住它，我方旧代码读一次就 `gpio_reset_pin` ⇒ 线悬空 ⇒ PMIC 未上电 ⇒ `0x34` 全 NACK。'
    'R56 补做那一步、重建出 `' + BIN_MD5[:8] + '…` 那只并**真机烧进 COM14**，然后一次烧录抓四臂。',
    '- **四臂读数（§38.23）**：`0x34` 相关行合计 **' + FOUR_ROWS + ' 条、应答 0 条** ⇒ `VERDICT=FOUR-ARMS-ALL-NACK`。'
    'R57 的 **E 臂**把最后那一格（锂电池在位 + 复位起抓）补进样本：probe ' + E_PROBE + ' 次、应答 **' + E_ACK +
    '** 条，与 C 臂在 PWR / ACK 读数 / acked 名单 / 全总线扫四格上**逐格同形**，唯一实测差 = 供电档位。',
    '- ⇒ **判词换代**："拉住 GPIO1 就能开屏电"这一半被实测否证；"不拉它连上电都没有"那一半仍在。'
    '按 §14.3「只有 ACK/TIMEOUT 能定案、全 NACK 不定案」——**不结案、不改判 PMIC 本体**，R34~R43 那批位碰探针的结论范围因此仍带"未上电前提"这个限定。',
    '- **屏侧分母**：我方 **' + E_DEN + ' 只**（E 臂 +1）；官方例程 2 只外部对照不进分母。`panel blanked` / `witness` / `low_no_high` 仍 0 行 ⇒ 屏亮 **0 次**肉眼确认。',
    '',
    '### 收口批四遍的形状（本批 paperwork 的全部）',
    '',
    '- **崩溃遍 2026-09-25 14:01:51**：把 SEAL 写盘前后互核那句写成**链式三段**，左元素取 FOLD-A 摘要、右元素混进 FOLD-B 摘要 ⇒ 恒红；'
    '且它排在 `open()` 之后 ⇒ 排查记录 §38.28 与 `FreqErr.md` 第四批 2 条**已经落盘**、载体没落，正文里"由载体现数"的指针指向空文件。'
    '- **补落遍 part A ' + PARTA_AT + '**：不回写崩溃遍正文，只追加一行登记 + 新落 `hardware/r57_paperwork_tail_a_fix.txt`；'
    '它复算"崩溃遍没改过任何旧行"（拿上一遍在册 md5 对盘上前 N 行现算），并用上一批刚立的**双侧窗口 + 候选池逐格分完**认出崩溃遍那只代落件。',
    '- **订正遍（在册，2026-09-25 13:48:14 那一格）**：只订正代落件的**归属**、不动任何数值；两只件逐行只差 `RUN_AT=` 那一行。',
    '- **本遍 part B ' + RUN_AT + '**：台账五只件一次落齐（todo 第十七遍 / done 第 二十四 节 203+204 / 本文件 / `updates/' + UPDNAME + '` / 烧录须知 〇-补3）。',
    '- **本遍自己抓到的一处新形态**：todo 台账行正文含命令原文里那只被搜串 ⇒ 写盘后"整行子串"口径 = 改前 + 1，"行首前缀"口径不变。'
    '这是 `FreqErr.md` 里那条"命令文本含被搜串 ⇒ 计数自指永不为真"的**第三种形态：被污染的是下一遍的那把尺**。'
    '从本行起 todo 这一格的权威尺 = 前缀口径（等式由本遍载体 `SELFREF` 行写盘后独立回读兑现）。',
    '',
    '### 现场态（' + RUN_AT + ' 现跑）',
    '',
    '- `git rev-list --count origin/main..HEAD` = **' + REV + '**（**未 push**、零历史重写）。',
    '- `git -c core.quotePath=false status --porcelain` = **' + str(len(ST)) + ' 行**（' + str(ST_M) + ' 只 ` M` + ' + str(ST_Q) + ' 只 `??`）；其中 `main/` 侧仍带那只在册的明文件（逐只点名 DROP，见下）。',
    '- 串口枚举 = **' + COMS + '** ⇒ COM14 在位 = **' + str(HAS14) + '**；屏亮 0 次肉眼确认 ⇒ **不播提示音**。',
    '- 归档封界未动：本批所有工具与载体都写在 `hardware/`（`hardware/ht305_sync/` 之外），gen 24 仍是末版，两把尺 FOLD-A / FOLD-B 各自的值随读数与折法一起登在载体 `SEAL` 行。',
    '- 明文半径（登记事实，不抄口令）：四臂里 3 只 + E 臂那 1 只入库件各带 2 处 / 0 处明文（现读在册取证载体 PLAIN 行），`provision_ap.c` 与 dev_log/20260919.md 同案 ⇒ **每轮提交逐只点名 DROP、永不 stage、永不 push、永不删除**。',
    '',
    '### 本批没做（点名）',
    '',
    '- 没换电池 / 没上万用表 / 没接第二块板（三条物理分叉仍在用户侧）；本遍零串口动作、没烧录。',
    '- 没改 `main/` 源码、没重建固件 ⇒ 待烧那只由本遍现读、板上那只没动。',
    '- 没勾 todo 那 17 只未选项（本遍改的是"怎么证明它们没变"，不是它们的内容）。',
    '- 没往 `hardware/ht305_sync/` 落一字节、没新建清单代次；没新建备份根（`diff -rq` 由 #187/#190 那一轮自己判）。',
    '- 没 `git push`、没 amend、零删除；`%TEMP%` 里 D 臂与 E 臂原件仍在原位（它们是抓取时刻的唯一权威）。',
    '- docs 快照第十遍、backups README 第十次读数、提交轮 #9、第 14 代 ht305 同步、mindog 双路复核、空上下文故障检测子AGENT **都在本文件之后** ⇒ 本批不预写它们的数。',
    '',
]
DEV_NEW = '\n'.join(DEV_BODY)
UPD_BODY = [
    '# 2026-09-25 R56/R57：新镜像真机首烧 + 四臂与 E 臂仍全 NACK + 收口批四遍（一遍崩溃、两把尺混装、一道永不成立的门）',
    '',
    '时刻：本文件所有数字写于 ' + RUN_AT + ' 的一次现跑；动作区间 = 2026-09-24 19:59:57（四臂抓取）~ 2026-09-25 14:01:51（崩溃遍落纸）~ 2026-09-25 14:20:31（补落遍 part A 载体）~ 本遍 ' + RUN_HMS + '（part B 台账）。',
    '触发：用户常设指令「继续，深入搜索检修了解，及时同步至服务器 ht305（ssh）。不要问问题直到所有任务结束。」',
    '本批性质：**真机首烧 + 判读 + paperwork** —— 屏侧一个字节没再动（COM14 ' + ('在位' if HAS14 else '不在') + '，本遍现跑 = ' + COMS + '），屏亮仍 0 次肉眼确认 ⇒ 不播提示音。',
    '',
    '## 一句话结论',
    '',
    '- (91) 那条根因**否证一半**：拉住 GPIO1 + 补上电 + 锂电池在位 + 复位起抓，四格全凑齐之后 `0x34` 应答仍然是 **0**（四臂 ' + FOUR_ROWS + ' 行 / E 臂 probe ' + E_PROBE + ' 次）⇒ 按 §14.3 不结案。',
    '- 板上那只 = 待烧那只 = `' + BIN_MD5[:8] + '…`（本遍现读 ' + format(BIN_SIZE, ',') + ' B + boot ELF 前 16 位 ' + BOOT16 + ' == bin[176:184] 复算）⇒ "待烧 = 板上"这条等式从本批起回到原位。',
    '- paperwork 侧交出的是一整套"量具自查"：链式三段混装两把尺（恒红、红在写盘之后 ⇒ 半状态）、微秒判等（永不成立）、同名 FOLD-B 两种折法（命名碰撞）、台账行自指污染下一遍的子串口径。',
    '',
    '## 落点',
    '',
    '- 排查记录 §38.23 / §38.27 / §38.28 在册（崩溃遍落的正文 + 补落遍追加的那行登记，前缀等式与"崩溃遍没改旧行"两把尺都在 part A 载体上）；`FreqErr.md` 第四批 2 条 + 第五批 2 条。',
    '- 台账：`todo.md` 第十七遍（新口径：命令原文 + 本次输出同落纸，对照物 = 上一遍载体输出）；`done.md` 第 二十四 节 203/204；本文件 + `dev_log/20260925.md`；`hardware/烧录须知.md` 〇-补3。',
    '- 取证：`hardware/20260925_R57_E臂判据摘录_v2.txt`、`hardware/r57_paperwork1.txt`、`hardware/r57_paperwork1_fix2.txt`、`hardware/r57_paperwork_tail_a_fix.txt`、本遍 `hardware/r57_paperwork_tail_b.txt`。',
    '- 现场态：`rev-list` = ' + REV + '（未 push）/ `status --porcelain` = ' + str(len(ST)) + ' 行 / 归档 gen 24 末版未动 / 屏侧我方 ' + E_DEN + ' 只。',
    '',
    '## 本批没做（点名）',
    '',
    '- 没换电池 / 没万用表 / 没第二块板；本遍零串口动作、没烧录、没改 `main/` 源码、没重建固件。',
    '- 没往 `hardware/ht305_sync/` 落一字节、没新建清单代次、没新建备份根；没 push、没 amend、零删除。',
    '- docs 快照第十遍、backups README 第十次读数、提交轮 #9、第 14 代同步、mindog 双路复核、空上下文故障检测子AGENT 均在本文件之后 ⇒ 不预写它们的数。',
    '',
]
DEV_NEW_LF = DEV_NEW + '\n'
UPD_NEW = '\n'.join(UPD_BODY) + '\n'
TODO_NEW = TODO_T + '\r\n' + TODO_ROW + '\r\n'
assert TODO_NEW.startswith(TODO_T), 'ABORT: todo.md 前缀等式不成立'
assert '\r\n' + TODO_ROW + '\r\n' == TODO_NEW[len(TODO_T):]

PAYLOADS = {'todo': TODO_ROW, 'done': '\n'.join(DONE_TAIL), 'flash': _ins, 'devlog': DEV_NEW, 'upd': UPD_NEW, 'carrier': ''}
_all = ''.join(PAYLOADS.values())
assert chr(92) not in _all, 'ABORT: 本遍正文含 ASCII 反斜杠'
for _s in ('%s', '%d', '@@', 'None', 'BUIL'):
    assert _s not in _all, 'ABORT: 本遍正文含未替换哨兵 ' + _s


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
assert S0A[2] == SEAL_REF, 'ABORT: 写盘前 FOLD-A 与在册聚合不等 ⇒ 归档目录已被动过，本遍不落'
assert S0A[:2] == S0B[:2], 'ABORT: 两把尺的公共量（只数、字节）互核失败'
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
assert PA[2] != S0A[2] and PB[2] != S0B[2], 'ABORT: SEAL 门没有执行者（内存假名未使两把尺变红）'
assert not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: 阳性对照假名落到盘上了'
_FIRED = 2

_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏，明文门无法自证扫的是真口令'
secret = _secret.group(1).encode('utf-8')
assert len(secret) > 0, 'ABORT: 口令宏体为空串 ⇒ 明文门恒真'
for _k, _v in PAYLOADS.items():
    assert secret not in _v.encode('utf-8'), 'ABORT: 明文口令出现在 ' + _k + ' 正文里'

# ================= 写盘（裁决门全部在这之前）=================
open(TODO, 'w', encoding='utf-8', newline='').write(TODO_NEW)
open(DONE, 'w', encoding='utf-8', newline='').write(DONE_NEW)
open(FLASH, 'w', encoding='utf-8', newline='').write(FLASH_NEW)
open(DEVLOG, 'w', encoding='utf-8', newline='').write(DEV_NEW_LF)
open(UPD, 'w', encoding='utf-8', newline='').write(UPD_NEW)

t_after = rd(TODO)
d_after = rd(DONE)
f_after = rd(FLASH)
v_after = rd(DEVLOG)
u_after = rd(UPD)
assert (t_after, d_after, f_after, v_after, u_after) == (TODO_NEW, DONE_NEW, FLASH_NEW, DEV_NEW_LF, UPD_NEW), 'ABORT: 五只件回读与内存串不等'
assert t_after.count('\n') == t_after.count('\r\n') and '\r' not in d_after and '\r' not in f_after and '\r' not in v_after and '\r' not in u_after, 'ABORT: 写盘后行尾纯度破了'
for _p, _b in ((TODO, t_after), (DONE, d_after), (FLASH, f_after), (DEVLOG, v_after), (UPD, u_after)):
    assert secret not in _b.encode('utf-8') and chr(92) not in _b, 'ABORT: 明文/反斜杠写进了 ' + os.path.basename(_p)
for _p, _t in ((DEVLOG, v_after), (UPD, u_after)):
    assert _t.count('\n') >= 20 and len(_t) > 1000, 'ABORT: 新建文件空壳嫌疑 ' + _p

TL2 = t_after.split('\r\n')
POST_PRE = [i + 1 for i, l in enumerate(TL2) if l.startswith('- [ ]')]
POST_SUB = [i + 1 for i, l in enumerate(TL2) if '- [ ]' in l]
assert POST_PRE == PRE_PRE, 'ABORT: 本遍把前缀口径也动了 ⇒ 第十七遍台账那句"未变"不成立'
assert len(POST_SUB) == len(PRE_SUB) + 1, 'ABORT: 自指等式（改后子串 = 改前子串 + 1）不成立 ⇒ 本遍那句"新形态"没有出处'
NEW_SUB = [x for x in POST_SUB if x not in PRE_SUB]
assert len(NEW_SUB) == 1 and TL2[NEW_SUB[0] - 1].startswith('【**todo 第十七遍台账｜'), 'ABORT: 子串口径多出的那只不是本行 ⇒ 归因错'
DL2 = [l for l in d_after.split('\n') if l.startswith('## ')]
SEC24 = [l for l in d_after.split('\n') if l.startswith('- [x] 203')] + [l for l in d_after.split('\n') if l.startswith('- [x] 204')]
assert len(SEC24) == 2, 'ABORT: 203/204 现读 ' + str(len(SEC24)) + ' 只'

_vm = run((sys.executable, VMRUN))
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=' + str(_vm.returncode)
VM_CARRIER = _mc.group(1).split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_CARRIER)).split('\n') if l.startswith('INNER_ROWS=')][0]
assert VM_CARRIER not in NAMED, 'ABORT: 本遍代落件与上一遍在册同名 ⇒ 归属门失效'
assert len([f for f in POOL if nm_time(f) > LAST_NAMED and f != VM_CARRIER]) == 0, 'ABORT: 上一遍与本遍之间还有未归格的代落件'
S1A, S1B = fold_a(SYNC), fold_b(SYNC)
assert (S0A[0], S0A[1], S0A[2]) == (S1A[0], S1A[1], S1A[2]), 'ABORT: FOLD-A 写盘前后不等（同尺比）'
assert (S0B[0], S0B[1], S0B[2]) == (S1B[0], S1B[1], S1B[2]), 'ABORT: FOLD-B 写盘前后不等（同尺比）'
assert (S0A[0], S0A[1]) == (S1B[0], S1B[1]), 'ABORT: 两把尺公共量在写后破了'

ROWS = []
ROWS.append('R57 收口批 part B  MODE=TAIL-PAPERWORK-B  台账五只件一次落齐')
ROWS.append('本遍现跑于 ' + RUN_AT + '（进入时刻 _T0 取在任何产证动作之前）；本遍零串口动作，只 comports() 只读列口')
ROWS.append('LEDGER 名单格（§38.24 换代后的新口径：命令原文 + 本次输出同落纸，对照物 = 上一遍载体输出）：本遍现跑前缀口径 = ' + str(len(PRE_PRE)) + ' 只，行号 = ' +
            ' '.join(str(x) for x in PRE_PRE) + '；上一遍载体 hardware/' + os.path.basename(LEDGER_CAR) + ' 第 ' + str(_led[0] + 1) + ' 行在册 = ' +
            ' '.join(str(x) for x in CAR_LIST) + '（只数 ' + str(CAR_N) + '）⇒ 逐位相等 = True，新口径下第 2 次现跑未变（第 1 次 = §38.24 那一遍）')
ROWS.append('SELFREF 两把尺第一次分叉由本遍自己造成（现算，不是叙述）：改前 前缀 ' + str(len(PRE_PRE)) + ' = 子串 ' + str(len(PRE_SUB)) +
            '（逐位相等 = True）；写盘后独立回读 前缀 = ' + str(len(POST_PRE)) + '（未动 = True，本行以方括号汉字起头不匹配前缀）、子串 = ' + str(len(POST_SUB)) +
            ' = 改前 + 1 = True；多出的那一行号 = ' + str(NEW_SUB[0]) + '，现读该行起头 = todo 第十七遍台账那句 = True ⇒ 命令文本含被搜串这一族第三种形态：**被污染的是下一遍那把尺**，从本行起前缀口径为权威')
ROWS.append('IDENTITY 待烧 = 板上（本遍现算）：' + BIN + ' = ' + format(BIN_SIZE, ',') + ' B / md5 ' + BIN_MD5 +
            '（32 个十六进制字符 = md5，不是 sha256）；boot ELF 前 16 位 ' + BOOT16 + ' == bin[176:184] = ' + BIN16 + ' = True ⇒ §38.23 之前那条分裂已合')
ROWS.append('ARMS 屏侧读数出处（现读取证件与正文，不转抄）：E 臂 probe# ' + E_PROBE + ' 次 / 应答 ' + E_ACK + ' 条 / 我方分母 ' + E_DEN +
            ' 只；四臂在册 ' + FOUR_ROWS + ' 条 0x34 行、应答 0 条、VERDICT=FOUR-ARMS-ALL-NACK（grep 该字样 = True）⇒ 全 NACK 不定案')
ROWS.append('WRITE 五只件写盘（裁决门全在 open() 之前）：todo 追加 1 行（CRLF）/ done 追加 ' + str(len(DONE_TAIL)) + ' 行（LF，新节 二十四 + 203/204）/ '
            '烧录须知 插入 ' + str(len(FLASH_TAIL)) + ' 行（LF，插在「' + FLASH_ANCHOR[:11] + '」之前，replace 还原等式 = True）/ dev_log 与 updates 各新建 1 只（LF，槽位进入前均为空）')
ROWS.append('VM 本遍现跑内层复核器代落：rc=0 / ' + INNER + ' / 代落件 = hardware/' + VM_CARRIER + '；今日池子 ' + str(len(POOL)) +
            ' 只 = 上一遍载体在册点名 ' + str(len([f for f in POOL if f in NAMED])) + ' 只 + 本遍 1 只，未归格 0 只 = True')
ROWS.append('FIELD 现跑：串口枚举 = ' + COMS + ' ⇒ COM14 在位 = ' + str(HAS14) + ' / rev-list = ' + REV + '（未 push）/ status --porcelain = ' +
            str(len(ST)) + ' 行（' + str(ST_M) + ' 只 M + ' + str(ST_Q) + ' 只 ??）')
ROWS.append('SEAL 两条同尺比较 + 一条公共量互核（定义随读数落盘：FOLD-A = walk 序只折各文件 content 摘要；FOLD-B = 相对路径冒号摘要、排序后以换行连接再折）。'
            'FOLD-A 写前 (' + str(S0A[0]) + ', ' + str(S0A[1]) + ', ' + S0A[2] + ') == 写后 (' + str(S1A[0]) + ', ' + str(S1A[1]) + ', ' + S1A[2] + ') = True；'
            'FOLD-B 写前 ' + S0B[2] + ' == 写后 ' + S1B[2] + ' = True；两把尺只数字节互核 = True；FOLD-A 逐字复现在册 ' + SEAL_REF + ' = True；'
            '内存假名（' + PROBE + '，只在内存，盘上无那只 = True）使两把尺双红 = 2 ⇒ 本批未往 hardware/ht305_sync/ 落一字节，gen 24 仍是末版')
ROWS.append('GATE 本遍各道门：自身 ast.parse / 缺件 10 只 / 空槽 4 格（载体 + dev_log + updates + 两处标题字样）/ 行尾纯度按各自口径（todo = CRLF，done 与 dev_log 与 updates 与烧录须知 = LF）/ '
            'todo 与 done 前缀等式 / 烧录须知 插入还原等式 / 反斜杠 / 明文（口令只从宏体读出做比对，不进正文与命令文本）/ 哨兵 5 只 / '
            '名单对照上一遍载体输出 / 代落件池子归属 / 身份等式 / 自指三关系式 / 回读等值 5 只 / 新建件空壳闸 / SEAL 两条同尺 + 公共量 = 全 0 破；'
            'ARMS_FIRED（真红计数）= ' + str(_FIRED) + '，全部来自内存假名（FOLD-A 与 FOLD-B 各 1）；本遍写盘前自纠 0 次')
ROWS.append('LAND 写盘后独立回读现数（完成态数字在这里数，本遍正文不预写）：todo = ' + str(len(TL2) - 1) + ' 行 / ' + str(os.path.getsize(TODO)) +
            ' B / md5 ' + md5b(t_after.encode('utf-8')) + '；done = ' + str(len(d_after.rstrip(chr(10)).split(chr(10)))) + ' 行 / ' + str(os.path.getsize(DONE)) +
            ' B / md5 ' + md5b(d_after.encode('utf-8')) + ' / 末节号现读 = ' + DL2[-1][3:7] + ' / 203 与 204 各 1 行 = True；'
            '烧录须知 = ' + str(len(f_after.rstrip(chr(10)).split(chr(10)))) + ' 行 / ' + str(os.path.getsize(FLASH)) + ' B；'
            'dev_log/20260925.md = ' + str(len(v_after.rstrip(chr(10)).split(chr(10)))) + ' 行 / ' + str(os.path.getsize(DEVLOG)) + ' B；'
            'updates/' + UPDNAME + ' = ' + str(len(u_after.rstrip(chr(10)).split(chr(10)))) + ' 行 / ' + str(os.path.getsize(UPD)) + ' B')
ROWS.append('WITNESS 本遍现读 md5（前 12 位）：本遍工具 ' + md5b(rb(TOOL))[:12] + ' / part A 载体 ' + md5b(rb(CARA))[:12] + ' / 名单对照载体 ' +
            md5b(rb(LEDGER_CAR))[:12] + ' / E 臂取证 v2 ' + md5b(rb(CAR_E2))[:12] + ' / 待烧 bin ' + BIN_MD5[:12] + ' / todo(改前) ' +
            md5b(TODO_T.encode('utf-8'))[:12] + ' / done(改前) ' + md5b(DONE_T.encode('utf-8'))[:12] + ' / 烧录须知(改前) ' + md5b(FLASH_T.encode('utf-8'))[:12])
ROWS.append('NOTDONE 本批没做（点名）：没换电池 / 没万用表 / 没第二块板 / 没碰串口（只 comports() 列口）/ 没烧录 / 没改 main/ 源码 / 没重建固件 / '
            '没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / 没新建备份根 / 没 push、没 amend / 零删除（含 %TEMP% 里 D 臂与 E 臂原件）/ '
            '没勾 todo 那 17 只未选项 / 屏亮仍 0 次肉眼确认 ⇒ 不播提示音 / docs 快照第十遍、backups README 第十次读数、提交轮 #9、第 14 代同步、'
            'mindog 双路复核、空上下文故障检测子AGENT 都在本件之后 ⇒ 本遍不预写它们的数')
ROWS.append('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(ROWS)) + ' 行（含本行）')

body = '\n'.join(ROWS) + '\n'
assert secret not in body.encode('utf-8') and chr(92) not in body, 'ABORT: 载体正文含明文/反斜杠'
PAYLOADS['carrier'] = body
open(CARRIER, 'w', encoding='utf-8', newline='').write(body)
_c = rd(CARRIER)
assert _c == body and '\r' not in _c, 'ABORT: 载体回读不等或非纯 LF'
print('CARRIER hardware/' + os.path.basename(CARRIER), len(_c.rstrip('\n').split('\n')), 'rows', os.path.getsize(CARRIER), 'B')
print('TODO', len(TL2) - 1, 'DONE', len(d_after.rstrip('\n').split('\n')), 'FLASH', len(f_after.rstrip('\n').split('\n')))
print('PRE', len(PRE_PRE), 'POSTPRE', len(POST_PRE), 'POSTSUB', len(POST_SUB), 'SELFROW', NEW_SUB[0])
print('SEAL A', S1A[0], S1A[1], S1A[2], 'B', S1B[0], S1B[1], S1B[2])
print('VM', VM_CARRIER, 'POOL', len(POOL), 'COM14', HAS14, 'REV', REV, 'BIN', BIN_MD5[:8], BOOT16)
print('RUN_AT', RUN_AT)
