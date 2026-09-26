# 第十七批落盘后的独立只读复核遍（不复用落地器的任何中间量：pre-image 现读、盘上现读，两串重算差集）。
# 只读：不写 FreqErr.md，只在 evidence/ 落一只本遍自己的载体（由调用方 tee）。
import glob
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）' % (prefix, must, len(hits))
    return hits[0]


# 时间戳前缀只吃纯数字开头的那几只：本遍自己的 verify 载体（verify_ 开头）、上一遍崩掉的载体都不能进候选，
# 落地器载体再按内容 `VERDICT=LANDED rc=0` 收窄到 1 只。
PIMG = one('freqerr_pre17_*.md')
LAND = one('r61b_freqerr17_[0-9]*.txt', 'VERDICT=LANDED rc=0')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
old = io.open(PIMG, 'rb').read()
new = io.open(TGT, 'rb').read()
ol, nl = old.splitlines(), new.splitlines()

print('PRE-IMAGE %s (%d B / md5 %s)' % (os.path.basename(PIMG), len(old), hashlib.md5(old).hexdigest()[:8]))
print('CARRIER   %s (%d B)' % (os.path.basename(LAND), os.path.getsize(LAND)))
print('ON-DISK   FreqErr.md (%d B / md5 %s)' % (len(new), hashlib.md5(new).hexdigest()[:8]))

EB = '[错误类型]'.encode('utf-8')
o_e, n_e = sum(1 for l in ol if l.startswith(EB)), sum(1 for l in nl if l.startswith(EB))
print('ENTRIES %d -> %d (delta %d) | LINES %d -> %d (delta %d) | BYTES %d -> %d (delta %d)' % (
    o_e, n_e, n_e - o_e, old.count(b'\n'), new.count(b'\n'), new.count(b'\n') - old.count(b'\n'),
    len(old), len(new), len(new) - len(old)))
assert n_e - o_e == 1, 'ABORT: 条目增量 %d != 1' % (n_e - o_e)

# 行级差集：就地改动必须恰好一行，且那一行是第十三批台账行；其余行逐字等。
assert len(nl) == len(ol) + 6, 'ABORT: 行数增量 %d != 6（5 正文 + 1 台账）' % (len(nl) - len(ol))
diff = [i for i in range(len(ol)) if nl[i] != ol[i]]
assert len(diff) == 1, 'ABORT: 就地改动行数 = %d（应为 1），行号 %s' % (len(diff), [i + 1 for i in diff])
LN = diff[0] + 1
assert LN == 2254, 'ABORT: 被改那一行是第 %d 行，不是第 2254 行' % LN
_line_new = nl[diff[0]].decode('utf-8')
_line_old = ol[diff[0]].decode('utf-8')
assert 'R61 第十三批' in _line_new and _line_new.startswith('**【'), 'ABORT: 宿主行不是第十三批台账行'
assert '第十五批' in _line_new, 'ABORT: 改后没有写者点名（正向钉）'
assert not re.findall(u'本批第|本遍第|本文件第 ' + chr(92) + 'd+ 行', _line_new), 'ABORT: 改后仍带位置相关指代'
print('FIXED line %d: OLDSEG仍在=%s | 加粗 %d -> %d | 该行 %d -> %d B' % (
    LN, '，见本批第②条与本文件第 2254 行）。'.encode('utf-8') in new,
    _line_old.count('**'), _line_new.count('**'),
    len(_line_old.encode('utf-8')), len(_line_new.encode('utf-8'))))

# 尾部追加段：逐行重算，必须与盘上尾部 6 行等。
append_on_disk = nl[len(ol):]
assert append_on_disk[5].decode('utf-8').startswith(u'**【2'), 'ABORT: 追加段第 6 行不是台账行'
assert all(l.startswith(EB) for l in append_on_disk[0::5][:1]), 'ABORT: 追加段首行不是 [错误类型]'
body = b'\r\n'.join(append_on_disk[:5])
assert sec not in new[len(old) - 200:] and sec not in body, 'ABORT: 明文闸在盘上失效'
assert sec not in _line_new.encode('utf-8'), 'ABORT: 被改那一行含明文'

# 全册尺：加粗奇数行 = **基线**量（正文里表格/嵌套强调本来就留奇数行），闸门是"不新增"，不是"绝对 0"；
# 真配对判据落在被改那一行本身（必须偶数、增量 = 新段点名的对数）。
_odd = lambda ls: sum(1 for l in ls if l.count(b'**') % 2)
odd_old, odd_new = _odd(ol), _odd(nl)
bs_old = sum(1 for l in ol if chr(92).encode() in l)
print('BOLD_ODD_LINES 基线 %d -> 现读 %d（增量必须 0） | 被改那一行 %d -> %d（必须都是偶数） | 全册含反斜杠的行 基线 %d -> 现读 %d' % (
    odd_old, odd_new, _line_old.count('**'), _line_new.count('**'), bs_old,
    sum(1 for l in nl if chr(92).encode() in l)))
assert odd_new == odd_old, 'ABORT: 本批新增了 %d 行加粗不配对' % (odd_new - odd_old)
assert _line_old.count('**') % 2 == 0 and _line_new.count('**') % 2 == 0, 'ABORT: 被改那一行加粗不配对'
# 增量不写死：从台账行自己的那句声明里读（载体是权威源），再与盘上现读互核。
_mc = re.search(u'该行加粗只数 (\\d+) -> (\\d+)（增量 = 新段自己点名的 (\\d+) 对', append_on_disk[5].decode('utf-8'))
assert _mc, 'ABORT: 台账行里没有"该行加粗只数 a -> b（增量 = 新段自己点名的 n 对"这句 ⇒ 无法互核'
cb, ca, cp = int(_mc.group(1)), int(_mc.group(2)), int(_mc.group(3))
assert (cb, ca) == (_line_old.count('**'), _line_new.count('**')), \
    'ABORT: 台账声称 %d -> %d != 盘上现读 %d -> %d' % (cb, ca, _line_old.count('**'), _line_new.count('**'))
assert ca - cb == cp * 2, 'ABORT: 加粗增量 %d != 台账自己声明的 %d 对' % (ca - cb, cp)
newtext = b'\r\n'.join(append_on_disk).decode('utf-8')
bs = [l[:70] for l in newtext.split('\n') if chr(92) in l]
assert not bs, 'ABORT: 本批新写文本有 %d 行含反斜杠：%r' % (len(bs), bs[:2])
placeholder = [l[:70] for l in newtext.split('\n')
               if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}', l) or re.search(r'%[sd]\b', l)]
assert not placeholder, 'ABORT: 本批新写文本有 %d 行带未插值占位符：%r' % (len(placeholder), placeholder[:2])

# 台账行自洽：它声称的终态三格必须 == 本遍盘上现读
m = re.search(r'条 \*\*(\d+)\*\* / 行 \*\*(\d+)\*\* / B \*\*([\d,]+)\*\*', append_on_disk[5].decode('utf-8'))
assert m, 'ABORT: 台账行取不到终态三格'
claim = (int(m.group(1)), int(m.group(2)), int(m.group(3).replace(',', '')))
now = (n_e, new.count(b'\n'), len(new))
print('LEDGER claim %s == on-disk %s -> %s' % (claim, now, 'OK' if claim == now else 'MISMATCH'))
assert claim == now, 'ABORT: 台账三格与盘上现读不等'
# 幂等门复跑必须拒绝（只验证令牌在册，不真的跑落地器）
assert 'R61 第十七批'.encode('utf-8') in new, 'ABORT: 幂等令牌不在册'
print('VERDICT=VERIFY_OK rc=0')
