# FreqErr.md 第十五批**独立复核遍**（只读，不写目标文件）。
# 为什么需要它：落地器 `land_r61b_freqerr15.py` 在 `write(exp)` **之后**的证明段里 ABORT（rc=1）
# ⇒ 它自己那句"写完后还在盘上复量一次"没有跑到，盘上终态目前没有执行者复量。
# 本遍做的事：拿落地器留下的 pre-image 与盘上现状做**逐行**差集（不是字节偏移），并复算台账行自己声称的三格。
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
EB = '[错误类型]'.encode('utf-8')


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）' % (prefix, must, len(hits))
    return hits[0]


PIMG = one('freqerr_pre15_*.md')
pre = io.open(PIMG, 'rb').read()
cur = io.open(TGT, 'rb').read()
pl, cl = pre.splitlines(), cur.splitlines()

# ① 逐行差集：必须**恰好**一行被就地改（同一行号）、其余全是尾部追加、零删除
_changed = [(i, pl[i], cl[i]) for i in range(len(pl)) if pl[i] != cl[i]]
assert len(_changed) == 1, 'ABORT: 改前/改后逐行差集 = %d 行被改（应为 1）⇒ 订正不是就地单行改' % len(_changed)
_ci, _old, _new = _changed[0]
assert _old.startswith('**【'.encode('utf-8')) and 'R61 第十三批' in _old.decode('utf-8') \
    and _new.startswith(_old[:20]), 'ABORT: 被改那一行不是第十三批台账行的就地订正'
assert len(pl) + 31 == len(cl), 'ABORT: 追加行数 = %d（预期 31 = 本批 30 行正文 + 1 行台账）' % (len(cl) - len(pl))
assert cl[_ci + 1:len(pl)] == pl[_ci + 1:], 'ABORT: 订正行之后的原文行不等于改前'

# ② 台账行自己声称的三格必须与**现数**同值（改前两格量 pre-image，终态三格量盘上现状）
HDR = cl[-1].decode('utf-8')
assert 'R61 第十五批' in HDR, 'ABORT: 末行不是本批台账行'
_m = re.search(r'`\^\[错误类型\]` = \*\*(\d+)\*\* 条 / \*\*(\d+)\*\* 行 / \*\*([\d,]+)\*\* B', HDR)
assert _m, 'ABORT: 台账行取不到"追加之前"那三格'
b_e, b_l, b_b = int(_m.group(1)), int(_m.group(2)), int(_m.group(3).replace(',', ''))
assert (b_e, b_l, b_b) == (sum(1 for l in pl if l.startswith(EB)), len(pl), len(pre)), \
    'ABORT: 台账行"追加之前"三格 %s 与 pre-image 现数 %s 不同值' % (
        (b_e, b_l, b_b), (sum(1 for l in pl if l.startswith(EB)), len(pl), len(pre)))
_m2 = re.search(r'条 \*\*(\d+)\*\* / 行 \*\*(\d+)\*\* / B \*\*([\d,]+)\*\*', HDR)
assert _m2, 'ABORT: 台账行取不到"终态"三格'
f_e, f_l, f_b = int(_m2.group(1)), int(_m2.group(2)), int(_m2.group(3).replace(',', ''))
_now = (sum(1 for l in cl if l.startswith(EB)), len(cl), len(cur))
assert (f_e, f_l, f_b) == _now, 'ABORT: 台账行终态三格 %s 与盘上现数 %s 不同值' % ((f_e, f_l, f_b), _now)
assert f_e == b_e + 6 and f_l == b_l + 31, 'ABORT: 条目/行数增量与本批声称的 6 条 / 31 行不等'

# ③ 订正那一行的字节增量必须等于台账行声称的那格（"只加 241 B"这一类句式的前提）
_md = re.search(r'该行只加 \*\*(\d+)\*\* B.*?订正段长度 (\d+) B -> (\d+) B', HDR)
assert _md, 'ABORT: 台账行没有登记订正段的三格尺寸'
_dln, _dol, _dnl = int(_md.group(1)), int(_md.group(2)), int(_md.group(3))
assert (len(_new) - len(_old), _dol, _dnl) == (_dln, _dol, _dnl), \
    'ABORT: 订正行实测尺寸差 = %d B，台账声称 %d B' % (len(_new) - len(_old), _dln)

# ④ 占位符：大写式必须 0 只；宽口径只数不得比改前增加（历史里有 6 行代码片段带花括号）
UP, WIDE = re.compile(r'\{[A-Z][A-Z0-9_]*[:,]*\}'), re.compile(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}')
_txt = '\n'.join(l.decode('utf-8', 'replace') for l in cl)
_pre = '\n'.join(l.decode('utf-8', 'replace') for l in pl)
assert not UP.search(_txt), 'ABORT: 盘上仍有未插值的大写式占位符'
# 订正那一遍**恰好**拿掉三只哨兵（那一行现在没有花括号了），追加段一只都不许有
_newtext = b'\n'.join([_new] + cl[len(pl):])
assert not WIDE.search(_newtext.decode('utf-8')), 'ABORT: 订正行 + 追加段里扫到花括号 ⇒ 本遍写进了未插值文本'
_w_now, _w_pre = len(WIDE.findall(_txt)), len(WIDE.findall(_pre))
assert _w_now == _w_pre - 3, 'ABORT: 全册花括号从 %d 处变到 %d 处（预期恰好 −3 = 那三只哨兵）' % (_w_pre, _w_now)

# ⑤ 口令明文：本批新写的那 31 行（含订正行）逐行扫，命中即红
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
assert sec not in _newtext, 'ABORT: 本批新写文本含口令明文'
assert sec not in cur, 'ABORT: 全册含口令明文（那是另一回事，本遍只点名）'

print('PRE-IMAGE %s = %d B / md5 %s / %d 行 / %d 条' % (
    os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8], len(pl), b_e))
print('现读目标 = %d B / md5 %s / %d 行 / %d 条' % (len(cur), hashlib.md5(cur).hexdigest()[:8], _now[1], _now[0]))
print('逐行差集：就地改 1 行（第 %d 行）+ 尾部追加 %d 行，删除 0 行' % (_ci + 1, len(cl) - len(pl)))
print('台账三格复算：追加前 %s == pre-image 现数 / 终态 %s == 盘上现数' % ((b_e, b_l, b_b), _now))
print('订正行尺寸差 = %d B（台账声称 %d B）| 花括号 宽 %d -> %d，大写式 0' % (len(_new) - len(_old), _dln, _w_pre, _w_now))
print('本批新写 %d B 明文闸 HITS=0' % len(_newtext))
print('VERDICT=STILL_TRUE rc=0')
