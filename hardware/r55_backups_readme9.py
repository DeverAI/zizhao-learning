# R55 收口 #180：backups/README.md §1 **第九次读数** + §38.18/§38.19 的**第二遍读数** + 一处结构性缺陷就地修 + FreqErr 两条。
# 为什么写在 hardware/ 而不是 hardware/ht305_sync/scripts/：末版 gen 24 之后往归档里落任何一只 = 亲手把末版降级（见 §38.19 ④）。
# 红线：本格每个数都由本脚本现跑现读；写盘顺序 = 读前值 → 修补空行 → 读后值 → 落载体 → 落 README → 落 FreqErr（台账先数后回填）。
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
RDME = os.path.join(REPO, 'backups', 'README.md')
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
DOCS = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
BUILD_BIN = r'C:/esp/zproj/build/zizhao_esp32s3.bin'
SYNC = os.path.join(REPO, 'hardware', 'ht305_sync')
SRC_MACRO = MAIN + '/provision_ap.c'
CARRY = os.path.join(REPO, 'hardware', 'r55_backups_readme9.txt')
AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
assert shutil.which('diff'), 'ABORT: PATH 里没有 diff，五把尺跑不了'


def sh(args):
    p = subprocess.run(args, cwd=REPO, capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def diffrq(root):
    rc, out = sh(('diff', '-rq', os.path.join(REPO, root, 'main'), MAIN))
    assert rc in (0, 1), 'ABORT: diff 非 0/1 退出 = 命令没跑成（rc=%d）' % rc
    return len([l for l in out.split('\n') if l.strip()]), out


def git(*a):
    rc, out = sh(('git',) + a)
    assert rc == 0, 'ABORT: git 失败 ' + ' '.join(a)
    return out


def money(x):
    return '{:,}'.format(int(x))


def md5_of(p):
    assert os.path.isfile(p), 'ABORT: 该读 md5 的文件不存在 ' + p
    b = open(p, 'rb').read()
    return hashlib.md5(b).hexdigest(), len(b)


# ---------------- 五把尺（现跑） ----------------
ns = [l.split('\t') for l in git('-c', 'core.quotePath=false', 'diff', 'HEAD', '--numstat',
                                 '--', 'hardware/zizhao-esp32s3/main').splitlines() if l.strip()]
r1_n, r1_p, r1_m = len(ns), sum(int(x[0]) for x in ns), sum(int(x[1]) for x in ns)
r1_names = sorted(os.path.basename(x[2]) for x in ns)
assert r1_n == 1 and r1_names == ['provision_ap.c'], 'ABORT: main/ 脏集不再是那只每轮被 DROP 的件：%s' % r1_names
r2a = diffrq('backups/r43_20260922_131029')
r2b = diffrq('hardware/zizhao-esp32s3/backups/r43_20260922_131029')
r3a = diffrq('backups/r53_20260924_083929')
r3b = diffrq('hardware/zizhao-esp32s3/backups/r53_20260924_083929')
r5 = diffrq('backups/r44_sourceonly_20260923_084628')
assert r2a[0] == r2b[0] and r3a[0] == r3b[0], 'ABORT: A/B 两根不同值 ⇒ "两根同一时刻"那句要重写'
mfiles = sorted(os.listdir(MAIN))
mbytes = sum(os.path.getsize(os.path.join(MAIN, f)) for f in mfiles if os.path.isfile(os.path.join(MAIN, f)))
assert len(mfiles) == 30, 'ABORT: 工作树 main/ 不再是 30 只（现 %d）' % len(mfiles)
rev = git('rev-list', '--count', 'origin/main..HEAD').strip()
st = [l for l in git('-c', 'core.quotePath=false', 'status', '--porcelain').splitlines() if l.strip()]
bin_md5, bin_bytes = md5_of(BUILD_BIN)
arc_md5, arc_bytes = md5_of(os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin'))
r53_md5, r53_bytes = md5_of(os.path.join(REPO, 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin'))
assert bin_md5.startswith('fb32168a') and arc_md5.startswith('4842a3a0') and r53_md5 == bin_md5
ports = sorted(set(re.findall(r'(?m)^(COM\d+)',
               subprocess.run((sys.executable, '-m', 'serial.tools.list_ports'), cwd=REPO,
                              capture_output=True).stdout.decode('utf-8', 'replace'))))
assert 'COM14' not in ports, 'ABORT: COM14 又出现 ⇒ 本批叙述要重写'
dfiles = sorted(os.listdir(DOCS))
dnote = open(os.path.join(DOCS, 'SNAPSHOT_NOTE.txt'), encoding='utf-8').read()
dsrc = len([l for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
dsnap_at = re.search(r'刷新时刻 (.+?)。', dnote).group(1)
dcred = re.search(r'）：(\d+) 只源全扫，命中数必须为 0 才动手；本次 HITS=(\d+)', dnote)
assert dcred and int(dcred.group(1)) == dsrc and dcred.group(2) == '0', 'ABORT: NOTE 里那句凭据闸读数与表格行数不同代'
pyc_n = sum(1 for r, d, fs in os.walk(os.path.join(REPO, 'backups'))
            for n in d + fs if n == '__pycache__' or n.endswith('.pyc'))

# ---------------- 第二遍读数：§38.18 那 6 只 + §38.19 那两个 README 数 ----------------
IN6 = [('scripts/land_r54_docs.py', 'land_r54_docs.py', 18770, 'dabdf8bc'),
       ('scripts/derive_refresh_docs_r54.py', 'derive_refresh_docs_r54.py', 4757, '84b1fe5b'),
       ('scripts/refresh_docs_snapshot_r54.py', 'refresh_docs_snapshot_r54.py', 7979, '45813ba4'),
       ('scripts/land_backups_r54.py', 'land_backups_r54.py', 7092, '017670d3'),
       ('scripts/land_memory_r54.py', 'land_memory_r54.py', 6617, 'eee2f56d'),
       ('evidence/refresh_docs_r54.txt', 'refresh_docs_r54.txt', 123, '021679ba')]
rer = []
for rel, name, b0, m0 in IN6:
    mm, bb = md5_of(os.path.join(SYNC, rel))
    rer.append((name, bb, mm[:8], bb == b0 and mm.startswith(m0)))
same6 = sum(1 for x in rer if x[3])
rm = os.path.join(SYNC, 'README.md')
rm_m, rm_b = md5_of(rm)
ml = open(os.path.join(SYNC, 'MANIFEST.txt'), encoding='utf-8').read().splitlines()
mt = dict((l.split('\t')[0], l.split('\t')[1]) for l in ml if l.startswith(('TOTAL\t', 'TOTAL_BYTES\t', 'BOM_FILES\t')))
assert int(mt['TOTAL']) == 386 and rm_b == 105343, 'ABORT: 末版清单或 README 与本批登记不同值'

# ---------------- 缺陷：节间空行（现跑计数，不凭记忆） ----------------
doc_raw = open(DOC, encoding='utf-8', newline='').read()
assert doc_raw.count('\n') == doc_raw.count('\r\n') and doc_raw.endswith('\r\n'), 'ABORT: 排查记录行尾不是纯 CRLF'
dl = doc_raw.split('\r\n')
if dl and dl[-1] == '':
    body = dl[:-1]
    trail = 1
else:
    body, trail = dl, 0
bad = [i for i, l in enumerate(body) if l.startswith('#') and i > 0 and body[i - 1].strip()]
heads = sum(1 for l in body if l.startswith('#'))
assert len(bad) == 2, 'ABORT: 缺空行的标题数不是 2（现 %d）⇒ 先查是谁又动了' % len(bad)
doc_b0, doc_m0 = len(doc_raw.encode('utf-8')), hashlib.md5(doc_raw.encode('utf-8')).hexdigest()
doc_l0 = len(body)
sec18_0 = [i + 1 for i, l in enumerate(body) if l.startswith('### 38.18')][0]
sec19_0 = [i + 1 for i, l in enumerate(body) if l.startswith('### 38.19')][0]
sec17_0 = [i + 1 for i, l in enumerate(body) if l.startswith('### 38.17')][0]
assert (sec17_0 - 1) in bad and (sec19_0 - 1) in bad, \
    'ABORT: 缺空行的两只不是 §38.17/§38.19 那两只标题（bad=%s / 17-19 在 %d/%d）' % (bad, sec17_0, sec19_0)
fixed = []
for i, l in enumerate(body):
    if i in bad:
        fixed.append('')
    fixed.append(l)
assert len(fixed) == len(body) + 2
new_doc = '\r\n'.join(fixed) + ('\r\n' if trail else '')
nb = new_doc.encode('utf-8')
assert len(nb) == doc_b0 + 4, 'ABORT: 只该净增 2 只 CRLF'
assert new_doc.count('\n') == new_doc.count('\r\n') == doc_l0 + 2
open(DOC, 'w', encoding='utf-8', newline='').write(new_doc)
doc_t2 = open(DOC, encoding='utf-8', newline='').read()
assert doc_t2 == new_doc
assert sum(1 for i, l in enumerate(doc_t2.split('\r\n')) if l.startswith('#') and i > 0 and doc_t2.split('\r\n')[i - 1].strip()) == 0
doc_b1, doc_m1 = len(nb), hashlib.md5(nb).hexdigest()
sec18_1, sec19_1 = [i + 1 for i, l in enumerate(doc_t2.split('\r\n')) if l.startswith('### 38.18')][0], \
                   [i + 1 for i, l in enumerate(doc_t2.split('\r\n')) if l.startswith('### 38.19')][0]

# ---------------- 独立复核：末版之后归档有没有被自己人污染 ----------------
# ⚠ 这不是 gen 24 那一遍的重跑洗绿：它验的是"末版之后这批 paperwork 有没有往归档里落东西"（判据 = UNLISTED）。
_hwd = os.path.join(REPO, 'hardware')
_before = set(f for f in os.listdir(_hwd) if f.startswith('verify_manifest_') and f.endswith('.txt'))
rc, out = sh((sys.executable, os.path.join(SYNC, 'scripts', 'verify_manifest.py')))
_new = sorted(f for f in os.listdir(_hwd)
              if f.startswith('verify_manifest_') and f.endswith('.txt') and f not in _before)
assert len(_new) == 1, 'ABORT: 复核器这次没自落载体（或落了多只）：%s' % _new
vm_carrier = _new[0]
vm_txt = open(os.path.join(_hwd, vm_carrier), encoding='utf-8').read()
vm_rc = re.search(r'VERIFY_RC=(\d)', vm_txt).group(1)
assert int(vm_rc) == rc == 0, 'ABORT: 末版之后复核不再是 rc=0（现 %s / 进程 %d）⇒ 封界被破了，先查是谁落进归档' % (vm_rc, rc)
vm_ver = re.search(r'VERDICT=(\w+)', out).group(1)
rows = re.search(r'ROWS=(\d+)  MISMATCH=(\d+)  MISSING=(\d+)', out)
unl = re.search(r'UNLISTED\(盘上有、清单没记\)=(\d+)', out)
assert rows and unl and vm_ver == 'MANIFEST_STILL_TRUE', 'ABORT: 复核输出形状或裁决不符：' + out[:200]
print('VERIFY rc=%s %s ROWS=%s MISMATCH=%s MISSING=%s UNLISTED=%s  自落载体=hardware/%s' % (
    vm_rc, vm_ver, rows.group(1), rows.group(2), rows.group(3), unl.group(1), vm_carrier))

# ---------------- 载体先落盘 ----------------
with open(CARRY, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R55 第九次读数 + 第二遍读数 现跑于 ' + AT + '（本文件由 hardware/r55_backups_readme9.py 单次运行写出）\n')
    f.write('RULER1 git diff HEAD --numstat main/ = %d 只 / +%d / -%d  名单=%s\n' % (r1_n, r1_p, r1_m, ','.join(r1_names)))
    f.write('RULER2 diff -rq r43 根A/根B vs main = %d / %d 行\n' % (r2a[0], r2b[0]))
    f.write('RULER3 diff -rq r53 根A/根B vs main = %d / %d 行\n' % (r3a[0], r3b[0]))
    f.write('RULER4 工作树 main/ = %d 只 / %d B\n' % (len(mfiles), mbytes))
    f.write('RULER5 diff -rq r44_sourceonly vs main = %d 行\n' % r5[0])
    f.write('FIELD rev-list=%s  porcelain=%d 行  ports=%s\n' % (rev, len(st), ','.join(ports)))
    f.write('BIN build=%s/%d B  r43归档=%s/%d B  r53归档=%s/%d B\n' % (bin_md5[:8], bin_bytes, arc_md5[:8], arc_bytes, r53_md5[:8], r53_bytes))
    f.write('DOCS files=%d  表格行=%d  SNAPSHOT_AT=%s  凭据闸 OF=%s HITS=%s  pyc/pycache=%d\n' % (
        len(dfiles), dsrc, dsnap_at, dcred.group(1), dcred.group(2), pyc_n))
    for name, bb, mm, ok in rer:
        f.write('REREAD %s bytes=%d md5=%s match=%s\n' % (name, bb, mm, ok))
    f.write('REREAD 汇总 = %d/6 与 §38.18 ② 表格逐字同值\n' % same6)
    f.write('SYNC_README bytes=%d md5=%s  MANIFEST TOTAL=%s/%s B/BOM=%s\n' % (rm_b, rm_m[:8], mt['TOTAL'], mt['TOTAL_BYTES'], mt['BOM_FILES']))
    f.write('DOC_BEFORE bytes=%d md5=%s lines=%d  标题=%d  缺空行=%d  §38.17/18/19 行号=%d/%d/%d\n' % (
        doc_b0, doc_m0[:8], doc_l0, heads, len(bad), sec17_0, sec18_0, sec19_0))
    f.write('DOC_AFTER  bytes=%d md5=%s lines=%d  缺空行=0（复跑量具同一条）  §38.18/19 行号=%d/%d\n' % (
        doc_b1, doc_m1[:8], doc_l0 + 2, sec18_1, sec19_1))
    f.write('VERIFY2 rc=%s %s ROWS=%s MISMATCH=%s MISSING=%s UNLISTED=%s 载体=hardware/%s\n' % (
        vm_rc, vm_ver, rows.group(1), rows.group(2), rows.group(3), unl.group(1), vm_carrier))
    f.write('VERDICT=REREAD_DONE\n')

# ---------------- 本格标题那句"五把尺逐字与第八次同值"由代码判，不由话术判 ----------------
assert (r1_n, r1_p, r1_m) == (1, 210, 14), 'ABORT: 尺① 变了 ⇒ "与第八次同值"不成立，先查是谁动了 main/'
assert (r2a[0], r2b[0], r3a[0], r3b[0], r5[0]) == (5, 5, 0, 0, 3), 'ABORT: 尺②③⑤ 与第八次不同值'
assert (len(mfiles), mbytes) == (30, 641444), 'ABORT: 尺④ 与第八次不同值 ⇒ 有代码进了工作树'
assert same6 == 6, 'ABORT: §38.18 ② 那 6 只复跑不是 6/6 同值'
_done202 = open(os.path.join(REPO, 'done.md'), encoding='utf-8').read()
assert (money(doc_b0) in _done202) and ('第 **' + str(sec19_0) + '** 行') in _done202, \
    'ABORT: done 202 ⑥ 里没有本格⑧说它引用的那两个数 ⇒ "推翻三处"那句不成立'
_ck = open(os.path.join(REPO, 'hardware', 'r55_sec38_19_check.txt'), encoding='utf-8').read()
assert ('bytes=' + str(doc_b0)) in _ck and ('SECTION_LINES=' + str(sec19_0)) in _ck, \
    'ABORT: 复核器载体里没有那两处无前导分隔的同源数 ⇒ "三处"要改口'

# ---------------- backups/README.md §1 第九次读数（纯 LF 追加式插入） ----------------
rd_t = open(RDME, encoding='utf-8', newline='').read()
assert rd_t.count('\r') == 0 and rd_t.count('\n') > 100, 'ABORT: backups/README.md 行尾或体量异常'
assert '第九次读数' not in rd_t, 'ABORT: §1 已经有第九次读数那一格 ⇒ 本脚本不可重跑（会插第二格）'
anchor = '## 2. 命名规则'
assert rd_t.count(anchor) == 1, 'ABORT: §2 锚点不唯一'
BLOCK = (
    '【09-24 **' + AT[11:] + ' 第九次读数**｜**R53→R55 三批零代码进工作树 ⇒ 五把尺逐字与第八次同值 ⇒ 本轮仍不新建备份根**；'
    '本遍另兑现两件事：§38.19"本节没做"② 欠的那次 `diff -rq` 复跑，以及一次"末版之后归档有没有被自己人污染"的独立复核】\n'
    '① **相对 `HEAD`**：`git -c core.quotePath=false diff HEAD --numstat -- hardware/zizhao-esp32s3/main` ⇒ **{r1_n} 只 / +{r1_p} / −{r1_m}**，'
    '名单现读 = **{r1_names}** 那只（自带 1 处明文、每轮被点名 DROP）⇒ 与第八次逐字同值。\n'
    '② **相对 r43 那两根**：`diff -rq` 根 A / 根 B 各现跑 = **{r2a} / {r2b} 行**（第八次同为 5 ⇒ 两根仍是"09-22 20:55 那一烧的历史输入"，不刷新）。\n'
    '③ **相对 r53 那两根**：同一命令 = **{r3a} / {r3b} 行** ⇒ 两根各 0 行输出 = **当前待烧镜像的构建输入仍只有 r53 这一根** ⇒ 本代不需要新根（判据与第八次同源，本遍是它的**第二次独立复跑**）。\n'
    '④ **工作树 `main/` 体量**：**{mfiles} 只 / {mbytes} B**（python 现读，与第六、八次逐字同值 ⇒ "R54/R55 零代码进工作树"就是这一格量的）。\n'
    '⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main hardware/zizhao-esp32s3/main` ⇒ 仍 **{r5} 行 differ**'
    '（第六次那句"本代过期"没有被顺手修好，也不该修——动历史镜像等于造第二把尺）。\n'
    '⑥ **配套读数**：`git rev-list --count origin/main..HEAD` 现跑 = **{rev}**（未 push；`status --porcelain` = {st} 行）；'
    '`md5sum` 三处 = 构建目录 **{bin_md5}**（**md5，32 位 hex** / {bin_bytes} B）= 根 A r53 那只（**归档 == 待烧** 成立）≠ 根 A r43 与板上那只 **{arc_md5}** / {arc_bytes} B'
    '（**待烧 ≠ 板上** 仍在原位）；**docs/ 第九遍**快照 = 目录现读 **{dfiles} 只**、NOTE 表格 **{dsrc} 行**（`SNAPSHOT_AT {dsnap_at}`、NOTE 自述凭据闸 **{dgate}**、`NEW_ONES 1`），'
    '执行件这次在仓库内 = `hardware/refresh_docs_snapshot_r55.py`；python 走一遍 `backups/` 数 `__pycache__` 与 `.pyc` = **{pyc_n}**。\n'
    '⑦ **第二遍读数（§38.18 ② 那 6 只 + §38.19 ⑥ 那个 README 数）**：入库后复跑同一把尺（`md5sum` + 字节数）⇒ **{same6}/6 只逐字同值**'
    '（`land_r54_docs` / `derive_refresh_docs_r54` / `refresh_docs_snapshot_r54` / `land_backups_r54` / `land_memory_r54` / `refresh_docs_r54.txt`），'
    '`hardware/ht305_sync/README.md` = **{rm_b} B / md5 {rm_md5}** 与末版清单那一行同值、`MANIFEST.txt` 汇总仍是 `TOTAL {mt_total} / {mt_bytes} B / BOM {mt_bom}` ⇒ '
    '**§38.18/§38.19 里没有一处读数在本遍复跑中漂**（唯一漂的是下面⑧那两个节号与那只 `.md` 的字节，漂的原因是本遍自己动手修的）。\n'
    '⑧ **本遍我自己抓到并就地修掉的一处结构缺陷**：排查记录 **{heads}** 只标题里有 **2** 只前面缺空行（`### 38.17` 在 §38.16 末只要点之后、`### 38.19` 在 §38.18 ⑥ 之后），'
    '而这两只标题分别是 **R54 / R55 两代自己的落地器**写进去的 ⇒ 形状 = **纯插入式落地器只验"正文没被吞"，不验"节与节之间那只空行"**（同族：项目记忆 (66)-(68)"跨行锚点 Edit 会静默删除原有结构"）。'
    '修法 = 各补 1 只空行，**现跑等式**：{doc_b0} B → **{doc_b1} B（+4 = 两只 CRLF）**、{doc_l0} 行 → **{doc_l0p} 行**、md5 `{doc_m0}` → `{doc_m1}`、'
    '复跑同一把量具 ⇒ 缺空行标题数 **2 → 0**；节号随插行顺移 **§38.18 {sec18_0}→{sec18_1}**、**§38.19 {sec19_0}→{sec19_1}**。\n'
    '⚠ **这次修复推翻了三处别人的登记**（**不就地改数**，只在此点名）：`done.md` 202 ⑥ 与 `hardware/r55_sec38_19_check.txt` 里对排查记录的三处引用'
    '（字节 **{doc_b0}**、行数 **{doc_l0}**、§38.19 节标题行号 **{sec19_0}**）⇒ 本遍之后盘上各多 4 B / 2 行 / 2 个节号；'
    'docs/ 第九遍快照（`{dsnap_at}`）里那只排查记录副本同样停在修复前。三者都在"快照非终态 / 读数取于最后一次编辑之前"的既有口径内，不重跑洗绿。\n'
    '⇒ 判定不变：**不重建、不重烧、不新建根**。本轮真正落地的只有 docs 第九遍、本格（第九次读数）、§38.18/§38.19 第二遍读数与那 2 只空行；**没烧录、没碰串口**'
    '（{hhmmss} 现跑枚举 = `{ports}` ⇒ **COM14 不在**，§38.13 那两行判据样本数仍 **0**、屏亮 **0 次肉眼确认** ⇒ **不播提示音**）；**未 `git push`**；**零删除**。\n'
    '（载体：本格与⑦⑧全部读数 = `hardware/r55_backups_readme9.txt`，同一时刻写出；`hardware/{vm_carrier}` = ⑦ 末版独立复核的自落载体。）\n\n')

REPL = dict(r1_n=r1_n, r1_p=r1_p, r1_m=r1_m, r1_names=r1_names[0], r2a=r2a[0], r2b=r2b[0],
            r3a=r3a[0], r3b=r3b[0], mfiles=len(mfiles), mbytes=money(mbytes), r5=r5[0], rev=rev, st=len(st),
            bin_md5=bin_md5, bin_bytes=money(bin_bytes), arc_md5=arc_md5, arc_bytes=money(arc_bytes),
            dfiles=len(dfiles), dsrc=dsrc, dsnap_at=dsnap_at, dgate=dcred.group(1) + ' 只源全扫 / HITS=' + dcred.group(2),
            pyc_n=pyc_n, same6=same6, rm_b=money(rm_b),
            rm_md5=rm_m, mt_total=mt['TOTAL'], mt_bytes=money(mt['TOTAL_BYTES']), mt_bom=mt['BOM_FILES'],
            heads=heads, doc_b0=money(doc_b0), doc_b1=money(doc_b1), doc_l0=doc_l0, doc_l0p=doc_l0 + 2,
            doc_m0=doc_m0[:8], doc_m1=doc_m1[:8], sec18_0=sec18_0, sec18_1=sec18_1, sec19_0=sec19_0, sec19_1=sec19_1,
            ports=', '.join(ports), hhmmss=AT[11:], vm_carrier=vm_carrier)
BLINES = BLOCK.format(**REPL).split('\n')
secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', open(SRC_MACRO, encoding='utf-8').read()).group(1).encode('utf-8')
for _ln in BLINES:
    assert chr(92) not in _ln, 'ABORT: 正文里有反斜杠：' + _ln[:60]
    assert '{' not in _ln and '}' not in _ln, 'ABORT: 有未求值的占位：' + _ln[:60]
    assert secret not in _ln.encode('utf-8'), 'ABORT: 明文凭据闸命中'
idx = rd_t.index(anchor)
new_rd = rd_t[:idx] + '\n'.join(BLINES) + rd_t[idx:]
open(RDME, 'w', encoding='utf-8', newline='').write(new_rd)
rb = open(RDME, encoding='utf-8', newline='').read()
assert rb.count('\r') == 0
assert rb.startswith(rd_t[:idx]) and rb.endswith(rd_t[idx:]) and rb.count(anchor) == 1
assert rb.count('\n') == rd_t.count('\n') + len(BLINES) - 1, \
    'ABORT: README 行数增量与块行数不符（%d vs %d + %d - 1）' % (rb.count('\n'), rd_t.count('\n'), len(BLINES))
assert '第九次读数' in rb and rb.count('第九次读数') == rd_t.count('第九次读数') + 1
rd_lines = rb.count('\n')

# ---------------- FreqErr.md 两条（先数后回填） ----------------
frq_t = open(FREQ, encoding='utf-8', newline='').read()
assert frq_t.count('\n') == frq_t.count('\r\n') and frq_t.endswith('\r\n')
f_l0 = frq_t.count('\r\n') - 1
f_e0 = sum(1 for l in frq_t.split('\r\n') if l.startswith('[错误类型]'))
ROWS = [
    '[错误类型] **纯插入式落地器只验"正文没被吞"，不验"节与节之间那只空行"**：排查记录 {heads} 只标题里有 2 只前面没有空行，'
    '而这两只正是 R54 与 R55 **自己两代**的落地器写进去的（`### 38.17` 紧跟 §38.16 末只要点、`### 38.19` 紧跟 §38.18 ⑥）⇒ 断言 `startswith(旧全文)` 只保证"前面没被动"，'
    '它**看不见**插入点自身缺的那只分隔符，量具想不到的东西就永远不会红。 → **正确做法**：任何"往 markdown 里插一节"的落地器，写盘后必须**复跑同一把量具**做**否定式**检查'
    '（"标题前面有空行的只数 == 标题总数"），并把修复的**前→后等式**一起登记：{fix_eq} ⇒ 修复本身也推翻了三处旧登记（`done.md` 202 ⑥、`hardware/r55_sec38_19_check.txt`、docs 第九遍副本），'
    '推翻**只点名不就地改数**。同族 = 项目记忆 (66)-(68)（跨行锚点 Edit 静默删除原有结构）/ (64)（记录取证那步自己没落盘）。',
    '[错误类型] **把"末版已复核"当成"之后也不会脏"**：gen 24 末版之后又落了 paperwork 一整套（本批 5 只文档 + docs 第九遍 39 只目录 + 2 只落地器）⇒ 若没人再跑一次 `verify_manifest.py`，'
    '"封界生效"这句话就只是**意图**，不是**读数**。 → **正确做法**：末版之后**任何一批** paperwork 收尾时复跑一次那只复核器，把 `UNLISTED=0` 当成"封界没被自己人破掉"的证据（本遍 rc={vm_rc} / {vm_ver} / UNLISTED={vm_unl}），'
    '并**明确它不是洗绿**：它验的是"此后有没有新增"，不是"重跑把上一次的红洗成绿"（区别写进载体，见 `hardware/r55_backups_readme9.txt` 末两行）。同族 = 项目记忆 (74)（不许拿重跑链把 `MANIFEST_STALE` 洗成绿）。',
]
ROWS = [r.format(heads=heads, fix_eq=money(doc_b0) + ' B → ' + money(doc_b1) + ' B（+4 = 两只 CRLF）/ '
                 + str(doc_l0) + ' → ' + str(doc_l0 + 2) + ' 行 / md5 ' + doc_m0[:8] + '→' + doc_m1[:8],
                 vm_rc=vm.group(1), vm_ver=vm.group(2), vm_unl=unl.group(1)) for r in ROWS]
TAIL = '\r\n'.join(ROWS) + '\r\n'
for _ln in TAIL.split('\r\n'):
    assert chr(92) not in _ln and '{' not in _ln and '}' not in _ln
    assert secret not in _ln.encode('utf-8')
    assert len(_ln) > 40 or _ln == ''
new_frq = frq_t + TAIL
f_l1 = new_frq.count('\r\n') - 1
f_e1 = sum(1 for l in new_frq.split('\r\n') if l.startswith('[错误类型]'))
open(FREQ, 'w', encoding='utf-8', newline='').write(new_frq)
fb = open(FREQ, encoding='utf-8', newline='').read()
assert fb.startswith(frq_t) and fb.count('\r\n') == new_frq.count('\r\n')
assert sum(1 for l in fb.split('\r\n') if l.startswith('[错误类型]')) == f_e1 == f_e0 + 2
assert fb.count('\n') - 1 == f_l1

print('RULER 1=%d只/+%d/-%d %s  2=%d/%d  3=%d/%d  4=%d只/%s B  5=%d' % (
    r1_n, r1_p, r1_m, ','.join(r1_names), r2a[0], r2b[0], r3a[0], r3b[0], len(mfiles), money(mbytes), r5[0]))
print('FIELD rev-list=%s porcelain=%d ports=%s' % (rev, len(st), ','.join(ports)))
print('DOCS 第九遍 = %d 只 / 表格 %d 行 @%s / pyc=%d' % (len(dfiles), dsrc, dsnap_at, pyc_n))
print('REREAD 第二遍 = %d/6 同值  README=%s B %s  MANIFEST TOTAL=%s' % (same6, money(rm_b), rm_m[:8], mt['TOTAL']))
print('DOC 节间空行修复 %d/%d -> %d/%d 行  md5 %s->%s  缺空行 2->0' % (
    doc_b0, doc_l0, doc_b1, doc_l0 + 2, doc_m0[:8], doc_m1[:8]))
print('README_LINES %d -> %d（§1 第九次读数块 %d 行，纯 LF，插入未动 §2 及之后）' % (rd_t.count(chr(10)), rd_lines, len(BLINES)))
print('FREQ 错误类型 %d -> %d 行 %d -> %d（两条，先数后回填）' % (f_e0, f_e1, f_l0, f_l1))
print('CARRY = hardware/r55_backups_readme9.txt (%d B)' % os.path.getsize(CARRY))
print('VERDICT=BACKUPS_README9_DONE')
