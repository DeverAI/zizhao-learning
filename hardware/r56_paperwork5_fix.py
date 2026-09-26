# R56 第五批**订正遍**：给 §38.26 补一条订正句 —— 那一节里"新增写盘后反查"记的是崩溃那一刻之前的形状
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 只在 §38.26 末尾**追加一行**，正文一字不改
#   ② FreqErr.md 一字不动（本遍不新增错误类型：第 7 次命中那条已登记为第六批义务）
#   ③ hardware/r56_paperwork5_fix.txt（LF，载体，本脚本自己落盘）
#   ④ hardware/20260924_r56_paperwork5_fix崩溃traceback.txt（第一遍那份 traceback 从临时目录抄进仓库；
#      只登记在临时目录 = 没有取证，见 R46/R47 那一族"记录取证那步自己没落盘"）
# 两支：MODE=APPEND（订正句不在册 → 追加一行 + 复跑 paperwork5 + 落载体）
#       MODE=ALREADY（订正句已在册 = 第一遍落了正文却死在自己的前向对照上 → 一字不写 + 复跑 paperwork5 + 落载体）
# 规矩：已落地正文不许回写，只追加订正句；订正句里那段"被订正的原文"必须运行时现读、逐字插进来（不许凭记忆造引文）
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
P5 = os.path.join(HDIR, 'r56_paperwork5.py')
CRASH_EV = os.path.join(HDIR, '20260924_r56_paperwork5_fix崩溃traceback.txt')
SEC = '### 38.26'
TS = '[0-9-]{10} [0-9:]{8}'
# 订正句的行首标记：拆两段拼出来 —— 本文件源码若含整串，幂等闸与 paperwork5 的 N_CORR 计数都会自指
MARK = '- **订正' + '（第五批订正遍'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
BS = chr(92)


def money(x):
    return format(x, ',')


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def md5_(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def crlf_pure(p):
    b = open(p, 'rb').read()
    return b.count(b'\r\n') == b.count(b'\n')


# ---------- 进入时体检：两只目标形状 + 本遍的作用域 ----------
for p in (DOC, FREQ):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 本遍只该追加，行尾却已经混了，先查' % os.path.basename(p)
_b = open(DOC, 'rb').read()
_lines = rd(DOC).split('\r\n')
assert _lines[-1] == '' and _b.endswith(b'\r\n'), 'ABORT: 排查记录末行不是空串 ⇒ 插入点算不出来'
_h = [i for i, l in enumerate(_lines) if l.startswith(SEC)]
assert len(_h) == 1, 'ABORT: %s 命中 %d 处 ⇒ 本节标题被写重了' % (SEC, len(_h))
_next = [i for i in range(_h[0] + 1, len(_lines) - 1) if re.match(r'^#{2,3} +\d', _lines[i])]
assert not _next, 'ABORT: §38.26 之后还有第 %d 行的下一个标题 ⇒ 本节不在 EOF，本遍的"整只前缀"等式不适用，别落' % (
    _next[0] if _next else -1)
_last = max(i for i, l in enumerate(_lines[:-1]) if l.strip() != '')
assert _last > _h[0], 'ABORT: §38.26 里除标题外没有正文行 ⇒ 没东西可订正'
_rows_pre = len(_lines) - 1
_B0 = len(_b)
_FREQ_MD5_PRE = md5_(FREQ)
_DOC_MD5_PRE = md5_(DOC)

# ---------- 分支：订正句已在册 = 只重落载体（第一遍把正文落了、死在自己的前向对照上） ----------
_FIXROWS = [i for i, l in enumerate(_lines) if l.startswith(MARK)]
assert len(_FIXROWS) <= 1, 'ABORT: 订正句在册 %d 只（第 %s 行）⇒ 本遍这一行落重了，先查是谁又跑了一遍' % (
    len(_FIXROWS), [i + 1 for i in _FIXROWS])
MODE = 'ALREADY' if _FIXROWS else 'APPEND'

# ---------- 现读被订正的那一句：引文逐字取自盘上，不凭记忆造 ----------
#   ALREADY 支里那一行订正句自己也含被搜串（它逐字引了原句）⇒ 必须按 MARK 排除，否则命中 2 行、引文无从确定
_quoted = [l for l in _lines[_h[0]:_last + 1] if '新增写盘后反查' in l and not l.startswith(MARK)]
assert len(_quoted) == 1, 'ABORT: §38.26 里"新增写盘后反查"命中 %d 行 ⇒ 要么没落纸要么落重了，引文无从现读' % len(_quoted)
Q_LINE = _h[0] + 1 + _lines[_h[0]:_last + 1].index(_quoted[0])   # 1-based
Q_TXT = _quoted[0]
assert 'POSTWRITE' in Q_TXT, 'ABORT: 被订正那句里已经没有 `POSTWRITE` 指针 ⇒ 下面这段订正句的引文对不上'
_frag = Q_TXT[Q_TXT.index('并新增写盘后反查'):].strip()
assert _frag and BS not in _frag, 'ABORT: 从盘上截出的引文为空或含反斜杠'

# ---------- 跨文件核对：paperwork5 里那段 N_CORR 标记必须与本遍的 MARK 逐字同源 ----------
_p5 = rd(P5).replace('\r\n', '\n')
assert "'- **订正' + '" in _p5 and '（第五批订正遍' in _p5, \
    'ABORT: r56_paperwork5.py 里没有拆两段的 MARK 构造 ⇒ 它那格 N_CORR 认不出本遍这一行，SNAP 等式会假红'
#   第一遍就是红在这一格上的：那只工具的 SNAP 等式当时写成 `len(WIN_D) − N_CORR`（减式）。本遍落载体前要求减式已不在源码里
assert 'len(WIN_D) - N_CORR' not in _p5, \
    'ABORT: r56_paperwork5.py 里 SNAP 等式仍是减式（len(WIN_D) 减 N_CORR）⇒ 本遍追加之后它还会红，前向对照跑不绿'

LANDED_AT = NAMED_CAR = LANDED_LINE = 'NA（本遍真跑追加那一支，盘上还没有订正句）'
LA_TIE = 'NA'
if MODE == 'ALREADY':
    LANDED_LINE = _lines[_FIXROWS[0]]
    LANDED_AT = re.search(TS, LANDED_LINE).group(0)
    assert _FIXROWS[0] > Q_LINE - 1, 'ABORT: 订正句排在被订正那行之前 ⇒ 本节顺序不是"原文 + 订正"，先查'
    # 订正句里那两个指针（行号 + 引文 + 载体名）必须仍对得上本遍现读的盘 —— 订正句也是断言，也要有执行者
    _la = re.search(r'本节上面第 (\d+) 行那句「(.*?)」记的是', LANDED_LINE)
    assert _la and int(_la.group(1)) == Q_LINE and _la.group(2) == _frag, \
        'ABORT: 在册订正句指向第 %s 行，本遍现读的被订正行 = 第 %d 行 / 引文不等 ⇒ 那句已经飘了，别只重落载体' % (
            _la and _la.group(1), Q_LINE)
    LA_TIE = True
    _nc = re.search(r'取证载体 = `hardware/([^`]+)`', LANDED_LINE)
    assert _nc, 'ABORT: 在册订正句里读不到"取证载体 = `hardware/...`"那一句 ⇒ 载体名没有权威源'
    NAMED_CAR = _nc.group(1)

# ---------- 载体槽位：ALREADY 支必须落在在册那一句点名的名字上（否则那句成了假指针） ----------
_cands = ['r56_paperwork5_fix.txt'] + ['r56_paperwork5_fix_%d.txt' % i for i in range(2, 40)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)
if MODE == 'ALREADY':
    assert os.path.basename(CARRIER) == NAMED_CAR, \
        'ABORT: 在册订正句点名载体 = %s，本遍挑到的空槽 = %s ⇒ 落进去那句就是假指针，拒绝' % (NAMED_CAR, CARRIER)
# 本工具进目录时已在册的槽位载体（= 本工具自己写得了的那批名字，减去本遍这一只），按落盘先后排
_PHOTOS = sorted([f for f in _cands
                  if f != os.path.basename(CARRIER) and os.path.exists(os.path.join(HDIR, f))],
                 key=lambda f: os.path.getmtime(os.path.join(HDIR, f)))

FIX_TEXT = (MARK + '｜' + NOW_AT + '）**：本节上面第 ' + str(Q_LINE) + ' 行那句「' + _frag + '」记的是**落纸那一刻的形状**，'
            '而那个形状第一次真跑就崩：`rd()` 走通用换行把 CRLF 盘件读成 LF 归一串，与带 CRLF 的最终串永不相等 ⇒ '
            'assert 在两只目标已落盘**之后**才红（§38.21 ① 那一族第 7 次命中）。本遍现读 `hardware/r56_paperwork5.py` 的 '
            '`POSTWRITE = (` 那一格：反查已改为四条腿同取（盘上字节 == 最终串字节 / 现读大小 == 最终串 CRLF 编码长度 / 纯 CRLF / '
            '`rd()` 归一串 == `lf(最终串)`），另加仓库外改前快照的独立前缀反查（载体 `SNAPPREFIX` 行）。'
            '本节正文按规矩不回写，本行是追加的订正句；取证载体 = `hardware/' + os.path.basename(CARRIER) + '`，'
            '其 `POSCTL` 行记本句落纸后 paperwork5 的复跑读数。')

# ---------- 落盘前三步序：体检 → 哨兵/明文/反斜杠零容忍 → 写盘后独立回读 ----------
for _bad in ('@', '%s', '%d'):
    assert _bad not in FIX_TEXT, 'ABORT: 订正句里还有 %r 这种没吃参数的占位（落纸即假锚点）' % _bad
assert BS not in FIX_TEXT, 'ABORT: 订正句含反斜杠（§38.18 那一族）'
assert 'zizhao1' not in FIX_TEXT, 'ABORT: 订正句含口令明文'

ROWS1 = _rows_pre
if MODE == 'APPEND':
    _new = _lines[:_last + 1] + [FIX_TEXT] + _lines[_last + 1:]
    OUT = '\r\n'.join(_new)
    assert OUT.endswith('\r\n'), 'ABORT: 追加后文件不以 CRLF 收尾'
    _ob = OUT.encode('utf-8')
    assert _ob.startswith(_b), 'ABORT: 新串不是原串逐字前缀 ⇒ 本遍不只做了追加'
    assert _ob.count(b'\n') == _ob.count(b'\r\n'), 'ABORT: 追加后行尾混了'
    with open(DOC, 'wb') as f:
        f.write(_ob)
    _rb = open(DOC, 'rb').read()
    LANDED = (_rb == _ob and len(_rb) - _B0 == len(FIX_TEXT.encode('utf-8')) + 2
              and crlf_pure(DOC) and md5_(FREQ) == _FREQ_MD5_PRE)
    assert LANDED, 'ABORT: 写盘后独立回读不等（字节 %d vs %d / FreqErr md5 变了 = %s）⇒ 先查再落载体' % (
        len(_rb), len(_ob), md5_(FREQ) != _FREQ_MD5_PRE)
    ROWS1 = len(_new) - 1
    WRITTEN = 1
else:
    # 零写入证明：本遍一只正文都不碰 ⇒ 盘上字节 / md5 / mtime 三样都必须与进入时同值
    _rb, _ob = _b, _b
    LANDED = 'NA（本遍没写正文：订正句已在册，见 ALREADY 行）'
    assert md5_(DOC) == _DOC_MD5_PRE and open(DOC, 'rb').read() == _b, \
        'ABORT: ALREADY 支进入后发现 DOC 变了 ⇒ 谁在本遍之外又写了它，先查'
    WRITTEN = 0

# ---------- 第一遍那份 traceback：从临时目录抄进仓库（临时目录里的东西不算取证） ----------
#   挑法不许"取最新那只"：本遍自己的 stdout 就可能重定向进同一命名空间（r56fix2.txt 那次实测把这份证据挤成 0 命中）。
#   改按内容挑：崩溃行 + 被点名的工具名两条同时命中，命中多只则要求字节同值
_logs = sorted(glob.glob(os.path.join(tempfile.gettempdir(), 'r56fix*.txt')), key=os.path.getmtime)
CRASH_LINE = CRASH_EV_TIE = 'NA（本遍真跑追加那一支，还没有"第一遍崩在前向对照上"这回事）'
CRASH_SRC = CRASH_MD5 = 'NA'
CRASH_COPIED = CRASH_NHIT = 0
if MODE == 'ALREADY':
    assert _logs, 'ABORT: 临时目录里没有第一遍那份 traceback（r56fix*.txt）⇒ "第一遍死在 POSCTL"这句只剩叙述级证据，先把它找回来再落'
    _hit = []
    for _f in _logs:
        _tx = open(_f, encoding='utf-8', errors='replace').read()
        _ls = [l for l in _tx.split('\n') if l.startswith('AssertionError: ABORT: 追加段行数')]
        if not _ls:
            continue
        assert len(_ls) == 1, 'ABORT: 那只日志 %s 里"追加段行数"崩溃行命中 %d 只 ⇒ 一只日志里两次红，抄哪次说不清' % (
            os.path.basename(_f), len(_ls))
        assert 'r56_paperwork5_fix.py' in _tx, \
            'ABORT: 那只日志不是本工具（订正遍）自己崩的那一份 ⇒ 它是 paperwork5 的红，不能当"第一遍崩在前向对照上"的证据'
        _hit.append((_f, _ls[0], md5_(_f)))
    CRASH_NHIT = len(_hit)
    assert _hit, 'ABORT: 临时目录里 %d 只 r56fix*.txt 没有一只含"追加段行数"崩溃行 ⇒ 第一遍那次红没有原件，别落 CRASH 行' % len(_logs)
    assert len(set(h[2] for h in _hit)) == 1, \
        'ABORT: 含该崩溃行的日志有 %d 只且字节不等（%s）⇒ 分不清哪一份是第一遍那次，拒绝抄' % (
            CRASH_NHIT, [os.path.basename(h[0]) for h in _hit])
    _cf, CRASH_LINE, CRASH_MD5 = _hit[-1]
    CRASH_SRC = os.path.basename(_cf)
    assert BS not in CRASH_LINE, 'ABORT: 要嵌进载体的崩溃行含反斜杠（§38.18 那一族），只能引用不能整抄：%r' % CRASH_LINE[:80]
    assert '追加段行数 (15, 25)' in CRASH_LINE and '订正遍 1 行' in CRASH_LINE, \
        'ABORT: 崩溃行读数不是第一遍那两格（15,25 / 订正遍 1 行）⇒ 抄错了对象：%r' % CRASH_LINE[:80]
    # 抄进仓库这一步也要能复跑：那只已在册且 md5 与临时原件同值 ⇒ 本遍不覆写，只登记"已在册同值"；不同值才 ABORT
    _pre = os.path.exists(CRASH_EV)
    if _pre:
        assert md5_(CRASH_EV) == CRASH_MD5, \
            'ABORT: 仓库里已有那只崩溃 traceback 而 md5 与临时原件不等 ⇒ 不是同一份，拒绝覆写也拒绝登记'
    else:
        shutil.copyfile(_cf, CRASH_EV)
    CRASH_EV_TIE = md5_(CRASH_EV) == CRASH_MD5
    assert CRASH_EV_TIE, 'ABORT: 抄进仓库的 traceback 与临时目录那只 md5 不等 ⇒ 拷贝过程动了字节'
    CRASH_COPIED = 1 if not _pre else 0
    assert 'zizhao1' not in rd(CRASH_EV), 'ABORT: 要入库的 traceback 含口令明文'

# ---------- 前向对照：本句在册/落纸后复跑 paperwork5，它必须仍 rc=0（N_CORR 那格就是为这一趟改的） ----------
_SLOTS5_PRE = set(f for f in os.listdir(HDIR) if re.match(r'^r56_paperwork5(_\d+)?\.txt$', f))
_r = subprocess.run([sys.executable, P5], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = ' | '.join(l[:120] for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT=', 'DOC ')))
assert _r.returncode == 0 and _pos, 'ABORT: 复跑 paperwork5 rc=%d ⇒ 本遍/本工具把它弄红了，别把这条当收口：\n%s' % (
    _r.returncode, _r.stdout[-1500:] + _r.stderr[-800:])
# 它这一趟又落了一张自己的照片：拿"进入时名单"与"调用后名单"的差集登记，两支都成立（不按 mtime 猜）
def _slots5():
    return set(f for f in os.listdir(HDIR) if re.match(r'^r56_paperwork5(_\d+)?\.txt$', f))


_NEW5 = sorted(_slots5() - _SLOTS5_PRE, key=lambda f: os.path.getmtime(os.path.join(HDIR, f)))
assert len(_NEW5) == 1, 'ABORT: paperwork5 这一趟新增的照片数 = %d（%s）⇒ 前向对照没有唯一产物，登记不了' % (
    len(_NEW5), _NEW5)
DOC_TIE = md5_(DOC) == _DOC_MD5_PRE
assert DOC_TIE, 'ABORT: paperwork5 复跑之后 DOC 的 md5 变了 ⇒ 前向对照自己动了被检查物'
_sync_files = sorted(os.listdir(SYNC))
REV_LIST = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
assert REV_LIST.isdigit(), 'ABORT: rev-list 读数不是数字'
_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
_ALREADY_TXT = (
    '盘上第 %d 行已在册的那条订正句由本工具第一遍落纸，而那一遍**没落自己的载体** —— 它把正文写完之后就复跑 paperwork5，'
    '红在那只工具改前的 SNAP 减式上（崩溃行逐字见 CRASH 行）⇒ 追加式落地的东西不会因为 assert 回滚，'
    '所以"写了正文、没落载体"这一个形状在本批出现了两次（paperwork5 一次、本工具一次），第二次是本遍亲手。'
    '本遍处置 = 一字不写（零写入证明见 LAND 行），只补载体 + 把第一遍的 traceback 抄进仓库' % (_FIXROWS[0] + 1)) \
    if MODE == 'ALREADY' else \
    '本遍真跑追加那一支：订正句由本遍落纸，"第一遍崩在自己的前向对照上"这一形状此刻还没发生'
_lines2 = [
    'R56 第五批 订正遍  MODE=%s' % MODE,
    '本遍现跑于 %s（在册订正句的落纸时刻 = %s；载体由脚本自己落盘，在归档目录之外。两值不等 ⇒ 本遍是复跑支，'
    '与 §38.26 那一行同形（那是 APPEND/ALREADY 的判别副证））' % (_now2, LANDED_AT),
    'PHOTO 本工具的第 %d 张照片（进入时在册 %s）⇒ 权威 = 本张，前几张不复算、不引用为新证据，只点名它们存在' % (
        len(_PHOTOS) + 1, ' + '.join(_PHOTOS) or '无'),
    'ALREADY 幂等支（本遍走 ' + MODE + ' 这一支，点名第一遍）：' + _ALREADY_TXT,
    'TARGET 插入点（现算）：§38.26 标题在第 %d 行 / 本节末行在第 %d 行 / 其后无下一标题 = %s ⇒ 订正句插在末行之后（= 文件 EOF 之前），'
    '整只前缀等式因此适用' % (_h[0] + 1, _last + 1, not _next),
    'QUOTE 引文由本遍现读盘上第 %d 行逐字截取（不凭记忆造被订正原文）：截出长度 %d 字符，含 `POSTWRITE` 指针 = %s；'
    '它原样嵌进订正句 = %s / ALREADY 支回核：在册那句里写的行号与引文仍等于本遍现读值 = %s' % (
        Q_LINE, len(_frag), 'POSTWRITE' in _frag, _frag in FIX_TEXT, LA_TIE),
    'CRASH 第一遍崩溃行（逐字）：原件 = 临时目录那只 %s（md5 %s，按内容命中 %d 只、字节同值）；仓库副本 = %s，'
    '两侧 md5 相等 = %s（本遍新抄 %d 只）⇒ %s' % (
        CRASH_SRC, str(CRASH_MD5)[:8], CRASH_NHIT, os.path.basename(CRASH_EV), CRASH_EV_TIE, CRASH_COPIED, CRASH_LINE),
    'CROSS 跨文件核对：本遍的 MARK 拆两段（`- **订正` + `（第五批订正遍`），paperwork5 源码里那两段的构造在册 = %s；'
    '并且它原来的减式（len(WIN_D) 减 N_CORR）已不在源码里 = %s ⇒ 第一遍红的那一格是真被改掉了，不是被绕过去' % (
        "'- **订正' + '" in _p5, 'len(WIN_D) - N_CORR' not in _p5),
    'LAND 盘上账目（本遍 MODE=%s）：进入 %d 行 / %s B（md5 %s）→ 现在 %d 行 / %s B（md5 %s）⇒ 本遍写盘 %d 只正文、追加 %d 行；'
    'FreqErr md5 前后不变 = %s / 排查记录仍是纯 CRLF = %s' % (
        MODE, _rows_pre, money(_B0), _DOC_MD5_PRE[:8], ROWS1, money(os.path.getsize(DOC)), md5_(DOC)[:8],
        WRITTEN, ROWS1 - _rows_pre, md5_(FREQ) == _FREQ_MD5_PRE, crlf_pure(DOC)),
    'SEAL 本遍对 `hardware/ht305_sync/` 零写入：目录名单 %d 只，与进入时同一把尺现算；gen 24 仍是末版（本遍没跑清单、没跑 verify_manifest）' % (
        len(_sync_files)),
    "LEDGER 本遍现跑：命令原文 = `grep -cF -- '- [ ]' todo.md`，但本遍**执行的是同语义的 Python 逐行数**"
    '（数 `todo.md` 里以 `- [ ]` 开头的行）= %d ⇒ 输出与命令同义、尺子不同名，这一点写清楚而不是含糊过去（本遍没动 todo.md）' % (
        len([l for l in rd(os.path.join(REPO, 'todo.md')).replace('\r\n', '\n').split('\n') if l.startswith('- [ ]')])),
    'FIELD rev-list=%s（未推送提交数，口径 = `git rev-list --count origin/main..HEAD`）/ 本遍零串口动作 / 屏亮肉眼确认 0 次 / 未播提示音' % REV_LIST,
    'POSCTL 复跑第五批落地器 paperwork5 rc=%d / %s；它这一趟落的照片 = %s（进目录时本工具在册 %d 张，它那张不算在本工具的槽位里）' % (
        _r.returncode, _pos, _NEW5[0], len(_PHOTOS)),
    'NOTDONE 本遍没做：FreqErr 一字未动（第 7 次命中那条留作第六批义务）/ 串口 / 烧录 / 改 main 源码 / 重建固件 / 勾那 17 只未选项 / '
    '新建备份根 / 新建清单代次 / 第 14 代同步 / push / amend / 删除。第六批义务追加一条：把"前向对照排在写盘之后 ⇒ 红也回滚不了正文"'
    '这一族落成 FreqErr 新条 + 排查记录新节（本批已在两只工具上各见到一次：paperwork5 的写侧支、本工具的第一遍；'
    '族内序数不在这里登记，那是第六批台账的活）',
    'VERDICT=%s（排查记录本遍写盘 %d 只 / 追加 %d 行、FreqErr +0、载体 1 只 + 第一遍 traceback 副本 %d 只）' % (
        'OK-CARRIER-ONLY' if MODE == 'ALREADY' else 'OK-ONE-LINE-APPENDED', WRITTEN, ROWS1 - _rows_pre, CRASH_COPIED),
]
_txt = '\n'.join(_lines2) + '\n'
assert BS not in _txt, 'ABORT: 载体行里有反斜杠（§38.18 那一族）：%r' % [l for l in _lines2 if BS in l][:2]
assert 'zizhao1' not in _txt, 'ABORT: 载体含口令明文'
assert not re.search(r'@[A-Za-z0-9_]+@', _txt), 'ABORT: 载体行还有未回填占位 @%s@' % re.findall(r'@([A-Za-z0-9_]+)@', _txt)[:3]
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write(_txt)
print('MODE=%s 本遍写正文 %d 只 / 追加 %d 行（%d -> %d 行）/ DOC %s -> %s B' % (
    MODE, WRITTEN, ROWS1 - _rows_pre, _rows_pre, ROWS1, money(_B0), money(os.path.getsize(DOC))))
print('QUOTE 第 %d 行现读 %d 字符 / CRASH 行已嵌载体 = %s' % (Q_LINE, len(_frag), bool(_FIXROWS)))
print('POSCTL paperwork5 rc=%d / %s' % (_r.returncode, _pos[:220]))
print('VERDICT=%s CARRIER=%s PHOTO=%s' % (
    'OK-CARRIER-ONLY' if MODE == 'ALREADY' else 'OK-ONE-LINE-APPENDED', os.path.basename(CARRIER), _NEW5[0]))
