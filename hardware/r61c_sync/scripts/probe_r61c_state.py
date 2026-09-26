# 一次性读数器（R61c 收口 paperwork 的第一遍）：只打印、不写盘。
# 目的：paperwork 正文里的每个数都要有"当轮现跑"的出处，而不是从上一代正文里抄。
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:/Users/david/Documents/all_projects/自招学习'


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'git %s failed: %s' % (a, r.stderr.decode('utf-8', 'replace')[:200])
    return r.stdout.decode('utf-8', 'replace')


def stat(rel):
    p = os.path.join(REPO, rel.replace('/', os.sep))
    b = io.open(p, 'rb').read()
    return '%s | bytes=%d | LF=%d | CR=%d | lines=%d | md5=%s' % (
        rel, len(b), b.count(b'\n'), b.count(b'\r'), len(b.splitlines()), hashlib.md5(b).hexdigest()[:8])


print('MEASUREMENTS')
for f in ['FreqErr.md', 'done.md', 'todo.md', 'hardware/烧录须知.md',
          'hardware/20260919_墨水屏点屏排查记录.md', 'dev_log/20260926.md',
          'backups/README.md', 'backups/r43_20260922_131029/docs/SNAPSHOT_NOTE.txt']:
    print(' ', stat(f))
print('FREQERR_ENTRIES', sum(1 for l in io.open(os.path.join(REPO, 'FreqErr.md'), encoding='utf-8').read().split('\n')
                            if l.startswith('[错误类型]')))
print('HEAD', git('rev-parse', '--short', 'HEAD').strip())
print('REVLIST', git('rev-list', '--count', 'origin/main..HEAD').strip())
por = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
print('PORCELAIN_LINES', len(por))
import collections
print('PORCELAIN_BY_OP', dict(collections.Counter(l[:2].strip() or '??' for l in por)))
print('LSFILES_OTHERS', len(git('ls-files', '--others', '--exclude-standard').splitlines()))
print('--- r61c evidence carriers')
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
for n in sorted(os.listdir(EV)):
    p = os.path.join(EV, n)
    print('  %-40s %8d B  %s' % (n, os.path.getsize(p),
                                 __import__('datetime').datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M:%S')))
