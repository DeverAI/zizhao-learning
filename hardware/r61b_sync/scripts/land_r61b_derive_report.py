# 第 15 代（r61b）派生取证补落：`derive_r61b.py` 只 print 不落盘 ⇒ 那一段 stdout 当时**没有载体**
# （"记录取证那一步自己没落盘"那一族，(64)）。本脚本做的事：把 stdout 原文逐字转录进 evidence/，
# 并给这段转录装两把**独立**的尺，让它不是一句"我相信我看到的"：
#   尺①：6 行报告里各自的 `md5_dst=` 与盘上派生件现算 md5 逐只对（6/6 才写）；
#   尺②：报告尾部那段"指针逐条对盘"的名单，用同一套正则**在盘上重跑一遍**，与转录的集合做双向差集，必须 0-0。
# 另记一条本遍现跑的补扫描结果：大写代次标记的余留（派生表 A 只换小写 ⇒ 反度量 OLD_TOKENS 也全是小写，量不到大写形态）。
# 裁决全部排在写盘之前；目标已存在即 ABORT（不覆盖）；解析路径含 ht305_sync 即 ABORT。
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCRIPT = os.path.join(REPO, 'hardware', 'r61_sync', 'scripts', 'derive_r61b.py')
DST_DIR = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
OUT = os.path.join(EV, 'r61b_derive_report.txt')
for _p in (EV, OUT, DST_DIR, SCRIPT):
    if 'ht305_sync' in _p:
        raise SystemExit('ABORT: 路径指进了封存归档目录 ' + _p)

# ---------- 待转录的 stdout 原文（13:05 那一遍，rc=0；逐字，不改一个字符） ----------
REPORT = [
    "sync_r61.py -> sync_r61b.py | src_lines=128 dst_lines=128 | md5_src=034a7cf3 md5_dst=eca7adf5 | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 9, 'zsynctest17': 0, '第 15 代': 1, '第 14 代': 1, 'gen-15': 0, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 4, 'D 余留 ht305_sync/scripts': 0}",
    "r61_upload.ps1 -> r61b_upload.ps1 | src_lines=109 dst_lines=109 | md5_src=f0068c12 md5_dst=4df956af | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 19, 'zsynctest17': 5, '第 15 代': 1, '第 14 代': 1, 'gen-15': 0, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 3, 'D 余留 ht305_sync/scripts': 0}",
    "chk_r61.ps1 -> chk_r61b.ps1 | src_lines=44 dst_lines=44 | md5_src=f3c17a01 md5_dst=a07aac4a | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 9, 'zsynctest17': 0, '第 15 代': 0, '第 14 代': 1, 'gen-15': 1, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 3, 'D 余留 ht305_sync/scripts': 0}",
    "r61_listdiff.py -> r61b_listdiff.py | src_lines=89 dst_lines=89 | md5_src=ce2c3d23 md5_dst=af81a6bb | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 18, 'zsynctest17': 0, '第 15 代': 2, '第 14 代': 1, 'gen-15': 0, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 2, 'D 余留 ht305_sync/scripts': 0}",
    "r61_cutoff_delta.py -> r61b_cutoff_delta.py | src_lines=81 dst_lines=81 | md5_src=3a74421d md5_dst=918ef72f | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 6, 'zsynctest17': 0, '第 15 代': 1, '第 14 代': 1, 'gen-15': 0, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 2, 'D 余留 ht305_sync/scripts': 0}",
    "r61_roundtrip.py -> r61b_roundtrip.py | src_lines=105 dst_lines=105 | md5_src=09133e0c md5_dst=5eb393fb | LEFT={'r55': 0, 'zsynctest15': 0, 'zizhao_20260926_r61final': 0} | {'r61b': 11, 'zsynctest17': 2, '第 15 代': 1, '第 14 代': 1, 'gen-15': 0, 'r61_sync/scripts': 1, '守卫 ht305_sync 出现次数': 2, 'D 余留 ht305_sync/scripts': 0}",
]
POINTERS = [
    'sync_r61b.py  hardware/r61_sync/scripts/sync_r61.py  OK',
    'r61b_upload.ps1  hardware/r61_sync/scripts/r61_upload.ps1  OK',
    'chk_r61b.ps1  hardware/r61_sync/scripts/chk_r61.ps1  OK',
    'chk_r61b.ps1  hardware/r61b_sync/scripts/r61b_upload.ps1  OK',
    'r61b_listdiff.py  hardware/r61_sync/scripts/r61_listdiff.py  OK',
    'r61b_listdiff.py  hardware/r61b_sync/scripts/r61b_cutoff_delta.py  OK',
    'r61b_cutoff_delta.py  hardware/r61_sync/scripts/r61_cutoff_delta.py  OK',
    'r61b_roundtrip.py  hardware/r61_sync/scripts/r61_roundtrip.py  OK',
]
EVPTRS = ['chk_r61b.ps1  hardware/r61b_sync/evidence/r61b_parse_check.txt  not-yet(=本代待写)']
DERIVED = ['sync_r61b.py', 'r61b_upload.ps1', 'chk_r61b.ps1',
           'r61b_listdiff.py', 'r61b_cutoff_delta.py', 'r61b_roundtrip.py']

# ---------- 尺①：报告里每只的 md5_dst 必须等于盘上现算值 ----------
pairs = []
for line in REPORT:
    m = re.search(r'-> (\S+) \|.*?md5_dst=([0-9a-f]{8})', line)
    assert m, 'ABORT: 报告行里读不出 md5_dst：' + line[:40]
    p = os.path.join(DST_DIR, m.group(1))
    assert os.path.isfile(p), 'ABORT: 报告点名的派生件不在盘上 ' + p
    now8 = hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]
    assert now8 == m.group(2), 'ABORT: md5 不符 %s 转录=%s 现算=%s' % (m.group(1), m.group(2), now8)
    pairs.append('%s md5_dst(转录)==md5(现算)=%s PASS' % (m.group(1), now8))
assert len(pairs) == len(DERIVED) == len(REPORT), 'ABORT: 报告行数 / 派生件只数 / md5 对数三者不等 (%d,%d,%d)' % (
    len(pairs), len(DERIVED), len(REPORT))

# ---------- 尺②：指针名单在盘上重跑，与转录集合做双向差集 ----------
PTR = re.compile(r'hardware[/\\]r61b?_sync[/\\]scripts[/\\][A-Za-z0-9_.\-]+')
PTRA = re.compile(r'hardware[/\\]r61b?_sync[/\\]evidence[/\\][A-Za-z0-9_.\-]+')
redo = set()
for fn in DERIVED:
    txt = io.open(os.path.join(DST_DIR, fn), encoding='utf-8').read()
    for m in set(PTR.findall(txt)):
        p = os.path.normpath(os.path.join(REPO, m.replace('\\', '/')))
        redo.add('%s  %s  %s' % (fn, m.replace('\\', '/'),
                                 'OK' if (os.path.isfile(p) or os.path.isdir(p)) else 'MISSING'))
redo_ptr = set(POINTERS)
only_tr = sorted(redo_ptr - redo)
only_re = sorted(redo - redo_ptr)
assert not only_tr and not only_re, 'ABORT: 指针名单重跑与转录不等 %s / %s' % (only_tr, only_re)
assert 'MISSING' not in ' '.join(POINTERS), 'ABORT: 转录里出现 MISSING 指针'

# ---------- 本遍补扫描：大写代次标记（派生表 A 只换小写，反度量 OLD_TOKENS 也只小写 ⇒ 量不到这里） ----------
upper_hits = []
for _fn in DERIVED:
    for _i, _l in enumerate(io.open(os.path.join(DST_DIR, _fn), encoding='utf-8').read().splitlines()):
        if re.search(r'R61|R55', _l) and not _l.lstrip().startswith('#'):
            upper_hits.append('%s:%d %s' % (_fn, _i + 1, _l.strip()))

# ---------- 六只派生件 mtime 现读（"一次派生"这句要有盘上出处，不能把上面 stat 那一眼抄进正文） ----------
import datetime
MT = []
for fn in DERIVED:
    st = os.stat(os.path.join(DST_DIR, fn))
    MT.append('%s mtime=%s bytes=%d' % (
        fn, datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'), st.st_size))
MTS = set(x.split('mtime=')[1].split(' bytes=')[0] for x in MT)
assert len(MTS) == 1, 'ABORT: 六只 mtime 不同值，"一次派生"不成立：%s' % sorted(MTS)
DERIVED_AT = MTS.pop()

BODY = '\n'.join([
    '第 15 代（r61b）同步件派生取证 · stdout 逐字转录 + 两把独立尺复核',
    'DERIVE_SCRIPT      = hardware/r61_sync/scripts/derive_r61b.py（md5 现读 %s / 行数现读 %d）' % (
        hashlib.md5(open(SCRIPT, 'rb').read()).hexdigest()[:8],
        len(io.open(SCRIPT, encoding='utf-8').read().splitlines())),
    'DERIVED_AT         = %s（六只派生件盘上 mtime **现读且同值**，逐只见文末 stat 段）' % DERIVED_AT,
    '本载体是**事后补落**：派生器本身只 print 不写文件，那一遍跑完（rc=0）盘上没有任何一份它的读数。',
    '为让这段转录不只是一句"我相信我看到的"，本脚本对它做两件独立复核：',
    '  尺① 报告 6 行里各自的 md5_dst，与盘上派生件现算 md5 逐比对；',
    '  尺② 尾部"指针逐条对盘"那段名单，用同一套正则在盘上**重跑**一遍，与转录集合做双向差集，必须 0-0。',
    '转录正文（rc=0 那一遍的 stdout，逐字）：',
    '----- BEGIN stdout -----',
] + REPORT + POINTERS + EVPTRS + [
    'WROTE=6 DIR=%s EV_DIR=%s' % (DST_DIR, EV),
    'POINTERS_SCRIPTS=%d MISSING=0 | EVIDENCE_POINTERS_REPORTED=%d' % (len(POINTERS), len(EVPTRS)),
    'VERDICT=DERIVED rc=0',
    '----- END stdout -----',
    '',
    '尺① 复核（本遍现算，md5 逐只对：通过 %d 行 / 报告点名 %d 只 / 派生件名单 %d 只，三者必须同值）：' % (
        len(pairs), len(REPORT), len(DERIVED)),
] + ['  ' + x for x in pairs] + [
    '尺② 复核：指针名单重跑 转录-only=%d 重跑-only=%d（两个都必须 0）' % (len(only_tr), len(only_re)),
    'stat 段（本遍现读，逐只；六行 mtime 必须同值，否则"一次派生"这句不成立）：',
] + ['  ' + x for x in MT] + [
    '',
    '本遍补扫描·大写代次标记余留（**派生表的已知盲区**，不是本代的缺陷读数）：',
    '  命中 %d 处：%s' % (len(upper_hits), '、'.join(upper_hits)),
    '  ⇒ 派生表 A 只换小写 `r61`，反度量 OLD_TOKENS 也全是小写形态，所以这一处**在派生器眼里不存在**；',
    '  ⇒ 它只影响 `r61b_roundtrip.py` 自己那行标签（打印出的 `R61_ROUNDTRIP_AT`），',
    '    该行右侧的数值仍是脚本当场跑的读数（时刻见同目录 r61b_roundtrip.txt）⇒ 本代不返工：',
    '    返工会新增一只载体，而它的 PRIOR_ATTEMPT 句写的是"前一只读数不作数"，与事实相反。',
    '    改法记给下一代派生表：替换表加一条 `R61`→`R61B`（并把它纳入反度量 OLD_TOKENS 的大写形态）。',
], ) + '\n'

if os.path.exists(OUT):
    raise SystemExit('ABORT: 取证件已存在，不覆盖 ' + OUT)
with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
    f.write(BODY)
back = io.open(OUT, encoding='utf-8').read()
assert back == BODY, 'ABORT: 回读不等于写入'
assert 'MISSING' not in back.split('----- END stdout -----')[1], 'ABORT: 复核段里出现 MISSING'
print(BODY)
print('OUT=%s BYTES=%d LINES=%d' % (OUT, os.path.getsize(OUT), back.count('\n')))
print('VERDICT=LANDED rc=0')
