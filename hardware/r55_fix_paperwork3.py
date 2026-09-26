# R55 第三批 的**落地后自查订正器**（只动 FreqErr.md 一只，一次写盘）：
#   ① 本批台账行上方补那只缺的空行 —— 由 `r55_paperwork3.py` 落盘后的独立回读抓到，正是 (102) 那一族；
#   ② 文件末尾**纯追加**一行订正，同时登记第二处、性质更重的缺陷：幂等闸的**读侧解析式在落地那一遍从未被执行**。
# 本遍不动排查记录、不动四只记忆文件（两只 CRLF 文档各自的 stat 改前 == 改后或仅 FreqErr 变，由末尾断言兑现）。
# 归档封界：本脚本与其载体一律落 `hardware/` 根，`hardware/ht305_sync/` 一只不落（gen 24 是末版）。
import hashlib
import os
import re
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
FREQ = os.path.join(REPO, 'FreqErr.md')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
C_LAND = os.path.join(HDIR, 'r55_paperwork3.txt')
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   # 本遍现跑的唯一时刻，(104) 的落点
TS = '[0-9-]{10} [0-9:]{8}'
LED = '复跑｜R55 第三批'
FIXPFX = '> **【订正｜'
FIXNUM = re.compile(r'条数 = \*\*(\d+)\*\*、行数 = \*\*(\d+)\*\*')
PAT_LAND = re.compile(r'FREQ 追加之前(?:现读|反推) [\d,]+ B / (\d+) 条 / (\d+) 行 -> 之后 [\d,]+ B / (\d+) 条 / (\d+) 行 ; md5 \w{8} -> (\w{8})')
PAT_SELF = re.compile(r'FREQ 三级两把尺：改前 (\d+) 条 / (\d+) 行 -> 补空行后 \d+ 条 / \d+ 行 -> 终态 (\d+) 条 / (\d+) 行 ; .+?md5 (\w{8}) -> (\w{8})')

_cands = ['r55_fix_paperwork3.txt'] + ['r55_fix_paperwork3_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)
# 权威前序载体 = 已存在的最后一只（复跑补写的 _2 起就盖过首载体，首载体只作历史保留）
_prior = [c for c in _cands if os.path.exists(os.path.join(HDIR, c))]
C_PRIOR = os.path.join(HDIR, _prior[-1]) if _prior else None


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def stat(p):
    b = open(p, 'rb').read()
    return len(b), b.count(b'\n'), b.count(b'\r'), hashlib.md5(b).hexdigest()[:8]


def kinds(text):
    return len(re.findall(r'(?m)^\[错误类型\]', text))


def both(text):
    return kinds(text), text.count('\r\n')


P_LED = lambda l: LED in l and not l.startswith(FIXPFX)     # 台账行锚：订正行哪怕把锚抄进标题也不许命中
P_FIX = lambda l: l.startswith(FIXPFX) and 'R55 第三批' in l   # 本批订正行：只认批次名，不认台账锚


def rows(text, pred):
    ls = text.split('\r\n')
    return [i for i, l in enumerate(ls) if pred(l)]


def blanks_above(text, i):
    ls = text.split('\r\n')
    n, j = 0, i - 1
    while j >= 0 and not ls[j].strip():
        n, j = n + 1, j - 1
    return n


def line_only(path, pat, why):
    hits = [l for l in rd(path).replace('\r\n', '\n').split('\n') if re.search(pat, l)]
    assert len(hits) == 1, 'ABORT: %s 里 %r 命中 %d 行（须恰好 1）⇒ %s' % (os.path.basename(path), pat, len(hits), why)
    return hits[0]


def win_end(ls, last_i):
    """本批窗口末行的 1-based 行数：从"本批写的最后一行"往后找到下一只批次标题（`## `），
    标题前那只空行归下一批。不划这个界，后续批次一追加就把本批所有断言染成假红。"""
    nxt = [i for i in range(last_i + 1, len(ls)) if ls[i].startswith('## ')]
    if not nxt:
        return len(ls) - 1, 0, ls[last_i + 1:-1]
    assert ls[nxt[0] - 1].strip() == '', \
        'ABORT: 窗口右界没落在批次边界上（前一行 %r）⇒ 是在半截内容里切的' % ls[nxt[0] - 1][:20]
    return nxt[0] - 1, len(nxt), ls[last_i + 1:nxt[0] - 1]


# ---------- 前置事实：盘上现状 + 落地批载体在册的 AFTER ----------
raw0 = open(FREQ, 'rb').read()
txt0 = rd(FREQ)
md5_0 = hashlib.md5(raw0).hexdigest()[:8]
assert txt0.endswith('\r\n'), 'ABORT: FreqErr 不以 CRLF 结尾 ⇒ 追加会造出半行'
assert raw0.count(b'\r\n') == raw0.count(b'\n'), 'ABORT: FreqErr 行尾本来就混杂'
k0, l0 = both(txt0)
led_i = rows(txt0, P_LED)
assert len(led_i) == 1, 'ABORT: 本批台账行在盘上有 %d 处 ⇒ 不是"落地一次"的状态' % len(led_i)
led_line = txt0.split('\r\n')[led_i[0]]
fix_i = rows(txt0, P_FIX)
n_blank = blanks_above(txt0, led_i[0])
_ls0 = txt0.split('\r\n')
if fix_i:
    WIN_END, LATER_N, WIN_TAIL = win_end(_ls0, fix_i[0])          # 订正行是本批写的最后一行 ⇒ 窗口到它为止
    assert not WIN_TAIL, 'ABORT: 订正行之后、下一批标题之前还有 %d 行不属于本批 ⇒ %r' % (len(WIN_TAIL), WIN_TAIL[0][:30])
    WIN_KIND = sum(1 for l in _ls0[:WIN_END] if l.startswith('[错误类型]'))
else:
    WIN_END, LATER_N, WIN_KIND = l0, 0, k0                        # PRE 态：本批刚落地完，窗口 == 文件
LATER_LINES = l0 - WIN_END
d0 = stat(DOC)
_doc0 = rd(DOC)
# 节号只做"前后相等"的对照，不做"下一节不许存在"的禁令 —— 后者是前向假红：第四批一落 §38.21 本闸必红
S20_0, S21_0 = _doc0.count('### 38.20'), _doc0.count('### 38.21')

m_land = PAT_LAND.search(line_only(C_LAND, r'^FREQ 追加之前现读 ', '落地批载体的 FREQ 读数行'))
assert m_land, 'ABORT: 落地批载体第 2 行不合 FREQ 读数式 ⇒ 无法与盘上互核'
c_bk, c_bl, c_ak, c_al, c_md5 = m_land.groups()
LAND_T = re.search(r'本遍现跑于 (' + TS + ')', line_only(C_LAND, r'^R55 第三批 paperwork 落地器', '落地批载体首行')).group(1)

# ---------- 幂等闸：三种盘上态唯一区分（改前 = 台账 AFTER ; 改后 = 空行 + 订正行都在册）----------
PRE = (int(c_ak), int(c_al)) == (k0, l0) and md5_0 == c_md5 and n_blank == 0 and not fix_i
POST = n_blank == 1 and len(fix_i) == 1
assert PRE != POST, 'ABORT: 盘上既不是"落地刚落完"也不是"订正批已改完"（空行 %d 只 / 订正行 %d 处 / k0,l0=%d,%d / 台账 AFTER=%s,%s / md5 %s vs 载体 %s）' % (
    n_blank, len(fix_i), k0, l0, c_ak, c_al, md5_0, c_md5)
if PRE:
    assert led_i[0] + 1 == int(c_al), \
        'ABORT: 台账行现居第 %d 行，落地批在册 AFTER 行数却是 %s ⇒ 中间别处动过行' % (led_i[0] + 1, c_al)
    MODE = 'FIX_NOW'
else:
    fl0 = txt0.split('\r\n')[fix_i[0]]
    MODE = 'ANCHOR_REWRITE' if LED in fl0 else 'REWROTE_CARRIER_ONLY'
    if C_PRIOR:
        m_self = PAT_SELF.search(line_only(C_PRIOR, r'^FREQ 三级两把尺', '本订正批载体的三级读数行'))
        assert m_self, 'ABORT: 本订正批载体在册的三级读数行不合格式 ⇒ 改后态无从核对'
        assert (int(m_self.group(3)), int(m_self.group(4))) == (WIN_KIND, WIN_END), \
            'ABORT: 载体在册终态(%s,%s) 与本批窗口现值(%d 条 / 末行 %d) 不符 ⇒ 载体之后又有人在本批窗口内改盘' % (
                m_self.group(3), m_self.group(4), WIN_KIND, WIN_END)
print('MODE=%s' % MODE)

# ---------- 订正行：FIX_NOW 现造；改后态则从盘上取回那一句、走同一套闸 ----------
if MODE == 'FIX_NOW':
    RUN_AT = NOW_AT   # 订正行头那一刻 == 本遍现跑那一刻，载体 TSX 行两格互证
    CORR = (FIXPFX + RUN_AT + '｜R55 第三批**】 本批台账行（落地时它是文件最后一行）上方原缺一只空行：'
            '它的前一行是本批第 4 条末尾那句"同族"，两行直接相接 ⇒ 正是本批第 2 条所立的 (102) 那一族在我自己的落地器上复现；'
            '本遍就地补上那只空行，台账行自身的字节、以及它之上除这只空行以外的一切逐字不动（前缀等式 + 写盘后独立回读由本脚本兑现）。'
            '同一遍自查另抓到第二处、性质更重的一处：**幂等闸从台账行反推读数的两条解析式，在 ' + LAND_T + ' 落地那一遍从未被执行**'
            '（那一遍走的是写侧分支），今天第一次真正走到就因 AFTER 段少写了两字而抛 AttributeError ⇒ 工具已改三处：'
            '解析式与写侧同源、写侧产出台账行的那一遍就用读侧那套式子回解一次（阳性对照）、不命中一律 ABORT 并点名段落，'
            '不再让 traceback 当报错。**三把尺现跑**：改之前条数 = **' + str(k0) + '**、行数 = **' + str(l0) + '** ; '
            '补空行之后条数 = **' + str(k0) + '**、行数 = **' + str(l0 + 1) + '** ; '
            '终态（追加本订正行连同其上方那只空行）条数 = **' + str(k0) + '**、行数 = **' + str(l0 + 3) + '**。'
            '⇒ 条数三遍不变（只加行、不加条目），行数三级差 +1、再 +2（合计 +3）与"补 1 只空行""追加空行 + 订正行"逐字对应。'
            '第 5 条错误类型（**从未被执行的那一侧分支，它的守卫不算已验证**）留待下一批补登并落 §38.21，本遍不动台账条数。')
    EXP = [(k0, l0), (k0, l0 + 1), (k0, l0 + 3)]
else:
    fl0 = txt0.split('\r\n')[fix_i[0]]
    RUN_AT = re.search(r'订正｜(' + TS + ')', fl0).group(1)
    if C_PRIOR:
        m_tsx = re.search(r'corr_head=(' + TS + ') written_at=(' + TS + ')',
                          line_only(C_PRIOR, r'^TSX corr_head=', '本订正批载体的 TSX 行'))
        SELF_W = re.search(r'本遍现跑于 (' + TS + ')',
                           line_only(C_PRIOR, r'^R55 第三批 落地后自查订正器', '本订正批载体首行')).group(1)
        assert m_tsx.group(2) == SELF_W, \
            'ABORT: 载体首行的"本遍现跑于"(%s) 与它自己 TSX 行的 written_at(%s) 不等 ⇒ 同一只载体内部两格有一格是抄来的' % (
                SELF_W, m_tsx.group(2))
        assert RUN_AT == m_tsx.group(1), \
            'ABORT: 盘上订正行头时刻(%s) 与载体 TSX 在册的 corr_head(%s) 不符 ⇒ 两处有一处是猜的' % (
                RUN_AT, m_tsx.group(1))
    if MODE == 'ANCHOR_REWRITE':
        assert fl0.count('｜' + LED) == 1, 'ABORT: 订正行标题里的台账锚不是恰好一处 ⇒ 换字无从下手'
        CORR = (fl0.replace('｜' + LED, '｜R55 第三批', 1) +
                '（' + NOW_AT + ' 这一遍换字时又抓到本句自身的一处：它的标题原本把台账锚整串抄了进来 ⇒ '
                '"数本批台账行"的那把尺在同一只文件里命中两处，正是项目记忆 (40)「命令文本含被搜串 ⇒ 计数自指」那一族；'
                '本遍去掉那三个字符并补上这句说明，行数与条数一律不变。）')
        assert LED not in CORR, 'ABORT: 换字之后订正行里仍有台账锚 ⇒ 自指没去掉'
    else:
        CORR = fl0
    EXP = None

# ---------- 零容忍闸（对将被写出的那一句，而不是对中间串）----------
assert '\\' not in CORR, 'ABORT: 订正行里有反斜杠 ⇒ 正是 §38.18 那一族'
assert not re.search(r'\{[A-Za-z_][A-Za-z0-9_]*\}|@[A-Z]+@', CORR), 'ABORT: 订正行里有未回填占位'
assert '\r' not in CORR and '\n' not in CORR and CORR.count(FIXPFX) == 1, 'ABORT: 订正行不是恰好一行'
assert 'VERDICT=SCP_FAILED' not in CORR, 'ABORT: 订正行里出现了没被点名的失败裁决'
pairs = [(int(a), int(b)) for a, b in FIXNUM.findall(CORR)]
assert len(pairs) == 3, 'ABORT: 订正行应当并列三把尺，实际 %d 把 ⇒ 措辞与 FIXNUM 不同形' % len(pairs)
assert EXP is None or pairs == EXP, 'ABORT: 订正行里的三把尺与本次将要产生的状态不符：%s vs %s' % (pairs, EXP)
assert all(k == WIN_KIND for k, _ in pairs), \
    'ABORT: 三把尺里有哪一把的条数与本批**窗口**现值不等：%s vs %d（盘上全量 %d 条，其中窗口外 %d 条属于后续批次，不参与本闸）' % (
        pairs, WIN_KIND, k0, k0 - WIN_KIND)

# ---------- 写盘（只写 FreqErr 一只）----------
if MODE == 'FIX_NOW':
    cut = txt0.index(led_line)
    head, tail = txt0[:cut], txt0[cut:]
    assert tail.startswith(led_line) and tail.endswith('\r\n'), 'ABORT: 从台账行切出来的尾巴不合预期结构'
    txt_mid = head + '\r\n' + tail
    txt_new = txt_mid + '\r\n' + CORR + '\r\n'
    assert txt_mid.startswith(head) and txt_new.startswith(txt_mid), 'ABORT: 不再是纯插入 / 纯追加'
    assert both(txt_mid) == (k0, l0 + 1) and both(txt_new) == (k0, l0 + 3), 'ABORT: 中间态或终态两把尺不等'
    assert txt_new.count(led_line) == 1, 'ABORT: 台账行在待写串里不止一处'
    assert txt_new.count(LED) == 1, 'ABORT: 待写串里台账锚出现 %d 次 ⇒ 有别处把它抄了进去' % txt_new.count(LED)
    open(FREQ, 'w', encoding='utf-8', newline='').write(txt_new)
elif MODE == 'ANCHOR_REWRITE':
    ls0 = txt0.split('\r\n')
    txt_new = '\r\n'.join(ls0[:fix_i[0]] + [CORR] + ls0[fix_i[0] + 1:])
    assert txt_new.count(CORR) == 1 and CORR not in txt0, 'ABORT: 待写订正行要么已在盘上、要么落不进那一行'
    assert (kinds(txt_new), txt_new.count('\r\n')) == (k0, l0), 'ABORT: 换字动了条数或行数（本遍口径：只换那一句）'
    assert len(ls0) == len(txt_new.split('\r\n')) and \
        sum(1 for a, b in zip(ls0, txt_new.split('\r\n')) if a != b) == 1, 'ABORT: 不止一行被改动'
    assert txt_new.count(LED) == 1, 'ABORT: 换字之后台账锚仍在盘上命中 %d 处 ⇒ 自指没去掉' % txt_new.count(LED)
    open(FREQ, 'w', encoding='utf-8', newline='').write(txt_new)
else:
    txt_new = txt0

# ---------- 写盘后独立回读（另一次调用，不复用上面那次的字符串）----------
txt_back = rd(FREQ)
raw_back = open(FREQ, 'rb').read()
assert raw_back.count(b'\r\n') == raw_back.count(b'\n'), 'ABORT: 回读显示行尾被写杂'
assert txt_back == txt_new, 'ABORT: 独立回读与待写字节不逐字相同'
kb, lb = both(txt_back)
led_b = rows(txt_back, P_LED)
fix_b = rows(txt_back, P_FIX)
assert (len(led_b), len(fix_b)) == (1, 1), 'ABORT: 回读显示台账行 %d 处 / 订正行 %d 处 ⇒ 二次追加' % (len(led_b), len(fix_b))
assert txt_back.count(LED) == 1, \
    'ABORT: 回读显示台账锚"复跑｜R55 第三批"在盘上命中 %d 处 ⇒ 有一处是抄来的锚（(40) 那一族）' % txt_back.count(LED)
assert txt_back.count(LED) >= 1, 'ABORT: 回读显示台账锚"复跑｜R55 第三批"在盘上一处都没有'
# —— 回读侧独立划一次窗口界（不复用进入时那次的算式），两界只许差在本批那 0 / 3 行上 ——
_lsb = txt_back.split('\r\n')
WEND_B, LATER_B, WTAIL_B = win_end(_lsb, fix_b[0])
WKIND_B = sum(1 for l in _lsb[:WEND_B] if l.startswith('[错误类型]'))
LINES_B = lb - WEND_B                      # 本批窗口之外（后续批次）的行数
KINDS_B = kb - WKIND_B                     # 本批窗口之外的错误类型条数
assert not WTAIL_B, 'ABORT: 回读显示订正行与下一批标题之间还有 %d 行 ⇒ %r' % (len(WTAIL_B), WTAIL_B[0][:30])
assert (WEND_B, WKIND_B) == (WIN_END + (3 if MODE == 'FIX_NOW' else 0), WIN_KIND), \
    'ABORT: 回读窗口 (%d 行 / %d 条) 与进入时窗口 (%d 行 / %d 条) 之差不是本批的 +%d 行 0 条 ⇒ 本批窗口内被人动过' % (
        WEND_B, WKIND_B, WIN_END, WIN_KIND, 3 if MODE == 'FIX_NOW' else 0)
assert (LINES_B, KINDS_B) == (LATER_LINES, k0 - WIN_KIND), \
    'ABORT: 窗口外（后续批次）的量从进入时 %d 行 / %d 条 变成回读 %d 行 / %d 条 ⇒ 本遍越界改了不属于本批的内容' % (
        LATER_LINES, k0 - WIN_KIND, LINES_B, KINDS_B)
assert '\r\n'.join(_lsb[:WEND_B]).count(LED) == 1, \
    'ABORT: 台账锚在本批窗口内命中 %d 处 ⇒ 有一处是抄来的锚（(40) 那一族）' % (
        '\r\n'.join(_lsb[:WEND_B]).count(LED))
assert blanks_above(txt_back, led_b[0]) == 1 and blanks_above(txt_back, fix_b[0]) == 1, \
    'ABORT: 回读显示两行上方不是各恰好一只空行（台账 %d / 订正 %d）' % (
        blanks_above(txt_back, led_b[0]), blanks_above(txt_back, fix_b[0]))
assert txt_back.split('\r\n')[led_b[0]] == led_line, 'ABORT: 台账行自身被改动'
assert txt_back[:txt_back.index(led_line)].endswith('\r\n\r\n'), 'ABORT: 台账行上方那只空行没落对位置'
pb = [(int(a), int(b)) for a, b in FIXNUM.findall(txt_back.split('\r\n')[fix_b[0]])]
assert pb[0] == (int(c_ak), int(c_al)) and pb[-1] == (WKIND_B, WEND_B), \
    'ABORT: 盘上那句订正行的三把尺与两份载体对不上：%s vs 落地批 %s/%s、回读窗口 %d/%d' % (
        pb, c_ak, c_al, WKIND_B, WEND_B)
assert all(k == WKIND_B for k, _ in pb), 'ABORT: 盘上订正行的三把尺有条数与回读窗口条数不等的一组：%s vs %d' % (pb, WKIND_B)
if EXP is not None:
    assert pb == EXP, 'ABORT: 写盘那三把尺与回读结果不等：%s vs %s' % (pb, EXP)
    assert re.search(r'订正｜(' + TS + ')', txt_back.split('\r\n')[fix_b[0]]).group(1) == RUN_AT, \
        'ABORT: 回读到的订正行时刻不是本遍现跑那一刻'
d1 = stat(DOC)
assert d1 == d0, 'ABORT: 本遍动了排查记录：改前 %s B/md5 %s -> 改后 %s B/md5 %s' % (d0[0], d0[3], d1[0], d1[3])
_doc_back = rd(DOC)
assert _doc_back.count('\r\n') == _doc_back.count('\n'), 'ABORT: 排查记录行尾混杂'
S20_B, S21_B = _doc_back.count('### 38.20'), _doc_back.count('### 38.21')
assert (S20_B, S21_B) == (S20_0, S21_0), \
    'ABORT: 本遍动了排查记录的节（§38.20 %d→%d、§38.21 %d→%d）' % (S20_0, S20_B, S21_0, S21_B)

md5_b = hashlib.md5(raw_back).hexdigest()[:8]
assert led_b[0] + 1 == int(c_al) + 1, \
    'ABORT: 回读台账行 1-based 位置 %d != 落地批在册 AFTER 行数 %s + 1（本批在它上方补的那只空行） ⇒ 中间别处动过行' % (
        led_b[0] + 1, c_al)
lines = [
    'R55 第三批 落地后自查订正器（FreqErr 台账行上方补空行 + 追加订正行 / 换字去掉抄进去的台账锚），本遍现跑于 %s；MODE=%s' % (NOW_AT, MODE),
    'FREQ 三级两把尺：改前 %d 条 / %d 行 -> 补空行后 %d 条 / %d 行 -> 终态 %d 条 / %d 行 ; 行数三级差 = +1 / +2，合计 +3 ; md5 %s -> %s ; 本遍是否加行 = %s' % (
        pb[0][0], pb[0][1], pb[1][0], pb[1][1], pb[2][0], pb[2][1], md5_0, md5_b,
        '是（+3）' if MODE == 'FIX_NOW' else '否（订正行在册三把尺 == 本次回读窗口 %d 条 / 末行 %d）' % (WKIND_B, WEND_B)),
    'TSX corr_head=%s written_at=%s mode=%s carrier=%s' % (RUN_AT, NOW_AT, MODE, os.path.basename(CARRIER)),
    'XCHECK 落地批载体首行现跑于 %s，其 FREQ 行在册 AFTER = %s 条 / %s 行、md5 %s…；本批订正行自述三把尺 = %s，'
    '第一把 == 落地批在册、末一把 == 回读**窗口**现值（%d 条 / 末行 %d）' % (LAND_T, c_ak, c_al, c_md5, pb, WKIND_B, WEND_B),
    'WINDOW 本批断言范围：进入时末行 %d / %d 条 -> 回读末行 %d / %d 条（差 +%d 行 0 条，正是本批 +1 空行 +1 空行+1 订正行 或 0）；'
    '回读时窗口外（后续批次）尚有 %d 行 / %d 条，与进入时 %d 行 / %d 条 逐字相等 ⇒ 本遍没越界；盘上全量 %d 条 / %d 行' % (
        WIN_END, WIN_KIND, WEND_B, WKIND_B, WEND_B - WIN_END, LINES_B, KINDS_B, LATER_LINES, k0 - WIN_KIND, kb, lb),
    'LEDGER 台账行 0-based 下标：本遍进入时 %d → 回读时 %d（1-based = %d = 落地批在册 AFTER 行数 %s + 本批补的那只空行；'
    '落地那一遍它正是文件最后一行）; 其上方空行数 %d → %d ; 台账锚全文命中数 %d → %d' % (
        led_i[0], led_b[0], led_b[0] + 1, c_al, n_blank, blanks_above(txt_back, led_b[0]), txt0.count(LED), txt_back.count(LED)),
    'DOC 本遍未动：%s B / %d 行 / md5 %s ; 节号 §38.20 = %d 处、§38.21 = %d 处（进入与回读两侧逐字相等，本闸只核相等、不禁止后续节存在）' % (
        money(d1[0]), d1[1], d1[3], S20_B, S21_B),
    'GUARD 反斜杠=0 / 未回填占位=0 / 纯插入 + 纯追加（或只换那一句）+ 独立回读逐字 / 台账行与订正行上方各恰好一只空行 / '
    '条数三遍不变 / 台账锚在本批窗口内命中数=1 / 台账行 1-based 位置 == 落地批 AFTER + 1（现算断言）/ '
    '载体 corr_head 与 written_at 分格互证（订正行头 == corr_head，绝不拿它比 written_at，(104) 族）/ '
    '前序权威载体 = 已存在的最后一只 / '
    '断言范围按批次窗口右界切：本批只认"订正行 ~ 下一只 `## ` 标题之前"，窗口外的行 %d 只（后续批次 %d 只标题）'
    '逐字不参与本批两把尺比对，只要求进入/回读两侧相等 ⇒ 第四批落地不会把本批闸染成假红' % (LINES_B, LATER_N),
    'VERDICT=' + {'FIX_NOW': 'PAPERWORK3_FIX_LANDED', 'ANCHOR_REWRITE': 'PAPERWORK3_FIX_ANCHOR_REWRITTEN',
                  'REWROTE_CARRIER_ONLY': 'PAPERWORK3_FIX_CARRIER_ONLY'}[MODE],
]
open(CARRIER, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('CARRIER=hardware/' + os.path.basename(CARRIER))
