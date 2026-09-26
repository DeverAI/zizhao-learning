# 落地器：把 §38.33（提交轮 #9）与 §38.34（第 14 代同步）追加进 `hardware/20260919_墨水屏点屏排查记录.md`。
# 三条硬规矩（都是本仓库登记过的缺陷形态的执行者，逐条对应）：
#   ①**幂等前置**：写盘前先查两节标题在不在，已在即 ABORT —— 不依赖"我记得上一遍有没有落盘"；
#   ②**裁决在写盘之前**：所有断言（节序、行尾、口令扫描、每个引来的数字与载体逐字段相等）全部排在
#     `open(...,'ab')` 前面 —— `rc≠0` 必须蕴含"盘上没动过"（FreqErr 第十三批那条的第三次发作才换来的口径）；
#   ③**数字不手抄**：本节正文里每一个读数都是从当轮取证载体现读、现场断言后插值进去的，
#     载体缺一字段即 ABORT，宁可响不静默。
import datetime
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
EV = os.path.join(REPO, 'hardware', 'r61_sync', 'evidence')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
H33 = '### 38.33 '
H34 = '### 38.34 '


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr)
    return r.stdout


def field(path, pat, cast=str):
    txt = io.open(path, encoding='utf-8').read()
    m = re.search(pat, txt)
    assert m, 'ABORT: 载体 %s 里找不到 %r' % (os.path.basename(path), pat)
    return cast(m.group(1))


# ---------- 现场态：git 侧 ----------
HEAD = git('rev-parse', '--short', 'HEAD').strip()
REVL = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
C9 = 'c7de970'
_num9 = [l.split('\t') for l in git('diff', '--numstat', C9 + '^', C9).strip().splitlines()]
# `--numstat` 对**二进制**行打的是 `-\t-\t路径`，不是两个整数 ⇒ 直接 int() 会崩（本遍首跑就是这么死的），
# 而更糟的修法是把 `-` 当成 0 相加 ⇒ 只数对、构成说错。这里把两只二进制单独点出来，文本增量只加数字行。
_bin9 = sorted(x[2] for x in _num9 if x[0] == '-' or x[1] == '-')
_txt9 = [x for x in _num9 if x[0] != '-' and x[1] != '-']
N9, ADD9, DEL9 = len(_num9), sum(int(x[0]) for x in _txt9), sum(int(x[1]) for x in _txt9)
assert len(_bin9) == 2, 'ABORT: #9 里的二进制只数不是 2（本批事故那两只）：%s' % _bin9
porc = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
MODN = len([l for l in porc if l.startswith(' M')])
STGN = len([l for l in porc if l.startswith('D ')])
UNTN = len([l for l in porc if l.startswith('??')])
assert STGN == 2, 'ABORT: 移出跟踪的 `D ` 行数不是 2（两只原厂镜像）：%d' % STGN
# 未跟踪行按目录现数（不硬编码"11 只取证件 + 8 只脚本"那种快照）：本代自产件全在 r61_sync 下，
# 在册排除项固定三只（.workbuddy/ 折叠行、Agent_readme.txt、dev_log/20260919.md）⇒ 四桶必须正好铺满 ?? 行。
_un = [l[3:].strip() for l in porc if l.startswith('??')]
_UMEAN = [p for p in _un if p.startswith('hardware/r61_sync/evidence/')]
_USCRP = [p for p in _un if p.startswith('hardware/r61_sync/scripts/')]
_ONREG = [p for p in _un if p in ('.workbuddy/', 'Agent_readme.txt', 'dev_log/20260919.md')]
assert len(_UMEAN) + len(_USCRP) + len(_ONREG) == UNTN, 'ABORT: ?? 行没有被四桶铺满（冒出了没点名的新目录）：%s' % (
    sorted(set(_un) - set(_UMEAN) - set(_USCRP) - set(_ONREG)))

# ---------- 现场态：仓库外那批含明文的串口原始日志到底几只（现扫，不抄旧数） ----------
_sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(SRC, encoding='utf-8').read()).group(1).encode()
assert len(_sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
ESPL = os.path.join('C:', os.sep, 'esp')
RAW = sorted(os.path.basename(p) for p in
             [os.path.join(ESPL, f) for f in os.listdir(ESPL) if f.endswith('.log')]
             if _sec in io.open(p, 'rb').read())
assert RAW, 'ABORT: `C:\\esp\\*.log` 里一只含明文的都没有 ⇒ 这一把尺没有样本，"载荷里缺什么"那句无从写起（命中 0 ≠ 干净）'

# ---------- 现场态：提交轮 #9 的门与清单 ----------
LST = os.path.join(EV, 'staged_list_122059.txt')
G1 = os.path.join(EV, 'staged_cred_gate_r61_index507.txt')
G2 = os.path.join(EV, 'staged_cred_gate_r61_final514.txt')
P1 = os.path.join(EV, 'staged_cred_gate_r61_index507_pos.txt')
P2 = os.path.join(EV, 'staged_cred_gate_r61_final514_pos.txt')
for p in (LST, G1, G2, P1, P2):
    assert os.path.isfile(p), 'ABORT: 载体不存在 ' + p
LB, LM = os.path.getsize(LST), hashlib.md5(open(LST, 'rb').read()).hexdigest()[:8]
_ltxt = io.open(LST, encoding='utf-8').read()
_m = re.search(r'git diff --name-only\((\d+)\) \+ git ls-files --others --exclude-standard\((\d+)\)', _ltxt)
assert _m, 'ABORT: 清单载体头部没有那两个口径数'
MODN_LST, UNTN_LST = int(_m.group(1)), int(_m.group(2))
DROPN = field(LST, r'排除并点名（[^）]*）：(\d+) 只', int)
KEEP = field(LST, r'进清单 (\d+) 只', int)
assert MODN_LST + UNTN_LST - DROPN == KEEP, 'ABORT: 清单自身三数不平'
F1 = field(G1, r'FILES_SCANNED=(\d+)', int)
F2 = field(G2, r'FILES_SCANNED=(\d+)', int)
V1, V2 = field(G1, r'VERDICT=(\w+)'), field(G2, r'VERDICT=(\w+)')
A1, A2 = field(P1, r'ARMS_FIRED=(\d/2)'), field(P2, r'ARMS_FIRED=(\d/2)')
assert (F1, F2) == (507, 514) and V1 == V2 == 'CLEAN' and A1 == A2 == '2/2', 'ABORT: #9 门读数与预期不符'
assert N9 == F2 + 3, 'ABORT: 提交只数 %d 与门 %d + 门自产 3 只不相等' % (N9, F2)

# ---------- 现场态：两只原厂镜像（本轮移出跟踪） ----------
FB, PT = (os.path.join(REPO, x) for x in ('esp32s3_flash_backup_8mb.bin', 'esp32s3_partition_table.bin'))
fbsz, fbmd5 = os.path.getsize(FB), hashlib.md5(open(FB, 'rb').read()).hexdigest()
ptsz, ptmd5 = os.path.getsize(PT), hashlib.md5(open(PT, 'rb').read()).hexdigest()
RULN = None
RULELINE = ''
for i, l in enumerate(io.open(TGT, encoding='utf-8').read().splitlines(), 1):
    if '两只都是用户资料' in l and '永不 stage' in l:
        RULN, RULELINE = i, l
assert RULN, 'ABORT: 找不到"永不 stage"那句原话 ⇒ 本批事故叙述的前提没了'
# "盘上原件一字节未动"这句要落进正文，就得让**那句在册登记自己**当量具：现读那一行里登的两只 md5，
# 与本遍现算的逐字比 —— 不靠我复抄一遍哈希（复抄即漂移源，(88) 那条订正句假引文同族）。
assert fbmd5 in RULELINE and ptmd5 in RULELINE, 'ABORT: 本遍现算的两只 md5 与第 %d 行在册值不同 ⇒ "只读未动"这句不能写' % RULN
# 两条在册句按**行号 + 逐字片段**现查（不复抄全文：复抄会让引用它的这一节自己变成下一处漂移源）
OBLN = None   # 上一批留下的义务：先把"同步证据落归档外"的机制建起来
SIXLN = None  # "包 == 现状"最后一次登记序数的那一句（第六次）
RRTL = None   # 往返"自第 6 代起每代复现"那句在册口径
for i, l in enumerate(io.open(TGT, encoding='utf-8').read().splitlines(), 1):
    if OBLN is None and '要么先把"同步证据落归档外"的机制建起来' in l:
        OBLN = i
    if '第六次' in l and '包 == 现状' in l:
        SIXLN = i
    if '自第 6 代起每代复现' in l:
        RRTL = i
assert OBLN and SIXLN and RRTL, 'ABORT: 三条在册前提缺件（义务 / 第六次 / 往返口径） OBLN=%s SIXLN=%s RRTL=%s' % (
    OBLN, SIXLN, RRTL)
GI = [i for i, l in enumerate(io.open(os.path.join(REPO, '.gitignore'), encoding='utf-8').read().splitlines(), 1)
      if l in ('/esp32s3_flash_backup_8mb.bin', '/esp32s3_partition_table.bin')]
assert len(GI) == 2, 'ABORT: .gitignore 里那两条精确名不齐'

# ---------- 现场态：第 14 代同步六只载体 ----------
LOC, VER, LDA, RT = (os.path.join(EV, x) for x in
                     ('r61_local.txt', 'r61_verify.txt', 'r61_listdiff.txt', 'r61_roundtrip.txt'))
for p in (LOC, VER, LDA, RT):
    assert os.path.isfile(p), 'ABORT: 同步载体不存在 ' + p
zsz = field(LOC, r'zip size/md5        = (\d+) ', int)
zmd5 = field(LOC, r'zip size/md5        = \d+ ([0-9a-f]{32})')
cf, cb = (int(x) for x in re.search(r'content files/bytes = (\d+) / (\d+)', io.open(LOC, encoding='utf-8').read()).groups())
agg_l = field(LOC, r'LOCAL_AGGREGATE     = ([0-9a-f]{64})')
dropn = field(LOC, r'dropped \(逐只点名\)   = (\d+) ', int)
_dn = re.search(r"dropped \(逐只点名\)   = \d+ \[(.*)\]", io.open(LOC, encoding='utf-8').read())
assert _dn, 'ABORT: dropped 行点名部分取不到'
DROPNAMES = [x.strip().strip("'") for x in _dn.group(1).split(', ') if x.strip()]
assert len(DROPNAMES) == dropn, 'ABORT: dropped 计数 %d 与点名只数 %d 不符' % (dropn, len(DROPNAMES))
pt_hits = field(LOC, r'plaintext in staging= (\d+) ', int)
rz, rm = field(VER, r'REMOTE_ZIP_SIZE=(\d+)', int), field(VER, r'REMOTE_ZIP_MD5=([0-9a-f]{32})')
rf, rb, rbad = (field(VER, r'REMOTE_FILES=(\d+)', int), field(VER, r'REMOTE_BYTES=(\d+)', int),
                field(VER, r'REMOTE_FORBIDDEN=(\d+)', int))
agg_r = field(VER, r'REMOTE_AGGREGATE=([0-9a-f]{64})')
te = field(os.path.join(EV, 'r61_probe.txt'), r'TARGET_EXISTS=(\w+)')
desks = [l for l in io.open(os.path.join(EV, 'r61_probe.txt'), encoding='utf-8') if l.startswith('DESKTOP')]
zn = [l.split('\t')[1] for l in desks if l.split('\t')[1].startswith('zizhao_') and l.split('\t')[1].endswith('.zip')]
ll, rl = field(LDA, r'LOCAL_LINES=(\d+)', int), field(LDA, r'REMOTE_LINES=(\d+)', int)
ol, orr = field(LDA, r'ONLY_IN_LOCAL=(\d+) ', int), field(LDA, r'ONLY_IN_REMOTE=(\d+) ', int)
ident, chg, dele = (field(LDA, r'identical\(内容逐字节等,  sha256\) = (\d+)', int),
                    field(LDA, r'changed_since_cutoff = (\d+) ', int),
                    field(LDA, r'deleted_since_cutoff = (\d+) ', int))
news = field(LDA, r'new_since_cutoff     = (\d+) ', int)
cand = field(LDA, r'四桶互斥且并集 == 当前候选集\((\d+)\)', int)
ldv = field(LDA, r'VERDICT=(\w+)')
rtb, rtmd5 = field(RT, r'REMOTE_BYTES=(\d+) ', int), field(RT, r'REMOTE_BYTES=\d+ md5=([0-9a-f]{32})')
rbt = field(RT, r'BYTE_EQUAL_TO_WORKTREE=(\w+)')
rv = field(RT, r'VERDICT=(\w+)')
# 两把独立尺子必须给同一个数（远端报的回本地，本地算的报远端）：
assert (zsz, zmd5, cf, cb, agg_l) == (rz, rm, rf, rb, agg_r), 'ABORT: 本机算与远端算的五个字段不全等'
assert (ll, rl, ol, orr, ldv) == (cf, cf, 0, 0, 'LISTDIFF_EQUAL'), 'ABORT: 差集不是 0-0'
assert (chg, dele) == (0, 0) and ident == cf, 'ABORT: 包 != 现状'
assert te == 'False' and rbt == 'True' and rv == 'REMOTE_CARRIES_PLAINTEXT', 'ABORT: 探测/往返读数与预期不符'
assert pt_hits == 1 and rbad == 0, 'ABORT: 载荷明文只数或禁传件计数与既定口径不符'

# ---------- 正文（每个数字都是上面现读并断言过的变量） ----------
TS = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
B = []
B.append('')
B.append(H33 + 'R61 尾巴·提交轮 #9（现跑于 %s）：%d 只逐只点名进仓 + **一处在册裁决被清单无声推翻**的事故（本遍改了仓库跟踪状态、未 push）' % (TS, N9))
B.append('')
B.append('- **门与清单（读数取自 `hardware/r61_sync/evidence/` 五只载体，本遍逐字段现读并断言，不是抄录）**：'
         '清单 `%s`（%s B / md5 前 8 位 `%s`）口径 = `git diff --name-only`(%d) + `git ls-files --others --exclude-standard`(%d)，'
         'DROP=%d ⇒ KEEP=%d（三数由本遍现读清单头部并断言 `MOD+UNT-DROP==KEEP`）；'
         '索引门两遍 `FILES_SCANNED=%d / %d`、两遍 `TOTAL_HITS=0`、两遍 `VERDICT=%s/%s`、`PY_EXIT=0`；'
         '阳性对照两遍均 `ARMS_FIRED=%s / %s`（PROV 那路由两只已知脏的工作树件各 hits=1 点亮；SSH 那路只在进程内存造合成样本，服务器口令全程不落盘），'
         '并与门载体逐字段互核 `equal=True`。' % (os.path.basename(LST), format(LB, ','), LM,
                                                MODN_LST, UNTN_LST, DROPN, KEEP, F1, F2, V1, V2, A1, A2))
B.append('- **提交**：`%s` = %d 只，其中文本 %d 只（`--numstat` 相加 = +%s / −%d）+ **二进制 %d 只**（numstat 打 `-\\t-\\t` 而非整数，'
         '即本批那两只原厂镜像 `%s`——把它们当 0 行相加会"只数对、构成说错"，故逐只点名）。'
         '%d 只 = 门最终扫到的 %d 只 + 门自己那一遍扫不到的 3 只载体'
         '（门输出、驱动 ps-copy、对照输出——**门永远扫不到自己的输出**，这一形态自提交轮 #2 起历轮相同，故此处点名而不假装它被覆盖了）。'
         'HEAD 前 `rev-list origin/main..HEAD` = %d ⇒ 现 %d；**未 push、未 amend**。' % (
             C9, N9, len(_txt9), format(ADD9, ','), DEL9, len(_bin9), '`、`'.join(_bin9),
             N9, F2, REVL - 1, REVL))
B.append('- **本批事故（点名；形态是"在册裁决被清单无声推翻"，不是又一次算术错）**：'
         '排查记录第 **%d** 行那句「两只都是用户资料，本遍只读、一字节未改，**且永不 stage**」是 09-25 R58 落的一条在册裁决；'
         '本轮的逐只点名清单器 `make_staged_list_r61.py` **只认自己 EXCLUDE 表里那 %d 条硬编码项**，'
         '不知道盘上有这样一条裁决 ⇒ 两只原厂镜像（`esp32s3_flash_backup_8mb.bin` = %s B、`esp32s3_partition_table.bin` = %s B）'
         '在 %s 里被当作普通新文件一起进了仓。'
         '**错在哪**：排除表是"我此刻想到的几只会脏"，而裁决是"某只永久不许进"——两者不是一个东西，'
         '门只查口令明文、不查在册裁决，所以它 `TOTAL_HITS=0` 全绿的同时把那两只放了进去：**门绿不等于裁决被读**。' % (
             RULN, DROPN, format(fbsz, ','), format(ptsz, ','), C9))
B.append('- **处置（不做历史改写）**：%s 已经进了本地历史，**不 amend、不 reset、不 rewrite** ⇒ 那 %s B 的 blob 永久留在本地历史里，'
         '这条代价在此点名而不隐藏；本遍做的是把它移出**跟踪**：`git rm --cached` 两只（`git status --porcelain` 现读 `D ` 行 = %d），'
         '`.gitignore` 第 %d/%d 行按**准确文件名**排除（不用 `*.bin` 通配，通配会把以后真要入库的二进制一并无声吞掉），'
         '盘上原件一字节未动：本遍现算 md5 `%s` / `%s`，与该第 %d 行登记的逐字相等 ⇒ 「只读」这句现在仍然真。' % (
             C9, format(fbsz, ','), STGN, GI[0], GI[1], fbmd5, ptmd5, RULN))
B.append('- **本轮工作树余量（本遍现跑 `git status --porcelain`，逐类现数不抄旧数）**：共 %d 行 =` M` %d + `D ` %d + `??` %d。'
         '` M` 那两只是 `.gitignore` 与带 `PROV_PASS` 宏值的 `provision_ap.c`（宏值只进工作树，永远不进 git 侧）；'
         '`D ` 那两只就是本批移出跟踪的两张原厂镜像；`??` 行按目录现数 = 本代取证件 %d + 本代脚本 %d + 在册排除项 %d（`.workbuddy/` 折叠行、`Agent_readme.txt`、`dev_log/20260919.md`），'
         '四桶由本遍断言正好铺满 `??` 行 ⇒ 没有第四桶之外的漏网目录。这三类全在下一轮提交轮的逐只点名清单里，本节不预判。' % (
             len(porc), MODN, STGN, UNTN, len(_UMEAN), len(_USCRP), len(_ONREG)))
B.append('')
B.append(H34 + 'R61 尾巴·第 14 代 ht305 全量同步（现跑于 %s）：本机算与远端解包后算的五个字段逐项全等、双向名单差集 0-0；服务器仍带明文 ⇒ 它不是回滚源（本遍远端**只写不删**、未 push）' % TS)
B.append('')
B.append('- **五个两侧独立读数（本机算一份、远端解包后算一份，本遍逐字段 assert 全等，不是"差不多"）**：'
         '包 `%s.zip` = %s B / md5 `%s`；内容 %d 只 / %s B；聚合 sha256 = `%s`；`REMOTE_FORBIDDEN=%d`（禁传表口径：`.log/.bin/.elf/.map/nvs.csv/^backups/`）；'
         '打包截止后新增 %d 只（全是本代自产的取证/脚本件，见下一条），当前候选集 %d 只，四桶互斥且并集 == 候选集 PASS。' % (
             'zizhao_20260926_r61final', format(zsz, ','), zmd5, cf, format(cb, ','), agg_l, rbad, news, cand))
B.append('- **双向名单差集 0-0 与包↔现状**：`LOCAL_LINES=%d REMOTE_LINES=%d ONLY_IN_LOCAL=%d ONLY_IN_REMOTE=%d` ⇒ `%s`；'
         '逐只 sha256 比对 `identical=%d / changed_since_cutoff=%d / deleted_since_cutoff=%d` ⇒ 服务器那份**逐字等于**本机此刻的工作树。'
         '**本遍不登记序数**：在册的「包 == 现状」最后一次带序数是第 **%d** 行那句"第六次"（第 11 代），'
         '第 12 / 13 代两遍都只登记了读数没登记序数 ⇒ 此刻"第几次"要我先补算两遍的账才能成立，'
         '而**没落盘的补算不算取证**（(90) 那条：台账自己的序数不复算就就地降级），故本节只写本代读数与"这是第 14 代同步"。' % (
             ll, rl, ol, orr, ldv, ident, chg, dele, SIXLN))
B.append('- **远端动作半径（这是本节唯一涉及共享系统的部分，逐条点名）**：探测 `TARGET_EXISTS=%s`（不覆盖任何既有产物）⇒ scp `RC=0` ⇒ '
         '解包进**全新**根 `zsynctest16`（上一代是 zsynctest15，每代一个新根，**绝不清空、绝不删除**）；'
         '服务器桌面本遍现读文件 %d 只，其中同步包 `zizhao_*.zip` **%d 只并存**；**零删除**。' % (te, len(desks), len(zn)))
B.append('- **往返复核（"远端到底带不带明文"这句话唯一的量法，第 %d 行那句在册口径的又一次复现）**：'
         '把远端解包件 `provision_ap.c` 抓回 %%TEMP%% 与工作树逐字比 ⇒ `%d B / md5 `%s` / `BYTE_EQUAL_TO_WORKTREE=%s`，'
         '同尺在已知脏的工作树原件上 hits=1（阳性）、在本代按宏名读口令的 `sync_r61.py` 上 hits=0（阴性），'
         '判决 `%s` ⇒ **服务器不是回滚源，本仓库任何一只都绝不 push**。'
         '（这条与"载荷里不许有明文"是两件事：载荷取的是工作树，而工作树里那只 `.c` 本来就把宏值写在盘上。）' % (
             RRTL, rtb, rtmd5, rbt, rv))
B.append('- **本遍兑现的是上一批写下的一条义务（不是新起动作）**：排查记录第 **%d** 行那句"要么先把『同步证据落归档外』的机制建起来，'
         '要么下一批在 paperwork 之前先同步、再重新冻结一代"——本遍走的是**第一支**：证据全部落 `hardware/r61_sync/`，'
         '`hardware/ht305_sync/` 一只没碰，gen 24 因此**仍是末版**（本代不新建清单代，见下一条守卫）。' % OBLN)
B.append('- **取证落点边界（本代新装的守卫）**：第 14 代全部 6 只脚本（`sync_r61.py / r61_upload.ps1 / chk_r61.ps1 / r61_listdiff.py / r61_cutoff_delta.py / r61_roundtrip.py`）'
         '与全部取证件都落在 `hardware/r61_sync/` 之下；`hardware/ht305_sync/` **一只没碰**（那里 SEAL 停在 gen 24，本代不新建清单代）。'
         '6 只脚本里每一只都自带一条 ABORT：解析出的路径含 `ht305_sync` 即停 —— 上一代没有这道闸，它的 ps 驱动把 `*_ps.txt` 硬编码写进 `ht305_sync/evidence/`，'
         '本代若照抄就会往封存归档目录多落一只派生字节日、把 `verify_manifest.py` 打成 `MANIFEST_STALE`（"检查动作污染被检查物"那一族，这次是**提前**被自己的守卫挡住，未发生）。')
B.append('- **载荷里没有的东西（点名，别把"传上去了"读成"什么都传上去了"）**：'
         '① %d 只含 `PROV_PASS` 明文的串口原始日志只存在于 `C:\\esp\\` **顶层 `*.log`**（本遍现扫 %d 只 `C:\\esp\\*.log`，逐只按宏体现读、不递归子目录，'
         '口径边界就写在这里；永不 stage / 永不 push / 永不删除）⇒ ht305 上的是**脱敏取证件**，不是这些原始日志；'
         '② `backups/` 整目录（`.gitignore:19`，仓库外只落盘）；③ 两只原厂整片镜像（本批刚移出跟踪，见 §38.33）；'
         '④ 本代自产的 %d 只取证/脚本件（打包截止之后才落盘，`r61_cutoff_delta.py` 的 new_since 桶逐只点名）；'
         '⑤ 同步排除表点名 drop 的 %d 只：%s（**逐字取自 `r61_local.txt` 的 dropped 行，不是我另列一份**）。' % (
             len(RAW), len([f for f in os.listdir(ESPL) if f.endswith('.log')]),
             news, dropn, '、'.join('`%s`' % x for x in DROPNAMES)))
B.append('- **本遍没做（点名）**：没烧录、没碰串口（COM14 此刻在板的是 §38.32 那只出厂镜像，本遍未复查它还在不在）；'
         '人眼看到第二页 = 0 次、用户真按 BOOT = 0 次（§38.32 那两个 0 本遍一个都没推进）⇒ **不播提示音的判据仍成立**；'
         '`hardware/ht305_sync/` 归档链本代不重跑；`todo.md`/`done.md`/`FreqErr.md` 的收口在别的节；未 push、未 amend。')

BODY = '\n'.join(B) + '\n'

# ---------- 裁决全部排在写盘之前 ----------
pre = io.open(TGT, 'rb').read()
pre_lines, pre_bytes = pre.count(b'\n'), len(pre)
if H33.encode('utf-8') in pre or H34.encode('utf-8') in pre:
    raise SystemExit('ABORT: 38.33/38.34 已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\n'):
    raise SystemExit('ABORT: 既有正文末行不以换行收尾，直接追加会粘行')
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(SRC, encoding='utf-8').read()).group(1)
assert sec and len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
bb = BODY.encode('utf-8')
assert sec.encode('utf-8') not in bb, 'ABORT: 正文含口令明文'
# 行尾口径必须**现读再选**（不是"历代都这么写"）：现算本文件 CRLF / 裸 LF 各多少、末行以哪种收尾，
# 只有"末行以裸 LF 收尾"成立时，追加体沿用裸 LF 才不与接缝处自相矛盾。
_eolc = pre.count(b'\r\n')
assert pre_lines > _eolc and pre[-2:] != b'\r\n', 'ABORT: 末行接缝是 CRLF，追加体不能写裸 LF'
_exp_lines = pre_lines + BODY.count('\n')
_exp_bytes = pre_bytes + len(bb)
whole = bb

io.open(TGT, 'ab').write(whole)
chk = io.open(TGT, 'rb').read()
post_lines, post_bytes = chk.count(b'\n'), len(chk)
assert chk[:pre_bytes] == pre, 'ABORT: 前缀被改动（本脚本自称纯追加器，这条是事后复算，不是事后补救）'
assert (post_lines, post_bytes) == (_exp_lines, _exp_bytes), 'ABORT: 落盘后行数/字节数与写盘前算的期望不符（%d/%d vs %d/%d）' % (
    post_lines, post_bytes, _exp_lines, _exp_bytes)
print('EOL_BEFORE CRLF=%d bareLF=%d | EOL_APPEND=LF(接缝现读为裸 LF)' % (_eolc, pre_lines - _eolc))
print('TGT_LINES %d -> %d | TGT_BYTES %d -> %d' % (pre_lines, post_lines, pre_bytes, post_bytes))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('ADDED_BYTES=%d ADDED_LINES=%d' % (post_bytes - pre_bytes, post_lines - pre_lines))
print('VERDICT=LANDED rc=0')
