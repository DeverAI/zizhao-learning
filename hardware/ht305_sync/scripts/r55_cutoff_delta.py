import datetime
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
EV = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
STG = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/zizhao_20260924_r55final'
out = os.path.join(EV, 'r55_cutoff_delta.txt')


def h(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


if os.path.exists(out):
    print('ABORT: 取证件已存在，不覆盖', out)
    sys.exit(1)
if not os.path.isdir(STG):
    print('ABORT: 暂存树不存在（先跑 sync_r55.py）', STG)
    sys.exit(1)

staged = {}
for r, dirs, fs in os.walk(STG):
    for x in fs:
        p = os.path.join(r, x)
        staged[os.path.relpath(p, STG).replace(os.sep, '/')] = p

same, diff, gone = [], [], []
for rel, p in staged.items():
    q = os.path.join(REPO, rel.replace('/', os.sep))
    if not os.path.isfile(q):
        gone.append(rel)
    elif h(p) == h(q):
        same.append(rel)
    else:
        diff.append(rel)

# files currently selected for the package but NOT in **this run's** staging tree
import subprocess


def g(args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8')
    return r.stdout.split()


files = g(['ls-files', '-c']) + g(['ls-files', '-o', '--exclude-standard'])
sel = sorted(set(f for f in files
                 if not f.startswith('.workbuddy/') and f != 'dev_log/20260919.md'))
new_since = [f for f in sel if f not in staged]

# 本代新装的一道自核（(77) 那族"数值对而过程未自证"）：四个桶必须**互斥且并起来等于当前候选集**。
# 上一代只报了 4 个数，没报"这四个数是不是同一把尺上的一次划分"。
union = set(diff) | set(gone) | set(same) | set(new_since)
assert union == set(sel), 'ABORT: 四桶并集 != 当前候选集，说明有一侧口径漏了（差 %d 只）' % (
    len(union ^ set(sel)))
assert len(diff) + len(gone) + len(same) == len(staged), 'ABORT: 暂存树三桶没分完'
assert not (set(same) & set(new_since)) and not (set(diff) & set(new_since)), 'ABORT: 桶之间重叠'

with open(out, 'w', encoding='utf-8') as fh:
    fh.write('RAN_AT   = %s\n' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    fh.write('staged   = %d\n' % len(staged))
    fh.write('identical(内容逐字节等,  sha256) = %d\n' % len(same))
    fh.write('changed_since_cutoff = %d %s\n' % (len(diff), sorted(diff)))
    fh.write('deleted_since_cutoff = %d %s\n' % (len(gone), sorted(gone)))
    fh.write('new_since_cutoff     = %d %s\n' % (len(new_since), new_since))
    fh.write('SELF_CHECK = 四桶互斥且并集 == 当前候选集(%d)：PASS\n' % len(sel))
    fh.write('EXPLANATION = new_since 是本代**打包截止之后**才进仓库的取证/脚本件（取证直接落 evidence/ 的必然结果），'
             '不是包漏了东西；判"包 == 现状"看的是 changed/deleted 两桶。\n')
print(open(out, encoding='utf-8').read())
