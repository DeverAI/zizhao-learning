"""明文门：在把 %TEMP% 取证件收进 hardware/ht305_sync/ 之前，逐只扫 PROV_PASS 宏值。
只打印 文件名 + 命中次数，绝不打印口令本身。"""
import os, re, sys

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')

m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏本体')
    sys.exit(1)
secret = m.group(1)
print('SECRET_LEN', len(secret))

tmp = os.environ['TEMP']
cands = []
for pat in ('ht305_*.ps1', 'build_sync.py', 'build_zip.py', 'expected*.py', 'pw_*.py',
            'sync_r4*.py', 'r44_*.ps1', 'r44_*.txt', 'r45_*.ps1', 'r45_*.txt', 'r45_*.py',
            'chk_r45.ps1', 'probe_zip_vs_head*.py', 'cred_recount_0822.txt', 'land_r44b_report.py'):
    cands += [os.path.join(tmp, f) for f in __import__('glob').glob(os.path.join(tmp, pat))]

cands = sorted(set(cands))
bad = []
for p in cands:
    b = open(p, 'rb').read()
    hits = b.count(secret)
    if hits:
        bad.append((os.path.basename(p), hits))
    print(('HIT ' if hits else 'CLEAN '), os.path.basename(p), len(b))
print('---')
print('CANDIDATES', len(cands), 'DIRTY', len(bad), bad)
