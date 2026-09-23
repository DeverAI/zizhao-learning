import subprocess, os, re, shutil
repo = 'C:/Users/david/Documents/all_projects/自招学习'
stg  = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/zizhao_20260923'

def g(args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=repo,
                       capture_output=True, text=True, encoding='utf-8')
    return r.stdout.split()

files = g(['ls-files', '-c']) + g(['ls-files', '-o', '--exclude-standard'])
DROP_PREFIX = ('.workbuddy/',)
DROP_EXACT = set(['dev_log/20260919.md'])
sel = [f for f in files if not f.startswith(DROP_PREFIX) and f not in DROP_EXACT]
dropped = [f for f in files if f not in sel]

if os.path.isdir(stg):
    shutil.rmtree(stg)
missing = []
for f in sel:
    s = os.path.join(repo, f.replace('/', os.sep))
    if not os.path.isfile(s):
        missing.append(f)
        continue
    d = os.path.join(stg, f.replace('/', os.sep))
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(s, d)

pwfile = os.path.join(repo, 'hardware/zizhao-esp32s3/main/provision_ap.c')
pw = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
               open(pwfile, encoding='utf-8').read()).group(1)
hits, total, nbytes = [], 0, 0
for r, dirs, fs in os.walk(stg):
    for x in fs:
        p = os.path.join(r, x)
        b = open(p, 'rb').read()
        total += 1
        nbytes += len(b)
        if pw.encode() in b:
            hits.append(os.path.relpath(p, stg).replace(os.sep, '/'))
logs = [x for _, _, fs in os.walk(stg) for x in fs if x.endswith('.log')]
dirs = [d for _, dd, _ in os.walk(stg) for d in dd]
print('git-listed files    =', len(files))
print('dropped             =', len(dropped), dropped)
print('copied              =', len(sel), '| copy failures =', len(missing), missing[:5])
print('staged files/bytes  =', total, '/', nbytes)
print('plaintext in staging=', len(hits), hits)
print('any .log            =', len(logs), logs[:3])
print('any backups dir     =', 'backups' in dirs)
print('any nvs.csv         =', 'nvs.csv' in [x for _, _, fs in os.walk(stg) for x in fs])
