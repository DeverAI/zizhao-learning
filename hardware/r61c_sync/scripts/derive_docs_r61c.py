# r61c 代派生器：把 `hardware/refresh_docs_snapshot_r61b.py`（docs 第十二遍那一只脚本）**逐字派生**成第十三遍，只动替换表里那几处。
# 口径与上一代派生器一致（替换表 = 本轮改动唯一权威定义、每条锚 count==1、字节形状继承并断言、新清单每只源当场在盘上）。
# 封界守卫：解析出的目标路径含 `ht305_sync` 即停（末版 gen 24 之后往归档里落一字节 = 亲手把末版降级）。
import ast
import difflib
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r61b.py')
OUT = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r61c.py')
NEW_GEN = 'r61c'
SEAL = 'ht305_sync'
for p in (PRIOR, OUT):
    assert SEAL not in p.replace('\\', '/'), 'ABORT: 派生器自己的路径碰了封存归档 %s' % SEAL
assert os.path.isfile(PRIOR), 'ABORT: 被派生那只不在盘上 ⇒ NOTE 的派生自会是假指针'

pre_b = io.open(PRIOR, 'rb').read()
pre_txt = pre_b.decode('utf-8')
assert pre_b.count(b'\r') == 0, 'ABORT: 被派生那只带 CR，本代替换表是按 LF 写的'
assert pre_b[:3] != b'\xef\xbb\xbf', 'ABORT: 被派生那只有 BOM，继承断言的口径要跟着改'

R = []

# (A) 文件头三行：代名 + 派生源 + 派生器指针
R.append((
    "# 根 A docs/ 快照刷新（r61b 代 = 第十一遍）：由 hardware/refresh_docs_snapshot_r57.py（第十遍）逐字派生，"
    "派生器 = hardware/r61b_sync/scripts/derive_docs_r61b.py（替换表见该文件，表外任何一处字节变了它的 difflib 计数就红）。",
    "# 根 A docs/ 快照刷新（r61c 代 = 第十三遍）：由 hardware/refresh_docs_snapshot_r61b.py（第十二遍脚本）逐字派生，"
    "派生器 = hardware/r61c_sync/scripts/derive_docs_r61c.py（替换表见该文件，表外任何一处字节变了它的 difflib 计数就红）。"))

# (B) PRIOR 指针
R.append((
    "PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r57.py')",
    "PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r61b.py')"))

# (C) SRCS 追加 1 只（本代唯一的新收口件），锚在清单最后一只之后
R.append((
    "    'hardware/BOARD_S3_ePaper_1_54.md',\n]",
    "    'hardware/BOARD_S3_ePaper_1_54.md',\n"
    "    'updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md',\n]"))

# (D) 完整性守卫：只数下限 48 → 49
R.append((
    "# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35、r54 36、r55 37、r57 40，本代（r61b 代 = 第十一遍）抬到 48）："
    "五只\"活文档\"必须在清单里，否则说明这份派生清单被截断过。",
    "# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35、r54 36、r55 37、r57 40、r61b 48，"
    "本代（r61c 代 = 第十三遍）抬到 49）：五只\"活文档\"必须在清单里，否则说明这份派生清单被截断过。"))
R.append((
    "if absent or len(SRCS) < 48:\n"
    "    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 48）' % (absent, len(SRCS)))",
    "if absent or len(SRCS) < 49:\n"
    "    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 49）' % (absent, len(SRCS)))"))

# (E) NOTE 的派生自那一整段
R.append((
    "    f.write('派生自 hardware/refresh_docs_snapshot_r57.py（第十遍 = r57 代；两只派生源同在 hardware/，路径 grep 得到，'\n"
    "            '本代另带一只派生器 hardware/r61b_sync/scripts/derive_docs_r61b.py：改动以替换表为准，不靠手抄。'\n"
    "            '更早的第八遍在 hardware/ht305_sync/scripts/ 里，那是末版 gen 24 之前的事），三处改动：'\n",
    "    f.write('派生自 hardware/refresh_docs_snapshot_r61b.py（第十二遍脚本 = r61b 代；两只派生源同在 hardware/，路径 grep 得到，'\n"
    "            '本代派生器 hardware/r61c_sync/scripts/derive_docs_r61c.py：改动以替换表为准，不靠手抄。'\n"
    "            '更早的第八遍在 hardware/ht305_sync/scripts/ 里，那是末版 gen 24 之前的事），三处改动：'\n"))
R.append((
    "            '①SRCS 加 8 只：`dev_log/20260926.md`、两只 09-26 收口件 '\n"
    "            '（`updates/20260926_墨水屏R60版面R61翻页与两件档案补齐.md`、`updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md`）、'\n"
    "            '三只判据摘录（`hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt`、`hardware/20260925_R57_F臂判据摘录.txt`、'\n"
    "            '`hardware/20260925_R59板型鉴定判据摘录.txt`）、两只板档案（`hardware/BOARD_ePaper397.md`、'\n"
    "            '`hardware/BOARD_S3_ePaper_1_54.md`）——R56/R57-E 各有一只同名 v1，**v1 一律不进快照，只进 v2**；'\n"
    "            '②完整性守卫的只数下限从 40 抬到 48（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言、'\n"
    "            \"'派生那只必须真在仓库里'那道 r57 新增的闸，全部原样继承，不重写）；\"\n"
    "            '③本行本身（上一代这里写的是\"从 r55 派生、加 3 只 + 只数下限 37→40\"）。'\n",
    "            '①SRCS 加 1 只：`updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md`"
    "（r61b 收口件的阶段归档，本代唯一新增源；本批无新判据摘录、无新板档案、无新 dev_log 日期文件）；'\n"
    "            '②完整性守卫的只数下限从 48 抬到 49（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言、'\n"
    "            \"'派生那只必须真在仓库里'那道 r57 新增的闸，全部原样继承，不重写）；\"\n"
    "            '③本行本身（上一代这里写的是\"从 r57 派生、加 8 只 + 只数下限 40→48\"）。'\n"))

for i, (a, b) in enumerate(R):
    n = pre_txt.count(a)
    assert n == 1, 'ABORT: 替换表第 %d 条的锚命中 %d 次（应为 1）' % (i + 1, n)

new_txt = pre_txt
for a, b in R:
    new_txt = new_txt.replace(a, b, 1)

assert SEAL not in OUT.replace('\\', '/'), 'ABORT: 输出路径碰封存归档'
assert NEW_GEN in os.path.basename(OUT)
ast.parse(new_txt)
for tok in ('TODO', 'PLACEHOLDER', '占位'):
    assert tok not in new_txt, 'ABORT: 派生体里残留未解析哨兵 %r' % tok
_ns = ast.parse(new_txt)
_ps = ast.parse(pre_txt)


def _srcs(_tree):
    n = [x for x in _tree.body if isinstance(x, ast.Assign) and getattr(x.targets[0], 'id', '') == 'SRCS']
    assert len(n) == 1, 'ABORT: SRCS 赋值不是唯一一处'
    return [x.value for x in n[0].value.elts]


SRCS_NEW = _srcs(_ns)
SRCS_OLD = _srcs(_ps)
ADDED = [x for x in SRCS_NEW if x not in SRCS_OLD]
assert len(SRCS_OLD) == 49, 'ABORT: 被派生那只的 SRCS 不是 49 只（本替换表的前提没了）：%d' % len(SRCS_OLD)
assert len(SRCS_NEW) == len(SRCS_OLD) + 1 and len(ADDED) == 1, \
    'ABORT: SRCS 只数没有按替换表加 1（%d -> %d / 新增 %d）' % (len(SRCS_OLD), len(SRCS_NEW), len(ADDED))
assert len(set(SRCS_NEW)) == len(SRCS_NEW), 'ABORT: 新清单里有重名（路径级）'
_bn = [os.path.basename(x) for x in SRCS_NEW]
_dup = sorted({b for b in _bn if _bn.count(b) > 1})
assert not _dup, 'ABORT: 平铺到 docs/ 后会互相覆盖（同名 %d 只）：%s' % (len(_dup), _dup)
_missing = [x for x in SRCS_NEW if not os.path.isfile(os.path.join(REPO, x.replace('/', os.sep)))]
assert not _missing, 'ABORT: 新清单里 %d 只源不在盘上：%s' % (len(_missing), _missing)
_first = [x for x in SRCS_NEW if os.path.basename(x) in
          ('20260919_墨水屏点屏排查记录.md', '烧录须知.md', 'FreqErr.md', 'done.md', 'todo.md')]
assert len(_first) == 5, 'ABORT: 平铺后五只活文档的名字有撞车风险'

nb = new_txt.encode('utf-8')
assert nb.count(b'\r') == 0, 'ABORT: 派生体带 CR'
assert nb[:3] != b'\xef\xbb\xbf', 'ABORT: 派生体带 BOM'

_ol = pre_txt.splitlines()
_nl = new_txt.splitlines()
_removed = [l for l in difflib.unified_diff(_ol, _nl, lineterm='', n=0) if l.startswith('-') and not l.startswith('---')]
_old_lines_in_table = set()
for a, _b in R:
    _old_lines_in_table.update(a.splitlines())
_strays = [l[1:] for l in _removed if l[1:] not in _old_lines_in_table]
assert not _strays, 'ABORT: 替换表之外有 %d 行被改动：%s' % (len(_strays), _strays[:3])
_add = len([l for l in difflib.unified_diff(_ol, _nl, lineterm='', n=0) if l.startswith('+') and not l.startswith('+++')])
_del = len(_removed)

OUT_MD5_PRE_PRIOR = hashlib.md5(pre_b).hexdigest()
io.open(OUT, 'wb').write(nb)
back = io.open(OUT, 'rb').read()
assert back == nb, 'ABORT: 回读字节与写盘字节不等'
assert hashlib.md5(io.open(PRIOR, 'rb').read()).hexdigest() == OUT_MD5_PRE_PRIOR, 'ABORT: 被派生那只被本遍改动了'

print('PRIOR  %s | %d B / %d lines / md5 %s（写后复算同值）' % (
    os.path.basename(PRIOR), len(pre_b), pre_b.count(b'\n'), OUT_MD5_PRE_PRIOR[:8]))
print('OUT    %s | %d B / %d lines / md5 %s' % (
    os.path.basename(OUT), len(back), back.count(b'\n'), hashlib.md5(back).hexdigest()[:8]))
print('REPLACEMENTS=%d DIFF(+/-)=%d/%d STRAYS=0' % (len(R), _add, _del))
print('SRCS_OLD=%d SRCS_NEW=%d ADDED=%d 源全在盘上=OK 平铺名不撞=OK' % (
    len(SRCS_OLD), len(SRCS_NEW), len(ADDED)))
for x in ADDED:
    print('  +', x)
print('EOL=LF BOM=False CR=0 守卫下限: 48 -> 49')
print('VERDICT=DERIVED rc=0')
