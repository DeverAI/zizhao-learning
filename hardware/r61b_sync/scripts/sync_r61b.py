# 第 15 代 ht305 全量同步打包件：由 `hardware/r61_sync/scripts/sync_r61.py`（第 14 代）逐字派生。
# 派生改动逐处点名（只动名字与边界，不动口径）：
#   ①`top` 换代 r61final -> r61bfinal（日期跟着换成 20260926）；
#   ②**取证目录从 `hardware/ht305_sync/evidence/` 换到 `hardware/r61b_sync/evidence/`**，并新装一只 ABORT：
#     解析出的 ev 路径里出现 `ht305_sync` 就停。动因：那边停在 gen 24 的 SEAL，本代不新建清单代 ⇒
#     任何一只派生字节日落进去都会让 `verify_manifest.py` 报 MANIFEST_STALE（"检查动作污染被检查物"那一族）；
#   ③`DROP_PREFIX / DROP_EXACT` 之外**把实际排掉的只名逐只点名写进 `r61b_local.txt`**：
#     上一代只写"排了几只"的计数（`selected = %d`），排掉的是谁只在代码里，载体上读不到 ⇒
#     一次 `git rm --cached` + `.gitignore` 就能让某只悄悄离开载荷而全代读数不变。
#     两只原厂整片/分区表镜像自 09-26 起走 `.gitignore` 精确名排除（不在这里硬编码），本行的职责是**把当次真排掉的列出来**。
#   ④`tmp` 仍在（本机 zip 落 %TEMP%，那是运输载体不是取证载体）——与上一代同。
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

repo = 'C:/Users/david/Documents/all_projects/自招学习'
top = 'zizhao_20260926_r61bfinal'
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/' + top
tmp = 'C:/Users/david/AppData/Local/Temp'
out = os.path.join(tmp, top + '.zip')
ev = os.path.join(repo, 'hardware', 'r61b_sync', 'evidence')
if 'ht305_sync' in ev:
    raise SystemExit('ABORT: 取证落点指进了封存归档目录 ' + ev)

# cutoff: the moment the payload is read off disk -- everything edited after this is NOT in the package
now = lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
CUTOFF_COPY_BEGIN = now()
print('CUTOFF (copy begin) =', CUTOFF_COPY_BEGIN)

if not os.path.isdir(ev):
    raise SystemExit('ABORT: 取证目录不存在，拒绝往未知路径写：' + ev)
written = []


def write_ev(name, text):
    """取证进仓库，且只许首次写入（已存在即 ABORT，不覆盖、不删）。"""
    p = os.path.join(ev, name)
    assert 'ht305_sync' not in p, 'ABORT: 取证件落点指进封存归档目录 ' + p
    if os.path.exists(p):
        raise SystemExit('ABORT: 取证件已存在，不覆盖：' + p)
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)
    written.append(name)
    return p


def g(args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=repo,
                       capture_output=True, text=True, encoding='utf-8')
    return r.stdout.split()


files = g(['ls-files', '-c']) + g(['ls-files', '-o', '--exclude-standard'])
DROP_PREFIX = ('.workbuddy/',)
DROP_EXACT = set(['dev_log/20260919.md'])
dropped = sorted(set(f for f in files if f.startswith(DROP_PREFIX) or f in DROP_EXACT))
sel = sorted(set(f for f in files if not f.startswith(DROP_PREFIX) and f not in DROP_EXACT))

if 'zizhao_sync/' not in stg:
    raise SystemExit('ABORT: 暂存目录路径异常，拒绝递归删除 ' + stg)
if os.path.exists(out):
    raise SystemExit('ABORT: 本机包已存在，不覆盖不删除，请换新名字 ' + out)
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

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in sorted(allf):
        z.write(os.path.join(stg, rel.replace('/', os.sep)), top + '/' + rel)
    z.writestr(top + '/SYNC_MANIFEST.txt', '\n'.join(sorted(allf)) + '\n')
CUTOFF_ZIP_MADE = now()

# aggregate definition pinned in 排查记录 §31.2: strip top dir, sort digests, join "\n", sha256; exclude SYNC_MANIFEST.txt
zb = open(out, 'rb').read()
with zipfile.ZipFile(out) as z:
    names = [n for n in z.namelist() if n != top + '/SYNC_MANIFEST.txt']
    digs = [hashlib.sha256(n[len(top) + 1:].encode('utf-8') + z.read(n)).hexdigest() for n in names]
    agg = hashlib.sha256('\n'.join(sorted(digs)).encode('utf-8')).hexdigest()
    content_bytes = sum(z.getinfo(n).file_size for n in names)
    flagged = sum(1 for i in z.infolist() if i.flag_bits & 0x800)

write_ev('r61b_local_names.txt',
         '\n'.join(sorted(names[i][len(top) + 1:] for i in range(len(names)))) + '\n')

write_ev('r61b_local.txt',
         'git-listed (dupes)  = %d / dupes = %d\n' % (len(files), len(files) - len(set(files)))
         + 'selected            = %d | copy failures = %d %s\n' % (len(sel), len(missing), missing[:5])
         + 'dropped (逐只点名)   = %d %s\n' % (len(dropped), dropped)
         + 'staged files        = %d | bytes = %d\n' % (len(allf), sum(os.path.getsize(os.path.join(stg, r.replace('/', os.sep))) for r in allf))
         + 'plaintext in staging= %d %s\n' % (len(hits), hits)
         + 'any .log/.bin/.elf/.map = %s\n' % [x for x in allf if x.endswith(('.log', '.bin', '.elf', '.map'))]
         + 'any backups/nvs     = %s %s\n' % (any('backups/' in x for x in allf), any('nvs.csv' in x for x in allf))
         + 'zip entries         = %d | utf8-flagged = %d\n' % (len(names) + 1, flagged)
         + 'zip size/md5        = %d %s\n' % (len(zb), hashlib.md5(zb).hexdigest())
         + 'content files/bytes = %d / %d\n' % (len(names), content_bytes)
         + 'LOCAL_AGGREGATE     = %s\n' % agg
         + 'CUTOFF_COPY_BEGIN   = %s\n' % CUTOFF_COPY_BEGIN
         + 'CUTOFF_ZIP_MADE     = %s\n' % CUTOFF_ZIP_MADE
         + 'EVIDENCE_IN_REPO    = %s（取证自 gen 13 起直接进仓库；本代进的是 r61b_sync/evidence，见文件头②）\n' % ','.join(written))
print(open(os.path.join(ev, 'r61b_local.txt'), encoding='utf-8').read())
