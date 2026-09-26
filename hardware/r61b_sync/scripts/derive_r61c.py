# 第 16 代（r61c 代）同步件派生器：把 `hardware/r61b_sync/scripts/` 那 6 只**逐字**搬成 `hardware/r61c_sync/scripts/`。
# 为什么用派生器而不是手抄：与上一代同一句理由（手抄 6 只 = 给"逐字派生把上一代恰好没踩到的缺陷一起派生过来"那一族开门）。
# 写盘次序继承上一代：**先在内存里跑完全部替换与全部裁决，一只都不落盘；全绿了才一次写 6 只**。
#
# 本代相对上一代表（derive_r61b.py）的三处变化，逐一点名：
#   ① 自己的代号从 `r61` 变成 `r61b`，于是**替换源与替换目标第一次互为子串**：
#      `r61b` 含 `r61` ⇒ 上一代那种"A 之后再 E"的线性表在本代会把 `r61c` 洗成 `r61bc`、
#      把注释里的"派生自 sync_r61.py"和"自己的名字"混成一团。修法 = **占位符三步**：
#      先把本代名字整体摘下来换成哨兵串，再换上一代名字，最后把哨兵装成本代名字。
#      哨兵串在 6 只源里必须一只都不存在（下面 ASSERT 钉），否则三步不成立。
#   ② 上一代派生报告登记过的欠账：`r61b_roundtrip.py` 那行标签 `R61_ROUNDTRIP_AT` 是大写形态，
#      上一代的替换表只列小写 ⇒ 它一路顶着"第 14 代"的名字打了三代载体。本代表加一条 F：`R61` -> `R61C`，
#      并把大写形态纳入反度量（OLD_TOKENS 里加 `R61`，代码行命中即 ABORT）。
#   ③ 反度量的口径随①改：上一代"上一代名字只许出现在注释行"，本代同一句要**分开钉两种**——
#      哨兵串在裁决前必须 0 命中（防"源里本来就有 @@ 串"），`r61b`/`R61` 只许在注释行。
# 替换表（顺序即语义）：
#   A. `r61b` -> `<PH>`（把本代名字摘走）
#   E. `r61`  -> `r61b`（上一代名字：目录 `r61_sync`、6 只源脚本名、注释里的 `r61final` / 裸 `r61`）
#   A2. `<PH>` -> `r61c`（装回本代名字）
#   B. `zsynctest17` -> `zsynctest18`，**再** `zsynctest16` -> `zsynctest17`（降序，否则级联把
#      注释里"上一代根 16 -> 本代根 17"洗成"18 -> 18"。每代一个新解包根，绝不复用、绝不删旧的）
#   C. `第 15 代` -> `第 16 代`，**再** `第 14 代` -> `第 15 代`（降序）**以及** `gen-15` -> `gen-16`
#      （`chk_*.ps1` 头一行用的是 `gen-15 版`）。**`gen 24`（归档 SEAL）与 `gen 13` 是历史事实，一条都不许动**，
#      所以这里只列字面串，不做 `gen[ -]?\d+` 那种正则批量替换。
#   F. `R61` -> `R61C`（②那笔欠账）
import ast
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SRC_DIR = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
DST_DIR = os.path.join(REPO, 'hardware', 'r61c_sync', 'scripts')
EV_DIR = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
FILES = ['sync_r61b.py', 'r61b_upload.ps1', 'chk_r61b.ps1',
         'r61b_listdiff.py', 'r61b_cutoff_delta.py', 'r61b_roundtrip.py']
PH = '<R61C-SENTINEL>'

# 上一代才有的名字：只许出现在**注释行**（那是"派生自谁"的正文），落在代码行 = 漏换。
# 大写 `R61` 是②里点名的那只标签，本代起也纳入反度量 —— 但它**必须带负向断言** `R61(?!C)`：
# F 换出来的正面读数 `R61C_ROUNDTRIP_AT` 本身就以 `R61` 开头，用裸子串钉会让"修好的那一行"永远被判成余留。
OLD_TOKENS = [('r61b', r'r61b'), ('R61', r'R61(?!C)'),
              ('zsynctest16', r'zsynctest16'), ('zizhao_20260926_r61bfinal', r'zizhao_20260926_r61bfinal'),
              ('r61bfinal', r'r61bfinal'), ('zsynctest17', r'zsynctest17'),
              ('gen-15', r'gen-15'), ('第 15 代', r'第 15 代'), ('第 14 代', r'第 14 代')]


def is_comment(line):
    return line.lstrip().startswith('#')


def transform(t):
    assert PH not in t, 'ABORT: 源里已存在哨兵串 ' + PH
    t = t.replace('r61b', PH)                                                  # A
    t = t.replace('r61', 'r61b')                                               # E
    t = t.replace(PH, 'r61c')                                                  # A2
    t = t.replace('zsynctest17', 'zsynctest18').replace('zsynctest16', 'zsynctest17')   # B（降序）
    t = (t.replace('第 15 代', '第 16 代').replace('第 14 代', '第 15 代')
         .replace('gen-15', 'gen-16'))                                         # C
    t = t.replace('R61', 'R61C')                                               # F
    assert PH not in t, 'ABORT: 哨兵串没被装回本代名字，残留在产物里'
    return t


# ---------- 第一遍：只算、只裁决，不落盘 ----------
pending, report, bodies = [], [], {}
for fn in FILES:
    srcp = os.path.join(SRC_DIR, fn)
    assert os.path.isfile(srcp), 'ABORT: 派生源不存在 ' + srcp
    src_b = open(srcp, 'rb').read()
    src_txt = src_b.decode('utf-8')
    n_src = len(src_txt.splitlines())
    out = transform(src_txt)
    dst = os.path.join(DST_DIR, fn.replace('r61b', 'r61c'))
    assert not os.path.exists(dst), 'ABORT: 派生件已存在，不覆盖 ' + dst
    assert not any(d == dst for d, _ in pending), 'ABORT: 表里有两只映射到同一个目标名 ' + dst
    payload = out.encode('utf-8')
    # 字节日程原样继承：BOM（含中文 .ps1 吞行那一族）与行尾（CR 只数）都不许被这次写盘改动
    assert payload[:3] == src_b[:3], 'ABORT: BOM 未原样继承 ' + dst
    assert payload.count(b'\r') == src_b.count(b'\r'), 'ABORT: 行尾未原样继承 ' + dst
    if dst.endswith('.py'):
        ast.parse(out)                   # 仓库内不用 py_compile（它会落 .pyc = 检查动作污染被检查物）
    n_dst = len(out.splitlines())
    strays = {k: [i + 1 for i, l in enumerate(out.splitlines())
                  if re.search(p, l) and not is_comment(l)] for k, p in OLD_TOKENS}
    strays = {k: v for k, v in strays.items() if v}
    # `hard` = 换完应该**整只消失**的串（不分注释/代码）。这里刻意不放 `r61bfinal`：
    # E 会把源注释里那句"换代 r61final -> r61bfinal"里的上一代名字写成 `r61bfinal`，那是**正确的正文**，
    # 要求它为 0 就是拿上一代那把尺直接套本代（上一代在哨兵下限 50 行上正是这样误判了最小的那只）。
    hard = {k: out.count(k) for k in ('zsynctest16', 'gen-15', PH)}
    hits = {
        'r61c': out.count('r61c'),
        'zsynctest18': out.count('zsynctest18'),
        '第 16 代': out.count('第 16 代'),
        '第 15 代': out.count('第 15 代'),
        'gen-16': out.count('gen-16'),
        'R61C': out.count('R61C'),
        'r61b_sync/scripts': out.count('r61b_sync/scripts') + out.count(r'r61b_sync\scripts'),
        # 守卫字面量有两种形态：py 里 'ht305_sync'，ps1 里 '*ht305_sync*'（-like 通配）—— 上一代就栽在只数一种
        '守卫 ht305_sync 出现次数': out.count('ht305_sync'),
        '余留 ht305_sync/scripts': out.count('ht305_sync/scripts') + out.count(r'ht305_sync\scripts'),
    }
    report.append('%s -> %s | src_lines=%d dst_lines=%d | md5_src=%s md5_dst=%s | LEFT=%s | %s' % (
        fn, os.path.basename(dst), n_src, n_dst,
        hashlib.md5(src_b).hexdigest()[:8], hashlib.md5(payload).hexdigest()[:8],
        hard, hits))
    assert not strays, 'ABORT: 上一代名字残留在代码行 %s：%s' % (dst, strays)
    assert hard['zsynctest16'] == 0 and hard['gen-15'] == 0 and hard[PH] == 0, \
        'ABORT: 派生余留 %s' % (hard,)
    # 哨兵分两半：**等长**才是"派生没掉行"的判据；下限只用来挡"源读空了还全绿"（(63) 那一族）。
    assert n_dst == n_src, 'ABORT: 行数变了（本脚本只替换字面量，不该增删行）%s %d/%d' % (dst, n_src, n_dst)
    assert n_src >= 40, 'ABORT: 源行数 %d 低于哨兵下限 40（源可能被读空）%s' % (n_src, srcp)
    assert hits['守卫 ht305_sync 出现次数'] >= 1, 'ABORT: 派生件丢了封存归档目录守卫 ' + dst
    assert hits['余留 ht305_sync/scripts'] == 0, 'ABORT: 出处指针仍指进封存归档目录的 scripts/ ' + dst
    # 本代代次有两种写法（五只"第 N 代" + chk_*.ps1 的"gen-N 版"）；解包根只在真用它的那几只里 —— 两条都是
    # 上一代"尺只量到一种形态 / 覆盖面与被检物口径不一致"那两起假 ABORT 的执行者，本遍不再重犯。
    assert hits['第 16 代'] + hits['gen-16'] >= 1, 'ABORT: 派生件里没有本代代次（第 16 代 / gen-16 都没有）' + dst
    if 'zsynctest' in src_txt:
        assert hits['zsynctest18'] >= 1, 'ABORT: 派生件里没有本代解包根 ' + dst
    if 'R61' in src_txt:
        assert hits['R61C'] >= 1, 'ABORT: 源里有大写 R61 标签而派生件没换成 R61C ' + dst
    bodies[dst] = out
    pending.append((dst, payload))

# ---------- 假指针执行者（仍不落盘）：派生件里每条 hardware/r61*_sync/scripts/<file> 都要能取到 ----------
# 只裁决 **scripts/** 那一路：evidence 那一路是本代**待写**的载体（chk_*.ps1 对它的守卫正好反向 = "已存在即 ABORT"），
# 在那里要求存在会把自己拦死，所以 evidence 只报状态不裁决。
PTR = re.compile(r'hardware[/\\]r61(?:b|c)?_sync[/\\]scripts[/\\][A-Za-z0-9_.\-]+')
PTRA = re.compile(r'hardware[/\\]r61(?:b|c)?_sync[/\\]evidence[/\\][A-Za-z0-9_.\-]+')
will_write = set(os.path.normpath(d) for d, _ in pending)
ptr_lines, ev_lines, bad = [], [], []
for dst, _ in pending:
    txt = bodies[dst]
    for m in sorted(set(PTR.findall(txt))):
        p = os.path.normpath(os.path.join(REPO, m.replace('\\', '/')))
        ok = (os.path.isfile(p) or os.path.isdir(p) or os.path.normpath(p) in will_write)
        ptr_lines.append('%s  %s  %s' % (os.path.basename(dst), m.replace('\\', '/'),
                                         'OK' if ok else 'MISSING'))
        if not ok:
            bad.append(p)
    for m in sorted(set(PTRA.findall(txt))):
        p = os.path.normpath(os.path.join(REPO, m.replace('\\', '/')))
        ev_lines.append('%s  %s  %s' % (os.path.basename(dst), m.replace('\\', '/'),
                                        'ALREADY-ON-DISK' if os.path.exists(p) else 'not-yet(=本代待写)'))
assert not bad, 'ABORT: %d 条假指针，盘上取不到：%s' % (len(bad), bad)
assert ptr_lines, 'ABORT: 派生件里一条 scripts/ 指针都没扫到 ⇒ 这把反度量本身在漏，不能当"指针都对"用'

# ---------- 第二遍：全绿了才写 ----------
os.makedirs(DST_DIR, exist_ok=True)
os.makedirs(EV_DIR, exist_ok=True)
for dst, payload in pending:
    assert not os.path.exists(dst), 'ABORT: 裁决与写盘之间冒出了同名件，不覆盖 ' + dst
    with open(dst, 'wb') as f:
        f.write(payload)
    back = open(dst, 'rb').read()
    assert back == payload, 'ABORT: 回读不等于写入 ' + dst
    assert hashlib.md5(back).hexdigest() == hashlib.md5(payload).hexdigest()

print('\n'.join(report))
print('\n'.join(ptr_lines))
print('\n'.join(ev_lines))
print('WROTE=%d DIR=%s EV_DIR=%s' % (len(pending), DST_DIR, EV_DIR))
print('POINTERS_SCRIPTS=%d MISSING=%d | EVIDENCE_POINTERS_REPORTED=%d' % (
    len(ptr_lines), len(bad), len(ev_lines)))
print('VERDICT=DERIVED rc=0')
