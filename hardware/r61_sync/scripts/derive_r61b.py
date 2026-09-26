# 第 15 代（r61b 代）同步件派生器：把 `hardware/r61_sync/scripts/` 那 6 只**逐字**搬成 `hardware/r61b_sync/scripts/`。
# 为什么用派生器而不是手抄：手抄 6 只脚本 = 给"逐字派生把上一代恰好没踩到的缺陷一起派生过来"那一族开门；
# 派生器把**所有**改动做成一张可审计的替换表，跑完还能反过来量：每只打印一行"源/派生行数 + 两侧 md5 + 上一代名字余留 + 各条替换命中数"，
# 最后另起一段把派生件里所有 hardware/r61*_sync/scripts/ 指针逐条对盘（见文末 PTR）。
# 写盘次序：**先在内存里跑完全部替换与全部裁决，一只都不落盘；全绿了才一次写 6 只**。
#   动因：本脚本前两遍都在"写到第 2 只时断言失败"停下 —— 那两遍各留下一只已落盘的半成品，
#   清掉它得靠删文件（用户的红线：不轻易删）。裁决前置之后，失败 = 盘上零变化，删无可删。
# 替换表（**顺序即语义**；先把 6 只源里所有要换的样式现读一遍再定，见下面 REPORT 的反度量）：
#   A. `r61` → `r61b`（一次过：包名 / 载体名 / 兄弟脚本名 / 目录名 r61_sync→r61b_sync / TEMP 副本名）
#   B. `zsynctest16` → `zsynctest17`，**再** `zsynctest15` → `zsynctest16`（降序做，否则级联把注释里的
#      "上一代根 15 → 本代根 16" 洗成 "17 → 17"。每代一个新解包根，绝不复用、绝不删旧的）
#   C. `第 14 代` → `第 15 代` → `第 13 代` → `第 14 代`（同降序）**以及** `gen-14` → `gen-15`：
#      chk_*.ps1 头一行用的是 `gen-14 版` 这种写法，只换"第 N 代"会漏一处本代代次；
#      **`gen 24`（归档 SEAL）与 `gen 13`（"取证自 gen 13 起进仓库"、"gen 13 那遍 255 的教训"）是历史事实，
#      一条都不许动** —— 所以这里只列字面 `gen-14`，不做 `gen[ -]?\d+` 那种正则批量替换。
#   D. 出处指针目录：`hardware/ht305_sync/scripts/` → `hardware/r61_sync/scripts/`
#      （本版派生源是第 14 代那 6 只，它们住在 r61_sync/scripts，不在封存归档目录里）
#   E. 余下所有 `r55` 字样 → `r61`（在 A 之后 ⇒ 注释里的"换代 r55 -> r61"正好变成"r61 -> r61b"；
#      在 D 之后 ⇒ 指针名 `sync_r55.py` / `chk_r55.ps1` 变成盘上真存在的 `sync_r61.py` / `chk_r61.ps1`）
#      **这一步就是"假指针"那一族的执行者**：凡替换表里漏一处，下面 PTR_EXISTS 那条就会指着一条盘上没有的路径停下。
import ast
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SRC_DIR = os.path.join(REPO, 'hardware', 'r61_sync', 'scripts')
DST_DIR = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
EV_DIR = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
FILES = ['sync_r61.py', 'r61_upload.ps1', 'chk_r61.ps1',
         'r61_listdiff.py', 'r61_cutoff_delta.py', 'r61_roundtrip.py']

# 上一代才有的名字：只许出现在**注释行**（那是"派生自谁"的正文），落在代码行 = 漏换。
OLD_TOKENS = ['r55', 'zsynctest15', 'zizhao_20260926_r61final',
              'r61final', 'zsynctest16', 'gen-14', '第 14 代', '第 13 代']


def is_comment(line):
    return line.lstrip().startswith('#')


def transform(t):
    t = t.replace('r61', 'r61b')                                                        # A
    t = t.replace('zsynctest16', 'zsynctest17').replace('zsynctest15', 'zsynctest16')   # B（降序）
    t = (t.replace('第 14 代', '第 15 代').replace('第 13 代', '第 14 代')
         .replace('gen-14', 'gen-15'))                                                  # C
    t = t.replace('hardware/ht305_sync/scripts/', 'hardware/r61_sync/scripts/')         # D
    t = t.replace('r55', 'r61')                                                         # E
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
    dst = os.path.join(DST_DIR, fn.replace('r61', 'r61b'))
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
                  if k in l and not is_comment(l)] for k in OLD_TOKENS}
    strays = {k: v for k, v in strays.items() if v}
    hard = {k: out.count(k) for k in ('r55', 'zsynctest15', 'zizhao_20260926_r61final')}
    hits = {
        'r61b': out.count('r61b'),
        'zsynctest17': out.count('zsynctest17'),
        '第 15 代': out.count('第 15 代'),
        '第 14 代': out.count('第 14 代'),
        'gen-15': out.count('gen-15'),
        'r61_sync/scripts': out.count('r61_sync/scripts') + out.count(r'r61_sync\scripts'),
        # 守卫字面量有两种形态：py 里 'ht305_sync'，ps1 里 '*ht305_sync*'（-like 通配）。
        # 本仓库第一遍就是按单引号那种数，两只 .ps1 一起 ABORT —— 断言没错，错的是尺只量到一种形态。
        '守卫 ht305_sync 出现次数': out.count('ht305_sync'),
        'D 余留 ht305_sync/scripts': out.count('ht305_sync/scripts') + out.count(r'ht305_sync\scripts'),
    }
    report.append('%s -> %s | src_lines=%d dst_lines=%d | md5_src=%s md5_dst=%s | LEFT=%s | %s' % (
        fn, os.path.basename(dst), n_src, n_dst,
        hashlib.md5(src_b).hexdigest()[:8], hashlib.md5(payload).hexdigest()[:8],
        hard, hits))
    assert not strays, 'ABORT: 上一代名字残留在代码行 %s：%s' % (dst, strays)
    assert hard['r55'] == 0 and hard['zsynctest15'] == 0 and hard['zizhao_20260926_r61final'] == 0, \
        'ABORT: 派生余留 %s' % (hard,)
    # 哨兵分两半：**等长**才是"派生没掉行"的判据；下限只用来挡"源读空了还全绿"（(63) 那一族）。
    # 上一遍这里写死 50（那是 chk_*.ps1 给它自己的被检件 r61_upload.ps1=109 行定的口径），
    # 套到 6 只上就把最小的那只（chk_r61.ps1，现读 44 行）误判成缺陷 —— 一把从别处搬来的尺必须先在本代量一遍。
    assert n_dst == n_src, 'ABORT: 行数变了（本脚本只替换字面量，不该增删行）%s %d/%d' % (dst, n_src, n_dst)
    assert n_src >= 40, 'ABORT: 源行数 %d 低于哨兵下限 40（源可能被读空）%s' % (n_src, srcp)
    assert hits['守卫 ht305_sync 出现次数'] >= 1, 'ABORT: 派生件丢了封存归档目录守卫 ' + dst
    assert hits['D 余留 ht305_sync/scripts'] == 0, 'ABORT: 出处指针仍指进封存归档目录的 scripts/ ' + dst
    # "本代代次"也有**两种写法**：五只用"第 N 代"，chk_*.ps1 那只用"gen-N 版"。
    # 上一遍只数"第 15 代"，于是 chk_r61b.ps1 被误判成缺本代代次（它的 gen-15 就在第二行）—— 同一种"尺只量到一种形态"，第三遍又犯在另一只身上。
    assert hits['第 15 代'] + hits['gen-15'] >= 1, 'ABORT: 派生件里没有本代代次（第 15 代 / gen-15 都没有）' + dst
    # 解包根只存在于"上传/往返"那几只里（sync_*.py 根本不管远端目录）：
    # 断言的覆盖面必须与被检物口径一致，否则是**我的尺**错，不是那只漏了 —— 第二遍就在 sync_r61b.py 上误 ABORT。
    if 'zsynctest' in src_txt:
        assert hits['zsynctest17'] >= 1, 'ABORT: 派生件里没有本代解包根 ' + dst
    bodies[dst] = out
    pending.append((dst, payload))

# ---------- 假指针执行者（仍不落盘）：派生件里每条 hardware/r61*_sync/scripts/<file> 都要能取到 ----------
# 只裁决 **scripts/** 那一路：evidence 那一路是本代**待写**的载体（chk_*.ps1 对它的守卫正好反向 = "已存在即 ABORT"），
# 在那里要求存在会把自己拦死，所以 evidence 只报状态不裁决。
PTR = re.compile(r'hardware[/\\]r61b?_sync[/\\]scripts[/\\][A-Za-z0-9_.\-]+')
PTRA = re.compile(r'hardware[/\\]r61b?_sync[/\\]evidence[/\\][A-Za-z0-9_.\-]+')
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
