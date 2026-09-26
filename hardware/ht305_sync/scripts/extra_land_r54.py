# 第 12 代同步的**尾件落地器**：把 %TEMP% 的 `r54_roundtrip.txt` 复制进 evidence/，并当场做三件普查：
#  ⑴ 仓库里每一只 `evidence/r54_*.txt` 的明文凭据计数（口令从宏本体现读，只打计数、绝不打内容）；
#  ⑵ 远端抓回件在仓库里的**逐字节孪生**普查（**按目录段判**，不再凭"应当只有一只"这种凭空前提写断言 ——
#      第 9 代那一版就是栽在这里：首跑 rc=1，因为它假设"仓库里逐字节相同的只有一只"，实测 28 只；
#      载体 = evidence/r51_extra_land_try1_wrong_twin_premise.txt + ..._try1_script.txt）；
#  ⑶ 抓回件的**文件名**有没有漏进仓库（原件必须留在 %TEMP%，不进仓库）。
# 本脚本本体**入档**（第 9 代那一次只留了输出、脚本在 %TEMP% ⇒ "尾件落地器"这一族工具当时没有可复跑的字节）。
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TMP = os.environ.get('TEMP', 'C:/Users/david/AppData/Local/Temp')
DST = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
REL_SRC = 'hardware/zizhao-esp32s3/main/provision_ap.c'
RT_TMP = os.path.join(TMP, 'r54_roundtrip.txt')
FETCH = os.path.join(TMP, 'r54_remote_provision_ap.c')
OUT = os.path.join(DST, 'r54_extra_land.txt')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
                open(os.path.join(REPO, REL_SRC), encoding='utf-8').read()).group(1).encode()

for p, tag in ((RT_TMP, '尾件读数'), (FETCH, '远端抓回件')):
    if not os.path.isfile(p):
        print('ABORT: %s 不存在 %s' % (tag, p))
        sys.exit(1)
if os.path.exists(OUT):
    print('ABORT: 尾件落地记录已存在，不覆盖', OUT)
    sys.exit(1)

rb = open(FETCH, 'rb').read()
wb = open(os.path.join(REPO, REL_SRC.replace('/', os.sep)), 'rb').read()
if rb != wb:
    print('ABORT: 抓回件与工作树源头不再逐字节等，本轮"BYTE_EQUAL_TO_WORKTREE"这句已不成立')
    sys.exit(1)

# ⑵ 孪生普查：走全仓库（排除 .git），按 sha256 等值收集，再按路径里有没有 `backups` 段分两类
target = hashlib.sha256(rb).hexdigest()
twins, outside = [], []
for r, dirs, fs in os.walk(REPO):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in fs:
        p = os.path.join(r, f)
        try:
            if os.path.getsize(p) != len(rb):
                continue
            if hashlib.sha256(open(p, 'rb').read()).hexdigest() != target:
                continue
        except OSError:
            continue
        rel = os.path.relpath(p, REPO).replace(os.sep, '/')
        twins.append(rel)
        if 'backups/' not in rel:
            outside.append(rel)
if outside != [REL_SRC]:
    print('ABORT: 仓库里 backups/ 之外还有别的孪生件，来源不再唯一 %s' % outside)
    sys.exit(1)

# ⑶ 抓回件文件名有没有漏进仓库
leak = []
for r, dirs, fs in os.walk(REPO):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in fs:
        if 'r54_remote_provision_ap' in f:
            leak.append(os.path.relpath(os.path.join(r, f), REPO).replace(os.sep, '/'))

# ⑴ 落地尾件 + 逐只复扫本代 evidence
dst_rt = os.path.join(DST, 'r54_roundtrip.txt')
if os.path.exists(dst_rt):
    if open(dst_rt, 'rb').read() != open(RT_TMP, 'rb').read():
        print('ABORT: 尾件已存在且字节不等，不覆盖', dst_rt)
        sys.exit(1)
    print('SKIP_IDENTICAL', 'r54_roundtrip.txt')
    n_rt, b_rt = os.path.getsize(dst_rt), hashlib.md5(open(dst_rt, 'rb').read()).hexdigest()[:8]
else:
    shutil.copy2(RT_TMP, dst_rt)
    bb = open(dst_rt, 'rb').read()
    assert bb == open(RT_TMP, 'rb').read(), 'copy byte mismatch: r54_roundtrip.txt'
    n_rt, b_rt = len(bb), hashlib.md5(bb).hexdigest()[:8]

rows, bad = [], []
for f in sorted(os.listdir(DST)):
    if not (f.startswith('r54_') and f.endswith('.txt')) or f == 'r54_extra_land.txt':
        continue
    b = open(os.path.join(DST, f), 'rb').read()
    h = b.count(sec)
    if h:
        bad.append((f, h))
    rows.append('%s\t%d\thits=%d\tmd5:%s' % (f, len(b), h, hashlib.md5(b).hexdigest()[:8]))
if bad:
    print('ABORT: 本代凭证里有明文命中', bad)
    sys.exit(1)

t0 = datetime.now()
lines = ['CHECKED_AT=%s' % t0.strftime('%Y-%m-%d %H:%M:%S'),
         'FILES=1 BYTES=%d' % n_rt,
         'r54_roundtrip.txt\t%d\tmd5:%s' % (n_rt, b_rt),
         'NOTE=r54_land_log.txt is the 10+1 batch carrier; this file is the tail artifact landed after that batch',
         'FETCH=r54_remote_provision_ap.c bytes=%d md5=%s (留在 %%TEMP%%，未进仓库)' % (len(rb), hashlib.md5(rb).hexdigest()),
         'BYTE_EQUAL_TO_WORKTREE=True (本脚本当场重算，非抄尾件)',
         'BYTE_TWINS_IN_REPO=%d SOURCE=%s BACKUP_COPIES=%d OUTSIDE_BACKUPS=%d' % (len(twins), REL_SRC, len(twins) - 1, len(outside)),
         'FETCH_NAME_LEAKED_INTO_REPO=%d' % len(leak),
         'EXTRA_LAND_SCRIPT=scripts/extra_land_r54.py (本体入档)'] + rows
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('OUT', OUT, os.path.getsize(OUT))
