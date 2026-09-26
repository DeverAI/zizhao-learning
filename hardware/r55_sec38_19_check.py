# §38.19 落盘终态的**独立复核器**（R55 尾巴批）。为什么要有它：落地器 `r55_land_sec38_19.py` 13:00:26 跑完，
# 它的读数**只打在 stdout**（那正是本批 FreqErr 第 2 条点名的形状："跑绿了却没留证据"），而它**不可重跑**
# （头部 `assert '### 38.19' not in old` 会拒绝覆写）⇒ 那句 `LANDED_SEC38_19` 至今没有载体。
# 补法不是在旧脚本里补一行写载体（旧脚本已经跑过了，加了也追不回来），是**另立一把尺、当场自落载体**：
# 它不复述落地器的自述，只把"盘上 §38.19 那一块"与**它引用的每一只载体**逐字对一遍。
# 位置：`hardware/`（归档目录之外，gen 24 已于 12:53:39 冻结 ⇒ 见 FreqErr 本批第 6 条）。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
DST = os.path.join(REPO, 'hardware', 'ht305_sync')
EV = os.path.join(DST, 'evidence')
HDIR = os.path.join(REPO, 'hardware')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')

_cands = ['r55_sec38_19_check.txt'] + ['r55_sec38_19_check_%d.txt' % i for i in range(2, 10)]
CARRIER = next((os.path.join(HDIR, c) for c in _cands if not os.path.exists(os.path.join(HDIR, c))), None)
assert CARRIER, 'ABORT: 载体名 9 只全被占，拒绝覆写'


def ev(name):
    p = os.path.join(EV, name)
    assert os.path.isfile(p), 'ABORT: 载体不存在 ' + name
    return open(p, encoding='utf-8').read()


def g(name, pat):
    m = re.search(pat, ev(name))
    assert m, 'ABORT: %s 里找不到 %r' % (name, pat)
    return m.group(1)


def money(x):
    return '{:,}'.format(int(x))


raw = open(DOC, 'rb').read()
lines = raw.decode('utf-8').split('\r\n')
idx = [i for i, l in enumerate(lines) if l.startswith('### 38.19')]
assert len(idx) == 1, 'ABORT: §38.19 命中 %d 处，不是唯一一节' % len(idx)
i0 = idx[0]
nxt = [i for i in range(i0 + 1, len(lines)) if re.match(r'^#{2,4} ', lines[i])]
i1 = nxt[0] if nxt else len(lines) - 1
sec = '\r\n'.join(lines[i0:i1])
n_bullets = len(re.findall(r'(?m)^- ', sec))
assert n_bullets == 9 and len(re.findall('本节没做', sec)) == 1, \
    'ABORT: 本节形状不符（要点 %d 行）' % n_bullets

CHECKS = []


def ck(needle, src_desc):
    """`needle` 由某只载体的**现读值**拼出来（不在这里硬编码任何数字），本器只问一句：正文里真的写着它吗。
    两问分家：拼 needle 的那一步负责"载体是多少"，这里的 `in sec` 负责"正文写没写"。"""
    CHECKS.append((needle, src_desc, needle in sec))


vc1 = os.path.join(HDIR, 'verify_manifest_0924123702.txt')
vc2 = os.path.join(HDIR, 'verify_manifest_0924125339.txt')
mlast = open(os.path.join(DST, 'MANIFEST.txt'), encoding='utf-8').read()
mt = {l.split('\t')[0]: l.split('\t')[1] for l in mlast.splitlines()
      if l.startswith(('TOTAL\t', 'TOTAL_BYTES\t', 'BOM_FILES\t'))}
rmrow = [l.split('\t') for l in mlast.splitlines() if l.startswith('README.md\t')][0]

ck('ROWS=%s' % g('r55_verify_manifest_gen22_stale.txt', r'ROWS=(\d+)'), 'evidence/r55_verify_manifest_gen22_stale.txt')
for gate in ('cred_gate_recheck_123653.txt', 'cred_gate_recheck_125333.txt'):
    ck('FILES_SCANNED=%s' % g(gate, r'FILES_SCANNED=(\d+)'), 'evidence/' + gate)
ck('TOTAL=%s' % g('manifest_gen_log.txt', r'\d\d:\d\d:\d\d\t(\d+)\t1355088'), 'evidence/manifest_gen_log.txt（gen 23）')
ck('TOTAL=%s' % mt['TOTAL'], 'MANIFEST.txt 末三行（gen 24）')
ck('TOTAL_BYTES=%s' % money(mt['TOTAL_BYTES']), 'MANIFEST.txt 末三行')
ck('BOM=%s' % mt['BOM_FILES'], 'MANIFEST.txt 末三行')
ck(money(os.path.getsize(vc1)) + ' B', 'hardware/' + os.path.basename(vc1))
ck(money(os.path.getsize(vc2)) + ' B', 'hardware/' + os.path.basename(vc2))
ck(g('r55_cred_recount_2.txt', r'CRED_RECOUNT_AT=(.+)'), 'evidence/r55_cred_recount_2.txt')
ck('TOTAL_HITS=%s' % g('r55_cred_recount_2.txt', r'TOTAL_HITS=(\d+)'), 'evidence/r55_cred_recount_2.txt')
ck('%s 只逐只点名' % g('r55_cred_recount_2.txt', r'= (\d+) 只，逐只点名'), 'evidence/r55_cred_recount_2.txt')
ck(g('r55_parse_check_2.txt', r'VERDICT=(\S+)'), 'evidence/r55_parse_check_2.txt')
ck('%s 只' % g('r55_parse_check_2.txt', r'工具 (\d+) 只'), 'evidence/r55_parse_check_2.txt')
ck(money(rmrow[1]) + ' B', 'MANIFEST.txt 里 README.md 那一行')
ck('md5 `%s' % rmrow[2][:8], 'MANIFEST.txt 里 README.md 那一行')
ck(g('r55_land_readme_2.txt', r'LAND_README2_AT=\S+ (\d\d:\d\d:\d\d)'), 'evidence/r55_land_readme_2.txt')
# 关系式 `TOTAL == 本遍门 FILES_SCANNED - 1`：gen 23/24 正文里写着这一式，gen 22 只写时刻 ⇒ 式子只问 23/24。
mlog = ev('manifest_gen_log.txt')
rel = [(g('cred_gate_recheck_123427.txt', r'FILES_SCANNED=(\d+)'), re.search(r'\d\d:\d\d:\d\d\t(\d+)\t1352267', mlog).group(1), None),
       (g('cred_gate_recheck_123653.txt', r'FILES_SCANNED=(\d+)'), re.search(r'\d\d:\d\d:\d\d\t(\d+)\t1355088', mlog).group(1), '381 − 1 = 380'),
       (g('cred_gate_recheck_125333.txt', r'FILES_SCANNED=(\d+)'), mt['TOTAL'], '387 − 1 = 386')]
for fs, n, in_sec in rel:
    assert int(fs) - 1 == int(n), 'ABORT: 关系式 %s - 1 == %s 不成立' % (fs, n)
    if in_sec:
        assert in_sec == '%s − 1 = %s' % (fs, n), 'ABORT: 正文里那一式（%s）与载体现算（%s - 1 = %s）不符' % (in_sec, fs, n)
        ck(in_sec, '两遍门输出 + 两代清单（式子两边都是现读）')

# rev-list 是现场态：正文写的是"现跑"，本复核器**自己再跑一次**，两者必须同值才放行。
rev = subprocess.run(['git', '-C', REPO, 'rev-list', '--count', 'origin/main..HEAD'],
                     capture_output=True, text=True).stdout.strip()
assert rev.isdigit() and len(rev) <= 3, 'ABORT: rev-list 读数异常 ' + repr(rev)
ck('= %s**（这是' % rev, 'git rev-list --count origin/main..HEAD（本器现跑）')

# 明文门：本节新增的这段字节里 PROV_PASS 必须 0 命中（只数不打印；阳性对照只在内存）。
sec_b = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read()).group(1)
assert sec_b and len(sec_b) >= 8, 'ABORT: 读不到 PROV_PASS 宏本体，这道自证不成立'
hits = sec.encode('utf-8').count(sec_b)
pos = ('// 阳性对照：'.encode('utf-8') + sec_b).count(sec_b)
assert pos == 1 and hits == 0, 'ABORT: 明文自检失败（本节命中 %d / 对照 %d）' % (hits, pos)
assert raw.count(b'\r\n') == raw.count(b'\n'), 'ABORT: 整只文件行尾混杂'

bad = [c for c in CHECKS if not c[2]]
out = ['SEC3819_CHECK_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
       'DOC=%s bytes=%d md5=%s wc_l=%d（纯 CRLF：%s）'
       % (os.path.basename(DOC), len(raw), hashlib.md5(raw).hexdigest(), raw.count(b'\n'),
          raw.count(b'\r\n') == raw.count(b'\n')),
       'SECTION_LINES=%d..%d（标题 1 + 要点 9 行，含"本节没做"1 行；下一节边界由正则现找）' % (i0 + 1, i1),
       'CHECKS=%d（下面逐条点名，不截断；每条同时问"正文写没写"与"载体是多少"）' % len(CHECKS)]
out += ['%s 正文=%r 现读自=%s' % ('OK  ' if c[2] else 'FAIL', c[0], c[1]) for c in CHECKS]
out += ['RELATION_TOTAL_EQ_GATE_MINUS_1=gen22/23/24 三遍逐一带入 assert 并全过（%s）'
        % ', '.join('%s-1=%s' % (f, n) for f, n, _ in rel),
        'REV_LIST_NOW=%s（正文那句"现跑"与本器现跑同值 ⇒ 现场态没有过期）' % rev,
        'PLAINTEXT_HITS_IN_SECTION=%d POSITIVE_CONTROL_IN_MEMORY=%d（PROV_PASS 只数不打印）' % (hits, pos),
        'NOTE=本节"跑绿了却没载体"这件事本身已由 FreqErr 本批第 2 条登记；本载体是**事后补的第二把尺**，不是旧落地器的重跑（它拒绝覆写、不可重跑）。',
        'VERDICT=' + ('SEC38_19_TRUE' if not bad else 'SEC38_19_STALE（%d 条对不上）' % len(bad))]
text = '\n'.join(out) + '\n'
open(CARRIER, 'w', encoding='utf-8', newline='').write(text)
print(text)
print('CARRIER=hardware/' + os.path.basename(CARRIER))
sys.exit(0 if not bad else 1)
