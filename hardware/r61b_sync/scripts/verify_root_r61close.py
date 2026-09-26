# 复核遍：对**已经落盘**的那一对根（`r61close_20260926_133908`）现跑创建者本该打印、却因 NameError 没落盘的全部关系式。
# 为什么不在创建者里补跑：它的名字带秒级时间戳 ⇒ 重跑 = 多造一对根（幂等门挡不住，那条门是崩了之后才补的）。
# 本遍只做只读复核：不写根、不改根、不删任何东西，只往 `hardware/r61b_sync/evidence/` 落一只取证件。
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
BUILD = r'C:/esp/zproj/build'
ARTS = ['zizhao_esp32s3.bin', 'zizhao_esp32s3.elf', 'zizhao_esp32s3.map']
# 根名按前缀现扫（不硬编码：硬编码的输入文件名是本仓库登记过的缺陷口径）
_PARS = [os.path.join(REPO, 'backups'), os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups')]
_found = [[x for x in os.listdir(p) if x.startswith('r61close_')] for p in _PARS]
assert all(len(f) == 1 for f in _found), 'ABORT: r61close_* 根不是"两根各一只"：%s' % _found
assert _found[0] == _found[1], 'ABORT: A/B 两根不同名：%s' % _found
NAME = _found[0][0]
A = os.path.join(_PARS[0], NAME)
B = os.path.join(_PARS[1], NAME)
SEAL = 'ht305_sync'
for p in (A, B):
    assert SEAL not in p.replace('\\', '/'), 'ABORT: 路径碰了封存归档 ' + p
    assert os.path.isdir(p), 'ABORT: 根不存在 ' + p


def _md5(p):
    return hashlib.md5(io.open(p, 'rb').read()).hexdigest()


def _tree(root):
    out = {}
    for r, _d, fs in os.walk(root):
        for x in fs:
            f = os.path.join(r, x)
            out[os.path.relpath(f, root).replace('\\', '/')] = (os.path.getsize(f), _md5(f))
    return out


# ---------- 两根自身：名单/只数/字节/md5 ----------
ta, tb = _tree(os.path.join(A, 'main')), _tree(os.path.join(B, 'main'))
aa, ab = _tree(A), _tree(B)
assert set(ta) == set(tb), 'ABORT: A/B 两根 main/ 名单不同（%d vs %d）' % (len(ta), len(tb))
assert all(ta[k] == tb[k] for k in ta), 'ABORT: A/B 两根有 main/ 文件 md5 不等'
assert set(aa) == set(ab), 'ABORT: 两根全根名单不同（%d vs %d）' % (len(aa), len(ab))
_bad = sorted(k for k in aa if aa[k] != ab[k])
assert not _bad, 'ABORT: 两根全根口径有 %d 只不等：%s' % (len(_bad), _bad[:5])
NF = len(aa)
BYTES = sum(v[0] for v in aa.values())
assert len(ab) == NF, 'ABORT: 两根只数不等（A=%d B=%d）' % (NF, len(ab))
MAIN_N = len(ta)
assert MAIN_N == 32, 'ABORT: 根内 main/ 只数不是 32（工作树口径变了，本节读数不能沿用）：%d' % MAIN_N
assert NF == MAIN_N + len(ARTS), 'ABORT: 全根只数 %d != main/ %d + 产物 %d' % (NF, MAIN_N, len(ARTS))

# ---------- 关系式：根内 main/ == 当前工作树 main/ ----------
def _diffcnt(root_main):
    r = subprocess.run(['diff', '-rq', root_main, MAIN], capture_output=True, text=True, encoding='utf-8')
    return [l for l in r.stdout.splitlines() if l.strip()]


da, db = _diffcnt(os.path.join(A, 'main')), _diffcnt(os.path.join(B, 'main'))
assert not da and not db, 'ABORT: 新根 main/ 与工作树不等（A %d 行 / B %d 行）：%s' % (
    len(da), len(db), (da + db)[:3])

# ---------- 身份式：根里那只 bin 仍是 §38.32 登记的"板上 == 待烧"那只 ----------
ba, bb = os.path.join(A, ARTS[0]), os.path.join(B, ARTS[0])
build_bin = os.path.join(BUILD, ARTS[0])
ma, mb, mc = _md5(ba), _md5(bb), _md5(build_bin)
assert ma == mb == mc == '42b6b16fbb34505d083bd9dd0d3f33cb', \
    'ABORT: 三只 bin 的 md5 不是同一个 42b6b16f…（根A %s / 根B %s / 构建目录 %s）⇒ 归档与"此刻板上"脱钩了' % (ma, mb, mc)
sz = os.path.getsize(ba)
assert sz == 1108336, 'ABORT: 根内 bin 尺寸 %d 与 §38.32 的 1,108,336 不等' % sz
b176 = io.open(ba, 'rb').read()[176:184].hex()
assert b176 == 'a23c5df6b46f8293', 'ABORT: 根内 bin[176:184]=%s != §38.32 那 16 位' % b176
elf16 = io.open(ba, 'rb').read()[176:208].hex()
sha_full = hashlib.sha256(io.open(os.path.join(A, ARTS[1]), 'rb').read()).hexdigest()
assert elf16 == sha_full, 'ABORT: bin[176:208] != sha256(elf) 全等式（§38.30 那把尺今天不复现）'

# ---------- 与旧根的口径差（不覆写不删除，只点名） ----------
OLD = os.path.join(REPO, 'backups', 'r59_post_20260925_184900')
old_bin = _md5(os.path.join(OLD, ARTS[0]))
assert old_bin != ma, 'ABORT: 旧根那只 bin 与新根同值 ⇒ "新根才有板上镜像"这句前提没了'

print('ROOT_NAME %s' % NAME)
print('A = backups/%s   B = hardware/zizhao-esp32s3/backups/%s' % (NAME, NAME))
print('FILES_PER_ROOT=%d (main/ %d 只 + 产物 %d 只)  BYTES_PER_ROOT=%d' % (NF, MAIN_N, len(ARTS), BYTES))
print('A_vs_B: 名单相同=OK  逐只 md5 全等=OK（含 3 只产物，共 %d 只）' % NF)
print('DIFF_RQ_A_vs_worktree=%d 行  DIFF_RQ_B_vs_worktree=%d 行' % (len(da), len(db)))
print('BIN md5=%s / %d B / bin[176:184]=%s / bin[176:208]==sha256(elf) 成立' % (ma, sz, b176))
print('OLD r59_post bin md5=%s（不同值 ⇒ 板上那只镜像此前盘上无副本，本遍起有了）' % old_bin)
print('VERDICT=ROOT_VERIFIED rc=0')
