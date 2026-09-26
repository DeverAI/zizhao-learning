# R55 的"逐只明文复扫"载体。动因：本代把取证改成**脚本自己写进 evidence/** ⇒ 旧落地器（`land_rNN_evidence.py`
# / `extra_land_rNN.py`）顺带做的那两件事失去了执行者：①本代每只载体逐只数口令命中、②`%TEMP%` 抓回件的**文件名**
# 有没有被写进仓库（名字本身不含口令，但名字进仓库 = 有人以为它在仓库里，会去找一只不存在的东西）。
# README 的"本代没做"① 点的就是这两件 —— 本脚本是它的**执行者**，写出来就不该再留成义务。
# 红线：口令只从宏本体现读、只数不打印；抓回件本体绝不进仓库、也绝不读进 stdout。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
EV = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
FETCH_NAME = 'r55_remote_provision_ap.c'
# 载体名轮换：首跑（口径写错的那一遍）**留在盘上**，重跑另起一只并点名前一只。
_cands = ['r55_cred_recount.txt'] + ['r55_cred_recount_%d.txt' % i for i in range(2, 10)]
_prior = None
for _c in _cands:
    if not os.path.exists(os.path.join(EV, _c)):
        OUT = os.path.join(EV, _c)
        break
    _prior = _c
else:
    raise SystemExit('ABORT: 载体名 9 只全被占')

SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
TMP = os.environ.get('TEMP', 'C:/Users/david/AppData/Local/Temp')

sec = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read()).group(1)
assert sec, 'ABORT: 读不到 PROV_PASS 宏值，这道门自证不了扫的是真口令'
# 阳性对照的**内存样本**（(84) 那条：不为造脏样本落盘）：口令 + 一句定长说明，拼成字节当场数。
# 中文只能走 `.encode('utf-8')` —— `b'…中文…'` 是 `SyntaxError: bytes can only contain ASCII literal characters`，
# 这一条在 FreqErr 台账里已有登记，本代**第二次**踩在同一行形状上（写的时候没查台账）。
POS_SAMPLE = '// 阳性对照样本，只在内存里存在：'.encode('utf-8') + sec + b'\n'
assert POS_SAMPLE.count(sec) == 1, 'ABORT: 阳性对照样本自证失败'

rows = []
total_hits = 0
cands = sorted(f for f in os.listdir(EV) if re.fullmatch(r'r55_[A-Za-z0-9_]+\.txt', f))
if not cands:
    print('ABORT: 候选为 0 只，"命中 0"不等于"干净"（(55)/(71) 那条）')
    sys.exit(1)
for f in cands:
    b = open(os.path.join(EV, f), 'rb').read()
    n = b.count(sec)
    total_hits += n
    rows.append('%s\t%d\tmd5:%s\thits=%d' % (f, len(b), hashlib.md5(b).hexdigest()[:8], n))

# 载体**之外**还有一处必须扫：本代新写进 scripts/ 的脚本（它们会随下一代包上服务器）。
srows = []
scands = sorted(f for f in os.listdir(os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts'))
                if f.startswith(('r55_', 'sync_r55', 'land_r55_readme')))
for f in scands:
    b = open(os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts', f), 'rb').read()
    n = b.count(sec)
    total_hits += n
    srows.append('%s\t%d\tmd5:%s\thits=%d' % (f, len(b), hashlib.md5(b).hexdigest()[:8], n))

# 抓回件名是否泄漏进仓库（工作树里跟踪 + 未跟踪全部名，按字节搜文件名本身）。
r = subprocess.run(['git', '-c', 'core.quotePath=false', 'ls-files', '-c', '--others', '--exclude-standard'],
                   cwd=REPO, capture_output=True, text=True, encoding='utf-8')
names = r.stdout.split()
assert len(names) > 400, 'ABORT: 名册只有 %d 只，这把尺显然没覆盖全树' % len(names)
nb = FETCH_NAME.encode('utf-8')
inside, outside = [], []
for rel in names:
    if rel.startswith('.workbuddy/'):
        continue
    p = os.path.join(REPO, rel.replace('/', os.sep))
    if not os.path.isfile(p):
        continue
    if nb in open(p, 'rb').read():
        # **不静默排除任何一只**（第一版排除"声明该名的脚本自己"，那等于又造一把看不见的尺）。
        # 改成按**半径**分桶：`hardware/ht305_sync/` 之内含此名是按构造合法（声明它的脚本、打印它的取证载体，
        # 含本脚本首跑那只口径写错的载体），要判的是**仓库其余部分**有没有把它当成一件仓库里的东西写进文档。
        (inside if rel.startswith('hardware/ht305_sync/') else outside).append(rel)

lines = ['CRED_RECOUNT_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
if _prior:
    lines += ['PRIOR_ATTEMPT=evidence/%s（那一遍口径写错：把"声明该名的脚本自己"静默排除，'
              '等于造一把看不见的尺；首跑读数留在盘上不覆盖）' % _prior,
              'PRIOR_VERDICT=DIRTY（FETCH_NAME_LEAKED_INTO_REPO=1，那 1 只就在同步目录内）']
lines += ['SCOPE=evidence/r55_*.txt %d 只 + scripts/ 本代新写 %d 只 = %d 只，逐只点名（不截断）'
         % (len(cands), len(scands), len(cands) + len(scands)),
         '--- evidence/ ---'] + rows + ['--- scripts/ ---'] + srows + [
         'TOTAL_HITS=%d' % total_hits,
         'POSITIVE_CONTROL_IN_MEMORY_HITS=%d（应 1：证明这把尺真的含该串就会响，样本不落盘）'
         % POS_SAMPLE.count(sec),
         'FETCH=%s 在 %%TEMP%% 字节数=%s（只数不读）' % (FETCH_NAME,
                                                   os.path.getsize(os.path.join(TMP, FETCH_NAME))),
         'FETCH_NAME_IN_REPO_INSIDE_SYNC_SCOPE=%d（按构造合法：声明它的脚本 + 打印它的取证载体）' % len(inside),
         'FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=%d %s' % (len(outside), outside),
         'NAMES_SCANNED=%d（git ls-files -c --others --exclude-standard，排除 .workbuddy/）' % len(names),
         'VERDICT=' + ('CLEAN' if total_hits == 0 and not outside else 'DIRTY')]
txt = chr(10).join(lines) + chr(10)
open(OUT, 'w', encoding='utf-8', newline='').write(txt)
print(txt)
sys.exit(0 if total_hits == 0 and not outside else 1)
