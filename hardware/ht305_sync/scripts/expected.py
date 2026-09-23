import os, hashlib
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync'
dest_root = stg + '/zizhao_20260923'
rel = []
total = 0
for r, dirs, fs in os.walk(dest_root):
    for x in fs:
        p = os.path.join(r, x)
        rel.append(os.path.relpath(p, dest_root).replace(os.sep, '/'))
        total += os.path.getsize(p)
joined = '\n'.join(sorted(rel))
print('EXPECTED_DIR   = zizhao_20260923')
print('EXPECTED_COUNT =', len(rel))
print('EXPECTED_BYTES =', total)
print('EXPECTED_PATHSHA256 =', hashlib.sha256(joined.encode('utf-8')).hexdigest())
