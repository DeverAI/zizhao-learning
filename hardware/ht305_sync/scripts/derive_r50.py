# 第 8 代同步工具派生：逐字从第 7 代派生，**对每个替换断言命中数**、**源不存在即 ABORT**、**目标已存在即 ABORT**
# （口径来自排查记录 §34.8-② 与 §36.2；派生器本身会连注释里的"尺子"一起派生，见 FreqErr ht305 段 ⑲ 与 gen 12 那格）。
# 本代替换表多一条：包名日期跟着日历走 ⇒ zizhao_20260923_* -> zizhao_20260924_*（第 1~7 代都写在 09-23 内）。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

TOP_OLD = 'zizhao_20260923_r49final'
TOP_NEW = 'zizhao_20260924_r50final'

JOBS = [
    ('sync_r49.py', 'sync_r50.py',
     [(TOP_OLD, TOP_NEW), ('r49_', 'r50_')], 'utf-8'),
    ('r49_upload.ps1', 'r50_upload.ps1',
     [(TOP_OLD, TOP_NEW), ('zsynctest9', 'zsynctest10'), ('r49_', 'r50_')], 'utf-8-sig'),
    ('chk_r49.ps1', 'chk_r50.ps1',
     [('r49', 'r50'), ('gen-7', 'gen-8')], 'utf-8-sig'),
    ('r49_cutoff_delta.py', 'r50_cutoff_delta.py',
     [(TOP_OLD, TOP_NEW), ('r49_', 'r50_')], 'utf-8'),
    ('r49_listdiff.py', 'r50_listdiff.py',
     [('r49final', 'r50final'), ('r49_', 'r50_'), ('第 7 代', '第 8 代')], 'utf-8'),
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
    # 只有 .ps1 必须带 BOM（PowerShell 5.1 按 GBK 解码无 BOM 的 UTF-8）；.py 不带 BOM 才对
    need_bom = dst.endswith('.ps1')
    ok = (bom if need_bom else not bom) and (nonascii or not need_bom)
    print('DERIVED', dst, len(raw), 'B |', ' '.join(counts),
          '| BOM=%s NONASCII=%s NEED_BOM=%s OK=%s' % (bom, nonascii, need_bom, ok))
    if not ok:
        print('ABORT: 编码形态不符合本代口径', dst)
        sys.exit(1)

# 派生完把"本代不再引用上一代解包根"这件事读一遍：上一代栽过的地方（把 zsynctest8 喂给差集器）
for dst in ['sync_r50.py', 'r50_upload.ps1', 'chk_r50.ps1', 'r50_cutoff_delta.py', 'r50_listdiff.py']:
    t = open(os.path.join(SCR, dst), encoding='utf-8-sig').read()
    left = [k for k in ('r49final', 'zsynctest9', '第 7 代') if k in t]
    print('LEFTOVER_CHECK', dst, left if left else 'CLEAN')
