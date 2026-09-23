# 第 9 代同步工具派生：逐字从第 8 代派生，**对每个替换断言命中数**、**源不存在即 ABORT**、**目标已存在即 ABORT**
# （口径来自排查记录 §34.8-② 与 §36.2；派生器本身会连注释里的"尺子"一起派生，见 FreqErr ht305 段 ⑲ 与 gen 12 那格）。
# 本代比第 8 代多两个作业：落地器 `land_r50_evidence.py` 与尾件回扫 `r50_roundtrip.py` 一起进表
# （上一代那两只是**另写**的一次性脚本 ⇒ 派生表覆盖不到它们，"整代工具同源"这句话当时只覆盖五只）。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

TOP_OLD = 'zizhao_20260924_r50final'
TOP_NEW = 'zizhao_20260924_r51final'

JOBS = [
    ('sync_r50.py', 'sync_r51.py',
     [(TOP_OLD, TOP_NEW), ('r50', 'r51')], 'utf-8'),
    ('r50_upload.ps1', 'r51_upload.ps1',
     [(TOP_OLD, TOP_NEW), ('zsynctest10', 'zsynctest11'), ('r50', 'r51')], 'utf-8-sig'),
    ('chk_r50.ps1', 'chk_r51.ps1',
     [('gen-8', 'gen-9'), ('r50', 'r51')], 'utf-8-sig'),
    ('r50_cutoff_delta.py', 'r51_cutoff_delta.py',
     [(TOP_OLD, TOP_NEW), ('r50', 'r51')], 'utf-8'),
    ('r50_listdiff.py', 'r51_listdiff.py',
     [('第 8 代', '第 9 代'), ('r50final', 'r51final'), ('r50', 'r51')], 'utf-8'),
    ('land_r50_evidence.py', 'land_r51_evidence.py',
     [('第 8 代', '第 9 代'), ('r50', 'r51')], 'utf-8'),
    ('r50_roundtrip.py', 'r51_roundtrip.py',
     [(TOP_OLD, TOP_NEW), ('zsynctest10', 'zsynctest11'), ('第 8 代', '第 9 代'),
      ('R50', 'R51'), ('r50', 'r51')], 'utf-8'),
]

for src, dst, reps, enc in JOBS:
    sp, dp = os.path.join(SCR, src), os.path.join(SCR, dst)
    if not os.path.isfile(sp):
        print('ABORT: 派生源不存在', src)
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
    want = txt.encode(enc)          # utf-8-sig 时含 BOM，与下面写盘的字节同一算法
    if os.path.exists(dp):
        # 目标已存在时：只有"逐字节就等于本代会产出的那份"才允许跳过（让整代派生可复跑，
        # 不必为了重跑而删文件）；任何差异一律 ABORT，不覆盖。
        if open(dp, 'rb').read() == want:
            print('SKIP_IDENTICAL', dst, len(want), 'B')
            continue
        print('ABORT: 目标已存在且与本代派生结果不等，不覆盖', dst)
        sys.exit(1)
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

# 派生完把"本代不再引用上一代解包根/上一代包名"这件事读一遍：上一代栽过的地方（把 zsynctest8 喂给差集器）
DESTS = [d for _, d, _, _ in JOBS]
PREV = ['r50final', 'zsynctest10', '第 8 代', 'r50_', 'R50']
for dst in DESTS:
    t = open(os.path.join(SCR, dst), encoding='utf-8-sig').read()
    left = [k for k in PREV if k in t]
    print('LEFTOVER_CHECK', dst, left if left else 'CLEAN')

# 语法体检一律用 ast.parse —— 不在归档目录里跑 py_compile（它会落 .pyc，与清单 md5 脱钩，见 FreqErr 本段"检查动作污染被检查物"）
for dst in DESTS:
    if dst.endswith('.py'):
        import ast
        ast.parse(open(os.path.join(SCR, dst), encoding='utf-8').read())
        print('AST_OK', dst)
