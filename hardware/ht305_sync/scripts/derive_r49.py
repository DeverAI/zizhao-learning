# 第 7 代同步工具派生：逐字从第 6 代派生，**对每个替换断言命中数**、**源不存在即 ABORT**、**目标已存在即 ABORT**（口径来自排查记录 §34.8-② 与 §36.2）。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

JOBS = [
    ('sync_r48.py', 'sync_r49.py', [('r48final', 'r49final'), ('r48_', 'r49_')], 'utf-8'),
    ('r48_upload.ps1', 'r49_upload.ps1',
     [('r48final', 'r49final'), ('zsynctest8', 'zsynctest9'), ('r48_', 'r49_')], 'utf-8-sig'),
    ('chk_r48.ps1', 'chk_r49.ps1',
     [('r48', 'r49'), ('gen-6', 'gen-7')], 'utf-8-sig'),
    ('r48_cutoff_delta.py', 'r49_cutoff_delta.py', [('r48final', 'r49final'), ('r48_', 'r49_')], 'utf-8'),
    ('r48_listdiff.py', 'r49_listdiff.py',
     [('r48final', 'r49final'), ('r48_', 'r49_'), ('第 6 代', '第 7 代')], 'utf-8'),
]

for src, dst, reps, enc in JOBS:
    sp, dp = os.path.join(SCR, src), os.path.join(SCR, dst)
    if not os.path.isfile(sp):
        print('ABORT: 派生源不存在', src)
        sys.exit(1)
    if os.path.exists(dp):
        print('ABORT: 目标已存在，不覆盖', dst)
        sys.exit(1)
    txt = open(sp, encoding='utf-8' if enc == 'utf-8' else 'utf-8-sig').read()
    counts = []
    for a, b in reps:
        n = txt.count(a)
        if n == 0:
            print('ABORT: 替换串在本代源里 0 命中 %s -> %s (%s)' % (a, b, src))
            sys.exit(1)
        txt = txt.replace(a, b)
        counts.append('%s->%s:%d' % (a, b, n))
    with open(dp, 'w', encoding=enc, newline='') as f:
        f.write(txt)
    raw = open(dp, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    nonascii = any(x > 0x7F for x in raw)
    # 只有 .ps1 必须带 BOM（PowerShell 5.1 按 GBK 解码无 BOM 的 UTF-8）；.py 不带 BOM 才对 ⇒ 尺子按扩展名分
    need_bom = dst.endswith('.ps1')
    ok = (bom if need_bom else not bom) and (nonascii or not need_bom)
    print('DERIVED', dst, len(raw), 'B |', ' '.join(counts),
          '| BOM=%s NONASCII=%s NEED_BOM=%s OK=%s' % (bom, nonascii, need_bom, ok))
    if not ok:
        print('ABORT: 编码形态不符合本代口径', dst)
        sys.exit(1)
