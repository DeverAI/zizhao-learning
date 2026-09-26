# 落地器（第 15 代 / r61b）：把 §38.35 追加进 `hardware/20260919_墨水屏点屏排查记录.md`。
# 三条硬规矩照上一代落地器 `hardware/r61_sync/scripts/land_r61_38.py` 继承，逐条对应一种已登记过的缺陷形态：
#   ①**幂等前置**：写盘前先查 §38.35 标题在不在，已在即 ABORT；
#   ②**裁决排在写盘之前**：所有断言都在 `open(...,'ab')` 前面 ⇒ `rc≠0` 蕴含"盘上没动过"；
#   ③**数字不手抄**：正文里每个读数都从当轮载体现读并断言，载体缺字段即 ABORT。
# 本代另加一条（正是上一批刚登记的那类）：**行尾口径现读再选**，不继承"上一遍写的是裸 LF"这个记忆。
import datetime
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
SCRP = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
H35 = '### 38.35 '
TOP = 'zizhao_20260926_r61bfinal'
ROOT = 'zsynctest17'


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr)
    return r.stdout


def txt(path):
    return io.open(path, encoding='utf-8').read()


def g(path, pat, cast=None):
    m = re.search(pat, txt(path))
    assert m, 'ABORT: 载体 %s 里取不到 %r' % (os.path.basename(path), pat)
    v = m.group(1)
    return cast(v) if cast else v


# ---------- 六只派生件 + 十二只载体：先确认在，再谈读数 ----------
TOOLS = ['sync_r61b.py', 'r61b_upload.ps1', 'chk_r61b.ps1', 'r61b_listdiff.py',
         'r61b_cutoff_delta.py', 'r61b_roundtrip.py']
CARRIERS = ['r61b_local.txt', 'r61b_local_names.txt', 'r61b_parse_check.txt', 'r61b_probe.txt',
            'r61b_run_log.txt', 'r61b_scp_err.txt', 'r61b_verify.txt', 'r61b_remote_names.txt',
            'r61b_listdiff.txt', 'r61b_cutoff_delta.txt', 'r61b_roundtrip.txt', 'r61b_derive_report.txt']
for p in [os.path.join(SCRP, x) for x in TOOLS] + [os.path.join(EV, x) for x in CARRIERS]:
    assert os.path.isfile(p), 'ABORT: 本代文件不存在 ' + p
MTS = sorted(set(datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(SCRP, x)))
                 .strftime('%Y-%m-%d %H:%M:%S') for x in TOOLS))
assert len(MTS) == 1, 'ABORT: 六只派生件 mtime 不同值，"一次派生"这句不成立：%s' % MTS
DERIVE_MTIME = MTS[0]

LOC = os.path.join(EV, 'r61b_local.txt')
LNM = os.path.join(EV, 'r61b_local_names.txt')
PCH = os.path.join(EV, 'r61b_parse_check.txt')
PRB = os.path.join(EV, 'r61b_probe.txt')
SCE = os.path.join(EV, 'r61b_scp_err.txt')
VER = os.path.join(EV, 'r61b_verify.txt')
LDA = os.path.join(EV, 'r61b_listdiff.txt')
CDF = os.path.join(EV, 'r61b_cutoff_delta.txt')
RTR = os.path.join(EV, 'r61b_roundtrip.txt')
DRV = os.path.join(EV, 'r61b_derive_report.txt')
RT_TOOL = os.path.join(SCRP, 'r61b_roundtrip.py')
DRV_TOOL = os.path.join(REPO, 'hardware', 'r61_sync', 'scripts', 'derive_r61b.py')

# ---------- 派生遍读数（载体 = r61b_derive_report.txt：stdout 逐字转录 + 复核件） ----------
PTR_S = g(DRV, r'POINTERS_SCRIPTS=(\d+) MISSING=0', int)
assert g(DRV, r'POINTERS_SCRIPTS=\d+ MISSING=(\d+)', int) == 0, 'ABORT: 派生遍有缺失指针'
assert g(DRV, r'VERDICT=(\w+)') == 'DERIVED', 'ABORT: 派生遍不是 DERIVED'
NSTAT = len(re.findall(r'^  \S+ mtime=\S+ \S+ bytes=\d+$', txt(DRV), re.M))
NMD5PASS = len(re.findall(r'^  \S+ md5_dst\(转录\)==md5\(现算\)=[0-9a-f]{8} PASS$', txt(DRV), re.M))
assert (PTR_S, NSTAT, NMD5PASS) == (8, 6, 6), 'ABORT: 派生读数与预期不符 %s' % ((PTR_S, NSTAT, NMD5PASS),)
STAT_MTS = set(re.findall(r'^  \S+ mtime=(\S+ \S+) bytes=\d+$', txt(DRV), re.M))
assert STAT_MTS == {DERIVE_MTIME}, 'ABORT: 转录登的 mtime 与本遍现读的六只 mtime 不同值：%s vs %s' % (STAT_MTS, DERIVE_MTIME)
# 第三把尺（本遍新装）：转录里 6 只的 md5_dst 与**盘上现算** md5 逐只对——前两把都在读同一张纸条，第三把必须读盘。
MD5_LIVE = {fn: hashlib.md5(open(os.path.join(SCRP, fn), 'rb').read()).hexdigest()[:8] for fn in TOOLS}
_pairs = re.findall(r'^(\S+) -> (\S+) \|.*?md5_dst=([0-9a-f]{8})', txt(DRV), re.M)
# 转录每行是「源 -> 目标 | … md5_dst=…」：要被"盘上现算"复核的是**目标**那一只，源在上一代目录里。
assert len(_pairs) == 6 and set(x[1] for x in _pairs) == set(TOOLS), 'ABORT: 转录派生件名单与本代六只不符：%s' % _pairs
assert all(MD5_LIVE[d] == m for _s, d, m in _pairs), 'ABORT: 盘上现算 md5 与转录不符 %s' % _pairs

# ---------- 打包侧（本机算的那一份） ----------
GL = g(LOC, r'git-listed \(dupes\)\s+= (\d+) / dupes = 0', int)
DUP = g(LOC, r'dupes = (\d+)', int)
SEL = g(LOC, r'selected\s+= (\d+) \| copy failures = 0', int)
CFail = g(LOC, r'copy failures = (\d+) ', int)
DROPN = g(LOC, r'dropped \(逐只点名\)\s+= (\d+) \[', int)
DROPRAW = g(LOC, r'dropped \(逐只点名\)\s+= \d+ \[(.*?)\]')
DROPNAMES = [x.strip().strip("'") for x in DROPRAW.split(', ') if x.strip()]
SF = g(LOC, r'staged files\s+= (\d+) \| bytes = \d+', int)
SB = g(LOC, r'staged files\s+= \d+ \| bytes = (\d+)', int)
PTH = g(LOC, r'plaintext in staging= (\d+) \[', int)
PTNAME = g(LOC, r"plaintext in staging= \d+ \['(.*?)'\]")
ZE = g(LOC, r'zip entries\s+= (\d+) \| utf8-flagged = \d+', int)
ZU = g(LOC, r'utf8-flagged = (\d+)', int)
ZSZ = g(LOC, r'zip size/md5\s+= (\d+) [0-9a-f]{32}', int)
ZMD5 = g(LOC, r'zip size/md5\s+= \d+ ([0-9a-f]{32})')
CF = g(LOC, r'content files/bytes = (\d+) / \d+', int)
CB = g(LOC, r'content files/bytes = \d+ / (\d+)', int)
AGG_L = g(LOC, r'LOCAL_AGGREGATE\s+= ([0-9a-f]{64})')
CB1 = g(LOC, r'CUTOFF_COPY_BEGIN\s+= ([0-9: -]+)').strip()
CB2 = g(LOC, r'CUTOFF_ZIP_MADE\s+= ([0-9: -]+)').strip()
FORBID_LOCAL = g(LOC, r'any \.log/\.bin/\.elf/\.map = (\[.*\])')
NBK = g(LOC, r'any backups/nvs\s+= (\w+)', str)
NLOG = re.search(r'any backups/nvs\s+= \w+ (\w+)', txt(LOC)).group(1)
assert (DUP, CFail, len(DROPNAMES)) == (0, 0, DROPN), 'ABORT: 打包侧三数不符'
assert GL - DROPN == SEL == SF == CF and CB == SB, 'ABORT: 名单四数不平 %s' % ((GL, DROPN, SEL, SF, CF, SB, CB),)
assert (PTH, PTNAME) == (1, 'hardware/zizhao-esp32s3/main/provision_ap.c')
assert FORBID_LOCAL == '[]' and (NBK, NLOG) == ('False', 'False')

# ---------- 门（上传件解析门） ----------
CHK_AT = g(PCH, r'CHK_AT=(2026-\d\d-\d\d \d\d:\d\d:\d\d)')
BOM = g(PCH, r'UTF8_BOM=(\w+)')
PE = g(PCH, r'PARSE_ERRORS=(\d+)', int)
RIH = g(PCH, r'REMOVE_ITEM_HITS=(\d+)', int)
SL = g(PCH, r'SCRIPT_LINES=(\d+)', int)
SRC_L = g(PCH, r'SRC_LINES=(\d+)', int)
MDB = g(PCH, r'MD5_BOTH=([0-9A-F]{32})')
FIRST3 = g(PCH, r'FIRST3=([\d,]+)')
assert (BOM, PE, RIH) == ('True', 0, 0) and SL == SRC_L, 'ABORT: 门读数不符 %s' % ((BOM, PE, RIH, SL, SRC_L),)
# 跨载体交叉：门算的是 TEMP 副本 == 仓库原件，派生转录算的是仓库原件 ⇒ 同一只文件两条独立路径同值
assert MD5_LIVE['r61b_upload.ps1'] == MDB[:8].lower(), 'ABORT: 门 MD5_BOTH 与盘上现算不同值'

# ---------- 远端（解包后算的那一份） ----------
RZ = g(VER, r'REMOTE_ZIP_SIZE=(\d+)', int)
RM = g(VER, r'REMOTE_ZIP_MD5=([0-9a-f]{32})')
RF = g(VER, r'REMOTE_FILES=(\d+)', int)
RB = g(VER, r'REMOTE_BYTES=(\d+)', int)
RBAD = g(VER, r'REMOTE_FORBIDDEN=(\d+)', int)
AGG_R = g(VER, r'REMOTE_AGGREGATE=([0-9a-f]{64})')
EXOK = g(VER, r'EXTRACT_OK=(\w+)')
RAT = g(VER, r'REMOTE_AT=([0-9: -]+)', str).strip()
RDAT = g(VER, r'REMOTE_DONE_AT=([0-9: -]+)', str).strip()
assert (RZ, RM, RF, RB, AGG_R) == (ZSZ, ZMD5, CF, CB, AGG_L), 'ABORT: 本机算与远端算的五字段不全等'
assert EXOK == 'True' and RBAD == 0, 'ABORT: 解包/禁传读数不符'

# ---------- 探测与半径 ----------
TE = g(PRB, r'TARGET_EXISTS=(\w+)')
desks = [l for l in txt(PRB).splitlines() if l.startswith('DESKTOP')]
zn = [l.split('\t')[1] for l in desks if l.split('\t')[1].startswith('zizhao_')
      and l.split('\t')[1].endswith('.zip')]
assert TE == 'False', 'ABORT: 远端解包根不是"本来不存在" ⇒ "只写不覆盖"那句不成立'
SCPX = g(SCE, r'SCP_EXIT=(\d+)', int)
assert SCPX == 0

# ---------- 双向差集 + 包↔现状（母件与子件同跑，互核） ----------
LL = g(LDA, r'LOCAL_LINES=(\d+) REMOTE_LINES=', int)
RL = g(LDA, r'LOCAL_LINES=\d+ REMOTE_LINES=(\d+)', int)
OL = g(LDA, r'ONLY_IN_LOCAL=(\d+) \[\]', int)
ORR = g(LDA, r'ONLY_IN_REMOTE=(\d+) ', int)
LDV = re.findall(r'VERDICT=(\w+)', txt(LDA))[-1]
IDENT = g(LDA, r'identical\(内容逐字节等,  sha256\) = (\d+)', int)
CHG = g(LDA, r'changed_since_cutoff = (\d+) ', int)
DEL = g(LDA, r'deleted_since_cutoff = (\d+) ', int)
NEWS = g(LDA, r'new_since_cutoff     = (\d+) \[', int)
NEWRAW = g(LDA, r'new_since_cutoff     = \d+ \[(.*?)\]')
NEWLIST = [x.strip().strip("'") for x in NEWRAW.split(', ') if x.strip()]
CAND = g(LDA, r'四桶互斥且并集 == 当前候选集\((\d+)\)', int)
LEOL = g(LDA, r'EOL  LOCAL bytes=(\d+) lines=(\d+) CRLF=(\d+)', str)
REOL = g(LDA, r'EOL  REMOTE\(剥后名单\) bytes=(\d+) lines=(\d+) CRLF=(\d+)', str)
VZ = re.search(r'EOL  VERIFY.*?bytes=(\d+) lines=(\d+) CRLF=(\d+)', txt(LDA))
assert VZ, 'ABORT: VERIFY 那行行尾读数取不到'
VZB, VZL, VZC = (int(x) for x in VZ.groups())
assert (LL, RL, OL, ORR, LDV) == (CF, CF, 0, 0, 'LISTDIFF_EQUAL'), 'ABORT: 差集不是 0-0'
assert (CHG, DEL, IDENT, len(NEWLIST)) == (0, 0, CF, NEWS), 'ABORT: 包 != 现状'
assert (g(CDF, r'identical\(内容逐字节等,  sha256\) = (\d+)', int),
        g(CDF, r'new_since_cutoff     = (\d+) ', int)) == (IDENT, NEWS), 'ABORT: 同一次跑的子件与母件读数不同'
assert CAND == CF + NEWS, 'ABORT: 候选集 != 载荷 + new_since'
# 名单自身也现读一遍行尾，别只信差集件里那行
lb = open(LNM, 'rb').read()
assert (lb.count(b'\n'), lb.count(b'\r\n')) == (LL, 0), 'ABORT: 载荷名单行尾读数与差集件不符'

# ---------- 往返复核 ----------
RTB = g(RTR, r'REMOTE_BYTES=(\d+) ', int)
RTMD5 = g(RTR, r'REMOTE_BYTES=\d+ md5=([0-9a-f]{32})')
LB_B = g(RTR, r'LOCAL_BYTES=(\d+) ', int)
LB_M = g(RTR, r'LOCAL_BYTES=\d+ md5=([0-9a-f]{32})')
RBT = g(RTR, r'BYTE_EQUAL_TO_WORKTREE=(\w+)')
RV = re.findall(r'VERDICT=(\w+)', txt(RTR))[-1]
HR = g(RTR, r'PROV_PASS_HITS_REMOTE=(\d+)', int)
HL = g(RTR, r'PROV_PASS_HITS_LOCAL=(\d+)', int)
CTRL = g(RTR, r'CONTROL_LANDER_HITS=(\d+)', int)
POS = g(RTR, r'POSITIVE_CONTROL_WORKTREE_HITS=(\d+)', int)
assert (LB_B, LB_M) == (RTB, RTMD5) and RBT == 'True' and RV == 'REMOTE_CARRIES_PLAINTEXT'
assert (HR, HL, CTRL, POS) == (1, 1, 0, 1), 'ABORT: 往返两侧命中/两把对照读数不符'
assert ROOT in txt(RTR) and TOP in txt(RTR), 'ABORT: 往返件路径不是本代根/包名'

# ---------- 载荷名单里到底有没有本批 paperwork（"paperwork 进载荷"这句的量法） ----------
PROBE_KEYS = ['updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md', 'dev_log/20260926.md',
              'hardware/r61_sync/scripts/land_r61_38.py', 'hardware/r61_sync/scripts/derive_r61b.py',
              'hardware/r61_sync/evidence/r61_roundtrip.txt', 'FreqErr.md',
              'hardware/20260919_墨水屏点屏排查记录.md', 'hardware/r61b_sync/scripts/sync_r61b.py']
_lnames = set(x.strip() for x in txt(LNM).splitlines() if x.strip())
assert len(_lnames) == LL, 'ABORT: 名单去重后只数与差集 LOCAL_LINES 不等（有重名行）'
MISSING_KEYS = [k for k in PROBE_KEYS if k not in _lnames]
assert not MISSING_KEYS, 'ABORT: 这些 paperwork 不在载荷名单里：%s' % MISSING_KEYS

# ---------- 现场态：git ----------
HEAD = git('rev-parse', '--short', 'HEAD').strip()
REVL = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
porc = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
MODN = len([l for l in porc if l.startswith(' M')])
STGN = len([l for l in porc if l.startswith('D ')])
UNTN = len([l for l in porc if l.startswith('??')])
assert len(porc) == MODN + STGN + UNTN, 'ABORT: porcelain 有未点名前缀：%s' % porc
assert STGN == 2, 'ABORT: 移出跟踪的 `D ` 行数不是 2（两只原厂镜像）：%d' % STGN
_un = [l[3:].strip() for l in porc if l.startswith('??')]
_U14E = len([p for p in _un if p.startswith('hardware/r61_sync/evidence/')])
_U14S = len([p for p in _un if p.startswith('hardware/r61_sync/scripts/')])
_U15 = len([p for p in _un if p == 'hardware/r61b_sync/'])
_ONREG = len([p for p in _un if p in ('.workbuddy/', 'Agent_readme.txt', 'dev_log/20260919.md')])
_UPD = len([p for p in _un if p.startswith('updates/')])
assert _U14E + _U14S + _U15 + _ONREG + _UPD == UNTN, 'ABORT: ?? 行没被五桶铺满：%s' % _un
U15E = len(git('ls-files', '--others', '--exclude-standard', 'hardware/r61b_sync/evidence').splitlines())
U15S = len(git('ls-files', '--others', '--exclude-standard', 'hardware/r61b_sync/scripts').splitlines())
assert _U15 == 1 and U15E == 12 and U15S >= 7, 'ABORT: 折叠目录展开后的只数与预期不符'

# ---------- 仓库外那批含明文的串口原始日志（现扫，不抄旧数） ----------
_sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(SRC, encoding='utf-8').read()).group(1).encode()
assert len(_sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
ESPL = os.path.join('C:', os.sep, 'esp')
_all = [f for f in os.listdir(ESPL) if f.endswith('.log')]
RAW = sorted(f for f in _all if _sec in io.open(os.path.join(ESPL, f), 'rb').read())
assert RAW, 'ABORT: `C:\\esp\\*.log` 一只含明文的都没有 ⇒ 这把尺没有样本（命中 0 ≠ 干净）'

# ---------- 在册前提：要引用的旧句按行号现查（不复抄全文） ----------
_h33 = _h34 = _obl = _rrtl = None
for i, l in enumerate(txt(TGT).splitlines(), 1):
    if l.startswith('### 38.33 '):
        _h33 = i
    if l.startswith('### 38.34 '):
        _h34 = i
    if '要么先把"同步证据落归档外"的机制建起来' in l:
        _obl = i
    if '自第 6 代起每代复现' in l:
        _rrtl = i
assert _h33 and _h34 and _obl and _rrtl, 'ABORT: 在册前提缺件 §38.33=%s §38.34=%s 义务=%s 往返口径=%s' % (
    _h33, _h34, _obl, _rrtl)
# 大写盲区的落点：现读被检件（行号 + 整行文本），不抄
_rb_lines = txt(RT_TOOL).splitlines()
_up = [i for i, l in enumerate(_rb_lines, 1) if 'R61_ROUNDTRIP_AT' in l]
assert len(_up) == 1, 'ABORT: 大写代次标记命中不是 1 处：%s' % _up
UPPER_LN = _up[0]
UPPER_TXT = _rb_lines[UPPER_LN - 1].strip()
assert '_prior' in txt(RT_TOOL), 'ABORT: "返工即新增载体"的机制不在位 ⇒ 不返工的论证失效'
NDRV = len(txt(DRV_TOOL).splitlines())
MINLINES = min(len(txt(os.path.join(SCRP, x)).splitlines()) for x in TOOLS)
TOOL_LINES = {x: len(txt(os.path.join(SCRP, x)).splitlines()) for x in TOOLS}
CHK_LINES = len(txt(os.path.join(SCRP, 'chk_r61b.ps1')).splitlines())

# ---------- 本文件行尾现场：三把尺各读一件事，全部现跑（正文那句"i/lf w/crlf"要有执行者） ----------
EOLATTR = git('ls-files', '--eol', '--', TGT).split()
assert len(EOLATTR) >= 3, 'ABORT: ls-files --eol 输出结构不符预期：%r' % EOLATTR
I_EOL, W_EOL = EOLATTR[0], EOLATTR[1]
_ns = git('diff', '--numstat', 'HEAD', '--', TGT).strip().split('\t')
assert len(_ns) == 3, 'ABORT: numstat 不是三列：%r' % _ns
ND_ADD, ND_DEL = int(_ns[0]), int(_ns[1])
assert ND_DEL == 0, 'ABORT: 落地前工作树相对 HEAD 已有删改行（+%d/−%d），"纯追加"这个前提不成立' % (ND_ADD, ND_DEL)

# ---------- 正文（每个数字都是上面现读并断言过的变量） ----------
TS = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
B = []
B.append('')
B.append(H35 + 'R61 尾巴·第 15 代 ht305 收口同步（现跑于 %s）：六只脚本改由**替换表派生**而非手抄，四道假 ABORT 全是"尺的形状不对"；'
               '本代是**第一次把描述上一代的 paperwork 装进载荷**的一代；五字段两侧全等、双向名单差集 0-0（远端**只写不删**、未 push）' % TS)
B.append('')
B.append('- **为什么要第 15 代（不是"再跑一遍看看"）**：第 14 代（r61final）载荷里**没有**描述它自己的那批 paperwork'
         '（第 %d / %d 行那两节，以及 `dev_log/20260926.md` 第三十三批、`updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md`、`FreqErr.md` 第十四批）'
         '——打包截止在那几段落盘之前 ⇒ "证据已同步"这句话在第 14 代载荷上**不成立**。本代把这句话钉成可复算的：'
         '对载荷名单 `%s`（去重后 %d 只，与差集 LOCAL_LINES 相等，本遍断言）逐只点名查 %d 只关键件，'
         'membership 全中（缺一只即 ABORT）⇒ **paperwork 这次真在载荷里**：服务器拿到的不只是"描述证据的脚本"，还包括脚本所描述的那批文档本体。' % (
             _h33, _h34, os.path.basename(LNM), len(_lnames), len(PROBE_KEYS)))
B.append('- **派生方式换了（本代的主要动作）**：上一代那 6 只是**手抄换名**，本代改由 `hardware/r61_sync/scripts/derive_r61b.py`（%d 行，盘上现读）'
         '按替换表逐字派生：A `r61`→`r61b` / B 远端根 `zsynctest16`→`17`、`zsynctest15`→`16`（**降序**，否则先写出的 `17` 会被后一条规则再吃一遍）/ '
         'C 代次 `第 14 代`→`第 15 代`、`第 13 代`→`第 14 代`、`gen-14`→`gen-15`（同样降序）/ D 指向封存归档的 `hardware/ht305_sync/scripts/`→本代目录 / '
         'E 余留 `r55`→`r61`。派生器自带三道反度量：上一代名字只许出现在**注释行**、六只 md5 两侧都打、`ht305_sync/scripts` 余留必须为 0；'
         '写盘排成两阶段（6 只先全部算完并裁决，再一次性写），因为前几遍失败时**已写的派生件留在盘上**——那正是"半套工具"的形态。' % NDRV)
B.append('- **派生遍读数（载体 `%s`：stdout 逐字转录 + 复核件）**：`WROTE=6`、`POINTERS_SCRIPTS=%d MISSING=0`、`VERDICT=DERIVED rc=0`；'
         '六只 mtime 同值 `%s`（转录那 6 行与本遍**另起一把尺**现读的六只 mtime 必须同集合 ⇒ "一次派生"有盘上出处）；'
         '本遍再装**第三把尺**：转录里 6 只的 `md5_dst` 与盘上现算 md5 逐只对（6/6 全等；前两把都在读同一张纸条，第三把读盘）。'
         '另有一条跨载体交叉：门算的是 TEMP 副本、派生器算的是仓库原件，两条独立路径给出同一只 `r61b_upload.ps1` 的同一个值 `%s`（前 8 位 `%s`）。' % (
             os.path.basename(DRV), PTR_S, DERIVE_MTIME, MDB, MDB[:8].lower()))
B.append('- **四道假 ABORT（每一条都是"我的尺形状不对"，被测件从头到尾没错，逐条点名）**：'
         '①守卫字面量有**两种形态**——`.py` 里写单引号包住的 `ht305_sync`、`.ps1` 里写带通配星的 `*ht305_sync*`（`-like` 用），'
         '尺只按前一种数 ⇒ 两只 `.ps1` 一起 ABORT 而守卫其实一只没丢；改成数**形态无关的整串子串**，另加一条 `ht305_sync/scripts` 余留 = 0 的反向度量。'
         '②断言**口径超出被测物**——要求 `sync_r61b.py` 含 `zsynctest17`，可它压根不碰远端根；改成"源里含 `zsynctest` 才要求"。'
         '③**下限从别的文件搬来**——`n_dst == n_src >= 50` 杀掉了只 %d 行的 `chk_r61b.ps1`；那个 50 是上一代**另一只件**的地板，'
         '而"派生没掉行"真正的尺是**等长**那条，下限只该挡"源被读空"（本代六只行数现读 %s，最小 %d）。'
         '④**代次标记也有两种写法**——`chk_r61b.ps1` 写的是 `gen-15 版` 而不是"第 15 代"；判据换成两种形态相加 >= 1。'
         '四条同族：**一把尺只量一种形态时，量不到就被判成不存在**——(76) 那条"命中 0 ≠ 干净"在断言侧的镜像。' % (
             CHK_LINES, ' / '.join('%s=%d' % (k, v) for k, v in TOOL_LINES.items()), MINLINES))
B.append('- **派生表的已知盲区（登记而不返工，理由写在这里）**：替换表 A 只换小写 `r61`，反度量 `OLD_TOKENS` 也全是小写形态 ⇒ '
         '大写代次标记对整套尺**隐形**。全树现扫命中 **1** 处：`r61b_roundtrip.py` 第 %d 行 `%s`（行号与整行文本都是本遍现读被检件，不是抄的）。'
         '**本代不返工**：这只脚本自带"输出名不许占用已有载体"的机制，返工要多落一只 `r61b_roundtrip_2.txt`，而那只载体的 `PRIOR_ATTEMPT` 句写的正是'
         '"前一只读数不作数"——用它去洗一只**其实作数**的读数，等于让载体说谎（(75) 那条不许拿重跑链洗绿）。'
         '该行**等号右侧的数值仍是当场跑的读数**（时刻见 `%s` 头部），错的只是标签前缀。改法记给下一版替换表：加 `R61`→`R61B`，并把大写形态纳入反度量。' % (
             UPPER_LN, UPPER_TXT, os.path.basename(RTR)))
B.append('- **派生遍的 stdout 一度没有载体（本代补的洞）**：`derive_r61b.py` 只 print 不写文件，rc=0 那遍跑完盘上**没有任何一份它的读数** ⇒ '
         '"读数不落盘等于没跑"的又一型（这次落盘的是**执行件**，缺的是**它的输出**）。补法 = `land_r61b_derive_report.py`：'
         '把转录逐字落进 `%s`（%s B / %d 行），并在同一只脚本里对转录做两把独立尺复核（md5 逐只、指针名单用同一套正则**在盘上重跑**做双向差集 0-0），'
         '全部断言排在写盘前 ⇒ 这一条"补的洞"自己也有载体可复算。' % (
             os.path.basename(DRV), format(os.path.getsize(DRV), ','), len(txt(DRV).splitlines())))
B.append('- **本代同步读数（本机算一份、远端解包后算一份，五字段逐字段 assert 全等）**：包 `%s.zip` = %s B / md5 `%s`；'
         '解包内容 %d 只 / %s B；聚合 sha256 = `%s`；`REMOTE_FORBIDDEN=%d`（禁传口径 `.log/.bin/.elf/.map/nvs.csv/^backups/`）；`EXTRACT_OK=%s`。'
         '时间线（本机侧）：打包截止 `%s` → 成品 zip `%s`；远端侧：开始 `%s` → 完成 `%s`（四个时刻一律取自载体原文，本遍不做时长换算）。'
         'zip 条目 %d 只（其中带 utf8 名字标记 %d 只）；git 候选名单 %d 只 / 重名 %d / drop %d 只 / copy failures %d。' % (
             TOP, format(ZSZ, ','), ZMD5, CF, format(CB, ','), AGG_L, RBAD, EXOK, CB1, CB2, RAT, RDAT, ZE, ZU,
             GL, DUP, DROPN, CFail))
B.append('- **双向名单差集与包↔现状（母件与子件同一次跑，互核过）**：`LOCAL_LINES=%d REMOTE_LINES=%d ONLY_IN_LOCAL=%d ONLY_IN_REMOTE=%d` ⇒ `%s`；'
         '逐只 sha256 比对 `identical=%d / changed_since_cutoff=%d / deleted_since_cutoff=%d` ⇒ 服务器那份**逐字等于**本机此刻的工作树；'
         'new_since %d 只（全是本代自产取证件，见下条）；当前候选集 %d 只 = 载荷 %d + new_since %d（本遍断言这条等式，另断言四桶互斥且并集 == 候选集）。'
         '行尾前置读数**原样登记不事后归一**：LOCAL 名单 `%s B`、REMOTE 剥后名单 `%s B`（两份都 CRLF=0），'
         'VERIFY（远端 stdout 落盘原件，差集就是从它切出来的）= %s B / %d 行 / CRLF=%d ⇒ '
         '"两侧先剥 `\\r` 再比"那句必须留在正文里，不然两份同形名单会被读成两份口径。' % (
             LL, RL, OL, ORR, LDV, IDENT, CHG, DEL, NEWS, CAND, CF, NEWS, LEOL, REOL,
             format(VZB, ','), VZL, VZC))
B.append('- **远端动作半径（本节唯一涉及共享系统的部分，逐条点名）**：探测 `TARGET_EXISTS=%s`（不覆盖任何既有产物）⇒ scp `SCP_EXIT=%d` ⇒ '
         '解包进**全新**根 `%s`（上一代是 `zsynctest16`，每代一个新根，**绝不清空、绝不删除**，脚本里 `Test-Path` 命中即 `exit 1`）；'
         '服务器桌面本遍现读文件 %d 只，其中同步包 `zizhao_*.zip` **%d 只并存**（含本代那只）；**零删除、零覆盖**。' % (TE, SCPX, ROOT, len(desks), len(zn)))
B.append('- **往返复核（"远端到底带不带明文"这句话唯一的量法，第 %d 行那句在册口径"自第 6 代起每代复现"的又一次复现）**：'
         '把远端解包件 `provision_ap.c` 抓回 %%TEMP%% 与工作树逐字比 ⇒ 远端 %d B / md5 `%s`，本机 %d B / md5 `%s`，`BYTE_EQUAL_TO_WORKTREE=%s`；'
         '同尺命中数远端 %d / 本机 %d（阳性 = 已知脏的工作树原件 hits=%d；阴性 = 本代按宏名读口令的 `sync_r61b.py` hits=%d），判决 `%s` ⇒ '
         '**服务器不是回滚源，本仓库任何一只都绝不 push**。（这条与"载荷里不许有明文"是两件事：载荷取的是工作树，而工作树里那只 `.c` 本来就把宏值写在盘上。）' % (
             _rrtl, RTB, RTMD5, LB_B, LB_M, RBT, HR, HL, POS, CTRL, RV))
B.append('- **门与上传件（`%s`）：本代执行的是仓库里那一只**：`CHK_AT=%s`、`FIRST3=%s`（UTF-8 BOM 那三字节——含中文的 `.ps1` 没 BOM 会被 5.1 按 GBK 解并吞掉下一整行）、'
         '`UTF8_BOM=%s`、`PARSE_ERRORS=%d`、`REMOVE_ITEM_HITS=%d`（远端命令里不许出现 Remove-Item）、`SCRIPT_LINES=%d == SRC_LINES=%d`'
         '（TEMP 副本与仓库原件等长 ⇒ 解析结果描述的就是被执行的那只）。' % (
             os.path.basename(PCH), CHK_AT, FIRST3, BOM, PE, RIH, SL, SRC_L))
B.append('- **载荷里没有的东西（点名，别把"传上去了"读成"什么都传上去了"）**：'
         '① **%d 只含 `PROV_PASS` 明文的串口原始日志只存在于 `C:\\esp\\` 顶层 `*.log`**（本遍现扫 %d 只顶层日志，逐只按宏体现读、**不递归子目录**，'
         '口径边界就写在这里；永不 stage / 永不 push / 永不删除）⇒ ht305 上的是**脱敏取证件**，不是这些原始日志；'
         '②`backups/` 整目录（`.gitignore:19`，仓库外只落盘；载体里 `any backups/nvs = %s %s` 是本遍断言过的读数）；'
         '③两只原厂整片镜像（从第 %d 行起那一节记录的"移出跟踪"，`.gitignore` 按准确文件名排除，禁传表口径亦覆盖 `.bin`）；'
         '④本代自产的 %d 只取证件（打包截止**之后**才落盘，`r61b_cutoff_delta.py` 的 new_since 桶逐只点名，本遍核对只数与母件一致）；'
         '⑤同步排除表 drop 的 %d 只：%s（**逐字取自 `%s` 的 dropped 行，不另列一份**）。' % (
             len(RAW), len(_all), NBK, NLOG, _h33, NEWS, DROPN,
             '、'.join('`%s`' % x for x in DROPNAMES), os.path.basename(LOC)))
B.append('- **现场态（本遍同一刻现跑）**：HEAD `%s`、`git rev-list --count origin/main..HEAD` = **%d**（全未 push）；'
         '`git status --porcelain` = %d 行 = ` M` %d + `D ` %d + `??` %d，五桶铺满并断言无剩余：第 14 代取证件 %d / 第 14 代脚本 %d / '
         '第 15 代**整目录折叠成 1 行**（`ls-files --others` 现数 = 取证件 %d + 脚本 %d 只）/ 在册排除项 %d（`.workbuddy/` 折叠行、`Agent_readme.txt`、`dev_log/20260919.md`）/ '
         '`updates/` 新归档件 %d。**porcelain 那 1 行 != 1 只**：折叠目录的真实只数只认 `git ls-files --others`，本遍把这条差异写进断言而不是写进注释。' % (
             HEAD, REVL, len(porc), MODN, STGN, UNTN, _U14E, _U14S, U15E, U15S, _ONREG, _UPD))
B.append('- **本文件行尾现场（追加体行尾为什么这一遍换）**：本遍现读 `%s` = 盘上 %d 行、**全部 CRLF**（裸 LF 行数 0，见下面写盘前的现读断言）、'
         '末行以 CRLF 收尾；而 `git ls-files --eol` 现读给的是 `%s %s` ⇒ 索引侧纯 LF、工作树侧被本机 `core.autocrlf=true` 展开成 CRLF。'
         '第 %d / %d 行那两节落盘时（12:48:0x）现读到的是"末行裸 LF"因此追加体写的裸 LF，此刻同一份文件已是全 CRLF'
         '（本遍现跑 `git diff --numstat HEAD` = +%d / −0 ⇒ 那两节的 LF 追加体现在也读成 CRLF，而**行尾差异一行都不进 diff**，两把量具互核过）。'
         '**本遍据此现读重选追加体行尾为 CRLF，不继承"上一遍写的是 LF"这个记忆**——行尾是一把会被外部动作挪动的尺，'
         '两遍之间它变了，而"我上一遍选的肯定还对"正是这一族的错法。' % (
             os.path.basename(TGT), txt(TGT).count('\n'), I_EOL, W_EOL, _h33, _h34, ND_ADD))
B.append('- **本遍没做（点名）**：没烧录、没碰串口（板上仍是第 %d 行那一节提到的那只出厂镜像，本遍未复查它还在不在）；'
         '人眼看到第二页 = 0 次、用户真按 BOOT = 0 次 ⇒ **不播提示音的判据仍成立**；'
         '`hardware/ht305_sync/` 归档链本代**不重跑**（SEAL 停在 gen 24，本代不新建清单代，六只脚本各自的守卫都带这条 ABORT）；'
         '`todo.md`/`done.md`/`FreqErr.md` 第十五批的收口在别的任务里；未 push、未 amend。' % _h34)

BODY = '\n'.join(B)

# ---------- 裁决全部排在写盘之前 ----------
pre = io.open(TGT, 'rb').read()
pre_lines, pre_bytes = pre.count(b'\n'), len(pre)
if H35.encode('utf-8') in pre:
    raise SystemExit('ABORT: §38.35 已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\n'):
    raise SystemExit('ABORT: 既有正文末行不以换行收尾，直接追加会粘行')
_sec_s = _sec.decode('utf-8')
assert _sec_s not in BODY, 'ABORT: 正文含口令明文'
bb = (BODY + '\n').encode('utf-8')
assert _sec not in bb, 'ABORT: 正文含口令明文（字节侧）'
# 行尾口径与写盘口径必须一致：现读裸 LF 行数与末行收尾，两者共同决定追加体用什么。
_eolc = pre.count(b'\r\n')
_bare = pre_lines - _eolc
assert pre.endswith(b'\r\n') and _bare == 0, 'ABORT: 盘上不是"全 CRLF 且末行 CRLF"（bareLF=%d），本遍的 CRLF 追加体不成立'
assert (I_EOL, W_EOL) == ('i/lf', 'w/crlf'), 'ABORT: 行尾现场与本遍叙述不符：%s %s' % (I_EOL, W_EOL)
bb = bb.replace(b'\n', b'\r\n')
_exp_lines = pre_lines + BODY.count('\n') + 1
_exp_bytes = pre_bytes + len(bb)
assert bb.count(b'\r\n') == _exp_lines - pre_lines, 'ABORT: 追加体自身行尾不齐'

io.open(TGT, 'ab').write(bb)
chk = io.open(TGT, 'rb').read()
post_lines, post_bytes = chk.count(b'\n'), len(chk)
assert chk[:pre_bytes] == pre, 'ABORT: 前缀被改动（本脚本自称纯追加器，这条是事后复算）'
assert (post_lines, post_bytes) == (_exp_lines, _exp_bytes), 'ABORT: 落盘后行数/字节数与写盘前算的期望不符（%d/%d vs %d/%d）' % (
    post_lines, post_bytes, _exp_lines, _exp_bytes)
assert chk.count(b'\r\n') == post_lines, 'ABORT: 落盘后文件不再"全 CRLF"'
# 事后第三把尺：仓库侧的口径也必须只看到新增行（若行尾差异会进 diff，这里就会 −N）
_ns2 = git('diff', '--numstat', 'HEAD', '--', TGT).strip().split('\t')
assert int(_ns2[1]) == 0 and int(_ns2[0]) == ND_ADD + (post_lines - pre_lines), \
    'ABORT: 落盘后 git 侧不是纯新增（+%s/−%s，期望 +%d/−0）' % (_ns2[0], _ns2[1], ND_ADD + post_lines - pre_lines)
print('EOL_BEFORE CRLF=%d bareLF=%d | EOL_APPEND=CRLF(接缝现读为 CRLF)' % (_eolc, _bare))
print('TGT_LINES %d -> %d | TGT_BYTES %d -> %d' % (pre_lines, post_lines, pre_bytes, post_bytes))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('ADDED_BYTES=%d ADDED_LINES=%d | git numstat 前 +%d/−0 后 +%s/−%s' % (
    post_bytes - pre_bytes, post_lines - pre_lines, ND_ADD, _ns2[0], _ns2[1]))
print('PROBE_KEYS_ALL_IN_PAYLOAD=%d | PAYLOAD_NAMES=%d | ESP_LOG=%d/%d | PORCELAIN=%d' % (
    len(PROBE_KEYS), len(_lnames), len(RAW), len(_all), len(porc)))
print('VERDICT=LANDED rc=0')
