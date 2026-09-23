import subprocess, os, re, shutil, zipfile, hashlib

repo = 'C:/Users/david/Documents/all_projects/自招学习'
top = 'zizhao_20260923_r44final'
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/' + top
out = 'C:/Users/david/AppData/Local/Temp/' + top + '.zip'


def g(args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=repo,
                       capture_output=True, text=True, encoding='utf-8')
    return r.stdout.split()


files = g(['ls-files', '-c']) + g(['ls-files', '-o', '--exclude-standard'])
DROP_PREFIX = ('.workbuddy/',)
DROP_EXACT = set(['dev_log/20260919.md'])
sel = sorted(set(f for f in files if not f.startswith(DROP_PREFIX) and f not in DROP_EXACT))
dupes = len(files) - len(set(files))

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

pw = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
               open(os.path.join(repo, 'hardware/zizhao-esp32s3/main/provision_ap.c'),
                    encoding='utf-8').read()).group(1).encode()

hits, allf = [], []
for r, dirs, fs in os.walk(stg):
    for x in fs:
        p = os.path.join(r, x)
        allf.append(os.path.relpath(p, stg).replace(os.sep, '/'))
        if pw in open(p, 'rb').read():
            hits.append(os.path.relpath(p, stg).replace(os.sep, '/'))

if os.path.exists(out):
    os.remove(out)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in sorted(allf):
        z.write(os.path.join(stg, rel.replace('/', os.sep)), top + '/' + rel)
    z.writestr(top + '/SYNC_MANIFEST.txt', '\n'.join(sorted(allf)) + '\n')

# local aggregate: EXACT definition recorded in 排查记录 §31.2 (strip top dir, sort, join "\n")
zb = open(out, 'rb').read()
with zipfile.ZipFile(out) as z:
    names = [n for n in z.namelist() if n != top + '/SYNC_MANIFEST.txt']
    digs = [hashlib.sha256(n[len(top) + 1:].encode('utf-8') + z.read(n)).hexdigest() for n in names]
    agg = hashlib.sha256('\n'.join(sorted(digs)).encode('utf-8')).hexdigest()
    content_bytes = sum(z.getinfo(n).file_size for n in names)
    flagged = sum(1 for i in z.infolist() if i.flag_bits & 0x800)

print('git-listed (dupes)  =', len(files), '/ dupes =', dupes)
print('selected            =', len(sel), '| copy failures =', len(missing), missing[:5])
print('staged files        =', len(allf), '| bytes =', sum(os.path.getsize(os.path.join(stg, r.replace("/", os.sep))) for r in allf))
print('plaintext in staging=', len(hits), hits)
print('any .log/.bin/.elf/.map =', [x for x in allf if x.endswith(('.log', '.bin', '.elf', '.map'))])
print('any backups/nvs     =', any('backups/' in x for x in allf), any('nvs.csv' in x for x in allf))
print('zip entries         =', len(names) + 1, '| utf8-flagged =', flagged)
print('zip size/md5        =', len(zb), hashlib.md5(zb).hexdigest())
print('content files/bytes =', len(names), '/', content_bytes)
print('LOCAL_AGGREGATE     =', agg)
