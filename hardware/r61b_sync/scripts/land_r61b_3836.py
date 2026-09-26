# 落地器（R61b 收口遍第五段）：把 §38.36 追加进 hardware/20260919_墨水屏点屏排查记录.md。
# 三条硬规矩继承自上一代落地器（land_r61b_38.py）：①幂等前置 ②全部裁决排在写盘之前
# ③数字不手抄（每个读数都从盘上载体或现跑命令取，取不到即 ABORT）。
# 本遍另加两条，都是第十八批刚登记过的：
#   ④**盘上证明用三段式**（纯追加 = 前缀逐字等 + 追加段逐行等），不再用逐位置差集；
#   ⑤**diff -rq 类判据必须先看目录在不在、stderr 空不空**，否则"0 行 differ"是假绿。
import ast
import datetime
import glob
import hashlib
import io
import os
import re
import subprocess
import sys
import time

_START = time.time()
_ST = datetime.datetime.fromtimestamp(_START).strftime('%H:%M:%S')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
SIB = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'backups')
BK = os.path.join(REPO, 'backups')
READM = os.path.join(BK, 'README.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
DOCS = os.path.join(BK, 'r43_20260922_131029', 'docs')
NOTE = os.path.join(DOCS, 'SNAPSHOT_NOTE.txt')
SRC = os.path.join(MAIN, 'provision_ap.c')
ESPLOG = r'C:/esp'
H36 = '### 38.36 '
H35 = '### 38.35 '
ROUND_FROM = '141401'


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr.decode('utf-8', 'replace')[:200])
    return r.stdout.decode('utf-8', 'replace')


def txt(p):
    return io.open(p, encoding='utf-8').read()


def g(p, pat, cast=None):
    m = re.search(pat, txt(p))
    assert m, 'ABORT: 载体 %s 里取不到 %r' % (os.path.basename(p), pat)
    return cast(m.group(1)) if cast else m.group(1)


def dqr(a, b):
    for p in (a, b):
        assert os.path.isdir(p), 'ABORT: diff 的输入目录不存在，不能把它的失败读成 0 行 differ：' + p
    r = subprocess.run(['diff', '-rq', a, b], capture_output=True, shell=False)
    err = r.stderr.decode('utf-8', 'replace').strip()
    assert not err, 'ABORT: diff 自身报错（rc=%d）：%s' % (r.returncode, err[:200])
    return len([l for l in r.stdout.decode('utf-8', 'replace').splitlines() if l.strip()])


pre = io.open(TGT, 'rb').read()
H36B = H36.encode('utf-8')
STALE_B = STALE_LINES = STALE_CUR_B = STALE_CUR_LINES = 0
STALE_NAME = None
if H36B in pre:
    # 幂等门的**权威判据是载体里有没有写盘后令牌 `LANDED`**，不是"正文里有没有本节"：
    # 上一遍崩在写盘之后的行数断言上（缺陷 (o)），盘上确实留着它写的那一版本节，而那一遍没有 LANDED。
    _landed = [os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_3836_*.txt'))
               if 'VERDICT=LANDED' in txt(p)]
    assert not _landed, 'ABORT: §38.36 已有一遍打出 LANDED（%s）⇒ 真幂等门，本遍不叠加' % _landed
    assert pre.count(H36B) == 1, 'ABORT: 标题现读 %d 处 ⇒ 不是"一遍追加"的形态，本遍不敢核销' % pre.count(H36B)
    _cut = pre.index(H36B)
    _cand = pre[:_cut]
    _pimgs = sorted(glob.glob(os.path.join(EV, 'record_pre3836_*.md')))
    assert _pimgs, 'ABORT: 盘上已有本节却一只 pre-image 都扫不到 ⇒ 无法证明"去掉尾节 = 回到崩前那一瞬"'
    for _p in _pimgs:
        assert io.open(_p, 'rb').read() == _cand, \
            'ABORT: pre-image %s 与"去掉尾节的现件"不等 ⇒ 头段不干净，本遍不动盘' % os.path.basename(_p)
    _cur_b, _cur_l = len(pre), len(pre.splitlines())
    STALE_B, STALE_LINES = len(pre) - _cut, len(pre[_cut:].splitlines())
    _tt0 = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    _simg = os.path.join(EV, 'record_stale3836_%s.md' % _tt0)
    assert not os.path.exists(_simg), 'ABORT: 旧版本节归档目标已存在 ' + _simg
    io.open(_simg, 'wb').write(pre)
    assert io.open(_simg, 'rb').read() == pre, 'ABORT: 旧版本节归档回读不等'
    STALE_NAME = os.path.basename(_simg)
    STALE_CUR_B, STALE_CUR_LINES = _cur_b, _cur_l
    print('STALE-TAIL 核销：现件 %d B / %d 行，其中尾节 %d B / %d 行 先整体归档进 %s，'
          '头段与 %d 只 pre-image 逐字节相等后回落到头段' % (
              _cur_b, _cur_l, STALE_B, STALE_LINES, STALE_NAME, len(_pimgs)))
    pre = _cand
pl = pre.splitlines()
assert pre.endswith(b'\r\n'), 'ABORT: 末行不以 CRLF 收尾'
bare_lf = pre.count(b'\n') - pre.count(b'\r')
assert bare_lf == 0, 'ABORT: 现读裸 LF 行数 = %d ≠ 0 ⇒ 追加体行尾要按现读口径重选' % bare_lf
lines_before, bytes_before = pre.count(b'\n'), len(pre)
_h35 = [l for l in pl if l.startswith(H35.encode('utf-8'))]
assert len(_h35) == 1, 'ABORT: §38.35 的标题行现读 %d 只（应为 1）⇒ 本节"落在它之后"没有出处' % len(_h35)
H35_AT = re.search(r'现跑于 ([0-9: -]{19})', _h35[0].decode('utf-8')).group(1)
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', txt(SRC)).group(1).encode()
assert len(sec) >= 4

# ---------- 载体：先确认在，再取数 ----------
F15 = os.path.join(EV, 'r61b_freqerr15_141401.txt')
CAR = ['r61b_freqerr17_144314.txt', 'r61b_freqerr17_verify_144521.txt',
       'r61b_stage_list_144941.txt', 'r61b_stage_list_final_145334.txt',
       'staged_cred_gate_r61b_index98.txt', 'staged_cred_gate_r61b_index98_pos.txt',
       'staged_cred_gate_r61b_final105.txt', 'staged_cred_gate_r61b_final105_pos.txt',
       'staged_cred_gate_r61b_final106.txt', 'staged_cred_gate_r61b_final106_pos.txt',
       'readme_pre12_20260926_150515.md', 'r61b_readme12_proof_151116.txt',
       'r61b_readme12_proof_151152.txt', 'r61b_readme12_carrier_fix_151258.txt',
       'r61b_freqerr18_152413.txt', 'r61b_freqerr18_verify_152543.txt',
       'freqerr_pre18_20260926_152413.md', 'freqerr_pre17_20260926_144314.md']
for p in [F15] + [os.path.join(EV, x) for x in CAR]:
    assert os.path.isfile(p), 'ABORT: 本节要引的载体不存在 ' + p
CRASH18 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_freqerr18_*.txt'))
                 if '152413' not in p and 'verify' not in p)
# (g) 那句"全崩在写盘之前"必须有执行者：逐只现读，不含写盘后令牌 `LANDED`，并且**确实留下错误证据**。
# 错误证据有两种形态：`Traceback`（跑起来才崩）与 `SyntaxError`（模块根本没跑起来 ⇒ 更强的"没动盘"）。
# 本遍首版只认前者，被 15:21 那只 SyntaxError 载体当场假红 —— 判据写窄与写宽同样是缺陷。
for _c in CRASH18:
    _t = txt(os.path.join(EV, _c))
    assert 'LANDED' not in _t, 'ABORT: 第十八批崩遍载体 %s 含 LANDED ⇒ 它不是崩在写盘前' % _c
    assert 'Traceback' in _t or 'Error' in _t, 'ABORT: 第十八批崩遍载体 %s 里两种错误证据都没有' % _c
    _pm = re.search(r'PRE-IMAGE (\S+\.md)', _t)
    if _pm:
        _pp = os.path.join(EV, _pm.group(1))
        assert io.open(_pp, 'rb').read() == io.open(FREQ, 'rb').read(), \
            'ABORT: 第十八批崩遍 %s 的 pre-image 与 FreqErr 现件不等 ⇒ 归因要重写' % _c
assert CRASH18, 'ABORT: 第十八批崩遍名单现扫 0 只 ⇒ (g) 那句话没有对象'
# 取证名单按 **mtime** 圈（不靠文件名里的 6 位时刻：同名后缀跨天会混进上一日的载体）
_T_FROM = datetime.datetime.strptime(datetime.date.today().strftime('%Y-%m-%d ') + ROUND_FROM,
                                      '%Y-%m-%d %H%M%S').timestamp()
EV_TAIL = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, '*'))
                 if os.path.isfile(p) and os.path.getmtime(p) >= _T_FROM
                 and os.path.getmtime(p) < _START - 2)
n_ev_tail = len(EV_TAIL)
assert EV_TAIL, 'ABORT: 本轮取证名单现扫 0 只 ⇒ 这个计数尺本身在漏，不能作为读数'

GATE = os.path.join(EV, 'staged_cred_gate_r61b_final106.txt')
POS = os.path.join(EV, 'staged_cred_gate_r61b_final106_pos.txt')
gs_files = int(g(GATE, r'(?m)^FILES_SCANNED=(\d+)$'))
gs_hits = int(g(GATE, r'(?m)^TOTAL_HITS=(\d+)$'))
gs_verdict = g(GATE, r'(?m)^VERDICT=(\w+)$')
ps_del = int(g(POS, r'(?m)^INDEX_DELETED=(\d+)'))
ps_scan = int(g(POS, r'(?m)^INDEX_SCANNED=(\d+)'))
ps_arms_m = re.search(r'(?m)^ARMS_FIRED=(\d+/\d+)', txt(POS))
assert ps_arms_m, 'ABORT: 阳性对照载体取不到 ARMS_FIRED 的 n/n 两段'
ps_arms = ps_arms_m.group(1)
ps_del_names = sorted(re.search(r'INDEX_DELETED=\d+ \[([^\]]*)\]', txt(POS)).group(1).replace("'", '').split(', '))
ps_eq = g(POS, r'(?m)^CROSS_CHECK.*equal=(\w+)$')
ps_verdict = g(POS, r'(?m)^VERDICT=(\w+)$')
assert (gs_hits, gs_verdict, ps_eq, ps_arms, ps_verdict) == (0, 'CLEAN', 'True', '2/2',
                                                             'POSITIVE_CONTROL_FIRES_AND_INDEX_CLEAN')
assert gs_files == ps_del + ps_scan, 'ABORT: 门扫 %d 只 != 删除 %d + blob %d' % (gs_files, ps_del, ps_scan)

head = git('rev-parse', '--short', 'HEAD').strip()
revlist = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
num = git('diff', '--numstat', 'c7de970', head).strip().split('\n')
n_files = len(num)
n_bin = len([l for l in num if l.split('\t')[0] == '-'])
n_txt = n_files - n_bin
plus = sum(int(l.split('\t')[0]) for l in num if l.split('\t')[0] != '-')
minus = sum(int(l.split('\t')[1]) for l in num if l.split('\t')[1] != '-')
deleted = sorted(os.path.basename(l.split('\t')[2]) for l in num if l.split('\t')[0] == '-')
assert (n_files, n_bin, n_txt) == (gs_files, ps_del, ps_scan), 'ABORT: 提交只数 %d/%d/%d != 门 %d = 删除 %d + blob %d' % (
    n_files, n_bin, n_txt, gs_files, ps_del, ps_scan)
assert plus > 0 and minus >= 0, 'ABORT: numstat 行数读数异常 +%d/-%d' % (plus, minus)
assert deleted == ps_del_names, 'ABORT: numstat 的二进制名单 %s != 阳性对照 INDEX_DELETED %s' % (deleted, ps_del_names)
assert all(x.endswith('.bin') for x in deleted), 'ABORT: 二进制那两只不按名对上'
st = [l for l in git('status', '--porcelain').split('\n') if l.strip()]
st_lines = len(st)
st_kind = {}
for l in st:
    st_kind[l[:2]] = st_kind.get(l[:2], 0) + 1
st_dirs = len([l for l in st if l[:2] == '??' and l[3:].rstrip(chr(34)).endswith('/')])
assert st_dirs > 0, 'ABORT: porcelain 里 0 行是目录折叠 ⇒ "行数 != 只数"这句话本遍没有样本'

# ---------- §38.33 那条在册裁决的执行者：两只原厂镜像现算尺寸+md5，与那一节自己登记的字节互核 ----------
_i33 = next(k for k, l in enumerate(pl) if l.startswith('### 38.33 '.encode('utf-8')))
_i34 = next(k for k, l in enumerate(pl) if l.startswith('### 38.34 '.encode('utf-8')))
assert _i34 > _i33, 'ABORT: §38.33/§38.34 两节顺序不对，取不到那一节的区间'
S33 = '\n'.join(l.decode('utf-8') for l in pl[_i33:_i34])
sz_rec = dict((n, int(s.replace(',', ''))) for n, s in re.findall(r'`(esp32s3_[A-Za-z0-9_.]+)` = ([\d,]+) B', S33))
md_rec = re.findall(r'现算 md5 `([0-9a-f]{32})` / `([0-9a-f]{32})`', S33)
assert len(sz_rec) == 2 and len(md_rec) == 1, 'ABORT: §38.33 里尺寸格 %d 只 / md5 格 %d 处 ⇒ 无法作为互核对象' % (
    len(sz_rec), len(md_rec))
md_set = sorted(md_rec[0])
bin_probe = []
for n in deleted:
    p = os.path.join(REPO, n)
    assert os.path.isfile(p) and not os.access(p, os.W_OK), 'ABORT: 原厂镜像 %s 不在盘上或已可写（在册是只读）' % n
    bin_probe.append((n, os.path.getsize(p), hashlib.md5(io.open(p, 'rb').read()).hexdigest()))
assert [x[1] for x in bin_probe] == [sz_rec[x[0]] for x in bin_probe], 'ABORT: 两只原厂镜像现算尺寸 != §38.33 登记值 %s' % sz_rec
assert sorted(x[2] for x in bin_probe) == md_set, 'ABORT: 两只原厂镜像现算 md5 != §38.33 登记值 ⇒ "只读、一字节未改"这句要重判'

FE = io.open(FREQ, 'rb').read()
fe_l = FE.splitlines()
fe_n = sum(1 for l in fe_l if l.startswith('[错误类型]'.encode('utf-8')))
fe_lines, fe_bytes = FE.count(b'\n'), len(FE)
fe_md5 = hashlib.md5(FE).hexdigest()[:8]
assert fe_n == int(g(os.path.join(EV, 'r61b_freqerr18_152413.txt'), r'ENTRIES \d+ -> (\d+)'))
_l17t = [l for l in fe_l if 'R61 第十七批'.encode('utf-8') in l]
_l18t = [l for l in fe_l if 'R61 第十八批'.encode('utf-8') in l]
assert len(_l17t) == 1 and len(_l18t) == 1, 'ABORT: 第十七/十八批台账行现读不是各 1 只'

RB = io.open(READM, 'rb').read()
rb_lines, rb_bytes = RB.count(b'\n'), len(RB)
rb_md5 = hashlib.md5(RB).hexdigest()[:8]

# ---------- 第十二格 ②③④⑤ 与第十一次格同一批编号、再对本遍现跑：三向全等才是"同值"的执行者 ----------
_rb = RB.decode('utf-8').split('\n')
# 只认**标题行**（以 `【09-26 ` 开头）：正文里也会引用"（第十一次读数）"这种短语，不锚标题就会 2 处命中
_head = lambda l, s: l.startswith('【09-26') and s in l
rb12 = len([l for l in _rb if _head(l, '第十二次读数')])
assert rb12 == 1, 'ABORT: README 第十二格标题现读 %d 处' % rb12
_i12 = [k for k, l in enumerate(_rb) if _head(l, '第十二次读数')]
_i11 = [k for k, l in enumerate(_rb) if _head(l, '第十一次读数')]
assert len(_i12) == 1 and len(_i11) == 1, 'ABORT: README 第十一/十二格标题现读 %d/%d 处' % (len(_i11), len(_i12))
assert _i11[0] < _i12[0], 'ABORT: README 里第十一次格排在第十二格之后 ⇒ 两格谁是"在册"无法判'
CELL = _rb[_i12[0]:_i12[0] + 15]
# 第十一次格的块**不得越过**第十二格标题，否则两格同号编号（②③④⑤）会互相串台
CELL11 = _rb[_i11[0]:min(_i11[0] + 15, _i12[0])]


def cell(block, tag, pat, n):
    for l in block:
        if l.startswith(tag):
            m = re.search(pat, l)
            assert m, 'ABORT: 那一格取不到 %s 的 %r' % (tag, pat)
            assert len(m.groups()) == n, 'ABORT: %s 捕获组数 %d != %d' % (tag, len(m.groups()), n)
            return tuple(int(x.replace(',', '')) for x in m.groups())
    raise SystemExit('ABORT: 格子里没有 %s 这一行' % tag)


C43 = cell(CELL, '②', r'根 A / 根 B = \*\*(\d+) / (\d+) 行\*\*', 2)
C53 = cell(CELL, '③', r'同一命令 = \*\*(\d+) / (\d+) 行\*\*', 2)
CWT = cell(CELL, '④', r'体量\*\*：\*\*(\d+) 只 / ([\d,]+) B\*\*', 2)
CSR = cell(CELL, '⑤', r'仍 \*\*(\d+) 行 differ\*\*', 1)
CRC = cell(CELL, '⑥', r'A=(\d+) 只 / B=(\d+) 只.*= \*\*(\d+) / (\d+) 行\*\*', 4)
D43 = cell(CELL11, '②', r'根 A / 根 B = \*\*(\d+) / (\d+) 行\*\*', 2)
D53 = cell(CELL11, '③', r'同一命令 = \*\*(\d+) / (\d+) 行\*\*', 2)
DWT = cell(CELL11, '④', r'体量\*\*：\*\*(\d+) 只 / ([\d,]+) B\*\*', 2)
DSR = cell(CELL11, '⑤', r'仍非 0（\*\*(\d+) 行\*\*', 1)

# ---------- 板上 == 待烧：从 1.54 板档案现读在册三字段，再对构建目录那只现算互核（本遍没重建的执行者） ----------
BOARDS = os.path.join(REPO, 'hardware', 'BOARD_S3_ePaper_1_54.md')
bm = re.search(r'构建目录 `[^`]*`：\*\*([\d,]+) B\*\*，md5 `([0-9a-f]{32})`，`bin\[176:184\]` = `([0-9a-f]{16})`',
               txt(BOARDS))
assert bm, 'ABORT: 1.54 板档案里取不到构建目录那格的三个字段'
rec_size, rec_md5, rec_elf16 = int(bm.group(1).replace(',', '')), bm.group(2), bm.group(3)
BB = os.path.join(ESPLOG, 'zproj', 'build', 'zizhao_esp32s3.bin')
bbuf = io.open(BB, 'rb').read()
bb_md5, bb_elf16 = hashlib.md5(bbuf).hexdigest(), bbuf[176:184].hex()
bb_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(BB))
assert (len(bbuf), bb_md5, bb_elf16) == (rec_size, rec_md5, rec_elf16), 'ABORT: 构建目录那只与在册三字段不等（%d/%s/%s vs %d/%s/%s）' % (
    len(bbuf), bb_md5[:8], bb_elf16, rec_size, rec_md5[:8], rec_elf16)
assert os.path.getmtime(BB) < _T_FROM, 'ABORT: 构建目录那只 mtime %s 晚于本轮起点 %s ⇒ "本遍没重建"不成立' % (
    bb_mtime.strftime('%H:%M:%S'), ROUND_FROM)

note_t = txt(NOTE)
snap_at = g(NOTE, r'刷新时刻 ([0-9: -]{19})')
# NOTE 自己声称「"现读 N 只源"这句真的在 NOTE 里」——本遍给这句话装执行者：两处只数各自现读并互核
src_n = int(g(NOTE, r'现读 (\d+) 只源'))
src_n_run = int(g(NOTE, r'源清单现读 (\d+) 只'))
src_n_gate = int(g(NOTE, r'(\d+) 只源全扫'))
assert src_n == src_n_run == src_n_gate, 'ABORT: NOTE 三处只数互不相等（%d / %d / %d）' % (src_n, src_n_run, src_n_gate)
tbl_rows = len([l for l in note_t.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
new_rows = len([l for l in note_t.split('\n') if re.search(r'\tNEW -> \d', l)])
docs_files = len([f for f in os.listdir(DOCS) if os.path.isfile(os.path.join(DOCS, f))])
assert (docs_files, tbl_rows, src_n) == (src_n + 1, src_n, src_n), 'ABORT: docs 快照三格不自洽（目录 %d / 表 %d / 源 %d）' % (
    docs_files, tbl_rows, src_n)
assert 'HITS=0' in note_t, 'ABORT: NOTE 里没有 HITS=0 那格'
_fr = [l for l in note_t.split('\n') if l.startswith('FreqErr.md\t')]
assert len(_fr) == 1, 'ABORT: NOTE 里 FreqErr.md 那一行现读 %d 只' % len(_fr)
freq_docs = int(_fr[0].split('\t')[1])
_p18s = glob.glob(os.path.join(EV, 'freqerr_pre18_*.md'))
assert len(_p18s) == 1, 'ABORT: 第十八批 pre-image 现扫 %d 只（应为 1）' % len(_p18s)
fe18_key = re.search(r'freqerr_pre18_(\d{8}_\d{6})\.md', os.path.basename(_p18s[0])).group(1)
fe18_at = datetime.datetime.strptime(fe18_key, '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
snap_key = snap_at.replace('-', '').replace(':', '').replace(' ', '_')
assert H35_AT.replace('-', '').replace(':', '').replace(' ', '_') < snap_key, 'ABORT: §38.35 现跑于 %s 并不早于快照刷新 %s' % (
    H35_AT, snap_at)
assert snap_key < fe18_key, 'ABORT: 快照刷新时刻 %s 并不早于第十八批落地 %s ⇒ "快照不含第十八批"这句不成立' % (
    snap_at, fe18_at)
assert freq_docs < fe_bytes, 'ABORT: 快照里那只 FreqErr 是 %d B >= 盘上现读 %d B ⇒ "快照早于第十八批"这句不成立' % (
    freq_docs, fe_bytes)

wt_n = len([f for f in os.listdir(MAIN) if os.path.isfile(os.path.join(MAIN, f))])
wt_b = sum(os.path.getsize(os.path.join(MAIN, f)) for f in os.listdir(MAIN) if os.path.isfile(os.path.join(MAIN, f)))
d_r43a, d_r43b = dqr(os.path.join(BK, 'r43_20260922_131029', 'main'), MAIN), dqr(os.path.join(SIB, 'r43_20260922_131029', 'main'), MAIN)
d_r53a, d_r53b = dqr(os.path.join(BK, 'r53_20260924_083929', 'main'), MAIN), dqr(os.path.join(SIB, 'r53_20260924_083929', 'main'), MAIN)
d_src = dqr(os.path.join(BK, 'r44_sourceonly_20260923_084628', 'main'), MAIN)
RC = 'r61close_20260926_133908'
rc_a, rc_b = os.path.join(BK, RC), os.path.join(SIB, RC)
rc_ca = [f for f in os.listdir(rc_a) if os.path.isfile(os.path.join(rc_a, f))]
rc_cb = [f for f in os.listdir(rc_b) if os.path.isfile(os.path.join(rc_b, f))]
rc_files = sum(len([f for f in os.listdir(os.path.join(rc_a, d)) if os.path.isfile(os.path.join(rc_a, d, f))])
               if os.path.isdir(os.path.join(rc_a, d)) else 1 for d in os.listdir(rc_a))
rc_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(rc_a) for f in fs)
d_rca, d_rcb = dqr(os.path.join(rc_a, 'main'), MAIN), dqr(os.path.join(rc_b, 'main'), MAIN)
assert sorted(rc_ca) == sorted(rc_cb), 'ABORT: 新根 A/B 顶层名单不同'
assert (d_rca, d_rcb) == (0, 0), 'ABORT: 新根与工作树不再逐字等（%d / %d 行）' % (d_rca, d_rcb)
# 五格在册读数 == 本遍现跑（"与第十一次同值"这句话的执行者；不等即 ABORT，不就地改数）
assert (d_r43a, d_r43b) == C43 == D43, 'ABORT: r43 两根三向不等：现跑 %d/%d / 第十二格 %s / 第十一次格 %s' % (d_r43a, d_r43b, C43, D43)
assert (d_r53a, d_r53b) == C53 == D53, 'ABORT: r53 两根三向不等：现跑 %d/%d / 第十二格 %s / 第十一次格 %s' % (d_r53a, d_r53b, C53, D53)
assert (wt_n, wt_b) == CWT == DWT, 'ABORT: 工作树 main/ 三向不等：现跑 %d 只/%d B / 第十二格 %s / 第十一次格 %s' % (
    wt_n, wt_b, CWT, DWT)
assert d_src == CSR[0] == DSR[0], 'ABORT: sourceonly 尺三向不等：现跑 %d / 第十二格 %s / 第十一次格 %s' % (d_src, CSR, DSR)
assert (rc_files, rc_files, d_rca, d_rcb) == CRC, 'ABORT: 新根现跑 %d 只 + diff %d/%d != 第十二格 ⑥ 在册 %s' % (
    rc_files, d_rca, d_rcb, CRC)

r = subprocess.run([sys.executable, '-m', 'serial.tools.list_ports'], capture_output=True)
assert r.returncode == 0
coms = sorted(set(re.findall(r'COM\d+', r.stdout.decode('utf-8', 'replace'))))
assert coms, 'ABORT: 串口枚举解析出 0 只 COM 名 ⇒ "COM14 缺席"不能由空读数得出'
com14 = 'COM14' in coms

h3 = os.path.join(REPO, 'hardware', 'ht305_sync')
h3_all = [os.path.join(r, f) for r, _, fs in os.walk(h3) for f in fs]
h3_py = [p for p in h3_all if '__pycache__' in os.path.relpath(p, h3).split(os.sep)]
h3_files = len(h3_all) - len(h3_py)
assert h3_files == 388, 'ABORT: `hardware/ht305_sync/` 递归现读 %d 只（在册 388）⇒ "gen 24 之后一字节未落"不成立，本节读数要换代' % h3_files
h3_latest = max((os.path.getmtime(p) for p in h3_all if p not in h3_py), default=0)
# 在册末版那只在正文里必须带**仓库相对路径**：只给裸名（`MANIFEST.txt`）就落进本遍自己的"假指针"族——
# 全仓同名件可能不止一只，而且下面的 `_named` 存在性闸按仓库根解析，裸名一律判查无此物。
_h3_last_pair = max(((os.path.getmtime(p), p) for p in h3_all if p not in h3_py))
h3_latest_name = os.path.relpath(_h3_last_pair[1], REPO).replace(os.sep, '/')
assert os.path.isfile(os.path.join(REPO, h3_latest_name)), 'ABORT: 在册末版指针落不到盘：' + h3_latest_name
log_files = sorted(glob.glob(os.path.join(ESPLOG, '*.log')))
log_dirty = [os.path.basename(p) for p in log_files if sec in io.open(p, 'rb').read()]
assert log_files, 'ABORT: C 盘 esp 顶层一只日志都扫不到 ⇒ "17 / 137"那类读数没有来源'
assert len(log_dirty) == 17, 'ABORT: 含明文的串口原始日志现读 %d 只（在册口径 17）⇒ 现场态要换代' % len(log_dirty)

# 两批各几条**不手抄**：从各批权威载体的 `ENTRIES a -> b (本批 +N)` 一行现读，并用 a/b 差复算 N
def batch_entries(carrier):
    m = re.search(r'ENTRIES (\d+) -> (\d+) \(本批 \+(\d+)\)', txt(carrier))
    assert m, 'ABORT: 载体 %s 里取不到 ENTRIES a -> b (本批 +N) 这一格' % os.path.basename(carrier)
    a, b, n = (int(x) for x in m.groups())
    assert b - a == n, 'ABORT: 载体 %s 的 ENTRIES %d->%d 与"本批 +%d"不自洽' % (os.path.basename(carrier), a, b, n)
    return a, b, n

A17, B17, n17 = batch_entries(os.path.join(EV, 'r61b_freqerr17_144314.txt'))
A18, B18, n18 = batch_entries(os.path.join(EV, 'r61b_freqerr18_152413.txt'))
assert B17 == A18, 'ABORT: 第十七批终值 %d != 第十八批起值 %d ⇒ 两批之间还叠过别的批次，本节叙述要重写' % (B17, A18)
VER18 = os.path.join(EV, 'r61b_freqerr18_verify_152543.txt')
cited18 = int(g(VER18, r'CITED_CARRIERS (\d+) 只全部盘上存在'))
ns_plus18 = int(g(VER18, r'GIT_DIFF_NUMSTAT \+(\d+) / -0'))
assert int(g(VER18, r'GIT_DIFF_NUMSTAT \+\d+ / -(\d+)')) == 0, 'ABORT: 第十八批复核载体里减号列不是 0'
p17 = glob.glob(os.path.join(EV, 'freqerr_pre17_*.md'))
assert len(p17) == 1 == len(_p18s), 'ABORT: 十七/十八批 pre-image 现扫不是各 1 只'

# 本遍自己 rc=1 的那几遍：候选判据 = mtime 早于本遍进入 且 非空，逐只再钉"含错误证据 + 不含 LANDED"。
# 其中崩在写盘**之后**的那一遍（缺陷 (o)）没有把目标改到别处去：它的尾节已在文件开头那道核销闸里整只归档、
# 头段与全部 pre-image 逐字节对账过，所以这里"pre-image == 本遍头段"那条等式对它仍然成立。
# 并要求每只候选**真的含 Traceback** —— 否则"这一遍崩过"这句话没有证据（也顺手排掉 size 0 的本遍载体）。
CRASH36 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_3836_*.txt'))
                 if os.path.getmtime(p) < _START and os.path.getsize(p) > 0)
CRASH36_PREIMG = []
for _c in CRASH36:
    _t = txt(os.path.join(EV, _c))
    assert 'Traceback' in _t or 'Error' in _t, 'ABORT: 候选崩遍载体 %s 里两种错误证据都没有 ⇒ 它不是崩溃那遍' % _c
    assert 'LANDED' not in _t, 'ABORT: 崩遍载体 %s 里含写盘后令牌 LANDED ⇒ 它不是崩在写盘前' % _c
    # PRE-IMAGE 那行打在 pre-image 落盘之后、正文写盘之前，所以"含 PRE-IMAGE"不能当"已写盘"用。
    # 判"目标未被改"要靠盘上对照：那遍写的 pre-image 必须与**本遍回落所用的头段**逐字节相等。
    # （上一代我拿它对"目标现件"，缺陷 (o) 之后那个口径不成立：现件可能带着上一遍写进去的尾节，
    #   而头段已经被上面那道核销闸钉成与所有 pre-image 全等。）
    _pm = re.search(r'PRE-IMAGE (\S+\.md)', _t)
    if _pm:
        _pp = os.path.join(EV, _pm.group(1))
        assert os.path.isfile(_pp), 'ABORT: 崩遍 %s 点名了 pre-image %s 而它不在盘上' % (_c, _pm.group(1))
        assert io.open(_pp, 'rb').read() == pre, \
            'ABORT: 崩遍 %s 的 pre-image 与本遍头段不等 ⇒ 归因要重写' % _c
        CRASH36_PREIMG.append(_pm.group(1))

# 内容级闸③（本遍新增，给 (k) 那族装执行者）：**被 `%` 格式化的字符串字面量里不得有裸 `%`**。
# 上一遍它就是以 `TypeError: not enough arguments for format string` 崩在 BODY 装配处（写盘之前）。
_self = io.open(__file__, encoding='utf-8').read()
# `%%` 必须**整对**吃掉：只写前瞻会把转义对的第二个 `%` 当成裸 `%`（本闸首版就是这样假红了 5 处）
_PCT_OK = re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[sdrifxeEgGoc])')
_stray_pct = []
for _n in ast.walk(ast.parse(_self)):
    if isinstance(_n, ast.BinOp) and isinstance(_n.op, ast.Mod) \
            and isinstance(_n.left, ast.Constant) and isinstance(_n.left.value, str):
        _s = _n.left.value
        _ok = set()
        for _m in _PCT_OK.finditer(_s):
            _ok.update(range(_m.start(), _m.end()))
        _stray_pct += [(_n.lineno, _s[max(0, _i - 10):_i + 10])
                       for _i, _ch in enumerate(_s) if _ch == '%' and _i not in _ok]
assert not _stray_pct, 'ABORT: 本脚本有 %d 处 %%-格式串里含裸 %%：%r' % (len(_stray_pct), _stray_pct[:2])

DEFECTS = [
    '(a) `land_r61b_readme12.py` 写盘后的证明段把**行下标喂给 bytes 对象**（`chk[行号]` 取到一个 int 再 `.decode` 才崩）——'
    '这一处是**改之前就静态发现**的，盘上从未存在过那个形态，所以没有"崩溃那次的读数"要洗',
    '(b) **纯插入的行级证明写成逐位置差集** ⇒ 插入点之后每行都错位，**盘上内容是对的而证明全红**，且崩在写盘之后（盘已动）、'
    '那一遍**没写载体**（同目录按 `r61b_readme12_land_*` 前缀现扫 = 0 只，本遍钉成 assert）；'
    '修法 = 三段式 `prove()`（前缀逐字等 / 插入段逐行等 / 后缀逐字等 + 行数等式），并加 `--proof-only` 模式让修好的分支'
    '**在真字节上被执行一次**（可达性取证），权威 = `r61b_readme12_proof_151152.txt`',
    '(c) proof 遍首跑打印了 `VERDICT=LANDED rc=0` 而它按设计什么都不写 ⇒ 令牌没按模式分支，字面为假',
    '(d) README 那行载体先引了一只**盘上从未存在**的文件名（假指针），由 ②③ 那两遍改掉',
    '(e) **`diff -rq` 的输入目录不存在时 stdout 为空 ⇒ 按行数算的"0 行 differ"照样绿**（根 B 家族住在 '
    '`hardware/zizhao-esp32s3/backups/` 而最初写成 `main/` 下），修法 = `dqr()` 里 assert 两侧目录存在 + stderr 空',
    '(f) **Python 单引号正文里嵌 ASCII 撇号** ⇒ 字面量提前闭合、剩下半句被读成幂运算，报 '
    '`TypeError: unsupported operand type(s) for ** or pow()`，而**语法体检照过**（闭合后仍合法），崩在写盘前的裁决段',
    '(g) 上一批（FreqErr 第十八批）自己 rc=1 的那几遍 = %s，逐只现读其 stdout 不含写盘后令牌 `LANDED`，'
    '且留有错误证据（`Traceback`，或像 15:21 那只那样根本没跑起来的 `SyntaxError`；若哪遍已写到 pre-image，'
    '还要那只与 `FreqErr.md` 现件逐字节相等）⇒ 全崩在写盘之前'
    % '、'.join('`%s`' % x for x in CRASH18),
    '(h) **本节落地器首跑栽在"行尾尺"的公式上**：裸 LF 行数我写成 `len(splitlines()) - 1 - count(CR)`（从上一代'
    '落地器抄来的形状），对**末行以 CRLF 收尾**的文件恒差 1 ⇒ 全 CRLF 的排查记录算出 **-1**、被 `== 0` 拦下。'
    '错的方向是"假红"而不是"假绿"（它崩在写盘之前、盘上零改动），但同一只公式若反过来用在别的行尾口径上就会漏判；'
    '本遍改成 `count(LF) - count(CR)`，与写盘后那条 `裸 LF = 0` 用同一把尺',
    '(i) **读载体字段用不带行锚的 `re.search` ⇒ 取到的可能是另一行的同名 token**：门载体里 `TOTAL_HITS` '
    '先出现在 `PROV_PASS_TOTAL_HITS=` / `SSH_TOTAL_HITS=` 两只更长的字段内部（search 命中**第一处**，'
    '也就是 `PROV_PASS_TOTAL_HITS=0` 的后半截），阳性对照载体里 `VERDICT` 在第 13 行的 `CROSS_CHECK` 汇总句里'
    '已经出现了一次 `VERDICT=CLEAN`，而真正的裁决在第 15 行 ⇒ `ps_verdict` 取成 `CLEAN`、assert 当场炸（**假红**）。'
    '**同一族还有更险的一面**：`gs_hits` 那格两行恰好同为 0，所以它一直是"取错行但值碰巧对"的假绿，'
    '只有 `ps_verdict` 那一格替全族暴露了缺陷。修法 = 所有载体字段一律加 `(?m)^...$` 行锚，'
    '汇总行里的 `equal=` 则连前缀一起锚（`(?m)^CROSS_CHECK.*equal=(\\w+)$`）。'
    '本遍另外把"崩遍载体"的识别从"只看 mtime"升级成 **mtime + 非空 + 留有错误证据** 三条并判，'
    '否则本进程自己那只尚未落字的载体会被算进"已崩的那几遍"里（错误证据那一半一开始写窄了，见 (n)）',
    '(j) **定位 README 格子用裸子串 `' + '第十一次读数' + '` ⇒ 命中 2 处**：除标题行外，上一格正文末尾那句'
    '「本遍真正落地的 = 新根一对 + docs 第十一遍 + 本格（第十一次读数）」也含同一短语（而且**短语被括号包着、'
    '根本不是标题**）。这一族与 (i) 同根（匹配口径不锚结构），差别是 (i) 会**读错值**、这一条直接**假红**。'
    '修法 = 段起点只认结构前缀（标题行以 `【09-26 ` 开头），并顺手把上一格的取块区间**截到下一格标题之前**'
    '——否则两格同号编号（②③④⑤）会互相串台，那是一种既能假红也能假绿、且当下看不出来的形态',
    '(k) **正文里写路径环境变量 `%TEMP%` 时那个裸百分号没转义** ⇒ 那一格是被 `%` 格式化的字面量，'
    'Python 把 `%T` 当转换符，'
    '报 `TypeError: not enough arguments for format string`，崩在 BODY 装配处（仍是写盘之前）。'
    '与 (f) 同族（都是"排版字符撞进 Python 词法/格式化"），差别是 (f) 能被 `ast.parse` 放过、这一条要跑到那一行才炸。'
    '本遍不止改字面量，还给它**装了执行者**：写盘前用 `ast.walk` 扫本脚本自己，'
    '凡 `X % (...)` 且 X 是字符串字面量，就要求其中每个 `%` 都能被格式化语法解释，否则 ABORT —— '
    '这条闸对**本遍之后新写的每一格**都生效，不靠我记得转义。'
    '**而这张闸自己首遍就假红**：判"裸 %%"用的是负向前瞻 `%(?!...[sdrfx%])`，它把转义对 `%%` 的**第二个** `%` '
    '也单独看一眼，后面跟的是正文里的 `-` / `：` ⇒ 5 处全被点名（其中就包括闸自己那句 ABORT 文案）。'
    '修法 = 改成**整对吃掉**：一次 `finditer` 匹配 `%%` 或完整转换符并记下被覆盖的下标，'
    '剩下的 `%` 才是裸的 —— 前瞻式判据对"成对字符"天生不成立，这一条与 (i)(j) 同族（匹配口径没对齐结构）',
    '(l) **在册末版那只的名字用 `os.path.relpath(p, h3)` 算 ⇒ 正文里落成一个裸名 `MANIFEST.txt`**（它住在 '
    '`hardware/ht305_sync/` 下）。这一处比前几例更绕：字面量是我写的，但它**由变量插值而来**，'
    '所以我逐字读 BODY 也读不出问题，只有本遍那只"点名的文件必须盘上存在"的 `_named` 闸把它拦下来'
    '（该闸按仓库根解析裸名 ⇒ 查无此物）。修法 = 指针一律以**仓库相对路径**入正文，并紧跟一条 `isfile` 前置 assert；'
    '同类缺陷在上一代是"手写裸名"，本代是"算出来丢掉目录"，说明**只要指针的口径不锁死在仓库根，它就会漂**',
    '(m) **把 `PRE-IMAGE` 当"写盘之后"的令牌用 ⇒ 判别式与它要量的东西差半步**：本遍落地器是先写 pre-image、'
    '打印 `PRE-IMAGE ...` 那一行，**再**写目标文件。所以有一遍崩在这两步之间（一行 `print` 的格式占位符比实参少，'
    '其中一格还拿到了字符串），它的载体里带着 `PRE-IMAGE`，被我自己那条'
    '"崩遍不得含 PRE-IMAGE"assert 拦下 —— **这一次它拦的是真事，但拦的理由是错的**：那一遍确实没动目标文件，'
    '而按我的写法它会被判成"动过盘"。若反过来有一遍真动了盘却恰好没打印 LANDED，这把尺也照样瞎。'
    '修法 = 写盘后令牌只认 `LANDED`；`PRE-IMAGE` 改为**正向取证**——点名它的那遍必须让那只 pre-image 与'
    '**目标现件逐字节相等**（相等 = 目标至今没被这一遍改过），本遍与第十八批那批崩遍都走这一条。'
    '顺带：这一格最初把那句 Python 报错**原文照抄进正文**，被本节"未插值占位符"闸判红 —— '
    '那把尺在这里取到的是对的（读者无法区分"引用一条报错"和"漏填一个占位符"），所以措辞让位、改成转述',
    '(n) **给"崩遍"装的证据闸写窄了，被一只真崩溃假红**：我要求每只崩遍载体都含 `Traceback`，'
    '而第十八批 15:21 那遍是**编译期**就红（源码里一只圆括号未闭合的 `SyntaxError`）—— 模块**根本没开始执行**，'
    'Python 只吐报错头几行、没有 `Traceback` 那三行。这只恰恰是"崩得最早"的一类，却被我的判据判成"不是崩溃那遍"。'
    '教训与 (h) 成对：**判据的方向错了两种都会挨打**——写宽把"动过盘"放进来，写窄把真证据挡在外面，'
    '而挡下来时它也顺手把这句话的可信度打掉了。本遍改成两形态并认（`Traceback` 或任何 `Error`），'
    '并把"根本没跑起来"这一类单独说清楚（它比跑起来才崩更强的蕴含"没动盘"）',
    '(o) **写盘之后那条断言用的"预期值"算式自己错了一格 ⇒ 那一遍真的动了盘**：行数预期我写成 '
    '`lines_before + len(BODY) + 1`，那个 `+1` 是给"末行没有行尾符"的文件留的，而本文件末行以 CRLF **收尾**'
    '（前一道闸已经钉过 `pre.endswith(CRLF)`）⇒ `splitlines()` 比预期少 1 行，assert 就崩在 `write()` 的下一行。'
    '这是本系列一直靠"全部裁决排在写盘之前"躲开的那一类，而它从没被指望发生在**证明段**上：'
    '盘上因此多出 %d B / %d 行的**上一版本节**。那一段不是坏数据（它正是那一遍现算出来的正文），'
    '但它是**过期正文**——只数、时刻、缺陷条数都停在写它的那一瞬间，且不含本条，留着比没有更坏。'
    '本遍处置分三段：①幂等门的权威判据从"正文里有没有本节"换成"载体里有没有写盘后令牌 `LANDED`"'
    '（有 = 真落地过 ⇒ ABORT；没有 = 崩在写盘之后 ⇒ 允许核销）；②整只现件先按字节归档成 `%s`，'
    '再把"去掉尾节"剩下的头段与盘上**全部** pre-image 载体逐字节对账，任一只不等就本遍不动盘；'
    '③预期值不再由我手写的那一条算式单独决定：同一遍里用**两种独立推法**（行尾计数 `+ len(BODY)`，'
    '与"内存里先拼好的 `head + body` 去 `splitlines()` 数"）在**写盘之前**互等，不等即 ABORT，'
    '写盘后再拿这两个数跟盘上回读比。教训：**证明段用的算式也是待检的正文**——它错了不会放过任何一遍，'
    '反而会亲手制造它要防的那种事故；凡能在写盘前算出来的预期，都必须排在写盘前'
    % (STALE_B, STALE_LINES, STALE_NAME),
]
assert STALE_NAME is not None and STALE_B > 0 and STALE_LINES > 0, \
    'ABORT: (o) 的核销读数没有对象 ⇒ 盘上并没有待核销的尾节，本节措辞与现场态不符'
if CRASH36:
    DEFECTS[-1] += '。本遍进入前已崩的那几遍载体 = %s（逐只现读：留有错误证据、不含写盘后令牌 `LANDED`%s）' % (
        '、'.join('`%s`' % x for x in CRASH36),
        '；其中点名了 pre-image 的那些遍，pre-image 与**本遍回落所用的头段逐字节相等**（= 那一遍没把目标改到别处去）'
        if CRASH36_PREIMG else '；本遍进入前的各遍都没写到 pre-image 那一步')
else:
    DEFECTS = DEFECTS[:-1]

PT = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
BODY = [
    H36 + 'R61 尾巴·提交轮 #10 + docs 第十二遍 + README 第十二次读数 + FreqErr 第十七/十八批'
          '（现跑于 %s）：本遍**零代码进镜像**，但把"落地器自己的证明写法"审成了缺陷；'
          '在册裁决第一次有了代码执行者；一次"纯插入"落地的 rc=1 与"盘上内容是对的"同时成立；'
          '而本遍自己还多出一起相反形态：一次 rc=1 **确实动了盘**，其尾节已按字节归档并被本遍核销（见缺陷 (o)）'
          '（未 push、未 amend、零删除、屏侧零进展）' % PT,
    '',
    '- **本节登记的四件事是一遍，不是四遍**：提交轮 #10（`%s`）→ docs/ 快照第十二遍 → `backups/README.md` 第十二次读数 → '
    '`FreqErr.md` 第十七批与第十八批。四件都落在 §38.35 那一遍（标题行现跑于 **%s**，本遍 assert 它早于快照刷新时刻）**之后**、'
    '第 16 代同步之前，所以第 16 代的载荷必须同时含这四件（这一点在 §38.37 里现验，不在本节预写）。' % (head, H35_AT),
    '- **提交轮 #10 的构成（全部现跑）**：`git diff --numstat c7de970 %s` = **%d 只** = 文本 **%d 只**（**+%d / −%d** 行）'
    '+ 二进制 **%d 只**（numstat 对二进制打 `-` 而非整数，就是那两只原厂镜像 `%s`）；'
    '配套门 = 同目录 `staged_cred_gate_r61b_final106.txt`：`FILES_SCANNED=%d` / `TOTAL_HITS=%d` / `VERDICT=%s`，'
    '阳性对照 = 同目录 `staged_cred_gate_r61b_final106_pos.txt`：`INDEX_DELETED=%d` / `INDEX_SCANNED=%d` / `ARMS_FIRED=%s` / `equal=%s` / `VERDICT=%s`。'
    '**门名与提交只数第一次由代码对上**（`gs_files == ps_del + ps_scan == n_files` 三向 assert，缺一即 ABORT）；'
    '`rev-list --count origin/main..HEAD` 现跑 = **%d** ⇒ **未 push、未 amend**。' % (
        head, n_files, n_txt, plus, minus, n_bin, ' + '.join(deleted),
        gs_files, gs_hits, gs_verdict, ps_del, ps_scan, ps_arms, ps_eq, ps_verdict, revlist),
    '- **在册裁决第一次有执行者（承 §38.33 那起事故）**：清单器 `hardware/r61b_sync/scripts/make_staged_list_r61b.py` 里 '
    '`BIN_EXT` 后缀表 + `BINS_IN_KEEP` 必须为 0 + `RULING_PROBE`（拿盘上那两只原厂镜像当探针，md5 与尺寸现算，'
    '再与 §38.33 登记的文本互核）。上一代这句只是**叙述**，本代它跑在真字节上并落进载体；'
    '**本节写它之前又现跑了一遍，而且这次由代码核对**：从盘上现读 §38.33 那一节（`### 38.33` 到 `### 38.34` 之间），'
    '把它的尺寸格与「现算 md5」格解析成 %s 与 %s，再对两只文件现算 `getsize` + `md5` ⇒ 逐只全等（%s），'
    '且两只在盘、都**不可写**（在册口径「只读」由 `os.access(W_OK)` 反面 assert）。' % (
        '、'.join('%s = %d B' % (n, s) for n, s in sorted(sz_rec.items())),
        '、'.join('md5 %s' % m for m in md_set),
        '、'.join('`%s` %s B / md5 前 8 `%s`' % (n, format(s, ','), m[:8]) for n, s, m in bin_probe)),
    '- **docs/ 快照第十二遍（产物即凭证）**：`SNAPSHOT_NOTE.txt` 现读 = 刷新时刻 **%s** / 表格 **%d 行** / 目录现读 **%d 只** '
    '= 表格 %d + NOTE 自身（`docs_files == src_n + 1` 与 `tbl_rows == src_n` 两道 assert 由本遍把关）/ '
    '凭据闸 **%d 只源全扫、HITS=0** / 表内 `NEW -> ` 标记 **%d 处**（= 0 ⇒ 第十二遍与第十一遍同一只脚本、同一份 SRCS，**纯覆盖不新增**）。'
    '⚠ 点名一处口径：本遍**没有**给这遍快照另落一份 stdout 载体，上面五格**全部从盘上 NOTE 现读**，'
    '所以"执行输出没落盘"这一族在本节不构成假读数 —— 但它在 `hardware/r61b_sync/evidence/` 里是**空缺**，'
    '写在这里是为了下一遍别再引"第十二遍的 stdout"这种不存在的东西。'
    '⚠ 第二处口径：快照那一遍**早于** FreqErr 第十八批落地（上面第一格的刷新时刻 < 第十八批 pre-image 文件名内嵌时刻 `%s`，'
    '由本遍比较这两串把关），'
    'NOTE 里那只 `FreqErr.md` 还是 **%s B**（现读该行第 2 格），'
    '小于盘上现读 %s B ⇒ 按 NOTE 自己第 2 行那句「快照非终态」，本节不把它当终态。' % (
        snap_at, tbl_rows, docs_files, tbl_rows, src_n, new_rows, fe18_at, format(freq_docs, ','), format(fe_bytes, ',')),
    '- **`backups/README.md` 第十二次读数（现 %s B / %d 行 / md5 前 8 `%s`）**：第十二格 ①~⑬ 全现跑；'
    '本遍**把"九个数与第十一次同值"这句装了执行者** —— 从第十一、十二两格正文各自现读 ②③④⑤ 四组在册数字，'
    '与本遍现跑做**三向全等** assert（第十一次 == 第十二格 == 本遍）：'
    'r43 两根 **%d/%d** 行、r53 两根 **%d/%d** 行、工作树 `main/` **%d 只 / %s B**、`sourceonly` **%d** 行 differ；'
    '⑥ 那一格只有第十二格在册，做两向（新根 `%s` **%d 只**，两根对 `main/` 的 `diff` **%d/%d** 行）。'
    '同值才是这一代的真相：**本遍只动文档与取证件**；'
    '而 ④ 那一格的话要说全 —— 工作树那 %d 只里确有上一遍（R58~R61）的代码增量，本遍自己一字节代码没进。' % (
        format(rb_bytes, ','), rb_lines, rb_md5, d_r43a, d_r43b, d_r53a, d_r53b, wt_n, format(wt_b, ','),
        d_src, RC, rc_files, d_rca, d_rcb, wt_n),
    '- **README 这一格被自己动过三遍（点名，不藏）**：①插入 ①~⑬（`land_r61b_readme12.py`）→ ②补一行"载体"→ '
    '③把那行载体**订正成真话**（`fix_r61b_readme12_carrier.py`，`VERDICT=CARRIER_LINE_FIXED rc=0`）。'
    '上一版那句"只做了一次插入"落笔即假；三遍都**没覆写任何旧格、零删除**。pre-image 与两遍 proof 载体见本节末尾名单。',
    '- **本遍 %d 处缺陷（逐条点名，含修法与执行者；只数由 DEFECTS 列表自身给出，不写字面量）**：%s' % (
        len(DEFECTS), '；'.join(DEFECTS) + '。'),
    '- **(o) 的执行现场（本节是这个文件里第二次落笔，第一次那份永久留在归档件里）**：进入本遍时现件 = '
    '**%s B / %d 行**，其尾部 **%s B / %d 行** 是上一遍（载体在下方名单里）写进去的旧版本节。'
    '收口三步都在代码里：①先确认 `hardware/r61b_sync/evidence/` 下**没有任何** `r61b_3836_*.txt` 载体含 `VERDICT=LANDED`'
    '（有就说明本节真落地过一次 ⇒ 本遍 ABORT，不靠"正文里有没有标题"判幂等）；②整只现件按字节归档成 `%s`'
    '（目标已存在即 ABORT、写完立刻回读比等）；③"去掉尾节"剩下的头段与该目录下**全部** `record_pre3836_*.md` '
    '逐字节对账，任一只不等就不动盘 —— 全等才回落到头段并重写本节。**零删除**：被替换掉的那一份既在归档件里，'
    '也在这条 assert 的比对对象里。' % (
        format(STALE_CUR_B, ','), STALE_CUR_LINES, format(STALE_B, ','), STALE_LINES, STALE_NAME),
    '- **FreqErr.md 两批终态（现读）**：`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B / md5 前 8 `%s`；'
    '第十七批 = **%d** 条（把订正句插进**他人**台账行时"本批"随插入点换了指代、行号成自指），'
    '第十八批 = **%d** 条（上面 (b)(d)(e)(f) 四类，落地器自己就是第①条三段式证明的执行者）——'
    '这两个只数都是**从各自落地载体现读**（`ENTRIES a -> b (本批 +N)` 一行，并就地复算 `b − a == N`，'
    '且第十七批终值必须等于第十八批起值 ⇒ 两批之间没夹别的批次），不是本节自己数的。'
    '（本遍第一版这里写的是"正则 `本批正文 = N 条`"那把**盘上不存在的尺**，取不到即 ABORT，从未产出过读数）'
    '两批各带一份 pre-image（`%s` / `%s`），'
    '第十八批另有独立复核 `r61b_freqerr18_verify_152543.txt`：`LEDGER_MATCHES_DISK` / `APPEND_EQ_OK` / '
    '`PURE_APPEND`（盘上现件以 pre-image **逐字开头**）/ `CITED_ALL_PRESENT`（正文点名的 **%d** 只载体现扫全在）/ '
    '`GIT_DIFF_NUMSTAT +%d / -0`（相对**索引**，只量本批这一遍）。' % (
        fe_n, fe_lines, format(fe_bytes, ','), fe_md5, n17, n18,
        os.path.basename(p17[0]), os.path.basename(_p18s[0]), cited18, ns_plus18),
    '- **现场态（本节同一刻现跑）**：HEAD `%s` / `rev-list` **%d**（未 push）/ `status --porcelain` **%d 行**（%s），'
    '其中 `??` 里 **%d 行是目录折叠**（行尾是斜杠，一行代表整棵子树）⇒ **porcelain 行数与文件只数是两把不同的尺，'
    '任何两代之间都不能拿它互相换算**，本节只登记本遍这一把；'
    '`python -m serial.tools.list_ports` 现跑 = `%s` ⇒ **COM14 在位 = %s**（枚举 rc=0 且解析出 %d 只 COM 名，'
    '空读数会被 assert 拦下，所以"缺席"不是拿空列表蒙的）；'
    '`hardware/ht305_sync/` 递归现读 **%d 只**、目录内最新一只 = `%s`（mtime %s）⇒ **gen 24 之后一字节未落**、本代不新建清单代；'
    '`C:\\esp\\` 顶层串口原始日志现扫 **%d 只**，其中含 `PROV_PASS` 明文 **%d 只**（**不递归子目录**，'
    '这一族永不 stage / 永不 push / 永不删除，因此**不在 ht305 载荷里**，载荷里是脱敏取证件）。' % (
        head, revlist, st_lines, ' + '.join('`%s` %d' % (k.strip() or '空', v) for k, v in sorted(st_kind.items())),
        st_dirs, ', '.join(coms), com14, len(coms), h3_files, h3_latest_name,
        datetime.datetime.fromtimestamp(h3_latest).strftime('%Y-%m-%d %H:%M:%S'), len(log_files), len(log_dirty)),
    '- **本遍没做（点名）**：没烧录、没碰串口（COM14 不在位）⇒ 人眼看到屏 = 仍 **1 次**（R59 那一次）、'
    '看到第二页 **0 次**、用户真按 BOOT **0 次** ⇒ **不播提示音的判据仍成立**；'
    '**没重建镜像**——这句本遍有执行者：从 `hardware/BOARD_S3_ePaper_1_54.md` 现读在册三字段（**%s B / md5 `%s` / '
    '`bin[176:184]` `%s`**），对本遍现算的构建目录那只逐字段 assert 全等，且它的 mtime = **%s** 早于本轮起点 %s；'
    '更早在册那句「待烧仍是 `fb32168a…`」属于 09-24 的快照，**本遍不复述它**（复述就是把上一代读数当本代）。'
    '没新建备份根、没覆写任何旧根；`hardware/ht305_sync/` 一字节未落；'
    '**未 `git push`、未 amend、零删除**（含 `%%TEMP%%` 与各臂抓回原件）。第 16 代收口同步与 §38.37 在本节之后。' % (
        format(rec_size, ','), bb_md5, bb_elf16, bb_mtime.strftime('%Y-%m-%d %H:%M:%S'), ROUND_FROM),
    '- **本遍取证名单（`hardware/r61b_sync/evidence/` 内 mtime 落在「本轮起点 %s」与「本脚本进入时刻 %s」之间的只数 = %d，'
    '逐只点名；按 mtime 圈而不按文件名里的 6 位时刻圈 —— 后者跨天会把上一日的同名后缀混进来）**：%s。' % (
        ROUND_FROM, _ST, n_ev_tail, '、'.join('`%s`' % x for x in EV_TAIL)),
    '',
]
body_bytes = ('\r\n'.join(BODY) + '\r\n').encode('utf-8')
assert sec not in body_bytes, 'ABORT: 本节写出去的字节含口令明文'
_bt = body_bytes.decode('utf-8')
_stray = [l[:60] for l in _bt.split('\n') if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*\}', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本节有 %d 行带未插值占位符：%r' % (len(_stray), _stray[:2])
_bs = [l[:60] for l in _bt.split('\n') if chr(92) in l and 'esp' not in l and 'C:' not in l]
assert not _bs, 'ABORT: 本节有 %d 行含反斜杠字符（除点名 C 盘路径那格）：%r' % (len(_bs), _bs[:2])
_ap = [l for l in _bt.split('\n') if chr(39) in l]
assert not _ap, 'ABORT: 本节有 %d 行含 ASCII 撇号：%r' % (len(_ap), [x[:60] for x in _ap[:2]])
# 抽出来的是**裸名**（字符类不含 `/`），所以存在性按"全仓（除 .git）basename 命中"判 ——
# 那只假指针闸量的是"这物存不存在"，指针该带哪一层目录由正文自己写全（在册末版那只另有 isfile 前置 assert）。
_repo_bases = set()
for _r, _ds, _fs in os.walk(REPO):
    if '.git' in _ds:
        _ds.remove('.git')
    _repo_bases.update(_fs)
assert len(_repo_bases) > 100, 'ABORT: 仓库 basename 现读 %d 只 ⇒ 这把我自己喂给闸的尺子本身在漏' % len(_repo_bases)
_named = set(re.findall(r'[A-Za-z0-9_.-]+\.(?:txt|md|py|bin|log)', _bt))
_missing = [x for x in sorted(_named) if x not in ('SNAPSHOT_NOTE.txt',) and x not in _repo_bases
            and not os.path.isfile(os.path.join(EV, x))]
assert not _missing, 'ABORT: 本节点名了查无此物的载体/文件：%s' % _missing
# 预期值：两种**独立**推法必须在写盘之前互等（缺陷 (o) 的执行者；上一遍只有后一种的错式，崩在写盘之后）
exp_lines = len((pre + body_bytes).splitlines())
exp_bytes = len(pre + body_bytes)
assert exp_lines == lines_before + len(BODY), \
    'ABORT: 行数两种推法不等 %d != %d ⇒ 本遍在写盘之后才会知道，公式错了也不许动盘' % (exp_lines, lines_before + len(BODY))
assert exp_bytes == bytes_before + len(body_bytes), 'ABORT: 字节两种推法不等'

_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'record_pre3836_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('GATE %d/%s/HITS%d POS DEL%d SCAN%d ARMS%s equal%s VERDICT%s 门名==提交只数 %d==%d+%d' % (
    gs_files, gs_verdict, gs_hits, ps_del, ps_scan, ps_arms, ps_eq, ps_verdict, gs_files, ps_del, ps_scan))
print('COMMIT %s FILES %d TXT %d BIN %d +%d/-%d DELETED %s REVLIST %d STATUS %d' % (
    head, n_files, n_txt, n_bin, plus, minus, deleted, revlist, st_lines))
print('FREQERR %d 条 / %d 行 / %d B / md5 %s' % (fe_n, fe_lines, fe_bytes, fe_md5))
print('README12 %d B / %d 行 / md5 %s | DOCS AT %s 源 %d 表 %d 目录 %d NEW %d' % (
    rb_bytes, rb_lines, rb_md5, snap_at, src_n, tbl_rows, docs_files, new_rows))
print('ROOTS r43 %d/%d r53 %d/%d sourceonly %d WT %d 只/%d B r61close %d 只/%d B diff %d/%d（五格在册==现跑，已 assert）' % (
    d_r43a, d_r43b, d_r53a, d_r53b, d_src, wt_n, wt_b, rc_files, rc_bytes, d_rca, d_rcb))
print('BINS %s | BUILD %d B md5 %s elf16 %s mtime %s（与板档案在册三字段全等）' % (
    '、'.join('%s %d B/%s' % (n, s, m[:8]) for n, s, m in bin_probe),
    rec_size, bb_md5[:8], bb_elf16, bb_mtime.strftime('%Y-%m-%d %H:%M:%S')))
print('SNAP12 AT %s < FREQERR18 %s | NOTE 里 FreqErr %d B < 盘上 %d B | STATUS %d 行（目录折叠 %d）' % (
    snap_at, fe18_at, freq_docs, fe_bytes, st_lines, st_dirs))
print('COMS %s COM14=%s | HT305_SYNC %d 只 最新 %s | ESPLOG %d 只含明文 %d 只' % (
    coms, com14, h3_files, h3_latest_name, len(log_files), len(log_dirty)))
print('EV_TAIL %d 只（mtime 落在 %s ~ 本遍进入 %s 之间）' % (n_ev_tail, ROUND_FROM, _ST))
print('DEFECTS %d 处（本遍进入前崩遍载体 %s）| 十七批 %d 条 / 十八批 %d 条 / 复核点名 %d 只载体 / +%d-0' % (
    len(DEFECTS), CRASH36 or '无', n17, n18, cited18, ns_plus18))

io.open(TGT, 'wb').write(pre + body_bytes)
chk = io.open(TGT, 'rb').read()
cl = chk.splitlines()
assert len(cl) == exp_lines, 'ABORT: 行数 %d != 预期 %d' % (len(cl), exp_lines)
assert len(chk) == exp_bytes, 'ABORT: 字节 %d != 预期 %d' % (len(chk), exp_bytes)
assert cl[:len(pl)] == pl, 'ABORT: 前缀未逐字保持（本节是纯追加）'
assert cl[len(pl):] == body_bytes.split(b'\r\n')[:-1], 'ABORT: 追加段逐行不等'
assert chk.count(b'\n') - chk.count(b'\r') == 0, 'ABORT: 追加后出现裸 LF，行尾口径破了'
assert H36.encode('utf-8') in chk and H35.encode('utf-8') in chk
print('PREFIX %d 行逐字等 / APPEND %d 行逐行等 / 后缀为空（三段式）' % (len(pl), len(cl) - len(pl)))
print('RECORD %d 行 / %d B -> %d 行 / %d B | MD5 %s -> %s' % (
    lines_before, bytes_before, len(cl), len(chk), hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
