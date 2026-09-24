# 第 11 代同步凭证落地：把 %TEMP% 里那批 r53_*.txt 复制进仓库 evidence/，**目标已存在即拒写**、**含明文即拒收**。
# 口令只从 main/provision_ap.c 的宏本体现读，绝不打印、绝不内嵌字面量。
# 本代跑的是 R49 复查给 `land_r49_evidence.py` 补的那两条守卫（聚合行缺失即 ABORT + 摘要必须是 64 位十六进制 + 落地记录自己落盘）：
# 它们的**首个真载体是第 8 代**（README 代次表 gen 12 那格②），本代只是延续 ⇒ 不自称"第一次真的执行"（派生会把上一代的自述句一起派过来）。
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

NAMES = ['r53_local.txt', 'r53_probe.txt', 'r53_scp_err.txt', 'r53_verify.txt',
         'r53_run_log.txt', 'r53_local_names.txt', 'r53_remote_names.txt',
         'r53_listdiff.txt', 'r53_cutoff_delta.txt', 'r53_parse_check.txt']

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
                open(os.path.join(REPO, 'hardware/zizhao-esp32s3/main/provision_ap.c'),
                     encoding='utf-8').read()).group(1).encode()

missing = [n for n in NAMES if not os.path.isfile(os.path.join(TMP, n))]
if missing:
    print('ABORT: 源凭证不存在', missing)
    sys.exit(1)

t0 = datetime.now()
rows = []
for n in NAMES:
    s, d = os.path.join(TMP, n), os.path.join(DST, n)
    if os.path.exists(d):
        print('ABORT: 目标已存在，不覆盖', n)
        sys.exit(1)
    b = open(s, 'rb').read()
    if sec in b:
        print('ABORT: 凭证里含明文口令，拒收', n)
        sys.exit(1)
    shutil.copy2(s, d)
    assert open(d, 'rb').read() == b, 'copy byte mismatch: ' + n
    rows.append('%s\t%d\tmd5:%s' % (n, len(b), hashlib.md5(b).hexdigest()[:8]))

src_agg = [l for l in open(os.path.join(TMP, 'r53_local.txt'), encoding='utf-8').read().splitlines()
           if l.startswith('LOCAL_AGGREGATE')]
ra = [l for l in open(os.path.join(DST, 'r53_verify.txt'), encoding='utf-8').read().splitlines()
      if l.startswith('REMOTE_AGGREGATE')]
if not src_agg or not ra:
    print('ABORT: 聚合行缺失 LOCAL=%d REMOTE=%d，"相等"无从判起' % (len(src_agg), len(ra)))
    sys.exit(1)
lv, rv = src_agg[0].split('=', 1)[1].strip(), ra[0].split('=', 1)[1].strip()
for tag, v in (('LOCAL', lv), ('REMOTE', rv)):
    if len(v) != 64 or any(c not in '0123456789abcdef' for c in v.lower()):
        print('ABORT: %s_AGGREGATE 不是一只 sha256 摘要（%r）⇒ 拒给 AGGREGATE_MATCH' % (tag, v[:12]))
        sys.exit(1)
print(src_agg[0].strip())
print(ra[0].strip())
print('AGGREGATE_MATCH=%s' % ('YES' if lv == rv else 'NO'))

# 落地时刻与汇总自己写一只文件（R49 那一代 LANDED_AT 只在 stdout ⇒ 文档里那一格时刻无载体）
land_log = os.path.join(DST, 'r53_land_log.txt')
if os.path.exists(land_log):
    print('ABORT: 落地记录已存在，不覆盖', land_log)
    sys.exit(1)
with open(land_log, 'w', encoding='utf-8', newline='\n') as f:
    f.write('LANDED_AT=%s\n' % t0.strftime('%Y-%m-%d %H:%M:%S'))
    f.write('FILES=%d BYTES=%d\n' % (len(rows), sum(int(r.split('\t')[1]) for r in rows)))
    for r in rows:
        f.write(r + '\n')
    f.write(src_agg[0].strip() + '\n' + ra[0].strip() + '\n')
    f.write('AGGREGATE_MATCH=%s\n' % ('YES' if lv == rv else 'NO'))
print('LAND_LOG', land_log, os.path.getsize(land_log))
