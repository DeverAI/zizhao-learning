import zipfile, hashlib, subprocess, os, datetime
ROOT = r'C:\Users\david\Documents\all_projects\自招学习'
tmp = os.environ['TEMP']
top = 'zizhao_20260923_r44final/'
z = zipfile.ZipFile(os.path.join(tmp,'zizhao_20260923_r44final.zip'))
out = subprocess.run(['git','-c','core.quotePath=false','ls-tree','-r','--format=%(objectname) %(path)','HEAD'],
    capture_output=True, text=True, encoding='utf-8', cwd=ROOT).stdout
head = dict(l.partition(' ')[::2] for l in out.splitlines())
bl = lambda d: hashlib.sha1(b'blob %d\0' % len(d) + d).hexdigest()
same=eol=genuine=absent=0; gpaths=[]
for i in z.infolist():
    if i.is_dir(): continue
    r = i.filename[len(top):]
    if r == 'SYNC_MANIFEST.txt': continue
    d = z.read(i)
    if r not in head: absent += 1; continue
    if bl(d) == head[r]: same += 1
    elif bl(d.replace(b'\r\n', b'\n')) == head[r]: eol += 1
    else: genuine += 1; gpaths.append(r)
print('T =', datetime.datetime.now().strftime('%H:%M:%S'))
print('exact==HEAD :', same)
print('EOL-only    :', eol)
print('GENUINE diff:', genuine)
print('not in HEAD  :', absent)
print('--- genuine paths ---')
for p in gpaths: print(' ', p)
