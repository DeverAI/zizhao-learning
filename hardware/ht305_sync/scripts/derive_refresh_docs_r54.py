# -*- coding: utf-8 -*-
# 派生 refresh_docs_snapshot_r54.py（第八遍）= r53 那只的逐字派生，只动点名的 5 处。
# 纪律：任何一处的目标行必须"恰好出现 1 次"，否则 ABORT 且不写盘（校验前置于写盘）。
import sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')

TMP = os.path.join(os.environ['LOCALAPPDATA'], 'Temp')
SRC = os.path.join(TMP, 'refresh_docs_snapshot_r53.py')
DST = os.path.join(TMP, 'refresh_docs_snapshot_r54.py')

t = open(SRC, encoding='utf-8').read()
lines = t.split('\n')


def find_unique(pred, what):
    idx = [i for i, l in enumerate(lines) if pred(l)]
    assert len(idx) == 1, 'ABORT: %s 命中 %d 次' % (what, len(idx))
    return idx[0]


edits = []

i = find_unique(lambda l: l.startswith('# 根 A docs/ 快照刷新（r53 代 = 第七遍）'), '头 1')
edits.append((i, i, ['# 根 A docs/ 快照刷新（r54 代 = 第八遍）：由 C:\\Users\\david\\AppData\\Local\\Temp\\refresh_docs_snapshot_r53.py（第七遍）逐字派生。']))

i = find_unique(lambda l: l.startswith('# 对**被派生那只**的改动只有三处'), '头 2')
edits.append((i, i, ['# 对**被派生那只**的改动只有四处，逐处点名见文件末尾 NOTE 的"派生自"那一行（本代第 ③ 处是新的：NOTE 里所有只数一律插值，不再手抄）。']))

i = find_unique(lambda l: l == "    'updates/20260924_墨水屏R53_GPIO1按住落地与两处自查.md',", 'SRCS 尾巴')
edits.append((i, i, [lines[i], "    'updates/20260924_墨水屏R54第12代同步与gen20-21冻结.md',"]))

i = find_unique(lambda l: l.startswith('# 守卫（r50 代新增'), '守卫注释')
edits.append((i, i, ['# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35，本代（r54 代 = 第八遍）抬到 36）：五只"活文档"必须在清单里，否则说明这份派生清单被截断过。']))

i = find_unique(lambda l: l == 'if absent or len(SRCS) < 35:', '阈值')
edits.append((i, i, ['if absent or len(SRCS) < 36:']))

i = find_unique(lambda l: l.startswith("    print('ABORT: 源清单不完整"), 'ABORT 文案')
edits.append((i, i, ["    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 36）' % (absent, len(SRCS)))"]))

i = find_unique(lambda l: l.startswith("    f.write('派生自 C:"), 'NOTE 派生自段 ①')
j = find_unique(lambda l: l.strip().startswith("'注意：本 NOTE 里"), 'NOTE 派生自段 末')
NOTE_NEW = r'''    f.write('派生自 C:\\Users\\david\\AppData\\Local\\Temp\\refresh_docs_snapshot_r53.py（第七遍 = r53 代），四处改动：'
            '①SRCS 加 1 只：`updates/20260924_墨水屏R54第12代同步与gen20-21冻结.md`（本代新增的收口件）；'
            '②完整性守卫的只数下限从 35 抬到 36（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言都原样继承，不重写）；'
            '③**本 NOTE 里所有只数一律由脚本插值**（上一代那句"35 只源"比自身表格晚了一代）⇒ 下面另加两道自核：表格行数 == len(rows)、"现读 %d 只源"这句真的在 NOTE 里；'
            '④本行本身（上一代这里写的是"从 r51a 派生、加 1 只 + 只数下限 34→35"）。'
            '本次运行：源清单现读 %d 只，运行数以 stdout 的 CRED_GATE / FILES / TABLE_ROWS 三行为准。\n' % (len(SRCS), len(SRCS)))'''
edits.append((i, j, NOTE_NEW.split('\n')))

i = find_unique(lambda l: l == "print('FILES', len(rows))", 'FILES 打印')
edits.append((i, i, [
    "print('FILES', len(rows))",
    "note_txt = open(note, encoding='utf-8').read()",
    "table_rows = len([l for l in note_txt.split('\\n') if re.match(r'^[^\\t]+\\t\\d+\\tmd5:', l)])",
    "assert table_rows == len(rows), 'NOTE 表格行数 %d != rows %d' % (table_rows, len(rows))",
    "assert ('现读 %d 只源' % len(SRCS)) in note_txt, 'NOTE 里的只数没有插值成 SRCS 现读数'",
    "print('TABLE_ROWS', table_rows, '== FILES', len(rows))"]))

# 从后往前替换，避免下标漂移
for a, b, new in sorted(edits, key=lambda e: -e[0]):
    lines[a:b + 1] = new

out = '\n'.join(lines)
assert out.count('refresh_docs_snapshot_r53.py') == 2, out.count('refresh_docs_snapshot_r53.py')
assert "R54第12代同步与gen20-21冻结" in out
assert len(SRC) and os.path.isfile(SRC)
assert not os.path.exists(DST), '目标已存在，不覆盖: ' + DST
import ast
ast.parse(out)
open(DST, 'w', encoding='utf-8', newline='\n').write(out)
print('DERIVED', DST, len(out.encode('utf-8')), 'bytes  md5', hashlib.md5(out.encode('utf-8')).hexdigest()[:8])
print('PARENT ', SRC, os.path.getsize(SRC), 'bytes  md5', hashlib.md5(open(SRC, 'rb').read()).hexdigest()[:8])
print('EDITED_LINES_TOTAL', sum(len(n) - (b - a + 1) for a, b, n in edits))
