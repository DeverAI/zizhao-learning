import os, hashlib, datetime

repo = 'C:/Users/david/Documents/all_projects/自招学习'
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/zizhao_20260923_r45final'
out = 'C:/Users/david/AppData/Local/Temp/r45_cutoff_delta.txt'


def h(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


staged = {}
for r, dirs, fs in os.walk(stg):
    for x in fs:
        p = os.path.join(r, x)
        staged[os.path.relpath(p, stg).replace(os.sep, '/')] = p

same, diff, gone = [], [], []
for rel, p in staged.items():
    q = os.path.join(repo, rel.replace('/', os.sep))
    if not os.path.isfile(q):
        gone.append(rel)
    elif h(p) == h(q):
        same.append(rel)
    else:
        diff.append(rel)

# files currently selected for the package that are NOT in the 10:03:58 staging tree
import subprocess


def g(args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=repo,
                       capture_output=True, text=True, encoding='utf-8')
    return r.stdout.split()


files = g(['ls-files', '-c']) + g(['ls-files', '-o', '--exclude-standard'])
sel = sorted(set(f for f in files
                 if not f.startswith('.workbuddy/') and f != 'dev_log/20260919.md'))
new_since = [f for f in sel if f not in staged]

with open(out, 'w', encoding='utf-8') as fh:
    fh.write('RAN_AT   = %s\n' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    fh.write('staged   = %d\n' % len(staged))
    fh.write('identical(内容逐字节等,  sha256) = %d\n' % len(same))
    fh.write('changed_since_cutoff = %d %s\n' % (len(diff), sorted(diff)))
    fh.write('deleted_since_cutoff = %d %s\n' % (len(gone), sorted(gone)))
    fh.write('new_since_cutoff     = %d %s\n' % (len(new_since), new_since))
print(open(out, encoding='utf-8').read())
