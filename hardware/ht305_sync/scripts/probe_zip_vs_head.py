import zipfile, hashlib, subprocess, os, datetime
tmp = os.environ['TEMP']
zp = os.path.join(tmp, 'zizhao_20260923_r44final.zip')
top = 'zizhao_20260923_r44final/'
git = lambda *a: subprocess.run(['git','-c','core.quotePath=false',*a],
        capture_output=True, text=True, encoding='utf-8',
        cwd=r'C:\Users\david\Documents\all_projects\自招学习').stdout
def blob(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
out = git('ls-tree','-r','--format=%(objectname) %(path)','HEAD')
head = {}
for line in out.splitlines():
    h, _, p = line.partition(' ')
    head[p] = h
z = zipfile.ZipFile(zp)
rels = [i.filename[len(top):] for i in z.infolist() if not i.is_dir()]
same=diff=absent=0; diffs=[]
for r in rels:
    if r=='SYNC_MANIFEST.txt': continue
    data=z.read(top+r)
    if r not in head: absent+=1; continue
    if blob(data)==head[r]: same+=1
    else:
        diff+=1
        if data.replace(b'\r\n',b'\n')==z.read(top+r).replace(b'\r\n',b'\n') and blob(data.replace(b'\r\n',b'\n'))==head[r]:
            diffs.append(r+' [EOL-only]')
        else: diffs.append(r)
print('T =', datetime.datetime.now().strftime('%H:%M:%S'))
print('same=%d diff=%d notinHEAD=%d' % (same,diff,absent))
print('--- differing (first 15) ---')
for d in diffs[:15]: print(d)
