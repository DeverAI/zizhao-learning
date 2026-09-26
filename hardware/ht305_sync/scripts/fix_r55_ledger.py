# R55 第一遍的**台账订正**追加器（FreqErr.md 只追加、不改已写行）。
# 为什么要有这一步：land_r55_A.py 的"追加之后"两数是在**行尾闭合那一步之前**数的 ⇒ 登记 1824 行、盘上 1825 行。
# 本脚本自己不再犯：所有"之后"的数都对**将被写出的完整字节串**数，闭合换行也算进去。
import hashlib
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FREQ = 'C:/Users/david/Documents/all_projects/自招学习/FreqErr.md'
raw = open(FREQ, 'rb').read()
t = raw.decode('utf-8')
assert raw.endswith(b'\r\n') and raw.count(b'\r') == raw.count(b'\n'), 'FreqErr 不是纯 CRLF 或末行未闭合'
ET = '[错误类型]'
ets = sum(1 for l in t.split('\r\n') if l.startswith(ET))
lines = t.count('\n')
print('DISK_BEFORE ets=%d lines=%d bytes=%d' % (ets, lines, len(raw)))
assert ets == 181 and lines == 1825, ('盘上读数与 ④/载体登记不符', ets, lines)
# 上一格台账里那句错登记必须逐字在盘上，否则订正句就成了假引文（(77)~(79) 之训）
BAD = '`wc -l` = **1824**'
assert t.count(BAD) == 1, '要找的是那句 1824，盘上没有/不止一处都不许动手'

add = '\r\n'.join([
 '',
 '> **【订正｜%s】** 上一格（R55 第一遍台账）那句"追加之后 `wc -l` = **1824**"**少 1**：本行落笔前另一次独立调用现读磁盘 = **1825 行 / `^[错误类型]` 181 条** ⇒ 错误类型那一对（179→181）无误，漂的仍只有行数。根因**不是** R54 那条"没算台账行自身"（那次已修对），而是**同一台账行写完后的"行尾闭合"那一步在计数之后执行**：落地器先对 `final` 数了行数，再判"末字节不是 CRLF 就补一只 `\\r\\n`" ⇒ 补的那一只换行没进任何一次计数。本仓库口径：**台账只追加、不就地改数**（上一行原样保留），本行之上那格 1824 与盘上 1825 的关系由本行给出。'
 % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
])
final = t + add + '\r\n'
n_ets = sum(1 for l in final.split('\r\n') if l.startswith(ET))
n_lines = final.count('\n')
raw2 = final.encode('utf-8')
assert raw2.endswith(b'\r\n'), '闭合换行没算进 final'
assert raw2.count(b'\n') == n_lines and raw2.count(b'\r') == n_lines, 'final 字节数与本行登记的数不符'
assert raw2[:len(raw)] == raw, '不是纯追加'
open(FREQ, 'wb').write(raw2)
c = open(FREQ, 'rb').read()
print('AFTER ets=%d lines=%d bytes=%d match=%s' % (
    n_ets, n_lines, len(c), c == raw2 and c.count(b'\n') == n_lines))
print('订正句里的 ET 计数不变：', n_ets == ets, '（本行不以 [错误类型] 开头）')
