# R56 第三批（台账里那串"未勾选名单"复算不成立）的落地器：一次调用落 3 只文件
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 新增 §38.24
#   ② FreqErr.md（CRLF）—— 本批 2 条新错误类型 + 台账行（两把尺在最终串上现算，(99)）
#   ③ hardware/r56_paperwork3.txt（LF，载体，本脚本自己落盘，在归档目录之外）
# 触发：写 todo 第十七遍之前，我照惯例要重跑那两条"老命令"。第一条的**只数**仍是 17，
#   而**名单**从 `44 46 48 …` 变成 `107 111 115 …` ⇒ 于是去 git 历史里找那串旧数的出处（**全史每一版都不等**），
#   结论：那串数**不可复算**，它在 16 遍里是被复述而不是被重跑。本批就是把这件事登记 + 换口径。
# 幂等：`### 38.24` 已在盘上 ⇒ MODE=REWROTE_CARRIER_ONLY，一字节都不写那两只 CRLF 文件。
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
TODO = os.path.join(REPO, 'todo.md')
MAN = os.path.join(SYNC, 'MANIFEST.txt')
GLOG = os.path.join(SYNC, 'evidence', 'manifest_gen_log.txt')
P2 = os.path.join(HDIR, 'r56_paperwork2.py')
TS = '[0-9-]{10} [0-9:]{8}'
SEC = '### 38.24'
SECNUM = '38.24'
FSEC = '## 2026-09-24（R56 第三批'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
N_ENTRY = 2

_cands = ['r56_paperwork3.txt'] + ['r56_paperwork3_%d.txt' % i for i in range(2, 60)]
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


# ---------- 本批要复核的那把尺：命令原文 + 输出，一起现跑、一起落纸 ----------
# 两条在册命令的**渲染形式**在本批改成了 `-F`（定长串）—— 因为落地文本里不许出现反斜杠（§38.18 那一族），
# 而正则写法 `^- \[ \]` 必带反斜杠。换渲染的正当性由下面的 EQUIV 行现跑证明：两种匹配在同一只文件上逐位等值。
UNCHECK = "grep -nF -- '- [ ]' todo.md"
UNITS = "grep -cF -- '- [ ]' todo.md"
MARK = '- [ ]'


def _unt(path_text, pred):
    return [i + 1 for i, l in enumerate(lf(path_text).split('\n')) if pred(l)]


def _unt_pre(t):
    return _unt(t, lambda l: l.startswith(MARK))


def _unt_sub(t):
    return _unt(t, lambda l: MARK in l)


todo_disk = rd(TODO)
LIST_NOW = _unt_pre(todo_disk)
EQUIV = _unt_sub(todo_disk) == LIST_NOW
assert EQUIV, 'ABORT: 前缀匹配与子串匹配给出的名单不等 ⇒ -F 渲染换了判据，本批不许落'
CNT_NOW = len(LIST_NOW)
HEAD_T = subprocess.run(['git', 'show', 'HEAD:todo.md'], cwd=REPO, capture_output=True,
                        text=True, encoding='utf-8', errors='replace').stdout
assert HEAD_T.strip(), 'ABORT: git show HEAD:todo.md 空 ⇒ 换尺没做完'
LIST_HEAD = _unt_pre(HEAD_T)
_head_md5 = hashlib.md5(lf(HEAD_T).encode('utf-8')).hexdigest()[:8]
# 旧那串在册名单（从 todo.md 正文里逐字抓，不是我抄的）
REG = re.findall(r'未勾选名单与只数.*?（仍 `([0-9 ]+)` / \*\*(\d+)\*\*', lf(todo_disk))
assert REG, 'ABORT: todo.md 里抓不到"未勾选名单与只数"那句式 ⇒ 本批的对照物不存在'
LAST = REG[-1]
LIST_REG = [int(x) for x in LAST[0].split()]
CNT_REG = int(LAST[1])
OLD_STR = ' '.join(map(str, LIST_REG))
assert len(set(r[0] for r in REG)) == 1, 'ABORT: 历次登记的名单串并非同一串 ⇒ "整串换过"这句要重查'
assert len(set(r[1] for r in REG)) == 1, 'ABORT: 历次登记的只数并非同一个数'
_TL = lf(todo_disk).split('\n')
_RLN = [i + 1 for i, l in enumerate(_TL) if OLD_STR in l]
RECITE = len(_RLN)
NREG = len(REG)
assert RECITE >= NREG >= 1, 'ABORT: 在册登记行数 %d < 句式命中 %d ⇒ 两个口径有一个是假的' % (RECITE, NREG)
RECITE17 = len([i for i in _RLN if '**%d**' % CNT_NOW in _TL[i - 1]])
CN = dict(zip('零一二三四五六七八九', range(10)))


def cn2i(s):
    if '十' not in s:
        return CN[s]
    a, _, b = s.partition('十')
    return (CN[a] if a else 1) * 10 + (CN[b] if b else 0)


def i2cn(n):
    d = '零一二三四五六七八九'
    if n < 10:
        return d[n]
    if n < 20:
        return '十' + (d[n % 10] if n % 10 else '')
    return d[n // 10] + '十' + (d[n % 10] if n % 10 else '')


ORDS = [cn2i(x) for x in re.findall(r'第([一二三四五六七八九十]+)遍', lf(todo_disk))]
assert ORDS, 'ABORT: todo.md 里没有"第 N 遍"序数 ⇒ "本遍是第 X 遍"这句没有出处'
LAST_PASS, NEXT_PASS = max(ORDS), i2cn(max(ORDS) + 1)

# ---------- 同族的两处弱判据：本遍真跑一遍，只点名"它们是同族"，不背书 ----------
DONE = os.path.join(REPO, 'done.md')
done_lines = lf(rd(DONE)).split('\n')
DH = [(i + 1, l) for i, l in enumerate(done_lines) if l.startswith('## ')]
assert len(DH) >= 20, 'ABORT: done.md 的 `^## ` 标题只 %d 只 ⇒ 末节号那格的口径不对' % len(DH)
DONE_SEC = re.match(r'^## +([^、\s]+)', DH[-1][1]).group(1)
TASKS = [int(m.group(1)) for l in done_lines for m in [re.match(r'- \[x\] (\d+)', l)] if m]
T_MAX = max(TASKS)


def _done_cnt(n):
    s = '- [x] %s' % n
    pre = [i + 1 for i, l in enumerate(done_lines) if l.startswith(s)]
    sub = [i + 1 for i, l in enumerate(done_lines) if s in l]
    assert pre == sub and len(pre) == 1, 'ABORT: done.md 里 %r 两把尺不等或不是 1（%s / %s）' % (s, pre, sub)
    return len(pre), pre == sub


T_PREV = T_MAX - 1
(DONE_N1, E1), (DONE_N2, E2) = _done_cnt(T_PREV), _done_cnt(T_MAX)
DONE_EQUIV = E1 and E2
CMD_SEC = 'grep -n "^## " done.md | tail -1'
CMD_N1 = "grep -cF -- '- [x] %s' done.md" % T_PREV
CMD_N2 = "grep -cF -- '- [x] %s' done.md" % T_MAX

DRIFT = len([k for k in range(max(len(LIST_REG), len(LIST_NOW)))
             if (LIST_REG[k] if k < len(LIST_REG) else None) != (LIST_NOW[k] if k < len(LIST_NOW) else None)])
assert CNT_REG == CNT_NOW, 'ABORT: 只数就不等了（在册 %d vs 现跑 %d）⇒ 本批那句"只数没变"要改' % (CNT_REG, CNT_NOW)
assert DRIFT == len(LIST_NOW), 'ABORT: 现跑名单与在册名单竟有重合位（%d/%d）⇒ "整串换过"这句要重写' % (
    len(LIST_NOW) - DRIFT, len(LIST_NOW))
# 全部历史版 todo.md 里有没有哪一版真产出过在册那串数
# （原写法是 `-80`，本遍第一次跑就 ABORT："rev-list -80 只拿到 32 版" ⇒ 本仓库总共 32 版，
#   那句"最近 80 版无一命中"的**半径**本来就是假的。改成不限数扫全史，半径由 len(_rev) 现算。）
_rev = subprocess.run(['git', 'rev-list', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.split()
HIT_REV = []
for r in _rev:
    t = subprocess.run(['git', 'show', r + ':todo.md'], cwd=REPO, capture_output=True,
                       text=True, encoding='utf-8', errors='replace').stdout
    if _unt_pre(t) == LIST_REG:
        HIT_REV.append(r[:7])
assert len(_rev) >= 2, 'ABORT: rev-list HEAD 只拿到 %d 版 ⇒ "全史无一命中"这句没有半径' % len(_rev)
CMD_REV = 'git rev-list HEAD'
REV_LIST_NOW = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
assert REV_LIST_NOW.isdigit()

# ---------- 进入时现读两只 CRLF 文件 + 幂等闸 ----------
for p in (FREQ, DOC):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 追加会造出混行尾' % p
freq_disk, doc_disk = rd(FREQ), rd(DOC)
_hf, _hd = starts(freq_disk, FSEC), starts(doc_disk, SEC)
assert len(_hf) <= 1 and len(_hd) <= 1, 'ABORT: 本批标题命中 %d / %d 处 ⇒ 已重复追加' % (len(_hf), len(_hd))
MODE = 'REWROTE_CARRIER_ONLY' if _hf or _hd else 'LANDED_NOW'
assert bool(_hf) == bool(_hd), 'ABORT: §38.24 与 FreqErr 本批节"存在性"不一致 ⇒ 上一遍落了一半'
_fl = lf(freq_disk).split('\n')
if MODE == 'REWROTE_CARRIER_ONLY':
    _led = [i for i, l in enumerate(_fl) if l.startswith('> **【') and '落地｜R56 第三批 %d 条】**' % N_ENTRY in l]
    assert len(_led) == 1 and _led[0] > _hf[0], 'ABORT: 本批台账行命中 %d 只 / 不在本批标题之下' % len(_led)
    freq_pre = '\n'.join(_fl[:_hf[0]]).rstrip('\n') + '\n'
    doc_pre = '\n'.join(lf(doc_disk).split('\n')[:_hd[0]]).rstrip('\n') + '\n'
else:
    freq_pre, doc_pre = freq_disk, doc_disk
K0, L0 = kinds(freq_pre), nl(freq_pre)
DOC_ROWS0, DOC_B0 = nl(doc_pre), len(doc_pre.encode('utf-8'))
DOC_B0D = len(crlf(doc_pre).encode('utf-8'))   # 落盘口径（行尾 CRLF）的改前字节数 —— 与"终态"同一把尺
_rec = lf(doc_pre).split('\n')
GLUE_F = GLUE_D = TAIL_KF = TAIL_D = 0
_tail_f = []

# ---------- 取证载体（上一批那只）逐字现读，本批正文只引用它、不重算它 ----------
EV2 = os.path.join(HDIR, 'r56_paperwork2.txt')
assert os.path.isfile(EV2), 'ABORT: 上一批载体不在 ⇒ §38.24 那句"paperwork 载体"是假指针'
ev2 = rd(EV2)
EV2_AT = re.search(r'本遍现跑于 (' + TS + ')', ev2).group(1)
EV2_CITE = [l for l in ev2.split('\n') if l.startswith('CITE ')][0]
EV2_ID = [l for l in ev2.split('\n') if l.startswith('IDENTITY ')][0]

# ---------- 封界门 + 只在内存的阳性对照（承前两批，同一条判据） ----------
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
PROBE = 'evidence/SEAL_VIOLATION_PROBE3.txt'
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

# ---------- FreqErr 本批段（正文 2 条）----------
FREQ_SEC = """@H@

> 一句话总纲：本批屏侧一个字节没动（没烧录、没碰串口，本遍只 `comports()` 只读列口 = @COM@），
> 抓到的两条都在**我自己那把"复跑老命令"的尺子**上：它的只数一直对，它的名单第一次现跑就整串换了。

[错误类型] **台账里"照惯例复跑那两条老命令"的那一格，连续 @RECITE@ 次登记的是**记忆里的那串数**而不是命令的输出 ⇒ 本遍第一次把命令原文与输出一起落纸，就发现"未勾选名单"整串换过（在册 `@REG_SHORT@ …` / 现跑 `@NOW_SHORT@ …`），只有只数 @CNT@ 不变**
→ 症状：每一遍正文都写着「名单与只数**第 N 次逐字未变**」，而这句话的产生方式没人登记过。今天（@T@）我要写第 @NEXT_PASS@ 遍，先跑了 `@UNITS@` = **@CNT@** 与 `@UNCHECK@` ⇒ 只数对上、**位置一只都对不上**（重合位 @OVERLAP@ / @CNT@）；再去 `@CMD_REV@` 里找那串旧数的出处，**@REV_N@ 版 todo.md 无一产出过它**（命中版本 = @HIT@）。
→ 形状：与 (89)「台账自己的序数计数不复算就就地降级」同族，但多一层更糟的：**它看起来一直在复算**。只数 @CNT@ 在 @RECITE17@ 次登记里一次没跳过，正是"命令确实跑过"的样子 —— 而只数恰恰是这个判据里**唯一没变的那一维**，所以它是复述还是复算，只数回答不了。
→ 为什么它危险：这条判据的全部作用是"证明 `todo.md` 的阻塞项没有被偷偷改掉"。名单换了位置本身可能无害（前面批次确实往那 @CNT@ 只上面插过行），但只要"未变"是复述来的，它就**一次也没证明过**任何东西；更坏的是它给每一批都盖了个"老命令都跑过、都未变"的章，那章会被后面的批次当**基准**引用。
→ 正确做法：①凡"复跑某命令"的格子，命令原文与**本次输出**必须同时进载体（本批载体 `LEDGER` 行就是这个形状），正文只引用载体；②比较对象是**上一遍载体的输出**，不是上一遍正文里那句"未变"；③"只数不变"与"名单不变"是两格，只登记前者时禁止写后者；④对已经复述出去的旧数，按 (89) 就地降级为**不可复算的旧快照**（本批起：`@REG_SHORT@ …` 这串作废，不再作为对照物），并在同一节点名它的替代口径；⑤一次横向自查：本仓库另两处也用"第 N 次逐字未变"句式（`done.md` 末节号、以及 §38.22 那种"两把尺互不可换算"），它们的产生方式在本批载体里已改为现跑现抄。
→ **同族**：项目记忆 (89)、(76)"命中 0 ≠ 干净"、(41)"报两侧不一致先读产生那个数的命令"；`feedback-verifiable-acceptance.md`"数字连算法与漏判""读数不落盘等于没跑"。

[错误类型] **一条断言一旦被写进"台账"这种会被复述的位置，它的真假判定就退化成"上一次是否有人写过它是真" ⇒ 前 @LAST_PASS@ 遍里没有任何一道闸检查过它，因为它是**散文**而不是判据**
→ 症状：本批同一批里第二次撞到：上一批（§38.23）我把"全部现算、无手抄"写在文件头部，而它罩着的数字是手抄的；这一批是"逐字未变"写在正文里，罩着的是一串从没重跑过的数。两次都是**元断言没有执行者**。
→ 为什么它危险：判据型断言（assert / 门 / rc）会自然复跑，散文型断言只在被人读到时才"生效"。台账正是**只被读、不被跑**的那种位置；而它写的又是全仓库最像取证的话（"第 N 次""逐字""未变"）。
→ 正确做法：①把散文断言改写成可跑的形状：本批起 todo 台账那一格必须带 `命令 = 输出`；②落地脚本里给这类格子装断言（本遍 = 进脚本时先 `re.findall` 抓在册名单与只数，若现跑输出与它不等 ⇒ 本批必须登记这件事才允许写盘）；③"未变"类句子一律带上"与哪一只载体里的哪一行比"；④元断言（"全部现算""逐字未变""无一例外"）在同批必须做一次反向对照：从它罩着的对象里**随机抽一只去重跑**，跑不动就删掉那句。
→ **同族**：本批上一条、项目记忆 (95)"落地脚本三步序"、(102) 一族"规矩要有执行者"；`feedback-verifiable-acceptance.md`"计数型安全门必须配阳性对照""不许拿重跑链把 RED 洗成 GREEN"（本批没有把这条洗成"其实名单也差不多"，而是降级 + 换口径）。
""".replace('@H@', FSEC + '：todo 台账那串"未勾选名单"复算不成立）新增 %d 条（根族：**一把被登记了 @RECITE@ 次的尺子，第一次现跑就换了名单**）' % N_ENTRY)

# ---------- 排查记录 §38.24 ----------
SEC_BODY = """@SEC@ R56 第三批 = 台账里那串"未勾选名单"**第一次现跑就整串换过**（本遍现跑于 @T@；**没烧录、没碰串口、没 push、屏侧零进展**）

- **触发（是我要落第 @NEXT_PASS@ 遍台账，不是我去找错）**：`todo.md` 正文里逐字含在册那串名单的一共 **@RECITE@ 行**（首行 @REC_FIRST@、末行 @REC_LAST@），其中写成「两条老命令 ⇒ 未勾选名单与只数**第 N 次逐字未变**（仍 … / **@CNT@**）」这个句式的 = **@NREG@ 次**。落第 @NEXT_PASS@ 遍之前我照例要重跑，`@UNITS@` = **@CNT@**（与在册只数等），`@UNCHECK@` = **@NOW@** ⇒ 与在册那串 **@REG@** **一只都对不上**（重合位 @OVERLAP@ / @CNT@）。
- **它是不是"漂了"？我去了历史里查**：`@CMD_REV@` 逐版跑同一条命令 ⇒ **@REV_N@ 版里没有一版产出过在册那串数**（命中 = @HIT@），而 `git show HEAD:todo.md` 的输出与工作树**逐字同值**（两把 md5 同 = `@TREE_MD5@` / `@HEAD_MD5@`，且两串名单相等 = @SAME@）⇒ 不是"未提交的改动把行号挤动了"，那串数在**任何一版上都不成立** = 它是被复述的，不是被跑出来的。
- **只数为什么一直对**：那 @CNT@ 只未选项本身没被增删，而 @RECITE17@ / @RECITE@ 行在册登记写的都是同一个 @CNT@。**只数恰好是这条判据里唯一没动的维度** ⇒ 拿它当"命令跑过了"的证据，等于拿一条对任何名单都成立的性质去证明一件具体的事。从本行起：这条判据的对照物是**名单**，只数只是它的副产品。
- **口径换代（本行起生效）**：①在册那串 `@REG_SHORT@ …` **就地降级为不可复算的旧快照**，此后不许再作为"未变"的对照物；②新口径 = 台账格子必须同时带**命令原文 + 本次输出**，正文只引用载体（本批 = 载体 `LEDGER` 行）；③比较对象 = **上一遍载体的输出**，不是上一遍正文里那句"未变"。
- **命令渲染换了形，判据没换（本遍现跑两把尺等值）**：在册那两条写的是转义正则（正则里标一个方括号要一个反斜杠），而落地文本禁反斜杠（§38.18 那一族）⇒ 本批起改用定长串匹配 = `@UNCHECK@`。等值不是我说的：同一遍里按"行首前缀"与"整行子串"两种口径各数一次，两串名单**逐位相等** = @EQUIV@（若子串口径多出一只，本脚本在进入时就 ABORT 了）。
- **同族另两处一并核过（避免"只修被抓到的那一处"）**：`@CMD_SEC@` 末节号现跑 = **@DONE_SEC@**，`@CMD_N1@` = **@DONE_N1@**、`@CMD_N2@` = **@DONE_N2@**（两格都是 1，且"前缀 / 子串"两种匹配在 `done.md` 上也逐位等值，见载体 `DONE` 行）⇒ 这三格本遍是真跑的、结果与在册一致；**但同族风险已确认**：它们同样是"只数 / 末节号"型的弱判据，所以本批把 §38.24 的登记范围写成"这一格换了口径"，而不是"这些都可靠"。
- **与上一批的分界（不许把两批混成一批）**：§38.23 落盘于 @EV2_AT@（载体 = `hardware/r56_paperwork2.txt`），它的在册行包括：`@EV2_ID_SHORT@`。本批**不重跑四臂、不重烧、不碰串口**，只对台账这一格换口径 ⇒ 屏侧读数全部停在 §38.23 那一遍。
- **本节没做（点名，绑定执行者）**：①**本遍**（paperwork，@T@）零串口动作；本遍列口 = `@COM@`；②没动那 @CNT@ 只未选项本身（既没勾掉也没新增）——本批改的是**怎么证明它们没变**，不是它们的内容；③没烧录 / 没换电池 / 没万用表 / 没第二块板（那两条物理分叉仍在用户侧，见 §38.23 的 a/b）；④没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 只在内存假名 `@PROBE@` = 本遍 `@ARMS@`），也没新建清单代次 ⇒ gen 24 仍是末版（`TOTAL @RT@` / `@RB@ B` / BOM `@RBOM@`，末版 @SEAL_AT@，本遍复核 `rc=@VRC@`，载体 `@VM_CARRIER@`）；⑤没 push、没 amend、零删除；⑥docs 快照第十遍、backups README 第十次读数、提交轮 #9、第 14 代同步都在本节之后 ⇒ 本遍不预写它们的数。
> 本节对应 `FreqErr.md` 那 @N@ 条在册（标题前缀 `@FSEC@`），取证载体 = `hardware/@CAR@`（本遍写的那一只：LEDGER 行（命令 + 输出 + 在册名单 + 重合位）/ HIST 行（@REV_N@ 版扫描）/ SEAL + GATE + VM + POSCTL + WITNESS）。
""".replace('@SEC@', SEC).replace('@T@', NOW_AT).replace('@N@', str(N_ENTRY))

SUBS = {'@T@': NOW_AT,
        '@CAR@': os.path.basename(CARRIER), '@COM@': _com, '@PROBE@': PROBE, '@ARMS@': ARMS_FIRED,
        '@T@': NOW_AT,
        '@FSEC@': FSEC, '@UNCHECK@': UNCHECK, '@UNITS@': UNITS, '@CNT@': str(CNT_NOW),
        '@REG@': ' '.join(str(x) for x in LIST_REG), '@REG_SHORT@': ' '.join(str(x) for x in LIST_REG[:6]),
        '@NOW@': ' '.join(str(x) for x in LIST_NOW), '@NOW_SHORT@': ' '.join(str(x) for x in LIST_NOW[:6]),
        '@REV_N@': str(len(_rev)), '@HIT@': (' + '.join(HIT_REV) if HIT_REV else '无'),
        '@SAME@': str(LIST_HEAD == LIST_NOW), '@TREE_MD5@': md5_(TODO), '@HEAD_MD5@': _head_md5,
        '@EQUIV@': str(EQUIV), '@OVERLAP@': str(len(LIST_NOW) - DRIFT), '@CMD_REV@': CMD_REV,
        '@RECITE@': str(RECITE), '@RECITE17@': str(RECITE17), '@NREG@': str(NREG),
        '@REC_FIRST@': str(_RLN[0]), '@REC_LAST@': str(_RLN[-1]),
        '@NEXT_PASS@': NEXT_PASS, '@LAST_PASS@': str(LAST_PASS),
        '@VRC@': str(_v.returncode), '@VM_CARRIER@': VM_CARRIER,
        '@SEAL_AT@': SEAL_AT, '@RT@': str(len(_rows)), '@RB@': money(int(GEN_BYTES)), '@RBOM@': GEN_BOM,
        '@CMD_SEC@': CMD_SEC, '@CMD_N1@': CMD_N1, '@CMD_N2@': CMD_N2,
        '@T1@': str(T_PREV), '@T2@': str(T_MAX), '@DONE_SEC@': DONE_SEC,
        '@DONE_N1@': str(DONE_N1), '@DONE_N2@': str(DONE_N2),
        '@EV2_AT@': EV2_AT, '@EV2_ID_SHORT@': EV2_ID[:96] + '…'}
for _k, _val in SUBS.items():
    SEC_BODY = SEC_BODY.replace(_k, _val)
    FREQ_SEC = FREQ_SEC.replace(_k, _val)

LED_TPL = ("> **【@T@ 落地｜R56 第三批 @N@ 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：全文 `^[错误类型]` 条数 = **@K0@**、"
           "`wc -l` 行数 = **@L0@**；追加之后现算，**口径 = 含本台账行自身的最终字节串（本批窗口内，不含后续批次）**："
           "`^[错误类型]` 条数 = **@K1@**、`wc -l` 行数 = **@L1@**（两把尺都在最终串上数 —— (99)）。"
           "本批两条 = **①台账里那串被逐字登记了 @RECITE@ 次的\"未勾选名单\"第一次现跑就整串换过（只数 @CNT@ 不变而 @CNT@ 只位置全错，`@CMD_REV@` 里 @REV_N@ 版无一产出过它）；"
           "②散文型元断言（\"第 N 次逐字未变\"）没有执行者 ⇒ 判据退化成\"上一次有人写过它是真\"**"
           "（正文登记在排查记录 §@SN@，取证载体在 `hardware/@CAR@`；新口径 = 命令原文 + 本次输出一起落纸）。")

LED_TS = NOW_AT if MODE == 'LANDED_NOW' else re.match(
    r'^> \*\*【(' + TS + ')', _fl[_led[0]]).group(1)


def build(freq_pre_t, doc_pre_t):
    base = lf(freq_pre_t).rstrip('\n') + '\n\n' + lf(FREQ_SEC) + '\n'
    k1, l1 = kinds(base), nl(base) + 1
    led = LED_TPL
    for _k, _val in {'@T@': LED_TS, '@N@': str(N_ENTRY), '@K0@': str(K0), '@L0@': str(L0),
                     '@K1@': str(k1), '@L1@': str(l1), '@CAR@': SUBS['@CAR@'],
                     '@SN@': SECNUM, '@RECITE@': SUBS['@RECITE@'], '@CNT@': SUBS['@CNT@'],
                     '@CMD_REV@': CMD_REV,
                     '@REG_SHORT@': SUBS['@REG_SHORT@'], '@REV_N@': SUBS['@REV_N@']}.items():
        led = led.replace(_k, _val)
    assert not re.search(r'@[A-Za-z0-9_]+@', led), 'ABORT: 台账行还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', led)[:5]
    assert chr(92) not in led, 'ABORT: 台账行含反斜杠（§38.18 那一族）'
    final = crlf(base + led + '\n')
    assert kinds(final) == k1 and nl(final) == l1, 'ABORT: 台账行在册的两把尺与最终串不等 ⇒ (99) 那句是假话'
    assert '§' + SECNUM in led, 'ABORT: 台账行没点名本节节号'
    dfin = crlf(lf(doc_pre_t).rstrip('\n') + '\n\n' + lf(SEC_BODY))
    return final, dfin


assert not re.search(r'@[A-Za-z0-9_]+@', SEC_BODY), 'ABORT: §38.24 里还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', SEC_BODY)[:5]
assert not re.search(r'@[A-Za-z0-9_]+@', FREQ_SEC), 'ABORT: FreqErr 本批段还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', FREQ_SEC)[:5]
assert 'zizhao1' not in SEC_BODY and 'zizhao1' not in FREQ_SEC, 'ABORT: 正文含 SoftAP 口令明文'
_SECTREF = re.compile(r'§(\d+(?:\.\d+)+)')
for _t, _tag in ((SEC_BODY, '§38.24'), (FREQ_SEC, 'FreqErr 本批段')):
    for _n in sorted(set(_SECTREF.findall(_t))):
        if _n == SECNUM:
            continue
        assert any(re.match(r'#{2,4} +' + re.escape(_n) + r'(?![0-9])', l) for l in _rec), \
            'ABORT: %s 引用了 §%s，而改前排查记录里没有这个标题行' % (_tag, _n)
    _dash = sorted(set(re.findall(r'§(\d+(?:-\d+)+)', _t)))
    assert not _dash, 'ABORT: %s 里出现 dash 式节号 %s（本批正文不再引用 v1 那句假指针，出现即错）' % (_tag, _dash)

if MODE == 'LANDED_NOW':
    freq_final, doc_final = build(freq_pre, doc_pre)
    assert re.match(r'^> \*\*【' + TS + ' 落地｜R56 第三批', lf(freq_final).split('\n')[-2]), 'ABORT: 台账行没落在末行前'
else:
    freq_final, doc_final = freq_disk, doc_disk
    _lt = _fl[_led[0]]
    _m = re.search(r'条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*.*?条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*', _lt)
    assert _m and (K0, L0) == (int(_m.group(1)), int(_m.group(2))), 'ABORT: 台账行在册的"改前"两把尺与反推值不等'
    GLUE_F = 1 if _fl[_hf[0] - 1].strip() == '' else 0
    assert GLUE_F == 1, 'ABORT: 本批 FreqErr 标题上方没有空行 ⇒ 追加形状变了'
    _tail_f = _fl[_led[0] + 1:-1]
    TAIL_KF = len([l for l in _tail_f if l.startswith('[错误类型]')])
    # 行数等式里不加 GLUE_F：那只空行已被本批在册的 AFTER 行数数过，而 _tail_f 从本批台账行的下一行起算。
    # （这一格在 LANDED_NOW 那一遍永远走不到 —— §38.21 ① 那一族第 3 次命中就在上一批 paperwork2 的这条等式上。）
    assert (kinds(freq_disk), nl(freq_disk)) == \
        (int(_m.group(3)) + TAIL_KF, int(_m.group(4)) + len(_tail_f)), \
        'ABORT: 台账行在册终态(%s,%s) + 窗口外(TAIL=%d 行 %d 条) != 盘上现算(%d,%d)' % (
            _m.group(3), _m.group(4), len(_tail_f), TAIL_KF, kinds(freq_disk), nl(freq_disk))
    assert len([l for l in _fl[_hf[0]:_led[0]] if l.startswith('[错误类型]')]) == N_ENTRY, 'ABORT: 本批尾段条数不是 %d' % N_ENTRY
    _dl = lf(doc_disk).split('\n')
    _dnx = [i for i in range(_hd[0] + 1, len(_dl) - 1) if _dl[i].startswith(('## ', '### '))]
    _dwin_end = _dnx[0] if _dnx else len(_dl) - 1
    # 窗口右界不许把"下一批落纸时插进来的那只空行"算进本批节：那是**下一批的 glue**，归尾段。
    #   不剥的话"本批终态 = 盘上 − 尾段"会多出一行（3722 读成 3723），台账行在册值就对不上。
    while _dwin_end > _hd[0] and _dl[_dwin_end - 1].strip() == '':
        _dwin_end -= 1
    WIN_D = _dl[_hd[0]:_dwin_end]
    TAIL_D = len(_dl) - 1 - _dwin_end
    GLUE_D = 1 if _dl[_hd[0] - 1].strip() == '' else 0
    assert GLUE_D == 1, 'ABORT: §38.24 标题上方没有空行'
    assert nl(doc_disk) == DOC_ROWS0 + GLUE_D + len(WIN_D) + TAIL_D, \
        'ABORT: 排查记录行数账目不闭合：盘上 %d != 改前 %d + 上方空行 %d + 本批节 %d + 之后 %d' % (
            nl(doc_disk), DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)
if MODE == 'LANDED_NOW':
    WIN_F = lf(freq_final).split('\n')[L0:]
    _df = lf(doc_final).split('\n')
    _dwi = [i for i, l in enumerate(_df) if l.startswith(SEC)][0]
    WIN_D = _df[_dwi:-1]
else:
    WIN_F = _fl[_hf[0]:_led[0] + 1]   # WIN_D 已在上面复跑支里按"标题行 ~ 下一只标题之前"取定

# ---------- "本批终态"必须扣掉尾段（第三批之后又落了第四批）----------
# 载体的"改前 -> 终态"讲的是**本批窗口**：拿 live 盘长当终态 ⇒ 箭头差值变成跨批的和，
#   DOC-RULER 那条对账式会随后续批次漂，且第二只载体起各只读数互不相等（§38.25 第 1 条那一族第 5 次命中）。
_df0 = lf(doc_disk).split('\n')
assert _df0[-1] == '' and len(_df0) - 1 == nl(doc_disk), \
    'ABORT: 行数尺子对不上（尾行 %r / 行数 %d vs `\\n` 计数 %d）' % (_df0[-1], len(_df0) - 1, nl(doc_disk))
SELF_ROWS1 = nl(doc_disk) - TAIL_D
SELF_STR = ''.join(l + '\n' for l in _df0[:SELF_ROWS1])
SELF_B1 = len(crlf(SELF_STR).encode('utf-8'))
TAIL_STR = ''.join(l + '\n' for l in _df0[SELF_ROWS1:-1])
SELF_TIE = SELF_B1 + len(crlf(TAIL_STR).encode('utf-8')) == os.path.getsize(DOC)
SELF_K1 = kinds(freq_disk) - TAIL_KF
SELF_L1 = nl(freq_disk) - len(_tail_f)
assert SELF_TIE, 'ABORT: 本批终态 %d B + 尾段 %d B != 盘上 %d B ⇒ 尾段/终态切分没有覆盖整只文件' % (
    SELF_B1, len(crlf(TAIL_STR).encode('utf-8')), os.path.getsize(DOC))
assert SELF_ROWS1 == DOC_ROWS0 + GLUE_D + len(WIN_D), \
    'ABORT: 本批终态行数 %d != 改前 %d + 上方空行 %d + 本批节 %d' % (SELF_ROWS1, DOC_ROWS0, GLUE_D, len(WIN_D))
assert SELF_K1 == K0 + N_ENTRY, 'ABORT: 本批终态条数 %d != 改前 %d + %d 条' % (SELF_K1, K0, N_ENTRY)
if MODE == 'REWROTE_CARRIER_ONLY':
    assert (SELF_K1, SELF_L1) == (int(_m.group(3)), int(_m.group(4))), \
        'ABORT: 扣尾段得到的本批终态 (%d,%d) != 台账行在册终态 (%s,%s)' % (
            SELF_K1, SELF_L1, _m.group(3), _m.group(4))
BS = chr(92)
assert BS not in '\n'.join(WIN_F), 'ABORT: 本批 FreqErr 追加段里有反斜杠（§38.18 那一族）：%r' % [l for l in WIN_F if BS in l][:2]
assert BS not in '\n'.join(WIN_D), 'ABORT: 本批 §38.24 追加段里有反斜杠：%r' % [l for l in WIN_D if BS in l][:2]
assert (kinds(freq_final) - K0 == N_ENTRY) if MODE == 'LANDED_NOW' \
    else (kinds(freq_disk) - K0 == N_ENTRY + TAIL_KF), \
    'ABORT: 本批正文 `[错误类型]` 增量不是 %d（现算 %d，尾段 TAIL_KF=%d）' % (N_ENTRY, kinds(freq_disk) - K0, TAIL_KF)
assert not [l for l in WIN_D if l.strip() and not l.strip().startswith(('-', '>', '#'))], 'ABORT: §38.24 有裸行'
_dfl = lf(doc_final).split('\n')
_hidx = [i for i, l in enumerate(_dfl) if l.startswith(SEC)]
assert len(_hidx) == 1 and _dfl[_hidx[0] - 1].strip() == '', 'ABORT: §38.24 标题上方缺空行（或标题命中 %d 处）' % len(_hidx)

print('MODE=%s LEDGER: 只数 在册%s/现跑%s 重合位=%d / 名单换过=%s' % (MODE, CNT_REG, CNT_NOW, len(LIST_NOW) - DRIFT, DRIFT == CNT_NOW))
print('HIST rev-list 全史扫描=%d 版 / 命中在册那串的版=%s' % (len(_rev), HIT_REV or '无'))
print('EOL todo md5 工作树=%s HEAD=%s 两串名单相等=%s' % (md5_(TODO), _head_md5, LIST_HEAD == LIST_NOW))
print('SEAL rows=%d disk=%d GATE %s / VM rc=%d %s' % (len(_rows), DISK_N, ARMS_FIRED, _v.returncode, VM_CARRIER))
print('FREQ 改前 %d 条 / %d 行 -> %d 条 / %d 行' % (K0, L0, kinds(freq_final), nl(freq_final)))

if MODE == 'LANDED_NOW':
    open(FREQ, 'wb').write(freq_final.encode('utf-8'))
    open(DOC, 'wb').write(doc_final.encode('utf-8'))

_r = subprocess.run([sys.executable, P2], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = ' | '.join(l[:110] for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT=', 'FREQ ')))
assert _r.returncode == 0 and _pos, 'ABORT: 前向对照（复跑上一批落地器）rc=%d ⇒ 本批追加把它弄红了' % _r.returncode

_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
PRE_EQ_F = lf(freq_disk).startswith(lf(freq_pre).rstrip('\n'))
PRE_EQ_D = lf(doc_disk).startswith(lf(doc_pre).rstrip('\n'))
assert PRE_EQ_F and PRE_EQ_D, 'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 本批不只做了追加'
_p2 = rd(P2)
FIX_NEW = 'int(_m.group(4)) + len(_tail_f)' in _p2
FIX_OLD = 'GLUE_F + len(_tail_f)' in _p2
FIX_GLUE = 'assert GLUE_F == 1' in _p2
assert FIX_NEW and not FIX_OLD and FIX_GLUE, \
    'ABORT: paperwork2 复跑支的 GLUE_F 重复计数没修好（新等式=%s 旧等式还在=%s 空行闸=%s）' % (FIX_NEW, FIX_OLD, FIX_GLUE)
_secs = [i + 1 for i, l in enumerate(lf(rd(DOC)).split('\n')) if l.startswith('### 38.21')]
assert len(_secs) == 1, 'ABORT: §38.21 标题在盘上命中 %d 处（应为 1）' % len(_secs)
_sec_line_now = _secs[0]
# —— 同一行两把尺的自查：改前 B 曾按 LF 串长度算、终态 B 按盘上 CRLF 大小算 ⇒ 差值里混进了 CR 字节
DISK_TIE = len(crlf(doc_final).encode('utf-8')) == os.path.getsize(DOC)
assert DISK_TIE, \
    'ABORT: 把终态串按 CRLF 重排后长度 %d != 盘上现读 %d ⇒ 文件里有裸 CR/LF，落盘口径不成立' % (
        len(crlf(doc_final).encode('utf-8')), os.path.getsize(DOC))
PREV3 = os.path.join(HDIR, 'r56_paperwork3.txt')
_PL = [i + 1 for i, l in enumerate(lf(rd(PREV3)).split('\n')) if l.startswith('DOC 改前')]
assert len(_PL) == 1, 'ABORT: 上一遍载体里 DOC 行命中 %d 处（应为 1）' % len(_PL)
_pm = re.search(r'DOC 改前 (\d+) 行 / ([\d,]+) B -> \S+ (\d+) 行 / ([\d,]+) B', lf(rd(PREV3)))
assert _pm, 'ABORT: 反查上一遍载体的 DOC 行没抓到（换口径的证据落不了纸）'
_P_ROWS, _P_B0, _P_ROWS1, _P_B1 = (int(_pm.group(1)), int(_pm.group(2).replace(',', '')),
                                   int(_pm.group(3)), int(_pm.group(4).replace(',', '')))
# 订正行自己**不许拿 live getsize 当尺**：盘上大小会随后续批次长，那条等式就会在下一批之后漂掉
#   （这正是 §38.25 第 1 条那一族的第 4 次命中 —— 本遍第一次跑红就是它）。对照物一律取**不可变载体**。
# 选对照物**不许**按"载体里有没有 `两格同尺` 这句话"扫：本工具往每只载体里都写那一格 ⇒ 第二遍起必然越扫越多，
#   那是 R42「命令文本含被搜串 ⇒ 计数自指永不成立」的同族。改成按**本遍算得出的两把尺**反向点名：
#   同尺载体 = 改前 B == 本遍 `crlf(改前串)` 长度，混尺载体 = 改前 B == 本遍 LF 串长度，两者终态都须 == 本批终态。
_CAND = [f for f in sorted(os.listdir(HDIR))
         if f.startswith('r56_paperwork3') and f.endswith('.txt')]
_TRIP = {}
for _f in _CAND:
    _sm = re.search(r'DOC 改前 (\d+) 行 / ([\d,]+) B -> \S+ (\d+) 行 / ([\d,]+) B', rd(os.path.join(HDIR, _f)))
    if _sm:
        _TRIP[_f] = (int(_sm.group(1)), int(_sm.group(2).replace(',', '')),
                     int(_sm.group(3)), int(_sm.group(4).replace(',', '')))
assert _TRIP, 'ABORT: %s 目录里没有一只 %s*.txt 带 DOC 行 ⇒ 对照物不存在，等式落不了纸' % ('hardware/', 'r56_paperwork3')
_SAME3 = sorted(f for f, v in _TRIP.items() if v == (DOC_ROWS0, DOC_B0D, SELF_ROWS1, SELF_B1))
_MIXED3 = sorted(f for f, v in _TRIP.items() if v == (_P_ROWS, _P_B0, SELF_ROWS1, SELF_B1))
assert _SAME3 and _MIXED3, 'ABORT: 同尺对照物 %s / 混尺对照物 %s 至少有一组为空（现读 %d 只读数 = %s）' % (
    _SAME3, _MIXED3, len(_TRIP), sorted(set(_TRIP.values())))
_S_B0, _S_ROWS1, _S_B1 = DOC_B0D, SELF_ROWS1, SELF_B1      # 同尺那只：三个数都由本遍现算，载体只是它的落纸副本
_TIEL = _S_B1 - _S_B0                            # 同尺口径下本批真追加的字节数
_MIXED = _P_B1 - _P_B0                           # 上一遍那一行箭头给出的差值（混尺）
assert _MIXED - _TIEL == _P_ROWS, \
    'ABORT: 混尺差值 %d - 同尺差值 %d != 改前那 %d 行（每行 1 只 CR）⇒ 这一格的对账式不成立，别落' % (
        _MIXED, _TIEL, _P_ROWS)
assert DOC_B0D - _P_B0 == _P_ROWS, \
    'ABORT: 本遍同尺改前 %d - 上一遍混尺改前 %d != %d 只 CR' % (DOC_B0D, _P_B0, _P_ROWS)
_lines = [
    'R56 第三批 paperwork 落地器  MODE=%s' % MODE,
    '本遍现跑于 %s（台账行标题时刻 = %s；载体由脚本自己落盘，在归档目录之外）' % (_now2, LED_TS),
    'LEDGER 命令原文现跑（新口径：命令与输出一起落纸）：`%s` 输出 = %s（只数 %d）' % (UNCHECK, ' '.join(map(str, LIST_NOW)), CNT_NOW),
    'LEDGER 同一遍的第二条：`%s` 输出 = %d' % (UNITS, CNT_NOW),
    'LEDGER 在册那串（进脚本时从 todo.md 正文 re.findall 抓到的最后一次登记，逐字）= %s / 只数 %d' % (' '.join(map(str, LIST_REG)), CNT_REG),
    'LEDGER 两串逐位比对：重合位 = %d / %d ⇒ 名单整串换过 = %s；只数相等 = %s（在册那串自本行起作废，降级为不可复算的旧快照）' % (
        len(LIST_NOW) - DRIFT, len(LIST_NOW), DRIFT == CNT_NOW, CNT_REG == CNT_NOW),
    'LEDGER 换渲染的等值对照（同一遍两把尺）：按"行首前缀 - [ ]"与"整行含 - [ ]"两种口径各数一遍，两串行号逐位相等 = %s / 两种口径都是 %d 只' % (
        EQUIV, CNT_NOW),
    'HIST 出处查证：`%s` 逐版跑同一条命令 = %d 版（本仓库总版数由同一条命令现算，不设上限），产出在册那串的版 = %s ⇒ 那串数在任何一版上都不成立' % (
        CMD_REV, len(_rev), ' + '.join(HIT_REV) if HIT_REV else '无'),
    'HIST 同遍两把尺：`git show HEAD:todo.md` 的名单与工作树名单逐字相等 = %s；整只 md5 工作树 = %s / HEAD 版（LF 归一后）= %s' % (
        LIST_HEAD == LIST_NOW, md5_(TODO), _head_md5),
    'RECITE 在册那串在 todo.md 正文里逐字出现的行数 = %d（首行 %d / 末行 %d），其中带"**%d**"只数的 = %d 行，写成"未勾选名单与只数…第 N 次逐字未变"句式的 = %d 次；本遍是第 %s 遍（前一遍序数现读自正文 = 第 %d 遍）' % (
        RECITE, _RLN[0], _RLN[-1], CNT_NOW, RECITE17, NREG, NEXT_PASS, LAST_PASS),
    'DONE 同族三格本遍现跑（只点名"它们是同族"，不背书）：`%s` 末节号 = %s；`%s` = %d；`%s` = %d；两格的前缀 / 子串两种匹配逐位等值 = %s' % (
        CMD_SEC, DONE_SEC, CMD_N1, DONE_N1, CMD_N2, DONE_N2, DONE_EQUIV),
    'EV 上一批载体 = hardware/%s（%s B / md5=%s）/ 本遍现跑于 %s / CITE 行原样引：见该行' % (
        os.path.basename(EV2), money(os.path.getsize(EV2)), md5_(EV2)[:8], EV2_AT),
    'EV 上一批在册等式 = %s' % EV2_ID[:150],
    'SEAL 清单在册=%d 行 / 目录全量=%d 只 / %s B / 差集逐只点名=%s / mtime 秒数全部 == 末版那一秒 %s' % (
        len(_rows), DISK_N, money(DISK_B), ' + '.join(NOT_LISTED), SEAL_AT),
    'GATE %s（假名 %s 只在内存；盘上反查不存在 = True）' % (ARMS_FIRED, PROBE),
    'GEN 末版=代次日志末行 %s（本批未新建代次）' % _glog_last.replace(chr(9), ' / '),
    'VM 本遍真跑 rc=%d / %s / VM_CARRIER=%s' % (_v.returncode, _vm_rows[0], VM_CARRIER),
    'FIELD rev-list=%s / comports=%s / 本遍零串口动作 / 屏亮肉眼确认 0 次 / 未播提示音' % (REV_LIST_NOW, _com),
    'FREQ 改前 %d 条 / %d 行 -> %s %d 条 / %d 行' % (K0, L0, '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
                                                SELF_K1, SELF_L1),
    'DOC 改前 %d 行 / %s B -> %s %d 行 / %s B（两格同尺 = 行尾 CRLF 的落盘字节数；反查 `终态 %s B + 尾段 %d 行 = 盘上现读 %s B` = %s）' % (
        DOC_ROWS0, money(DOC_B0D), '本遍写盘终态' if MODE == 'LANDED_NOW' else '本批在册终态',
        SELF_ROWS1, money(SELF_B1), money(SELF_B1), TAIL_D, money(os.path.getsize(DOC)), SELF_TIE),
    'WINDOW 前缀等式（"只追加、正文一字未改"）：FreqErr %d 行是盘上 %d 行的逐字前缀 = %s / 排查记录 %d -> %d 行 = %s；'
    '本批窗口 = FreqErr %d 行 + §38.24 %d 行' % (
        nl(freq_pre), nl(freq_disk), PRE_EQ_F, DOC_ROWS0, nl(doc_disk), PRE_EQ_D, len(WIN_F), len(WIN_D)),
    'POSCTL 复跑上一批落地器 rc=%d / %s' % (_r.returncode, _pos),
    'FIX 复跑支修复的现场证据（本遍从 %s 源码现读三格，不是抄上一遍的话）：行数等式含 `int(_m.group(4)) + len(_tail_f)` = %s / '
    '含被剔除的 `GLUE_F + len(_tail_f)` = %s / 含 `assert GLUE_F == 1` = %s；§38.21 标题在盘上第 %d 行（现读）' % (
        os.path.basename(P2), FIX_NEW, FIX_OLD, FIX_GLUE, _sec_line_now),
    'FIX 第一次 POSCTL rc=1 的根因（本节登记的就是这件事）：paperwork2 复跑支把"本批 FreqErr 标题上方那只空行"既算进 AFTER 行数、'
    '又额外加进 `kinds/行数` 等式 ⇒ 盘上现算比在册终态多 1 行。它是 §38.21 ① 那一族（写侧那一遍永远走不到复跑支）的**第 3 次命中**；'
    '本轮按规矩只订正工具源码，不改已落地的 §38.23 正文',
    'DOC-RULER 订正（反查本批第一遍载体 %s 第 %d 行，逐字抓回两个数）：那一行"改前 B"按 LF 串长度 %s B 算、'
    '"终态 B"按盘上 CRLF 大小 %s B 算 ⇒ 同一行两把尺，箭头差 %s B 里混进了 %d 只 CR 字节（= 改前那 %d 行每行 1 只）。'
    '本遍起两格同尺（落盘 CRLF）：真追加 %s B，对账式 %s - %s == %s 成立；上一遍那一行按规矩不回写，只在此点名' % (
        os.path.basename(PREV3), _PL[0], money(_P_B0), money(_P_B1), money(_MIXED), _P_ROWS, _P_ROWS,
        money(_TIEL), money(_MIXED), money(_TIEL), money(DOC_ROWS0)),
    'RULER-SELF 终态那把尺也要扣尾段（本遍第二次跑红的根因）：第三批之后 §38.25 又落了一次 ⇒ 盘上现读是**跨两批的和**，'
    '拿它当"本批终态"会让箭头失去意义、并让每只重写的载体互不相等。本遍起终态 = 盘上 − 尾段 = (%d 行, %s B)，'
    '与台账行在册值逐字相等 = %s；对照物按"改前 B == 本遍现算"反向点名：同尺 %s / 混尺 %s（不匹配 %s）' % (
        SELF_ROWS1, money(SELF_B1), (SELF_ROWS1, SELF_B1) == (_P_ROWS1, _P_B1),
        ' + '.join(_SAME3), ' + '.join(_MIXED3),
        ' + '.join(sorted(set(_TRIP) - set(_SAME3) - set(_MIXED3))) or '无'),
    'RULER-SELF 同族第 5 次命中（点名口径）：这一格错在**新写的复跑支断言里**（`_P_*` 解包把 group(3)/(4) 名字对调 + '
    '按载体文本里的"两格同尺"字样选对照物 = 自指），第一次执行者是下一批的前向对照 ⇒ §38.21 ①「写侧那一遍永远走不到复跑支」'
    '在本轮的第 5 次；本遍只订正工具源码，已落地的 §38.24 正文与 %s 里的旧读数一律不回写' % os.path.basename(PREV3),
    'WITNESS FREQ md5=%s / DOC md5=%s / TODO md5=%s（本遍结束时现算，todo 本遍未写）' % (
        md5_(FREQ)[:8], md5_(DOC)[:8], md5_(TODO)[:8]),
    'NOTDONE 本遍（%s）没做：串口 / 烧录 / 换电池 / 万用表 / 第二块板 / 改 main 源码 / 重建固件 / 勾或改那 %d 只未选项 / '
    '新建备份根 / 新建清单代次 / push / amend / 删除 —— 屏亮 0 次肉眼确认 ⇒ 未播提示音；'
    'docs 第十遍、backups README 第十次读数、提交轮#9、第 14 代同步在本节之后 ⇒ 本遍不预写它们的数' % (_now2, CNT_NOW),
    'VERDICT=%s（两只 CRLF 目标里本遍写盘 %d 只 + 载体 1 只）' % (
        'OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY', 2 if MODE == 'LANDED_NOW' else 0),
]
assert BS not in '\n'.join(_lines), 'ABORT: 载体行里有反斜杠（§38.18 那一族）：%r' % [l for l in _lines if BS in l][:2]
assert 'zizhao1' not in '\n'.join(_lines), 'ABORT: 载体含口令明文'
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(_lines) + '\n')
print('VERDICT=OK CARRIER=%s' % os.path.basename(CARRIER))
print('POSCTL rc=%d %s' % (_r.returncode, _pos[:200]))
