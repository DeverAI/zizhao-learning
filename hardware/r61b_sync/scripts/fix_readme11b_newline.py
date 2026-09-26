# 修补遍：上一遍（`land_r61b_readme11b.py` 第一跑）把载体行**插成了不但不换行、还吞掉了一根空行**——
# `ins = pfx + b'\n' + line + sfx` 里 `sfx` 已经跳过原件那根换行符，而 `line` 自身不带换行 ⇒
# 载体行的行尾**借用了**原本"标题前那根空行"的换行：字面上标题仍独占一行（肉眼看不出），
# 但 `行数没涨（462 = 写盘前）而字节 +464` ⇒ 那一格与 `## 2. 命名规则` 之间的空行没了。
# 抓到它的正是那条 `assert (chk.count(b'\n'), len(chk)) == (_exp_lines, _exp_bytes)`，
# 而它排在**写盘之后**（探测器不是防护）⇒ 这里先按规矩取证：把**坏态**整只快照进 evidence/，
# 再只在标题前补一根 `\n`（单字节插入，不删、不覆写任何其他字节）。
# 修补后的期望值不手抄：行数/字节数从上一遍 stdout 日志现读再各 +1，md5 现算。
import datetime
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
# bytes 字面量装不下非 ASCII（`b'…命名规则'` 直接 SyntaxError）⇒ 先写 str 再编码。
HEAD2 = '## 2. 命名规则'.encode('utf-8')
GATE = '（载体：本格 ①~⑪ 全部现跑读数'.encode('utf-8')

LOG = [p for p in sorted(glob.glob(os.path.join(EV, 'r61b_readme11_land_*.txt')))
       if 'VERDICT=LANDED rc=0' in io.open(p, encoding='utf-8').read()]
assert len(LOG) == 1, 'ABORT: 上一遍 stdout 载体命中 %d 只（应为 1）' % len(LOG)
m = re.search(r'README 行 (\d+) -> (\d+) \| 字节 (\d+) -> (\d+)', io.open(LOG[0], encoding='utf-8').read())
assert m, 'ABORT: 上一遍日志里取不到行列'
A_LN, A_BY = int(m.group(2)), int(m.group(4))

cur = io.open(RM, 'rb').read()
assert GATE in cur, 'ABORT: 载体行不在盘上 ⇒ 本遍要修的东西不存在，先看清现场'
i = cur.index(GATE)
j = cur.index(HEAD2, i)
# 坏态的形状（本遍现读确认，不是猜的）：载体行**吃掉了**标题前面那根空行——
# 上一遍产出的尾巴是 `判定行\n` + `\n## 2. 命名规则`（标题前有一根空行），
# 本遍插进去的 `line` 不带换行，于是拿走了那根空行的换行 ⇒ 变成 `判定行\n` + `载体行\n## 2. 命名规则`。
# 所以判据不是"标题前有没有换行"（有，一行 terminator），而是"**标题前是不是两根换行**"。
assert cur[j - 1:j] == b'\n' and cur[j - 2:j - 1] != b'\n', \
    'ABORT: 标题前不是"一行 terminator 而缺空行"这种坏态（前两字节 = %r）⇒ 本遍不该动手' % (cur[j - 2:j],)
assert cur[i:j].count(b'\n') == 1, 'ABORT: 载体行与标题之间不是恰好一根换行 ⇒ 坏态与登记的不是一回事'
assert cur.count(b'\n') == A_LN and len(cur) > A_BY, \
    'ABORT: 现读 %d 行 / %d B 与"上一遍写盘后 %d 行 + 只增字节"的形状不符 ⇒ 坏态不是我认的那种' % (
        cur.count(b'\n'), len(cur), A_LN)
assert cur.count(b'\r') == 0, 'ABORT: 现读带 CR'
assert cur.count(HEAD2) == 1, 'ABORT: 标题锚命中 %d 处（应为 1）⇒ 插入点不唯一' % cur.count(HEAD2)

# 坏态取证（只新建，不覆写：同秒重名即 ABORT）
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BAD = os.path.join(EV, 'readme_broken_nocr_%s.md' % ts)
assert not os.path.exists(BAD), 'ABORT: 坏态快照目标已存在，不覆写 ' + BAD
io.open(BAD, 'wb').write(cur)
assert io.open(BAD, 'rb').read() == cur, 'ABORT: 坏态快照回读不等'

fixed = cur[:j] + b'\n' + cur[j:]
_exp_lines, _exp_bytes = A_LN + 1, len(cur) + 1
io.open(RM, 'wb').write(fixed)
chk = io.open(RM, 'rb').read()
assert chk[:j] == cur[:j], 'ABORT: 前缀被改动'
assert chk[j + 1:] == cur[j:], 'ABORT: 后缀被改动'
assert (chk.count(b'\n'), len(chk)) == (_exp_lines, _exp_bytes), 'ABORT: 补换行后的行/字节与期望不符'
assert chk.count(HEAD2) == 1 and chk.count(b'\r') == 0 and chk[:3] != b'\xef\xbb\xbf'
assert chk.count(GATE) == 1, 'ABORT: 载体行不止一处（叠加了）'
print('BAD-SNAPSHOT %s (%d B / md5 %s)' % (os.path.basename(BAD), len(cur), hashlib.md5(cur).hexdigest()[:8]))
print('README 行 %d -> %d | 字节 %d -> %d | md5 %s -> %s' % (
    cur.count(b'\n'), chk.count(b'\n'), len(cur), len(chk),
    hashlib.md5(cur).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('期望值来源：上一遍日志 %s 现读 (%d 行 / %d B) 各 +1 = (%d, %d)' % (
    os.path.basename(LOG[0]), A_LN, A_BY, _exp_lines, _exp_bytes))
print('前后缀逐字等=OK 只插一根 \\n=OK 标题前空行恢复=OK 载体行只 1 处=OK 零删除=OK')
print('VERDICT=NEWLINE_REPAIRED rc=0')
