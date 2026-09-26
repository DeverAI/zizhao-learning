# 新备份根一对（r61close 代）：把**此刻板子上在跑的那只镜像**的构建输入 + 产物一起归档。
# 为什么要新建（历代 README 判据给的，不是"到点了就建一根"）：
#   ①现行待烧 == 板上 == **md5** `42b6b16f…`（1,108,336 B，见 §38.32 的身份等式），
#   而盘上最近一只**带产物的全根**（`r59_post_20260925_184900`）里那只 bin 是 `714b9b84…` ⇒
#   **此刻板上跑的镜像在仓库外没有任何一只字节副本**（构建目录 `C:\esp\zproj\build\` 会被下一次构建覆盖）；
#   ②R61 那两"根"（`r61_pre_.../main` 4 只、`r61b_.../eink_display.c` 1 只）是**改前单只快照**，不是全根，量不出"回滚到此刻"。
# 三条硬规矩：①目标目录**必须不存在**（存在即 ABORT，绝不覆写既有根）；②逐只字节回读相等才算拷成；
# ③两根（A=仓库外 `backups/`、B=项目内 `hardware/zizhao-esp32s3/backups/`）必须**只数/字节/md5 全等**，
#   否则"双根互为备份"这句就是空的。封界：解析出的路径含 `ht305_sync` 即停。
import hashlib
import io
import os
import shutil
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
BUILD = r'C:/esp/zproj/build'
ARTS = ['zizhao_esp32s3.bin', 'zizhao_esp32s3.elf', 'zizhao_esp32s3.map']
NAME = 'r61close_' + datetime.now().strftime('%Y%m%d_%H%M%S')
ROOT_A = os.path.join(REPO, 'backups', NAME)
ROOT_B = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups', NAME)
SEAL = 'ht305_sync'

# ---------- 裁决排在写盘之前 ----------
for p in (ROOT_A, ROOT_B):
    assert SEAL not in p.replace('\\', '/'), 'ABORT: 目标路径碰了封存归档 ' + p
    assert not os.path.exists(p), 'ABORT: 目标根已存在，绝不覆写 ' + p
# ⚠ 这道幂等门是**首跑崩了之后补装的**（本文件第一次跑到"写盘之后"的关系式复核时 NameError，
#   两根其实已经落盘）：原名带秒级时间戳 ⇒ "目标不存在"永真 ⇒ **重跑一遍就多一对根**，
#   这一条按名字查的闸门根本挡不住重跑。改成按**前缀**扫：同代已有任何 r61close_* 即停。
_pref = [os.path.join(_par, x) for _par in (os.path.dirname(ROOT_A), os.path.dirname(ROOT_B))
         for x in os.listdir(_par) if x.startswith('r61close_')]
assert not _pref, 'ABORT: 同代根已存在 %d 只（重跑会多造一对，本脚本按前缀拒绝）：%s' % (
    len(_pref), [os.path.basename(x) for x in _pref])
assert os.path.isdir(MAIN), 'ABORT: 读不到工作树 main/'
_srcs = []
for r, _d, fs in os.walk(MAIN):
    for x in sorted(fs):
        f = os.path.join(r, x)
        if '__pycache__' in f or x.endswith('.pyc'):
            continue
        _srcs.append(f)
_srcs.sort()
# 正向钉：只数必须落在已知区间内。**只写"A 与 B 对称差为空"是不够的**——两边同时为空时那种等式恒真
# （首跑平铺缺陷就是这样从 `set(ta)==set(tb)` 底下滑过去的）。
assert 30 <= len(_srcs) <= 40, 'ABORT: 工作树 main/ 只数 %d 不在已知区间 [30,40] ⇒ 本脚本的口径前提变了' % len(_srcs)
_bins = [f for f in _srcs if f.endswith(('.bin', '.elf', '.map'))]
assert not _bins, 'ABORT: 工作树 main/ 里冒出了二进制：%s' % _bins
arts = [os.path.join(BUILD, a) for a in ARTS]
for a in arts:
    assert os.path.isfile(a), 'ABORT: 构建产物缺失 ' + a
_md5 = lambda p: hashlib.md5(io.open(p, 'rb').read()).hexdigest()  # noqa: E731
bin_md5, bin_sz = _md5(arts[0]), os.path.getsize(arts[0])
assert bin_md5 == '42b6b16fbb34505d083bd9dd0d3f33cb' and bin_sz == 1108336, \
    'ABORT: 构建目录那只 bin 已不是 §38.32 登记的板上那只（%s / %d B）⇒ 本根不再是"板上镜像的输入"' % (bin_md5, bin_sz)
b176 = io.open(arts[0], 'rb').read()[176:184].hex()
assert b176 == 'a23c5df6b46f8293', 'ABORT: bin[176:184] 与 §38.32 那 16 位不等（%s）' % b176

# ---------- 落盘：两根各拷一遍，逐只回读 ----------
# ⚠ 这一行的 `'main'` 前缀是**首跑之后补的**：原来写的是裸 `os.path.relpath(f, MAIN)`，
#   相对 `MAIN` 的路径天然不含 `main/` ⇒ 32 只源码全平铺到根顶层（能抓到它的 `diff -rq` 排在写盘之后）。
plan = [(f, os.path.join('main', os.path.relpath(f, MAIN))) for f in _srcs] \
       + [(a, os.path.basename(a)) for a in arts]
report = []
for ROOT in (ROOT_A, ROOT_B):
    n = b = 0
    for src, rel in plan:
        dst = os.path.join(ROOT, *rel.split(os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        sb, db = io.open(src, 'rb').read(), io.open(dst, 'rb').read()
        assert sb == db, 'ABORT: 逐字节回读不等 %s' % rel
        n += 1
        b += len(db)
    report.append((ROOT, n, b))
(A, na, ba), (B, nb, bb) = report
assert (na, ba) == (nb, bb) == (len(plan), sum(os.path.getsize(s) for s, _ in plan)), 'ABORT: 两根只数/字节不等'
_mismatch = []
for _s, rel in plan:
    pa = os.path.join(A, *rel.split(os.sep))
    pb = os.path.join(B, *rel.split(os.sep))
    if _md5(pa) != _md5(pb):
        _mismatch.append(rel)
assert not _mismatch, 'ABORT: A/B 两根有 %d 只 md5 不等：%s' % (len(_mismatch), _mismatch)

# ---------- 关系式复核：新根必须是"当前工作树的镜像" ----------
def _diffcnt(root_main):
    # 走 subprocess 的参数数组而不拼 shell 命令：本仓库路径含中文，`os.popen` 那一趟要过 cmd 的代码页。
    r = subprocess.run(['diff', '-rq', root_main, MAIN], capture_output=True, text=True, encoding='utf-8')
    return len([l for l in r.stdout.splitlines() if l.strip()])


da = _diffcnt(os.path.join(A, 'main'))
db = _diffcnt(os.path.join(B, 'main'))
assert (da, db) == (0, 0), 'ABORT: 新根 main/ 与工作树不等（A=%d 行 / B=%d 行）⇒ 这根不能当回滚源' % (da, db)

print('ROOT  A=%s' % A.replace(REPO, '%REPO%'))
print('ROOT  B=%s' % B.replace(REPO, '%REPO%'))
print('FILES_PER_ROOT=%d (main/ %d 只 + 产物 %d 只)  BYTES=%d' % (len(plan), len(_srcs), len(arts), ba))
print('A_vs_B: files %d/%d bytes %d/%d md5_mismatch=0' % (na, nb, ba, bb))
print('DIFF_RQ_NEWROOT_A_vs_worktree=%d行  B=%d行' % (da, db))
print('BIN md5=%s / %d B / bin[176:184]=%s（== §38.32 板上那 16 位）' % (bin_md5, bin_sz, b176))
print('OLD_FULL_ROOT r59_post bin md5=714b9b84ce05b27f1a665c0fb75ee46a（本根之后它是历史输入，不覆写不删除）')
print('VERDICT=ROOT_MADE rc=0')
