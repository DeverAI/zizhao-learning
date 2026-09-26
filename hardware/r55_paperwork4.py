# R55 第四批（第三批那两只工具的**复跑路径**与**下一批落地之后**自查）的收口落地器：一次调用落两只 CRLF 文件
#   ① FreqErr.md —— 本批 1 条新错误类型 + 台账行（两把尺都在"将被写出的最终串"上现算，(99)）
#   ② hardware/20260919_墨水屏点屏排查记录.md —— 新增 §38.21
# 位置：`hardware/`（**归档目录之外**）—— gen 24 是末版，此后任何一只文件落进 `hardware/ht305_sync/`
#   都会把 `UNLISTED` 顶成非 0 ⇒ 末版自动降级（§38.19 ④）。本脚本对这条封界**装了执行者**：写盘前后各数一遍
#   那只目录的名字数 + 字节数，两遍逐字相等才写载体（SEAL 行）。
# 本批把自己也当作被检对象：落地之后**当场**把第三批两只工具各复跑一遍（POSCTL），
#   判据 = 两只 rc=0 且"本批窗口之外有后续行"—— 这就是第 5 条错误类型所说的"前向对照"，不是叙述。
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
P3 = os.path.join(HDIR, 'r55_paperwork3.py')
P3F = os.path.join(HDIR, 'r55_fix_paperwork3.py')
C3_WIT = os.path.join(HDIR, 'r55_paperwork3.txt')          # 第三批落地器：唯一"现读改前的盘"那一遍
C3_BUG = os.path.join(HDIR, 'r55_paperwork3_2.txt')        # 同脚本：混取格那一版的载体（引文原件）
C3_BUG2 = os.path.join(HDIR, 'r55_paperwork3_3.txt')       # FreqErr 修好、排查记录仍混取的那一版
C3F_BUG = os.path.join(HDIR, 'r55_fix_paperwork3.txt')     # 订正器：把 BEFORE 行数标成 AFTER 的那一版
C_RD9 = os.path.join(HDIR, 'r55_backups_readme9.txt')
TS = '[0-9-]{10} [0-9:]{8}'
LED4 = '复跑｜R55 第四批'
LED3 = '复跑｜R55 第三批'          # 前向兼容：本批正文一个字都不许把这只锚抄进去（第三批的尺会命中两处）
SEC_ANCHOR = '### 38.21'
FIXPFX = '> **【订正｜'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_cands = ['r55_paperwork4.txt'] + ['r55_paperwork4_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)
_self_prior = [c for c in _cands if os.path.exists(os.path.join(HDIR, c))]


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def crlf_pure(p):
    b = open(p, 'rb').read()
    assert b.count(b'\r\n') == b.count(b'\n'), 'ABORT: %s 行尾混杂' % os.path.basename(p)


def kinds(text):
    return len(re.findall(r'(?m)^\[错误类型\]', text))


def heads(text):
    return len(re.findall(r'(?m)^#{2,3} ', text))


def blanks_above(text, idx):
    ls = text.split('\r\n')
    n, j = 0, idx - 1
    while j >= 0 and not ls[j].strip():
        n, j = n + 1, j - 1
    return n


def head_hits(text, anchor):
    """标题类锚一律按**行首**数：正文里引用同一节号、或把带井号的原文抄一遍，都会让裸子串 count 翻倍（(40) 族）。"""
    return len([l for l in text.split('\r\n') if l.startswith(anchor)])


def line_hits(text, anchor):
    return len([l for l in text.split('\r\n') if anchor in l])


def line_only(path, pat, why):
    hits = [l for l in rd(path).replace('\r\n', '\n').split('\n') if re.search(pat, l)]
    assert len(hits) == 1, 'ABORT: %s 里 %r 命中 %d 行（须恰好 1）⇒ %s' % (os.path.basename(path), pat, len(hits), why)
    return hits[0]


def sync_seal():
    """末版封界的执行者：归档目录里所有只文件的名字 + 字节数聚合成一把尺（本批只读它，一字节都不许写）。"""
    acc = []
    for root, dirs, fs in os.walk(SYNC):
        dirs.sort()
        for f in sorted(fs):
            p = os.path.join(root, f)
            acc.append((os.path.relpath(p, SYNC).replace('\\', '/'), os.path.getsize(p)))
    return len(acc), sum(n for _, n in acc), hashlib.md5(repr(acc).encode('utf-8')).hexdigest()[:8]


# ---------- 现读：第三批载体在册的读数与本批要引用的三段原文（引文一律运行时现读、逐字插入）----------
assert 'MODE=LANDED_NOW' in line_only(C3_WIT, r'^R55 第三批 paperwork 落地器', '第三批写盘那一遍的载体首行')
P3_LAND_AT = re.search(r'本遍现跑于 (' + TS + ')',
                       line_only(C3_WIT, r'^R55 第三批 paperwork 落地器', '第三批写盘那一遍首行')).group(1)
_w3 = line_only(C3_WIT, r'^FREQ 追加之前现读 ', '第三批写盘那一遍的 FREQ 行')
_m3 = re.search(r'FREQ 追加之前现读 ([\d,]+) B / (\d+) 条 / (\d+) 行 -> .* (\d+) 条 / (\d+) 行 ; md5 ([0-9a-f]{8}) -> ', _w3)
assert _m3, 'ABORT: 第三批见证载体的 FREQ 行不再合"现读 B/条/行 -> B/条/行 + md5"句式 ⇒ 下面的算式没有原件'
w3_bbytes, w3_bk, w3_bl, w3_ak, w3_al, w3_bmd5 = _m3.groups()
Q_WIT = _w3
assert w3_bl == '1873' and w3_al == '1907', \
    'ABORT: 第三批写盘那遍的 BEFORE/AFTER 行数不再是 1873 / 1907 ⇒ "错标"那句引文的算式要重推：%s / %s' % (w3_bl, w3_al)
assert int(w3_bk) + 4 == int(w3_ak), \
    'ABORT: 第三批写盘那遍在册的条数差不是 4 ⇒ §38.21 里"它新增 4 条"这句话与原件脱节：%s -> %s' % (w3_bk, w3_ak)
Q_FREQ_BUG = line_only(C3_BUG, r'^FREQ 追加之前', '第三批混取格那一版的 FREQ 行')
Q_DOC_BUG = line_only(C3_BUG, r'^DOC ', '第三批混取格那一版的 DOC 行')
# §38.21 第 ② 格那两句"混取"的话，就地拿原件复算一遍 —— 不是拿我的记忆当证据
_mb = re.search(r'^FREQ 追加之前现读 ([\d,]+) B / (\d+) 条 / (\d+) 行 -> 之后 ([\d,]+) B', Q_FREQ_BUG)
assert _mb, 'ABORT: 混取旧载体的 FREQ 行不合式 ⇒ §38.21 第 ② 格没有原件可引：%r' % Q_FREQ_BUG[:60]
assert (_mb.group(2), _mb.group(3)) == (w3_bk, w3_bl) and _mb.group(1) != w3_bbytes, \
    'ABORT: 旧载体那一行的"改前条/行"不是改前值、或"改前 B"反倒与改前同值 ⇒ §38.21 第 ② 格的措辞要重推：%r vs %r' % (
        _mb.groups(), _m3.groups())
_mdg = re.search(r'^DOC ([\d,]+) B / (\d+) 行 / 标题 (\d+) -> ([\d,]+) B / (\d+) 行 / 标题 (\d+)', Q_DOC_BUG)
assert _mdg and _mdg.group(1) == _mdg.group(4) and _mdg.group(2) == _mdg.group(5) \
    and _mdg.group(3) != _mdg.group(6), \
    'ABORT: 旧载体 DOC 行不是"改前改后同 B 同行、唯标题数不同"那个形状 ⇒ §38.21 第 ② 格那句引文与原件脱节'
Q_LEDGER_BUG = line_only(C3F_BUG, r'^LEDGER 台账行', '订正器把 BEFORE 标成 AFTER 的那一版 LEDGER 行')
assert ('AFTER 行数 = ' + w3_bl) in Q_LEDGER_BUG and ('AFTER 行数 = ' + w3_al) not in Q_LEDGER_BUG, \
    'ABORT: 旧载体 LEDGER 行不再把 BEFORE 行数(%s) 标成 AFTER ⇒ §38.21 第 ③ 格那句"取错列"与原件脱节（真 AFTER 是 %s）' % (
        w3_bl, w3_al)
Q_DOC_BUG2 = line_only(C3_BUG2, r'^DOC ', '第三批 FreqErr 已修、DOC 未修那一版的 DOC 行')
assert Q_DOC_BUG == Q_DOC_BUG2, 'ABORT: 两版混取 DOC 行不逐字相同 ⇒ 本批引文只覆盖了其中一版'
P3F_CANDS = [c for c in os.listdir(HDIR) if re.match(r'r55_fix_paperwork3(_\d+)?\.txt$', c)]
P3_CANDS = [c for c in os.listdir(HDIR) if re.match(r'r55_paperwork3(_\d+)?\.txt$', c)]


def seq_of(name):
    m = re.search(r'_(\d+)\.txt$', name)
    return int(m.group(1)) if m else 1


def authority(cands):
    """"权威载体"按**序号**取最大，绝不按字典序（`_10` 在字典序里排在 `_2` 之前）。"""
    assert cands, 'ABORT: 载体名单为空 ⇒ 无从取权威'
    return max(cands, key=seq_of)


P3_AUTH, P3F_AUTH = authority(P3_CANDS), authority(P3F_CANDS)
# 本批第一次真跑（17:0x）在 POSCTL 第二只上崩：落地器已复跑并写下这只载体，订正器随后 rc=1 ⇒ 崩溃那一遍有时刻可引
C4_CRASH_C = os.path.join(HDIR, 'r55_paperwork3_10.txt')
assert os.path.basename(C4_CRASH_C) in P3_CANDS, 'ABORT: 崩溃那一遍的落地器载体不在册 ⇒ POSCTL_CRASH 那一句没有原件'
_crash_head = line_only(C4_CRASH_C, r'^R55 第三批 paperwork 落地器', '崩溃那一遍的落地器载体首行')
assert 'MODE=REWROTE_CARRIER_ONLY' in _crash_head, 'ABORT: 在册的崩溃载体首行不是复跑那一遍：%s' % _crash_head[:60]
CRASH_AT = re.search(r'本遍现跑于 (' + TS + ')', _crash_head).group(1)
_crash_f = line_only(C4_CRASH_C, r'^FREQ 追加之前', '崩溃那一遍的落地器载体 FREQ 读数行')
_mc = re.search(r'-> 之后（本批窗口末行 \d+） [\d,]+ B / (\d+) 条 / \d+ 行.*?盘上现值（含后续批次）[\d,]+ B / (\d+) 条', _crash_f)
assert _mc, 'ABORT: 崩溃载体的 FREQ 行不再合"窗口终态 + 盘上现值"句式 ⇒ POSCTL_CRASH 那一句没有原件：%r' % _crash_f[:60]
CRASH_WIN_KIND, CRASH_DISK_KIND = int(_mc.group(1)), int(_mc.group(2))
t_rd9 = line_only(C_RD9, r'(?m)^R55 第九次读数', '第九次读数首行')
rd9_run = re.search(r'现跑于 (' + TS + ')', t_rd9).group(1)
t_docs9 = line_only(C_RD9, r'(?m)^DOCS ', 'docs 第九遍快照行')
docs_n = re.search(r'^DOCS files=(\d+)', t_docs9).group(1)
docs_at = re.search(r'SNAPSHOT_AT=(' + TS + ')', t_docs9).group(1)

git = lambda *a: subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a),
                                capture_output=True, cwd=REPO).stdout.decode('utf-8', 'replace')
rev = git('rev-list', '--count', 'origin/main..HEAD').strip()
assert rev.isdigit(), 'ABORT: rev-list 读数不是数字：' + rev[:20]
por = [l for l in git('status', '--porcelain').split('\n') if l.strip()]
ports = sorted(__import__('serial.tools.list_ports', fromlist=['comports']).comports(), key=lambda c: c.device)
port_names = ', '.join(p.device for p in ports)
has14 = 'COM14' in port_names

# ---------- 进入时现读两只 CRLF 文件 + 幂等闸 ----------
freq_old, doc_old = rd(FREQ), rd(DOC)
crlf_pure(FREQ)
crlf_pure(DOC)
assert freq_old.endswith('\r\n') and doc_old.endswith('\r\n'), 'ABORT: 追加目标不以 CRLF 结尾 ⇒ 会造出半行'
ls_f = freq_old.split('\r\n')
led4_i = [i for i, l in enumerate(ls_f) if LED4 in l and not l.startswith(FIXPFX)]
has_sec = head_hits(doc_old, SEC_ANCHOR) == 1
assert head_hits(doc_old, SEC_ANCHOR) <= 1, 'ABORT: §38.21 标题在盘上有 %d 处 ⇒ 二次追加' % head_hits(doc_old, SEC_ANCHOR)
assert (len(led4_i) == 1) == has_sec, \
    'ABORT: 半落地（本批台账行=%d 处 / §38.21=%s）⇒ 上一遍只写完一半，拒绝补齐' % (len(led4_i), has_sec)
MODE = 'REWROTE_CARRIER_ONLY' if has_sec else 'LANDED_NOW'
if led4_i:
    assert LED3 not in ls_f[led4_i[0]], 'ABORT: 本批台账行里出现了第三批的锚 ⇒ 第三批"数本批台账行"那把尺会命中两处（(40) 族）'


def split_ledger(line):
    parts = line.split('追加之后现算，')
    assert len(parts) == 2, \
        'ABORT: 台账行的分节锚 `追加之后现算，` 出现 %d 次 ⇒ 台账行结构与解析式不同形：%r' % (len(parts) - 1, line[:70])
    return parts


# 写侧与读侧**同一把式子**（第三批第 5 条错误类型的①：不得各写一套，否则"另一侧分支"里的解析式永不执行）
PAT_LED = re.compile(r'条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*')


def led_pair(seg, name):
    hits = PAT_LED.findall(seg)
    assert len(hits) == 1, 'ABORT: 台账行的 %s 段里那把式子命中 %d 处（须恰好 1）⇒ 读侧解析式与写侧不同形（第三批就是在这里崩的）' % (
        name, len(hits))
    return tuple(int(x) for x in hits[0])


def win_end(ls, last_i):
    """本批断言范围的右界 = "本批写的最后一行" 之后第一只 `## ` 标题之前那一段（标题归下一批）。
    不划这个界，第五批一追加就把本批所有闸染成假红 —— 这正是 §38.21 第 ④ 格登记的口径缺陷。
    界前**有没有那只空行**是下一批的排版，不是本批的判据：全文 18 只 `## ` 里 3 只上方非空行（R53 两只 + R56 一只），
    旧写法硬要求空行 ⇒ 与本批同族的"守卫写在只有我的世界里"，见本载体的 WIN_BOUND 行。"""
    nxt = [i for i in range(last_i + 1, len(ls)) if ls[i].startswith('## ')]
    if not nxt:
        return len(ls) - 1, 0, ls[last_i + 1:-1], '无下一批标题（右界 = EOF）'
    _p = ls[nxt[0] - 1]
    if _p.strip():
        assert _p.startswith(('> ', '- ', '@', '#### ')), \
            'ABORT: 窗口右界上一行是裸正文 %r ⇒ 真的是在半截内容里切的' % _p[:24]
        return nxt[0], len(nxt), ls[last_i + 1:nxt[0]], '紧接（该批标题上方 0 只空行）'
    return nxt[0] - 1, len(nxt), ls[last_i + 1:nxt[0] - 1], '空行分隔'


LEDGER_TMPL = ('> **【@T@ 复跑｜R55 第四批 1 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'
               '全文 `^[错误类型]` 条数 = **@BK@**、`wc -l` 行数 = **@BL@**；追加之后现算，'
               '**口径 = 含本台账行自身的最终字节串（本批窗口内，不含后续批次）**：'
               '`^[错误类型]` 条数 = **@AK@**、`wc -l` 行数 = **@AL@**'
               '（两把尺都在最终串上数，不数未含台账行的中间串 —— (99)）。'
               '本批一条 = **守卫只写在"另一侧分支"里，那一道闸等于没验过**：三处现场（一次 `AttributeError`、'
               '一次 `AssertionError`、一次把正确状态判成假红的口径）全部只在"复跑那一遍"或"下一批落地之后"才暴露，'
               '正文登记在排查记录 §38.21，取证载体在 `hardware/r55_paperwork4*.txt`（本批落地那遍写的那一只，'
               '含落地后当场复跑第三批两只工具的前向对照 POSCTL 行）。')

FREQ_HEAD = ('## 2026-09-24（R55 第四批：第三批两只工具的"复跑路径"与"下一批落地之后"自查）新增 1 条'
             '（根族：**我只在缺陷第一次被触发的那一侧验过工具，另一侧分支里的守卫等于没验过**）')
FREQ_LEAD = ['一句话总纲：本批屏侧仍一个字节没动（没烧录、没碰串口、COM14 不在，本遍只 `comports()` 只读列口），',
             '三处缺陷全部只在"复跑那一遍"或"下一批落地之后"这两个第一次没有的现场才暴露。']
FREQ_LEAD = ['> ' + l for l in FREQ_LEAD]
FREQ_ENTRY = [
    '[错误类型] **守卫只写在"另一侧分支"里 ⇒ 修好的那一次运行根本没执行它，第一次真正执行是下一次复跑 / 下一批落地'
    '（本批实测：一次 `AttributeError`、一次 `AssertionError`、一次把正确状态判成假红的口径）**',
    '→ 症状：三处。①订正器的时刻复核写在"前序载体存在"那一支，落地那遍没有前序载体 ⇒ 一次也没执行过；'
    '本批第一次复跑走到就抛 `AssertionError` —— 它拿载体的**写盘时刻**去比订正行**标题时刻**，两格本就该不等 '
    '（(104)「凭证写的时刻不等于它标的那一刻」换了个藏身处，同族第 4 次）。'
    '②落地器复跑支的反推解析式同样从未执行，第一次走到取到 `None` 再抛 `AttributeError` —— '
    '我把 witness 定位成"名字最新的那只载体"，而最新那只恰好是 buggy 代码自己写的（它里面写着 `md5 见台账行`）。'
    '③两只工具的"台账行之后只许有订正行""§38.21 不许存在"两道闸按**整只文件**算 ⇒ 本批（第四批）一落这两只文件它们立刻假红，'
    '而盘上没有任何东西错。①② 已在本批修好并各复跑过；③ 由本批落地后**当场把第三批两只工具再各跑一遍**做前向对照'
    '（判据 = 两只 rc=0 且"本批窗口之外有后续行"）。',
    '→ 形状：与 (81)「首跑崩溃的取证脚本也要入库」、(185)「崩溃那次的读数不作数」同族，新出的一层是**分支覆盖**：'
    '一道守卫是否可信，不由它有没有写在盘上决定，由它**有没有被执行过**决定；而幂等闸的写侧那一遍在结构上永远走不进读侧那一支 '
    '⇒ "复跑时才第一次执行"不是偶然，是这类脚本的固有形状。第 ③ 处是它的镜像：断言的**口径**（整只文件 vs 本批窗口）'
    '没有执行者，只有下一批落地那一刻才被发现。',
    '→ 为什么它危险：这类缺陷的报错与"盘真的坏了"完全同形。第一反应是"工具坏了"⇒ 要么把断言改松'
    '（缺陷从"未验证"降级成"未登记"），要么"重跑一次把它洗绿"（直接违反 (74)(82) 那一族）。'
    '两种反应都会把唯一能发现"越界改动 / 二次追加"的读数永久关掉 —— 而本项目的整套纪律就建在这几道闸上。',
    '→ 正确做法：①写侧产出台账行的那一遍**当场用读侧那套解析式回解一次**（阳性对照，本脚本的 `led_state` 就在写盘前那一步调用），'
    '两对数各自回来才继续；②witness 一律按**语义属性**定位（载体首行含 `MODE=LANDED_NOW`），绝不按名字/时间排序取"最新"，'
    '候选集为 0 只即 ABORT；③断言范围按**批次窗口右界**切：只认"本批最后一行 ~ 下一只 `## ` 标题之前"，'
    '窗口外的行逐字不参与两把尺比对、只要求进入与回读两侧相等；④"下一节不许存在"这类**禁止后续**的闸一律改写成"前后相等"'
    '（后续节存不存在是别人的批次，不是本批的不变量）；⑤载体首行的"本遍现跑于"必须是本遍 `datetime.now()`，'
    '与"台账行头时刻"分两格并列，并断言两格相等只在真的写了盘那一遍成立。',
    '→ **同族**：项目记忆 (63)~(65)、(81)、(99)、(102)、(103)、(104)、(185)；'
    '用户记忆 `feedback-verifiable-acceptance.md`「读数不落盘等于没跑」「否定式断言要配前置钉」「已跑完要带 rc 与载体文件名」。',
]

SEC = f'''
### 38.21 R55 第四批 = 第三批两只工具的**复跑路径**与**下一批落地之后**自查（{{RUN_AT}} 本节登记；**没烧录、没碰串口、没 push、屏侧零进展**）

- **本节登记什么**：§38.20 那批的两只工具（`hardware/r55_paperwork3.py` 落地器 + `hardware/r55_fix_paperwork3.py` 订正器）
  在 2026-09-24 15:0x~15:2x 各绿过一遍，本批为了"复跑仍然绿"这个承诺去真跑第二遍，结果**两只都在读侧崩了**，
  并且当场发现它们的前向口径会在本批（第四批）落地那一刻变成假红。四条工具改动 + 一条错误类型 + 本节，屏侧零动作。
- **① 分支覆盖：写侧那一遍永远走不到读侧那一支**。①订正器的时刻复核写在"前序载体存在"分支里，第一次执行就是本批复跑，
  一执行就抛 `AssertionError`（它拿载体**写盘时刻**去比订正行**标题时刻** —— 两格本就该不等，正是 (104) 那一族）；
  ②落地器复跑支的反推解析式同样第一次执行就抛 `AttributeError`（witness 被我按"名字最新"取，而最新那只是 buggy 代码写的，
  它的 FREQ 行里写的是 `md5 见台账行` 而不是一个 md5）。两次崩溃**都没有载体**（崩在写载体之前），所以这一格是叙述级证据；
  可核的替代证据是：修法本身已进脚本、且下面 ②③④ 三格都有盘上原件。
- **② 载体的"改前"格混取了两块盘（引文现读自 `{os.path.basename(C3_BUG)}`，逐字）**：
  `{Q_FREQ_BUG}` —— 同一行里 {_mb.group(1)} B 是**改后**文件的字节数（witness 在册的真改前是 {w3_bbytes} B）、
  {_mb.group(2)} 条 / {_mb.group(3)} 行是**改前**的读数，还顶着"现读"两个字；
  `{Q_DOC_BUG}` —— 更直白：改前改后同为 {_mdg.group(1)} B / {_mdg.group(2)} 行，而"标题 {_mdg.group(3)} -> {_mdg.group(6)}"又是按追加前后分的，一只文件不可能同时是两代。
  修法：复跑支一律**从盘上反推**改前串再取格，并逐项与该脚本唯一那次 `MODE=LANDED_NOW` 的载体（`{os.path.basename(C3_WIT)}`：
  `{Q_WIT}`）现读在册的改前三格 + md5 **逐字互核**，witness 候选不为恰好 1 只即 ABORT。
  `{os.path.basename(C3_BUG2)}` 是"FreqErr 已修、排查记录还没修"的中间版，它的 DOC 行与上一版**逐字相同** ⇒ 一次只修一只文件等于没修完。
- **③ 一格取错了列**：`{os.path.basename(C3F_BUG)}` 的 LEDGER 行原文含 `{Q_LEDGER_BUG[Q_LEDGER_BUG.index('（'):Q_LEDGER_BUG.index('）') + 1]}`，
  而 {w3_bl} 是第三批载体在册的 **BEFORE** 行数（AFTER 是 {w3_al}）⇒ "台账行 1-based 位置 == AFTER + 1" 这条等式当时是拿错列凑出来的，
  形式对、量的是别的东西。现已把等式两端的列名点名，并加一条现算断言。
- **④ 前向口径（本批就是它的阳性对照）**：第三批两只工具原本按**整只文件**算两把尺、还禁止"下一节 §38.21 存在" ⇒
  §38.20 里那句"§38.21 是下一批的事"本身就是前向假红。现改为**批次窗口右界**：本批只认"本批最后一行 ~ 下一只 `## ` 标题之前"，
  窗口外的行不参与两把尺比对、只要求进入与回读两侧相等；"禁止后续节存在"改成"节号计数前后相等"。
  载体名池也从 9 只扩到 19 只（复跑必新增一只，撞到上限会拒绝覆写而不是覆盖 —— 保留拒绝，只是把天花板抬高）。
- **⑤ 本节落地之后当场做前向对照**：本脚本在写盘 + 独立回读之后，把 `r55_paperwork3.py` 与 `r55_fix_paperwork3.py`
  各复跑一遍，判据 = 两只 `rc=0` 且第三批载体在册的"窗口外行数 / 后续批次数"由 0 变成非 0（见本批载体 POSCTL 行）。
  **判据在盘上、结论由脚本断言，不靠本节复述**；复跑那两遍各自新增一只第三批载体，名单同样在 POSCTL 行。
- **⑥ 写盘半径与末版封界（装了执行者）**：本批只写 `FreqErr.md`、排查记录、`hardware/r55_paperwork4*.txt` 三类，
  全部在 `hardware/ht305_sync/` 之外；`hardware/` 下第三批那两只工具脚本自身被本批改过（前向口径与同源格），
  它们是**工具**、不是归档物。封界判据 = 写盘前后各数一遍 `ht305_sync/` 的名字数 / 字节数 / 聚合 md5，两遍逐字相等（SEAL 行）。
- **⑦ 现场态（本遍现跑，不是登记常量）**：`git rev-list --count origin/main..HEAD` = **{rev}**、
  `git status --porcelain` = **{len(por)} 行**；串口 = `{port_names}` ⇒ **COM14 {"在" if has14 else "仍不在"}**，
  §38.13 那两行判据样本数照旧 0、肉眼确认 0 次 ⇒ **不播提示音**；docs 快照停在第九遍 {docs_n} 只 @{docs_at}、
  backups README 停在第九次读数 @{rd9_run} ⇒ §38.21 一落这两格即过期，第十遍 + 第十次读数是后续义务；
  第三批载体如今并存 {len(P3_CANDS)} 只（权威 = `{P3_AUTH}`）/ 订正器 {len(P3F_CANDS)} 只（权威 = `{P3F_AUTH}`）⇒
  权威按**序号**取最大那只，绝不按字典序（`_10` 会排在 `_2` 之前）；本批 ⑤ 的前向对照之后各 +1 只，那两只的名字只在本批载体 POSCTL 行。
- **本节没做（点名）**：① 没烧录、没碰串口（只 `comports()` 只读列口）；② 没 `git push`、零历史重写
  （rebase / filter-branch / **amend** 都没碰）；③ 没新建备份根、没重跑 `diff -rq`；④ 零删除，含 `%TEMP%` 里那只在册明文抓回件；
  ⑤ 没动四只记忆文件（本批只读它们取现场态）；⑥ 提交轮 #9 与第十遍 docs 快照在本节之后；
  ⑦ 第 ①② 两次崩溃**没有盘上 traceback 载体**（崩在写载体之前），那一格是叙述级证据，本节没有把它写成可复算判据。
'''

def led_state(line):
    pre, post = split_ledger(line)
    return led_pair(pre, 'BEFORE'), led_pair(post, 'AFTER')


def extra_ok(ls, a_i, end):
    """本批窗口在台账行之后只许长出"空行 / 本批订正行"（第三批就靠这条把口径钉住）。
    写成"台账行必须正好是窗口末行"的话，下一批订正行一追加就把本批闸染成假红。"""
    bad = [l for l in ls[a_i + 1:end] if l.strip() and not l.startswith(FIXPFX)]
    assert not bad, 'ABORT: 台账行之后、窗口末行之前出现了非"空行 / 订正行"的内容 ⇒ %r' % bad[0][:40]
    return len([l for l in ls[a_i + 1:end] if l.startswith(FIXPFX)])


# ---------- 两遍各自算出"改前 / 终态"读数：改前的每一格都必须来自同一块盘的同一次读取 ----------
_ls_f = freq_old.split('\r\n')
_ls_d = doc_old.split('\r\n')
if MODE == 'LANDED_NOW':
    RUN_AT = NOW_AT
    freq_before_str, doc_pre_str = freq_old, doc_old
    b_kind, b_lines = kinds(freq_before_str), freq_before_str.count('\r\n')
    app = ('\r\n' + FREQ_HEAD + '\r\n\r\n' + '\r\n'.join(FREQ_LEAD) + '\r\n\r\n' + '\r\n'.join(FREQ_ENTRY))
    mid = freq_before_str + app + '\r\n\r\n' + LEDGER_TMPL + '\r\n'
    a_kind, a_lines = kinds(mid), mid.count('\r\n')
    assert a_kind == b_kind + 1, 'ABORT: 台账条数增量不是 1：%d -> %d' % (b_kind, a_kind)
    ledger = (LEDGER_TMPL.replace('@T@', RUN_AT).replace('@BK@', str(b_kind)).replace('@BL@', str(b_lines))
              .replace('@AK@', str(a_kind)).replace('@AL@', str(a_lines)))
    assert led_state(ledger) == ((b_kind, b_lines), (a_kind, a_lines)), \
        'ABORT: 写侧刚产出的台账行，用读侧那套式子回解不出来 ⇒ 两把式子不同形（第三批就是死在这里）'
    FREQ_SEG = app + '\r\n\r\n' + ledger + '\r\n'
    freq_new = freq_before_str + FREQ_SEG
    assert (kinds(freq_new), freq_new.count('\r\n')) == (a_kind, a_lines), \
        'ABORT: 回填四个数之后两把尺漂了 ⇒ 数算在了中间串上（(99) 族）'
    assert freq_new.startswith(freq_before_str + app), 'ABORT: 不再是纯追加'
    li = [i for i, l in enumerate(freq_new.split('\r\n')) if LED4 in l and not l.startswith(FIXPFX)]
    assert len(li) == 1, 'ABORT: 待写串里本批台账行有 %d 处' % len(li)
    assert blanks_above(freq_new, li[0]) == 1, 'ABORT: 待写台账行上方不是恰好一只空行 ⇒ (102) 那一族，写盘前拦下'
    _led_pos = li[0] + 1
    _end = _led_pos          # 写盘那一遍：台账行就是本批窗口末行（它之后什么都没有）
    SEC_LAND = '\r\n' + SEC.replace('{RUN_AT}', RUN_AT).strip('\r\n').replace('\n', '\r\n') + '\r\n'
    doc_new = doc_old + SEC_LAND
    dh = [i for i, l in enumerate(doc_new.split('\r\n')) if l.startswith(SEC_ANCHOR)]
    assert len(dh) == 1 and blanks_above(doc_new, dh[0]) == 1, 'ABORT: 待写 §38.21 不是恰好一处 / 上方不缺那只空行'
    FREQ_AT_STR, DOC_AT_STR = freq_new, doc_new
    FREQ_TAIL_REST, DOC_TAIL_REST = '', ''
    LATER_N, LATER_LINES, DOC_LATER, DOC_LATER_HEADS = 0, 0, 0, 0
    BOUNDSHAPE, DOC_NEXT_SEC = '写盘那一遍：§38.21 就是文件末节（下一节尚不存在）', '-'
    WIN_BOUND = '写盘那一遍：本批台账行就是文件末行（下一批标题尚不存在）'
    N_FIX = 0
    PRE_KIND = '现读'
    _wit_note = '本遍即写盘那一遍 ⇒ 改前两文件是**现读**的盘，不需要 witness'
else:
    cut = freq_old.index(FREQ_HEAD)
    freq_before_str = freq_old[:cut].rstrip('\r\n') + '\r\n'
    b_kind, b_lines = kinds(freq_before_str), freq_before_str.count('\r\n')
    _wit = [c for c in _self_prior
            if 'MODE=LANDED_NOW' in line_only(os.path.join(HDIR, c), r'^R55 第四批 paperwork 落地器', '本脚本前序载体首行')]
    assert len(_wit) <= 1, 'ABORT: 前序载体里"写盘那一遍"（MODE=LANDED_NOW）有 %d 只 ⇒ 反推值有两份互不相容的原件' % len(_wit)
    if _wit:
        # 正常态：本批落地那遍的载体就是 witness，它的"改前四格"是现读的盘
        C4_WIT = os.path.join(HDIR, _wit[0])
        _wl = line_only(C4_WIT, r'^FREQ 追加之前', '写盘那一遍载体的 FREQ 行')
        _dl = line_only(C4_WIT, r'^DOC ', '写盘那一遍载体的 DOC 行')
        _wit_note = os.path.basename(C4_WIT) + '（本批落地那遍现读的 witness）'
    elif _self_prior:
        # 崩溃取证遍复跑态：本批**没有**"写盘那一遍"载体（那一遍崩在写载体之前）⇒ 取链上前一只在册的改前格
        C4_WIT = os.path.join(HDIR, authority(_self_prior))
        _wl = line_only(C4_WIT, r'^FREQ 追加之前', '链上前一只载体的 FREQ 行')
        _dl = line_only(C4_WIT, r'^DOC ', '链上前一只载体的 DOC 行')
        _wit_note = os.path.basename(C4_WIT) + '（本批无"写盘那一遍"载体：落地那遍崩在写载体之前 ⇒ 取链上前一只的在册改前格）'
    else:
        # 首次崩溃取证遍：连链上载体也没有 ⇒ 改到**内容匹配**取证 —— 扫第三批落地器的在册载体，
        # 取它们"盘上现值（含后续批次）"那一格；只有与本遍反推串逐字相等的那些只算 witness。
        C4_WIT = None
        _ev = []
        for _c in P3_CANDS:
            _t = rd(os.path.join(HDIR, _c)).replace('\r\n', '\n')
            _ef = re.search(r'盘上现值（含后续批次）([\d,]+) B / (\d+) 条 / (\d+) 行 / md5 ([0-9a-f]{8})', _t)
            _ed = re.search(r'盘上现值（含后续小节）([\d,]+) B / (\d+) 行 / 标题 (\d+)', _t)
            if not _ef and not _ed:
                continue          # 这只载体早于"盘上现值"两格的格式（落地那一遍），它不参与内容匹配
            assert _ef and _ed, 'ABORT: 第三批载体 %s 只缺两格里的一格 ⇒ 内容匹配取证读不得半截：%r / %r' % (_c, _ef, _ed)
            _ev.append((_c, int(_ef.group(1).replace(',', '')), int(_ef.group(2)), int(_ef.group(3)), _ef.group(4),
                        int(_ed.group(1).replace(',', '')), int(_ed.group(2)), int(_ed.group(3))))
        _pre_b, _pre_k, _pre_l = len(freq_before_str.encode('utf-8')), b_kind, b_lines
        assert _ev, 'ABORT: 第三批在册 %d 只载体里没有一只带"盘上现值"两格 ⇒ 内容匹配取证没有任何原件' % len(P3_CANDS)
        _pre_m = hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8]
        _m4 = [e for e in _ev if e[1:5] == (_pre_b, _pre_k, _pre_l, _pre_m)]
        assert _m4, 'ABORT: 反推的改前四格与第三批任何一只在册载体的"盘上现值"格都不等 ⇒ 反推串不可信（%d 只候选全不中）' % len(_ev)
        assert len(set(e[1:5] for e in _m4)) == 1, 'ABORT: 内容匹配到的多只载体彼此读数不一致 ⇒ 取证链断了'
        _e = _m4[0]
        w_b, w_k, w_l, w_md5 = _e[1], _e[2], _e[3], _e[4]
        wd_b, wd_l, wd_h, wd_md5 = _e[5], _e[6], _e[7], None
        _wl = _dl = None
        _wit_note = '%d 只第三批载体的"盘上现值"格（首只 %s，其余同名格逐字相等）⇒ 本批落地那遍崩在写载体之前，改按内容匹配取证' % (
            len(_m4), _e[0])
    if C4_WIT:
        _mw = re.search(r'^FREQ 追加之前(?:现读|反推) ([\d,]+) B / (\d+) 条 / (\d+) 行 -> .*?md5\(改前串\) ([0-9a-f]{8}) -> ', _wl)
        assert _mw, 'ABORT: witness 的 FREQ 行不合"改前 B/条/行 + md5(改前串)"句式 ⇒ 反推值无从互核：%r' % _wl[:60]
        w_b, w_k, w_l, w_md5 = int(_mw.group(1).replace(',', '')), int(_mw.group(2)), int(_mw.group(3)), _mw.group(4)
        _md = re.search(r'^DOC ([\d,]+) B / (\d+) 行 / 标题 (\d+) -> .*?md5\(改前串\) ([0-9a-f]{8}) -> ', _dl)
        assert _md, 'ABORT: witness 的 DOC 行不合"改前三格 + md5(改前串)"句式 ⇒ 反推值无从互核：%r' % _dl[:60]
        wd_b, wd_l, wd_h, wd_md5 = int(_md.group(1).replace(',', '')), int(_md.group(2)), int(_md.group(3)), _md.group(4)
    _dcut = doc_old.index(SEC_ANCHOR)
    _i21 = [i for i, l in enumerate(_ls_d) if l.startswith(SEC_ANCHOR)]
    assert len(_i21) == 1, 'ABORT: §38.21 标题在盘上有 %d 处 ⇒ 二次追加' % len(_i21)
    _dnx = [i for i in range(_i21[0] + 1, len(_ls_d)) if _ls_d[i].startswith(('### ', '## '))]
    if _dnx:
        # 右界只认"下一只节标题那一行"；它上方**有无空行**是下一批的排版口径，不是本批窗口的判据。
        #   旧写法在这里硬要求空行 ⇒ 只要后一批把小节紧贴上一段落下来（R56 第一批 §38.22 就是），
        #   本批的读侧守卫立刻假红 —— 那是 §38.21 第 ① 格"守卫写在只有我的世界里"的又一处现场。
        #   仍然要挡住"在半截内容里切"：末行不许是一句裸正文，必须是本仓库四种块前缀之一。
        _db = _ls_d[_dnx[0] - 1]
        if _db.strip():
            assert _db.startswith(('> ', '- ', '@', '#### ')), \
                'ABORT: §38.21 窗口右界上一行是裸正文 %r ⇒ 真的是在半截内容里切的' % _db[:24]
            BOUNDSHAPE = '紧接（该小节标题上方 0 只空行）'
            _dend = _dnx[0]
        else:
            BOUNDSHAPE = '空行分隔'
            _dend = _dnx[0] - 1
        DOC_NEXT_SEC = _ls_d[_dnx[0]][:40]
    else:
        BOUNDSHAPE = '无下一节（§38.21 就是文件末节）'
        DOC_NEXT_SEC = '-'
        _dend = len(_ls_d) - 1
    DOC_AT_STR = '\r\n'.join(_ls_d[:_dend]) + '\r\n'
    assert doc_old.startswith(DOC_AT_STR), 'ABORT: 排查记录窗口不是盘上开头的逐字前缀 ⇒ 行序与字符序对不上'
    doc_pre_str = doc_old[:_dcut].rstrip('\r\n') + '\r\n'
    assert DOC_AT_STR.startswith(doc_pre_str), 'ABORT: 窗口不在改前串之后 ⇒ 切点没落在行边界上'
    SEC_LAND = DOC_AT_STR[len(doc_pre_str):]        # = 落地那遍追加的那一段（含它上方那只空行）
    assert SEC_LAND.startswith('\r\n' + SEC_ANCHOR), 'ABORT: 反推出的 §38.21 段不是"空行 + 节标题"开头'
    DOC_TAIL_REST = doc_old[len(DOC_AT_STR):]
    DOC_LATER = len(_ls_d) - 1 - _dend
    DOC_LATER_HEADS = heads(DOC_TAIL_REST)
    _li = [i for i, l in enumerate(_ls_f) if LED4 in l and not l.startswith(FIXPFX)]
    assert len(_li) == 1, 'ABORT: 盘上本批台账行有 %d 处 ⇒ 二次追加' % len(_li)
    _fx = [i for i, l in enumerate(_ls_f) if l.startswith(FIXPFX) and 'R55 第四批' in l]
    assert len(_fx) <= 1, 'ABORT: 本批订正行在盘上有 %d 处' % len(_fx)
    _last = max([_li[0]] + _fx)
    _end, LATER_N, _wtail, WIN_BOUND = win_end(_ls_f, _last)
    assert not _wtail, 'ABORT: 本批窗口之后、下一批标题之前还有 %d 行 ⇒ %r' % (len(_wtail), _wtail[0][:30])
    FREQ_AT_STR = '\r\n'.join(_ls_f[:_end]) + '\r\n'
    assert freq_old.startswith(FREQ_AT_STR), 'ABORT: 台账窗口不是盘上开头的逐字前缀 ⇒ 行序与字符序对不上'
    FREQ_SEG = FREQ_AT_STR[len(freq_before_str):]
    FREQ_TAIL_REST = freq_old[len(FREQ_AT_STR):]
    LATER_LINES = freq_old.count('\r\n') - _end
    assert blanks_above(freq_old, _li[0]) == 1, 'ABORT: 复跑那遍读到台账行上方不是 1 只空行'
    N_FIX = extra_ok(_ls_f, _li[0], _end)
    ledger = _ls_f[_li[0]]
    RUN_AT = re.search(r'【(' + TS + ') 复跑｜R55 第四批', ledger).group(1)
    _led_pos = _li[0] + 1
    a_kind, a_lines = kinds(FREQ_AT_STR), _end
    _led_b, _led_a = led_state(ledger)
    assert _led_b == (b_kind, b_lines), \
        'ABORT: 台账行在册的 BEFORE(%s,%s) 与本遍反推出的改前(%d,%d) 不等 ⇒ 中间别处动过后一半内容' % (
            _led_b[0], _led_b[1], b_kind, b_lines)
    assert a_kind == _led_a[0] and a_lines >= _led_a[1], \
        'ABORT: 窗口终态与台账在册的 AFTER 不吻合：条数 %d vs %d、行数 %d vs %d（行数只许因订正行而变长）' % (
            a_kind, _led_a[0], a_lines, _led_a[1])
    freq_new = doc_new = None
    PRE_KIND = '反推'
    # witness 互核：反推出来的"改前"四格（FreqErr）+ 三格（排查记录）必须与在册值逐字相等
    assert (len(freq_before_str.encode('utf-8')), b_kind, b_lines,
            hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8]) == (w_b, w_k, w_l, w_md5), \
        'ABORT: 反推的改前正文四格与 witness 在册不等：(%d,%d,%d,%s) vs (%d,%d,%d,%s)' % (
            len(freq_before_str.encode('utf-8')), b_kind, b_lines,
            hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8], w_b, w_k, w_l, w_md5)
    _doc_pre4 = (len(doc_pre_str.encode('utf-8')), doc_pre_str.count('\r\n'), heads(doc_pre_str),
                 hashlib.md5(doc_pre_str.encode('utf-8')).hexdigest()[:8])
    assert _doc_pre4[:3] == (wd_b, wd_l, wd_h), 'ABORT: 反推的改前排查记录三格与在册不等：%s vs %s' % (_doc_pre4[:3], (wd_b, wd_l, wd_h))
    assert wd_md5 is None or _doc_pre4[3] == wd_md5, 'ABORT: 反推的改前 md5 与在册不等：%s vs %s' % (_doc_pre4[3], wd_md5)
assert (MODE == 'LANDED_NOW') == (RUN_AT == NOW_AT), 'ABORT: 时刻两格与 MODE 不自洽 ⇒ 有一格是抄来的'

# ---------- 零容忍闸（对将被写出 / 已在盘上的那**一段**，不数整只文件、不数中间串）----------
for seg, name in ((FREQ_SEG, 'FreqErr 本批段'), (SEC_LAND, '§38.21')):
    assert '\\' not in seg, 'ABORT: %s 里有反斜杠 ⇒ 正是 §38.18 那一族' % name
    assert not re.search(r'\{[A-Za-z_][A-Za-z0-9_]*\}|@[A-Z]+@', seg), 'ABORT: %s 里有未回填占位' % name
    assert LED3 not in seg, 'ABORT: %s 把第三批的台账锚抄进来了 ⇒ 第三批"数本批台账行"那把尺会命中两处（(40) 族）' % name
assert line_hits(FREQ_AT_STR, LED4) == 1 and head_hits(DOC_AT_STR, SEC_ANCHOR) == 1, \
    'ABORT: 本批锚在窗口内不止一处（台账行 %d / §38.21 标题 %d）⇒ 二次追加，或正文把锚抄给自己数了（(40) 族）' % (
        line_hits(FREQ_AT_STR, LED4), head_hits(DOC_AT_STR, SEC_ANCHOR))

# ---------- 本批窗口的读数（载体"之后"那一侧只许记它，盘上全量另记一格）----------
b_md5 = hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8]
at_bytes, at_kind, at_lines = len(FREQ_AT_STR.encode('utf-8')), kinds(FREQ_AT_STR), FREQ_AT_STR.count('\r\n')
at_md5 = hashlib.md5(FREQ_AT_STR.encode('utf-8')).hexdigest()[:8]
dp_bytes, dp_lines, dp_heads = len(doc_pre_str.encode('utf-8')), doc_pre_str.count('\r\n'), heads(doc_pre_str)
dp_md5 = hashlib.md5(doc_pre_str.encode('utf-8')).hexdigest()[:8]
dat_bytes, dat_lines, dat_heads = len(DOC_AT_STR.encode('utf-8')), DOC_AT_STR.count('\r\n'), heads(DOC_AT_STR)
dat_md5 = hashlib.md5(DOC_AT_STR.encode('utf-8')).hexdigest()[:8]
assert (at_kind, at_lines) == (b_kind + 1, b_lines + FREQ_SEG.count('\r\n')), \
    'ABORT: 窗口终态两把尺与"改前 + 本批那一段"的算式不吻合：(%d,%d) vs (%d,%d)' % (
        at_kind, at_lines, b_kind + 1, b_lines + FREQ_SEG.count('\r\n'))
assert (dat_heads, dat_lines) == (dp_heads + 1, dp_lines + SEC_LAND.count('\r\n')), \
    'ABORT: 窗口终态标题/行数与"改前 + 本批那一节"的算式不吻合：(%d,%d) vs (%d,%d)' % (
        dat_heads, dat_lines, dp_heads + 1, dp_lines + SEC_LAND.count('\r\n'))

# ---------- 末版封界：写盘前数一遍 ----------
seal0 = sync_seal()

# ---------- 写盘（幂等：REWROTE 模式一律不动盘）----------
if MODE == 'LANDED_NOW':
    open(FREQ, 'w', encoding='utf-8', newline='').write(freq_new)
    open(DOC, 'w', encoding='utf-8', newline='').write(doc_new)

# ---------- 写盘后独立回读（另一次调用，不复用上面那次的字符串）----------
freq_back, doc_back = rd(FREQ), rd(DOC)
crlf_pure(FREQ)
crlf_pure(DOC)
if MODE == 'LANDED_NOW':
    assert freq_back.startswith(freq_old) and doc_back.startswith(doc_old), 'ABORT: 独立回读显示不是纯追加'
    assert freq_back == freq_new and doc_back == doc_new, 'ABORT: 回读与待写字节不逐字相同'
_lsb = freq_back.split('\r\n')
bl_f = [i for i, l in enumerate(_lsb) if LED4 in l and not l.startswith(FIXPFX)]
assert len(bl_f) == 1, 'ABORT: 回读显示本批台账行 %d 处 ⇒ 二次追加' % len(bl_f)
_bfx = [i for i, l in enumerate(_lsb) if l.startswith(FIXPFX) and 'R55 第四批' in l]
assert len(_bfx) <= 1, 'ABORT: 回读显示本批订正行 %d 处' % len(_bfx)
_bend, _bn, _btail, _bbound = win_end(_lsb, max(bl_f + _bfx))
assert _bbound == WIN_BOUND, 'ABORT: 独立回读算出的窗口右界形状(%s) 与进入时(%s) 不等 ⇒ 两遍之间有人重排了行' % (
    _bbound, WIN_BOUND)
assert not _btail, 'ABORT: 回读显示本批窗口之后、下一批标题之前还有 %d 行 ⇒ %r' % (len(_btail), _btail[0][:30])
assert freq_back.count(LED3) == 1, 'ABORT: 回读显示第三批锚命中 %d 处（应为它自己那 1 处）⇒ 本批越界抄了它' % freq_back.count(LED3)
assert blanks_above(freq_back, bl_f[0]) == 1, 'ABORT: 回读显示台账行上方空行 %d 只' % blanks_above(freq_back, bl_f[0])
assert _lsb[bl_f[0]] == ledger, 'ABORT: 回读的台账行与本遍算出的那一行不逐字相同'
assert bl_f[0] + 1 == _led_pos, 'ABORT: 回读显示台账行 1-based 位置 %d != 进入时 %d ⇒ 两遍之间本批窗口之上被插过行' % (
    bl_f[0] + 1, _led_pos)
assert _bend >= _led_pos and extra_ok(_lsb, bl_f[0], _bend) == len(_bfx), \
    'ABORT: 回读窗口在台账行之后混进了非订正行内容（末行 %d / 台账 %d / 订正行 %d 只）' % (_bend, _led_pos, len(_bfx))
assert '\r\n'.join(_lsb[:_bend]) + '\r\n' == FREQ_AT_STR, \
    'ABORT: 回读看到的本批窗口与进入时算的不逐字相同 ⇒ 两遍之间有别的写入者在这块盘上动过'
assert freq_back[len(FREQ_AT_STR):] == FREQ_TAIL_REST, 'ABORT: 回读看到的"窗口之外"与进入时不逐字相同 ⇒ 后续批次的行被挪动过'
_dlsb = doc_back.split('\r\n')
_dh = [i for i, l in enumerate(_dlsb) if l.startswith(SEC_ANCHOR)]
assert len(_dh) == 1, 'ABORT: 回读显示 §38.21 %d 处' % len(_dh)
assert blanks_above(doc_back, _dh[0]) == 1, 'ABORT: 回读显示 §38.21 上方缺空行'
assert doc_back[len(DOC_AT_STR):] == DOC_TAIL_REST, 'ABORT: 回读看到的排查记录窗口之外与进入时不逐字相同'
DISK_KIND_LATER, DISK_LINES_LATER = kinds(FREQ_TAIL_REST), FREQ_TAIL_REST.count('\r\n')
assert (LATER_LINES, LATER_N) == (DISK_LINES_LATER, _bn), \
    'ABORT: 窗口外行数两种算法不等：进入时 %d / 回读 %d（标题 %d vs %d）' % (LATER_LINES, DISK_LINES_LATER, LATER_N, _bn)
assert (kinds(freq_back), freq_back.count('\r\n')) == (at_kind + DISK_KIND_LATER, at_lines + DISK_LINES_LATER), \
    'ABORT: 盘上全量两把尺 != 本批窗口 + 窗口外 ⇒ 窗口切点没落在行边界上'
assert heads(doc_back) == dat_heads + DOC_LATER_HEADS, \
    'ABORT: 排查记录标题数 %d != 本批窗口内 %d + 窗口外 %d ⇒ 后续小节没按整节追加（也不是 +1 的巧合）' % (
        heads(doc_back), dat_heads, DOC_LATER_HEADS)
seal1 = sync_seal()
assert seal0 == seal1, 'ABORT: 归档目录被本批动过 ⇒ gen 24 末版降级（写盘前 %s / 写盘后 %s）' % (seal0, seal1)

# ---------- 前向对照（§38.21 第 ⑤ 格的执行者）：本批落地之后当场把第三批两只工具各复跑一遍 ----------
def row_of(out, prefix, name):
    hits = [l for l in out.splitlines() if l.startswith(prefix)]
    assert len(hits) == 1, 'ABORT: %s 的输出里前缀 %r 的行有 %d 只 ⇒ 判据落不到具体那一行' % (name, prefix, len(hits))
    return hits[0]


def cell(text, pat, name):
    hits = re.findall(pat, text)
    assert len(hits) == 1, 'ABORT: %s 里式子 %r 命中 %d 处（须恰好 1）⇒ 本批的正则与它的口径已经脱节（第三批正是死在"式子从没执行过"）' % (
        name, pat, len(hits))
    return tuple(int(x) for x in hits[0])


pos = []
for tool, tag, cands in ((P3, '落地器', P3_CANDS), (P3F, '订正器', P3F_CANDS)):
    nm = os.path.basename(tool)
    r = subprocess.run([sys.executable, tool], capture_output=True, cwd=REPO)
    out = r.stdout.decode('utf-8', 'replace')
    assert r.returncode == 0, 'ABORT: 第三批 %s(%s) 复跑 rc=%d ⇒ 前向窗口闸破了：\n%s' % (
        nm, tag, r.returncode, out[-1200:] + r.stderr.decode('utf-8', 'replace')[-1200:])
    carrier = row_of(out, 'CARRIER=hardware/', nm).split('CARRIER=hardware/')[1].strip()
    assert carrier and carrier not in cands, 'ABORT: %s 复跑没新增载体（%s 在册）⇒ 它走的不是"复跑"那一支' % (nm, carrier)
    verdict = row_of(out, 'VERDICT=', nm).split('VERDICT=')[1].strip()
    head1 = rd(os.path.join(HDIR, carrier)).split('\n')[0]
    assert 'MODE=REWROTE_CARRIER_ONLY' in head1, \
        'ABORT: %s 新载体 %s 首行不是 REWROTE_CARRIER_ONLY ⇒ 前向对照没走到读侧那一支（本批第 5 条要抓的就是这个）：%s' % (
            nm, carrier, head1[:60])
    if tool == P3:
        f_lat, f_lines = cell(row_of(out, 'FREQ 追加之前', nm), r'其中窗口外 (\d+) 条 / (\d+) 行', nm + ' FREQ 行')
        d_lines, d_heads = cell(row_of(out, 'DOC ', nm), r'其中窗口外 (\d+) 行 / (\d+) 只标题', nm + ' DOC 行')
    else:
        f_lines, f_lat = cell(row_of(out, 'WINDOW ', nm), r'窗口外（后续批次）尚有 (\d+) 行 / (\d+) 条', nm + ' WINDOW 行')
        d_lines = d_heads = None
    assert f_lines > 0 and (d_lines is None or d_lines > 0), \
        'ABORT: %s 前向对照不过：本批窗口外行数 FREQ=%d / DOC=%s ⇒ 第三批的窗口口径没真的生效（还是在按整只文件算）' % (
            nm, f_lines, d_lines)
    pos.append((nm, tag, r.returncode, verdict, carrier, f_lat, f_lines, d_lines, d_heads))
for p in pos:
    assert p[2] == 0 and p[6] > 0 and (p[7] is None or p[7] > 0), 'ABORT: 前向对照判据破了：%s' % (p,)
seal2 = sync_seal()
assert seal0 == seal2, 'ABORT: 第三批两只工具复跑动了归档目录 ⇒ 末版封界破（前 %s / 后 %s）' % (seal0, seal2)
assert kinds(freq_back) == CRASH_DISK_KIND + DISK_KIND_LATER, \
    'ABORT: 盘上全量条数(%d) != 崩溃那一遍在册的盘上读数(%d) + 本批窗口外条数(%d) ⇒ 崩溃之后到本遍之间 FreqErr 被改过的量对不上，POSCTL_CRASH 那句要重推' % (
        kinds(freq_back), CRASH_DISK_KIND, DISK_KIND_LATER)

b_md5 = hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8]


def _no_blank_above(ls):
    hs = [i for i, l in enumerate(ls) if l.startswith('## ') or l.startswith('### ')]
    return len(hs), len([i for i in hs if i and ls[i - 1].strip()])


FREQ_HN, FREQ_HBAD = _no_blank_above(freq_back.split('\r\n'))
DOC_HN, DOC_HBAD = _no_blank_above(doc_back.split('\r\n'))
lines = [
    'R55 第四批 paperwork 落地器（FreqErr 1 条 + 排查记录 §38.21 + 前向对照），本遍现跑于 %s；本批台账行头时刻 = %s；MODE=%s' % (
        NOW_AT, RUN_AT, MODE),
    'FREQ 追加之前%s %s B / %d 条 / %d 行 -> 之后（本批窗口末行 %d） %s B / %d 条 / %d 行 ; md5(改前串) %s -> %s ; 行尾=纯 CRLF ; '
    '"改前"四格来源 = %s ; 盘上现值（含后续批次）%s B / %d 条 / %d 行 / md5 %s…，其中窗口外 %d 条 / %d 行（后续批标题 %d 只）' % (
        PRE_KIND, money(len(freq_before_str.encode('utf-8'))), b_kind, b_lines, at_lines, money(at_bytes), at_kind, at_lines,
        b_md5, at_md5, _wit_note, money(len(freq_back.encode('utf-8'))), kinds(freq_back), freq_back.count('\r\n'),
        hashlib.md5(freq_back.encode('utf-8')).hexdigest()[:8], DISK_KIND_LATER, DISK_LINES_LATER, LATER_N),
    'DOC %s B / %d 行 / 标题 %d -> %s B / %d 行 / 标题 %d（本批窗口末）; md5(改前串) %s -> %s ; §38.21 上方空行数 = %d ; '
    '盘上现值（含后续小节）%s B / %d 行 / 标题 %d，其中窗口外 %d 行 / %d 只标题' % (
        money(dp_bytes), dp_lines, dp_heads, money(dat_bytes), dat_lines, dat_heads, dp_md5, dat_md5,
        blanks_above(doc_back, _dh[0]),
        money(len(doc_back.encode('utf-8'))), doc_back.count('\r\n'), heads(doc_back), DOC_LATER, DOC_LATER_HEADS),
    'BOUND 本批两处窗口右界形状：FreqErr 台账侧 = %s ；排查记录 §38.21 侧 = %s（下一节标题现读 %r）。'
    '这两道守卫在 R56 之前都硬要求右界上方是空行，R56 第一批把 §38.22 / R56 小节标题紧贴上一段落下来 ⇒ 本批复跑假红一次'
    '（§38.21 第 ① 格"守卫写在只有我的世界里"的又一处现场，且**同时红在两只文件上**）。'
    '现在两种形状都收，但仍要求段末行以 > / - / @ / #### 开头 ⇒ 裸正文半截切照样红。'
    '盘上现算：FreqErr %d 只 `## ` 标题里 %d 只上方非空行、排查记录 %d 只 `##`/`###` 标题里 %d 只上方非空行 '
    '⇒ "上方必空行"从来不是全文不变量，本守卫收两种形状不是给 R56 开后门' % (
        WIN_BOUND, BOUNDSHAPE, DOC_NEXT_SEC, FREQ_HN, FREQ_HBAD, DOC_HN, DOC_HBAD),
    'LEDGER 台账行 1-based 位置 = 进入时 %d / 回读 %d（两遍逐字相等）; 本批窗口末行 = 进入时 %d / 回读 %d，'
    '其间只许"空行 + 本批订正行"（本批订正行现 %d 只）; 台账行上方空行数 = %d ; 台账锚命中行数 = %d ; '
    '第三批锚命中数 = %d（那是它自己那一只，本批一个字没抄）' % (
        _led_pos, bl_f[0] + 1, _end, _bend, N_FIX, blanks_above(freq_back, bl_f[0]), line_hits(freq_back, LED4),
        freq_back.count(LED3)),
    'SEAL 末版封界（ht305_sync/ 名字数 / 字节数 / 聚合 md5）：写盘前 %s ; 写盘后 %s ; 前向对照复跑后 %s ⇒ 三遍逐字相等，本批零写入归档目录' % (
        seal0, seal1, seal2),
    'POSCTL 前向对照 = 本批落地后当场复跑第三批两只工具：%s' % (
        ' ; '.join('%s(%s) rc=%d %s 新载体=%s FREQ 窗口外=%d 条/%d 行%s' % (
            n, tg, rc, v, k, fl, ln, '' if dl is None else ' / DOC 窗口外=%d 行/%d 只标题' % (dl, dh))
                   for n, tg, rc, v, k, fl, ln, dl, dh in pos))
        + ' ⇒ 判据 = 两只 rc=0 **且新载体首行 MODE=REWROTE_CARRIER_ONLY**（走到的正是第三批从未执行过的读侧那一支）'
          '且窗口外行数 > 0（第四批落地之前恒为 0）',
    'POSCTL_CRASH 本批第一次真跑（第三批落地器复跑那遍于 %s 写下 r55_paperwork3_10.txt）在 POSCTL 第二只上崩：订正器 rc=1 —— '
    '它把订正行在册的三把尺条数（本批窗口 %d 条）与**整只文件**现值 %d 条比 ⇒ 第四批一落地这条比对必假红，'
    '是 §38.21 第 ① 格"另一侧分支从未执行"的又一处现场、也是整只文件口径的第四处。'
    '修法 = `hardware/r55_fix_paperwork3.py` 里那条比对改成按窗口（WIN_KIND），错误消息同时点名盘上全量与窗口外条数；'
    '本遍复跑它 rc=0（见上一行）。该缺陷的正文登记随本批订正遍落 §38.21 之下（本遍不动台账条数）' % (
        CRASH_AT, CRASH_WIN_KIND, CRASH_DISK_KIND),
    'WITNESS 本批"改前四格"的来源 = %s ; 引用于 §38.21 的三格混取旧载体原件 = %s(FREQ+DOC) / %s(DOC) / %s(LEDGER)，'
    '三段引文运行时现读、逐字插入 ; 第三批写盘那一遍现跑于 %s、它的改前 md5 = %s（§38.21 ② 那句"与 witness 逐字互核"以这一行为基准）' % (
        _wit_note, os.path.basename(C3_BUG), os.path.basename(C3_BUG2), os.path.basename(C3F_BUG), P3_LAND_AT, w3_bmd5),
    'FIELD rev-list=%s porcelain=%d ports=%s COM14=%s ; docs 停在第九遍 %s 只 @%s ; backups 停在第九次 @%s' % (
        rev, len(por), port_names, 'PRESENT' if has14 else 'ABSENT', docs_n, docs_at, rd9_run),
    'GUARD 反斜杠=0 / 未回填占位=0 / 第三批锚未抄进本批正文（本批那一段断言，不数整只文件）/ 纯追加 + 独立回读逐字 / '
    '台账行与 §38.21 上方各恰好一只空行 / 两把尺在最终串上数 / 写侧产出台账行那遍用读侧同一条解析式回解一次（阳性对照）/ '
    'witness 按语义属性（MODE=LANDED_NOW）定位且候选不为 1 即 ABORT / 反推的改前四格与 witness 逐字互核 / '
    '断言范围按批次窗口右界切（窗口外只要求进入与回读两侧逐字相等）/ 封界有执行者（三遍）/ 前向对照有执行者（两只 rc + 新载体 MODE + 窗口外行数）',
    'VERDICT=' + ('PAPERWORK4_LANDED' if MODE == 'LANDED_NOW' else 'PAPERWORK4_STATE_VERIFIED'),
]
open(CARRIER, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('CARRIER=hardware/' + os.path.basename(CARRIER))
