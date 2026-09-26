# R55 项目记忆索引那只 CR 的**盘上复核件**（只读；不复现"修前"，修前读数由 §38.18 ③④ 与 r55_land_A.txt 那格给出）。
# 为什么要有这只：修复动作当时是在命令行 heredoc 里做的（正是本批第 1 条错误类型的现场），修后需要一个**能独立重跑的判据**，
# 否则"我修好了"只剩一句叙述。判据全为字节级，且刻意**不用** ③ 里那三只瞎量具（grep/Edit/Read）当唯一依据。
import hashlib
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BS = chr(92)
CR = bytes([0x0D])
MEM = 'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/memory/'
IDX = MEM + 'MEMORY.md'
BODY = MEM + 'hardware-epaper397-power.md'
REPO_EVID = 'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync/evidence/refresh_docs_r54.txt'
PATH_STR = ('%TE' + 'MP%' + BS + 'refresh_docs_r54.txt').encode('utf-8')

ib = open(IDX, 'rb').read()
bb = open(BODY, 'rb').read()
eb = open(REPO_EVID, 'rb').read()
out = []
out.append('INDEX_LEN=%d INDEX_CR=%d INDEX_LF=%d INDEX_MD5=%s' % (
    len(ib), ib.count(CR), ib.count(b'\n'), hashlib.md5(ib).hexdigest()))
out.append('INDEX_PATH_HITS=%d INDEX_DUP_STOP=%d INDEX_ITEMS=%d' % (
    ib.count(PATH_STR), ib.count('。。'.encode('utf-8')),
    sum(1 for l in ib.decode('utf-8').split('\n') if l.startswith('- ['))))
out.append('BODY_LEN=%d BODY_CR=%d BODY_PATH_HITS=%d' % (len(bb), bb.count(CR), bb.count(PATH_STR)))
out.append('REPO_CARRIER_LEN=%d REPO_CARRIER_MD5=%s' % (len(eb), hashlib.md5(eb).hexdigest()))
verdict = []
verdict.append(('索引零 CR', ib.count(CR) == 0))
verdict.append(('索引纯 LF 行数 = 9', ib.count(b'\n') == 9))
verdict.append(('索引里那句路径逐字命中 1', ib.count(PATH_STR) == 1))
verdict.append(('索引无重复句号', ib.count('。。'.encode('utf-8')) == 0))
verdict.append(('正文那句路径逐字命中 1 且零 CR', bb.count(PATH_STR) == 1 and bb.count(CR) == 0))
verdict.append(('修后 LEN/md5 与 §38.18 ④ 登记逐字一致',
                len(ib) == 23785 and hashlib.md5(ib).hexdigest().startswith('ebba4023')))
for name, ok in verdict:
    out.append('CHECK %-42s %s' % (name, 'PASS' if ok else 'FAIL'))
allok = all(o for _, o in verdict)
out.append('VERDICT=' + ('MEMORY_INDEX_CLEAN' if allok else 'MEMORY_INDEX_DIRTY'))
txt = '\n'.join(out) + '\n'
print(txt, end='')
EVID = 'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync/evidence/chk_memory_c_r55.txt'
import os
assert not os.path.exists(EVID), '复核件已存在，不覆盖（要重跑请先按新时刻命名）'
open(EVID, 'w', encoding='utf-8', newline='\n').write(txt)
print('CARRIER', EVID, os.path.getsize(EVID))
raise SystemExit(0 if allok else 1)
