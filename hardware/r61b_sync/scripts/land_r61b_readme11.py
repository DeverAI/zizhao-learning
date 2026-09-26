# 落地器：往 `backups/README.md` §1 的"读数"链**第十次读数之后**插入第十一次读数一整格（本格 ①~⑪ + 一句判定）。
# 与 §38.x 那些**纯追加**落地器的区别：README 的读数格必须按时间顺序待在 §1 内部（"## 2. 命名规则"在它后面）⇒
#   这是一次**文件中部插入**，"前缀未动"那条证明不够用，所以本遍另做两件事：
#   ①写盘前把 README **原样**复制一只 pre-image 进 `hardware/r61b_sync/evidence/`（"可逆"要有盘上快照，不能只靠断言）；
#   ②事后证明分三段：插入点之前逐字等、插入体逐字等、插入点之后逐字等。
# 三条老规矩照守：幂等门先查"第十一次读数"在不在；全部裁决排在写盘之前；正文里每个数都从当轮载体现读并断言，不手抄。
import datetime
import glob
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
RM = os.path.join(REPO, 'backups', 'README.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
SRC = os.path.join(MAIN, 'provision_ap.c')
BUILD = r'C:/esp/zproj/build'
ANCHOR = '\n## 2. 命名规则\n'
# 幂等门的令牌不含时刻（时刻每遍都变，含时刻的门重跑就等于没门）。
GATE = '第十一次读数'
HEAD11 = '【09-26 **%s %s**' % (datetime.datetime.now().strftime('%H:%M:%S'), GATE)


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr)
    return r.stdout


def sh(*a):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace')
    assert r.returncode in (0, 1), 'ABORT %s rc=%d %s' % (a, r.returncode, r.stderr)
    return [l for l in r.stdout.splitlines() if l.strip()]


def carrier(prefix, must):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 载体 %r 含 %r 的命中 %d 只（应为 1）：%s' % (
        prefix, must, len(hits), [os.path.basename(x) for x in hits])
    return hits[0]


def g(path, pat, cast=None):
    txt = io.open(path, encoding='utf-8', errors='replace').read()
    m = re.search(pat, txt)
    assert m, 'ABORT: 载体 %s 里取不到 %r' % (os.path.basename(path), pat)
    return cast(m.group(1)) if cast else m.group(1)


# ---------- 五把尺：全部现跑 ----------
# ① 相对 HEAD
_ns = [l.split('\t') for l in git('diff', 'HEAD', '--numstat', '--', 'hardware/zizhao-esp32s3/main').strip().splitlines()]
N1, ADD1, DEL1 = len(_ns), sum(int(x[0]) for x in _ns), sum(int(x[1]) for x in _ns)
NAMES1 = [os.path.basename(x[2]) for x in _ns]
assert N1 == 1 and NAMES1 == ['provision_ap.c'], 'ABORT: ① 那格口径变了（名单 %s）⇒ "只有那只 dirty 文件"这句前提要重读' % NAMES1
# ②③⑤ 四把 diff -rq 镜像尺
ROTS = {
    'r43-A': os.path.join(REPO, 'backups', 'r43_20260922_131029', 'main'),
    'r43-B': os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups', 'r43_20260922_131029', 'main'),
    'r53-A': os.path.join(REPO, 'backups', 'r53_20260924_083929', 'main'),
    'r53-B': os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups', 'r53_20260924_083929', 'main'),
    'r59pre-A': os.path.join(REPO, 'backups', 'r59_pre_20260925_175032', 'main'),
    'r59post-A': os.path.join(REPO, 'backups', 'r59_post_20260925_184900', 'main'),
    'r59post-B': os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups', 'r59_post_20260925_184900', 'main'),
    'sourceonly': os.path.join(REPO, 'backups', 'r44_sourceonly_20260923_084628', 'main'),
}
DIF = {}
for k, p in ROTS.items():
    assert os.path.isdir(p), 'ABORT: 镜像尺 %s 的根不存在 %s' % (k, p)
    DIF[k] = len(sh('diff', '-rq', p, MAIN))
# 新落的那对全根（本遍的主角）：两根各 0 行 = 它是**唯一**与工作树逐字同值的全根
NEWR = carrier('r61b_verify_root_*.txt', 'VERDICT=ROOT_VERIFIED')
DA = g(NEWR, r'DIFF_RQ_A_vs_worktree=(\d+) 行', int)
DB = g(NEWR, r'DIFF_RQ_B_vs_worktree=(\d+) 行', int)
assert (DA, DB) == (0, 0), 'ABORT: 新根与工作树不等（A=%d B=%d）⇒ 本遍"新建根"的前提不成立' % (DA, DB)
ROOTNAME = g(NEWR, r'ROOT_NAME (\S+)')
ROOT_N = g(NEWR, r'FILES_PER_ROOT=(\d+)', int)
ROOT_MAIN = g(NEWR, r'FILES_PER_ROOT=\d+ \(main/ (\d+) 只', int)
ROOT_B = g(NEWR, r'BYTES_PER_ROOT=(\d+)', int)
BINM = g(NEWR, r'BIN md5=([0-9a-f]{32})')
BINSZ = g(NEWR, r'BIN md5=[0-9a-f]{32} / (\d+) B', int)
B176 = g(NEWR, r'bin\[176:184\]=([0-9a-f]{16})')
OLDBIN = g(NEWR, r'OLD r59_post bin md5=([0-9a-f]{32})')
assert BINM != OLDBIN, 'ABORT: 新根与旧那只 bin 同值 ⇒ "板上镜像此前盘上无副本"这句是假的'
# ④ 工作树 main/ 体量（python 现读，排除派生字节）
_wf = [os.path.join(r, x) for r, _d, fs in os.walk(MAIN) for x in fs
       if '__pycache__' not in os.path.join(r, x) and not x.endswith('.pyc')]
WN, WB = len(_wf), sum(os.path.getsize(f) for f in _wf)
assert WN == ROOT_MAIN, 'ABORT: 工作树 main/ 只数 %d != 新根 main/ 只数 %d（两根不是同一时刻的镜像）' % (WN, ROOT_MAIN)
# ④b "多的那几只"不许手抄：拿工作树名单与 09-24 那根（末次记为 30 只的那把尺）的名单现读做双向差集。
_ref = os.path.join(REPO, 'backups', 'r53_20260924_083929', 'main')


def _names(top):
    return {os.path.join(r, x)[len(top) + 1:].replace(os.sep, '/')
            for r, _d, fs in os.walk(top) for x in fs
            if '__pycache__' not in r and not x.endswith('.pyc')}


_refn = _names(_ref)
_extra = sorted(_names(MAIN) - _refn)
_gone = sorted(_refn - _names(MAIN))
assert len(_refn) == 30 and len(_extra) == WN - 30 and not _gone, \
    'ABORT: 名单差集不是"纯增 %d 只"（参照根 %d 只 / 多 %d 只 / 少 %d 只）⇒ "多的那几只"这句要重写' % (
        WN - 30, len(_refn), len(_extra), len(_gone))
# ⑥ git 侧现场态
HEAD = git('rev-parse', '--short', 'HEAD').strip()
REVL = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
PORC = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
PN, PM, PD, PU = (len(PORC), len([l for l in PORC if l.startswith(' M')]),
                  len([l for l in PORC if l.startswith('D ')]), len([l for l in PORC if l.startswith('??')]))
assert PN == PM + PD + PU, 'ABORT: porcelain 四类没有铺满（M %d + D %d + ?? %d != %d）⇒ 冒出了没点名的状态字母' % (
    PM, PD, PU, PN)
# ⑦ docs 第十一遍快照（现读那一遍的 stdout 载体，不抄旧数）
DS = carrier('r61b_docs_snapshot11_*.txt', 'TABLE_ROWS')
DAT = g(DS, r'SNAPSHOT_AT (2026-\d\d-\d\d \d\d:\d\d:\d\d)')
DFS = g(DS, r'FILES (\d+)', int)
DTR = g(DS, r'TABLE_ROWS (\d+)', int)
DNO = g(DS, r'NEW_ONES (\d+)', int)
DGA = g(DS, r'CRED_GATE HITS=0 OF (\d+)', int)
assert DGA == DFS == DTR and DNO == 8, 'ABORT: docs 快照三数互不咬合（闸 %d / FILES %d / 表行 %d / NEW %d）' % (DGA, DFS, DTR, DNO)
DDIR = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
DN = len(os.listdir(DDIR))
assert DN == DFS + 1, 'ABORT: docs/ 目录现读 %d 只 != 表格 %d + NOTE（自核等式不成立）' % (DN, DFS)
# "本代新入哪几只"从 NOTE 的 `NEW -> ` 行现读，不照上一代正文手抄。
NEWROWS = [l.split('\t')[0] for l in io.open(os.path.join(DDIR, 'SNAPSHOT_NOTE.txt'), encoding='utf-8').read().splitlines()
           if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]{8}\tNEW -> \d+$', l)]
assert len(NEWROWS) == DNO == 8 and len(set(NEWROWS)) == 8, \
    'ABORT: NOTE 里 NEW 行 %d 只 != stdout 的 NEW_ONES %d ⇒ 这只名单不能用' % (len(NEWROWS), DNO)
# ⑨ 串口现场态（只读枚举）
PORTS = subprocess.run([sys.executable, '-m', 'serial.tools.list_ports'], cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
PORTLIST = sorted(re.findall(r'^(COM\d+)\s*$', PORTS, re.M))
# 命中 0 ≠ 干净：解析不出一只 COM 名时 `COM14 在位=False` 会说谎，那是**解析失败**不是缺席。
assert PORTLIST, 'ABORT: 端口枚举没解析出任何 COM 名 ⇒ 本遍"COM14 缺席"这句不能用（原文 %r）' % PORTS[:120]
COM14 = 'COM14' in PORTLIST
# ⑩ 封界：`hardware/ht305_sync/` 里最新一只的 mtime 必须仍停在 gen 24 那一刻（本代未落一字节）
_HT = os.path.join(REPO, 'hardware', 'ht305_sync')
_htf = [os.path.join(r, x) for r, _d, fs in os.walk(_HT) for x in fs]
_htnew = max(_htf, key=lambda p: os.path.getmtime(p))
HTN, HTMT, HTMAX = len(_htf), datetime.datetime.fromtimestamp(os.path.getmtime(_htnew)), os.path.relpath(_htnew, REPO).replace('\\', '/')
assert HTMT < datetime.datetime(2026, 9, 25), 'ABORT: ht305_sync 里有 09-25 之后的字节（最新 mtime %s / 那只 %s）⇒ 末版被污染' % (
    HTMT, HTMAX)

# ⑫ 与"第十次"那一格比对的六个数**也不手抄**：从 README 自己的第十次那一格现读（本遍唯一允许的旧数来源 = 台账本体）。
pre = io.open(RM, 'rb').read()
_p0 = pre.decode('utf-8')
_i10 = _p0.index('【09-25 **15:37:12 第十次读数**')
assert _p0.count('【09-25 **15:37:12 第十次读数**') == 1, 'ABORT: 第十次那一格的标题不唯一 ⇒ 旧数边界没了'
_P10 = _p0[_i10:_p0.index(ANCHOR)]


def p10(pat, grp=1, cast=str):
    m = re.search(pat, _P10)
    assert m, 'ABORT: 第十次那一格里取不到 %r ⇒ 本格"与第十次相比"的句式前提没了' % pat
    return cast(m.group(grp))


def p10all(pat):
    m = re.search(pat, _P10)
    assert m, 'ABORT: 第十次那一格里取不到 %r ⇒ 本格"与第十次相比"的句式前提没了' % pat
    return tuple(int(x) for x in m.groups())


P_N, P_ADD, P_DEL = p10all(r'\*\*(\d+) 只 / \+(\d+) / −(\d+)\*\*')
P_R43A, P_R43B = p10all(r'根 A / 根 B = \*\*(\d+) / (\d+) 行\*\*')
P_WN = p10(r'\*\*(\d+) 只 / ([\d,]+) B\*\*（python 现读', 1, int)
P_WB = p10(r'\*\*(\d+) 只 / ([\d,]+) B\*\*（python 现读', 2)
P_SRC = p10(r'仍 \*\*(\d+) 行 differ\*\*', cast=int)
P_REV = p10(r'现跑 = \*\*(\d+)\*\*（未 push）', cast=int)
P_PORC = p10(r'= \*\*(\d+) 行\*\*（', cast=int)
P_DN, P_DTR = p10all(r'目录现读 \*\*(\d+) 只\*\* = 表格 \*\*(\d+) 行\*\*')
assert (P_N, P_WN, P_DN, P_DTR) == (1, 30, 42, 41), \
    'ABORT: 第十次那一格现读的四个锚值 (①只数,④只数,⑦只数,⑦行) = %s 与预期 (1,30,42,41) 不符 ⇒ 上面这些正则抓错了字段' % (
        (P_N, P_WN, P_DN, P_DTR),)

# ---------- 正文 ----------
B = []
B.append(HEAD11 + '｜**"零代码进工作树"这条判据自 R58 起断了：R58~R61 四批有真代码进镜像并 6 烧 6 抓 ⇒ 本遍新建一对全根 `' + ROOTNAME + '`**；'
                  '五把尺本遍逐把现跑，其中三把与第十次**不同值**（不同值才是这一代的真相）】')
B.append('① **相对 `HEAD`（%s）**：`git diff HEAD --numstat -- hardware/zizhao-esp32s3/main` ⇒ **%d 只 / +%d / −%d**，'
         '名单现读 = `%s` 一只（自带 `PROV_PASS` 宏值、每轮被逐只点名 DROP，宏值只进工作树永不进 git 侧）⇒ 名单与第十次同形；'
         '那次的三个数（%d 只 / +%d / −%d）由本遍从第十次那一格**现读**，差值 **+%d / −%d** 是两把尺相减得来的（R58~R61 四批都往这只文件里加过语义，'
         '本遍不逐批拆分）。' % (HEAD, N1, ADD1, DEL1, NAMES1[0], P_N, P_ADD, P_DEL, ADD1 - P_ADD, DEL1 - P_DEL))
B.append('② **相对 r43 那两根**：`diff -rq` 根 A / 根 B = **%d / %d 行**（第十次是 %d / %d，由本遍现读那一格）⇒ '
         '两根继续当 09-22 20:55 那一烧的历史输入，**不刷新**。' % (DIF['r43-A'], DIF['r43-B'], P_R43A, P_R43B))
B.append('③ **相对 r53 那两根**：同一命令 = **%d / %d 行**（第八、九、十次连三次 0 / 0 的那条链到此**断了**）⇒ '
         'R59~R61 的代码确实改动了 `main/`，r53 那两根**不再**是当前镜像的构建输入；这一格从"判据"降级成"历史"。' % (
             DIF['r53-A'], DIF['r53-B']))
B.append('④ **工作树 `main/` 体量**：**%d 只 / %s B**（第十次那一格现读回来 = %d 只 / %s B）⇒ 比 `backups/r53_20260924_083929/main`'
         '（末次记下"30 只"那把尺）多的那 %d 只是 `%s`——**这几只名字由本遍现读两侧名单做双向差集得出**（参照根 30 只、反向差集为空 ⇒ 纯增，'
         '不是"少了几只又多了几只"），不是照第十次那格手抄的。它们就是 R59-5 那块 1.54 吋屏的移植件与板型开关头'
         '（**这一格就是历代"零代码进工作树"那句话的量具，本遍它第一次不为零**）。' % (
             WN, format(WB, ','), P_WN, P_WB, len(_extra), '`、`'.join(_extra)))
B.append('⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main …` ⇒ 仍非 0（**%d 行**，第十次那一格 %d 行）⇒ 那条 ⚠ 条件继续成立，'
         '它记的是"09-23 08:46 那一刻的镜像"，**不顺手修**（动历史镜像 = 造第二把尺）。' % (DIF['sourceonly'], P_SRC))
B.append('⑥ **本遍新建的那对全根**（`backups/%s` = 根 A、`hardware/zizhao-esp32s3/backups/%s` = 根 B）：'
         '每根 **%d 只 = main/ %d 只 + 构建产物 3 只（.bin/.elf/.map）** / %s B；A/B 两根**名单相同、逐只 md5 全等**（本遍现跑 35 只逐只比），'
         '两根各自 `diff -rq …/main 工作树 main` = **%d / %d 行** ⇒ 它是**盘上唯一**与工作树逐字同值的全根。' % (
             ROOTNAME, ROOTNAME, ROOT_N, ROOT_MAIN, format(ROOT_B, ','), DA, DB))
B.append('⑦ **为什么非建不可（不是"到点了建一根"）**：板上此刻在跑的那只 = **md5** `%s` / %s B / `bin[176:184]=%s`'
         '（身份等式见 §38.32，那是 R61 六烧六抓里唯一仍在盘上的产物）；而建遍之前盘上最近一只**带产物的全根** `'
         'r59_post_20260925_184900` 里那只 bin 是 `%s` ⇒ **板上那只镜像在仓库外曾经一只副本都没有**'
         '（构建目录 `C:\\esp\\zproj\\build\\` 会被下一次构建覆盖，那不是归档）。R61 那两处（`r61_pre_20260926_102058/main` 4 只、'
         '`r61b_20260926_104357/eink_display.c` 1 只）是**改前单只快照**、不是全根，量不出"回滚到此刻"。**旧根一只没覆写、一只没删。**' % (
             BINM, format(BINSZ, ','), B176, OLDBIN))
B.append('⑧ **建根这一遍自己出的两处缺陷（点名，不藏）**：'
         '(a) 创建器用 `os.path.relpath(f, MAIN)` 当目标相对路径 ⇒ 该路径**天然不含 `main/` 前缀** ⇒ 32 只源码平铺到根顶层；'
         '能抓到它的那道 `diff -rq …/main 工作树/main` **排在写盘之后**，所以根先落地、复核才崩（`NameError: subprocess` 那次连复核都没跑到）。'
         '(b) 复核器头两道断言是 `set(ta)==set(tb)` 与 `all(ta[k]==tb[k])` —— 两边**同时为空时恒真**，'
         '真正把它拽住的是后面那只**正向钉** `MAIN_N == 32`。修法：搬移遍（不删不覆写、逐只 md5 回读，`main/` 已存在即 ABORT）'
         '+ 创建器补两处守卫：**目标名带秒级时间戳 ⇒ "目标不存在"永真、重跑就多造一对 ⇒ 幂等门改成按前缀扫**、'
         '源只数加正向区间 `[30,40]`。取证 = `hardware/r61b_sync/evidence/` 的 `r61b_make_root_*`（含崩溃那次）、'
         '`r61b_root_layout_fix_*`、`r61b_verify_root_*`（末值 %s）。' % os.path.basename(NEWR))
B.append('⑨ **docs/ 快照第十一遍**（本遍之前刚跑，`hardware/refresh_docs_snapshot_r61b.py` = 派生自 `…_r57.py`，'
         '派生器 `hardware/r61b_sync/scripts/derive_docs_r61b.py`，替换表 6 条、表外零改动 `STRAYS=0`）：'
         '目录现读 **%d 只** = 表格 **%d 行** + `SNAPSHOT_NOTE.txt`（等式 %d+1=%d 由本遍现跑 assert；第十次那一格现读回来 = %d 只 / %d 行）、'
         '`SNAPSHOT_AT %s`、凭据闸 **%d 只源全扫 / HITS=0**。本代新入的 %d 只（名单由本遍从 `SNAPSHOT_NOTE.txt` 的 `NEW -> ` 行现读，'
         '不手抄）：`%s`；R56/R57-E 各有一只同名 v1，**v1 不进快照只进 v2**。python 走一遍 `backups/` 数 `__pycache__`/`.pyc` = 0（搬移遍顺带核过）。' % (
             DN, DTR, DTR, DN, P_DN, P_DTR, DAT, DGA, len(NEWROWS), '`、`'.join(NEWROWS)))
B.append('⑩ **串口与封界现场态**：`python -m serial.tools.list_ports` 现跑 = `%s` ⇒ **COM14 在位 = %s**'
         '（枚举解析出 %d 只 COM 名，"命中 0"那种假缺席本遍由 assert 挡在写盘之前；第十次那格"COM14 回来了"到此又被覆盖：'
         '本遍之后**没有新的串口动作**，§38.32 六烧六抓不在本遍）；'
         '`hardware/ht305_sync/` 现读 %d 只、目录内最新一只的 mtime = %s（那只叫 `%s`）'
         '⇒ gen 24 之后**一字节未落**、本代不新建清单代；本遍所有取证落 `hardware/r61b_sync/evidence/`。' % (
             ', '.join(PORTLIST), str(COM14), len(PORTLIST), HTN, HTMT.strftime('%Y-%m-%d %H:%M:%S'), HTMAX))
B.append('⑪ **git 侧配套读数（现跑）**：HEAD = `%s`，`rev-list --count origin/main..HEAD` = **%d**（第十次那一格 %d）⇒ **未 push、未 amend**；'
         '`status --porcelain` = **%d 行**（` M` %d + `D ` %d + `??` %d，四类由本遍 assert 铺满；第十次那一格 %d 行）⇒ 两代行数不可跨代换算成"几只文件"，'
         '那条点名（`--porcelain` 对未跟踪目录按目录折叠）本遍继续适用。' % (
             HEAD, REVL, P_REV, PN, PM, PD, PU, P_PORC))
B.append('⇒ 判定**变了**：**新建一对全根**（本遍唯一涉及磁盘大量写入的动作），**不重建镜像、不重烧、不覆写任何旧根**；'
         '本遍真正落地的 = 新根一对 + docs 第十一遍 + 本格（第十一次读数）。'
         '**没烧录、没碰串口**（%s）⇒ 屏亮肉眼确认仍 **1 次**（R59 那一次，本遍没推进）、看到第二页 **0 次**、'
         '用户真按 BOOT **0 次** ⇒ **不播提示音的判据仍成立**；**未 `git push`**、未 amend、**零删除**（含 `%%TEMP%%` 与各臂抓回原件）。' % (
             'COM14 本遍不在位' if not COM14 else 'COM14 本遍在位，但本遍零串口动作'))
BODY = '\n'.join(B) + '\n'

# ---------- 裁决排在写盘之前（`pre` = 上面 ⑫ 那把尺读过的那一只，不再二次读取，避免"旧数来自 A 遍、写盘针对 B 遍"） ----------
if GATE.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十一次读数已在册（幂等门），本遍不叠加')
assert pre.count(b'\r') == 0, 'ABORT: README 带 CR，本插入体是按 LF 写的'
assert pre[:3] != b'\xef\xbb\xbf', 'ABORT: README 有 BOM'
assert pre.endswith(b'\n'), 'ABORT: README 末行不以换行收尾'
assert pre.count(ANCHOR.encode('utf-8')) == 1, 'ABORT: 插入锚 %r 命中数不是 1' % ANCHOR
_idx = pre.index(ANCHOR.encode('utf-8'))
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(SRC, encoding='utf-8').read()).group(1)
assert sec and len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
bb = BODY.encode('utf-8')
assert sec.encode('utf-8') not in bb, 'ABORT: 正文含口令明文'
assert b'\r' not in bb, 'ABORT: 插入体带 CR'
assert not re.search(rb'%[sdf]', bb), 'ABORT: 插入体里残留未插值的 %% 占位符'
_exp_bytes = len(pre) + len(bb)
_exp_lines = pre.count(b'\n') + BODY.count('\n')
# pre-image 快照（"可逆"要落在盘上，不能只靠事后断言）
_ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'readme_pre11_%s.md' % _ts)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'

io.open(RM, 'wb').write(pre[:_idx] + bb + pre[_idx:])
chk = io.open(RM, 'rb').read()
assert chk[:_idx] == pre[:_idx], 'ABORT: 插入点之前被改动'
assert chk[_idx + len(bb):] == pre[_idx:], 'ABORT: 插入点之后被改动'
assert (chk.count(b'\n'), len(chk)) == (_exp_lines, _exp_bytes), 'ABORT: 落盘后行/字节与写盘前算的期望不符'
assert hashlib.md5(io.open(PIMG, 'rb').read()).hexdigest() == hashlib.md5(pre).hexdigest(), 'ABORT: pre-image 与写盘前原件不等'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('README 行 %d -> %d | 字节 %d -> %d | md5 %s -> %s' % (
    pre.count(b'\n'), chk.count(b'\n'), len(pre), len(chk),
    hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('插入点之前逐字等=OK 插入体逐字等=OK 插入点之后逐字等=OK')
print('五把尺现跑：①+%d/−%d ②%d/%d ③%d/%d ④%d 只 %d B ⑤%d 行 ⑥新根 A/B diff=%d/%d' % (
    ADD1, DEL1, DIF['r43-A'], DIF['r43-B'], DIF['r53-A'], DIF['r53-B'], WN, WB, DIF['sourceonly'], DA, DB))
print('COM14=%s 端口=%s | ht305_sync %d 只 / 最新 mtime %s（gen 24 后零落字节）' % (COM14, PORTLIST, HTN, HTMT))
print('VERDICT=LANDED rc=0')
