import zipfile, os, hashlib, sys
stg = 'C:/Users/david/AppData/Local/Temp/zizhao_sync/zizhao_20260923'
out = 'C:/Users/david/AppData/Local/Temp/zizhao_sync_20260923_r43.zip'
if os.path.exists(out):
    os.remove(out)
names = []
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for r, dirs, fs in os.walk(stg):
        for x in sorted(fs):
            p = os.path.join(r, x)
            arc = os.path.relpath(p, os.path.dirname(stg)).replace(os.sep, '/')
            z.write(p, arc)
            names.append(arc)
    z.writestr('zizhao_20260923/SYNC_MANIFEST.txt',
               '\n'.join(sorted(names)) + '\n')
b = open(out, 'rb').read()
print('zip files   =', len(names))
print('zip bytes   =', len(b))
print('zip md5     =', hashlib.md5(b).hexdigest())
nonascii = [n for n in names if any(ord(c) > 127 for c in n)]
print('non-ascii   =', len(nonascii))
print('sample      =', nonascii[0] if nonascii else 'none')
with zipfile.ZipFile(out) as z:
    infos = z.infolist()
    flagged = sum(1 for i in infos if i.flag_bits & 0x800)
    print('entries     =', len(infos), '| utf8-flagged  =', flagged)
