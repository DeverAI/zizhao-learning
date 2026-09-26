# R55 paperwork 落地器（任务 #182）：done 201/202 + todo 第十六遍 + dev_log 追加 + updates 新建 + 烧录须知现场态。
# 为什么在 hardware/ 而不是 hardware/ht305_sync/scripts/：gen 24 已冻成末版，此后任何一只文件落进归档都会把
# verify_manifest 的 UNLISTED 顶成非 0（口径见排查记录 §38.19 ④）。
# 红线：正文里每个数字都从载体或现跑命令读，载体缺失即 ABORT；正文不写反斜杠；落盘前过一道明文凭据闸。
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

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
EV = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
DONE = os.path.join(REPO, 'done.md')
TODO = os.path.join(REPO, 'todo.md')
DEVLOG = os.path.join(REPO, 'dev_log', '20260924.md')
NOTE = os.path.join(REPO, 'hardware', '烧录须知.md')
SRC_MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
UPD_REL = 'updates/20260924_墨水屏R55第13代同步与gen22-24三代.md'
UPD = os.path.join(REPO, *UPD_REL.split('/'))
BUILD_BIN = r'C:/esp/zproj/build/zizhao_esp32s3.bin'
ARCH_BIN = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin')
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ev(name):
    p = os.path.join(EV, name)
    assert os.path.isfile(p), 'ABORT: 取证件不存在，拒绝凭记忆写数：' + name
    return open(p, encoding='utf-8', errors='replace').read()


def g(name, pat, grp=1):
    m = re.search(pat, ev(name))
    assert m, 'ABORT: %s 里找不到 %r' % (name, pat)
    return m.group(grp)


def hard(name):
    p = os.path.join(REPO, 'hardware', name)
    assert os.path.isfile(p), 'ABORT: 归档外载体缺失 ' + name
    return open(p, encoding='utf-8').read()


def git(*a):
    p = subprocess.run(('git',) + a, cwd=REPO, capture_output=True)
    assert p.returncode == 0, 'ABORT: git 失败 ' + ' '.join(a) + p.stderr.decode('utf-8', 'replace')[:200]
    return p.stdout.decode('utf-8', 'replace')


def money(x):
    return '{:,}'.format(int(x))


def md5_of(p):
    assert os.path.isfile(p), 'ABORT: 该读 md5 的文件不存在 ' + p
    b = open(p, 'rb').read()
    return hashlib.md5(b).hexdigest(), len(b)


def man_row(rel):
    for ln in open(os.path.join(REPO, 'hardware', 'ht305_sync', 'MANIFEST.txt'), encoding='utf-8').read().splitlines():
        f = ln.split('\t')
        if len(f) == 5 and f[0] == rel:
            return int(f[1]), f[2]
    raise SystemExit('ABORT: 末版清单里没有 %s' % rel)


# ---------------- 现跑：现场态 ----------------
rev = git('rev-list', '--count', 'origin/main..HEAD').strip()
assert rev.isdigit(), 'ABORT: rev-list 读数不是数字'
st = [l for l in git('-c', 'core.quotePath=false', 'status', '--porcelain').splitlines() if l.strip()]
mod_n = len([l for l in st if l[:2] == ' M'])
un_n = len([l for l in st if l[:2] == '??'])
main_dirty = [l[3:] for l in st if l[:2] == ' M' and '/main/' in l]
pp = subprocess.run((sys.executable, '-m', 'serial.tools.list_ports'), cwd=REPO, capture_output=True)
assert pp.returncode == 0, 'ABORT: 串口枚举失败'
ports = sorted(set(re.findall(r'(?m)^(COM\d+)', pp.stdout.decode('utf-8', 'replace'))))
assert 'COM14' not in ports, 'ABORT: COM14 又出现了 ⇒ 本批"没碰串口"的叙述要重写'
bin_md5, bin_bytes = md5_of(BUILD_BIN)
arc_md5, arc_bytes = md5_of(ARCH_BIN)
assert bin_md5.startswith('fb32168a'), 'ABORT: 构建目录那只不再是待烧指纹，先查清是谁重建了'
assert arc_md5.startswith('4842a3a0'), 'ABORT: 归档 bin 变了，"板上=归档"那句要重写'
logs = [f for f in os.listdir(os.path.join(REPO, 'hardware'))
        if ('真机' in f or 'COM14' in f) and '官方例程' not in f]
power_n = len(logs)
official_n = len([f for f in os.listdir(os.path.join(REPO, 'hardware')) if '官方例程' in f])

# ---------------- 现读：冻结链 / 门 / 复核 ----------------
genlog = [l.split('\t') for l in ev('manifest_gen_log.txt').splitlines()
          if re.match(r'^\d\d-\d\d \d\d:\d\d:\d\d\t\d+\t', l)]
n22, b22, bom22 = (int(x) for x in genlog[-3][1:])
n23, b23, bom23 = (int(x) for x in genlog[-2][1:])
n24, b24, bom24 = (int(x) for x in genlog[-1][1:])
mlines = open(os.path.join(REPO, 'hardware', 'ht305_sync', 'MANIFEST.txt'), encoding='utf-8').read().splitlines()
mtail = [l.split('\t') for l in mlines if l.startswith(('TOTAL\t', 'TOTAL_BYTES\t', 'BOM_FILES\t'))]
assert len(mtail) == 3 and int(mtail[0][1]) == n24 and int(mtail[1][1]) == b24, 'ABORT: 末版清单与代次日志末行不同代'
fs22 = g('cred_gate_recheck_123427.txt', r'FILES_SCANNED=(\d+)')
fs23 = g('cred_gate_recheck_123653.txt', r'FILES_SCANNED=(\d+)')
fs24 = g('cred_gate_recheck_125333.txt', r'FILES_SCANNED=(\d+)')
for fs, n in ((fs22, n22), (fs23, n23), (fs24, n24)):
    assert int(fs) - 1 == int(n), 'ABORT: 门扫数-1==TOTAL 有一代不成立（%s/%s）' % (fs, n)

v22_rows = g('r55_verify_manifest_gen22_stale.txt', r'ROWS=(\d+)')
v22_mis = g('r55_verify_manifest_gen22_stale.txt', r'MISMATCH=(\d+)')
v22_mss = g('r55_verify_manifest_gen22_stale.txt', r'MISMATCH=\d+  MISSING=(\d+)')
v22_unl = g('r55_verify_manifest_gen22_stale.txt', r'UNLISTED\(盘上有、清单没记\)=(\d+)')
v22_ver = g('r55_verify_manifest_gen22_stale.txt', r'VERDICT=(\w+)')
v22_hdr = g('r55_verify_manifest_gen22_stale.txt', r'现跑于 (.+?)；')
assert v22_rows == str(n22) and v22_ver == 'MANIFEST_STALE'
vc1 = os.path.join(REPO, 'hardware', 'verify_manifest_0924123702.txt')
vc2 = os.path.join(REPO, 'hardware', 'verify_manifest_0924125339.txt')
for pth in (vc1, vc2):
    assert os.path.isfile(pth), 'ABORT: 终态复核载体缺失 ' + pth
t1, t2 = open(vc1, encoding='utf-8').read(), open(vc2, encoding='utf-8').read()
v1_rc, v2_rc = re.search(r'VERIFY_RC=(\d)', t1).group(1), re.search(r'VERIFY_RC=(\d)', t2).group(1)
v1_ver, v2_ver = re.search(r'VERDICT=(\w+)', t1).group(1), re.search(r'VERDICT=(\w+)', t2).group(1)
assert (v1_rc, v1_ver) == ('1', 'MANIFEST_STALE') and (v2_rc, v2_ver) == ('0', 'MANIFEST_STILL_TRUE'), \
    'ABORT: 两遍终态复核形状与叙述不符'

# ---------------- 现读：§38.18 落地器 + 两把补尺 + README 两落地器 ----------------
la = ev('r55_land_A.txt')
la_in, la_out = g('r55_land_A.txt', r'ENTER_AT (.+)'), g('r55_land_A.txt', r'EXIT_AT  (.+)')
la_ports = g('r55_land_A.txt', r'COMPORTS ([\w,]+)')
la_rec = re.search(r'REC_BEFORE lines=(\d+) bytes=(\d+)  REC_AFTER lines=(\d+) bytes=(\d+)', la)
la_frq = re.search(r'FREQ_BEFORE ets=(\d+) lines=(\d+)\s+DISK_ERRTYPES=(\d+) DISK_LINES=(\d+)', la)
la_mem = re.search(r'MEMORY_LEN=(\d+) CR=(\d+) LF=(\d+)', la)
corr_line, corr_at = None, None
for _i, _l in enumerate(open(FREQ, encoding='utf-8', newline='').read().split('\r\n')):
    if '上一格（R55 第一遍台账）' in _l:
        corr_line = _i + 1
        corr_at = re.search(r'订正｜(.+?)】', _l).group(1)
assert corr_line and corr_at, 'ABORT: FreqErr 里那只订正行找不到 ⇒ ②那段没证据'
rc1_at, rc1_scope = g('r55_cred_recount.txt', r'CRED_RECOUNT_AT=(.+)'), g('r55_cred_recount.txt', r'SCOPE=(.+)')
rc1_leak = g('r55_cred_recount.txt', r'FETCH_NAME_LEAKED_INTO_REPO=(\d+)')
rc2_at = g('r55_cred_recount_2.txt', r'CRED_RECOUNT_AT=(.+)')
rc2_scope = g('r55_cred_recount_2.txt', r'= (\d+) 只，逐只点名')
rc2_hits = g('r55_cred_recount_2.txt', r'TOTAL_HITS=(\d+)')
rc2_pos = g('r55_cred_recount_2.txt', r'POSITIVE_CONTROL_IN_MEMORY_HITS=(\d+)')
rc2_in = g('r55_cred_recount_2.txt', r'FETCH_NAME_IN_REPO_INSIDE_SYNC_SCOPE=(\d+)')
rc2_out = g('r55_cred_recount_2.txt', r'FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=(\d+)')
rc2_names = g('r55_cred_recount_2.txt', r'NAMES_SCANNED=(\d+)')
assert rc2_hits == '0' and rc2_out == '0' and rc2_pos == '1', 'ABORT: 明文复扫不是 CLEAN'
pb_at = g('r55_parse_check_2.txt', r'CHKB_AT=(.+)')
pb_n = g('r55_parse_check_2.txt', r'SCOPE=本代冻结后被改写的工具 (\d+) 只')
pa_at = g('r55_parse_check.txt', r'CHK_AT=(.+)')
pa_src = g('r55_parse_check.txt', r'SRC_LINES=(\d+)')
assert g('r55_parse_check_2.txt', r'VERDICT=(\S+)') == 'TOOLS_PARSE_CLEAN'
lr1_at = g('r55_land_readme.txt', r'LAND_README_AT=(.+)')
lr1_b = g('r55_land_readme.txt', r'README_BYTES (\d+) ->')
lr1_a = g('r55_land_readme.txt', r'README_BYTES \d+ -> (\d+)')
lr2_at = g('r55_land_readme_2.txt', r'LAND_README2_AT=(.+)')
lr2_edits = g('r55_land_readme_2.txt', r'EDITS=(\d+) 项')
lr2_a = g('r55_land_readme_2.txt', r'README_AFTER_BYTES=(\d+)')
rm_bytes, rm_md5 = man_row('README.md')
DELTA = rm_bytes - int(lr2_a)
assert DELTA == 9, 'ABORT: README 净差不再是 +9 B ⇒ ③那段分解要重写'

fe = hard('r55_freqerr2.txt')
fe_at = re.search(r'FREQERR2_AT=(.+)', fe).group(1)
fe_kb, fe_ka = re.search(r'KIND_COUNT=(\d+)->(\d+)', fe).groups()
fe_lb, fe_la = re.search(r'WC_L=(\d+)->(\d+)', fe).groups()
fe_bb, fe_ba, fe_ap = re.search(r'DOC_BEFORE_BYTES=(\d+) DOC_AFTER_BYTES=(\d+) APPENDED=(\d+)', fe).groups()
assert int(fe_ka) - int(fe_kb) == 6
ck = hard('r55_sec38_19_check.txt')
ck_at = re.search(r'SEC3819_CHECK_AT=(.+)', ck).group(1)
ck_n = re.search(r'CHECKS=(\d+)', ck).group(1)
ck_ver = re.search(r'VERDICT=(\S+)', ck).group(1)
assert ck_ver == 'SEC38_19_TRUE', 'ABORT: §38.19 独立复核不是 TRUE'
doc_b = re.search(r'DOC=(.+?) bytes=(\d+) md5=([0-9a-f]{32}) wc_l=(\d+)', ck)
sec_line = int(re.search(r'SECTION_LINES=(\d+)\.\.', ck).group(1))

# ---------------- 现读：本批已落盘的排查记录 / FreqErr 现状 ----------------
doc_t = open(DOC, encoding='utf-8', newline='').read()
assert int(doc_b.group(2)) == len(doc_t.encode('utf-8')), 'ABORT: 排查记录在复核器读完之后又被改过'
assert doc_t.count('\n') == int(doc_b.group(4)) and doc_t.count('\r\n') == doc_t.count('\n')
laten = re.search(r'潜伏了 (\d+) 个世代', doc_t).group(1)
_lines = doc_t.split('\r\n')
assert _lines[sec_line - 1].startswith('### 38.19'), 'ABORT: §38.19 不在复核器登记的那一行'
bullets = len([l for l in _lines[sec_line - 1:sec_line + 10] if l.startswith('- ')])
assert bullets == 9, 'ABORT: §38.19 要点行数与复核器读的不符（现 %d）' % bullets
frq_t = open(FREQ, encoding='utf-8', newline='').read()
frq_lines = frq_t.count('\n')
frq_ets = sum(1 for l in frq_t.split('\r\n') if l.startswith('[错误类型]'))

# ---------------- 现读：同步侧 ----------------
loc_files, loc_bytes = re.search(r'staged files\s+= (\d+) \| bytes = (\d+)', ev('r55_local.txt')).groups()
loc_listed, loc_dupes = re.search(r'git-listed \(dupes\)  = (\d+) / dupes = (\d+)', ev('r55_local.txt')).groups()
loc_sel, loc_fail = re.search(r'selected            = (\d+) \| copy failures = (\d+)', ev('r55_local.txt')).groups()
loc_plain = g('r55_local.txt', r'plaintext in staging= (\d+)')
zip_ent, zip_utf = re.search(r'zip entries         = (\d+) \| utf8-flagged = (\d+)', ev('r55_local.txt')).groups()
zip_size, zip_md5 = re.search(r'zip size/md5        = (\d+) ([0-9a-f]{32})', ev('r55_local.txt')).groups()
loc_agg = g('r55_local.txt', r'LOCAL_AGGREGATE     = ([0-9a-f]{64})')
cut_copy = g('r55_local.txt', r'CUTOFF_COPY_BEGIN   = (.+)')
cut_zip = g('r55_local.txt', r'CUTOFF_ZIP_MADE     = (.+)')
probe_at = g('r55_probe.txt', r'PROBE_AT (.+)')
probe_te = g('r55_probe.txt', r'TARGET_EXISTS=(\w+)')
desk = [l.split('\t')[1] for l in ev('r55_probe.txt').splitlines() if l.startswith('DESKTOP\t')]
desk_r = [d for d in desk if re.search(r'_r\d+(_final)?$', d.split('.')[0])]
ver_at = g('r55_verify.txt', r'REMOTE_AT=(.+)')
ver_md5 = g('r55_verify.txt', r'REMOTE_ZIP_MD5=([0-9a-f]{32})')
ver_size = g('r55_verify.txt', r'REMOTE_ZIP_SIZE=(\d+)')
ver_ok = g('r55_verify.txt', r'EXTRACT_OK=(\w+)')
ver_files, ver_bytes, ver_forb = g('r55_verify.txt', r'REMOTE_FILES=(\d+)'), g('r55_verify.txt', r'REMOTE_BYTES=(\d+)'), g('r55_verify.txt', r'REMOTE_FORBIDDEN=(\d+)')
ver_agg = g('r55_verify.txt', r'REMOTE_AGGREGATE=([0-9a-f]{64})')
ver_done = g('r55_verify.txt', r'REMOTE_DONE_AT=(.+)')
assert ver_md5 == zip_md5 and ver_agg == loc_agg and ver_files == loc_files and ver_bytes == loc_bytes
assert int(ver_size) == int(zip_size), 'ABORT: 两侧包大小不同值'
rt1_at, rt1_rc = g('r55_roundtrip.txt', r'R55_ROUNDTRIP_AT=(.+)'), g('r55_roundtrip.txt', r'SCP_RC=(\d+)')
rt2_at = g('r55_roundtrip_2.txt', r'R55_ROUNDTRIP_AT=(.+)')
rt2_rc = g('r55_roundtrip_2.txt', r'SCP_ATTEMPT=1 RC=(\d+)')
rt2_bytes, rt2_md5 = re.search(r'REMOTE_BYTES=(\d+) md5=([0-9a-f]{32})', ev('r55_roundtrip_2.txt')).groups()
rt2_eq = g('r55_roundtrip_2.txt', r'BYTE_EQUAL_TO_WORKTREE=(\w+)')
rt2_hits = g('r55_roundtrip_2.txt', r'PROV_PASS_HITS_REMOTE=(\d+)')
rt2_ver, rt2_end = g('r55_roundtrip_2.txt', r'VERDICT=(\S+)'), g('r55_roundtrip_2.txt', r'RAN_END_AT=(.+)')
ld_at = g('r55_listdiff.txt', r'现跑于 (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)')
ld_local, ld_remote = re.search(r'LOCAL_LINES=(\d+) REMOTE_LINES=(\d+)', ev('r55_listdiff.txt')).groups()
ld_only_l, ld_only_r = g('r55_listdiff.txt', r'ONLY_IN_LOCAL=(\d+)'), g('r55_listdiff.txt', r'ONLY_IN_REMOTE=(\d+)')
ld_eol = re.search(r'EOL  LOCAL bytes=(\d+) lines=(\d+) CRLF=(\d+) bareLF=(\d+)', ev('r55_listdiff.txt'))
ld_same = g('r55_listdiff.txt', r'identical[^=]*= (\d+)')
ld_chg, ld_new = g('r55_listdiff.txt', r'changed_since_cutoff = (\d+)'), g('r55_listdiff.txt', r'new_since_cutoff     = (\d+)')
ld_cand, ld_ver = g('r55_listdiff.txt', r'当前候选集\((\d+)\)'), g('r55_listdiff.txt', r'VERDICT=(\S+)')
assert ld_ver == 'LISTDIFF_EQUAL' and int(ld_only_l) == 0 and int(ld_only_r) == 0
assert int(loc_sel) + int(ld_new) == int(ld_cand), 'ABORT: 四桶并集与"包内 + 截止后新增"不再自洽'

todo_t = open(TODO, encoding='utf-8', newline='').read()
assert todo_t.count('\n') == todo_t.count('\r\n'), 'ABORT: todo.md 行尾已混杂'
todo_lines = todo_t.count('\r\n')
ids = re.findall(r'(?m)^- \[ \] (\d+)', todo_t)
unchecked = ' '.join(ids)
done_t = open(DONE, encoding='utf-8', newline='').read()
assert done_t.count('\r\n') == 0, 'ABORT: done.md 不是纯 LF'
done_sec = re.findall(r'(?m)^## ([一二三四五六七八九十百]+)、', done_t)[-1]
assert int(re.findall(r'(?m)^- \[[ x]\] (\d+)', done_t)[-1]) == 200, 'ABORT: done.md 末条不是 200 ⇒ 编号要重排'
assert not os.path.exists(UPD), 'ABORT: updates 那只已存在 ⇒ 不覆写（本轮应新建）'
FULLW = sum(1 for l in todo_t.split('\r\n') if l.count('（') != l.count('）'))
HALF = sum(1 for l in todo_t.split('\r\n') if l.count('(') != l.count(')'))

# ================= done.md 201 / 202 =================
D201 = f'''
- [x] 201 **R55 前半批 = 排查记录 §38.18（把"只落在 TEMP 的取证"补进仓库）+ 第 13 代 ht305 全量同步 `r55final` + 归档链 gen 22 **假红** / gen 23 **跑绿了却没载体**（{la_in} §38.18 落盘 → {corr_at} FreqErr 台账订正 → {cut_copy} 截止拷贝 → {cut_zip} 建包 → {probe_at} 上传前探测 → {ver_done} 远端解包校验 → {rt1_at} 往返首跑 `SCP_RC={rt1_rc}` → {rt2_at} 重跑绿 → {ld_at} 两把差集尺 → {genlog[-3][0]} gen 22 → {genlog[-2][0]} gen 23；**没烧录、没碰串口、没 push、屏侧零字节**）**（09-24 12:0x~12:3x；任务 #175 / #178 / #179）
  ① **§38.18 落地（{la_in}~{la_out}，载体 `evidence/r55_land_A.txt`）**：排查记录 {la_rec.group(1)} → **{la_rec.group(3)} 行 / {money(la_rec.group(2))} → {money(la_rec.group(4))} B**，纯 CRLF 未破、新增节 `### 38.18` = 1；`FreqErr.md` 该遍登记 {la_frq.group(1)}→{la_frq.group(3)} 条，**盘上实测 {la_frq.group(3)} 条 / {la_frq.group(4)} 行** ⇒ 它自述的"之后行数"少 1（见②）；同一次调用还核了项目记忆索引 `MEMORY.md` = {la_mem.group(1)} B / CR **{la_mem.group(2)}** / LF {la_mem.group(3)} ⇒ 上一代"肉眼看不见的 CR"确认已消失。该遍串口枚举（同一载体）= `{la_ports}` ⇒ **COM14 不在**。
  ② **那一处"少 1"由订正句收尾、不就地改数**：`fix_r55_ledger.py` 于 **{corr_at}** 在 `FreqErr.md` 追加一行（现读第 **{corr_line}** 行），把 {la_frq.group(4)} 与盘上那一遍的独立回读值对齐；根因**不是** R54 那条"没算台账行自身"（那次已修对），而是**台账写完后的"行尾闭合"那一步在计数之后执行** ⇒ 补的那一只换行没进任何一次计数。错误类型那一对（{la_frq.group(1)}→{la_frq.group(3)}）自始至终无误，漂的只有行数。
  ③ **第 13 代同步（截止 {cut_copy} 拷贝 → {cut_zip} 建包）**：载荷 **{loc_files} 只 / {money(loc_bytes)} B**（`git-listed {loc_listed} / dupes {loc_dupes}`、`selected {loc_sel} | copy failures {loc_fail}` 三道前置闸现量），包 **{money(zip_size)} B / md5 `{zip_md5}`**、zip 条目 {zip_ent}（UTF-8 标志 {zip_utf} 只）；`plaintext in staging = {loc_plain}` 只 = `provision_ap.c`，按既有口径**随包上 ht305、不入库**。远端 {ver_at}~{ver_done}：`REMOTE_ZIP_SIZE={money(ver_size)} / REMOTE_ZIP_MD5` 与本地逐字同值、`EXTRACT_OK={ver_ok}`、`REMOTE_FILES={ver_files} / REMOTE_BYTES={money(ver_bytes)} / REMOTE_FORBIDDEN={ver_forb}`、聚合 sha256（64 字符全长）`{ver_agg[:8]}…` 两侧同值；解包根 `zsynctest15`，**一根只喂一代**。
  ④ **上传前探测 = 零删除的前置**：{probe_at} `TARGET_EXISTS={probe_te}` ⇒ 本代包第一次落盘就是干净的；同一次调用列全桌面 = **{len(desk)} 项**，其中 r 系列同步包 **{len(desk_r)} 只并存**（含 1 只已被冠 `SUPERSEDED-` 前缀的 tar）⇒ 本轮**没有覆盖动作、也没有删除动作**。
  ⑤ **往返那一步首跑是红的**：{rt1_at} `SCP_RC={rt1_rc}`（原件留 `evidence/r55_roundtrip.txt`，**失败那次的读数不作数**）→ {rt2_at} 重跑 `RC={rt2_rc}`：两侧 **{money(rt2_bytes)} B / md5 `{rt2_md5[:8]}…`** 同值、`BYTE_EQUAL_TO_WORKTREE={rt2_eq}`、`PROV_PASS_HITS_REMOTE={rt2_hits}` ⇒ `VERDICT={rt2_ver}`（{rt2_end}）。登记**事实**不是事故：服务器副本一直带明文、本机 `git grep HEAD` 仍 0 ⇒ **绝不 `git push`**，ht305 任何一份都**不能当回滚源**。
  ⑥ **两把差集尺（{ld_at}）**：名单尺 `LOCAL_LINES={ld_local} / REMOTE_LINES={ld_remote} / ONLY_IN_LOCAL={ld_only_l} / ONLY_IN_REMOTE={ld_only_r}`，且这段**之前**先落 EOL 前置读数（LOCAL `{ld_eol.group(1)} B / {ld_eol.group(2)} 行 / CRLF={ld_eol.group(3)} / bareLF={ld_eol.group(4)}` ⇒ 两侧先归一再比，(56) 那条本代兑现）；内容尺 **{ld_same} 只 identical + {ld_chg} 只 `changed_since_cutoff`（往返脚本自己 = 派生时刻差）+ {ld_new} 只 `new_since_cutoff`（截止之后才进仓库的取证件）**，四桶并集 == 当前候选集 {ld_cand} ⇒ `SELF_CHECK=PASS / VERDICT={ld_ver}`。
  ⑦ **归档链本批前两手：一只假红、一只"跑绿了没证据"**：gen 22 = {fs22} 只门（`{genlog[-3][0]}` 前 15 秒，`PROV_PASS`/SSH 两计数 0、`VERDICT=CLEAN`）→ {v22_hdr} 清单 `TOTAL={n22}`（关系式 `{fs22} − 1 = {n22}` ✓）→ `verify_manifest.py` 裁决 **{v22_ver}**，而同一行 `ROWS={v22_rows} / MISMATCH={v22_mis} / MISSING={v22_mss} / UNLISTED={v22_unl}`、汇总三字段逐项 OK ⇒ 根因 = 清单头部 **{v22_hdr}** 与代次日志 **{genlog[-3][0]}** 跨秒：`gen_manifest.py` 一次运行取了**两只 `now()`**，中间隔着 {n22} 只文件的哈希遍历。该判据自 gen 9 就在 ⇒ **潜伏 {laten} 个世代**才第一次咬人（只在跨秒那一瞬才假）。假红原件入库 `evidence/r55_verify_manifest_gen22_stale.txt`，**不重跑洗绿**；修法 = 源头只取一次时刻 + verifier 把**判决**与**展示**分家。gen 23 = {fs23} 只门 → {genlog[-2][0]} `TOTAL={n23}`（`{fs23} − 1 = {n23}` ✓）→ 复核 `rc=0`，**但那一步当时没有任何载体**（裁决只打在 stdout）⇒ 12:46 补跑的复核对 gen 23 只能给 `VERIFY_RC={v1_rc} / VERDICT={v1_ver}`（`hardware/verify_manifest_0924123702.txt`，{money(os.path.getsize(vc1))} B）⇒ 新规：**"已跑完"必须同时给出 `rc` 与载体文件名，且载体由工具自己在同一次运行里落盘**。
  ⑧ **本条没做（点名）**：没烧录、没碰串口、没接电池、没短接 ⇒ §38.13 那两行判据样本数仍 **0**、屏亮 0 次肉眼确认 ⇒ **不播提示音**；`esp_gpio_hold_en()` 故意仍未加；**未 `git push`**、零历史重写；gen 24 末版、明文复扫补尺、工具体检补尺、README 第二落地器、§38.19、FreqErr 第二遍、独立复核器、提交轮 #9、docs 第九遍、backups 第九次读数、项目记忆、mindog 第二路、空上下文复查**全部排在本条之后**；本轮**零删除**（`%TEMP%` 那批带明文的抓回件仍在，不入库也不删）。
'''

D202 = f'''
- [x] 202 **R55 尾巴批 = 两把"本代欠、本代还"的补尺 + gen 24 **末版** + §38.19 + `FreqErr.md` 第二遍 {int(fe_ka) - int(fe_kb)} 条 + 一只事后补的独立复核器（{rc1_at} 首跑口径错 → {rc2_at} 明文复扫补跑 → {pb_at} 工具体检补跑 → {lr1_at} README 第一落地器 → {lr2_at} 第二落地器 → {fs24} 只门 → {genlog[-1][0]} gen 24 末版 → {fe_at} FreqErr → {ck_at} 复核器 → {RUN_AT} 本条落笔；**没烧录、没碰串口、没 push、屏侧零进展**）**（09-24 12:3x~13:3x；任务 #181 / #182）
  ① **补尺一 = 明文复扫：首跑那遍造了一把看不见的尺**：{rc1_at} 第一遍（`evidence/r55_cred_recount.txt`）口径 "{rc1_scope}"，其 `FETCH_NAME_LEAKED_INTO_REPO={rc1_leak}` 之所以像脏，是因为**它把"声明该名的脚本自己"静默排除在外**；修法不是改结论而是**换分桶**：{rc2_at} 第二遍（**{rc2_scope}** 只逐只点名、不截断）⇒ `TOTAL_HITS={rc2_hits}` + 内存阳性对照 `{rc2_pos}`（样本不落盘）+ 抓回件文件名按**半径**分桶（同步目录内 {rc2_in} 只按构造合法 / 目录外 {rc2_out} 只）+ `NAMES_SCANNED={rc2_names}` ⇒ `VERDICT=CLEAN`；**首跑原件不覆盖**，由新载体的 `PRIOR_ATTEMPT` / `PRIOR_VERDICT` 点名。
  ② **补尺二 = 工具体检，覆盖面按"本代真改过什么"重算**：第一遍 {pa_at} 只查 `scripts/r55_upload.ps1`（{pa_src} 行、`FIRST3=239,187,191` ⇒ BOM 在、`PARSE_ERRORS=0`、`REMOVE_ITEM_HITS=0`）⇒ 对 12:37 之后被改写的 `.py` 工具**零覆盖**；{pb_at} 第二遍补 **{pb_n} 只**（`verify_manifest.py` / `gen_manifest.py` / `r55_cred_recount.py`）逐只 `ast.parse` OK + 阳性对照（同尺必须对已知坏字符串抛 `SyntaxError`）⇒ `TOOLS_PARSE_CLEAN`。**不在归档目录里用 `py_compile`**（它落 `.pyc`，`gen_manifest.py` 见派生字节即 ABORT）。
  ③ **README 两个落地器 + 一个"自述值被自己推翻"**：第一遍 {lr1_at}（`{money(lr1_b)} → {money(lr1_a)} B`、纯 LF、`PURE_INSERT=PASS`、表不动）；第二遍 {lr2_at} 落 **{lr2_edits}** 处编辑（首行轮数 / 两套序数 / gen 22~24 三格 / 叙述两段 / "本代没做"整条改写 / 远端清理轮数 + `zsynctest15` + 第四遍桌面探测），它自述 `README_AFTER_BYTES={money(lr2_a)}`；**写完我自己回读**又抓到三处排版缺陷（载体指针缺目录前缀、日期写了两遍、表格那格缺日期）⇒ 就地三笔订正后，**末版清单里的权威值 = {money(rm_bytes)} B / md5 `{rm_md5[:8]}…`**，净差 **+{DELTA} B** 恰好等于第一处那 9 个字符（`evidence/`）的长度、另两处一加一减互抵 ⇒ 口径固式：**"归档内某只文件的当前字节"只引末版清单那一行，不引任何落地器的自述**。
  ④ **gen 24 = 本批末版，两样证据齐了才叫末版**：12:53:33 门（`cred_gate_recheck_125333.txt`：**{fs24} 只 / 两计数 0 / CLEAN**）→ {genlog[-1][0]} 清单 `TOTAL={n24} / TOTAL_BYTES={money(b24)} / BOM={bom24}`（关系式 `{fs24} − 1 = {n24}` ✓，本批第 5 次实测）→ `verify_manifest.py`（**不接管道**：stdout 重定向后再看 `$?`）`VERIFY_RC={v2_rc} / VERDICT={v2_ver} / ROWS={n24} / MISMATCH=0 / MISSING=0 / UNLISTED=0`，**并且工具自己在归档外落了载体** `hardware/verify_manifest_0924125339.txt`（{money(os.path.getsize(vc2))} B）。
  ⑤ **末版封界固化成一条可执行纪律**：末版之后还剩排查记录 / done / dev_log / updates / 烧录须知 / backups README / docs 快照 / 项目记忆一整套 paperwork ⇒ 本批**所有落地器与载体都写在 `hardware/`（`hardware/ht305_sync/` 之外）**，否则 `UNLISTED` 立刻非 0、gen 24 自动降级（README 自己数到第 7 次那条链）⇒ **"末版"不是"我承诺不再改"，是"之后的写盘动作全都安排在归档目录之外"**。本条所在文件、`todo.md` 第十六遍、`hardware/r55_paperwork.py` 自己，都在外面。
  ⑥ **§38.19 落地（`hardware/r55_land_sec38_19.py`）**：排查记录现读 **{money(int(doc_b.group(2)))} B / md5 `{doc_b.group(3)[:8]}…` / {doc_b.group(4)} 行，纯 CRLF = {str(doc_t.count(chr(13)) == doc_t.count(chr(10)))}**，节标题在第 **{sec_line}** 行、要点 **{bullets}** 条（入口 + ①~⑦ + 本节没做）。**它的落地时刻只存在于当时那次 stdout**（无载体 = 本批⑦那只复核器存在的理由），所以本条**不写它的时刻**，只写它留下的可复算量：字节 / md5 / 行数 / 节标题行号 / 要点条数（全部由复核器现读）。
  ⑦ **一只事后补的独立复核器把⑥那句话变成可复算**：`hardware/r55_sec38_19_check.py`（{ck_at}）对 §38.19 引用的 **{ck_n}** 处读数逐条重导（needle 一律从载体现读拼出，每条同时问"正文写没写"与"载体是多少"）⇒ `CHECKS={ck_n}` 全 OK、三条 `TOTAL == 门 − 1` 逐一带入 assert、`rev-list` 现跑 = **{rev}** 与正文那句同值、§38.19 正文明文字节数 **0**（内存阳性对照 1）⇒ `VERDICT={ck_ver}`，载体 `hardware/r55_sec38_19_check.txt`。**它不是旧落地器的重跑**（那只拒绝覆写、不可重跑）。
  ⑧ **`FreqErr.md` 第二遍登记 {int(fe_ka) - int(fe_kb)} 条（{fe_at}）**：`{money(int(fe_bb))} → {money(int(fe_ba))} B（+{money(int(fe_ap))}）`、`^[错误类型]` **{fe_kb} → {fe_ka}**、`wc -l` **{fe_lb} → {fe_la}**（盘上现读 {frq_lines} 行 / {frq_ets} 条，两把尺与载体逐字同值）；六条 = 跨秒双 `now()` 假红 / 跑绿没载体 / 静默排除=隐形尺 / 打印已 assert 过的等式=半绿 / 同代第二次踩字节字面量里的中文与 `%`-格式串里的字面 `%` / 把"末版"读成"承诺不再改"。**落盘前两次 abort 都是守卫赢了**：(a) 回填占位那一步命中的是**历史台账行**里那个未替换占位 ⇒ 会就地洗掉一行历史，改成"先在模板上解析占位、再拼接"并追加两条断言（纯前缀 + 旧行仍以该占位开头）；(b) 输出段把三元组当二元解包抛 `ValueError`。两次都没碰到盘上文件（前后字节数同值）。
  ⑨ **本条没做（点名）**：① 没烧录、没碰串口（{RUN_AT} 现跑枚举 = **{', '.join(ports)}** ⇒ **COM14 不在**，我方真机日志仍 **{power_n} 只**、官方对照另 {official_n} 只 ⇒ 屏侧零进展、肉眼确认 0 次 ⇒ **不播提示音**）；② 没有新建备份根；③ 没有 `git push`、零历史重写（rebase / filter-branch / **amend** 都没碰）；④ `%TEMP%` 里那只带明文的抓回件仍在（本会话一律不删）；⑤ 服务器侧那一份**仍带明文** ⇒ **不能当回滚源**；⑥ docs 第九遍 / backups README 第九次读数 / 项目记忆 (101) / 提交轮 #9 / mindog 第二路 / 空上下文复查**都在本条之后**。
'''

for _blk in (D201, D202):
    for _ln in _blk.split('\n'):
        assert chr(92) not in _ln, 'ABORT: done 正文里有反斜杠（CR 静默损坏那一族）'
        assert 'None' not in _ln and '<built-in' not in _ln and '{' not in _ln, 'ABORT: 正文里有没被求值的占位'

# 明文凭据闸：口令只从宏本体读出，不打印、不进命令文本；命中即 ABORT，一只都不写。
_m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', open(SRC_MACRO, encoding='utf-8').read())
assert _m, 'ABORT: 读不到 PROV_PASS 宏，闸无法自证扫的是真口令'
_secret = _m.group(1).encode('utf-8')
old_done = done_t
new_done = old_done + D201.strip('\n') + '\n\n' + D202.strip('\n') + '\n'

# ================= todo.md 第十六遍（纯 CRLF） =================
T16 = f'''【**{RUN_AT} R55 尾巴批（第 13 代同步 + gen 22/23/24 + 两把补尺 + §38.19 + FreqErr 第二遍 + 独立复核器）落笔之后复跑（第十六遍）**：① 两条老命令 ⇒ 未勾选名单与只数**第十六次逐字未变**（仍 `{unchecked}` / **{len(ids)}**），`done.md` 末节号仍是 **{done_sec}**，数其中 `- [x] 201` 那一行 = **1** 次、换 `202` 同样 = **1**（由本落地器写盘后独立回读兑现），`git rev-list --count origin/main..HEAD` 现跑 = **{rev}**（**本行不回填**：提交轮 #9 之后会 +1，届时的数以那一轮自己的载体为准）。② **冻结链三代各自成立、只登记式子**：`TOTAL == 本遍门 FILES_SCANNED − 1` 在 gen 22（{fs22}→{n22}）、gen 23（{fs23}→{n23}）、gen 24（{fs24}→{n24}）**三次独立成立**；gen 22 那遍的裁决是 `MANIFEST_STALE` 而 `ROWS/MISMATCH/MISSING/UNLISTED` 四项全清白 ⇒ 根因 = 清单头部（{v22_hdr}）与代次日志末行（{genlog[-3][0]}）**跨了一秒**，本行是"假红原件已入库"的指针（`evidence/r55_verify_manifest_gen22_stale.txt`）。③ **末版 = gen 24**（{genlog[-1][0]} / `TOTAL {n24}` / `{money(b24)} B` / `BOM {bom24}`，`verify_manifest.py` `VERIFY_RC={v2_rc} / VERDICT={v2_ver}`，载体 `hardware/verify_manifest_0924125339.txt`）⇒ **此后所有写盘都在 `hardware/ht305_sync/` 之外**，包括本文件、本行的落地器、docs 快照脚本、backups README。④ 现场态（{RUN_AT} 现跑）：`python -m serial.tools.list_ports` = **{', '.join(ports)}** ⇒ **COM14 不在**，§38.13 那两行判据样本数还是 **0**，"接电池 + 强制通电 + 短接重烧"仍全在用户侧；构建目录 `zizhao_esp32s3.bin` 现算 md5 = `{bin_md5}`（**md5，32 位 hex，不是 sha256**）/ {money(bin_bytes)} B ≠ 板上与归档那只 `{arc_md5[:8]}…` / {money(arc_bytes)} B ⇒ **待烧 ≠ 板上**；`git -c core.quotePath=false status --porcelain` = **{mod_n} 只 ` M` + {un_n} 只 `??` = {len(st)} 行**，其中 `main/` 侧 **{len(main_dirty)}** 只（每轮被点名 DROP 的那只），同一时刻用户端报的"66 个未提交变更"与本行**两把尺互不可换算** ⇒ 只登记各自的数，**不得拿 {len(st)} 去驳回 66**（承接第十三、十五遍）。⑤ **行数 {todo_lines} → {todo_lines + 1}：本行是本遍唯一一处净 +1 行**（第十一~十五遍各声明过一次"唯一"，主语都只限它们自己那一遍）；两把括号尺（全角 （） / 半角 () 逐行数不配平的只数）追加前后各测一次 ⇒ **{FULLW} / {HALF}** 逐字同值，由脚本末尾断言兑现，不是话术。】'''
assert todo_t.endswith('\r\n'), 'ABORT: todo.md 不以 CRLF 结尾，追加会造出半行'
new_todo = todo_t + T16 + '\r\n'

# ================= dev_log 追加 =================
DEV = f'''
### R55（09-24 {la_in}~{RUN_AT}）：第 13 代 ht305 同步 `r55final` + 归档链 gen 22/23/**24**（首只**假红** + 第一次**跑绿没载体** + 末版封界）+ §38.18/§38.19 + `FreqErr.md` 六条 —— 纯同步与 paperwork，屏侧零字节

- **同步（{cut_copy} 截止拷贝 → {cut_zip} 建包 → {probe_at} 探测 → {ver_done} 远端验 → {rt1_at} 往返首跑红 → {rt2_at} 重跑绿 → {ld_at} 两把差集尺）**：载荷 **{loc_files} 只 / {money(loc_bytes)} B**、包 **{money(zip_size)} B / md5 `{zip_md5}`**、两侧聚合 sha256 `{loc_agg[:8]}…` 逐字同值、`REMOTE_FORBIDDEN={ver_forb}`；`TARGET_EXISTS={probe_te}` ⇒ 桌面 r 系列 **{len(desk_r)} 只并存、零删除**；往返**首跑 `SCP_RC={rt1_rc}` 失败、原件留盘不洗绿**，重跑两侧 {money(rt2_bytes)} B / md5 `{rt2_md5[:8]}…` 同值 ⇒ `VERDICT={rt2_ver}`（服务器副本仍带明文 ⇒ **绝不 push、不能当回滚源**）；差集名单 {ld_only_l}/{ld_only_r}、内容尺 {ld_same} identical / {ld_chg} 改（脚本自己）/ {ld_new} 新（截止后落的取证件），四桶并集 == {ld_cand}。
- **§38.18（{la_in}）**：把"取证只落在 `%TEMP%`"这一族补进仓库；排查记录 {la_rec.group(1)} → **{la_rec.group(3)} 行 / {money(int(la_rec.group(4)))} B**（纯 CRLF）。那一遍的 `FreqErr` 台账自述行数**少 1**，由 {corr_at} 的订正行收尾（现读第 {corr_line} 行；**只追加、不就地改数**），根因 = "行尾闭合"发生在计数之后 ⇒ 补的那只换行没进任何一次计数。
- **gen 22 = 假红**：`{fs22} − 1 = {n22}` 成立、`ROWS={v22_rows} / MISMATCH={v22_mis} / MISSING={v22_mss} / UNLISTED={v22_unl}` 全清白，裁决却是 `{v22_ver}` ⇒ `gen_manifest.py` 一次运行取了**两只 `now()`**，中间隔着 {n22} 只文件的哈希遍历，**跨秒即断**（清单头部 {v22_hdr} vs 日志末行 {genlog[-3][0]}）；该判据自 gen 9 就在，**潜伏 {laten} 个世代**才第一次咬人。修法 = 源头只取一次时刻 + verifier 把判决与展示分家；假红原件 `evidence/r55_verify_manifest_gen22_stale.txt` 入库。
- **gen 23 = 跑绿了却没证据**：{fs23} 只门 → `TOTAL={n23}` → 复核 `rc=0`，**但 `rc=0` 只打在 stdout**（当时无载体）⇒ 新规：**"已跑完"必须同时给出 `rc` 与载体文件名，且载体由工具自己在同一次运行里落盘**；物证 = 事后补跑对 gen 23 给 `VERIFY_RC={v1_rc} / VERDICT={v1_ver}`（`hardware/verify_manifest_0924123702.txt`，{money(os.path.getsize(vc1))} B）。
- **gen 24 = 末版 + 封界**：{fs24} 只门 → {genlog[-1][0]} `TOTAL={n24} / {money(b24)} B / BOM {bom24}` → 复核（不接管道）`VERIFY_RC={v2_rc} / VERDICT={v2_ver}`，**工具自己在归档外落了载体**（{money(os.path.getsize(vc2))} B）⇒ 两样齐才叫末版；此后写盘一律在 `hardware/ht305_sync/` **之外**（本批所有落地器、docs 快照脚本、backups README 都在外面）。
- **两把补尺**：明文复扫 {rc1_at} 首跑把"声明该名的脚本自己"静默排除 = **造了一把看不见的尺** ⇒ {rc2_at} 改按**半径**分桶（{rc2_scope} 只逐只点名 `TOTAL_HITS={rc2_hits}` + 内存阳性对照 {rc2_pos} + 目录外 {rc2_out} 只）⇒ `CLEAN`，首跑原件不覆盖、由 `PRIOR_ATTEMPT` 点名；工具体检第一遍 {pa_at} 只覆盖 1 只 `.ps1` ⇒ {pb_at} 补 {pb_n} 只 `ast.parse` + 阳性对照 ⇒ `TOOLS_PARSE_CLEAN`（**归档内不用 `py_compile`**，`.pyc` 会破归档）。
- **README 两个落地器**：{lr1_at} 第一遍（{money(lr1_b)} → {money(lr1_a)} B、纯 LF、纯插入 PASS）→ {lr2_at} 第二遍 {lr2_edits} 处编辑（自述 {money(lr2_a)} B）→ 回读又抓三处排版缺陷就地订正 ⇒ **末版清单权威值 {money(rm_bytes)} B / md5 `{rm_md5[:8]}…`，净差 +{DELTA} B**（等于第一处那 9 个字符）⇒ 归档内某只文件的当前字节**只引末版清单那一行**。
- **登记落点**：排查记录 **§38.19**（第 {sec_line} 行起、要点 {bullets} 条，{money(int(doc_b.group(2)))} B / md5 `{doc_b.group(3)[:8]}…`）；`FreqErr.md` **{int(fe_ka) - int(fe_kb)} 条**（`^[错误类型]` {fe_kb}→**{fe_ka}**、`wc -l` {fe_lb}→**{fe_la}**，台账**先数后回填**）；独立复核器 `hardware/r55_sec38_19_check.py` ⇒ `CHECKS={ck_n}` / `{ck_ver}`；`hardware/ht305_sync/README.md`（gen 22~24 三格）；本文件本节、`done.md` **201 + 202**、`todo.md` **第十六遍**、`{UPD_REL}`（**本代新建一只**）；backups README 第九次读数与 docs 第九遍快照**排在本节之后**。
- **本批我自己造成的（全文在 `FreqErr.md` 那六条）**：① 跨秒双 `now()` 造出假红；② 跑绿没载体；③ 复扫静默排除自己；④ 打印一条已经 assert 过的等式 = 半绿；⑤ 同一代第二次踩"字节字面量里写中文"与"`%`-格式串里的字面 `%`"两只语法雷；⑥ 把"末版"理解成"承诺不再改"。**共同形状**：FreqErr 那一遍落盘前的两次 abort（历史台账行的未替换占位会被就地洗掉、三元组当二元解包）都响在写盘之前 ⇒ 修正与登记本身也是断言载体。
- **现场态（{RUN_AT} 现跑）**：`rev-list origin/main..HEAD` = **{rev}**（**未 push**、零历史重写）；COM 枚举 = **{', '.join(ports)}** ⇒ **COM14 不在**；待烧 `{bin_md5[:8]}…`（{money(bin_bytes)} B）≠ 板上/归档 `{arc_md5[:8]}…`（{money(arc_bytes)} B）；我方真机日志 **{power_n} 只**分母未动（官方对照另 {official_n} 只）；`status --porcelain` = **{len(st)} 行**（{mod_n} ` M` + {un_n} `??`，`main/` 侧 {len(main_dirty)} 只）⇒ 本批零代码进工作树；用户端"66 个未提交变更"与本行两把尺互不可换算。
- **本批没做**：没烧录 / 没碰串口 / 没接电池 / 没按电源键 / 没短接 / 屏亮 0 次肉眼确认 / **不播提示音** / **未 push** / 历史未脱敏（等裁决）/ `esp_gpio_hold_en()` 故意仍未加 / 没新建备份根 / docs 第九遍、backups 第九次读数、项目记忆 (101)、提交轮 #9、mindog 第二路、空上下文复查排在本节之后 / 本批**零删除**。
'''
dev_t = open(DEVLOG, encoding='utf-8', newline='').read()
assert dev_t.count('\r') == 0 and dev_t.endswith('\n'), 'ABORT: dev_log 不是纯 LF 结尾'

# ================= updates 新建 =================
UPD_T = f'''# 2026-09-24 R55 尾巴：第 13 代 ht305 全量同步 `r55final` + 归档链 gen 22 / 23 / 24（首只假红 → 跑绿没载体 → 末版封界）

时刻：本文件所有数字写于 {RUN_AT} 的一次现跑；动作区间 = 09-24 {la_in}（§38.18 落地）~ {genlog[-1][0]}（gen 24 末版）~ {ck_at}（独立复核器）。
触发：用户常设指令「继续，深入搜索检修了解，及时同步至服务器 ht305（ssh）。不要问问题直到所有任务结束。」
本代性质：**纯同步 + paperwork** —— 屏侧一个字节都没动（没烧录、没碰串口、COM14 不在，{RUN_AT} 现跑 = {', '.join(ports)}）。

## 一句话结论

第 13 代同步把 **{loc_files} 只 / {money(loc_bytes)} B** 搬上 ht305，包 md5、逐只大小聚合（sha256 全长）、双向名单差集**三把尺同时 0 差**；往返那一步**首跑 `SCP_RC={rt1_rc}` 失败、重跑才绿**，最终裁决 `{rt2_ver}`（服务器副本仍带明文 ⇒ **绝不 push**）。
归档链本批跑三代，把两件**从来没有载体覆盖过**的事第一次落到盘上：gen 22 是**假红**（`ROWS/MISMATCH/MISSING/UNLISTED` 全清白却 `MANIFEST_STALE`，根因 = 一次运行取两只 `now()` 跨秒，潜伏 {laten} 个世代），gen 23 是**跑绿了却没留证据**（`rc=0` 只打在 stdout）。修法同一条：**"已跑完"必须同时给出 `rc` 与载体文件名，且由工具自己在同一次运行里落盘**。
gen 24 起"末版"有了可执行定义：**之后的写盘动作全部安排在 `hardware/ht305_sync/` 之外**（本批所有落地器都在外面），而不是"我承诺不再改"。

## 本代做了什么（按时刻）

| 时刻 | 动作 | 载体 |
| --- | --- | --- |
| {la_in}~{la_out} | §38.18 落地：排查记录 {la_rec.group(1)}→{la_rec.group(3)} 行 / {money(int(la_rec.group(4)))} B，纯 CRLF | `evidence/r55_land_A.txt` |
| {corr_at} | `FreqErr.md` 台账"自述行数少 1"的订正行（只追加、不就地改数） | `FreqErr.md` 第 {corr_line} 行 |
| {cut_copy} / {cut_zip} | 截止拷贝 / 建包（{loc_files} 只 / {money(loc_bytes)} B；包 {money(zip_size)} B） | `evidence/r55_local.txt` |
| {probe_at} | 上传前探测：`TARGET_EXISTS={probe_te}` + 桌面 {len(desk)} 项全列（r 系列 {len(desk_r)} 只并存） | `evidence/r55_probe.txt` |
| {ver_at}~{ver_done} | 远端解包 + 校验：两侧聚合逐字等、`REMOTE_FORBIDDEN={ver_forb}`、解包根 `zsynctest15` | `evidence/r55_verify.txt` |
| {rt1_at} | 往返**首跑失败** `SCP_RC={rt1_rc}` ⇒ 该次读数不作数 | `evidence/r55_roundtrip.txt` |
| {rt2_at}~{rt2_end} | 往返重跑绿：两侧 {money(rt2_bytes)} B / md5 `{rt2_md5[:8]}…` 同值、`BYTE_EQUAL_TO_WORKTREE={rt2_eq}` | `evidence/r55_roundtrip_2.txt` |
| {ld_at} | 两把差集尺：名单 {ld_local}/{ld_remote} 差 {ld_only_l}/{ld_only_r}；内容 {ld_same} 同 + {ld_chg} 改 + {ld_new} 新（四桶并集 {ld_cand}） | `evidence/r55_listdiff.txt` |
| {rc1_at} → {rc2_at} | 明文复扫：首跑口径错（静默排除自己）→ 改按半径分桶 {rc2_scope} 只点名 `TOTAL_HITS={rc2_hits}` + 内存阳性对照 | `evidence/r55_cred_recount.txt` / `_2.txt` |
| {fs22} 只门 → {v22_hdr} | **gen 22 假红**：`{fs22} − 1 = {n22}` 成立但 `MANIFEST_STALE`（头部 {v22_hdr} vs 日志 {genlog[-3][0]}） | `evidence/cred_gate_recheck_123427.txt` / `r55_verify_manifest_gen22_stale.txt` |
| {fs23} 只门 → {genlog[-2][0]} | **gen 23 跑绿无载体**；事后补跑对它只能给 `VERIFY_RC={v1_rc}` | `..._123653.txt` / `hardware/verify_manifest_0924123702.txt` |
| {pa_at} → {pb_at} | 工具体检：第一遍只 1 只 `.ps1` → 补 {pb_n} 只 `ast.parse` + 阳性对照 ⇒ `TOOLS_PARSE_CLEAN` | `evidence/r55_parse_check.txt` / `_2.txt` |
| {lr1_at} → {lr2_at} | README 两遍落地器（{money(lr1_b)}→{money(lr1_a)}→自述 {money(lr2_a)}→末版清单 **{money(rm_bytes)} B / md5 `{rm_md5[:8]}…`**，净差 +{DELTA} B） | `evidence/r55_land_readme.txt` / `_2.txt` |
| {fs24} 只门 → {genlog[-1][0]} | **gen 24 末版**：`{fs24} − 1 = {n24}`、`VERIFY_RC={v2_rc} / {v2_ver}`，工具自落载体 | `..._125333.txt` / `MANIFEST.txt` / `hardware/verify_manifest_0924125339.txt` |
| 13:00 前后 | §38.19 落地（第 {sec_line} 行起 / 要点 {bullets} 条）——**该次 stdout 无载体**，故本表不写它的时刻 | `hardware/r55_land_sec38_19.py`（正文：排查记录 {money(int(doc_b.group(2)))} B / md5 `{doc_b.group(3)[:8]}…`） |
| {fe_at} | `FreqErr.md` 第二遍 **{int(fe_ka) - int(fe_kb)}** 条：`^[错误类型]` {fe_kb}→{fe_ka}、`wc -l` {fe_lb}→{fe_la} | `hardware/r55_freqerr2.txt` |
| {ck_at} | 独立复核器：`CHECKS={ck_n}` 全 OK ⇒ `{ck_ver}` | `hardware/r55_sec38_19_check.txt` |
| {RUN_AT} | 本批 paperwork（done 201/202 + todo 第十六遍 + dev_log + 本文件 + 烧录须知现场态） | `hardware/r55_paperwork.py` |

## 六条新错误类型（全文在 `FreqErr.md`）

1. **同一次运行里取两只 `now()`** ⇒ 跨秒即造出"数字全对、裁决为红"的假红；修法 = 只取一次并由它派生其余读数（相等由构造保证）。
2. **"跑绿了却没留证据"** ⇒ 判决只打在 stdout 等人抄 = 不可复算；修法 = 工具自己在同一次运行里落载体，登记时连 `rc` 与文件名一起给。
3. **静默排除"声明该名的脚本自己"** ⇒ 一把看不见的尺；修法 = 按**半径**分桶并逐只点名，首跑原件不覆盖、由新载体 `PRIOR_*` 点名。
4. **打印一条已经 assert 过的等式** = 半绿；落地器自述的 AFTER 值可被自己之后的回读推翻 ⇒ 归档内字节只引**末版清单那一行**。
5. **同一代第二次踩同一只语法雷**（字节字面量里写中文 / 格式串里写字面 `%`）⇒ 台账不能只当"修错前读物"，守卫要落在脚本里。
6. **把"末版"理解成"承诺不再改"** ⇒ 冻结后往归档里落任何一只 = 亲手把末版降级（`UNLISTED` 非 0）；这条是**封界型**，前六种是内容漂、这次是名册漂。

## 本代没做（点名）

没烧录 / 没碰串口 / 没接电池 / 没按电源键 / 没短接 / 屏亮 0 次肉眼确认 ⇒ **不播提示音**；没新建备份根；**未 `git push`**（{RUN_AT} 现跑 `rev-list` = **{rev}**）、零历史重写；`%TEMP%` 里那只带明文的抓回件仍在（本会话一律不删）；服务器侧那一份**仍带明文** ⇒ ht305 任何一份都**不能当回滚源**；待烧仍是 R53 那只 md5 `{bin_md5[:8]}…`（{money(bin_bytes)} B）而板上与归档仍是 `{arc_md5[:8]}…` ⇒ **"待烧 ≠ 板上"继续成立**；docs 第九遍、backups README 第九次读数、项目记忆 (101)、提交轮 #9、mindog 第二路、空上下文故障检测复查**均排在本文件之后**，读数落各自那一格。
'''

BLOCKS = (D201, D202, T16, DEV, UPD_T)
for _blk in BLOCKS:
    for _ln in _blk.split('\n'):
        assert chr(92) not in _ln.replace('\\r', '?'), 'ABORT: 正文里有反斜杠：' + _ln[:60]
        assert _secret not in _ln.encode('utf-8'), 'ABORT: 明文凭据闸命中，一只都不写'
print('CRED_GATE HITS=0 OF', len(BLOCKS), 'blocks')

# ================= 写盘 =================
open(DONE, 'w', encoding='utf-8', newline='').write(new_done)
back = open(DONE, encoding='utf-8', newline='').read()
assert back.startswith(old_done) and back.count('\r') == 0, 'ABORT: done.md 不是纯 LF 追加'
assert re.findall(r'(?m)^- \[[ x]\] (\d+)', back)[-2:] == ['201', '202'], 'ABORT: 新条目编号不对'
assert back.count('- [x] 201') == 1 and back.count('- [x] 202') == 1

open(TODO, 'w', encoding='utf-8', newline='').write(new_todo)
tb = open(TODO, 'rb').read()
assert tb.startswith(todo_t.encode('utf-8')) and tb.count(b'\r\n') == tb.count(b'\n') == todo_lines + 1, \
    'ABORT: todo.md 追加破了行尾或不是纯追加'
_t2 = tb.decode('utf-8')
assert sum(1 for l in _t2.split('\r\n') if l.count('（') != l.count('）')) == FULLW
assert sum(1 for l in _t2.split('\r\n') if l.count('(') != l.count(')')) == HALF

open(DEVLOG, 'w', encoding='utf-8', newline='').write(dev_t + DEV.lstrip('\n'))
_dv = open(DEVLOG, encoding='utf-8', newline='').read()
assert _dv.startswith(dev_t) and _dv.count('\r') == 0 and '### R55（' in _dv[len(dev_t):], 'ABORT: dev_log 追加不成立'

os.makedirs(os.path.dirname(UPD), exist_ok=True)
open(UPD, 'w', encoding='utf-8', newline='\n').write(UPD_T)
assert open(UPD, encoding='utf-8', newline='').read() == UPD_T
assert os.path.getsize(UPD) == len(UPD_T.encode('utf-8'))

note_t = open(NOTE, encoding='utf-8', newline='').read()
assert note_t.count('\r') == 0, 'ABORT: 烧录须知不是纯 LF'
nl = note_t.split('\n')
anchor = [i for i, l in enumerate(nl) if l.strip().startswith('【2026-09-24 07:59:16 现跑**换代**')]
assert len(anchor) == 1, 'ABORT: 换代块锚点不唯一（现 %d 处）' % len(anchor)
i = anchor[0]
assert nl[i].endswith('的口径到此为止。'), 'ABORT: 换代块末句与预期不符，别插错位置'
INS = ('  【' + RUN_AT + ' 现跑再复核（本行由 `hardware/r55_paperwork.py` 现读现写）】R53~R55 三批**全是盘上/文档/凭证，零串口动作、零抓日志、零行代码进工作树**'
       + '⇒ 我方真机日志分母仍 **' + str(power_n) + ' 只**（官方对照另 ' + str(official_n) + ' 只）、"几次上电"一条没动；'
       + '待烧仍是 R53 那只 **md5 `' + bin_md5[:8] + '…`**（' + money(bin_bytes) + ' B），板上与归档仍是 **`' + arc_md5[:8] + '…`**（'
       + money(arc_bytes) + ' B，`backups/r43_20260922_131029/zizhao_esp32s3.bin` 现算）⇒ **"待烧 ≠ 板上"继续成立，本行不推翻上面那句换代**；'
       + '`python -m serial.tools.list_ports` 现跑 = **' + ', '.join(ports) + '** ⇒ **COM14 仍不在**，〇-补2 那两行判据（`hold-on` 与 `PWR_OUT` 按住）的样本数**至今为 0**。'
       + '〇-补2 末尾"欠的动作"一条没变：要新的实测证据只有一条路 —— 把它真烧进去（强制通电 / 短接 BOOT 重烧），在此之前本节**没有任何新的屏侧结论可加**。')
assert chr(92) not in INS and _secret not in INS.encode('utf-8')
new_note = '\n'.join(nl[:i + 1] + [INS] + nl[i + 1:])
open(NOTE, 'w', encoding='utf-8', newline='').write(new_note)
nb = open(NOTE, encoding='utf-8', newline='').read()
assert nb.count('\r') == 0 and nb.count('\n') == note_t.count('\n') + 1, 'ABORT: 烧录须知插入破了行数或行尾'
assert nb.startswith('\n'.join(nl[:i + 1])) and 'R53~R55 三批' in nb
assert len(re.findall(r'(?m)^#{2,3} ', nb)) == len(re.findall(r'(?m)^#{2,3} ', note_t)), 'ABORT: 插入吞掉了标题'

# ================= 输出 =================
fin = open(DONE, encoding='utf-8', newline='').read()
print('PAPERWORK_AT=' + RUN_AT)
print('DONE 条目末两条=%s（新增 2 条，纯 LF 追加）' % '/'.join(re.findall(r'(?m)^- \[[ x]\] (\d+)', fin)[-2:]))
print('TODO_CRLF=%d->%d  未勾选名单=%s / %d 只  括号两把尺=%d / %d（追加前后同值）' % (
    todo_lines, todo_lines + 1, unchecked, len(ids), FULLW, HALF))
_dv2 = open(DEVLOG, encoding='utf-8', newline='').read()
print('DEVLOG_LINES=%d（+%d）  UPD_BYTES=%d  UPD_REL=%s' % (
    _dv2.count('\n'), _dv2.count('\n') - dev_t.count('\n'), os.path.getsize(UPD), UPD_REL))
print('NOTE_LINES=%d（净 +1 行，插入未吞标题）' % nb.count('\n'))
print('GEN22/23/24 = %s/%s/%s 只（门 %s/%s/%s）；末版 gen 24 @%s = %s B / BOM %s' % (
    n22, n23, n24, fs22, fs23, fs24, genlog[-1][0], money(b24), bom24))
print('FREQ_NOW 错误类型=%d 行数=%d（载体登记 %s / %s）' % (frq_ets, frq_lines, fe_ka, fe_la))
assert frq_ets == int(fe_ka) and frq_lines == int(fe_la), 'ABORT: FreqErr 盘上现状与载体登记不符'
print('FIELD rev-list=%s  ports=%s  待烧=%s/%s B  板上=归档=%s/%s B  日志分母=%d 只  官方=%d 只' % (
    rev, ','.join(ports), bin_md5[:8], money(bin_bytes), arc_md5[:8], money(arc_bytes), power_n, official_n))
print('NUMBERS_ALL_FROM=evidence 15 只 + hardware 4 只载体 + MANIFEST/genlog + 5 条现跑命令（全部现读，无手写数）')
print('VERDICT=PAPERWORK_LANDED_R55')
