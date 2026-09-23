import re, os
src = open('hardware/zizhao-esp32s3/main/provision_ap.c', encoding='utf-8').read()
pw = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', src).group(1)
hits=[]
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git','backups','build','managed_components','node_modules','.workbuddy')]
    for f in files:
        p = os.path.join(root, f)
        try:
            b = open(p,'rb').read()
        except Exception as e:
            print('SKIP', p, e); continue
        if pw.encode() in b: hits.append(p)
print('=== whole tree minus backups/ and .git: files with plaintext =', len(hits))
for h in sorted(hits): print('  ', h)
