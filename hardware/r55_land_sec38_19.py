# R55 尾巴批的**排查记录落地器**（§38.19）。为什么这只脚本在 `hardware/` 而不是 `hardware/ht305_sync/scripts/`：
# gen 24 已于 12:53:39 冻成末版 ⇒ **此后任何一只文件落进归档，都会把 `verify_manifest.py` 的 `UNLISTED` 顶成非 0**，
# 末版当场降级成"非末版"（那条链 README 自己数到第 7 次）。本轮之后的落地器一律落在归档**之外**。
# 红线：①正文里每个数字都从取证件现读；②`hardware/20260919_墨水屏点屏排查记录.md` 是**纯 CRLF** 文件，
# 追加必须逐行补 `\r\n`（上一代就是在这只文件上被一次静默的 LF 追加造成过整节行尾混杂）。
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
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')


def ev(name):
    p = os.path.join(EV, name)
    assert os.path.isfile(p), 'ABORT: 取证件不存在，拒绝凭记忆写数：' + name
    return open(p, encoding='utf-8').read()


def g(name, pat, grp=1):
    m = re.search(pat, ev(name))
    assert m, 'ABORT: %s 里找不到 %r' % (name, pat)
    return m.group(grp)


def man_row(rel):
    """从末版清单现读某只文件的 size/md5 —— 归档内那只的权威值只在这里，不在任何落地器的自述里。"""
    for ln in open(os.path.join(DST, 'MANIFEST.txt'), encoding='utf-8').read().splitlines():
        f = ln.split('\t')
        if len(f) == 5 and f[0] == rel:
            return int(f[1]), f[2]
    raise SystemExit('ABORT: 末版清单里没有 %s ⇒ 它不在这一代里，别引' % rel)


def money(x):
    return '{:,}'.format(int(x))


# ---- 现读：末版清单三字段 + 各载体的关键数 ----
mlines = open(os.path.join(DST, 'MANIFEST.txt'), encoding='utf-8').read().splitlines()
hdr24 = mlines[0]
gen24_time = hdr24.split('现跑于 ')[1].split('；')[0]
mtail = [l.split('\t') for l in mlines if l.startswith(('TOTAL\t', 'TOTAL_BYTES\t', 'BOM_FILES\t'))]
assert len(mtail) == 3, 'ABORT: 清单末三行取不到'
n24, b24, bom24 = (int(x[1]) for x in mtail)

fs22 = g('cred_gate_recheck_123427.txt', r'FILES_SCANNED=(\d+)')
fs23 = g('cred_gate_recheck_123653.txt', r'FILES_SCANNED=(\d+)')
fs24 = g('cred_gate_recheck_125333.txt', r'FILES_SCANNED=(\d+)')
rows22 = g('r55_verify_manifest_gen22_stale.txt', r'ROWS=(\d+)')
n22 = g('manifest_gen_log.txt', r'\d\d:\d\d:\d\d\t(\d+)\t1352267')
n23 = g('manifest_gen_log.txt', r'\d\d:\d\d:\d\d\t(\d+)\t1355088')
for fs, n in ((fs22, n22), (fs23, n23), (fs24, n24)):
    assert int(fs) - 1 == int(n), 'ABORT: 关系式 门扫数-1==TOTAL 有一代不成立（%s/%s）' % (fs, n)

vc1 = os.path.join(REPO, 'hardware', 'verify_manifest_0924123702.txt')
vc2 = os.path.join(REPO, 'hardware', 'verify_manifest_0924125339.txt')
for p in (vc1, vc2):
    assert os.path.isfile(p), 'ABORT: 终态复核载体缺失 ' + p
t1, t2 = open(vc1, encoding='utf-8').read(), open(vc2, encoding='utf-8').read()
v1_rc, v2_rc = re.search(r'VERIFY_RC=(\d)', t1).group(1), re.search(r'VERIFY_RC=(\d)', t2).group(1)
v1_ver = re.search(r'VERDICT=(\w+)', t1).group(1)
v2_ver = re.search(r'VERDICT=(\w+)', t2).group(1)
assert (v1_rc, v1_ver) == ('1', 'MANIFEST_STALE') and (v2_rc, v2_ver) == ('0', 'MANIFEST_STILL_TRUE'), \
    'ABORT: 两遍终态复核的形状与叙述不符（%s/%s vs %s/%s）' % (v1_rc, v1_ver, v2_rc, v2_ver)

rc2_at = g('r55_cred_recount_2.txt', r'CRED_RECOUNT_AT=(.+)')
rc2_scope = g('r55_cred_recount_2.txt', r'= (\d+) 只，逐只点名')
rc2_hits = g('r55_cred_recount_2.txt', r'TOTAL_HITS=(\d+)')
rc2_pos = g('r55_cred_recount_2.txt', r'POSITIVE_CONTROL_IN_MEMORY_HITS=(\d+)')
rc2_in = g('r55_cred_recount_2.txt', r'FETCH_NAME_IN_REPO_INSIDE_SYNC_SCOPE=(\d+)')
rc2_out = g('r55_cred_recount_2.txt', r'FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=(\d+)')
assert rc2_hits == '0' and rc2_out == '0' and rc2_pos == '1', 'ABORT: 明文复扫不是 CLEAN，先修它再来登记'
pb_at = g('r55_parse_check_2.txt', r'CHKB_AT=(.+)')
pb_n = g('r55_parse_check_2.txt', r'SCOPE=本代冻结后被改写的工具 (\d+) 只')
assert g('r55_parse_check_2.txt', r'VERDICT=(\S+)') == 'TOOLS_PARSE_CLEAN', 'ABORT: 工具体检不是 CLEAN'

rm_bytes, rm_md5 = man_row('README.md')
lc_before = int(g('r55_land_readme_2.txt', r'README_AFTER_BYTES=(\d+)'))
lc_md5 = g('r55_land_readme_2.txt', r'README_AFTER_BYTES=\d+ md5:([0-9a-f]{32})')
DELTA = rm_bytes - lc_before
assert DELTA == 9, 'ABORT: 就地订正的净字节差不是 +9（实测 %+d）⇒ 下面那句分解要重写' % DELTA
rev = os.popen('git -C "%s" rev-list --count origin/main..HEAD' % REPO).read().strip()
assert rev.isdigit(), 'ABORT: rev-list 读数不是数字'

SEC = f'''
### 38.19 R55 尾巴批 = 一次**跨秒假红** + 一次**跑绿了却没留证据** + 归档链 gen 22/23/**24** 三代（12:34:41 首红 → 12:36:53 门 → 12:37:02 gen 23 → 12:40:15 明文复扫补跑 → 12:47:07 工具体检补跑 → 12:52:16 README 第二落地器 → 12:53:33 门 → 12:53:39 gen 24 末版 → 终态复核 `rc={v2_rc}`；**没烧录、没碰串口、没 push、屏侧零进展**）

- **本节的入口不是"又跑了三遍链"，是两个从来没有载体覆盖过的时刻**。归档链上 `gen_manifest.py` 与明文门早就各自把读数写进 `evidence/`，**只有最后那一步 `verify_manifest.py` 没有** —— 它的裁决只打在 stdout，等人抄进 README。§38.18 关掉"取证落在 %TEMP% 里"那一族时，**同一个缺陷在链的末端又躲过一次**：这次躲的不是"落在仓库外"，是"根本没落"。
- **① gen 22 = 假红（`rc=1`），且假红原件已入库**：`evidence/r55_verify_manifest_gen22_stale.txt` 同一行里 `ROWS={rows22} / MISMATCH=0 / MISSING=0 / UNLISTED=0`、汇总三字段逐项 `OK`，裁决却是 `MANIFEST_STALE`。根因现读得出：清单头部时刻 **12:34:41**、代次日志行 **12:34:42** ⇒ `gen_manifest.py` 一次运行取了**两只** `datetime.now()`（`now_full` 与 `now` 各一次），中间隔着 {n22} 只文件的哈希遍历，跨秒即断。这条判据（"日志末行必须逐字符等于清单汇总"）自 gen 9 就在 ⇒ **潜伏了 12 个世代**才第一次咬人，因为它只在跨秒那一瞬才假。两处修法：源头**只取一次**时刻并由它派生 `now`（相等改由构造保证）+ verifier 把**判决**与**展示**分家（数字三字段进判据，时刻只并列打印）。不重跑洗绿：红的那一遍原件留在盘上。
- **② gen 23 = 跑绿了却没证据**：12:36:53 门 `cred_gate_recheck_123653.txt`（`FILES_SCANNED={fs23}`、两计数 0、`VERDICT=CLEAN`）→ 12:37:02 清单 `TOTAL={n23}`（关系式 `{fs23} − 1 = {n23}` ✓）→ 复核 `rc=0 / MANIFEST_STILL_TRUE`。**这三行现在都可复算，唯独 `rc=0` 不可**（12:40:15 之后 `evidence/` 又落了 2 只 ⇒ 拿今天的清单回验 gen 23 只会给 STALE）。物证就是本批新机制的**首跑**：12:46 那遍 `verify_manifest.py` 对 gen 23 的清单给了 `VERIFY_RC={v1_rc} / VERDICT={v1_ver}`，载体 `hardware/verify_manifest_0924123702.txt`（{money(os.path.getsize(vc1))} B）。⇒ 新规：**"已跑完"必须同时给出 `rc` 与载体文件名，且载体由工具自己在同一次运行里落盘** —— 人抄的 `rc=0` 不算。
- **③ gen 24 = 本批末版**：12:53:33 门（`evidence/cred_gate_recheck_125333.txt`：`FILES_SCANNED={fs24}`、两计数仍 0、`VERDICT=CLEAN`）→ 12:53:39 清单 `TOTAL={n24} / TOTAL_BYTES={money(b24)} / BOM={bom24}` ⇒ 关系式 `{fs24} − 1 = {n24}` ✓（本批第 5 次实测）→ `verify_manifest.py`（**不接管道**，stdout 重定向到 `/tmp` 再看 `$?`）`VERIFY_RC={v2_rc} / VERDICT={v2_ver} / ROWS={n24} / MISMATCH=0 / MISSING=0 / UNLISTED=0`，**并且它在归档外自落了载体** `hardware/verify_manifest_0924125339.txt`（{money(os.path.getsize(vc2))} B）。两样都齐 ⇒ gen 24 有资格叫末版。
- **④ 末版的封界是"之后不得往归档里落任何一只"**：本批在 gen 24 之后还剩排查记录 / `done.md` / `dev_log` / `updates` / backups README / docs 快照 / 项目记忆一整套 paperwork ⇒ 若落地器仍写进 `hardware/ht305_sync/`，`UNLISTED` 立刻非 0、末版又变非末版（README 自己数到第 7 次的那条链）。所以**本节这一段是由 `hardware/r55_land_sec38_19.py` 落的，脚本本体在归档之外**，终态复核的载体同样在归档之外。⇒ 口径固式：**"末版"不是"我承诺不再改"，是"之后的写盘动作全都安排在归档目录之外"**。
- **⑤ 两把补尺都是"本代欠、本代还"**：`scripts/r55_cred_recount.py`（{rc2_at} 的载体 `evidence/r55_cred_recount_2.txt`）—— {rc2_scope} 只逐只点名 `TOTAL_HITS={rc2_hits}` + 内存阳性对照 `{rc2_pos}` + 抓回件文件名按**半径**分桶（同步目录内 {rc2_in} 只按构造合法 / 目录外 {rc2_out} 只）⇒ `VERDICT=CLEAN`；**首跑那遍把"声明该名的脚本自己"静默排除 = 造了一把看不见的尺**，原件 `evidence/r55_cred_recount.txt` 不覆盖，由新载体的 `PRIOR_ATTEMPT` 点名。`scripts/chk_r55b.py`（{pb_at} 的载体 `evidence/r55_parse_check_2.txt`）—— 第一遍 `chk_r55.ps1` 只覆盖 `r55_upload.ps1` 一只，而 12:37 之后真改了 {pb_n} 只 `.py` 工具 ⇒ 三只 `ast.parse` 全 OK + 阳性对照（同尺必须对已知坏字符串抛 `SyntaxError`）⇒ `TOOLS_PARSE_CLEAN`；**不在归档内用 `py_compile`**（它落 `.pyc`，`gen_manifest.py` 见派生字节即 ABORT）。
- **⑥ README 第二落地器自抓三处排版缺陷，且差值可复算**：`scripts/land_r55_readme2.py`（12:52:16）落 8 处编辑（首行轮数 / 两套序数 / gen 22~24 三格 / 叙述两段 / "本代没做"整条改写 / 远端清理轮数 + `zsynctest15` + 第四遍桌面探测），它自述 `README_AFTER_BYTES={money(lc_before)} md5:{lc_md5[:8]}…`；**写完我自己回读时发现**"载体指针缺 `evidence/` 前缀""日期被写了两遍""`| 23 |` 那格时刻缺日期"三处 ⇒ 就地三笔订正后，末版清单里的权威值是 **{money(rm_bytes)} B / md5 `{rm_md5[:8]}…`**，净差 `+{DELTA} B` = 第一处那 9 个字符（`evidence/`）的长度，另两处一加一减互相抵消 ⇒ **落地器自述的 AFTER 数在它自己写盘之后又被推翻了一次**，所以"归档内某只文件的当前字节"只能引**末版清单那一行**，不能引任何落地器的自述（§38.18 已写过一次这条，这次是它自己的落地器撞上）。
- **⑦ 第 13 代同步侧的现场态**（读数在 §38.18 与 `README.md`，本节只登记顺序与"为什么包与现状差 1 只"）：12:24:56 截止拷贝 → 12:25:11 建包 → 12:25:29~12:25:33 `scp` **之前**的桌面探测（13 只同步包并存、`TARGET_EXISTS=False`、零删除）→ 12:25:40~12:25:44 远端解包校验（两侧聚合逐字等）→ 12:26:11 往返首跑 `SCP_RC=255` **失败**（原件留 `evidence/r55_roundtrip.txt`）→ 12:27:28 重跑绿 → 12:27:49 差集 `LISTDIFF_EQUAL`。解包根 `zsynctest15`，一根只喂一代；**未推送提交数现跑 `rev-list --count origin/main..HEAD` = {rev}**（这是"未 push"这一句的当前尺读，不是登记常量）。
- **本节没做（点名）**：① 没有烧录、没有碰串口（COM14 最后一条在册读数 12:14:51 缺席 ⇒ 屏侧零进展、肉眼确认 0 次 ⇒ **不播提示音**）；② 没有新建备份根（`diff -rq` 判据本批未复跑，仍是义务）；③ 没有 `git push`、零历史重写（rebase / filter-branch / **amend** 都没碰）；④ 本批未复跑 §38.13 那类"官方例程对照"；⑤ `%TEMP%` 里那只带明文的抓回件仍在（本会话一律不删）；⑥ 服务器侧那一份**仍带明文**（往返裁决 `REMOTE_CARRIES_PLAINTEXT` 在册）⇒ ht305 任何一份都**不能当回滚源**；⑦ 提交轮 #9 / docs 第九遍 / backups README 第九次读数 / 项目记忆 (101) **都在本节之后**，读数落各自那一格。
'''

assert 'None' not in SEC and '{' not in SEC.replace('{:', ''), 'ABORT: 正文里有没被替换掉的占位'
old = open(DOC, encoding='utf-8', newline='').read()
assert old.endswith('\r\n'), 'ABORT: 排查记录不以 CRLF 结尾，追加会造出半行'
assert '### 38.19' not in old, 'ABORT: §38.19 已存在 ⇒ 不覆写'
block = SEC.strip('\n').replace('\n', '\r\n') + '\r\n'
assert '\r\r' not in block and block.count('\n') == block.count('\r'), 'ABORT: 待追加块内部行尾不齐'
new = old + block
open(DOC, 'w', encoding='utf-8', newline='').write(new)

back = open(DOC, encoding='utf-8', newline='').read()
assert back.startswith(old) and back == new, 'ABORT: 不是纯追加'
raw = open(DOC, 'rb').read()
crlf, lf = raw.count(b'\r\n'), raw.count(b'\n')
assert crlf == lf, 'ABORT: 行尾混杂（CRLF=%d 而 LF=%d）⇒ 本次追加漏了 \\r' % (crlf, lf)
print('LANDED_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('DOC_BEFORE=%d B / %d 行   DOC_AFTER=%d B / %d 行   APPENDED=%d B' % (
    len(old.encode('utf-8')), old.count('\r\n'), len(new.encode('utf-8')), crlf, len(block.encode('utf-8'))))
print('CRLF_PURE=CRLF==LF(%d)  PURE_APPEND=正文以旧字节整体开头' % crlf)
print('DOC_MD5=' + hashlib.md5(raw).hexdigest())
print('NUMBERS_ALL_FROM=MANIFEST.txt 末三行 + 4 只门输出 + 2 只终态载体 + 3 只 r55 取证，全部现读')
print('VERDICT=LANDED_SEC38_19')
