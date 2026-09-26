# 补遍（第十一次读数的**载体行**）：上一遍的落地器把 ①~⑪ 写进了 README，但那一遍的 stdout 载体名是 shell 重定向
# 当场决定的 ⇒ 落地器**不可能**在自己的正文里写出它自己的载体名（第十次那一格就有这一行，本遍补齐这个缺口）。
# 三条老规矩照守：幂等门、全部裁决排在写盘之前、正文里每个数都从载体现读。
# 与上一遍的咬合处：本遍现读的 README md5 必须等于上一遍 stdout 里打印的那个"写盘后 md5"⇒ 两遍之间没夹进第三方改动。
# ⚠ 本只第一跑（13:59 之前）在"插入体自带行尾换行"这条上是错的：`line` 不带 `\n` 而 `sfx` 跳过了原件那根换行
#   ⇒ 插进去的这行**借走了标题前那根空行**，行数不涨而字节 +464，被写盘之后的行/字节等式咬住（rc=1 但盘已动）。
#   坏态取证 = `hardware/r61b_sync/evidence/readme_broken_nocr_*.md`，修补 = `scripts/fix_readme11b_newline.py`；
#   下面那三条 `assert` 里有两条（`line.endswith(b'\n')` / `pre[len(pfx)] == b'\n'`）就是为这一条补的前置钉。
import glob
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
RM = os.path.join(REPO, 'backups', 'README.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
GATE = '（载体：本格 ①~⑪ 全部现跑读数'
VERDICT_ANCHOR = '⇒ 判定**变了**'


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）：%s' % (
        prefix, must, len(hits), [os.path.basename(x) for x in hits])
    return hits[0]


# 上一遍的三处载体：stdout 日志、pre-image、以及本格引用的两只输入载体
LOG = one('r61b_readme11_land_*.txt', 'VERDICT=LANDED rc=0')
PIMG = one('readme_pre11_*.md')
VR = one('r61b_verify_root_*.txt', 'VERDICT=ROOT_VERIFIED')
DS = one('r61b_docs_snapshot11_*.txt', 'TABLE_ROWS')
log_txt = io.open(LOG, encoding='utf-8').read()
m = re.search(r'md5 ([0-9a-f]{8}) -> ([0-9a-f]{8})', log_txt)
assert m, 'ABORT: 上一遍日志里取不到 "md5 前 -> 后" 那一行'
MD5_PREV_IN, MD5_PREV_OUT = m.group(1), m.group(2)
m2 = re.search(r'README 行 (\d+) -> (\d+) \| 字节 (\d+) -> (\d+)', log_txt)
assert m2, 'ABORT: 上一遍日志里取不到行列'
LN_A0, LN_A1, BY_A0, BY_A1 = (int(x) for x in m2.groups())

pre = io.open(RM, 'rb').read()
assert hashlib.md5(pre).hexdigest()[:8] == MD5_PREV_OUT, \
    'ABORT: README 现读 md5 %s != 上一遍写盘后 md5 %s ⇒ 两遍之间夹进了没点名的改动' % (
        hashlib.md5(pre).hexdigest()[:8], MD5_PREV_OUT)
assert (pre.count(b'\n'), len(pre)) == (LN_A1, BY_A1), \
    'ABORT: README 现读行/字节 %d/%d != 上一遍写盘后 %d/%d' % (pre.count(b'\n'), len(pre), LN_A1, BY_A1)
if GATE.encode('utf-8') in pre:
    raise SystemExit('ABORT: 载体行已在册（幂等门），本遍不叠加')
p0 = pre.decode('utf-8')
assert p0.count(VERDICT_ANCHOR) == 1, 'ABORT: 判定锚 %r 命中 %d 处（应为 1）⇒ 插入点不唯一' % (
    VERDICT_ANCHOR, p0.count(VERDICT_ANCHOR))
_i = p0.index(VERDICT_ANCHOR)
_eol = p0.index('\n', _i)
assert p0.count('第十一次读数') >= 1 and p0[:_i].rindex('第十一次读数') > p0.rindex('【09-25 **15:37:12 第十次读数**'), \
    'ABORT: 那个判定锚不在第十一次那一格之内'
assert pre.count(b'\r') == 0 and pre[:3] != b'\xef\xbb\xbf', 'ABORT: README 形状不是"全 LF / 无 BOM"'

BODY = ('（载体：本格 ①~⑪ 全部现跑读数 = `hardware/r61b_sync/evidence/%s`（上一遍的 stdout，rc=0；'
        '写盘前的 README 原件快照同目录 `%s`，md5 %s）；⑥⑦ 两格的输入 = 同目录 `%s` 与 `%s`；'
        '本行本身由 `%s` 写出 ⇒ **本遍对 README 只做了一次插入，没覆写任何旧格**。）' % (
            os.path.basename(LOG), os.path.basename(PIMG), MD5_PREV_IN,
            os.path.basename(VR), os.path.basename(DS), os.path.basename(__file__)))
line = (BODY + '\n').encode('utf-8')   # ⚠ 插入体必须**自带行尾换行**：第一跑漏了它 ⇒ 载体行吞掉了标题前那根空行
assert b'%T' not in line and b'%S' not in line, 'ABORT: 载体行里混进了未转义的 % 序列'
assert line.endswith(b'\n') and line.count(b'\n') == 1, 'ABORT: 插入体不是"一行 + 一根行尾换行"'
# ⚠ 字符下标不能直接当字节偏移用（README 满篇中文 ⇒ p0 的第 i 个字符 != pre 的第 i 个字节）。
#    所以这里把"插入点之前的字符"整体编码成字节，再拿**字节长度**去切 `pre`。
pfx = p0[:_eol].encode('utf-8')
assert pre[:len(pfx)] == pfx, 'ABORT: 前缀编码回切不等 ⇒ 字符/字节混用又犯了'
assert pre[len(pfx):len(pfx) + 1] == b'\n', 'ABORT: 字符下标对应的位置不是换行 ⇒ 字节偏移推错了'
sfx = pre[len(pfx) + 1:]
ins = pfx + line + sfx
_exp_lines = pre.count(b'\n') + 1
_exp_bytes = len(pre) + len(line)

io.open(RM, 'wb').write(ins)
chk = io.open(RM, 'rb').read()
assert chk[:len(pfx)] == pfx, 'ABORT: 插入点之前被改动'
assert chk[len(pfx):len(pfx) + len(line)] == line, 'ABORT: 插入体逐字不等'
assert chk[len(pfx) + len(line):] == sfx, 'ABORT: 插入点之后被改动'
assert (chk.count(b'\n'), len(chk)) == (_exp_lines, _exp_bytes), 'ABORT: 落盘后行/字节与期望不符'
assert hashlib.md5(io.open(PIMG, 'rb').read()).hexdigest()[:8] == MD5_PREV_IN, 'ABORT: pre-image 与上一遍写盘前原件不等'
print('CARRIER_LINE %d B -> README 行 %d -> %d | 字节 %d -> %d | md5 %s -> %s' % (
    len(line), _exp_lines - 1, chk.count(b'\n'), len(pre), len(chk),
    hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('三段字节证明：插入点前=OK 插入体=OK 插入点后=OK | 与上一遍日志咬合：md5/行/字节 三处一致=OK')
print('VERDICT=CARRIER_LINE_LANDED rc=0')
