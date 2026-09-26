"""R56 第二批第一步：把 R56 第一批落地遍漏掉的两只空行补回去（只加空行，不动任何一个非空行）。

背景：FreqErr.md 的 R56 第一批节标题、排查记录的 ### 38.22 标题上方都缺空行，
被 hardware/r55_paperwork3.py 的 blank_gap_lines 闸当场抓住（它报 [3678]）。
本脚本只做"插入空行"这一件事，并证明插入前后**非空行的多重集逐字不变**（= 没有改一个字）。
"""
import os
import sys
from collections import Counter
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREQ = os.path.join(REPO, 'FreqErr.md')
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')

TARGETS = [
    ('FreqErr.md', FREQ, '## ', 'R56 第一批'),
    ('排查记录', DOC, '### 38.22', None),
]

out = []
changed_any = False
for label, path, pfx, extra in TARGETS:
    raw = open(path, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'ABORT: %s 行尾不是纯 CRLF' % label
    txt = raw.decode('utf-8')
    lines = txt.split('\r\n')
    if extra:
        hits = [i for i, l in enumerate(lines) if l.startswith(pfx) and extra in l]
    else:
        hits = [i for i, l in enumerate(lines) if l.startswith(pfx)]
    assert len(hits) == 1, 'ABORT: %s 锚命中 %d 处（须 1）' % (label, len(hits))
    h = hits[0]
    before_ne = Counter(l for l in lines if l.strip())
    if lines[h - 1] == '':
        out.append('%s 标题在第 %d 行，上方已是空行 ⇒ 本只不动' % (label, h + 1))
        continue
    changed_any = True
    new = lines[:h] + [''] + lines[h:]
    assert Counter(l for l in new if l.strip()) == before_ne, 'ABORT: %s 插入空行改动了非空行内容' % label
    assert len(new) == len(lines) + 1, 'ABORT: %s 行数不是 +1' % label
    body = '\r\n'.join(new)
    open(path, 'w', encoding='utf-8', newline='').write(body)
    back = open(path, 'rb').read()
    assert back.count(b'\r\n') == back.count(b'\n'), 'ABORT: %s 回读行尾被写杂' % label
    bl = back.decode('utf-8').split('\r\n')
    nh = [i for i, l in enumerate(bl) if (l.startswith(pfx) and (not extra or extra in l))]
    assert len(nh) == 1 and bl[nh[0] - 1] == '' and bl[nh[0] - 2] != '', \
        'ABORT: %s 回读显示空行没落在唯一正确位置' % label
    assert Counter(l for l in bl if l.strip()) == before_ne, 'ABORT: %s 回读非空行多重集变了' % label
    out.append('%s 标题第 %d 行上方补入 1 只空行：改前上方那行 = %r（截 60）/ 改后行数 %d（原 %d）'
               % (label, h + 1, lines[h - 1][:60], len(bl) - 1, len(lines) - 1))

# 复跑抓这一条的那道闸，确认它现在绿
import subprocess
r = subprocess.run([sys.executable, os.path.join(REPO, 'hardware', 'r55_paperwork3.py')],
                   cwd=REPO, capture_output=True, text=True, encoding='utf-8', errors='replace')
tail = ((r.stdout or '') + (r.stderr or '')).strip().split('\n')[-3:]
print('MODE=%s' % ('REPAIRED' if changed_any else 'ALREADY-OK'))
for l in out:
    print('BLANK %s' % l)
print('GATE rc=%d tail=%s' % (r.returncode, ' | '.join(x[:150] for x in tail)))
print('NOW %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
