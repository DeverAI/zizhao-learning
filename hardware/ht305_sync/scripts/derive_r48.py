# 第 6 代同步工具派生：逐字从第 5 代派生，但**对每个替换断言命中数**，且**源文件不存在即 ABORT**（第 5 代正是栽在"派生工具继承了上一代'依赖一个恰好存在的副作用'"，见排查记录 §34.8-②）。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

JOBS = [
    ('sync_r47.py', 'sync_r48.py', [('r47final', 'r48final'), ('r47_', 'r48_')], 'utf-8'),
    ('r47_upload.ps1', 'r48_upload.ps1',
     [('r47final', 'r48final'), ('zsynctest7', 'zsynctest8'), ('r47_', 'r48_')], 'utf-8-sig'),
    ('chk_r47.ps1', 'chk_r48.ps1',
     [('r47', 'r48'), ('gen-5', 'gen-6')], 'utf-8-sig'),
    ('r47_cutoff_delta.py', 'r48_cutoff_delta.py', [('r47final', 'r48final'), ('r47_', 'r48_')], 'utf-8'),
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
    print('DERIVED', dst, len(raw), 'B |', ' '.join(counts),
          '| BOM=%s NONASCII=%s OK=%s' % (bom, nonascii, (bom or not nonascii)))
