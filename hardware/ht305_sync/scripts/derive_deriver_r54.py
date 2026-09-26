# -*- coding: utf-8 -*-
"""第 12 代同步工具的派生器之派生：scripts/derive_r53.py -> scripts/derive_r54.py。
   做法 = **哨兵三段移位**（先把"新一代"标记换成哨兵，再把"上一代"换成新一代，最后把哨兵换成新新一代），
   因为直接按 r52->r53、r53->r54 顺序替换会让 JOBS 表的源名与目标名撞成同一只（src 变 r54、dst 也变 r54）。"""
import ast
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
SCR = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync/scripts'
SRC = os.path.join(SCR, 'derive_r53.py')
DST = os.path.join(SCR, 'derive_r54.py')
assert os.path.isfile(SRC), 'ABORT: 派生源不存在 ' + SRC
assert not os.path.exists(DST), 'refuse to overwrite ' + DST
txt = open(SRC, encoding='utf-8').read()
S = '\x00NEXT\x00'
PAIRS = [('r53', 'r52', 'r54'), ('第 11 代', '第 10 代', '第 12 代'),
         ('zsynctest13', 'zsynctest12', 'zsynctest14'), ('R53', 'R52', 'R54'),
         ('gen-11', 'gen-10', 'gen-12')]
counts = []
for new, old, nxt in PAIRS:
    a, b = txt.count(new), txt.count(old)
    assert a > 0 and b > 0, 'ABORT: 某一对在本代源里 0 命中 %s(%d) / %s(%d)' % (new, a, old, b)
    txt = txt.replace(new, S + new).replace(old, new).replace(S + new, nxt)
    counts.append('%s|%s->%s:%d/%d' % (old, new, nxt, b, a))
# 三段移位后：所有指代都恰好前进一代。这里逐条断言"上一代标识不得残留、下下一代不得出现"。
for bad in ('r52', 'R52', 'zsynctest12', '第 10 代', 'gen-10'):
    assert bad not in txt, 'ABORT: 仍残留上一代标识 ' + bad
for bad in ('r55', 'R55', 'zsynctest15', '第 13 代', 'gen-13'):
    assert bad not in txt, 'ABORT: 移过头了 ' + bad
assert S not in txt
PREV_REFS = ["PREV = ['r53final', 'zsynctest13', '第 11 代', 'r53_', 'R53']",
             "for src in ['r53_upload.ps1', 'land_r53_evidence.py']"]
for ref in PREV_REFS:
    assert txt.count(ref) == 1, 'ABORT: 上一代引用没落到位 ' + ref
jobs = [('sync_r53.py', 'sync_r54.py'), ('r53_upload.ps1', 'r54_upload.ps1'),
        ('chk_r53.ps1', 'chk_r54.ps1'), ('r53_cutoff_delta.py', 'r54_cutoff_delta.py'),
        ('r53_listdiff.py', 'r54_listdiff.py'), ('land_r53_evidence.py', 'land_r54_evidence.py'),
        ('r53_roundtrip.py', 'r54_roundtrip.py'), ('extra_land_r53.py', 'extra_land_r54.py')]
for src, dst in jobs:
    assert txt.count("'%s'" % src) >= 1 and txt.count("'%s'" % dst) == 1, 'ABORT: JOBS 撞名或缺项 %s/%s' % (src, dst)
assert 'zizhao_20260924_r54final' in txt and 'zizhao_20260924_r53final' in txt
ast.parse(txt)
open(DST, 'w', encoding='utf-8', newline='').write(txt)
print('DERIVED derive_r54.py %d B | %s' % (os.path.getsize(DST), ' '.join(counts)))
print('AST_OK LEFTOVER=r52:%d r53:%d r54:%d' % (txt.count('r52'), txt.count('r53'), txt.count('r54')))
