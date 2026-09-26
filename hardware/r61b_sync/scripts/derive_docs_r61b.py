# r61b 代派生器：把 `hardware/refresh_docs_snapshot_r57.py`（docs 第十遍）**逐字派生**成第十一遍，只动替换表里那几处。
# 为什么要派生器而不是手抄一遍（手抄是本仓库登记过的缺陷形态）：
#   ①替换表 = 本轮改动唯一的权威定义 —— 表外任何一处字节若变了，`difflib` 的计数断言就会红；
#   ②每条替换都要求 `count == 1`（0 = 上一代那句话已经不在了，>1 = 我改的不是我要改的那一处）；
#   ③字节形状（BOM / CR 只数 / 行只数）从被派生那只**继承并断言**，不靠"py 文件应该没 BOM"这种话术；
#   ④新清单里每一只源必须**当场在盘上存在**（缺一只即 ABORT）—— 快照脚本里留一只不存在的源 = 下一遍必崩。
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
PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r57.py')
OUT = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r61b.py')
NEW_GEN = 'r61b'
SEAL = 'ht305_sync'
for p in (PRIOR, OUT):
    assert SEAL not in p.replace('\\', '/'), 'ABORT: 派生器自己的路径碰了封存归档 %s' % SEAL
assert os.path.isfile(PRIOR), 'ABORT: 被派生那只不在盘上 ⇒ NOTE 的"派生自"会是假指针'

pre_b = io.open(PRIOR, 'rb').read()
pre_txt = pre_b.decode('utf-8')
assert pre_b.count(b'\r') == 0, 'ABORT: 被派生那只带 CR，本代派生器的替换表是按 LF 写的'
assert pre_b[:3] != b'\xef\xbb\xbf', 'ABORT: 被派生那只有 BOM，继承断言的口径要跟着改'

# ---------- 替换表（唯一权威定义，按"从上到下"排） ----------
R = []

# (A) 文件头三行：代名 + 派生源 + 改动处数
R.append((
    "# 根 A docs/ 快照刷新（r57 代 = 第十遍）：由 hardware/refresh_docs_snapshot_r55.py（第九遍）逐字派生。\n"
    "# 与上一代不同的一件事：派生源与上一代同处一只目录（都在 hardware/，不在 %TEMP%），\"派生自\"那一句仍是 grep 得到的仓库路径。\n"
    "# 对**被派生那只**的改动只有四处，逐处点名见文件末尾 NOTE 的\"派生自\"那一行。",
    "# 根 A docs/ 快照刷新（r61b 代 = 第十一遍）：由 hardware/refresh_docs_snapshot_r57.py（第十遍）逐字派生，"
    "派生器 = hardware/r61b_sync/scripts/derive_docs_r61b.py（替换表见该文件，表外任何一处字节变了它的 difflib 计数就红）。\n"
    "# 派生源仍与上一代同处一只目录（都在 hardware/，不在 %TEMP%），\"派生自\"那一句仍是仓库内 grep 得到的路径。\n"
    "# 对**被派生那只**的改动只有三处，逐处点名见文件末尾 NOTE 的\"派生自\"那一行。"))

# (B) PRIOR 指针：本代被派生的是 r57
R.append((
    "PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r55.py')",
    "PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r57.py')"))

# (C) SRCS 追加 8 只（锚在清单最后一只，追加在它之后）
R.append((
    "    'hardware/20260924_ps1编码吞行实验.txt',\n]",
    "    'hardware/20260924_ps1编码吞行实验.txt',\n"
    "    'dev_log/20260926.md',\n"
    "    'updates/20260926_墨水屏R60版面R61翻页与两件档案补齐.md',\n"
    "    'updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md',\n"
    "    'hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt',\n"
    "    'hardware/20260925_R57_F臂判据摘录.txt',\n"
    "    'hardware/20260925_R59板型鉴定判据摘录.txt',\n"
    "    'hardware/BOARD_ePaper397.md',\n"
    "    'hardware/BOARD_S3_ePaper_1_54.md',\n]"))

# (D) 完整性守卫：只数下限 40 → 48（守卫本体 / MUST 五只 / 明文凭据闸 / 逐字节回读断言原样继承）
R.append((
    "# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35、r54 36、r55 37，本代（r57 代 = 第十遍）抬到 40）："
    "五只\"活文档\"必须在清单里，否则说明这份派生清单被截断过。",
    "# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35、r54 36、r55 37、r57 40，"
    "本代（r61b 代 = 第十一遍）抬到 48）：五只\"活文档\"必须在清单里，否则说明这份派生清单被截断过。"))
R.append((
    "if absent or len(SRCS) < 40:\n"
    "    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 40）' % (absent, len(SRCS)))",
    "if absent or len(SRCS) < 48:\n"
    "    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 48）' % (absent, len(SRCS)))"))

# (E) NOTE 的"派生自"那一整段（本代的四处改动逐处点名，只数一律由脚本插值）
R.append((
    "    f.write('派生自 hardware/refresh_docs_snapshot_r55.py（第九遍 = r55 代；两只派生源同在 hardware/，路径 grep 得到。'\n"
    "            '更早的第八遍在 hardware/ht305_sync/scripts/ 里，那是末版 gen 24 之前的事），四处改动：'\n"
    "            '①SRCS 加 3 只：`updates/20260925_墨水屏R56四臂R57E臂与收口批四遍.md`、`dev_log/20260925.md`、'\n"
    "            '`hardware/20260925_R57_E臂判据摘录_v2.txt`（本代新落盘的收口件与 E 臂判据载体）；'\n"
    "            '②完整性守卫的只数下限从 37 抬到 40（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言都原样继承，不重写）；'\n"
    "            '③**本 NOTE 里所有只数仍由脚本插值**（承上一代 ③），另加两道自核：表格行数 == len(rows)、\"现读 %d 只源\"这句真的在 NOTE 里；'\n"
    "            '④本行本身（上一代这里写的是\"从 r54 派生、加 1 只 + 只数下限 36→37\"）。'\n"
    "            '本次运行：源清单现读 %d 只，运行数以 stdout 的 CRED_GATE / FILES / TABLE_ROWS 三行为准。\\n' % (len(SRCS), len(SRCS)))",
    "    f.write('派生自 hardware/refresh_docs_snapshot_r57.py（第十遍 = r57 代；两只派生源同在 hardware/，路径 grep 得到，'\n"
    "            '本代另带一只派生器 hardware/r61b_sync/scripts/derive_docs_r61b.py：改动以替换表为准，不靠手抄。'\n"
    "            '更早的第八遍在 hardware/ht305_sync/scripts/ 里，那是末版 gen 24 之前的事），三处改动：'\n"
    "            '①SRCS 加 8 只：`dev_log/20260926.md`、两只 09-26 收口件 '\n"
    "            '（`updates/20260926_墨水屏R60版面R61翻页与两件档案补齐.md`、`updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md`）、'\n"
    "            '三只判据摘录（`hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt`、`hardware/20260925_R57_F臂判据摘录.txt`、'\n"
    "            '`hardware/20260925_R59板型鉴定判据摘录.txt`）、两只板档案（`hardware/BOARD_ePaper397.md`、'\n"
    "            '`hardware/BOARD_S3_ePaper_1_54.md`）——R56/R57-E 各有一只同名 v1，**v1 一律不进快照，只进 v2**；'\n"
    "            '②完整性守卫的只数下限从 40 抬到 48（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言、'\n"
    "            \"'派生那只必须真在仓库里'那道 r57 新增的闸，全部原样继承，不重写）；\"\n"
    "            '③本行本身（上一代这里写的是\"从 r55 派生、加 3 只 + 只数下限 37→40\"）。'\n"
    "            '本 NOTE 里所有只数仍由脚本插值，两道自核照旧：表格行数 == len(rows)、\"现读 %d 只源\"这句真的在 NOTE 里。'\n"
    "            '本次运行：源清单现读 %d 只，运行数以 stdout 的 CRED_GATE / FILES / TABLE_ROWS 三行为准。\\n' % (len(SRCS), len(SRCS)))"))

for i, (a, b) in enumerate(R):
    n = pre_txt.count(a)
    assert n == 1, 'ABORT: 替换表第 %d 条的锚在被派生那只里命中 %d 次（应为 1）' % (i + 1, n)

new_txt = pre_txt
for a, b in R:
    new_txt = new_txt.replace(a, b, 1)

# ---------- 裁决全部排在写盘之前 ----------
assert SEAL not in OUT.replace('\\', '/'), 'ABORT: 输出路径碰封存归档'
assert NEW_GEN in os.path.basename(OUT)
ast.parse(new_txt)                                   # 语法先行（落地三步序第 1 步）
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
assert len(SRCS_OLD) == 41, 'ABORT: 被派生那只的 SRCS 不是 41 只（本替换表的前提没了）：%d' % len(SRCS_OLD)
assert len(SRCS_NEW) == len(SRCS_OLD) + 8 and len(ADDED) == 8, \
    'ABORT: SRCS 只数没有按替换表加 8（%d -> %d / 新增 %d）' % (len(SRCS_OLD), len(SRCS_NEW), len(ADDED))
assert len(set(SRCS_NEW)) == len(SRCS_NEW), 'ABORT: 新清单里有重名（路径级）'
_bn = [os.path.basename(x) for x in SRCS_NEW]
_dup = sorted({b for b in _bn if _bn.count(b) > 1})
assert not _dup, 'ABORT: 平铺到 docs/ 后会互相覆盖（同名 %d 只）：%s' % (len(_dup), _dup)
_missing = [x for x in SRCS_NEW if not os.path.isfile(os.path.join(REPO, x.replace('/', os.sep)))]
assert not _missing, 'ABORT: 新清单里 %d 只源不在盘上：%s' % (len(_missing), _missing)
# docs/ 是**平铺**目录：五只"活文档"派生后必须是五只不同的名字（同名 = 后拷的静默覆掉先拷的）。
_first = [x for x in SRCS_NEW if os.path.basename(x) in
          ('20260919_墨水屏点屏排查记录.md', '烧录须知.md', 'FreqErr.md', 'done.md', 'todo.md')]
assert len(_first) == 5, 'ABORT: 平铺后五只活文档的名字有撞车风险'

nb = new_txt.encode('utf-8')
assert nb.count(b'\r') == 0, 'ABORT: 派生体带 CR，与被派生那只（0 只 CR）不同形'
assert nb[:3] != b'\xef\xbb\xbf', 'ABORT: 派生体带 BOM，与被派生那只（无 BOM）不同形'

# 表外零改动：把 unified diff 里**被删掉的行**逐行回查——每一行都必须能在替换表某个旧锚的分行里找到。
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
print('EOL=LF BOM=False CR=0 守卫下限: 40 -> 48')
print('VERDICT=DERIVED rc=0')