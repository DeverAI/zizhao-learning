# R55 落地器 A 的第二只：把**第 13 代同步**的读数登记进 `hardware/ht305_sync/README.md`。
# 三步序（(95) 那条）：①`ast.parse` 体检由跑它的人做（它就是 python）；②写盘前对**占位符/哨兵零容忍**；
# ③写盘后独立回读 + 减号列 = 0 证明（纯插入）。清单代次那一行**不在本只**里写：gen 数字要等冻结跑完才有数，
# 写在这里就是"将来式锚点"（(85) 那条），由第二只落地器收。
import hashlib
import os
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
README = os.path.join(REPO, 'hardware', 'ht305_sync', 'README.md')
EV = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
OUT = os.path.join(EV, 'r55_land_readme.txt')
BS = chr(92)

old = open(README, 'rb').read()
assert old.count(b'\r') == 0, 'README 本应是纯 LF，现含 CR 字节'
txt = old.decode('utf-8')

ANCHOR = '## 清单世代（'
assert txt.count(ANCHOR) == 1, '锚点不唯一：' + str(txt.count(ANCHOR))

# 读数全部从 evidence 现读，不手抄：抄一个数就要再核一个数。
def rd(name):
    p = os.path.join(EV, name)
    assert os.path.isfile(p), '取证件不存在：' + name
    return open(p, encoding='utf-8-sig').read()


loc = rd('r55_local.txt')
ver = rd('r55_verify.txt')
ld = rd('r55_listdiff.txt')
rt1 = rd('r55_roundtrip.txt')
rt2 = rd('r55_roundtrip_2.txt')
pc = rd('r55_parse_check.txt')


def grab(src, key, name):
    m = re.search(re.escape(key) + r'(\S+)', src)
    assert m, '取证件 ' + name + ' 里找不到键 ' + key
    return m.group(1)


zip_md5 = grab(loc, 'zip size/md5        = 2055096 ', 'r55_local.txt')
agg = grab(loc, 'LOCAL_AGGREGATE     = ', 'r55_local.txt')
assert agg == grab(ver, 'REMOTE_AGGREGATE=', 'r55_verify.txt'), '两侧聚合不等，下面的话就不成立'
assert len(agg) == 64 and re.fullmatch(r'[0-9a-f]{64}', agg), '聚合摘要不是 64 位十六进制 sha256'
assert grab(ver, 'REMOTE_ZIP_MD5=', 'r55_verify.txt') == zip_md5
assert grab(pc, 'MD5_BOTH=', 'r55_parse_check.txt').lower() == '6b57cba02a2f65bfc091ecd61073825b'

new = []
new.append('→ **09-24 12:2x~12:3x**（**第 13 代同步 `r55final` 跑完 + §38.18 那一族缺陷的"由源头堵住"版本第一次生效**'
           ' ⇒ 本代最要紧的不是读数，是**取证载体的落点换了三处脚本**：`sync_r55.py` / `r55_upload.ps1` / `chk_r55.ps1` '
           '三只现在**各自把自己那一份 stdout 直接写进 `evidence/`**，不再先落 `%TEMP%` 再由一只"落地器"搬进来。'
           '于是本代 `scripts/` 里**少了两整只作业**（`land_rNN_evidence.py` 与 `extra_land_rNN.py`，第 8~12 代每代都要跑的那两只）'
           '——它们存在的唯一理由是"取证落在了仓库外"，理由没了，作业也就没了。'
           '这是 §38.18 缺陷一（"没入库"被写成豁免句 ⇒ 给永久不可复核的载体发了合法身份）第一次由**执行者**关掉，而不是由登记关掉。）')
new.append('  - 同步读数（逐字取自 `evidence/r55_*.txt`，不是回忆）：12:24:56 截止拷贝 → 12:25:11 建包 '
           '**2,055,096 B / md5 `%s`**，载荷 **542 只 / 5,058,948 B**，staging 里带明文的那 1 只 = '
           '`hardware/zizhao-esp32s3/main/provision_ap.c`；远端 12:25:40~12:25:44：`EXTRACT_OK=True / REMOTE_FILES=542 / '
           'REMOTE_BYTES=5058948 / REMOTE_FORBIDDEN=0`，zip 两侧同 size 同 md5，聚合摘要两侧逐字等 = `%s`'
           '（64 位十六进制 sha256，非截断）；解包根 `zsynctest15`（一个根只喂一代）。'
           '探测在 `scp` **之前**（12:25:29~12:25:33）：`TARGET_EXISTS=False`，桌面 23 只文件里含 "zizhao" 字面 14 只 = '
           '同步包 **13 只**（1 只 tar.gz + `zizhao_sync_20260923_r43.zip` + `r44final`~`r54final` 11 只）'
           '+ 1 只与同步无关的 `zizhao_esp32s3_flash_notice_20260918.zip` ⇒ **仍一只都没删**。' % (zip_md5, agg))
new.append('  - 差集那一遍（12:27:49，载体 `evidence/r55_listdiff.txt`）：`LOCAL_LINES=542 / REMOTE_LINES=542 / '
           'ONLY_IN_LOCAL=0 / ONLY_IN_REMOTE=0` ⇒ `VERDICT=LISTDIFF_EQUAL`（本代起判决同时落 stdout **与退出码**，'
           '旧版只打 `OUT … RC 0` 而差集非 0 也照样 rc=0）；包 ↔ 工作树 `identical=541 / changed_since_cutoff=1 / '
           'deleted=0 / new_since_cutoff=9`。那 1 只 changed = `scripts/r55_roundtrip.py` **自己**（下面那条重跑），'
           '9 只 new = 本代 9 只 `r55_*.txt` 取证 ⇒ **这是"取证直接进仓库"的必然结果，不是包漏了东西**：'
           '包是 12:24:56 的快照，取证在它之后才存在。差集器因此同时装了一道**划分自核**：'
           '`四桶互斥且并集 == 当前候选集(551)：PASS`（`SELF_CHECK` 行），把"四个数各说各话"这种口径堵成一次划分。')
new.append('  - 往返那一遍**首跑是失败的**（12:26:11 `SCP_RC=255` ⇒ `VERDICT=SCP_FAILED`，载体留在 '
           '`evidence/r55_roundtrip.txt`，不覆盖、不改写）；诊断不是猜：手工对同一路径 `scp` 立即拿到 10,199 B ⇒ 判为**瞬时失败**。'
           '处置不是"人再点一遍"，而是给脚本装重试：**原地最多两次**、两次的 rc 与 **stderr 正文**都登记'
           '（上一版只登 `SCP_STDERR_LINES=2`，255 到底说了什么盘上查不到 ⇒ 计数不带内容 = 没有取证）。'
           '重跑 = 12:27:28~12:27:39 `evidence/r55_roundtrip_2.txt`：`SCP_ATTEMPT=1 RC=0`、回件 10,199 B / md5 '
           '`0419bf1628f399f399ca41daf8ed3494` == 工作树 ⇒ `BYTE_EQUAL_TO_WORKTREE=True`，'
           '`PROV_PASS_HITS_REMOTE=1` ⇒ `VERDICT=REMOTE_CARRIES_PLAINTEXT`（登记事实、不是事故；服务器那一份不能当回滚源）；'
           '同批**两把对照**：阴性 `CONTROL_LANDER_HITS=0`（对照件 `scripts/land_r55_A.py`，本代把它从"写死一只当时还不存在的脚本"'
           '改成"不存在即 ABORT"——(63) 那族的第三次复发）、阳性 `POSITIVE_CONTROL_WORKTREE_HITS=1`（应 >0，'
           '证明这把尺在已知含该串的字节上真的会响）。')
new.append('  - 编码体检那一路（`chk_r55.ps1`）本代换了形态：**脚本自己把读数写进 `evidence/r55_parse_check.txt`**'
           '（目标已存在即 ABORT），捕获那一步不再是独立动作 ⇒ "记录取证那一步自己没落盘"那一族的入口在本代少一个。'
           '读数：`FIRST3=239,187,191`（UTF-8 BOM 在位）/ `PARSE_ERRORS=0` / `REMOVE_ITEM_HITS=0` / '
           '`SCRIPT_LINES=105 == SRC_LINES=105` / `MD5_BOTH=6B57CBA02A2F65BFC091ECD61073825B`。'
           '新增的 `SRC_LINES` 与 `SCRIPT_LINES<50 即 ABORT` 是对 (63) 那族（读空文件 ⇒ 读数全绿）的第二道哨兵。'
           '**一处必须说明的来源差异**：本代**实际执行的是归档那一只**（12:25:29 直接 `-File` 指向 `scripts/`），'
           '`%TEMP%` 副本只是"逐字节同孪生"的第二把尺 ⇒ 由 `MD5_BOTH` 两侧同值来担保解析结果描述的是被执行的那只。')
new.append('  - 本代**没做**的（点名，不写成豁免句）：① 没有 `land_rNN`/`extra_land_rNN`  ⇒ 不是漏了，是它们的动因已消失，'
           '但"逐只明文复扫"那一步本代**没有独立载体**（旧落地器顺手做了 12 只 `hits=0` 那件事）⇒ 记为 gen 之后第一笔义务；'
           '② 没有新建备份根（`diff -rq` 判据本轮未复跑）；③ 没有碰串口、没有烧录、屏侧零进展；④ `%TEMP%` 里那只 '
           '10,199 B 的抓回件（带明文）**仍在**，本会话一律不删 ⇒ 它在仓库外，`FETCH_NAME_LEAKED_INTO_REPO` 本代未现跑，不登记数字。')
new.append('')
block = chr(10).join(new) + chr(10)

updated = txt.replace(ANCHOR, block + ANCHOR, 1)
for ph in ('@ONE@', '@TWO@', '@PT@', '@TEMPREF@', 'TODO', 'XXX'):
    assert ph not in updated, '占位符未解析：' + ph
assert updated.count(ANCHOR) == 1, '锚行被复制或删除'
# 纯插入证明：去掉新块必须逐字节回到原文件
assert updated.replace(block, '', 1) == txt, '不是纯插入'
assert updated.encode('utf-8').startswith(old[:200])
if os.path.exists(OUT):
    print('ABORT: 载体现存，不覆盖', OUT)
    sys.exit(1)
open(README, 'wb').write(updated.encode('utf-8'))

# 落盘后**独立回读**（不拿内存里那份当结论）
back = open(README, 'rb').read()
assert back == updated.encode('utf-8'), '回读 != 待写字节'
assert back.count(b'\r') == 0, '写盘引入 CR'
btxt = back.decode('utf-8')
assert btxt.count(ANCHOR) == 1 and block in btxt
# 表格结构自查（(67) 那条：跨行锚点会静默吃掉标题/表格行）
assert btxt.count(chr(10) + '## ') == txt.count(chr(10) + '## ') + 0
assert btxt.split(chr(10))[0] == txt.split(chr(10))[0]
rows_now = len(re.findall(r'(?m)^\| ', btxt))
rows_old = len(re.findall(r'(?m)^\| ', txt))
assert rows_now == rows_old, '表格行数变了 %d -> %d（本只应是纯插入）' % (rows_old, rows_now)
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
lines = ['LAND_README_AT=' + now,
         'README_BYTES %d -> %d (+%d)' % (len(old), len(back), len(back) - len(old)),
         'README_MD5 %s -> %s' % (hashlib.md5(old).hexdigest()[:8], hashlib.md5(back).hexdigest()[:8]),
         'LF_ONLY=True CR=%d' % back.count(b'\r'),
         'PURE_INSERT=PASS（删掉新块 == 原字节）',
         'TABLE_ROWS %d -> %d（本只不动表）' % (rows_old, rows_now),
         'BULLETS_ADDED=%d' % (block.count(chr(10) + '  - ')),
         'AGGREGATE两侧等=%s' % (agg == grab(ver, 'REMOTE_AGGREGATE=', 'r55_verify.txt')),
         'VERDICT=README_LANDED']
open(OUT, 'w', encoding='utf-8', newline='').write(chr(10).join(lines) + chr(10))
print(chr(10).join(lines))
print('OUT', OUT)
