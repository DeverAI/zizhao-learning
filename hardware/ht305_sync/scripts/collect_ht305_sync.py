"""把 ht305 三轮同步的脚本与取证件从 %TEMP% 收进仓库 hardware/ht305_sync/。
前置：本脚本只在两道明文门（PROV_PASS + ht305 SSH 口令）均 0 命中之后运行；
命中即 ABORT，不复制任何文件。二进制复制（copy2）保留 BOM/字节，不重排内容。"""
import glob, hashlib, os, shutil, sys, datetime

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DST = os.path.join(REPO, 'hardware', 'ht305_sync')
TMP = os.environ['TEMP']
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')

import re
m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏本体'); sys.exit(1)
secret = m.group(1)

PATTERNS = ['r43_*.txt', 'ht305_*.ps1', 'build_sync.py', 'build_zip.py', 'expected*.py', 'pw_*.py',
            'sync_r4*.py', 'r44_*.ps1', 'r44_*.txt', 'r45_*.ps1', 'r45_*.txt', 'r45_*.py',
            'chk_r45.ps1', 'probe_zip_vs_head*.py', 'cred_recount_0822.txt',
            'land_r44b_report.py', 'ht305_sync_gate.py', 'ht305_sync_gate_ssh.ps1']
files = sorted({p for pat in PATTERNS for p in glob.glob(os.path.join(TMP, pat))})
dirty = [(os.path.basename(p), open(p, 'rb').read().count(secret)) for p in files]
dirty = [d for d in dirty if d[1]]
if dirty:
    print('ABORT: 明文门命中', dirty); sys.exit(1)
if os.path.exists(DST):
    print('ABORT: 目标已存在', DST); sys.exit(1)

for sub in ('scripts', 'evidence', 'gate'):
    os.makedirs(os.path.join(DST, sub), exist_ok=True)
GATE = {'ht305_sync_gate.py', 'ht305_sync_gate_ssh.ps1'}
SCRIPT_EXT = ('.ps1', '.py')

rows = []
for p in files:
    name = os.path.basename(p)
    bucket = 'gate' if name in GATE else ('scripts' if name.endswith(SCRIPT_EXT) else 'evidence')
    data = open(p, 'rb').read()
    d = os.path.join(DST, bucket)
    if os.path.exists(os.path.join(d, name)):
        print('ABORT: 目标重名', name); sys.exit(1)
    shutil.copy2(p, os.path.join(d, name))
    bom = data[:3] == b'\xef\xbb\xbf'
    rows.append((bucket, name, len(data), hashlib.md5(data).hexdigest(), bom))

now = datetime.datetime.now().strftime('%m-%d %H:%M:%S')
man = os.path.join(DST, 'MANIFEST.txt')
with open(man, 'w', encoding='utf-8', newline='') as f:
    f.write('ht305_sync 归档清单（由 %TEMP%\\collect_ht305_sync.py 生成于 09-23 ' + now + '）\n')
    f.write('来源目录 = %TEMP%；复制方式 = shutil.copy2（逐字节，保留 BOM）；'
            '明文门 = 双门 0 命中（PROV_PASS 宏值 + ht305 SSH 口令），门脚本见 gate/\n')
    f.write('bucket\tfile\tbytes\tmd5\tutf8_bom\n')
    for r in sorted(rows):
        f.write('\t'.join(str(x) for x in r) + '\n')
    f.write('TOTAL\t' + str(len(rows)) + '\n')
print('COPIED', len(rows), '->', DST, now)
for r in sorted(rows):
    print(r[0], r[1], r[2], 'BOM' if r[4] else 'noBOM')
