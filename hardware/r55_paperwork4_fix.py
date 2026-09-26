# R55 第四批落地之后的**自查订正遍**：把"三处现场"应读作"四处"这件事，以**只追加**的方式落进两只 CRLF 文件
#   ① FreqErr.md —— 本批台账行之下补"空行 + 订正行"（第四批的窗口口径 `extra_ok` 正是为此留的口子）
#   ② hardware/20260919_墨水屏点屏排查记录.md —— §38.21 之下追加订正句（不改写上面任何一行）
# 本遍自己的前向对照 = 追加**之后**当场把 `hardware/r55_paperwork4.py` 再跑一遍：
#   那一只的窗口闸"台账行之后只许空行 / 订正行"那一支，在本批落地那两遍里拿到的订正行数恒为 0，
#   本遍是它第一次拿到非 0 —— 正是 §38.21 ① 格所说"另一侧分支从未执行"的口径，本遍不能只登记别人、放过自己。
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
P4 = os.path.join(HDIR, 'r55_paperwork4.py')
C4_AUTH = os.path.join(HDIR, 'r55_paperwork4.txt')        # 本批权威载体（它的"盘上现值"两格 = 本遍的改前原件）
C4_CRASH = os.path.join(HDIR, 'r55_paperwork3_10.txt')    # 崩溃那一遍的落地器载体 = 第 4 处现场的盘上原件
TS = '[0-9-]{10} [0-9:]{8}'
LED4 = '复跑｜R55 第四批'
FIXPFX = '> **【订正｜'
SEC_ANCHOR = '### 38.21'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_cands = ['r55_paperwork4_fix.txt'] + ['r55_paperwork4_fix_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def kinds(text):
    return len(re.findall(r'(?m)^\[错误类型\]', text))


def heads(text):
    return len(re.findall(r'(?m)^#{2,3} ', text))


def line_hits(text, anchor):
    return len([l for l in text.split('\r\n') if anchor in l])


def head_hits(text, anchor):
    return len([l for l in text.split('\r\n') if l.startswith(anchor)])


def blanks_above(text, idx):
    ls = text.split('\r\n')
    n, j = 0, idx - 1
    while j >= 0 and not ls[j].strip():
        n, j = n + 1, j - 1
    return n


def line_only(path, pat, why):
    hits = [l for l in rd(path).replace('\r\n', '\n').split('\n') if re.search(pat, l)]
    assert len(hits) == 1, 'ABORT: %s 里 %r 命中 %d 行（须恰好 1）⇒ %s' % (os.path.basename(path), pat, len(hits), why)
    return hits[0]


def sync_seal():
    acc = []
    for root, dirs, fs in os.walk(SYNC):
        dirs.sort()
        for f in sorted(fs):
            p = os.path.join(root, f)
            acc.append((os.path.relpath(p, SYNC).replace('\\', '/'), os.path.getsize(p)))
    return len(acc), sum(n for _, n in acc), hashlib.md5(repr(acc).encode('utf-8')).hexdigest()[:8]


# ---------- 现读两只文件 + 幂等判定（本批正文已落地，本遍只追加订正内容）----------
freq_old = rd(FREQ)
doc_old = rd(DOC)
for p, t in ((FREQ, freq_old), (DOC, doc_old)):
    b = open(p, 'rb').read()
    assert b.count(b'\r\n') == b.count(b'\n'), 'ABORT: %s 行尾混杂' % os.path.basename(p)
    assert t.endswith('\r\n'), 'ABORT: %s 末尾没有换行 ⇒ 追加会接在半截行之后' % os.path.basename(p)

_ls = freq_old.split('\r\n')
li = [i for i, l in enumerate(_ls) if LED4 in l]
assert len(li) == 1, 'ABORT: 本批台账锚在 FreqErr 命中 %d 行 ⇒ %s' % (len(li), li)
LED_LINE = _ls[li[0]]
_led_pos = li[0] + 1
_tail = [l for l in _ls[_led_pos:-1] if l.strip()]
CORR_EXIST = [l for l in _tail if l.startswith(FIXPFX)]
assert len(CORR_EXIST) <= 1, 'ABORT: 本批台账行之下已有 %d 只订正行 ⇒ 二次追加' % len(CORR_EXIST)
MODE = 'REWROTE_CARRIER_ONLY' if CORR_EXIST else 'FIX_NOW'
_seal_a = sync_seal()
_ports = ' '.join(sorted(str(p.device) for p in
                         __import__('serial.tools.list_ports', fromlist=['comports']).comports())) or '-'

# ---------- 见证：本遍的"改前四格"必须与本批权威载体在册的"盘上现值"两格逐字相等 ----------
assert 'MODE=REWROTE_CARRIER_ONLY' in line_only(C4_AUTH, r'^R55 第四批 paperwork 落地器', '本批权威载体首行')
_wf = line_only(C4_AUTH, r'^FREQ 追加之前反推 ', '本批权威载体的 FREQ 行')
_mf = re.search(r'盘上现值（含后续批次）([\d,]+) B / (\d+) 条 / (\d+) 行 / md5 ([0-9a-f]{8})', _wf)
assert _mf, 'ABORT: 本批载体 FREQ 行里没有"盘上现值（含后续批次）B/条/行/md5"那一格 ⇒ 本遍的改前四格没有原件'
_wd = line_only(C4_AUTH, r'^DOC ', '本批权威载体的 DOC 行')
_md = re.search(r'盘上现值（含后续小节）([\d,]+) B / (\d+) 行 / 标题 (\d+)', _wd)
assert _md, 'ABORT: 本批载体 DOC 行里没有"盘上现值（含后续小节）B/行/标题"那一格 ⇒ 同上'
wb_b, wb_k, wb_l, wb_m = _mf.groups()
wd_b, wd_l, wd_h = _md.groups()
# 「改前四格 vs 载体在册的盘上现值」那条互核放在订正文本取回之后（复跑支要先反推掉尾巴才能比）
# 崩溃那一遍在册的两格（第 4 处现场的盘上原件，也是订正器窗口口径的对照）
_ch = line_only(C4_CRASH, r'^R55 第三批 paperwork 落地器', '崩溃那一遍的载体首行')
assert 'MODE=REWROTE_CARRIER_ONLY' in _ch, 'ABORT: %s 首行不是 REWROTE ⇒ 它不是崩溃那一遍的原件' % os.path.basename(C4_CRASH)
CRASH_AT = re.search(r'本遍现跑于 (' + TS + ')', _ch).group(1)
_cf = line_only(C4_CRASH, r'^FREQ 追加之前', '崩溃那一遍的 FREQ 行')
_mc = re.search(r'（本批窗口末行 \d+） [\d,]+ B / (\d+) 条 / \d+ 行.*?盘上现值（含后续批次）[\d,]+ B / (\d+) 条', _cf)
assert _mc, 'ABORT: 崩溃那一遍的 FREQ 行不再合"（本批窗口…）B/条/行 … 盘上现值…B/条"句式 ⇒ 那句引用没有原件'
CRASH_WIN_K, CRASH_DISK_K = int(_mc.group(1)), int(_mc.group(2))
# ⑦ 格与① 格末尾那句的原文改由下面的 first_hit 统一现读（锚全部钉行首，避免本遍订正句自指）

# ---------- 订正文本：四段引语一律运行时现读，锚全部钉在**行首**（(40) 自指 + (63)~(65) 假引文两族）----------
_fr = freq_old.split('\r\n')
_lsdf = doc_old.split('\r\n')


def first_hit(ls, pat, why, tail=None):
    hits = [i for i, l in enumerate(ls) if re.match(pat, l)]
    assert len(hits) == 1, 'ABORT: 锚 %r 命中 %d 行（须 1）⇒ %s' % (pat, len(hits), why)
    line = ls[hits[0]]
    if tail is None:
        return line, hits[0] + 1
    m = re.search(tail, line)
    assert m, 'ABORT: 锚 %r 命中的那一行里取不到 %r ⇒ 引文算式要重推：%r' % (pat, tail, line[-40:])
    return m.group(1), hits[0] + 1


QUOTE1, QUOTE1_IDX = first_hit(_fr, r'^\> \*\*【[^】]*' + LED4, '本批台账行（要引"三处现场（…）"的那一行）',
                               r'(三处现场（[^）]*）)')
# 「三处」这个词在本批**窗口**（正文标题行 ~ 台账行，含两端）里出现几处，本遍就订正几处 —— 名单现读，不手数（(40)/(46) 族）
_H4 = [i for i, l in enumerate(_fr) if l.startswith('## 2026-09-24（R55 第四批')]
assert len(_H4) == 1, 'ABORT: 本批正文标题行命中 %d 处 ⇒ 窗口左界没有唯一原件' % len(_H4)
assert QUOTE1_IDX > _H4[0], 'ABORT: 台账行不在本批标题之下 ⇒ 窗口是倒的，右界不可信'
TRI = [(i + 1, _fr[i].count('三处')) for i in range(_H4[0], QUOTE1_IDX)
       if '三处' in _fr[i] and not _fr[i].startswith(FIXPFX)]
assert TRI, 'ABORT: 本批窗口（第 %d ~ %d 行）内一处"三处"都没命中 ⇒ 本遍的订正对象不存在' % (_H4[0] + 1, QUOTE1_IDX)
assert any(i == QUOTE1_IDX for i, _ in TRI), 'ABORT: 台账行那一处不在窗口名单里 ⇒ 两套名单不同源'
assert not [i for i in range(_H4[0], QUOTE1_IDX) if '四处' in _fr[i]], \
    'ABORT: 本批窗口里已经出现"四处" ⇒ 订正对象已被人改过，先查是谁改的'
QUOTE2, QUOTE2_IDX = first_hit(_fr, r'^\> 三处缺陷全部只在', '本批正文那句"三处缺陷…"（第二只逐字引文）')
QUOTE2 = QUOTE2[2:]
assert QUOTE2_IDX in [i for i, _ in TRI], 'ABORT: 逐字引文那一行不在窗口名单里 ⇒ 引文与计数不同源'
assert not [q for q in (QUOTE1, QUOTE2) if '「' in q or '」' in q], 'ABORT: 引文里本身带「」⇒ 与本轮的定界符相混，逐字引文读不出边界'
TRI_N = sum(n for _, n in TRI)
QUOTE_LINES = {QUOTE1_IDX, QUOTE2_IDX}
_rest = [(i, len(_fr[i - 1])) for i, _ in TRI if i not in QUOTE_LINES]
QUOTED_TXT = ('本批窗口（正文标题行第 %d 行 ~ 台账行第 %d 行，排除订正行前缀 ⇒ 本遍自己不进名单）内现读到 %d 处"三处"'
              '（%s，合计 %d 个词）；其中 %d 只逐字引在此处 = 台账行那句「%s」（第 %d 行）、正文那句「%s」（第 %d 行）'
              % (_H4[0] + 1, QUOTE1_IDX, len(TRI), '、'.join('第 %d 行' % i for i, _ in TRI), TRI_N,
                 len(TRI) - len(_rest), QUOTE1, QUOTE1_IDX, QUOTE2, QUOTE2_IDX))
if _rest:
    QUOTED_TXT += ('；其余 %d 只（%s）刻意不逐字引 ⇒ 未引的这几只整行现读都很长，截任何一截都会造出半句引文（(63)~(65) 假引文族），'
                   '本遍只按行号 + 现读整行字数登记'
                   % (len(_rest), '、'.join('第 %d 行 / 整行现读 %d 字' % (i, n) for i, n in _rest)))
else:
    QUOTED_TXT += '；窗口名单里的 %d 只全部已逐字引，无未引项' % len(TRI)
QUOTE3, QUOTE3_IDX = first_hit(_lsdf, r'^  它的 FREQ 行里写的是', '§38.21 ① 格末尾那句（排查记录）',
                               r'(两次崩溃.*证据；)')
QUOTE4, QUOTE4_IDX = first_hit(_lsdf, r'^  ⑦ 第 ①② 两次崩溃', '§38.21"本节没做"⑦ 那一行（排查记录）')
QUOTE4 = QUOTE4[2:]

# ---------- 复跑支先从盘上取回本遍将要"重写"的那两段订正正文，再由它反推改前串（两遍共用同一套构造）----------
if MODE == 'REWROTE_CARRIER_ONLY':
    CORR = CORR_EXIST[0]
    _lsd = doc_old.split('\r\n')
    _dc0 = [i for i, l in enumerate(_lsd) if l.startswith(FIXPFX) and '｜§38.21' in l]
    assert len(_dc0) == 1, 'ABORT: 盘上 §38.21 订正句的标题行有 %d 只（须 1）⇒ 二次追加或落点错位' % len(_dc0)
    DOC_CORR = [_lsd[_dc0[0]]]
    _j = _dc0[0] + 1
    while _j < len(_lsd) - 1 and _lsd[_j].startswith('> '):
        DOC_CORR.append(_lsd[_j])
        _j += 1
    assert blanks_above(doc_old, _dc0[0]) == 1, 'ABORT: 盘上 DOC 订正句上方空行数不是 1（(102) 族）'
    # 反推改前 = **按锚点切**，不是按"我的尾段在文件末尾"切（R56 第一批 18:09 一往这两只文件追加，
    # 旧写法 `freq_old.endswith(我的尾段)` 就永久 rc=1 —— 那是 §38.21 那一族的第 5 处现场：守卫写在"只有我"的世界里）。
    # 尾段之后的**后续批次**内容原样透传（POST_*），既不许被吞进反推，也不许被本遍重写。
    _lsf = freq_old.split('\r\n')
    _fc = [i for i, l in enumerate(_lsf) if l.startswith(FIXPFX) and '｜R55 第四批' in l]
    assert len(_fc) == 1, 'ABORT: 盘上 FreqErr 订正行的标题行有 %d 只（须 1）⇒ 二次追加或落点错位' % len(_fc)
    assert _lsf[_fc[0]] == CORR, 'ABORT: 盘上那只订正行与本遍从 `CORR_EXIST` 取回的不是同一只 ⇒ 锚点与正文不同源'
    assert blanks_above(freq_old, _fc[0]) == 1, 'ABORT: 盘上 FreqErr 订正行上方空行数不是 1（(102) 族）'
    freq_pre = '\r\n'.join(_lsf[:_fc[0] - 1]) + '\r\n'
    POST_F = '\r\n'.join(_lsf[_fc[0] + 1:])
    doc_pre = '\r\n'.join(_lsd[:_dc0[0] - 1]) + '\r\n'
    POST_D = '\r\n'.join(_lsd[_j:])
    _tf, _td = '\r\n' + CORR + '\r\n', '\r\n' + '\r\n'.join(DOC_CORR) + '\r\n'
else:
    freq_pre, doc_pre, CORR, DOC_CORR = freq_old, doc_old, None, None
    POST_F = POST_D = ''
    assert len(CORR_EXIST) == 0, 'ABORT: 写侧分支却已在册订正行 ⇒ MODE 判定与盘上态矛盾'

# ---------- 改前四格：取自反推串（写侧即盘上原样），并与本批权威载体在册的"盘上现值"逐字互核 ----------
b_bytes, b_kind, b_lines = len(freq_pre.encode('utf-8')), kinds(freq_pre), freq_pre.count('\r\n')
assert (money(b_bytes), str(b_kind), str(b_lines), hashlib.md5(freq_pre.encode('utf-8')).hexdigest()[:8]) == \
    (wb_b, wb_k, wb_l, wb_m), 'ABORT: 反推的改前四格与本批载体在册的"盘上现值"不等 ⇒ 中间别处动过：%s/%s/%s/%s vs %s/%s/%s/%s' % (
        money(b_bytes), b_kind, b_lines, hashlib.md5(freq_pre.encode('utf-8')).hexdigest()[:8], wb_b, wb_k, wb_l, wb_m)
d_bytes, d_lines, d_heads = len(doc_pre.encode('utf-8')), doc_pre.count('\r\n'), heads(doc_pre)
assert (money(d_bytes), str(d_lines), str(d_heads)) == (wd_b, wd_l, wd_h), \
    'ABORT: 反推的 DOC 改前三格与本批载体在册的"盘上现值"不等 ⇒ 两只文件不同源：%s/%s/%s vs %s/%s/%s' % (
        money(d_bytes), d_lines, d_heads, wd_b, wd_l, wd_h)

if MODE == 'FIX_NOW':
    CORR = (FIXPFX + NOW_AT + '｜R55 第四批**】 ' + QUOTED_TXT +
            ' —— 上述 %d 只本遍一律订正为**四处**（台账行原枚举 ①`AssertionError`、②`AttributeError`、③"两道闸按**整只文件**算"那只口径；'
            '本遍新增的第 4 处 = ③同一族在**第三批订正器**的另一道闸上真的红了 —— 它把在册的窗口条数与整只文件现值比 ⇒ rc=1 的 `AssertionError`）：'
            '本批 POSCTL 第二只'
            '（第三批的订正器 `hardware/r55_fix_paperwork3.py`）在本批落地那一遍当场 rc=1 —— 它把订正行在册的三把尺条数'
            '（它自己那一批的窗口 %d 条）与**整只文件**现值 %d 条比 ⇒ 第四批一落地这条比对必假红，'
            '是"整只文件口径"在第三批工具里的第 4 处、也是 ① 格"守卫只写在另一侧分支里"的又一处现场（那一支本批第一次真走到，'
            '一走到就红）。修法 = 那条比对改成按窗口取现值、错误消息同时点名盘上全量与窗口外条数；本遍已改，'
            '与落地器一起各复跑一遍都 rc=0（读数见本遍载体的 POSCTL 行）。那次崩溃**没有出错工具自己的载体**（它 ABORT 在写载体之前），'
            '但与 ①② 两次不同的是：它所在那**一遍**留下了落地器载体 `%s`（%s 写下），其上在册"本批窗口 %d 条 / 盘上现值 %d 条"两格'
            '正是那条假红比对的原始读数 ⇒ 第 4 处的证据等级 = 同遍载体在册读数，不是纯叙述。'
            '另记本遍工具自己的一只同族（**不进上面那"四处"**，它不在 ① 格枚举的现场集合里，是落地之前在临时目录的 dry 副本里发现的）：'
            '本遍最初写的复跑支判据是"订正行标题时刻不等于本遍 NOW_AT 才算复跑"，它把"上一遍与本遍落在同一秒"的合法复跑判成假红 —— '
            '同秒可达性实测 = dry 连跑三遍的相邻两遍只差 1 秒（17:47:53 / 17:47:54 / 17:47:54）；构造证明 = 在 dry 副本里把 NOW_AT 强制等于'
            '盘上标题时刻（17:47:53），旧式判据现算 False（当场红）、本遍最终判据（复跑支改与上一遍载体在册的"订正行标题时刻"逐字互核）同一遍 rc=0。'
            '本遍**只追加、不改写上面任何一行**，台账条数一律不变：'
            '改前 %d 条 / %d 行 → 终态 %d 条 / %d 行（+1 只空行 +1 只订正行）。'
            % (len(TRI), CRASH_WIN_K, CRASH_DISK_K, os.path.basename(C4_CRASH), CRASH_AT,
               CRASH_WIN_K, CRASH_DISK_K, b_kind, b_lines, b_kind, b_lines + 2))
    DOC_CORR = [
        '> **【订正｜@T@｜§38.21 ① 格末尾与"本节没做"⑦ 格】** ① 格末尾那句"@Q3@"（现读逐字自本文件第 @Q3I@ 行，'
        '去掉了行首的两格缩进）对它自己枚举的那两次崩溃仍然成立；本批 POSCTL 那一遍又崩了**第三次**（第三批订正器 rc=1：'
        '它的三把尺拿窗口 @WK@ 条与盘上全量 @DK@ 条比），所以本小节的"现场"总数应读作**四处** = 3 次崩溃 + 1 次"整只文件"口径'
        '（④ 那两道闸里落地器的那一道至今没红过，它靠本批前向对照才第一次真正执行）。该次崩溃没有出错工具自己的载体，'
        '但它所在那一遍留下了落地器载体 `@CB@`（@CAT@ 写下），在册"本批窗口 @WK@ 条 / 盘上现值 @DK@ 条"两格就是那条假红比对的原始读数。',
        '> "本节没做" ⑦ 那一行的原文（现读逐字自本文件第 @Q4I@ 行）：`@Q4@` ⇒ 它的适用范围限于它枚举的**那两**次崩溃，'
        '本遍不扩写它；第 3 次崩溃（POSCTL 那一遍）的证据等级按上一行所述 = 同遍载体在册读数。'
        '本遍另立前向对照 = 追加之后当场把 `hardware/r55_paperwork4.py` 再跑一遍：它那"台账行之后只许空行 / 订正行"那把尺'
        '第一次拿到非 0 输入 ⇒ 本遍不能只登记别人、放过自己（判据与读数见 `@CC@` 的 POSCTL 行）。',
        '> 本遍工具自己在落地之前也红过一只同族（**不进上面"四处"这个数**，它不在 ① 格枚举的现场集合里）：复跑支原判据写成"标题时刻不等于本遍 NOW_AT"，'
        '于是"上一遍与本遍落在同一秒"的合法复跑会被判成假红；构造对照 = 在临时目录的 dry 副本里把 NOW_AT 强制等于盘上标题时刻，'
        '旧式判据现算 False、改判后同一遍 rc=0，可达性由 dry 连跑三遍的实测节奏（相邻两遍差 1 秒）给出。',
    ]
    DOC_CORR = [l.replace('@T@', NOW_AT).replace('@Q3I@', str(QUOTE3_IDX)).replace('@Q4I@', str(QUOTE4_IDX))
                .replace('@Q3@', QUOTE3).replace('@Q4@', QUOTE4).replace('@WK@', str(CRASH_WIN_K))
                .replace('@DK@', str(CRASH_DISK_K)).replace('@CB@', os.path.basename(C4_CRASH))
                .replace('@CAT@', CRASH_AT).replace('@CC@', os.path.basename(CARRIER)) for l in DOC_CORR]
    assert '\\' not in CORR, 'ABORT: FreqErr 订正行模板里有反斜杠 ⇒ 正是 §38.18 那一族'
    assert not [l for l in DOC_CORR if '@' in l], 'ABORT: DOC 订正句里还有未回填的 @占位@ ⇒ 模板与替换表不同源'
else:
    # 复跑支：四段引语本遍又现读了一次，必须逐字仍在盘上那段订正正文的原位（引文若漂了，反推的那一段就不该再写）
    assert QUOTE1 in CORR and QUOTE2 in CORR, 'ABORT: 本遍现读的 FreqErr 两段引语与盘上订正行不再逐字相符 ⇒ 上面有人改过原文'
    assert QUOTE3 in DOC_CORR[0] and QUOTE4 in DOC_CORR[1], \
        'ABORT: 本遍现读的排查记录两段引语与盘上订正句不再逐字相符 ⇒ 上面有人改过原文'
assert LED4 not in CORR and '### 38.21' not in CORR, 'ABORT: 订正行里有台账锚或 §38.21 标题写法 ⇒ 尺子会自指（(40) 族）'
for _l in DOC_CORR:
    assert LED4 not in _l and '### 38.21' not in _l, 'ABORT: 订正句里有自指锚 ⇒ %r' % _l[:40]
TITLE_TS = re.match(r'^> \*\*【订正｜(' + TS + ')', CORR).group(1)
_PREV = [os.path.join(HDIR, c) for c in _cands if os.path.exists(os.path.join(HDIR, c))]
if MODE == 'FIX_NOW':
    assert TITLE_TS == NOW_AT, 'ABORT: 写侧订正行标题时刻不等于本遍 NOW_AT ⇒ 那一格是抄来的'
    MODECHK = '写侧：标题时刻 == 本遍 NOW_AT（构造即等，%s）' % NOW_AT
else:
    # 复跑支的标题时刻**不许**拿"不等于本遍 NOW_AT"来验：同一秒内复跑时两格本就相等，那样判会把合法复跑判成假红
    #   （(104) 那一族换了个藏身处：本遍第一次复跑踩到，判据改为与上一遍载体的在册值互核）
    assert _PREV, 'ABORT: 盘上已有本遍订正行，可载体池 %s 里一只在册载体都没有 ⇒ 订正行没有同遍原件，标题时刻无法取证，拒绝静默通过' % (
        os.path.basename(HDIR))
    _ph = line_only(_PREV[0], r'^R55 第四批 落地后自查订正遍', '上一遍载体的首行')
    _pt = re.search(r'订正行标题时刻 = (' + TS + ')', _ph)
    assert _pt, 'ABORT: 上一遍载体 %s 首行里没有"订正行标题时刻 ="那一格 ⇒ 原件读不出可比的量' % os.path.basename(_PREV[0])
    assert _pt.group(1) == TITLE_TS, 'ABORT: 盘上订正行标题时刻 %s 与上一遍载体在册值 %s 不等 ⇒ 有人改过那一行' % (
        TITLE_TS, _pt.group(1))
    MODECHK = '复跑支：标题时刻 %s == 上一遍载体 %s 在册值（本遍 NOW_AT=%s，与它等或不等都不进判据）' % (
        TITLE_TS, os.path.basename(_PREV[0]), NOW_AT)
RUN_AT = TITLE_TS

# ---------- 终态串（两把尺都在**本批窗口串**上数，(99)；后续批次的内容按 POST_* 原样透传，不进尺子）----------
freq_new = freq_pre + '\r\n' + CORR + '\r\n' + POST_F
doc_new = doc_pre + '\r\n' + '\r\n'.join(DOC_CORR) + '\r\n' + POST_D
FWIN = freq_pre + '\r\n' + CORR + '\r\n'
DWIN = doc_pre + '\r\n' + '\r\n'.join(DOC_CORR) + '\r\n'
assert (freq_new == freq_old and doc_new == doc_old) == (MODE == 'REWROTE_CARRIER_ONLY'), \
    'ABORT: 终态串与盘上态的"等 / 不等"和 MODE 不自洽 ⇒ 复跑支没还原出盘上那一段，或写侧已经在盘上'
assert freq_new.startswith(freq_pre) and doc_new.startswith(doc_pre), 'ABORT: 不再是纯追加'
assert freq_new.count(CORR) == 1 and all(doc_new.count(l) == 1 for l in DOC_CORR), 'ABORT: 订正文本在待写串里不止一处'
n_kind, n_lines = kinds(FWIN), FWIN.count('\r\n')
dn_lines, dn_heads = DWIN.count('\r\n'), heads(DWIN)
assert (n_kind, n_lines) == (b_kind, b_lines + 2), \
    'ABORT: 追加订正行之后 FreqErr 两把尺不是"条数不变 + 行数 +2"：%d/%d -> %d/%d' % (b_kind, b_lines, n_kind, n_lines)
assert dn_heads == d_heads and dn_lines == d_lines + len(DOC_CORR) + 1, \
    'ABORT: DOC 订正遍动了标题数或行数：标题 %d -> %d、行 %d -> %d（期望行 +%d = 订正句 %d 行 + 1 只空行）' % (
        d_heads, dn_heads, d_lines, dn_lines, len(DOC_CORR) + 1, len(DOC_CORR))
if MODE == 'FIX_NOW':
    open(FREQ, 'w', encoding='utf-8', newline='').write(freq_new)
    open(DOC, 'w', encoding='utf-8', newline='').write(doc_new)

# ---------- 独立回读（另一次调用，不复用上面那次的字符串）----------
freq_back, doc_back = rd(FREQ), rd(DOC)
assert freq_back == freq_new and doc_back == doc_new, 'ABORT: 独立回读与待写字节不逐字相同'
for p in (FREQ, DOC):
    bb = open(p, 'rb').read()
    assert bb.count(b'\r\n') == bb.count(b'\n'), 'ABORT: 回读显示 %s 行尾被写杂' % os.path.basename(p)
_ls2 = freq_back.split('\r\n')
_led2 = [i for i, l in enumerate(_ls2) if LED4 in l]
assert len(_led2) == 1, 'ABORT: 回读显示台账锚命中 %d 行 ⇒ 锚被抄进订正文本（(40) 族）' % len(_led2)
_led_after = [i for i, l in enumerate(_ls2) if l.startswith(FIXPFX) and '｜R55 第四批' in l]
assert len(_led_after) == 1, 'ABORT: 回读显示本批订正行 %d 只（须 1）' % len(_led_after)
assert _led_after[0] > _led2[0], 'ABORT: 订正行落在台账行之上 ⇒ 不是"台账行之下追加"这一族口径'
_ba = blanks_above(freq_back, _led_after[0])
assert _ba == 1, 'ABORT: 订正行上方空行数 = %d（须 1，(102) 族）' % _ba
# 回读的两把尺也绑在**本批窗口**上（到订正行为止），不是整只文件：R56 第一批之后盘上这一行下面还压着别的批次，
# 拿整只文件现值跟本批窗口终态比 = §38.21 那一族的又一处现场（守卫写在"只有我"的世界里）。
FWIN_BACK = '\r\n'.join(_ls2[:_led_after[0] + 1]) + '\r\n'
assert FWIN_BACK == FWIN, 'ABORT: 回读的窗口段与待写的窗口段不逐字相同 ⇒ 窗口右界取错'
assert kinds(FWIN_BACK) == n_kind and FWIN_BACK.count('\r\n') == n_lines, 'ABORT: 回读窗口两把尺与待写终态不等'
_ls2d = doc_back.split('\r\n')
_dc2 = [i for i, l in enumerate(_ls2d) if l.startswith(FIXPFX) and '｜§38.21' in l]
assert len(_dc2) == 1, 'ABORT: 回读显示 DOC 订正句标题行 %d 只（须 1）⇒ 二次追加或落点错位' % len(_dc2)
_dend = _dc2[0] + len(DOC_CORR) - 1
assert _ls2d[_dend] == DOC_CORR[-1], 'ABORT: 回读里订正句末行不在第 %d 行 ⇒ 段内有空行被吞或多出' % (_dend + 1)
DWIN_BACK = '\r\n'.join(_ls2d[:_dend + 1]) + '\r\n'
assert DWIN_BACK == DWIN, 'ABORT: 回读的 DOC 窗口段与待写窗口段不逐字相同 ⇒ 窗口右界取错'
assert heads(DWIN_BACK) == dn_heads == int(wd_h), \
    'ABORT: DOC 窗口标题数 %d 与本批载体在册的"盘上现值"标题数 %s 不等 ⇒ 订正遍凭空多/少了标题' % (dn_heads, wd_h)
# 整只文件现值单独记一笔（它含后续批次，必然比窗口大；不参与本批判据，只参与载体取证）
FULL_K, FULL_L = kinds(freq_back), freq_back.count('\r\n')
DFULL_L, DFULL_H = doc_back.count('\r\n'), heads(doc_back)
assert (FULL_K, FULL_L) >= (n_kind, n_lines) and (DFULL_L, DFULL_H) >= (dn_lines, dn_heads), \
    'ABORT: 整只文件现值比本批窗口还小 ⇒ 窗口右界算错'

# ---------- 前向对照：追加之后当场把本批落地器再跑一遍 ----------
_seal_b = sync_seal()
r = subprocess.run([sys.executable, P4], cwd=REPO, capture_output=True)
out = r.stdout.decode('utf-8', 'replace')
assert r.returncode == 0, 'ABORT: 前向对照 r55_paperwork4.py rc=%d ⇒ %s' % (
    r.returncode, (out + r.stderr.decode('utf-8', 'replace'))[-800:])
_nc = re.search(r'^CARRIER=hardware/(\S+)', out, re.M)
assert _nc, 'ABORT: 前向对照没打印 CARRIER 名 ⇒ 那一遍没写出载体，POSCTL 判据落空'
_np = os.path.join(HDIR, _nc.group(1))
_nhead = line_only(_np, r'^R55 第四批 paperwork 落地器', '前向对照新写那一只的首行')
assert 'MODE=REWROTE_CARRIER_ONLY' in _nhead, 'ABORT: 前向对照的新载体首行 MODE 不是 REWROTE ⇒ %r' % _nhead[:120]
_nl = line_only(_np, r'^LEDGER ', '前向对照新写那一只的 LEDGER 行')
_mfix = re.search(r'本批订正行现 (\d+) 只', _nl)
assert _mfix and int(_mfix.group(1)) == 1, \
    'ABORT: 前向对照在册的本批订正行数不是 1（读到 %s）⇒ "台账行之后只许订正行"那一支拿到的仍是 0 输入，本遍的前向对照落空' % (
        _mfix.group(1) if _mfix else 'None')
_seal_c = sync_seal()

lines = [
    'R55 第四批 落地后自查订正遍（FreqErr 台账行下补空行 + 订正行 / §38.21 下追加订正句），本遍现跑于 %s；订正行标题时刻 = %s；MODE=%s' % (
        NOW_AT, RUN_AT, MODE),
    '%s 追加之前%s %s B / %d 条 / %d 行 -> 本批窗口终态 %s B / %d 条 / %d 行 ; md5(改前串) %s -> 窗口终态 %s ; '
    '整只文件盘上现值（含后续批次，不参与本批判据）%s B / %d 条 / %d 行 ; 行尾=纯 CRLF ; '
    '本遍改前四格与 %s 在册的"盘上现值"格逐字互核 ; 订正行上方空行数 = %d ; 台账锚命中行数 = %d' % (
        'FREQ', '反推' if MODE == 'REWROTE_CARRIER_ONLY' else '现读',
        money(b_bytes), b_kind, b_lines, money(len(FWIN.encode('utf-8'))), n_kind, n_lines,
        hashlib.md5(freq_pre.encode('utf-8')).hexdigest()[:8],
        hashlib.md5(FWIN.encode('utf-8')).hexdigest()[:8],
        money(len(freq_back.encode('utf-8'))), FULL_K, FULL_L,
        os.path.basename(C4_AUTH), _ba, len(_led2)),
    'DOC %s B / %d 行 / 标题 %d -> 本批窗口终态 %s B / %d 行 / 标题 %d ; md5(改前串) %s -> 窗口终态 %s ; '
    '整只文件盘上现值（含后续小节，不参与本批判据）%s B / %d 行 / 标题 %d ; 订正句 %d 行（%s）; '
    '⑦ 格引文原件 = 本文件第 %d 行' % (
        money(d_bytes), d_lines, d_heads, money(len(DWIN.encode('utf-8'))), dn_lines, dn_heads,
        hashlib.md5(doc_pre.encode('utf-8')).hexdigest()[:8],
        hashlib.md5(DWIN.encode('utf-8')).hexdigest()[:8],
        money(len(doc_back.encode('utf-8'))), DFULL_L, DFULL_H, len(DOC_CORR),
        '复跑支：从盘上取回并逐字回验' if MODE == 'REWROTE_CARRIER_ONLY' else '写侧：本遍现造，写盘后独立回读逐字',
        QUOTE4_IDX),
    'LEDGER 本批台账行 1-based 位置 = %d（改前后不变）; 订正行 1-based 位置 = %d ; 台账行与订正行之间只隔 1 只空行' % (
        _led2[0] + 1, _led_after[0] + 1),
    'MODECHK %s' % MODECHK,
    'SEAL 末版封界（ht305_sync/ 名字数 / 字节数 / 聚合 md5）：写盘前 %s ; 写盘后 %s ; 前向对照复跑后 %s ⇒ 三遍逐字相等，本遍零写入归档目录' % (
        _seal_a, _seal_b, _seal_c),
    'POSCTL 前向对照 = 本遍追加之后当场复跑 `hardware/r55_paperwork4.py`（本批落地器）：rc=0 新载体=%s，'
    '它那把"台账行之后只许空行 / 订正行"的尺在本遍之前拿到的输入恒为 0 只，本遍第一次给它非 0 ⇒ 判据 = 新载体 LEDGER 行在册"本批订正行现 1 只"'
    '（现读=%s 只）且首行 MODE=REWROTE_CARRIER_ONLY' % (os.path.basename(_np), _mfix.group(1)),
    'WITNESS 本遍改前四格原件 = %s 的 FREQ / DOC "盘上现值"两格 ; 第 3 次崩溃所在那一遍的落地器载体 = %s（%s，本批窗口 %d 条 / 盘上现值 %d 条）; '
    '四段引语全部运行时现读且锚钉行首：FreqErr.md 第 %d 行"三处现场（…）"、FreqErr.md 第 %d 行"三处缺陷…"、%s 第 %d 行"两次崩溃…证据；"、'
    '%s 第 %d 行"⑦ …"' % (
        os.path.basename(C4_AUTH), os.path.basename(C4_CRASH), CRASH_AT, CRASH_WIN_K, CRASH_DISK_K,
        QUOTE1_IDX, QUOTE2_IDX, os.path.basename(DOC), QUOTE3_IDX, os.path.basename(DOC), QUOTE4_IDX),
    'TRI 本批"三处"名单现读（窗口 = 正文标题行第 %d 行 ~ 台账行第 %d 行，排除订正行前缀 ⇒ 本遍订正行不进名单）：%s，合计 %d 个词 ⇒ 本遍订正 %d 处；'
    '逐字引文 %d 只（第 %d / %d 行），未逐字引 %d 只（%s）' % (
        _H4[0] + 1, QUOTE1_IDX, '、'.join('第 %d 行(%d)' % (i, n) for i, n in TRI), TRI_N, len(TRI),
        len(TRI) - len(_rest), QUOTE1_IDX, QUOTE2_IDX, len(_rest),
        '、'.join('第 %d 行 / 整行现读 %d 字' % (i, n) for i, n in _rest) or '无'),
    'FIELD rev-list=%d porcelain=%d ports=%s COM14=%s ; docs 停在第九遍 39 只 @2026-09-24 13:33:42 ; backups 停在第九次 @2026-09-24 13:43:38' % (
        int(subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                           capture_output=True).stdout or b'0'),
        len([x for x in subprocess.run(['git', 'status', '--porcelain'], cwd=REPO, capture_output=True)
             .stdout.decode('utf-8', 'replace').splitlines() if x.strip()]),
        _ports, 'PRESENT' if 'COM14' in _ports else 'ABSENT'),
    'GUARD 只追加不改写 / 独立回读逐字 / 两把尺在最终串上数 / 改前四格与本批载体"盘上现值"逐字互核 / 订正行上方恰好 1 只空行 / '
    '引语运行时现读 + 锚钉行首（四段：FreqErr 台账行的"三处现场（…）"、FreqErr 正文的"三处缺陷…"那句、§38.21 ① 格末尾"两次崩溃…证据；"、"本节没做"⑦ 那一行；另加崩溃那一遍载体在册两格）/ '
    '"三处"名单按窗口现读（正文标题行 ~ 台账行，排除订正行前缀 ⇒ 本遍自己不进名单），逐字引文与窗口名单同源断言 + 窗口内不许预存"四处" / 自指锚断言（订正文本里不许出现台账锚与 §38.21 标题写法）/ '
    'MODE 与订正行标题时刻互证（写侧 = 本遍 NOW_AT；复跑支 = 上一遍载体在册的"订正行标题时刻"逐字相等，且明文禁止拿"不等于 NOW_AT"当判据 ⇒ 同秒复跑不得被假红）/ 前向对照有执行者（rc + 新载体 + 订正行数非 0）/ 封界有执行者（三遍）',
    'VERDICT=' + {'FIX_NOW': 'PAPERWORK4_FIX_LANDED', 'REWROTE_CARRIER_ONLY': 'PAPERWORK4_FIX_CARRIER_ONLY'}[MODE],
]
assert _seal_a == _seal_b == _seal_c, 'ABORT: 归档目录 Seal 三遍不相等 ⇒ 本遍动过 ht305_sync/'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
for _l in lines:
    print(_l)
print('CARRIER=hardware/' + os.path.basename(CARRIER))
