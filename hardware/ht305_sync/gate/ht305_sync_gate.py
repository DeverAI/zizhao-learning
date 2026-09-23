"""明文门：在把 %TEMP% 取证件收进 hardware/ht305_sync/ 之前，逐只扫 PROV_PASS 宏值。
只打印 文件名 + 命中次数，绝不打印口令本身。"""
import glob, os, re, sys

# 12:42:50 实测：本门那句含 `⇒` 的 ABORT 文案在 GBK 控制台下自己崩了（rc 仍 1，但"设计好的 ABORT"变成"未设计的 traceback"）。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')

m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏本体')
    sys.exit(1)
secret = m.group(1)
print('SECRET_LEN', len(secret))

tmp = os.environ['TEMP']
# 09-23 12:3x 结构修订（落地 R45 复查里我自己复跑发现的一条）：PATTERNS 原先**按代枚举**
# （`r44_*.ps1` / `r45_*.ps1` / `chk_r45.ps1`…），于是第 4 代（`r46_*`）**一只都不在名单里**
# ⇒ README 那句"门可原地重跑"对 gen4 是假的：它扫 0 只也照样打 `DIRTY 0`，与"扫过且干净"逐字同形。
# 两处改掉：① 换成**跨代通配**；② 加一条硬守卫——**候选为 0 就 ABORT**（空扫不是"干净"）。
PATTERNS = ('ht305_*.ps1', 'build_sync.py', 'build_zip.py', 'expected*.py', 'pw_*.py',
            'sync_r4*.py', 'r4*_*.ps1', 'r4*_*.txt', 'r4*_*.py', 'chk_r4*.ps1',
            'probe_zip_vs_head*.py', 'cred_recount_*.txt', 'land_r4*.py',
            'ht305_sync_gate.py', 'ht305_sync_gate_ssh.ps1', 'collect_ht305_sync.py',
            'gen_manifest.py', 'verify_manifest.py', 'ps1_bom_scan.py',
            'cred_gate_recheck*.py', 'run_cred_gate_recheck.ps1',
            'staged_cred_gate.py', 'cred_gate_selftest.py')
cands = []
hit_per_pat = {}
for pat in PATTERNS:
    g = glob.glob(os.path.join(tmp, pat))
    hit_per_pat[pat] = len(g)
    cands += g

cands = sorted(set(cands))
if not cands:
    print('ABORT: 候选为 0 ⇒ 这道门一只都没扫，不能当成"干净"')
    sys.exit(1)
bad = []
for p in cands:
    b = open(p, 'rb').read()
    hits = b.count(secret)
    if hits:
        bad.append((os.path.basename(p), hits))
    print(('HIT ' if hits else 'CLEAN '), os.path.basename(p), len(b))
print('---')
print('CANDIDATES', len(cands), 'DIRTY', len(bad), bad)
# 每一族通配各匹配到几只：**0 命中要看得见**，否则"这一代没收进来"和"这一代没有文件"长得一样。
print('PER_PATTERN', ' '.join('%s=%d' % (k, v) for k, v in sorted(hit_per_pat.items()) if v))
print('DEAD_PATTERNS', [k for k, v in sorted(hit_per_pat.items()) if v == 0])
