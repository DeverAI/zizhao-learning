# 第 7 代同步凭证落地：把 %TEMP% 里那批 r49_*.txt 复制进仓库 evidence/，**目标已存在即拒写**、**含明文即拒收**。
# 口令只从 main/provision_ap.c 的宏本体现读，绝不打印、绝不内嵌字面量。
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

NAMES = ['r49_local.txt', 'r49_probe.txt', 'r49_scp_err.txt', 'r49_verify.txt',
         'r49_run_log.txt', 'r49_local_names.txt', 'r49_remote_names.txt',
         'r49_listdiff.txt', 'r49_cutoff_delta.txt']

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

# 派生器/工具那两只本来就直接写在仓库里，这里只做点名登记
print('LANDED_AT', t0.strftime('%Y-%m-%d %H:%M:%S'))
print('FILES', len(rows), 'BYTES', sum(int(r.split('\t')[1]) for r in rows))
for r in rows:
    print(' ', r)
src_agg = [l for l in open(os.path.join(TMP, 'r49_local.txt'), encoding='utf-8').read().splitlines()
           if l.startswith('LOCAL_AGGREGATE')]
dst_verify = open(os.path.join(DST, 'r49_verify.txt'), encoding='utf-8').read()
ra = [l for l in dst_verify.splitlines() if l.startswith('REMOTE_AGGREGATE')]
if not src_agg or not ra:
    print('ABORT: 聚合行缺失 LOCAL=%d REMOTE=%d，"相等"无从判起' % (len(src_agg), len(ra)))
    sys.exit(1)
lv, rv = src_agg[0].split('=', 1)[1].strip(), ra[0].split('=', 1)[1].strip()
# 09-24 补的守卫：原来只比两个字符串，**两边都取空也照样打 YES** ⇒ 与"聚合相等"同形。
# 现在要求两侧都是非空摘要（sha256 十六进制 64 位）才允许给结论。
for tag, v in (('LOCAL', lv), ('REMOTE', rv)):
    if len(v) != 64 or any(c not in '0123456789abcdef' for c in v.lower()):
        print('ABORT: %s_AGGREGATE 不是一只 sha256 摘要（%r）⇒ 拒给 AGGREGATE_MATCH' % (tag, v[:12]))
        sys.exit(1)
print(src_agg[0].strip())
print(ra[0].strip())
print('AGGREGATE_MATCH=%s' % ('YES' if lv == rv else 'NO'))

# 09-24 补的第二条：本脚本原来的 LANDED_AT 只打 stdout ⇒ 那一遍的时刻在仓库里查无载体
# （文档里"23:04:23 落地"就是靠这句叙述活着的）。现在落地时刻与汇总**自己往 evidence/ 写一只文件**，
# 目标已存在同样拒写。注意：**23:0x 那一次真跑用的是不含本段的旧字节**，所以本文件描述的是
# "下一代落地器会留下载体"，不是"第 7 代的时刻已被补出来"——那只能标成无载体（已按此口径登记）。
land_log = os.path.join(DST, 'r49_land_log.txt')
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

