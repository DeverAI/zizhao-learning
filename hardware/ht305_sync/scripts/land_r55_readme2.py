"""R55 的第二遍 README 落地器：把 gen 22 / gen 23 / gen 24 三格 + 序数 + 第四遍桌面探测 + "本代没做"那一条的
**已补/仍缺**改写落进 `hardware/ht305_sync/README.md`。

红线（本仓库既有口径，逐条对应到代码）：
- 正文里的**每一个数字都从取证载体现读**（`grab()`/日志解析），抄不进手写数（(88) 那族：订正句里的假引文）。
- 跨行锚点 Edit 会静默删除既有结构 ⇒ 本脚本**先算行数差集再写盘**，写完**独立回读**证明结构与预期一致。
- 载体不覆写：`evidence/r55_land_readme.txt` 是第一遍那只，本遍另起 `_2`。
"""
import hashlib
import os
import re
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DST = os.path.join(REPO, 'hardware', 'ht305_sync')
EV = os.path.join(DST, 'evidence')
RM = os.path.join(DST, 'README.md')
_orig = open(RM, encoding='utf-8').read()


def read(rel):
    p = os.path.join(DST, rel.replace('/', os.sep))
    assert os.path.isfile(p), 'ABORT: 取证件不存在，拒绝凭记忆写数：' + rel
    return open(p, encoding='utf-8').read()


def grab(rel, pat, grp=1):
    m = re.search(pat, read(rel))
    assert m, 'ABORT: 载体 %s 里找不到 %r' % (rel, pat)
    return m.group(grp)


def comma(n):
    return '{:,}'.format(int(n))


# ---- 现读：两代清单的三字段 + 两遍门的 FILES_SCANNED + gen 22 头部时刻 + 第四遍桌面探测 ----
log = [l.split('\t') for l in read('evidence/manifest_gen_log.txt').splitlines()
       if l and not l.startswith('#')]
g22 = [r for r in log if r[0].endswith('12:34:42')]
g23 = [r for r in log if r[0].endswith('12:37:02')]
assert len(g22) == 1 and len(g23) == 1, 'ABORT: 代次日志里 12:34:42 / 12:37:02 两行不唯一'
n22, b22, bom22 = g22[0][1:4]
n23, b23, bom23 = g23[0][1:4]
hdr22 = grab('evidence/r55_verify_manifest_gen22_stale.txt', r'现跑于 (\d\d-\d\d \d\d:\d\d:\d\d)')
gate22 = 'evidence/cred_gate_recheck_123427.txt'
gate23 = 'evidence/cred_gate_recheck_123653.txt'
fs22 = grab(gate22, r'FILES_SCANNED=(\d+)')
fs23 = grab(gate23, r'FILES_SCANNED=(\d+)')
assert int(fs22) - 1 == int(n22) and int(fs23) - 1 == int(n23), \
    'ABORT: 关系式 `门扫数 − 1 == TOTAL` 不成立，本遍不许登记它'
rows22 = grab('evidence/r55_verify_manifest_gen22_stale.txt', r'ROWS=(\d+)')
# ---- 第四遍桌面探测（`scp` 之前）----
probe = read('evidence/r55_probe.txt')
pkgs = [l.split('\t') for l in probe.splitlines() if l.startswith('DESKTOP\t')]
sync_pkgs = [p for p in pkgs if 'zizhao' in p[1] and 'flash_notice' not in p[1]]
tgt = grab('evidence/r55_probe.txt', r'TARGET_EXISTS=(\w+)')
assert len(sync_pkgs) == 13, 'ABORT: 桌面同步包数 = %d，与叙述里的 13 只不符' % len(sync_pkgs)
new_zip = [p for p in sync_pkgs if 'r54final' in p[1]]
assert len(new_zip) == 1, 'ABORT: 没点到本遍新增在服务器桌面那只包'
_g23_mtime = os.path.getmtime(os.path.join(DST, 'MANIFEST.txt'))
# 第二遍明文复扫的读数（半径分桶两行只取个数；名单本身不进正文）：
_rc2 = 'evidence/r55_cred_recount_2.txt'
inside_n = int(grab(_rc2, r'FETCH_NAME_IN_REPO_INSIDE_SYNC_SCOPE=(\d+)'))
outside_n = int(grab(_rc2, r'FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=(\d+)'))
rc2_hits = grab(_rc2, r'TOTAL_HITS=(\d+)')
rc2_scope = grab(_rc2, r'= (\d+) 只，逐只点名')
rc2_at = grab(_rc2, r'CRED_RECOUNT_AT=(.+)')
rc2_fetch = grab(_rc2, r'字节数=(\d+)')
_pb = 'evidence/r55_parse_check_2.txt'
assert grab(_pb, r'VERDICT=(\S+)') == 'TOOLS_PARSE_CLEAN', 'ABORT: 第二遍工具体检不是 CLEAN'
pb_at = grab(_pb, r'CHKB_AT=(.+)')
pb_targets = grab(_pb, r'SCOPE=本代冻结后被改写的工具 (\d+) 只')
assert rc2_hits == '0' and outside_n == 0, 'ABORT: 第二遍明文复扫不是 CLEAN，先修它再来登记'

# ===================== 编辑 1~2：首行 + 标题里的两套序数 =====================
s = _orig
EDITS = []


def sub1(text, old, new, tag):
    assert text.count(old) == 1, 'ABORT: 锚点在 %s 上命中 %d 次（应 1）' % (tag, text.count(old))
    EDITS.append(tag)
    return text.replace(old, new, 1)


s = sub1(s, 'ht305 十二轮全量同步', 'ht305 十三轮全量同步', 'E1 首行轮数 十二→十三')
s = sub1(s, '（本表到 21，同步表到 12）', '（本表到 24，同步表到 13）', 'E2 标题两套序数 21/12→24/13')

# ===================== 编辑 3：表格补三格（纯插入） =====================
lines = s.split('\n')
i21 = [k for k, l in enumerate(lines) if l.startswith('| 21 | ')]
assert len(i21) == 1, 'ABORT: `| 21 |` 行不唯一'
new_rows = [
    '| 22 | %s（现读载体 `%s` 首行；gen 22 那份 `MANIFEST.txt` 已被 gen 23 覆写 ⇒ 首行时刻**只能从复核载体里取**）'
    ' | **%s / %s B / BOM %s**（现读 `evidence/manifest_gen_log.txt` 的 `...12:34:42` 那一行；本遍门 `%s`：'
    '`FILES_SCANNED=%s` ⇒ 关系式 `%s − 1 = %s` 本代**第三次**实测成立） | '
    '**本代的真读数是一条 `rc=1` 的假红，且假红原件入库、不拿重跑洗绿**（`evidence/r55_verify_manifest_gen22_stale.txt`）。根因不是猜：'
    '`gen_manifest.py` 一次运行里取了**两只** `datetime.now()`（头部 `%s` / 日志行 `%s`），中间隔着 %s 只文件的哈希遍历 '
    '⇒ 跨秒就让 `log_line == exp_log` 这条**精确字符串**等式断裂；同一次 `ROWS=%s / MISMATCH=0 / MISSING=0 / '
    'UNLISTED=0` + 汇总三字段逐项 OK ⇒ 判的却是"清单不是脚本跑出来的"这句最重的话。这条判据自 gen 9 就在，'
    '**只是从未跨到过秒边界** ⇒ 一个 12 世代的潜伏缺陷第一次咬人。两处修法：源头只取一次时刻（`now_full` 单一源，'
    '`now` 由它派生）+ verifier 改按**三个数字字段**判决、时刻只并列展示。**本代不是末版**（后面还有 gen 23 / gen 24） |'
    % (hdr22, 'r55_verify_manifest_gen22_stale.txt', n22, comma(b22), bom22,
       os.path.basename(gate22), fs22, fs22, n22, hdr22, g22[0][0][-8:], n22, rows22),
    '| 23 | %s（现读 `MANIFEST.txt` 首行——它已被 gen 24 取代，本行引的是 `evidence/manifest_gen_log.txt` 的 `...12:37:02` 那一行）'
    ' | **%s / %s B / BOM %s**（本遍门 `%s`：`FILES_SCANNED=%s` ⇒ `%s − 1 = %s` ✓） | '
    '把 gen 22 那两处工具修法冻住：12:36:53 门（两计数仍 0、`VERDICT=CLEAN`）→ 12:37:02 清单 → 复核（**不接管道**）'
    '`rc=0 / VERDICT=MANIFEST_STILL_TRUE / ROWS=%s / MISMATCH=0 / MISSING=0 / UNLISTED=0`。'
    '**⚠ 这一次 `rc=0` 只存在于当次 stdout，盘上没有载体**：12:40:15 起 `evidence/` 又落了 %d 只 ⇒ 拿现在的清单回验 '
    'gen 23 只会给 STALE，该读数**已不可复算**——"读数不落盘等于没跑"那一族在归档链**最后一步**一直开着口子（`gen_manifest.py` '
    '与门早就自带载体，只有 verifier 没有）。本代把口子补上：`verify_manifest.py` 现在自己把终态裁决写进 '
    '`hardware/verify_manifest_<被复核那代时刻>.txt`（一代一只、已存在另起 `_2`）。**落在 `evidence/` 之外是刻意的**：'
    '落在里面就会被下一代清单少记一只、把 `UNLISTED` 顶成非 0，用"我自己的载体"去污染"清单是否仍真"这件正事。'
    '**本代也不是末版** |' % (g23[0][0][-8:], n23, comma(b23), bom23, os.path.basename(gate23), fs23, fs23, n23,
                             n23, 2),
    '| 24 | 末版时刻现读 `MANIFEST.txt` 首行 | 只数现读 `MANIFEST.txt` 的 `TOTAL` 行；判据仍是**关系式不是硬数**：'
    '本遍门 `FILES_SCANNED` − 1 == `TOTAL` | 把 gen 23 之后的四类字节冻住：**① 两遍补扫**（`scripts/r55_cred_recount.py`'
    ' 改半径分桶 + 其载体 `evidence/r55_cred_recount_2.txt`；`scripts/chk_r55b.py` 新增 + 载体 `evidence/r55_parse_check_2.txt`'
    ' —— 第一遍 `chk_r55.ps1` 只覆盖了 `r55_upload.ps1` 一只，本代 12:37 之后改写的 3 只工具**当时无人解析过**就要进下一代清单）；'
    '**② 工具再修两处**（`gen_manifest.py` 头部两句共用同一时刻；`verify_manifest.py` 自带终态载体 + `ROWS=0` 拒裁 + '
    '载体名 10 位数字断言）；**③ 归档目录之外那只终态载体** `hardware/verify_manifest_*.txt`（按 gen 23 那格的口径'
    '**不进本清单**）；**④ 本 README 这四格** + 首行"十三轮" + 标题"本表到 24，同步表到 13" + `zsynctest15` + 第四遍桌面探测。'
    '**本行之后本文件不再编辑**，否则本代又非末版（gen 16→17→18→19→20→21 那条链的第 7 次）。'
    '判据：`verify_manifest.py` `rc=0` + `MISMATCH=0 / MISSING=0 / UNLISTED=0` **且它在 `hardware/` 下自落的那只载体存在**'
    '（两样都要，只有 stdout 不算） |',
]
assert all('\r' not in r for r in new_rows)
lines[i21[0] + 1:i21[0] + 1] = new_rows
s = '\n'.join(lines)
EDITS.append('E3 表格补 3 格（gen 22/23/24，纯插入）')

# ===================== 编辑 4：叙述段补两段（纯插入，锚在 gen 12 段之前） =====================
lines = s.split('\n')
igt = [k for k, l in enumerate(lines) if l.startswith('gen 12（09-24）同样跑了不止一遍')]
assert len(igt) == 1, 'ABORT: `gen 12（09-24）` 那一段不唯一'
narr = [
    'gen 22（09-24 %s 清单，即日志行 %s 那一遍）是**假红那一遍**：门 `FILES_SCANNED=%s` → 清单 `TOTAL=%s`'
    '（关系式仍 ✓）→ `verify_manifest.py` 给 `rc=1 / VERDICT=MANIFEST_STALE`，而它同一行里 `MISMATCH=MISSING=UNLISTED=0`、'
    '汇总三字段逐项 `OK`。⇒ **判据的"红"必须能翻译成一件具体的事**，这次红的是"日志与清单不同代"，而真事是'
    '"一次运行里取了两次时刻"。修法分两头：`gen_manifest.py` 只取一次 `now_full` 并由它派生 `now`（同源 ⇒ 相等由构造成立，'
    '不再靠运气不落秒边界）；verifier 把**判决**与**展示**分家（数字三字段进判据，时刻并列打印不参与）。'
    '原件 = `evidence/r55_verify_manifest_gen22_stale.txt`（%s B，不重跑洗绿）。' % (
        hdr22, g22[0][0], fs22, n22,
        os.path.getsize(os.path.join(EV, 'r55_verify_manifest_gen22_stale.txt'))),
    'gen 23（09-24 %s 清单）是**跑通了却没留证据那一遍**：12:36:53 门（`FILES_SCANNED=%s`）→ %s 清单 `TOTAL=%s` → '
    '复核 `rc=0 / MANIFEST_STILL_TRUE`。这三行数字现在全部可复算（`evidence/manifest_gen_log.txt` + 那只门输出），'
    '**唯独 `rc=0` 不能**——它当年只在 stdout 上活过一次。⇒ 本代起 verifier 自己落终态载体（首跑实测：'
    '12:46 那遍对 gen 23 的清单给 `rc=1`，正是这条"已不可复算"的物证，载体 `hardware/verify_manifest_%s.txt`）。'
    '**清单之后盘上又动了 %d 只 `evidence/`**（按 mtime 现算，> %s），这就是"快照"两个字要付的账。' % (
        g23[0][0][-8:], fs23, g23[0][0][-8:], n23, ''.join(c for c in g23[0][0] if c.isdigit())[:10],
        sum(1 for f in os.listdir(EV)
            if os.path.isfile(os.path.join(EV, f))
            and os.path.getmtime(os.path.join(EV, f)) > _g23_mtime),
        g23[0][0]),
]
lines[igt[0]:igt[0]] = narr
s = '\n'.join(lines)
EDITS.append('E4 叙述段补 2 段（gen 22/23，纯插入）')

# ===================== 编辑 5："本代没做"那一条：①④ 已补执行者、⑤⑥ 新账 =====================
old_bullet = [l for l in s.split('\n') if l.startswith('  - 本代**没做**的（点名，不写成豁免句）')]
assert len(old_bullet) == 1, 'ABORT: "本代没做的"那一条不唯一（找到 %d 只）' % len(old_bullet)
new_bullet = (
    '  - 本代**没做 / 一度没做又补上**的（逐条点名，不写成豁免句）：'
    '① "逐只明文复扫 + 抓回件文件名有没有漏进仓库"这两步**一度只剩义务**（旧落地器顺手做的那两件事随 §38.18 一起消失了）'
    '⇒ 本代由 `scripts/r55_cred_recount.py` 补上执行者：%s 的载体 `evidence/r55_cred_recount_2.txt` 给 '
    '`TOTAL_HITS=%s`（%s 只逐只点名、不截断）+ 内存阳性对照 `POSITIVE_CONTROL_IN_MEMORY_HITS=1` + '
    '`FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=%d` ⇒ `VERDICT=CLEAN` / `rc=0`；**首跑那遍口径写错**'
    '（把"声明该名的脚本自己"静默排除 = 造一把看不见的尺），原件 `evidence/r55_cred_recount.txt` 留在盘上、'
    '由新载体的 `PRIOR_ATTEMPT` 行点名它。'
    '② 没有新建备份根（`diff -rq` 判据本轮未复跑）⇒ **仍是义务**。'
    '③ 没有碰串口、没有烧录、屏侧零进展 ⇒ **仍是义务**（12:14:51 那遍 COM14 缺席在册）。'
    '④ `%%TEMP%%` 里那只 %s B 的抓回件（带明文）**仍在**，本会话一律不删；它在仓库外，'
    '而"它的**文件名**有没有被写进仓库"本代**已现跑**：同步目录内 %d 只按构造合法（声明它的脚本 + 打印它的取证载体），'
    '目录外 %d 只 ⇒ 不静默排除任何一只，改按**半径**判决（第一版那个"排除自己"的做法已随 `PRIOR_ATTEMPT` 一起留档）。'
    '⑤ gen 23 的终态复核 `rc=0` **没有载体 ⇒ 已不可复算**，这一格就是它的讣告；口子由 `verify_manifest.py` '
    '自带载体封住（见"清单世代"gen 23 那格）。'
    '⑥ 第一遍编码体检（`chk_r55.ps1`）只覆盖 `r55_upload.ps1` 一只，而本代在 gen 23 之后真改了 %s 只 `.py` 工具 ⇒ '
    '由 `scripts/chk_r55b.py` 补第二遍（%s `VERDICT=TOOLS_PARSE_CLEAN`，阳性对照 = 同一把尺在已知坏字符串上抛 `SyntaxError`）。'
    % (rc2_at, rc2_hits, rc2_scope, outside_n, rc2_fetch, inside_n, outside_n, pb_targets, pb_at))
s = s.replace(old_bullet[0], new_bullet, 1)
EDITS.append('E5 改写"本代没做"那一条（1 行换 1 行）')

# ===================== 编辑 6：远端清理那条 —— 轮数 / 最新一代 / 第四遍探测 =====================
s = sub1(s, '- **没做**远端清理：**十二轮**同步在服务器上留下的包与解包根',
         '- **没做**远端清理：**十三轮**同步在服务器上留下的包与解包根', 'E6a 远端清理那句的轮数')
s = sub1(s, '最新一代 = `zsynctest14`（第 12 代那只；`zsynctest11`~`zsynctest14` 是第 9~12 代的，四代解包根都留在服务器上、一根只喂一代）',
         '最新一代 = `zsynctest15`（第 13 代那只；`zsynctest11`~`zsynctest15` 是第 9~13 代的，五代解包根都留在服务器上、一根只喂一代）',
         'E6b 最新一代解包根 zsynctest14→15')
probe_anchor = '读数在 `evidence/r54_probe.txt` ⇒ **仍一只都没删**】，'
fourth = ('读数在 `evidence/r54_probe.txt` ⇒ **仍一只都没删**】⇒【09-24 **12:25:29~12:25:33 第 13 代 `scp` 之前**'
          '同口径四探：桌面同步包已并存 **13 只** = 上面那只 tar.gz + **12 只 zip**（`zizhao_sync_20260923_r43.zip`'
          ' 1,117,960 B 与 `r44final`~`r54final` 十一只，本遍新落的那只 = `zizhao_20260924_r54final.zip` **%s B**'
          ' ⇒ 与三探那次"12 只"差**恰好 1 只**，因为第 13 代包那一刻还在本机），同批 `TARGET_EXISTS=%s`'
          '（本代目标包 `zizhao_20260924_r55final.zip` 那一刻还没上去），读数在 `evidence/r55_probe.txt`'
          ' ⇒ **仍一只都没删**】，') % (comma(new_zip[0][2]), tgt)
s = sub1(s, probe_anchor, fourth, 'E6c 第四遍桌面探测（纯插入一段）')

# ===================== 写盘前体检 =====================
assert '\r' not in s, 'ABORT: 落地后文本含 CR'
o_lines, n_lines = _orig.split('\n'), s.split('\n')
assert len(n_lines) - len(o_lines) == len(new_rows) + len(narr), \
    'ABORT: 行数差 = %d，与预期插入 %d 不符 ⇒ 有结构被静默删掉' % (
        len(n_lines) - len(o_lines), len(new_rows) + len(narr))
tbl_o = sum(1 for l in o_lines if l.startswith('| '))
tbl_n = sum(1 for l in n_lines if l.startswith('| '))
assert tbl_n - tbl_o == len(new_rows), 'ABORT: 表格行 %d → %d，只应 +3' % (tbl_o, tbl_n)
for gone in ['十二轮', '本表到 21，同步表到 12', '最新一代 = `zsynctest14`', '记为 gen 之后第一笔义务',
             '`FETCH_NAME_LEAKED_INTO_REPO` 本代未现跑']:
    assert gone not in s, 'ABORT: 过期读数 %r 仍在正文' % gone
md5_o = hashlib.md5(_orig.encode('utf-8')).hexdigest()
open(RM, 'w', encoding='utf-8', newline='').write(s)

# ===================== 写盘后独立回读 =====================
back = open(RM, encoding='utf-8').read()
assert back == s and hashlib.md5(back.encode('utf-8')).hexdigest() == hashlib.md5(s.encode('utf-8')).hexdigest()
assert sum(1 for l in back.split('\n') if l.startswith('| 22 | ')) == 1
assert sum(1 for l in back.split('\n') if l.startswith('| 23 | ')) == 1
assert sum(1 for l in back.split('\n') if l.startswith('| 24 | ')) == 1
cands = ['r55_land_readme_2.txt'] + ['r55_land_readme_2_%d.txt' % i for i in range(3, 11)]
OUT = next((os.path.join(EV, c) for c in cands if not os.path.isfile(os.path.join(EV, c))), None)
assert OUT, 'ABORT: 落地器载体名全被占'
txt = '\n'.join([
    'LAND_README2_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'PRIOR=evidence/r55_land_readme.txt（第一遍：只登记 gen 20/21 与第 13 代同步读数）',
    'EDITS=%d 项：%s' % (len(EDITS), ' / '.join(EDITS)),
    'NUMBERS_SOURCE=genlog(%s,%s) + gates(%s,%s) + probe(r55) + local(r55) 全部现读，无手写数' % (
        n22, n23, fs22, fs23),
    'README_BEFORE_BYTES=%d md5:%s' % (len(_orig.encode('utf-8')), md5_o),
    'README_AFTER_BYTES=%d md5:%s' % (len(back.encode('utf-8')),
                                      hashlib.md5(back.encode('utf-8')).hexdigest()),
    'LINES=%d -> %d（+%d 行，全部是插入；表格行 %d -> %d）' % (
        len(o_lines), len(n_lines), len(n_lines) - len(o_lines), tbl_o, tbl_n),
    'PURE_INSERT_PROOF=行数差 == 插入行数 ∧ 表格行差 == 3 ∧ 五处过期读数均已消失',
    'VERDICT=LANDED_README2',
]) + '\n'
open(OUT, 'w', encoding='utf-8', newline='').write(txt)
sys.stdout.reconfigure(encoding='utf-8')
print(txt)
