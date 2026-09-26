# FreqErr.md 第十九批落地器（R61c 收口遍第一段）：登记 §38.36 落地遍 + 第 16 代派生遍新暴露的四类缺陷。
# 本脚本自己就是第十九批第①条的执行者：纯追加，写盘后的盘上证明用三段式，预期值由**内存里拼好的最终字节串**
# 现数、并与分项加法**在写盘前**互等（第十八批第①条讲"证明不会看插入"，本批第①条讲"预期式自己就是待检正文"）。
# 本批新装三道闸（全部排在写盘之前）：
#   ①引文闸 = 正文里凡是自称"本文件某条"的短语，逐条对现读 FreqErr 求命中，命中 0 即 ABORT；
#   ②崩遍零改动独立回读闸 = 第十九批第③条要求的那三条件，实装成 assert 而不是叙述；
#   ③内容级四道 = 撇号 / 反斜杠字符 / 未插值占位符 / PROV_PASS 宏值命中，全在写盘前。
# 规矩照旧：幂等门（权威判据 = 同前缀载体里有没有写盘后令牌 LANDED，见本批第①条）→ 全部裁决前置 → pre-image → 三段式。
import datetime
import glob
import hashlib
import io
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
EVB = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')     # 被引载体（上一代取证）
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')      # 本遍取证落点
DSC = os.path.join(REPO, 'hardware', 'r61c_sync', 'scripts')      # 本脚本与被引派生件
BSRC = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
for _d in (EVB, EV, DSC, BSRC):
    assert os.path.isdir(_d), 'ABORT: 目录不存在 ' + _d
    assert 'ht305_sync' not in _d, 'ABORT: 取证落点指进封存归档目录 ' + _d
MARK = 'R61 第十九批'
BS = chr(92)

_T0 = time.time()
pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十九批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
pl = pre.splitlines()
EB = '[错误类型]'.encode('utf-8')
n_before = sum(1 for l in pl if l.startswith(EB))
lines_before = pre.count(b'\n')
bytes_before = len(pre)
freqerr_md5_before = hashlib.md5(pre).hexdigest()[:8]


def car(prefix, token=None, base=EVB):
    hits = [p for p in sorted(glob.glob(os.path.join(base, prefix)))
            if token is None or token in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 载体前缀 %r（含令牌 %r）命中 %d 只（应为 1）' % (prefix, token, len(hits))
    return hits[0], io.open(hits[0], encoding='utf-8', errors='replace').read()


# ---------- 本批正文里的每个数都必须读自盘上载体，不许手抄 ----------
# ① §38.36：崩遍（红在写盘后）与权威遍（含核销三步）
CRASH = os.path.join(EVB, 'r61b_3836_160241.txt')
assert os.path.isfile(CRASH), 'ABORT: 崩遍载体不在盘上'
ct = io.open(CRASH, encoding='utf-8', errors='replace').read()
_m = re.search(r'line (\d+), in <module>', ct)
RAISE_LN = int(_m.group(1))
_m = re.search(r'AssertionError: ABORT: 行数 (\d+) != 预期 (\d+)', ct)
ONDISK_L, EXP_L = int(_m.group(1)), int(_m.group(2))
assert ONDISK_L + 1 == EXP_L, 'ABORT: 崩遍那句红不是"差 1"那一案，本遍不许套模板'
_m = re.search(r'PRE-IMAGE (\S+) \((\d+) B / md5 (\w+)', ct)
CRASH_PIMG, CRASH_PIMG_B = _m.group(1), int(_m.group(2))
assert 'VERDICT=LANDED' not in ct, 'ABORT: 被当崩遍点名的载体里有写盘后令牌 ⇒ 它是完成态，本遍措辞全错'

AUTH, at = car('r61b_3836_161042.txt', 'VERDICT=LANDED rc=0')
_m = re.search(r'STALE-TAIL 核销：现件 (\d+) B / (\d+) 行，其中尾节 (\d+) B / (\d+) 行 先整体归档进 (\S+)，头段与 (\d+) 只 pre-image', at)
STALE_B, STALE_L, TAIL_B, TAIL_L, STALE_NAME, PIMG_N = (
    int(_m.group(1)), int(_m.group(2)), int(_m.group(3)), int(_m.group(4)), _m.group(5), int(_m.group(6)))
_m = re.search(r'^PRE-IMAGE (\S+) \((\d+) B / md5 (\w+)', at, re.M)
HEAD_B, HEAD_NAME = int(_m.group(2)), _m.group(1)
_m = re.search(r'PREFIX (\d+) 行逐字等 / APPEND (\d+) 行逐行等', at)
HEAD_L, APPEND_L = int(_m.group(1)), int(_m.group(2))
_m = re.search(r'RECORD (\d+) 行 / (\d+) B -> (\d+) 行 / (\d+) B \| MD5 (\w+) -> (\w+)', at)
POST_L, POST_B, POST_MD5 = int(_m.group(3)), int(_m.group(4)), _m.group(6)
_m = re.search(r'DEFECTS (\d+) 处（本遍进入前崩遍载体 \[(.*?)\]）', at)
DEFECT_N = int(_m.group(1))
CRASH36 = re.findall(r"(r61b_3836_\d+\.txt)", _m.group(2))
assert DEFECT_N == len(CRASH36), 'ABORT: 缺陷只数与崩遍载体只数不同值 ⇒ 那句在册读数不可信'
# 四条等式：崩遍留下的尾节、核销后的头段、权威遍的终态，全部互核（HEAD_B/TAIL_B/STALE_B 来自同一只载体）
assert STALE_B - HEAD_B == TAIL_B and STALE_L - HEAD_L == TAIL_L, 'ABORT: 尾节差值与现读不等'
assert HEAD_L + APPEND_L == POST_L, 'ABORT: 权威遍三段式的行数等式在载体里就不成立'
assert CRASH_PIMG_B == HEAD_B, 'ABORT: 崩遍 pre-image 尺寸 != 头段尺寸 ⇒ 它读的已不是头段'
pimgs = sorted(glob.glob(os.path.join(EVB, 'record_pre3836_*.md')))
assert len(pimgs) == PIMG_N + 1, 'ABORT: 盘上 pre-image 只数 %d != 载体在册 %d（在册那只算崩遍自己写的）' % (len(pimgs), PIMG_N + 1)
assert os.path.isfile(os.path.join(EVB, STALE_NAME)), 'ABORT: 被核销尾节的归档件不在盘上 ' + STALE_NAME

# ② ③ ④ 第 16 代派生遍
DCRASH, dct = car('derive_r61c_161508.txt', base=EV)
assert 'VERDICT=DERIVED' not in dct and 'WROTE=' not in dct, 'ABORT: 派生崩遍载体含写盘后令牌 ⇒ 第③条措辞为假'
_m = re.search(r'line (\d+), in <module>', dct)
KEYERR_LN = int(_m.group(1))
_m = re.search(r"KeyError: [\"']([^\"']+)[\"']", dct)
KEY_NAME = _m.group(1)
DOK, dot = car('derive_r61c_161520.txt', 'VERDICT=DERIVED rc=0', base=EV)
WROTE_N = int(re.search(r'WROTE=(\d+)', dot).group(1))
PTR_N, PTR_MISS = (int(x) for x in re.search(r'POINTERS_SCRIPTS=(\d+) MISSING=(\d+)', dot).groups())
assert PTR_MISS == 0 and PTR_N > 0, 'ABORT: 假指针执行者那格不是"非 0 只、0 缺"'
# 派生件名单取自成功遍载体报告行的第二列（不从目录里现扫：本脚本自己就住在那个目录里，扫出来会多一只）
derived = sorted(os.path.join(DSC, x) for x in re.findall(r'^\S+ -> (\S+) \| src_lines=', dot, re.M))
assert len(derived) == WROTE_N, 'ABORT: 载体在册派生件只数 %d != WROTE=%d' % (len(derived), WROTE_N)
for _p in derived:
    assert os.path.isfile(_p), 'ABORT: 在册派生件不在盘上 ' + _p
c_mtime = os.path.getmtime(DCRASH)
d_oldest = min(os.path.getmtime(p) for p in derived)
assert d_oldest > c_mtime, 'ABORT: 有派生件早于崩遍载体 ⇒ "那一遍一只都没写"是假的'
GAP = d_oldest - c_mtime
L18, _ = car('r61b_freqerr18_*.txt', 'VERDICT=LANDED rc=0')
# 第②条的凭证 = 三步替换的字面行序 + 哨兵两端 assert（不是"我踩过了"）
dtxt = io.open(os.path.join(BSRC, 'derive_r61c.py'), encoding='utf-8').read()
_ph = re.search(r"PH = '([^']+)'", dtxt).group(1)
_i_a = dtxt.index("t.replace('r61b', PH)")
_i_e = dtxt.index("t.replace('r61', 'r61b')")
_i_a2 = dtxt.index("t.replace(PH, 'r61c')")
assert _i_a < _i_e < _i_a2, 'ABORT: 哨兵三步的字面行序不是 A/E/A2'
assert dtxt.count('assert PH not in t') == 2, 'ABORT: 哨兵两端闸（源侧 + 产物侧）不足 2 处'
PH_ASSERT = dtxt.count('assert PH not in t')
_dl = dtxt.splitlines()
_ln = lambda needle: next(i + 1 for i, l in enumerate(_dl) if needle in l)
STEP_ORDER = '%d < %d < %d' % (_ln("t.replace('r61b', PH)"), _ln("t.replace('r61', 'r61b')"),
                               _ln("t.replace(PH, 'r61c')"))
WRITE_LN = _ln("open(dst, 'wb')")
assert KEYERR_LN < WRITE_LN, 'ABORT: 崩点行号 %d 不在写盘语句行号 %d 之前 ⇒ "崩在写盘之前"这句为假' % (KEYERR_LN, WRITE_LN)
PH_RES = sum(io.open(p, encoding='utf-8', errors='replace').read().count(_ph) for p in derived)
assert PH_RES == 0, 'ABORT: 哨兵残留在产物里 %d 次' % PH_RES
# 第④条的凭证 = 裸子串命中行数 与 带负向前视命中行数 的差值（在同一只产物上量）
RT = os.path.join(DSC, 'r61c_roundtrip.py')
rt_lines = [l for l in io.open(RT, encoding='utf-8').read().splitlines() if not l.lstrip().startswith('#')]
_bare = [l for l in rt_lines if re.search('R61', l)]
_neg = [l for l in rt_lines if re.search(r'R61(?!C)', l)]
assert len(_bare) >= 1 and len(_neg) == 0, 'ABORT: 第④条的"尺错"现场不复现（裸子串 %d 行 / 负向 %d 行）' % (len(_bare), len(_neg))
BARE_LN, NEG_LN = len(_bare), len(_neg)
SRC_R61_TAG = io.open(os.path.join(BSRC, 'r61b_roundtrip.py'), encoding='utf-8').read().count('R61_ROUNDTRIP_AT')
DST_R61C_TAG = io.open(RT, encoding='utf-8').read().count('R61C_ROUNDTRIP_AT')
assert SRC_R61_TAG == DST_R61C_TAG == 1, 'ABORT: 标签前身与本代读数不是一一对应 ⇒ 第④条那句并排登记写不出真话'
tag_files = [os.path.basename(p) for p in derived if 'R61C' in io.open(p, encoding='utf-8', errors='replace').read()]

# 本批自己进入之前的崩遍（第十九批第③条要求点名"它没写盘"，所以这一格必须现扫而不是叙述）。
# 三条同时才算一只崩遍：mtime 早于本遍进入 + 非空 + 留有错误证据 —— 本遍那只正被 shell 原地重定向的载体
# 满足第一条但为空，不满足第二条，不能混进名单（否则"崩过几遍"恒多 1）。
crash19 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61c_freqerr19_*.txt'))
                 if os.path.getmtime(p) < _T0 and os.path.getsize(p) > 0
                 and ('Traceback' in io.open(p, encoding='utf-8', errors='replace').read()
                      or 'Error' in io.open(p, encoding='utf-8', errors='replace').read()))
for _f in crash19:
    _t = io.open(os.path.join(EV, _f), encoding='utf-8', errors='replace').read()
    assert 'PRE-IMAGE' not in _t and 'VERDICT=LANDED' not in _t, 'ABORT: 本批前一遍崩溃载体其实动过盘：' + _f

CITED = ['裸子串 search 静默取回上一遍', '更糟的是它排在写盘之后', '逐字派生会把上一代',
         '纯插入式落地器不验节间空行', '单引号字面量提前闭合']
_pptxt = pre.decode('utf-8')
_cite_bad = [x for x in CITED if x not in _pptxt]
assert not _cite_bad, 'ABORT: %d 条自证引文在现读 FreqErr 里 grep 不到：%s' % (len(_cite_bad), _cite_bad)

ENTRIES = [
    # ① 写盘后的预期式自己就是待检正文
    ('[错误类型] **落地器把"预期终态"写成一条自己没验过的分项加法（给尾部 CRLF 预留了一只幻行）⇒ 断言红在写盘之后：'
     '盘已动、载体无 LANDED，而"重跑一遍"恰好会得到同一个数、把这条错式洗成永久隐身（R61b 实测：§38.36 那一遍 3930 对 3931）**',
     '症状：`land_r61b_3836.py` 第 %d 行的写盘后断言报 `AssertionError: ABORT: 行数 %d != 预期 %d`。`exp_lines` 当时写成'
     '"头段行数 + 本遍追加行数 + 1"，那只 `+1` 是给"末行没有行尾符"的文件预留的，而本仓库这类台账文件末行以 CRLF **收尾** ⇒ '
     '`splitlines()` 不产生幻行，预期恒比盘上多 1。三件事同时成立才是要登记的形状：①那一遍**已经写盘**（现件 %d B / %d 行，'
     '其中它自己追加的尾节 %d B / %d 行），所以它是"崩在写盘后、改动在盘上"，不是"崩在写盘前、零改动"；②它的载体里'
     '**没有** `VERDICT=LANDED`，只有 `PRE-IMAGE %s (%d B)` 那一行 —— 写盘前快照不是完成态凭证；③预期那个数（%d）恰好等于'
     '核销重写之后的终态行数 %d ⇒ 若我当时的第一反应是"重跑一遍看绿"，两遍会打出同一个数，算式里那只 `+1` 就永远看不见。'
     % (RAISE_LN, ONDISK_L, EXP_L, STALE_B, STALE_L, TAIL_B, TAIL_L, CRASH_PIMG, CRASH_PIMG_B, EXP_L, POST_L),
     '→ 正确做法：①**写盘后的"预期值"自己也是待检正文**：落盘前用两种独立推法互等 —— 一把在内存里拼好最终字节串现数 '
     '`len((pre + body).splitlines())`，一把用分项加法"头段行 + 追加行"，相等才动手；任何"我以为需要的口径修正"（那只 `+1`）'
     '必须被第一把尺证实或否证，不许只活在第二把尺里；②**幂等门的权威判据 = 同前缀载体里有没有写盘后令牌 `VERDICT=LANDED`**，'
     '不是"正文里有没有本节标题"：标题在而 LANDED 不在 ⇒ 那是过期正文，处置是**核销**，不是叠加、也不是"再追加一遍"；'
     '③核销三步（本遍实测）：先把现件**整体**归档（`%s` / %d B / %d 行），再断言"去掉尾节剩下的头段"与盘上每只 pre-image'
     '（现读 %d 只，逐只 getsize 与现读 md5）**逐字节相等**，全等才把目标回落到头段、当作本遍的 pre；'
     '④回落之后仍走三段式：前缀 %d 行逐字等 / 追加段 %d 行逐行等 / 后缀为空，再加 `头段行 + 追加行 == 终态行`（本遍 %d + %d == %d）；'
     '⑤判据红的时候先问"红在哪一行"：红在写盘前 = 盘上零变化，红在写盘后 = 本遍产物已在盘上 —— 两者下一步完全不同，'
     '而 **rc 非 0 本身不告诉你是哪一种**。' % (STALE_NAME, STALE_B, STALE_L, len(pimgs),
                                              HEAD_L, APPEND_L, HEAD_L, APPEND_L, POST_L),
     '→ **同族**：本文件第十八批第①条「盘上内容是对的」（那次是证明不会看插入，本次是预期式自己错，且多一层：盘真留了东西）；'
     '本文件「更糟的是它排在写盘之后」那条（同一形状：互核门排在写盘后 ⇒ 正文已落、载体未落）；'
     '用户记忆「崩溃那次的读数不作数」「完成态数字必须在载体落盘后现数」。'),

    # ② 替换源与目标互为子串 ⇒ 哨兵三步
    ('[错误类型] **换代替换表里"源名字"与"目标名字"互为子串（`r61b` 含 `r61`）⇒ 两条替换任何先后次序都至少吃错一次：'
     '前一步产物被后一步再换掉、或旧名被加成双层后缀。修法是先抽哨兵、换完再装回（derive_r61c 三步 A/E/A2，'
     '本条登记的是"设计期被反度量挡住"那一类，没有崩遍载体）**',
     '症状：第 16 代同步件派生器要把 6 只 `r61b` 件逐字派生成 `r61c`，而源里同时存在两种形态 —— 本代名 `r61b`（要变 `r61c`）'
     '与裸代根 `r61`（包名、目录名、解包根前缀，要变 `r61b`）。因为 `r61b` 以 `r61` 开头，两条替换互相侵蚀：'
     '先 `r61b -> r61c` 再做 `r61 -> r61b`，上一步刚换好的 `r61c` 里那段 `r61` 会被第二次替换再吃掉（写成 `r61bc`）；'
     '反过来先 `r61 -> r61b` 再做 `r61b -> r61c`，源里本来的 `r61b` 先被撑成 `r61bb`。'
     '**这一条没有崩遍载体**：它在写第一遍之前就被下面的反度量挡住，所以登记它的凭证是字面行序与 assert 命中数，'
     '不是"我踩过一次"（现读 `derive_r61c.py`：三步在源码里的行号先后为 %s，哨兵两端 assert 各 %d 处，'
     '哨兵字面量在 %d 只产物里出现 %d 次）。' % (STEP_ORDER, PH_ASSERT, len(derived), PH_RES),
     '→ 正确做法：①凡"上一代名"与"本代名"共享前缀（本仓库三代同形 `r61` / `r61b` / `r61c`），替换必须走**哨兵三步**：'
     'A 抽（本代名 -> 哨兵，抽前 assert 源里不含该串）、E 换（裸代根 -> 上一代名）、A2 装回（哨兵 -> 本代名）；'
     '②**两端都要有闸**：源侧 assert 哨兵预先不存在，产物侧 assert 哨兵残留 0 次（残留 = 有条路径没走完 A2）；'
     '本遍把这条同时放进 `hard` 反度量字典与报告行的 LEFT，所以"哨兵没装回"在**每一只**派生件的报告里都可见，'
     '不依赖那句 assert 崩出来才被看见；③降序替换只解决**数字类**（本遍的 `zsynctest17` / `zsynctest16` 与'
     '`第 15 代` / `第 14 代`），它解决不了**互为子串的字母类**，两类要分开设表；'
     '④没踩到的坑也要登记，但必须标明"凭证类型 = 字面量行序 + assert 命中数"，与"红过一遍"分开，否则下一代会以为这条已被实测过。',
     '→ **同族**：本文件「逐字派生会把上一代」那条（同族母题：派生连带把缺陷派生过来）；'
     '第十八批第④条（同一族"语法体检量不到的层次，要用内容级闸量"——本条量的是替换表的词法级自伤）。'),

    # ③ 改了数据形状没改它的 assert
    ('[错误类型] **改了一只反度量字典的键名，没改读它的那句 assert ⇒ KeyError 红在裁决段（R61c 实测：`hard` 的键已换成哨兵串，'
     '而 assert 仍按上一代那个已被换掉的键名取值）；本案唯一的好消息是"全部裁决排在写盘之前"当场兑现成盘上零变化**',
     '症状：`derive_r61c.py` 16:15:08 那一遍（载体 `%s`）在第 %d 行报 `KeyError: %s`。那一遍把 `hard` 的键从上一代那三个'
     '字面量换成"本代哨兵"那三个，而紧跟其后的 assert 还在按键名读一个已被换掉的键。它过了语法体检，因为'
     '"按键名读一个不存在的键"在语法上完全合法；`ast.parse` 这一层永远量不到它。盘上态由本遍独立回读判定，不靠记忆：'
     '崩点行号 %d 在该脚本第一只写盘语句（第 %d 行）之前，崩遍载体里既无 `WROTE=` 也无 `VERDICT=DERIVED`，'
     '%d 只在册派生件的 mtime 全部晚于该载体（最早一只晚 %.3f s）⇒ 那一遍确实一只都没写。' % (
         os.path.basename(DCRASH), KEYERR_LN, KEY_NAME, KEYERR_LN, WRITE_LN, WROTE_N, GAP),
     '→ 正确做法：①**数据结构与它的消费者同遍改**：键名一改，读它的 assert、下游解析正则、台账格式句全是要改的地方 —— '
     '可执行版本是让键名与 assert 出自同一处定义（同一变量，而不是把字面量抄第三遍）；②崩遍的"零改动"不许靠叙述登记：'
     '本遍把它实装成三条 assert（写盘后令牌缺席 + 产物 mtime 全晚于成功遍 + 目标目录只数），缺一即 ABORT；'
     '③这条纪律的回报要用**盘上零变化**验收，不用"我小心了"验收 —— 第十八批第④条第③点已经说过"rc 非 0 不蕴含零改动"，'
     '本案是它第一次**正面成立**的例子，正面也要有执行者；④成本不对称：KeyError 只花一遍，但它红在写盘后就要走第①条的'
     '核销三步（归档 + 头段对账 + 重写），红在写盘前只是重跑 —— 所以"裁决全部前置"不是洁癖，是把核销成本从盘上搬回内存。',
     '→ **同族**：第十八批第④条（语法闸与内容级闸之间的空档，本条是键名那一路）、第十八批第①条第⑤点'
     '（崩在写盘后的那一遍，盘上态要由下一遍独立回读判定）；用户记忆「新判据分支要有真源码可达性取证」——这里被反用一次：'
     '改完的分支必须**真的跑得动**才能红出来，跑不到的分支连 KeyError 都不给你。'),

    # ④ 反度量裸子串吃掉本代正面读数
    ('[错误类型] **反度量（"上一代名字不许出现在代码行"）用裸子串 ⇒ 把本代刚换出来的正面读数判成余留：'
     '`R61C_ROUNDTRIP_AT` 本身以 `R61` 开头，钉死 `R61` 等于要求这一行永远不许存在（R61c 实测：红的是尺，不是那六只件）**',
     '症状：派生器的 OLD_TOKENS 里新加了一条大写 `R61`（指代上一代那只串口标签），扫法是"命中且非注释行即 ABORT"。'
     '而 F 步换出来的正是 `R61C_ROUNDTRIP_AT`（%d 只产物里 %d 只含它）⇒ 按裸子串扫，产物里那 %d 行**每一行都是本代该有的'
     '正面读数**，却全部命中，六只一起红。同一遍里如果我只看到"ABORT: 上一代名字残留"这句，很可能的处置是把 F 步撤掉'
     '（把标签退回上一代拼法）—— 那是把修好的东西改回去来迁就尺。发现它是尺错的动作是本遍这次现读：'
     '同一只文件、同一批代码行，裸子串命中 %d 行，带负向前视命中 %d 行。' % (len(derived), len(tag_files), BARE_LN, BARE_LN, NEG_LN),
     '→ 正确做法：①**反度量与正度量成对出现**：`R61` 那一路的反向钉必须写成 `R61(?!C)`，并把两条命中数都打进报告 —— '
     '差值大于 0 才说明这条纪律真的在咬，两条同为 0 只是没量到东西；②报告里同时打印**正面读数的命中数**（本遍 = 产物侧 '
     '`R61C_ROUNDTRIP_AT` %d 次）与反向读数，缺一边就是半绿：只看红绿看不出"我把正确的东西判成错的"；'
     '③把"前身"与"本代"并排登记（源侧 `R61_ROUNDTRIP_AT` %d 次 -> 产物侧 %d 次），让"换对了"和"没余留"用同一次扫描说清；'
     '④凡是"上一代名"与"本代名"同前缀的场合（本仓库三代 r61 / r61b / r61c），裸子串一律不合法 —— 要么负向前视，'
     '要么整词边界，二选一，并且这条要写进反度量自己的定义处，不留在注释里。' % (DST_R61C_TAG, SRC_R61_TAG, DST_R61C_TAG),
     '→ **同族**：本文件「裸子串 search 静默取回上一遍」（同一把尺的反方向：那次子串取到旧的一遍，这次取到新的那一行）、'
     '第十八批第③条（"0 行 differ"是假绿；本案是它的镜像 —— "非 0 命中"是假红，共同点仍是**绿与红由命令给、不由判据给**）。'),
]

for _t, _s, _f, _k in ENTRIES:
    for _l in (_t, _s, _f, _k):
        assert chr(39) not in _l, 'ABORT: 正文含 ASCII 撇号，第十八批第④条讲的就是这个：' + _l[:60]
        assert BS not in _l, 'ABORT: 正文含反斜杠字符'
        assert sec.decode('utf-8') not in _l, 'ABORT: 正文含口令明文'

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += [t, s, fix, kin, '']

CARRIED = [AUTH, CRASH, os.path.join(EVB, STALE_NAME), os.path.join(EVB, CRASH_PIMG),
           os.path.join(EVB, HEAD_NAME), DCRASH, DOK, L18,
           os.path.join(BSRC, 'derive_r61c.py'), RT] + derived
CARRIED_B = 0
for _p in set(CARRIED):
    assert os.path.isfile(_p), 'ABORT: 正文点名的载体不在盘上 ' + _p
    CARRIED_B += os.path.getsize(_p)
N_CARRIED = len(set(CARRIED))
CRASH19_TXT = ('%d 只（%s），逐只现读其 stdout 不含 PRE-IMAGE 与 LANDED 两个标记 ⇒ 那几遍全部崩在写盘之前、盘上零改动'
               % (len(crash19), '、'.join('`%s`' % x for x in crash19))) if crash19 else \
    '0 只（按 `r61c_freqerr19_*.txt` 前缀现扫为空 ⇒ 本批首遍即绿，无账可记）'


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十九批 %d 条】** 追加之前现读磁盘：`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B（md5 前 8 位 %s）；'
        '本批正文 = **%d** 条 / **%d** 行（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；'
        '台账行自身不另加条目；**本遍无就地订正**（纯追加）；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**。'
        '**盘上证明 = 三段式**（第十九批第①条自己就是它的执行者，也是它把"预期值由分项加法独走"这条改掉的）：'
        '前缀 %d 行逐字等 + 追加段 %d 行逐行等 + 后缀为空，另加行数等式 盘上行 == 前 %d + %d；'
        '**预期值写盘前先两推法互等**（内存现数 对 分项加法），那只给尾部 CRLF 预留的幻行 `+1` 就是这样被否证的（第十八批第①条'
        '的盘上证明形状 + 本批第①条的预期式自查）。'
        '本遍进入前的读数出处（正文与台账行点名的每只载体现跑 isfile + getsize 过，第十八批第②条的闸：共 **%d** 只 / **%d** B）：'
        '`hardware/r61b_sync/evidence/` 下 `%s`（第十八批 rc=0）、'
        '`%s`（§38.36 权威遍 VERDICT=LANDED rc=0）、`%s`（§38.36 崩遍，红在第 %d 行 / 盘上 %d 行 对 预期 %d 行）、'
        '`%s`（被核销尾节的整体归档件）、`%s`（§38.36 崩遍留下的 pre-image）；'
        '`hardware/r61c_sync/evidence/` 下 `%s`（第 16 代派生崩遍 KeyError）、`%s`（第 16 代派生成功遍 WROTE=%d）；'
        '`hardware/r61c_sync/scripts/` 下 `%s`（本脚本自身）。'
        '**本遍进入前 rc=1 的那几遍 = %s**；'
        '本遍新装三道闸（都排在写盘之前）：①**引文闸** = 正文自称"本文件某条"的短语逐条对现读 FreqErr 求命中（本遍 %d 条全中）；'
        '②**崩遍零改动独立回读闸** = 第十九批第③条那三条实装成 assert（写盘后令牌缺席 + %d 只在册派生件 mtime 全晚于崩遍载体 + '
        '崩点行号早于写盘语句行号），并把 §38.36 那三条等式（现件减头段 == 尾节的字节与行数、头段加追加 == 终态行、'
        '崩遍 pre-image 尺寸 == 头段尺寸）同遍复算；③**内容级闸** = 本批新写文本含 ASCII 撇号行数 = 0、含反斜杠字符行数 = 0、'
        '未插值占位符 = 0、PROV_PASS 宏值命中 = 0（口令由脚本从宏现读、全程不打印）。' % (
            ts, len(ENTRIES), n_before, lines_before, format(bytes_before, ','), freqerr_md5_before,
            len(ENTRIES), len(rows),
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ','),
            lines_before, len(rows) + 1, lines_before, len(rows) + 1,
            N_CARRIED, CARRIED_B,
            os.path.basename(L18),
            os.path.basename(AUTH), os.path.basename(CRASH), RAISE_LN, ONDISK_L, EXP_L,
            STALE_NAME, os.path.basename(CRASH_PIMG),
            os.path.basename(DCRASH), os.path.basename(DOK), WROTE_N,
            os.path.basename(__file__),
            CRASH19_TXT, len(CITED), WROTE_N))


hdr = build(bytes_before)
for _ in range(12):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与台账行自身长度不收敛')

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
exp = pre + append_bytes
assert sec not in exp, 'ABORT: 本遍写出去的字节含口令明文'
_newtext = append_bytes.decode('utf-8')
_stray = [(i + 1, re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}|%[sd]\b', l).group(0))
          for i, l in enumerate(_newtext.split('\n'))
          if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本遍新写文本有 %d 行带未插值占位符（追加段内行号, 命中标记）：%s' % (len(_stray), _stray)
assert BS not in _newtext, 'ABORT: 本批新写文本含反斜杠字符'
assert chr(39) not in _newtext, 'ABORT: 本批新写文本含 ASCII 撇号'
exp_entries = sum(1 for l in exp.splitlines() if l.startswith(EB))
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 终态条目数 %d != %d' % (exp_entries, n_before + len(ENTRIES))
assert hdr.encode('utf-8') in exp and ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: 终态字节数与台账行不自洽'
# 第十九批第①条的执行者：两推法在**写盘前**互等
_p1_lines = len(exp.splitlines())
_p1_bytes = len(exp)
assert _p1_lines == lines_before + len(rows) + 1, \
    'ABORT: 行数两种推法不等 %d != %d ⇒ 本批第①条没被本遍执行' % (_p1_lines, lines_before + len(rows) + 1)
assert _p1_bytes == bytes_before + len(append_bytes), 'ABORT: 字节两种推法不等'

_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'freqerr_pre19_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), freqerr_md5_before))
print('CITED %d/%d 条自证引文在现读正文全中' % (len(CITED), len(CITED)))
print('CRASH-READBACK 崩遍 %s 红在第 %d 行 / 盘上 %d 行 vs 预期 %d 行 / 无 LANDED' % (
    os.path.basename(CRASH), RAISE_LN, ONDISK_L, EXP_L))
print('THREE-EQ 现件 %d - 头段 %d == 尾节 %d B | %d - %d == %d 行 | 头段 %d + 追加 %d == 终态 %d 行' % (
    STALE_B, HEAD_B, TAIL_B, STALE_L, HEAD_L, TAIL_L, HEAD_L, APPEND_L, POST_L))
print('DERIVE-CRASH %s KeyError=%s 第 %d 行 / %d 只派生件最早一只晚 %.3f s / WROTE=%d PTR=%d MISS=%d' % (
    os.path.basename(DCRASH), KEY_NAME, KEYERR_LN, WROTE_N, GAP, WROTE_N, PTR_N, PTR_MISS))
print('BARE-VS-NEG %s 裸子串 %d 行 / 负向前视 %d 行 | 前身 %d 次 -> 本代 %d 次' % (
    os.path.basename(RT), BARE_LN, NEG_LN, SRC_R61_TAG, DST_R61C_TAG))
print('SENTINEL 三步行序 A<E<A2 已核 / 两端 assert 2 处 / 产物残留 0 只')

io.open(TGT, 'wb').write(exp)
chk = io.open(TGT, 'rb').read()
cl, ol = chk.splitlines(), pl
# —— 三段式盘上证明（纯追加：不用逐位置差集，第十八批第①条）——
assert len(cl) == len(ol) + len(rows) + 1, 'ABORT: 行数增量与预期不等（%d -> %d）' % (len(ol), len(cl))
assert cl[:len(ol)] == ol, 'ABORT: 前缀未逐字保持（本遍是纯追加，前缀一字节都不许动）'
_ap = append_bytes.split(b'\r\n')[:-1]
assert cl[len(ol):] == _ap, 'ABORT: 追加段逐行不等'
assert len(chk) == _p1_bytes and len(cl) == _p1_lines, 'ABORT: 盘上复量 != 写盘前两推法互等的值'
post_entries = sum(1 for l in cl if l.startswith(EB))
assert (post_entries, chk.count(b'\n'), len(chk)) == (exp_entries, exp.count(b'\n'), len(exp)), 'ABORT: 盘上复量与内存终态不同值'
assert MARK.encode('utf-8') in chk and post_entries == n_before + len(ENTRIES)
print('ENTRIES %d -> %d (本批 +%d) | LINES %d -> %d | BYTES %d -> %d' % (
    n_before, post_entries, len(ENTRIES), lines_before, chk.count(b'\n'), bytes_before, len(chk)))
print('PREFIX %d 行逐字等 / APPEND %d 行逐行等 / 后缀为空（三段式）' % (len(ol), len(_ap)))
print('MD5 %s -> %s' % (freqerr_md5_before, hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
