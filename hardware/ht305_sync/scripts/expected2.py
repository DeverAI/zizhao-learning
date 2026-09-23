import os, hashlib
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync'
root = stg + '/zizhao_20260923'
digs = []
for r, dirs, fs in os.walk(root):
    for x in fs:
        p = os.path.join(r, x)
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        if rel == 'SYNC_MANIFEST.txt':
            continue
        h = hashlib.sha256()
        h.update(rel.encode('utf-8'))
        h.update(open(p, 'rb').read())
        digs.append(h.hexdigest())
digs.sort()
agg = hashlib.sha256(('\n'.join(digs)).encode('utf-8')).hexdigest()
print('LOCAL_FILES      =', len(digs))
print('LOCAL_AGGREGATE  =', agg)
