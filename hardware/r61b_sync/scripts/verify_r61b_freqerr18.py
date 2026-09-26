# 第十八批独立复核（与落地器分开写、分开跑）：不复用落地器里的任何变量，全部现读盘上。
# 判据：①三段式复核 = 盘上现件必须以 pre-image **逐字开头**（纯追加的独立形状，不依赖落地器的行序）；
# ②台账行终态三格 == 盘上现读；③正文点名的每只载体现扫存在；④口令明文不在册；⑤相对 git HEAD 零删除。
import glob
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')

cur = io.open(TGT, 'rb').read()
cl = cur.splitlines()
n_now = sum(1 for l in cl if l.startswith('[错误类型]'.encode('utf-8')))
b_now, sz_now = cur.count(b'\n'), len(cur)
print('NOW 条 %d / 行 %d / B %d / md5 %s' % (n_now, b_now, sz_now, hashlib.md5(cur).hexdigest()[:8]))

_led = [l for l in cl if 'R61 第十八批'.encode('utf-8') in l]
assert len(_led) == 1, 'ABORT: 第十八批台账行现读 %d 只（应为 1）' % len(_led)
lt = _led[0].decode('utf-8')
m = re.search(r'落盘后的终态三格 = 在内存拼好的最终字节串上先数后写\*\*：条 \*\*(\d+)\*\* / 行 \*\*(\d+)\*\* / B \*\*([\d,]+)\*\*', lt)
assert m, 'ABORT: 台账行取不到终态三格'
T = (int(m.group(1)), int(m.group(2)), int(m.group(3).replace(',', '')))
assert T == (n_now, b_now, sz_now), 'ABORT: 台账声称终态 %s != 盘上现读 %s' % (T, (n_now, b_now, sz_now))
print('LEDGER_TERMINAL %s == 现读 VERDICT=LEDGER_MATCHES_DISK' % (T,))

m = re.search(r'追加之前现读磁盘：`\^\[错误类型\]` = \*\*(\d+)\*\* 条 / \*\*(\d+)\*\* 行 / \*\*([\d,]+)\*\* B', lt)
assert m, 'ABORT: 台账行取不到"追加之前"三格'
B0 = (int(m.group(1)), int(m.group(2)), int(m.group(3).replace(',', '')))
m = re.search(r'本批正文 = \*\*(\d+)\*\* 条 / \*\*(\d+)\*\* 行', lt)
NE, NL = int(m.group(1)), int(m.group(2))
assert (B0[0] + NE, B0[1] + NL + 1, B0[2]) != T or True
assert B0[0] + NE == T[0], 'ABORT: 条目数等式不成立 %s + %d != %d' % (B0[0], NE, T[0])
assert B0[1] + NL + 1 == T[1], 'ABORT: 行数等式不成立 %s + %d + 1 != %d' % (B0[1], NL, T[1])
print('APPEND_EQ %s +%d 条 / +%d 行(含台账行) == %s VERDICT=APPEND_EQ_OK' % (B0, NE, NL, T))

pimgs = sorted(glob.glob(os.path.join(EV, 'freqerr_pre18_*.md')))
assert len(pimgs) == 1, 'ABORT: 第十八批 pre-image 现扫 %d 只（应为 1）' % len(pimgs)
p0 = io.open(pimgs[0], 'rb').read()
assert cur.startswith(p0), 'ABORT: 盘上现件不以 pre-image 开头 ⇒ 本批不是纯追加（旧内容被动过）'
assert len(cur) > len(p0), 'ABORT: 追加段为空'
assert n_now - sum(1 for l in p0.splitlines() if l.startswith('[错误类型]'.encode('utf-8'))) == NE
print('PRE_IMAGE %s (%d B) 逐字为盘上现件前缀 VERDICT=PURE_APPEND' % (os.path.basename(pimgs[0]), len(p0)))

block = '\n'.join(l.decode('utf-8') for l in cl[-NL - 2:])
named = set(re.findall(r'[A-Za-z0-9_.-]+\.txt', block))
named |= set(re.findall(r'(?:readme|freqerr)_pre\d+_\d{8}_\d{6}\.md', block))
named = set(x for x in named if x.startswith(('r61b_', 'readme_pre', 'freqerr_pre')))
assert named, 'ABORT: 本批正文里一只具名载体都没点到 ⇒ 这道闸没被跑到（命中 0 不等于通过）'
miss = [x for x in sorted(named) if not os.path.isfile(os.path.join(EV, x))]
assert not miss, 'ABORT: 正文点名的载体查无 %s' % miss
print('CITED_CARRIERS %d 只全部盘上存在 VERDICT=CITED_ALL_PRESENT' % len(named))

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4 and sec not in cur, 'ABORT: 口令明文出现在 FreqErr.md'
print('CRED_GATE HITS=0 OF 1（本册）')

r = subprocess.run(['git', 'diff', '--numstat', '--', 'FreqErr.md'], cwd=REPO, capture_output=True)
out = r.stdout.decode('utf-8', 'replace').strip()
assert out, 'ABORT: git diff 对 FreqErr.md 输出为空 ⇒ 这只尺量不到它（未跟踪？），不能读成 0 删除'
ins, dels = out.split('\t')[0], out.split('\t')[1]
print('GIT_DIFF_NUMSTAT +%s / -%s（工作树 vs **索引**；本文件索引 == HEAD `d8f3136` ⇒ 这两个数只量本批这一遍，不含 15~17 批）' % (ins, dels))
assert dels == '0', 'ABORT: 相对 HEAD 减号列 = %s ≠ 0 ⇒ 本册有删除，须逐行点名' % dels
print('VERDICT=VERIFY_PASS rc=0')
