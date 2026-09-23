import sys, os, datetime
sys.stdout.reconfigure(encoding='utf-8')
dst = 'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
os.chdir(dst)
listed = set()
for line in open('MANIFEST.txt', encoding='utf-8'):
    p = line.split('\t')[0].strip()
    if p.startswith(('evidence/', 'gate/', 'scripts/')) or p == 'README.md':
        listed.add(p)
cur = set()
for r, ds, fs in os.walk('.'):
    for f in fs:
        cur.add(os.path.relpath(os.path.join(r, f), '.').replace(os.sep, '/'))
new = sorted(cur - listed)
lines = ['RAN_AT = ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         '口径：拿 gen 9 那份 `MANIFEST.txt` 的逐名行 与 盘上现状 做差集（判"第 5 代同步往归档里放了几只"）',
         'listed(gen 9 manifest) = %d' % len(listed),
         'on disk now            = %d' % len(cur),
         'NEW since gen 9        = %d' % len(new)]
lines += ['  + ' + n for n in new]
lines.append('GONE = %s' % sorted(listed - cur))
lines.append('入清单只数 = NEW 减去 `MANIFEST.txt`（清单不自列）与 `evidence/manifest_gen_log.txt`（代次日志按设计不进清单）')
out = '\n'.join(lines) + '\n'
open('evidence/arch_delta_r47_vs_gen9.txt', 'w', encoding='utf-8', newline='\n').write(out)
print(out)
