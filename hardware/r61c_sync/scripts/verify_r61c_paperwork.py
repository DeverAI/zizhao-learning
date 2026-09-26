# R61c paperwork **独立复核遍**（不是重跑落地器去洗绿）。
# 存在理由 = 排查记录 (18) 第①条那句「修好的判据必须在真字节上被执行一次（可达性取证）」的执行者：
#   落地器上一遍崩在写盘之后的三段式证明（`cl` 是 bytes 行表、`al` 是 str 行表 ⇒ 恒不等 ⇒ 盘对而尺红），
#   改好之后的那一支从来没在真字节上跑过 ⇒ 本遍拿两只 pre-image 与盘上现件，把**同一种**三段式判据跑一遍。
# 三条继承：①候选为 0 一律 ABORT（命中 0 ≠ 干净）；②正文里每个数字都从盘上载体或现跑命令取，取不到即 ABORT；
#   ③本遍只读被检件，只在 evidence/ 落一只自己的载体（并在结论里点名"本遍自己让 porcelain 只数 +1"）。
import datetime
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
DEV = os.path.join(REPO, 'dev_log', '20260926.md')
DON = os.path.join(REPO, 'done.md')
FE = os.path.join(REPO, 'FreqErr.md')
REC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
RDM = os.path.join(REPO, 'backups', 'README.md')
DOCD = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
NOTE = os.path.join(DOCD, 'SNAPSHOT_NOTE.txt')
UPD = os.path.join(REPO, 'updates', '20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md')
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
LCL = os.path.join(EV, 'r61c_local.txt')
VRX = os.path.join(EV, 'r61c_verify.txt')
RT = os.path.join(EV, 'r61c_roundtrip.txt')
DLT = os.path.join(EV, 'r61c_cutoff_delta.txt')
LD = os.path.join(EV, 'r61c_listdiff.txt')
BS = chr(92)
ESP = 'C:' + BS + 'esp' + BS
BATCH = '第三十四批'
SECH = '## 二十六、'
KINDS = ['第十五批', '第十六批', '第十七批', '第十八批', '第十九批']
_T0 = datetime.datetime.now()


def rd(p):
    return io.open(p, encoding='utf-8').read()


def rb(p):
    return io.open(p, 'rb').read()


def mb(p):
    b = rb(p)
    return len(b), b.count(b'\n'), hashlib.md5(b).hexdigest()[:8]


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr.decode('utf-8', 'replace')[:200])
    return r.stdout.decode('utf-8', 'replace')


def one(pat, label):
    hits = sorted(glob.glob(os.path.join(EV, pat)))
    assert hits, 'ABORT: %s 候选 0 只（命中 0 不是干净）：' % label + pat
    assert len(hits) == 1, 'ABORT: %s 候选不唯一（%d 只）：%s' % (label, len(hits), hits)
    return hits[0]


# ---------- ① 三只 pre-image 现选现读 ----------
PRE_DEV = one('devlog_pre34_*.md', 'dev_log pre-image')
PRE_DON = one('done_pre26_*.md', 'done pre-image')
stamp = os.path.basename(PRE_DEV)[len('devlog_pre34_'):-len('.md')]
assert os.path.basename(PRE_DON).endswith('_%s.md' % stamp), 'ABORT: 两只 pre-image 不同遍（时刻戳不等）'
assert stamp == '20260926_164554', 'ABORT: pre-image 时刻戳与本遍预期的落地遍不同：' + stamp

pairs = [('20260926.md', PRE_DEV, DEV, '## ' + BATCH), ('done.md', PRE_DON, DON, SECH)]
APPEND = {}
for nm, pp, cp, anchor in pairs:
    pre, cur = rb(pp), rb(cp)
    pl, cl = pre.splitlines(), cur.splitlines()
    app = cur[len(pre):]
    al = app.splitlines()
    # 三段式（bytes 对 bytes）——上一遍红在这里，本遍是它修好后的第一次真字节执行
    assert cur.startswith(pre), 'ABORT: 前缀未逐字保持：' + nm
    assert cl[:len(pl)] == pl, 'ABORT: 前缀行不等：' + nm
    assert cl[len(pl):] == al, 'ABORT: 追加段逐行不等：' + nm
    assert len(cl) == len(pl) + len(al), 'ABORT: 行数加法不等（pre 末行不以换行收尾 ⇒ 字节偏移落在行中）：' + nm
    assert len(cur) == len(pre) + len(app), 'ABORT: 字节加法不等：' + nm
    assert cur == pre + app, 'ABORT: 后缀非空（盘上终态 != pre + 追加段）：' + nm
    # 阳性对照：把上一遍那把**错尺**（str 行表 vs bytes 行表）在同一段真字节上再跑一次，它必须仍然红。
    # 它不红 ⇒ 本遍这条 assert 没有牙，"修好了"就只是嘴上说的。
    old_form = cl[len(pl):] == [x.decode('utf-8') for x in al]
    assert old_form is False, 'ABORT: 错尺在本遍竟然通过 ⇒ 这段比较根本没在比东西：' + nm
    hd = [x for x in al if x.startswith(anchor.encode('utf-8'))]
    assert len(hd) == 1, 'ABORT: 本节标题在追加段里出现 %d 次：' % len(hd) + nm
    assert not [x for x in pre.splitlines() if x.startswith(anchor.encode('utf-8'))], \
        'ABORT: 追加前原件里已有本节标题（本遍不是纯追加）：' + nm
    txt = app.decode('utf-8')
    APPEND[nm] = txt
    assert txt.endswith('\n'), 'ABORT: 追加段末行不以换行收尾：' + nm
    print('PROVE %-12s 前缀 %d 行逐字等 / 追加 %d 行逐行等 / 后缀空 / %s -> %s B（+%s）/ 错尺复核 RED_AS_EXPECTED' % (
        nm, len(pl), len(al), format(len(pre), ','), format(len(cur), ','), format(len(app), ',')))

# ---------- ② 追加段正文级内容闸（与落地器同规，独立重跑） ----------
_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏，口令闸无法自证扫的是真口令'
sec = _secret.group(1)
for nm, txt in APPEND.items():
    for i, l in enumerate(txt.split('\n'), 1):
        assert chr(39) not in l, 'ABORT: %s 追加段第 %d 行含 ASCII 撇号：' % (nm, i) + l[:60]
        assert sec not in l, 'ABORT: %s 追加段含口令明文：' % nm + l[:60]
        assert l.count('`') % 2 == 0, 'ABORT: %s 追加段第 %d 行反引号不成对：' % (nm, i) + l[:80]
        if BS in l:
            assert ESP in l, 'ABORT: %s 追加段第 %d 行有意外反斜杠：' % (nm, i) + l[:80]
    stray = [(i + 1, l[:70]) for i, l in enumerate(txt.split('\n'))
             if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*', l) or re.search(r'%[sd]\b', l)]
    assert not stray, 'ABORT: %s 追加段有未插值占位符 %d 处：%s' % (nm, len(stray), stray[:3])
print('GATE 追加段两只：撇号 0 / 反斜杠只在点名的 Windows 路径行 / 反引号成对 / 占位符 0 / 口令明文 0')

# ---------- ③ 正文自述的「追加之前现读」逐格对 pre-image ----------
d_txt, n_txt = APPEND['20260926.md'], APPEND['done.md']
_pre = {'done.md': (rb(PRE_DON),), '20260926.md': (rb(PRE_DEV),)}
m = re.search(r'追加之前现读：`done\.md` \*\*(\d+) 行 / ([\d,]+) B\*\*、`dev_log/20260926\.md` \*\*(\d+) 行 / ([\d,]+) B\*\*', n_txt)
assert m, 'ABORT: done 追加段里那句「追加之前现读」形状不对，逐格对账无从下手'
claim = [int(m.group(1)), int(m.group(2).replace(',', '')), int(m.group(3)), int(m.group(4).replace(',', ''))]
actual = [rb(PRE_DON).count(b'\n'), len(rb(PRE_DON)), rb(PRE_DEV).count(b'\n'), len(rb(PRE_DEV))]
assert claim == actual, 'ABORT: 正文自述的追加前只数/字节 != pre-image 现读 %s vs %s' % (claim, actual)
print('PRE-CLAIM done 1456/291,804 + dev_log 97/10,687 逐格 == pre-image 现读（四格）')

# ---------- ④ 正文引用的现场态读数 vs 本遍现跑 ----------
fe_b, fe_l, fe_md5 = mb(FE)
fe_n = sum(1 for l in rd(FE).splitlines() if l.startswith('[错误类型]'))
rc_b, rc_l, rc_md5 = mb(REC)
rdm_b, rdm_l, rdm_md5 = mb(RDM)
def claims(pat, live, label, txts):
    """正文里所有该形状的读数都必须 == 本遍现跑；命中 0 只 = ABORT（不是"没写所以干净"）。"""
    hits = re.findall(pat, ''.join(txts))
    assert hits, 'ABORT: 追加段里找不到 %s 那一格（形状 %s）' % (label, pat)
    bad = [h for h in hits if tuple(h) != tuple(live)]
    assert not bad, 'ABORT: %s 正文读数与现跑不等 %s vs %s' % (label, bad, live)
    return len(hits)


n1 = claims(r'不是抄台账）：`.*?` = \*\*(\d+)\*\* 条 / \*\*(\d+)\*\* 行 / \*\*([\d,]+)\*\* B / md5 前 8 `([0-9a-f]{8})`',
            [str(fe_n), str(fe_l), format(fe_b, ','), fe_md5], 'FreqErr 全册现读', (d_txt, n_txt))
n2 = claims(r'`FreqErr\.md` \*\*(\d+) 条 / (\d+) 行 / ([\d,]+) B\*\*',
            [str(fe_n), str(fe_l), format(fe_b, ',')], 'FreqErr（done 225 那格）', (d_txt, n_txt))
n3 = claims(r'排查记录 \*\*([\d,]+) 行 / ([\d,]+) B / md5 前 8 `([0-9a-f]{8})`\*\*',
            [str(rc_l), format(rc_b, ','), rc_md5], '排查记录', (d_txt, n_txt))
n4 = claims(r'README\.md` 现读 \*\*([\d,]+) 行 / ([\d,]+) B / md5 前 8 `([0-9a-f]{8})`\*\*',
            [str(rdm_l), format(rdm_b, ','), rdm_md5], 'backups/README', (d_txt, n_txt))
print('LIVE-CLAIM FreqErr %d 条 / %d 行 / %s B / %s（%d 格）· 排查记录 %d 行 / %s B / %s（%d 格）· README %d 行 / %s B / %s（%d 格）全中' % (
    fe_n, fe_l, format(fe_b, ','), fe_md5, n1 + n2, rc_l, format(rc_b, ','), rc_md5, n3,
    rdm_l, format(rdm_b, ','), rdm_md5, n4))


# 五批台账：行号 + 只数逐格现跑
led = {}
for i, l in enumerate(rd(FE).splitlines(), 1):
    g = re.match(r'\*\*【([0-9: -]{19}) 落地｜R61 (第十[五六七八九]批) (\d+) 条】\*\*', l)
    if g:
        led[g.group(2)] = (i, int(g.group(3)), g.group(1))
assert sorted(led) == sorted(KINDS), 'ABORT: 五批台账现读不齐：%s' % sorted(led)
s_sum = sum(v[1] for v in led.values())
for k in KINDS:
    i, c, _ = led[k]
    assert ('第 %d 行（%s %d 条）' % (i, k, c)) in d_txt, 'ABORT: %s 的台账格与现跑不等（现跑 第 %d 行 / %d 条）' % (k, i, c)
assert ('五批合计 **%d** 条' % s_sum) in d_txt, 'ABORT: 五批合计 != 现跑求和（现跑 %d）' % s_sum
_ts = [led[k][2] for k in KINDS]
print('LEDGER 五批 %s = 第 %s 行 / 只数 %s / 合计 %d 条 · 时刻戳两端 %s ~ %s' % (
    '、'.join(KINDS), [led[k][0] for k in KINDS], [led[k][1] for k in KINDS], s_sum, _ts[0], _ts[-1]))

# ---------- ⑤ 第 16 代五字段 vs 载体（正文里的数字必须能被 carrier 逐字段对上） ----------
lx = rd(LCL)
def num(text, pat, label):
    g = re.search(pat, text)
    assert g, 'ABORT: 载体 %s 里读不到 %s（形状 %s）' % (label, label, pat)
    return g.group(1)
l_files = int(num(lx, r'staged files\s*=\s*(\d+)', 'r61c_local staged files'))
l_bytes = int(num(lx, r'staged files\s*=\s*\d+ \| bytes = (\d+)', 'r61c_local staged bytes'))
l_zip = int(num(lx, r'zip size/md5\s*=\s*(\d+)', 'r61c_local zip'))
l_md5 = num(lx, r'zip size/md5\s*=\s*\d+ ([0-9a-f]{32})', 'r61c_local zip md5')
l_agg = num(lx, r'LOCAL_AGGREGATE\s*=\s*([0-9a-f]{64})', 'r61c_local aggregate')
vx = rd(VRX)
r_files = int(num(vx, r'REMOTE_FILES=(\d+)', 'r61c_verify files'))
r_bytes = int(num(vx, r'REMOTE_BYTES=(\d+)', 'r61c_verify bytes'))
r_zip = int(num(vx, r'REMOTE_ZIP_SIZE=(\d+)', 'r61c_verify zip'))
r_md5 = num(vx, r'REMOTE_ZIP_MD5=([0-9a-f]{32})', 'r61c_verify zip md5')
r_forb = int(num(vx, r'REMOTE_FORBIDDEN=(\d+)', 'r61c_verify forbidden'))
r_agg = num(vx, r'REMOTE_AGGREGATE=([0-9a-f]{64})', 'r61c_verify aggregate')
assert (l_files, l_bytes, l_zip, l_md5, l_agg) == (r_files, r_bytes, r_zip, r_md5, r_agg), \
    'ABORT: 第 16 代五字段两侧不全等 %s vs %s' % ((l_files, l_bytes, l_zip, l_md5, l_agg), (r_files, r_bytes, r_zip, r_md5, r_agg))
rtx = rd(RT)
assert 'VERDICT=REMOTE_CARRIES_PLAINTEXT' in rtx, 'ABORT: 往返复核不是 REMOTE_CARRIES_PLAINTEXT'
root = num(rtx, r'Temp/(zsynctest\d+)/', 'roundtrip 解包根')
dx = rd(DLT)
chg = int(num(dx, r'changed_since_cutoff = (\d+)', 'cutoff changed'))
dele = int(num(dx, r'deleted_since_cutoff = (\d+)', 'cutoff deleted'))
newn = int(num(dx, r'new_since_cutoff\s*=\s*(\d+)', 'cutoff new'))
newlist = re.findall(r"'([^']+)'", num(dx, r'new_since_cutoff\s*=\s*\d+ \[(.*?)\]', 'cutoff new list'))
assert len(newlist) == newn, 'ABORT: new_since 名单只数 %d != 载体自述 %d' % (len(newlist), newn)
cand = int(num(dx, r'当前候选集\((\d+)\)', 'cutoff candidate'))
assert chg == 0 and dele == 0, 'ABORT: changed/deleted 非 0（%d/%d）⇒ "包 == 现状"不成立' % (chg, dele)
assert cand == l_files + newn, 'ABORT: 候选集等式不成立 %d != %d + %d' % (cand, l_files, newn)
assert 'VERDICT=LISTDIFF_EQUAL' in rd(LD), 'ABORT: 双向名单差集不是 LISTDIFF_EQUAL'
for lit in ('载荷 **%d 只 / %s B**' % (l_files, format(l_bytes, ',')),
            '包 **%s B / md5 `%s`**' % (format(l_zip, ','), l_md5),
            '`%s`' % l_agg,
            '`REMOTE_FORBIDDEN=%d`' % r_forb,
            '根 `%s`' % root,
            'changed_since_cutoff=%d' % chg,
            'new_since_cutoff=%d` 只' % newn,
            '等式 %d == %d + %d' % (cand, l_files, newn)):
    assert lit in d_txt, 'ABORT: dev_log 第 16 代那格里缺这句（载体现读值）：' + lit[:60]
for p in newlist:
    assert ("'%s'" % p) in dx, 'ABORT: new_since 名单里有只不在载体：' + p
    assert os.path.isfile(os.path.join(REPO, p.replace('/', os.sep))), 'ABORT: new_since 名单里有只不在盘上：' + p
    assert p.startswith('hardware/r61c_sync/evidence/'), 'ABORT: new_since 名单里有只不是本代自产取证件：' + p
dr_n = int(num(lx, r'dropped \(逐只点名\)\s*=\s*(\d+)', 'r61c_local dropped'))
dr_list = re.findall(r"'([^']+)'", num(lx, r'dropped \(逐只点名\)\s*=\s*\d+ \[(.*?)\]', 'r61c_local dropped list'))
assert len(dr_list) == dr_n, 'ABORT: drop 名单只数 %d != 载体自述 %d' % (len(dr_list), dr_n)
assert 'drop **%d 只**' % dr_n in d_txt, 'ABORT: dev_log 的 drop 只数 != 载体（现读 %d）' % dr_n
for p in dr_list:
    assert ('`%s`' % p) in d_txt, 'ABORT: drop 名单里有只没被正文点名：' + p
print('S16 五字段两侧全等（%d 只 / %s B / zip %s / md5 %s / agg %s…）· FORBIDDEN=%d · 根 %s · 等式 %d == %d + %d · drop %d 只逐只点名' % (
    l_files, format(l_bytes, ','), format(l_zip, ','), l_md5[:8], l_agg[:8], r_forb, root, cand, l_files, newn, dr_n))

# ---------- ⑤b 第 16 代取证只数 / 第十九批崩遍 / 派生崩点行号 —— 全部回到载体与盘上现读
PKR = one('r61c_paperwork_%s.txt' % stamp.split('_')[1], '落地遍载体')
pk = rd(PKR)
assert 'VERDICT=LANDED' not in pk, 'ABORT: 落地遍载体里竟含写盘后令牌（那它上一遍就没崩）'
cr_n = int(num(pk, r'非空载体 (\d+) 只', 'paperwork carrier 取证只数'))
assert '现读 **%d 只非空载体**' % cr_n in d_txt, 'ABORT: dev_log 的取证只数 != 落地遍载体（载体 %d）' % cr_n
crash19 = int(num(pk, r'第十九批崩遍 (\d+) 只', 'paperwork carrier 崩遍只数'))
auth19 = num(pk, r'权威遍 (\S+\.txt)', 'paperwork carrier 权威遍')
assert '崩遍 %d 只' % crash19 in d_txt and ('权威遍 `%s`' % auth19) in d_txt, \
    'ABORT: 第十九批崩遍/权威遍那格与落地遍载体不等（载体 %d / %s）' % (crash19, auth19)
assert 'VERDICT=LANDED rc=0' in rd(os.path.join(EV, auth19)), 'ABORT: 被点名的权威遍载体里没有写盘后令牌'
_dcr = one('derive_r61c_161508.txt', '派生崩遍载体')
assert 'Traceback' in rd(_dcr) and 'VERDICT=DERIVED' not in rd(_dcr), 'ABORT: 派生崩遍载体不像一次崩遍'
KEY_LN = int(num(rd(_dcr), r'derive_r61c\.py", line (\d+)', '崩遍 Traceback 行号'))
DSRC = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts', 'derive_r61c.py')
_dsrc = rd(DSRC).split('\n')
W_LN = [i + 1 for i, l in enumerate(_dsrc) if "open(dst, 'wb')" in l]
assert len(W_LN) == 1, 'ABORT: 派生器里写盘语句行号不唯一：%s' % W_LN
assert KEY_LN < W_LN[0], 'ABORT: 崩点行号 %d 不早于写盘行号 %d ⇒ "盘上零改动"这条不成立' % (KEY_LN, W_LN[0])
assert '崩点行号 %d 早于该文件里写盘语句的行号 %d' % (KEY_LN, W_LN[0]) in d_txt, \
    'ABORT: dev_log 那两句行号与现读不等（现读 %d / %d）' % (KEY_LN, W_LN[0])
print('S16-AUX 落地遍载体 %s（不含 LANDED）· 取证 %d 只 · 第十九批崩遍 %d 只 / 权威遍 %s 含令牌 · 崩点 %d < 写盘 %d' % (
    os.path.basename(PKR), cr_n, crash19, auth19, KEY_LN, W_LN[0]))


# ---------- ⑥ docs 快照「停在第几遍」那句 vs NOTE 现读 ----------
nx = rd(NOTE)
snap_at = num(nx, r'刷新时刻 ([0-9: -]{19})', 'NOTE 刷新时刻')
rows = len([l for l in nx.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
dirn = len([f for f in os.listdir(DOCD) if os.path.isfile(os.path.join(DOCD, f))])
assert dirn == rows + 1, 'ABORT: docs 目录只数 %d != 表格 %d + NOTE 自身' % (dirn, rows)
for lit in ('刷新时刻 %s' % snap_at, '表格 %d 行' % rows, '目录现读 %d 只' % dirn):
    assert lit in d_txt, 'ABORT: docs 那格与 NOTE 现读不等：' + lit
assert os.path.isfile(UPD) and os.path.basename(UPD) in d_txt, 'ABORT: 阶段摘要件不在盘上或未被点名'
for a in ('### 38.35', '### 38.36'):
    assert ('\n%s ' % a) in rd(REC) or ('\n%s' % a) in rd(REC), 'ABORT: 排查记录里没有 %s 这一节（正文引了它）' % a
print('DOCS NOTE 现读 %s / 表格 %d 行 / 目录 %d 只 = 表格 + NOTE · §38.35 §38.36 在册 · updates 件在册' % (
    snap_at, rows, dirn))

# ---------- ⑥b 第 16 代载荷的边界：谁在册、谁**不在**该代载荷里（汇报必须点名后者） ----------
NAMES = [l.strip() for l in rd(os.path.join(EV, 'r61c_local_names.txt')).split('\n') if l.strip()]
_cut = datetime.datetime.strptime(num(lx, r'CUTOFF_COPY_BEGIN\s*=\s*([0-9: -]{19})', 'cutoff'), '%Y-%m-%d %H:%M:%S')
for rel in ('dev_log/20260926.md', 'done.md', 'hardware/20260919_墨水屏点屏排查记录.md'):
    assert rel in NAMES, 'ABORT: 第 16 代名单里没有 ' + rel
_c36 = sorted(glob.glob(os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence', 'r61b_3836_*.txt')))
assert _c36, 'ABORT: §38.36 载体候选 0 只（命中 0 不是干净）'
_a36 = [p for p in _c36 if 'VERDICT=LANDED' in rd(p)]
assert len(_a36) == 1, 'ABORT: §38.36 权威遍不唯一（权威 %d / 候选 %d）' % (len(_a36), len(_c36))
P3836 = _a36[0]
_p36 = datetime.datetime.fromtimestamp(os.path.getmtime(P3836))
_rec_mt = datetime.datetime.fromtimestamp(os.path.getmtime(REC))
assert _rec_mt <= _cut, 'ABORT: 排查记录 mtime %s 晚于打包截止 %s ⇒ "§38.36 在该代载荷里"这句不成立' % (_rec_mt, _cut)
_dev_mt = datetime.datetime.fromtimestamp(os.path.getmtime(DEV))
assert _dev_mt > _cut, 'ABORT: dev_log mtime 早于截止 ⇒ 本遍 paperwork 竟进了第 16 代载荷（与本遍结论相反，先查时间戳）'
print('PAYLOAD 截止 %s：§38.36 落地遍 %s（%s）+ 排查记录 mtime %s ⇒ **在册**；本遍 paperwork 落 %s ⇒ **不在第 16 代载荷里**，随第 17 代入库' % (
    _cut.strftime('%H:%M:%S'), os.path.basename(P3836), _p36.strftime('%H:%M:%S'),
    _rec_mt.strftime('%H:%M:%S'), _dev_mt.strftime('%H:%M:%S')))

# ---------- ⑦ git 快照尺：只点名漂移，不据此判红、不就地改数 ----------
por = git('status', '--porcelain')
lines = [l for l in por.split('\n') if l]
pm = sum(1 for l in lines if l[:2] == ' M')
pq = sum(1 for l in lines if l[:2] == '??')
g = re.search(r'`git status --porcelain` = \*\*(\d+) 行\*\*（` M` (\d+) \+ `\?\?` (\d+)', n_txt)
assert g, 'ABORT: done 追加段里 porcelain 那句形状不对，无法点名漂移'
rec = (int(g.group(1)), int(g.group(2)), int(g.group(3)))
_landing = datetime.datetime.strptime(stamp, '%Y%m%d_%H%M%S')
_after = sorted(os.path.relpath(p, EV).replace(os.sep, '/') for p in glob.glob(os.path.join(EV, '*'))
                if os.path.isfile(p) and datetime.datetime.fromtimestamp(os.path.getmtime(p)) >= _landing)
print('GIT_SNAPSHOT 正文登记 %s · 本遍现跑 %d 行（` M` %d + `??` %d）· 差 %d 行' % (
    rec, len(lines), pm, pq, len(lines) - rec[0]))
print('GIT_DRIFT_EXPLAIN 落地时刻 %s 起 evidence/ 之后 %d 只新件（那时还没有本遍的载体）：%s' % (
    stamp, len(_after), '、'.join(_after[:6]) + ('…' if len(_after) > 6 else '')))
print('GIT_RULE porcelain 行数与文件只数是两把不同的尺（目录折叠行），且它是**快照**尺 ⇒ 本遍不据漂移判红，也不回头改正文那个数')

# ---------- ⑧ 结论落盘 ----------
_tt = _T0.strftime('%Y%m%d_%H%M%S')
out = os.path.join(EV, 'r61c_paperwork_verify_%s.txt' % _tt)
assert not os.path.exists(out), 'ABORT: 载体目标已存在 ' + out
body = (
    'R61c paperwork 独立复核遍，现跑于 %s（落地遍载体 r61c_paperwork_%s.txt，两只 pre-image 同戳）\n'
    '口径：本遍**不重跑落地器**（它的幂等门现在必红，重跑洗绿是禁止的），只拿 pre-image + 盘上现件把修好的三段式判据在真字节上执行一次，\n'
    '      并把追加段正文里的每一格读数分别对回 ①pre-image ②本遍现跑 ③第 16 代载体。\n\n'
    'PROVE 20260926.md  前缀 %d 行逐字等 / 追加 %d 行逐行等 / 后缀空 / %s -> %s B\n' % (
        _T0.strftime('%Y-%m-%d %H:%M:%S'), stamp,
        rb(PRE_DEV).count(b'\n'), rb(DEV).count(b'\n') - rb(PRE_DEV).count(b'\n'),
        format(len(rb(PRE_DEV)), ','), format(len(rb(DEV)), ',')) +
    'PROVE done.md       前缀 %d 行逐字等 / 追加 %d 行逐行等 / 后缀空 / %s -> %s B\n' % (
        rb(PRE_DON).count(b'\n'), rb(DON).count(b'\n') - rb(PRE_DON).count(b'\n'),
        format(len(rb(PRE_DON)), ','), format(len(rb(DON)), ',')) +
    'OLD_FORM 上一遍那把错尺（str 行表 vs bytes 行表）在同一段真字节上复核：两只都仍然 RED ⇒ 新尺有牙\n'
    'GATE 追加段：撇号 0 / 反斜杠只出现在点名的 Windows 路径行 / 反引号成对 / 未插值占位符 0 / 口令明文 0\n'
    'PRE-CLAIM 正文自述的追加前读数 done %d 行 %s B · dev_log %d 行 %s B == pre-image 现读（四格）\n' % (
        rb(PRE_DON).count(b'\n'), format(len(rb(PRE_DON)), ','), rb(PRE_DEV).count(b'\n'), format(len(rb(PRE_DEV)), ',')) +
    'LIVE-CLAIM FreqErr %d 条 / %d 行 / %s B / md5 %s · 排查记录 %d 行 / %s B / md5 %s · README %d 行 / %s B / md5 %s\n' % (
        fe_n, fe_l, format(fe_b, ','), fe_md5, rc_l, format(rc_b, ','), rc_md5, rdm_l, format(rdm_b, ','), rdm_md5) +
    'LEDGER 五批台账 第 %s 行 / 只数 %s / 合计 %d 条 == 正文逐格\n' % (
        [led[k][0] for k in KINDS], [led[k][1] for k in KINDS], s_sum) +
    'S16 五字段两侧全等 %d 只 / %s B / zip %s / md5 %s / 聚合 %s / FORBIDDEN=%d / 根 %s / 等式 %d == %d + %d（changed %d, deleted %d, LISTDIFF_EQUAL）\n' % (
        l_files, format(l_bytes, ','), format(l_zip, ','), l_md5, l_agg, r_forb, root, cand, l_files, newn, chg, dele) +
    'S16-AUX 落地遍载体 %s（其内无 LANDED 令牌）· 该遍自述取证 %d 只 · 第十九批崩遍 %d 只 / 权威遍 %s（其内含 LANDED）· 派生崩点行号 %d < 写盘行号 %d\n' % (
        os.path.basename(PKR), cr_n, crash19, auth19, KEY_LN, W_LN[0]) +
    'PAYLOAD 打包截止 %s：§38.36 载体 %s（%s）+ 排查记录 mtime %s ⇒ 在册；本遍 paperwork（dev_log/done）mtime %s ⇒ **不在第 16 代载荷里**，随第 17 代入库\n' % (
        _cut.strftime('%Y-%m-%d %H:%M:%S'), os.path.basename(P3836), _p36.strftime('%H:%M:%S'),
        _rec_mt.strftime('%H:%M:%S'), _dev_mt.strftime('%H:%M:%S')) +
    'DOCS NOTE %s / 表格 %d 行 / 目录 %d 只 · §38.35 §38.36 在册 · updates 件在册\n' % (snap_at, rows, dirn) +
    'GIT_SNAPSHOT 正文登记 %s / 本遍现跑 %d 行（` M` %d + `??` %d）⇒ 快照尺漂移 %d 行，来源见 stdout 点名，本遍不据此判红、不回头改正文\n' % (
        rec, len(lines), pm, pq, len(lines) - rec[0]) +
    'VERDICT=VERIFIED rc=0\n')
io.open(out, 'wb').write(body.encode('utf-8'))
chk = rb(out)
assert chk == body.encode('utf-8') and b'VERDICT=VERIFIED rc=0' in chk, 'ABORT: 载体回读不等'
print('CARRIER %s（%d B / md5 前 8 %s）' % (os.path.relpath(out, REPO).replace(os.sep, '/'), len(chk),
                                        hashlib.md5(chk).hexdigest()[:8]))
_p2 = [l for l in git('status', '--porcelain').split('\n') if l]
print('SELF_POLLUTE 落本遍载体后 porcelain 复跑 = %d 行（` M` %d + `??` %d），比落盘前 %d 行多 %d ⇒ 检查动作自己污染被检查物（(60) 那一族），登记不判红' % (
    len(_p2), sum(1 for l in _p2 if l[:2] == ' M'), sum(1 for l in _p2 if l[:2] == '??'), len(lines), len(_p2) - len(lines)))
print('VERDICT=VERIFIED rc=0')
