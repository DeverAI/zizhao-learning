import re, subprocess
src = open('hardware/zizhao-esp32s3/main/provision_ap.c', encoding='utf-8').read()
pw = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', src).group(1)
files = subprocess.run(['git','-c','core.quotePath=false','diff','--cached','--name-only'],
                       capture_output=True, text=True, encoding='utf-8').stdout.split()
bad = []
for f in files:
    b = subprocess.run(['git','show',':'+f], capture_output=True).stdout
    n = b.count(pw.encode())
    if n: bad.append((f, n))
print('staged files =', len(files), '| with plaintext =', len(bad))
for f, n in bad: print('  !', n, f)
