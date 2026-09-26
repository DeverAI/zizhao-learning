# 修复遍：把 r61close 那两根里**平铺在根顶层**的 32 只源码搬进各自的 `main/` 子目录（产物 3 只留在顶层，与 r59_post 那根的布局一致）。
# 缺陷成因（本遍登记进 FreqErr 的）：创建者用 `os.path.relpath(f, MAIN)` 当目标相对路径 ⇒ 相对于 `MAIN` 的路径**天然不含 `main/` 前缀**
#   ⇒ 32 只源码全落根顶层。能抓到它的那道 `diff -rq ROOT/main 工作树/main` 排在写盘之后，所以根先落地、复核才崩。
# 本遍只做**可逆的搬移**：不删、不覆写（目标 `main/` 若已存在即 ABORT），每只搬完立刻按 md5 回读核对。
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
ARTS = ['zizhao_esp32s3.bin', 'zizhao_esp32s3.elf', 'zizhao_esp32s3.map']
PARS = [os.path.join(REPO, 'backups'), os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups')]
# 根名**不许硬编码**（本仓库登记过的口径）：按前缀现扫，必须两根各扫到恰好一只且同名。
_found = [[x for x in os.listdir(p) if x.startswith('r61close_')] for p in PARS]
assert all(len(f) == 1 for f in _found), 'ABORT: r61close_* 根不是"两根各一只"：%s' % _found
assert _found[0] == _found[1], 'ABORT: A/B 两根不同名：%s' % _found
NAME = _found[0][0]
ROOTS = [os.path.join(p, NAME) for p in PARS]
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
SEAL = 'ht305_sync'
md5 = lambda p: hashlib.md5(io.open(p, 'rb').read()).hexdigest()  # noqa: E731

want = sorted(os.listdir(MAIN))
assert all(os.path.isfile(os.path.join(MAIN, x)) for x in want), 'ABORT: 工作树 main/ 顶层有子目录，搬移布局要重算'

for ROOT in ROOTS:
    assert SEAL not in ROOT.replace('\\', '/'), 'ABORT: 路径碰了封存归档 ' + ROOT
    top = sorted(os.listdir(ROOT))
    mdir = os.path.join(ROOT, 'main')
    assert not os.path.exists(mdir), 'ABORT: %s 已有 main/ ⇒ 本修复遍已经跑过，不叠加' % ROOT
    src = [x for x in top if x not in ARTS]
    assert sorted(src) == want, 'ABORT: %s 顶层待搬名单与工作树 main/ 不同（%d vs %d）' % (ROOT, len(src), len(want))
    assert set(ARTS) <= set(top), 'ABORT: %s 顶层少了构建产物' % ROOT
    before = {x: md5(os.path.join(ROOT, x)) for x in src}
    os.mkdir(mdir)
    for x in src:
        shutil.move(os.path.join(ROOT, x), os.path.join(mdir, x))
    after = {x: md5(os.path.join(mdir, x)) for x in src}
    assert before == after, 'ABORT: %s 搬移后有文件 md5 变了' % ROOT
    assert sorted(os.listdir(mdir)) == want, 'ABORT: %s 搬完 main/ 名单不等于工作树' % ROOT
    print('FIXED %s/main/ = %d 只（顶层余 %d 只 = 3 只产物）搬前后 md5 逐只全等' % (
        ROOT.replace(REPO, '%REPO%'), len(want), len(os.listdir(ROOT))))

# 搬完立刻用创建者本该跑的那把尺复核一遍（这次是**只读**）
import subprocess  # noqa: E402

for ROOT in ROOTS:
    r = subprocess.run(['diff', '-rq', os.path.join(ROOT, 'main'), MAIN],
                       capture_output=True, text=True, encoding='utf-8')
    d = [l for l in r.stdout.splitlines() if l.strip()]
    print('DIFF_RQ %s%s/main vs 工作树 main = %d 行' % (ROOT.replace(REPO, '%REPO%'), os.sep, len(d)))
    assert not d, 'ABORT: 搬完仍与工作树不等：%s' % d[:3]
    assert md5(os.path.join(ROOT, ARTS[0])) == '42b6b16fbb34505d083bd9dd0d3f33cb', 'ABORT: 根内 bin 不是板上那只'
print('VERDICT=ROOT_LAYOUT_FIXED rc=0')
