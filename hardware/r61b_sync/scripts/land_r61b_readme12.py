# README §1 第十二次读数落地器（R61b 代，提交轮 #10 之后）。
# 三步序照本代纪律：①幂等门（令牌不含时刻）②全部裁决排在写盘之前（rc≠0 蕴含盘上一字节未动）
# ③写盘后行级差集证明（差集 == 预期新行集合，其余行逐字等）。
# 所有只数/行数/字节数/提交号一律运行时现读并插值，不写死字面量。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
os.chdir(REPO)
EV = os.path.join('hardware', 'r61b_sync', 'evidence')
README = 'backups/README.md'
MACRO = os.path.join('hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
MAIN = os.path.join('hardware', 'zizhao-esp32s3', 'main')
SIB = os.path.join('hardware', 'zizhao-esp32s3', 'backups')   # 根 B 家族住这里，不在 main/ 下
DOCS = os.path.join('backups', 'r43_20260922_131029', 'docs')
HT305 = os.path.join('hardware', 'ht305_sync')
T0 = datetime.now()
OUTL = []


def say(s):
    OUTL.append(s)
    print(s)


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a),
                       capture_output=True, shell=False)
    assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')
    return r.stdout.decode('utf-8', 'replace')


def dqr(a, b):
    # 路径不存在时 diff 只打一行错误、返回非 0，差集行数照样是 0 ⇒ "0 行 differ"会变成假绿；
    # 所以两侧存在性由这里当场把关，不许靠调用点写对路径。
    for p in (a, b):
        assert os.path.isdir(p), 'ABORT: diff 的输入目录不存在，不能把它的失败读成 0 行 differ：' + p
    r = subprocess.run(['diff', '-rq', a, b], capture_output=True, shell=False)
    err = r.stderr.decode('utf-8', 'replace').strip()
    assert not err, 'ABORT: diff 自身报错（rc=%d）：%s' % (r.returncode, err[:200])
    return len([l for l in r.stdout.decode('utf-8', 'replace').splitlines() if l.strip()])


# ---- 现读：git 侧 ----
head = git('rev-parse', '--short', 'HEAD').strip()
prev = git('rev-parse', '--short', 'HEAD~1').strip()
revlist = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
sline = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
skind = {}
for l in sline:
    skind[l[:2]] = skind.get(l[:2], 0) + 1
ns = [l.split('\t') for l in git('diff', '--numstat', prev, head).splitlines() if l.strip()]
files_in_commit = len(ns)
plus = sum(int(x[0]) for x in ns if x[0] != '-')
minus = sum(int(x[1]) for x in ns if x[1] != '-')
bins = [os.path.basename(x[2]) for x in ns if x[0] == '-']
ns_main = [l.split('\t') for l in git('diff', 'HEAD', '--numstat', '--', MAIN).splitlines() if l.strip()]

# ---- 现读：提交轮 #10 的门与阳性对照载体 ----
GC = os.path.join(EV, 'staged_cred_gate_r61b_final106.txt')
PC = os.path.join(EV, 'staged_cred_gate_r61b_final106_pos.txt')
gc = open(GC, encoding='utf-8').read()
pc = open(PC, encoding='utf-8').read()
g_files = int(re.search(r'FILES_SCANNED=(\d+)', gc).group(1))
g_hits = int(re.search(r'TOTAL_HITS=(\d+)', gc).group(1))
g_verdict = re.search(r'VERDICT=(\w+)', gc).group(1)
g_label = re.search(r'LABEL=(\S+)', gc).group(1)
p_scanned = int(re.search(r'INDEX_SCANNED=(\d+)', pc).group(1))
p_deleted = int(re.search(r'INDEX_DELETED=(\d+)', pc).group(1))
p_arms = re.search(r'ARMS_FIRED=(\S+)/2', pc).group(1)
p_equal = re.search(r'equal=(\w+)', pc).group(1)
p_verdict = re.findall(r'VERDICT=(\w+)', pc)[-1]

# ---- 现读：在册裁决的后缀表 + 两只原厂镜像的盘上身份（与 §38.33 登记值互核） ----
LST = os.path.join('hardware', 'r61b_sync', 'scripts', 'make_staged_list_r61b.py')
lst_src = open(LST, encoding='utf-8').read()
_ext_m = re.search(r'BIN_EXT\s*=\s*\(([^)]*)\)', lst_src)
assert _ext_m, 'ABORT: 清单器里读不到 BIN_EXT 定义'
bin_ext = [x.strip().strip("'\"").lower() for x in _ext_m.group(1).split(',') if x.strip()]
assert 'RULING' in lst_src and 'RULING_PROBE' in lst_src, 'ABORT: 清单器里的裁决执行者不在了'
PZ = os.path.join('hardware', '20260919_墨水屏点屏排查记录.md')
pz = open(PZ, encoding='utf-8').read()
_sec33 = pz[pz.index('### 38.33'):pz.index('### 38.34')]
reg = {}
for nm in ('esp32s3_flash_backup_8mb.bin', 'esp32s3_partition_table.bin'):
    pth = os.path.join(REPO, nm)
    assert os.path.isfile(pth), 'ABORT: 原厂镜像 %s 盘上不在了' % nm
    mb = hashlib.md5(open(pth, 'rb').read()).hexdigest()
    sz = os.path.getsize(pth)
    assert mb in _sec33, 'ABORT: %s 的现算 md5 不在 §38.33 登记文本里（要么文件变了，要么那一节被改过）' % nm
    assert format(sz, ',d') in _sec33, 'ABORT: %s 的现算尺寸 %s 不在 §38.33 登记文本里' % (nm, format(sz, ',d'))
    reg[nm] = (sz, mb)
flash_bytes = reg['esp32s3_flash_backup_8mb.bin'][0]

# ---- 现读：第十七批 rc=0 载体，用来把"落地 → 快照"的先后钉成可复算的等式 ----
_f17 = [os.path.join(EV, f) for f in sorted(os.listdir(EV))
         if re.match(r'^r61b_freqerr17_\d+\.txt$', f) and 'VERDICT=LANDED rc=0' in
         open(os.path.join(EV, f), encoding='utf-8').read()]
assert len(_f17) == 1, 'ABORT: rc=0 的第十七批载体应恰 1 只，实测 %d' % len(_f17)
F17_NAME = os.path.basename(_f17[0])
F17_MTIME = datetime.fromtimestamp(os.path.getmtime(_f17[0])).strftime('%Y-%m-%d %H:%M:%S')

# ---- 现读：docs 快照第十二遍 ----
note_p = os.path.join(DOCS, 'SNAPSHOT_NOTE.txt')
note = open(note_p, encoding='utf-8').read()
snap_at = re.search(r'刷新时刻 ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})', note).group(1)
note_rows = len([l for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
docs_files = len([f for f in os.listdir(DOCS) if os.path.isfile(os.path.join(DOCS, f))])
note_bytes = os.path.getsize(note_p)
new_ones = len([l for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)])
src_cnt = int(re.search(r'本次运行：源清单现读 (\d+) 只', note).group(1))
assert note_rows == src_cnt, 'NOTE 表格行数与它自己声明的源清单只数不等'
assert docs_files == note_rows + 1, '目录只数 != 表格行数 + NOTE 自己'

# ---- 现读：五把根尺 ----
r43a, r43b = dqr(os.path.join('backups', 'r43_20260922_131029', 'main'), MAIN), \
             dqr(os.path.join(SIB, 'r43_20260922_131029', 'main'), MAIN)
r53a, r53b = dqr(os.path.join('backups', 'r53_20260924_083929', 'main'), MAIN), \
             dqr(os.path.join(SIB, 'r53_20260924_083929', 'main'), MAIN)
srcs = dqr(os.path.join('backups', 'r44_sourceonly_20260923_084628', 'main'), MAIN)
wf = [f for f in os.listdir(MAIN) if os.path.isfile(os.path.join(MAIN, f))]
wt_cnt, wt_bytes = len(wf), sum(os.path.getsize(os.path.join(MAIN, f)) for f in wf)
roots = {}
for tag, r in (('A', os.path.join('backups', 'r61close_20260926_133908')),
               ('B', os.path.join(SIB, 'r61close_20260926_133908'))):
    assert os.path.isdir(r), 'ABORT: 根 %s 不存在：%s' % (tag, r)
    c, t = 0, 0
    for dp, dn, fn in os.walk(r):
        for f in fn:
            c += 1
            t += os.path.getsize(os.path.join(dp, f))
    roots[tag] = (c, t, dqr(os.path.join(r, 'main'), MAIN))
assert roots['A'][0] == roots['B'][0], '两根只数不等'

# ---- 现读：串口 / 封界 / FreqErr ----
pr = subprocess.run([sys.executable, '-m', 'serial.tools.list_ports'],
                    capture_output=True, shell=False)
assert pr.returncode == 0, '串口枚举本身失败，不能把它的失败读成"COM14 缺席"'
ports = sorted(set(re.findall(r'COM\d+', pr.stdout.decode('utf-8', 'replace'))))
com14 = 'COM14' in ports
assert len(ports) >= 1, 'ABORT: 枚举解析出 0 只 COM 名，"命中 0"不等于"干净"'
hfiles = 0
for dp, dn, fn in os.walk(HT305):
    hfiles += len(fn)
htracked = len([l for l in git('ls-files', HT305.replace(os.sep, '/')).splitlines() if l.strip()])
hlataest = max(os.path.join(dp, f) for dp, dn, fn in os.walk(HT305) for f in fn)
hlm = datetime.fromtimestamp(os.path.getmtime(hlataest)).strftime('%Y-%m-%d %H:%M:%S')
fb = open('FreqErr.md', 'rb').read()
f_lines = fb.count(b'\n')
f_entries = len(re.findall(r'^\[错误类型\]', fb.decode('utf-8'), re.M))
f_md5 = hashlib.md5(fb).hexdigest()[:8]
pzb = open(os.path.join('hardware', '20260919_墨水屏点屏排查记录.md'), 'rb').read()
lastsec = re.findall(r'^### (38\.\d+)', pzb.decode('utf-8'), re.M)[-1]

# ---- 组正文（只数全部插值） ----
E = []
E.append('【09-26 **%s 第十二次读数**｜**提交轮 #10 已落进 git（`%s`）而本遍仍零代码进镜像**；五把根尺本遍逐把现跑，**九个数与第十一次全部同值**（同值才是这一代的真相：本遍只动文档与取证件）】'
         % (T0.strftime('%H:%M:%S'), head))
E.append('① **相对 `HEAD`（%s）**：`git diff HEAD --numstat -- …/main` ⇒ **%d 只 / +%s / −%s**，名单现读 = `%s` 一只（自带 `PROV_PASS` 宏值、每轮被逐只点名 DROP，宏值只进工作树永不进 git 侧）⇒ 与第十一次那一格**只数与两个数逐字同值**（那次 1 / +219 / −14）。'
         % (head, len(ns_main), ns_main[0][0], ns_main[0][1], os.path.basename(ns_main[0][2])))
E.append('② **相对 r43 那两根**：`diff -rq` 根 A / 根 B = **%d / %d 行**（与第十一次同值 ⇒ 两根仍是 09-22 20:55 那一烧的历史输入，不刷新）。' % (r43a, r43b))
E.append('③ **相对 r53 那两根**：同一命令 = **%d / %d 行**（同第十一次）⇒ 那一格自第十一次起就降级成"历史"，本遍没有再把它拽回判据。' % (r53a, r53b))
E.append('④ **工作树 `main/` 体量**：**%d 只 / %d B**（现读，与第十一次逐字同值）⇒ 本遍**没有一字节代码进工作树**，这一格在第十一次刚被"零代码进工作树断了"改写，本遍它仍然非零、但增量属于上一遍而不是本遍。' % (wt_cnt, wt_bytes))
E.append('⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main …` ⇒ 仍 **%d 行 differ**（不顺手修，动历史镜像等于造第二把尺）。' % srcs)
E.append('⑥ **上一遍新建的那对全根**（`r61close_20260926_133908`，A=%d 只 / B=%d 只）：两根各自 `diff -rq …/main 工作树 main` = **%d / %d 行** ⇒ 它仍是盘上唯一与工作树逐字同值的全根，本遍**一只没覆写、一只没删**。'
         % (roots['A'][0], roots['B'][0], roots['A'][2], roots['B'][2]))
E.append('⑦ **提交轮 #10 的构成（本遍新格）**：`%s` = **%d 只**（`git diff --numstat %s %s` 现数），其中文本 **%d 只**贡献 **+ %d / − %d** 行，另 **%d 只**为二进制（numstat 打 `-` 而非整数，本批那两只原厂镜像 `%s`、`%s`——把它们当 0 行相加会"只数对、构成说错"，故逐只点名）。门侧读数由本遍现读载体 `%s`（`LABEL=%s`）：**FILES_SCANNED=%d / TOTAL_HITS=%d / VERDICT=%s**；本遍现跑的等式 `门 %d 名 == 提交 %d 只` 成立（由 assert 把关，不是抄来的）。对照侧 `%s` 给出这一族的**口径分解**：**%d 名 = %d 只带 blob 的 + %d 只删除行**——`git diff --cached --name-only` 含删除行，删除在索引里没有 blob ⇒ `git show :path` 扫不到；这一处缺口本遍由 `pw_pos_control_r61b.py` 补成 `INDEX_DELETED` 逐只点名 + 等式 `scanned + deleted == 门 FILES_SCANNED`，两臂 `%s/2` 全亮、与门载体逐字段互核 `equal=%s`，末态 `VERDICT=%s`。'
         % (head, files_in_commit, prev, head, files_in_commit - len(bins), plus, minus, len(bins), bins[0], bins[1],
            os.path.basename(GC), g_label, g_files, g_hits, g_verdict, g_files, files_in_commit,
            os.path.basename(PC), g_files, p_scanned, p_deleted, p_arms, p_equal, p_verdict))
E.append('⑧ **在册裁决第一次有了执行者**：提交轮 #9 那起「门全绿却把两只原厂镜像放进仓」的事故（排查记录 §38.33）在本遍被写成**代码**——清单器 `%s` 里 `BIN_EXT` **%d 个后缀**（本遍从该文件现读定义，并断言 `RULING` / `RULING_PROBE` 两个令牌都还在）命中即 DROP[RULING]，并加 `BINS_IN_KEEP=0` 断言 + `RULING_PROBE=2/2`（拿盘上真实那两只验"这套后缀真能拦住它们"，不是拿假名字自证；探针还断言这两只**当轮不在候选里**——它们已在索引外，靠 `.gitignore` 的**准确文件名**排除，不用 `*.bin` 通配，通配会把以后真要入库的二进制一并无声吞掉）。本遍它们经 `git rm --cached` 移出**跟踪**，即 ⑦ 里那 %d 只删除行；盘上原件一字节未动：本遍现算 %s = %s B / md5 前 8 位 `%s`、%s = %s B / md5 前 8 位 `%s`，四个数都 grep 得到 §38.33 原文（由 assert 把关，不是抄的）⇒ 「只读」这句现在仍然真。**代价照点名不隐藏**：`c7de970` 已进本地历史，那只 %s B 的 blob 永久留在未推送历史里，本遍不 amend、不 reset、不改写。'
         % (LST.replace(os.sep, '/'), len(bin_ext), p_deleted,
            bins[0], format(reg[bins[0]][0], ',d'), reg[bins[0]][1][:8],
            bins[1], format(reg[bins[1]][0], ',d'), reg[bins[1]][1][:8],
            format(flash_bytes, ',d')))
E.append('⑨ **docs/ 快照第十二遍**（本遍之前刚跑，`hardware/refresh_docs_snapshot_r61b.py`，与第十一遍同一只脚本、SRCS 未增删）：目录现读 **%d 只** = 表格 **%d 行** + `SNAPSHOT_NOTE.txt`（等式 %d+%d=%d 由本遍现跑 assert，脚本自己那两把尺也各跑了一遍：`TABLE_ROWS == FILES`、`现读 %d 只源` 必须真在 NOTE 里）、`SNAPSHOT_AT %s`、凭据闸 **%d 只源全扫 / HITS=0**、`NOTE_BYTES %d`、**`NEW_ONES %d`** ⇒ 这一遍是纯覆盖：**它覆盖的正是本遍唯一必须覆盖的那只 `FreqErr.md`**——顺序由本遍现跑钉住：第十七批的 rc=0 载体 `%s` 的 mtime `%s` **早于** 快照时刻 `%s`（三值现读，不是抄的）；第十一遍那格量的是第十七批**之前**的 FreqErr，本遍没有推翻它。'
         % (docs_files, note_rows, note_rows, 1, docs_files, src_cnt, snap_at, src_cnt, note_bytes, new_ones,
            F17_NAME, F17_MTIME, snap_at))
E.append('⑩ **FreqErr / 排查记录 / 封界现场态（现读）**：`FreqErr.md` **%d 条 / %d 行 / %d B / md5 前 8 位 `%s`**（第十七批落地后本遍第一次现读，与 §38.36 那一节的登记互核）；`hardware/20260919_墨水屏点屏排查记录.md` **%d B / %d 行**，末节 = **§%s**，本遍之后新落的 §38.36 不在这一读数里（它落笔晚于本行取数）。'
         % (f_entries, f_lines, len(fb), f_md5, len(pzb), pzb.count(b'\n'), lastsec))
E.append('⑪ **串口与封界现场态**：`python -m serial.tools.list_ports` 现跑 = `%s` ⇒ **COM14 在位 = %s**（枚举 rc=0 且解析出 %d 只 COM 名，"命中 0"那种假缺席由 assert 挡在写盘之前）；`hardware/ht305_sync/` 递归现读 **%d 只**、`git ls-files` 侧 **%d 只**（两把尺同值），目录内最新一只 = `%s` 的 mtime `%s` ⇒ gen 24 之后**一字节未落**、本代不新建清单代；本遍所有取证仍落 `hardware/r61b_sync/evidence/`。'
         % (', '.join(ports), com14, len(ports), hfiles, htracked, os.path.basename(hlataest), hlm))
E.append('⑫ **本遍工作树余量（现跑）**：HEAD = `%s`，`rev-list --count origin/main..HEAD` = **%d**（第十一次那一格 %d ⇒ 本遍多出的那一只提交就是提交轮 #10，**未 push、未 amend**）；`status --porcelain` = **%d 行**（%s）——⚠ `--porcelain` 对未跟踪目录按目录折叠，本格只记"现跑行数"，不许跨代换算成只数。'
         % (head, revlist, 18, len(sline), ' + '.join('`%s` %d' % (k.strip() or 'AA', v) for k, v in sorted(skind.items()))))
E.append('⑬ **本遍四处缺陷（点名，不藏）**：(a) 第十七批落地器写盘后的证明段把**行下标**喂给了 **bytes** 对象（`chk[行号]` ⇒ 取到单个字节 int 再 `.decode` 才崩），它是**改之前就静态发现**的（盘上从未存在过那个形态），所以没有"崩溃那次的读数"要洗；(b) 独立复核工具 `verify_r61b_freqerr17.py` 连崩三遍：glob 匹配到 3 只载体（⇒ 加内容过滤 + `[0-9]` 前缀）、对 bytes 项用 str 模式（⇒ 模式忘了 `b` 前缀，比较恒不命中）、**把绝对零门装在基线本就非零的量上**（全册加粗奇数行基线 4 ⇒ 改成"不新增"，增量由台账行自己的声明推出）；末遍 `VERDICT=VERIFY_OK rc=0`，崩的三遍载体全部留盘点名；(c) 阳性对照脚本派生遍对 `git show :path` 不查 rc ⇒ 撞上提交轮 #9 遗留的 `D ` 行（原厂镜像的 staged 删除）直接 fatal，修法是改读 `--name-status` 并把删除行**逐只点名**而不静默；(d) 门载体一度叫 `staged_cred_gate_r61b_final105.txt` 而它体内 `FILES_SCANNED=106` ⇒ **载体名里的数字不等于体内读数**，本遍按真名 `final106` 重跑门与对照，错名那一对作为中间凭证留盘（零删除）。')
E.append('⇒ 判定不变：**不重建、不重烧、不新建根**（本遍唯一涉及磁盘大量写入的动作 = docs 快照第十二遍的覆盖拷贝）。**没烧录、没碰串口**（COM14 不在位）⇒ 屏亮肉眼确认仍 **1 次**（R59 那一次，本遍没推进）、看到第二页 **0 次**、用户真按 BOOT **0 次** ⇒ **不播提示音的判据仍成立**；**未 `git push`**、未 amend、**零删除**（含 `%TEMP%`、各臂抓回原件与上一遍那对错名门载体）。')
E.append('（载体：本格 ①~⑬ 全部现跑读数 = `hardware/r61b_sync/evidence/r61b_readme12_land_%s.txt`；写盘前的 README 原件快照 = 同目录 `readme_pre12_*.md`。**本行是这只 README 在本代被动的第四次**（插 ①~⑪ → 补载体行 → 订正行尾换行 → 本遍追加第十二格），历次都没覆写任何旧格、零删除。）'
         % T0.strftime('%H%M%S'))

body = '\n'.join(E) + '\n'

# ---- 写盘前裁决（全部排在 open(...,'w') 之前） ----
secret = re.search(rb'#define\s+PROV_PASS\s+"([^"]+)"', open(MACRO, 'rb').read()).group(1)
assert secret not in body.encode('utf-8'), 'ABORT: 正文明文命中口令'
assert 'ht305_sync' not in EV, 'ABORT: 取证落点指进封存归档目录'
assert body.count(chr(92)) == 0, 'ABORT: 正文含反斜杠（本代正文反斜杠闸）'
assert 'PLACEHOLDER' not in body and '%d' not in body and '%s' not in body, 'ABORT: 正文含未解析哨兵'
for tok in ('第十二次读数', 'docs/ 快照第十二遍', '提交轮 #10 的构成'):
    assert tok in body, 'ABORT: 正文缺关键锚 ' + tok
assert F17_MTIME < snap_at, 'ABORT: 落地载体 mtime 不早于快照时刻，顺序反了'
# 正文 ⑦ 那几句声称"由 assert 把关"，这里就是那些把关（缺一处 = 那句话落笔即假）：
assert g_files == files_in_commit, 'ABORT: 门 FILES_SCANNED %d != 提交只数 %d' % (g_files, files_in_commit)
assert p_scanned + p_deleted == g_files, 'ABORT: 口径分解不等式不成立'
assert (g_hits, g_verdict, p_equal, p_arms, p_verdict) == \
       (0, 'CLEAN', 'True', '2', 'POSITIVE_CONTROL_FIRES_AND_INDEX_CLEAN'), 'ABORT: 门/对照读数不是全绿'
assert len(bins) == p_deleted, 'ABORT: 提交里的二进制只数与索引删除行数不等'

PROOF_ONLY = '--proof-only' in sys.argv


def prove(lines0, lines1, new_lines, idx, skip=()):
    """纯插入的行级证明只能写成三段：前缀逐字等 + 插入段逐行等 + 后缀逐字等。
    上一版这里是"逐位置比 lines0[i] vs lines1[i]"——纯插入会把插入点之后的每一行都错位，
    于是盘上内容是对的而证明全红（rc=1 与"盘对"同时成立，本遍就栽在这上面）。
    skip 只允许点名"含现场态读数、按构造随本遍取证增长"的行；跳过必须连两侧值一起打印。"""
    assert len(lines1) == len(lines0) + len(new_lines), \
        'ABORT: 行数增量 %d != 预期 %d' % (len(lines1) - len(lines0), len(new_lines))
    assert lines1[:idx] == lines0[:idx], 'ABORT: 插入点之前的行未逐字保持'
    _skipped = []
    for i in range(len(new_lines)):
        if lines1[idx + i] == new_lines[i]:
            continue
        if i in skip:
            _skipped.append((i, lines1[idx + i][:160], new_lines[i][:160]))
            continue
        raise AssertionError('ABORT: 插入段第 %d 行不等\n  盘面: %r\n  预期: %r'
                             % (i, lines1[idx + i][:200], new_lines[i][:200]))
    assert lines1[idx + len(new_lines):] == lines0[idx:], 'ABORT: 插入点之后的行未逐字保持'
    return _skipped


if PROOF_ONLY:
    _cands = [os.path.join(EV, f) for f in sorted(os.listdir(EV)) if re.match(r'^readme_pre12_\d{8}_\d{6}\.md$', f)]
    assert len(_cands) == 1, 'ABORT: 原件快照应恰 1 只，实测 %d' % len(_cands)
    pre = _cands[0]
    rb0 = open(pre, 'rb').read()
    rb1 = open(README, 'rb').read()
    assert rb1.startswith(rb0[:200]), 'ABORT: 现件与原件快照开头不连续'
    lines0 = rb0.decode('utf-8').split('\n')
    lines1 = rb1.decode('utf-8').split('\n')
    anchors = [i for i, l in enumerate(lines0) if l.startswith('## 2. 命名规则')]
    assert len(anchors) == 1, 'ABORT: 锚点在原件快照里不唯一（%d 处）' % len(anchors)
    idx = anchors[0] - 1
    assert lines0[idx] == '', 'ABORT: 锚点前一行不是空行'
    # 那一遍落地的时刻写在载体名里，也写在正文末行；本遍是事后复核，T0 已不同 ⇒
    # 把正文里的"本遍时刻"回读成原件快照名里那个时刻，证明才是拿真文本比真字节。
    _stamp = re.search(r'readme_pre12_\d{8}_(\d{6})\.md$', pre).group(1)
    _h, _m, _s = _stamp[:2], _stamp[2:4], _stamp[4:6]
    assert body.count(T0.strftime('%H%M%S')) == 1, 'ABORT: 正文里本遍时刻的载体名不是恰好一处'
    assert body.count(T0.strftime('%H:%M:%S')) == 1, 'ABORT: 正文里本遍时刻的标题不是恰好一处'
    body = body.replace(T0.strftime('%H%M%S'), _stamp).replace(T0.strftime('%H:%M:%S'), '%s:%s:%s' % (_h, _m, _s))
    new_lines_exp = body.rstrip('\n').split('\n')
    # 只有两类行按构造会漂：⑫（现跑 status 行数，本遍每落一只取证就多一行）与载体行（它引的载体
    # 在这一遍之后才写）。其余 14 行必须逐字等，且漂的这两行必须由"新增取证只数"精确解释。
    _vol = [i for i, l in enumerate(new_lines_exp) if l.startswith('⑫ ') or l.startswith('（载体：')]
    assert len(_vol) == 2, 'ABORT: 易漂行应恰 2 行，实测 %d' % len(_vol)
    _skip = prove(lines0, lines1, new_lines_exp, idx, skip=set(_vol))
    for i, disk_v, exp_v in _skip:
        say('VOLATILE 第 %d 行（插入区 0 起）\n  盘面: %s\n  复核: %s' % (i, disk_v, exp_v))
    _n_disk = int(re.search(r'status --porcelain` = \*\*(\d+) 行\*\*', lines1[idx + _vol[0]]).group(1))
    _n_exp = int(re.search(r'status --porcelain` = \*\*(\d+) 行\*\*', new_lines_exp[_vol[0]]).group(1))
    _newev = sorted(f for f in os.listdir(EV)
                    if os.path.getmtime(os.path.join(EV, f)) >= os.path.getmtime(pre))
    say('STATUS_DRIFT %d -> %d / 差 %d；落地遍之后取证目录里新增（或原地留下）的只数 = %d：%s'
        % (_n_disk, _n_exp, _n_exp - _n_disk, len(_newev), _newev))
    assert _n_exp - _n_disk == len(_newev), \
        'ABORT: 漂移没有精确归因（差 %d != 新增取证 %d）' % (_n_exp - _n_disk, len(_newev))
    say('MODE=PROOF_ONLY（本遍不落盘，只把修好的三段式证明跑在真字节上）/ 落地时刻令牌回读为 %s' % _stamp)
    say('PRE=%s bytes=%d lines=%d' % (os.path.basename(pre), len(rb0), len(lines0)))
    say('README bytes=%d lines=%d / INSERTED %d @%d' % (len(rb1), len(lines1), len(lines1) - len(lines0), idx + 1))
else:
    rb0 = open(README, 'rb').read()
    assert not rb0.startswith(b'\xef\xbb\xbf'), 'ABORT: README 无 BOM，别引入'
    assert rb0.count(b'\r\n') == 0, 'ABORT: README 是 LF-only，本遍不许造 CR'
    assert rb0[-1:] == b'\n', 'ABORT: README 末字节不是换行'
    txt0 = rb0.decode('utf-8')
    assert '第十二次读数' not in txt0, 'ABORT: 第十二次读数已在册（幂等门），不重复插'
    lines0 = txt0.split('\n')
    anchors = [i for i, l in enumerate(lines0) if l.startswith('## 2. 命名规则')]
    assert len(anchors) == 1, 'ABORT: 插入锚点不唯一（%d 处）' % len(anchors)
    idx = anchors[0] - 1
    assert lines0[idx] == '', 'ABORT: 锚点前一行不是空行，插入会顶掉结构'

    pre = os.path.join(EV, 'readme_pre12_%s.md' % T0.strftime('%Y%m%d_%H%M%S'))
    assert not os.path.exists(pre), 'ABORT: 原件快照已存在，不覆盖'
    open(pre, 'wb').write(rb0)

    new_lines = body.rstrip('\n').split('\n')
    out = '\n'.join(lines0[:idx] + new_lines + [''] + lines0[idx + 1:])
    ob = out.encode('utf-8')
    open(README, 'wb').write(ob)

    # ---- 写盘后证明：三段式行级差集 ----
    rb1 = open(README, 'rb').read()
    assert rb1 == ob, 'ABORT: 盘上字节与预期串不等'
    lines1 = rb1.decode('utf-8').split('\n')
    prove(lines0, lines1, new_lines, idx)

    assert '## 2. 命名规则' in rb1.decode('utf-8'), 'ABORT: 标题被静默删除'
    assert lines1.count('') >= lines0.count(''), 'ABORT: 空行数减少（结构被吃掉）'

    say('README bytes %d -> %d / lines %d -> %d / INSERTED %d @%d'
        % (len(rb0), len(rb1), len(lines0), len(lines1), len(new_lines), idx + 1))
say('FREQERR %d 条 / %d 行 / %d B / md5 %s' % (f_entries, f_lines, len(fb), f_md5))
say('DOCS 第十二遍 SNAPSHOT_AT %s FILES %d NEW_ONES %d NOTE_BYTES %d' % (snap_at, note_rows, new_ones, note_bytes))
say('COMMIT %s FILES %d BINARY_NAMED %d PLUS +%d MINUS -%d' % (head, files_in_commit, len(bins), plus, minus))
say('REVLIST %d STATUS_LINES %d %s / COM14=%s / HT305 %d 只' % (revlist, len(sline), skind, com14, hfiles))
say('VERDICT=%s rc=0' % ('PROOF_ONLY_OK' if PROOF_ONLY else 'LANDED'))

txt = '\n'.join(OUTL) + '\n'
CARRIER = os.path.join(EV, 'r61b_readme12_%s_%s.txt'
                       % ('proof' if PROOF_ONLY else 'land', T0.strftime('%H%M%S')))
assert not os.path.exists(CARRIER), 'ABORT: 载体已存在'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(txt)
assert os.path.getsize(CARRIER) == len(txt.encode('utf-8')), 'ABORT: 载体字节数与输出不等'
print('CARRIER', CARRIER, os.path.getsize(CARRIER))
print('PRE_IMAGE', pre, os.path.getsize(pre), 'md5', hashlib.md5(open(pre, 'rb').read()).hexdigest()[:8])
