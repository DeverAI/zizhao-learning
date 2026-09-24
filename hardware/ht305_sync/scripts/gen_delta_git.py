# 清单世代间的**逐名差集尺（git 版）**：上一代名册不靠 mtime/birth 猜，直接从 git 里那一代被提交过的 `MANIFEST.txt` 取，
# 与本代 `MANIFEST.txt` 的名单做双向差集 ⇒ `NEW / GONE` 逐名点名。
# 为什么换这把尺：gen 15 那遍用的口径是"mtime ∈ 区间 且 birth == mtime ⇒ 新入档"，
# 而本代 11 只凭证是 `shutil.copy2` 落地的（**保留源 mtime、birth 是落地时刻**）⇒ `birth == mtime` 对它们恒不成立，
# 那 11 只新入档被错分成了"覆写在册件"（carrier = %TEMP% 里那一遍的输出，本脚本头部把它当作**被推翻的旧尺**登记）。
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
REL = 'hardware/ht305_sync'
CUR = os.path.join(REPO, REL.replace('/', os.sep), 'MANIFEST.txt')

# 参数 1（可选）= 上一代清单所在提交；缺省 = 最后一次改动 MANIFEST.txt 的提交。
ref = sys.argv[1] if len(sys.argv) > 1 else None
if ref is None:
    r = subprocess.run(['git', 'log', '-1', '--format=%H', '--', REL + '/MANIFEST.txt'],
                       capture_output=True, text=True, encoding='utf-8', cwd=REPO)
    ref = r.stdout.strip()
if not re.fullmatch(r'[0-9a-f]{40}', ref or ''):
    print('ABORT: 上一代清单所在提交取不到', repr(ref))
    sys.exit(1)


def names(blob):
    # 清单行形状 = `名字 \t 字节 \t md5 \t BOM \t mtime`（**5 段**，本脚本首跑按 4 段解析 ⇒ 两代名册各 0 只，
    # 被下面那条"名单行数 == TOTAL"的前置钉拦成 ABORT —— 这正是"名册解析不许静默为空"的执行者）
    out = set()
    for l in blob.splitlines():
        p = l.split('\t')
        if len(p) >= 4 and re.fullmatch(r'[0-9a-f]{32}', p[2]):
            out.add(p[0])
    return out


def totals(blob):
    d = {}
    for k in ('TOTAL', 'TOTAL_BYTES', 'BOM_FILES'):
        m = re.search(r'^' + k + r'\t(\d+)$', blob, re.M)
        d[k] = m.group(1) if m else None
    m = re.search(r'现跑于 ([0-9: -]+)', blob)
    d['AT'] = m.group(1) if m else None
    return d


prev_raw = subprocess.run(['git', 'show', ref + ':' + REL + '/MANIFEST.txt'],
                          capture_output=True, text=True, encoding='utf-8', cwd=REPO)
if prev_raw.returncode != 0:
    print('ABORT: git show 失败', prev_raw.stderr[-300:])
    sys.exit(1)
cur_raw = open(CUR, encoding='utf-8-sig').read()
pn, cn = names(prev_raw.stdout), names(cur_raw)
pt, ct = totals(prev_raw.stdout), totals(cur_raw)
for tag, d in (('PREV', pt), ('CUR', ct)):
    if not all(d.get(k) for k in ('TOTAL', 'TOTAL_BYTES', 'BOM_FILES', 'AT')):
        print('ABORT: %s 清单四个字段取不全' % tag, d)
        sys.exit(1)
for tag, d, s in (('PREV', pt, len(pn)), ('CUR', ct, len(cn))):
    if str(s) != d['TOTAL']:
        print('ABORT: %s 名单行数 %d != TOTAL %s ⇒ 名册解析漏了，差集不成立' % (tag, s, d['TOTAL']))
        sys.exit(1)

new, gone = sorted(cn - pn), sorted(pn - cn)
if not new and not gone:
    print('ABORT: 两代名册完全相同 ⇒ 这把尺什么都没读到（两代时刻 %s / %s）' % (pt['AT'], ct['AT']))
    sys.exit(1)

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
lines = ['清单世代逐名差集（git 版，本脚本现跑于 %s）' % now,
         '上一代名册来源 = `git show %s:%s/MANIFEST.txt`（现跑首行时刻 %s，TOTAL %s / BYTES %s / BOM %s）'
         % (ref[:7], REL, pt['AT'], pt['TOTAL'], pt['TOTAL_BYTES'], pt['BOM_FILES']),
         '本代名册来源 = 工作树 `MANIFEST.txt`（现跑首行时刻 %s，TOTAL %s / BYTES %s / BOM %s）'
         % (ct['AT'], ct['TOTAL'], ct['TOTAL_BYTES'], ct['BOM_FILES']),
         '前置钉：两代名单行数已各自等于其 TOTAL 行（%s/%s、%s/%s）⇒ 解析无漏' % (len(pn), pt['TOTAL'], len(cn), ct['TOTAL']),
         '互核：TOTAL 差 = %s - %s = %s；本脚本 NEW=%d GONE=%d ⇒ NEW-GONE=%d %s'
         % (ct['TOTAL'], pt['TOTAL'], int(ct['TOTAL']) - int(pt['TOTAL']), len(new), len(gone),
            len(new) - len(gone),
            'MATCH' if len(new) - len(gone) == int(ct['TOTAL']) - int(pt['TOTAL']) else 'MISMATCH(须点名原因)'),
         '', '--- NEW（本代有、上一代清单没有，逐名）---']
for n in new:
    p = os.path.join(REPO, REL.replace('/', os.sep), n.replace('/', os.sep))
    st = os.stat(p)
    lines.append('NEW\t%s\t%d B\tbirth=%s mtime=%s\t%s' % (
        n, st.st_size, datetime.fromtimestamp(st.st_ctime).strftime('%m-%d %H:%M:%S'),
        datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S'),
        'COPY2(birth>mtime)' if st.st_ctime > st.st_mtime + 1 else 'birth≈mtime'))
lines += ['', '--- GONE（上一代有、本代清单没有，逐名）---']
for n in gone:
    lines.append('GONE\t%s' % n)
lines += ['', '--- 在册件被改写的（两代都在、但盘上 md5 与上一代清单那一行不等）---']
prev_rows = {l.split('\t')[0]: l.split('\t')[2] for l in prev_raw.stdout.splitlines()
             if len(l.split('\t')) >= 4 and re.fullmatch(r'[0-9a-f]{32}', l.split('\t')[2])}
import hashlib
rewr = []
for n in sorted(cn & pn):
    p = os.path.join(REPO, REL.replace('/', os.sep), n.replace('/', os.sep))
    if not os.path.isfile(p):
        continue
    h = hashlib.md5(open(p, 'rb').read()).hexdigest()
    if h != prev_rows.get(n):
        st = os.stat(p)
        rewr.append('%s\tmd5_prev=%s md5_now=%s\tmtime=%s' % (
            n, prev_rows[n][:8], h[:8], datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')))
lines.append('REWRITTEN=%d' % len(rewr))
lines += rewr
txt = '\n'.join(lines) + '\n'
# 输出名里的时刻必须去掉 `:` —— Windows 不允许冒号进文件名（本脚本首跑就在 `open()` 上抛 `OSError 22`，
# 差集本身已经算完，只是那一只文件没落地 ⇒ 修名之后原地重跑）。
def stamp(s):
    return s[6:14].replace(':', '')


out = os.path.join(REPO, REL.replace('/', os.sep), 'evidence',
                   'gen_delta_%s_vs_%s_%s.txt' % (stamp(ct['AT']), stamp(pt['AT']),
                                                  datetime.now().strftime('%H%M%S')))
if os.path.exists(out):
    print('ABORT: 输出已存在，不覆盖', out)
    sys.exit(1)
open(out, 'w', encoding='utf-8', newline='\n').write(txt)
print(txt)
print('OUT', os.path.basename(out), os.path.getsize(out), 'BYTES')
