# R55 第三批（项目记忆/用户记忆落地 + 同一批里两次自查订正）的**收口落地器**：一次调用落两只 CRLF 文件
#   ① FreqErr.md —— 本批 4 条新错误类型 + 台账行（两把尺都在"将被写出的最终串"上现算，(99)）
#   ② hardware/20260919_墨水屏点屏排查记录.md —— 新增 §38.20
# 位置：`hardware/`（**归档目录之外**）—— gen 24 已于 12:53:39 冻成末版，此后任何一只文件落进
# `hardware/ht305_sync/` 都会把 `verify_manifest.py` 的 `UNLISTED` 顶成非 0 ⇒ 末版自动降级（§38.19 ④）。
# 本脚本同时是本批四条新规的**执行者**，逐条对上：
#   (103) 所有子串取证一律 `(?m)^` 行首锚 + 按行取 + 恰好 1 命中（见 line_of）；
#   (104) 五种时刻各读各的载体，本遍 NOW 只允许出现在点名"本遍现跑/本节登记"的那一格；
#   幂等闸 两只文件各自的锚现读 ⇒ 已落地那一遍**跳过写盘**、从盘上反推"追加之前"的读数再复核，不二次追加；
#   期望值不猜 所有 assert 的期望值由被检文本或另一只载体自身推导（三处交叉核对见 XCHECK 行）。
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
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
EV = os.path.join(SYNC, 'evidence')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
MAN = os.path.join(SYNC, 'MANIFEST.txt')
VER24 = os.path.join(HDIR, 'verify_manifest_0924125339.txt')
VER24B = os.path.join(HDIR, 'verify_manifest_0924125339_2.txt')
C_LAND = os.path.join(HDIR, 'r55_land_memory_r55.txt')
C_FIX = os.path.join(HDIR, 'r55_fix_memory_r55.txt')
C_RD9 = os.path.join(HDIR, 'r55_backups_readme9.txt')
C_RT2 = os.path.join(EV, 'r55_roundtrip_2.txt')
PMEM = r'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/memory'
UMEM = r'C:/Users/david/.qoder-cn/memory'
PMB = os.path.join(PMEM, 'hardware-epaper397-power.md')
PMI = os.path.join(PMEM, 'MEMORY.md')
UMB = os.path.join(UMEM, 'reference-qoder-tool-mapping.md')
UMI = os.path.join(UMEM, 'MEMORY.md')

_cands = ['r55_paperwork3.txt'] + ['r55_paperwork3_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)
# 本脚本自己的前序权威载体 = 已存在的最后一只（复跑补写的 _2 起盖过首载体，首载体只作历史保留）
_self_prior = [c for c in _cands if os.path.exists(os.path.join(HDIR, c))]


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def stat(p):
    b = open(p, 'rb').read()
    return len(b), b.count(b'\n'), b.count(b'\r'), hashlib.md5(b).hexdigest()[:8]


def line_of(path, pat, why, grp=0):
    """按行取、且要求全文件恰好 1 行命中 —— (103) 那条教训的执行者。"""
    hits = [l for l in rd(path).replace('\r\n', '\n').split('\n') if re.search(pat, l)]
    assert len(hits) == 1, 'ABORT: %s 里 %r 命中 %d 行（须恰好 1）⇒ %s' % (
        os.path.basename(path), pat, len(hits), why)
    return hits[0] if grp == 0 else re.search(pat, hits[0]).group(grp)


def crlf_pure(path):
    raw = open(path, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'ABORT: %s 行尾本来就混杂' % os.path.basename(path)


def unresolved(text):
    return re.findall(r'\{[A-Za-z_][A-Za-z0-9_]*\}', text)


def kinds(text):
    return len(re.findall(r'(?m)^\[错误类型\]', text))


def heads(text):
    return len(re.findall(r'(?m)^#{2,3} ', text))


def blank_gap_lines(text):
    """返回"标题行上方不是空行"的标题行号（末尾那只空元素是 CRLF 文件 EOF 的假象，先丢掉）。"""
    lns = text.split('\r\n')
    if lns and lns[-1] == '':
        lns.pop()
    return [i + 1 for i in range(1, len(lns)) if lns[i].startswith('#') and lns[i - 1].strip()]


TS = '[0-9-]{10} [0-9:]{8}'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   # 本遍现跑那一刻；只有写盘那一遍它才 == RUN_AT

# ---------- 现读：落地批载体（C_LAND）—— 副作用发生在断言之前的那一批的在册读数 ----------
t_land = line_of(C_LAND, r'(?m)^R55 项目记忆', '落地批载体首行')
LAND_AT = re.search(r'本遍现跑于 (' + TS + ')', t_land).group(1)
LAND_MODE = re.search(r'MODE=(\w+)', t_land).group(1)
BODY_AT = re.search(r'正文里那些时刻 = (' + TS + ')', t_land).group(1)
assert LAND_MODE == 'REWROTE_CARRIER_ONLY', 'ABORT: 落地批载体不是"补载体那一遍"，先查是谁写的：' + LAND_MODE
line_of(C_LAND, r'(?m)^LANDING_SEQUENCE', '落地批点名崩溃事实的那一行')

t_sync = line_of(C_LAND, r'(?m)^SYNC ', '第 13 代同步读数行')
sync_n = re.search(r'^SYNC \d+ 代 (\d+) 只', t_sync).group(1)
sync_b = re.search(r'/ (\d+) B / 包', t_sync).group(1)
pkg_b = re.search(r'包 (\d+) B', t_sync).group(1)
pkg_md5 = re.search(r'md5 ([0-9a-f]{32})', t_sync).group(1)
agg_md5 = re.search(r'聚合 ([0-9a-f]{64})', t_sync).group(1)
FAKE_V = 'VERDICT=SCP_FAILED'
assert FAKE_V in t_sync, 'ABORT: 上一遍载体里那句假裁决不在了 ⇒ 有人改写历史，先查'

t_gen = line_of(C_LAND, r'(?m)^GEN24 ', 'gen 24 末版读数行')
gen_total, gen_bytes, gen_bom = re.search(r'TOTAL=(\d+) / ([\d,]+) B / BOM (\d+)', t_gen).groups()
t_docs_land = line_of(C_LAND, r'(?m)^DOCS ', '落地批抄的 docs 快照行')
t_readme = line_of(C_LAND, r'(?m)^README ', '待烧 / 板上指纹行')
rm_bytes_land = int(re.search(r'^README (\d+) B md5 ([0-9a-f]{32})', t_readme).group(1))
rm_md5_land = re.search(r'^README \d+ B md5 ([0-9a-f]{32})', t_readme).group(1)
bin_new = re.search(r'BIN build md5=([0-9a-f]{32}) / (\d+) B', t_readme).groups()
bin_old = re.search(r'板上归档 md5=([0-9a-f]{32}) / (\d+) B', t_readme).groups()
_land_ls = rd(C_LAND).replace('\r\n', '\n').split('\n')
_k = [i for i, l in enumerate(_land_ls) if l.startswith('FILE hardware-epaper397-power.md')]
assert len(_k) == 1, 'ABORT: 落地批载体里项目正文那只 FILE 锚不是恰好 1 处：%d' % len(_k)
t_mem0 = _land_ls[_k[0] + 1]
assert t_mem0.startswith('  now   LF='), 'ABORT: 落地批载体 FILE 锚的下一行不是读数行：' + repr(t_mem0[:20])
t_docline = line_of(C_LAND, r'(?m)^DOC heads=', '落地批抄的排查记录体检行')
doc_h23_land, doc_bytes_land, doc_lines_land = re.search(
    r'heads=\d+（其中二/三级 (\d+)） 缺空行=(\d+) 节号.*?bytes=([\d,]+) lines=(\d+)', t_docline).group(1, 3, 4)
assert re.search(r'heads=\d+（其中二/三级 \d+） 缺空行=0 ', t_docline), 'ABORT: 落地批那遍量到的"缺空行"不是 0，本节的前置事实变了'
doc_md5_land = re.search(r'md5=([0-9a-f]{8})', t_docline).group(1)

# ---------- 现读：订正批载体（C_FIX）—— 它点名的两处假读数与真值 ----------
t_fix1 = line_of(C_FIX, r'(?m)^R55 落地后自查订正', '订正批载体首行')
FIX_AT = re.search(r'落盘于 (' + TS + ')', t_fix1).group(1)
FIX_CARRIER_AT = re.search(r'本遍现跑于 (' + TS + ')', t_fix1).group(1)
FIX_MODE = re.search(r'MODE=(\w+)', t_fix1).group(1)
t_true = line_of(C_FIX, r'(?m)^SRC ', '真裁决取证行（双同形 ⇒ 按行取末位，(103)）')
tok_true = re.findall(r'第 \d+ 行 (\S+)', t_true)
assert len(tok_true) == 2 and tok_true[0] == 'PRIOR_VERDICT=' + FAKE_V, \
    'ABORT: SRC 行不再"双同形"，本节 (103) 的叙述与载体不符：%r' % (tok_true,)
assert tok_true[1].startswith('VERDICT=')
TRUE_V = tok_true[-1]
assert TRUE_V == 'VERDICT=REMOTE_CARRIES_PLAINTEXT', 'ABORT: 真裁决与在册不符：' + TRUE_V
rt_at = re.search(r'RAN_END_AT=(' + TS + ')', t_true).group(1)
t_tm = line_of(C_FIX, r'(?m)^TIME ', '时刻冒充取证行')
rd9_at = re.search(r'真值 (' + TS + ')', t_tm).group(1)
fake_at = re.search(r'冒充值 (' + TS + ')', t_tm).group(1)
gap_min = re.search(r'分位差 (\d+) 分钟', t_tm).group(1)
assert fake_at == BODY_AT, 'ABORT: 订正载体点名的冒充值与落地批正文时刻不同值 ⇒ 两把尺量的不是同一处'
assert rd9_at != fake_at, 'ABORT: 真值与冒充值同值 ⇒ 这一格根本没有可订正的东西，别落这条'
t_pb = line_of(C_FIX, r'(?m)^PMEM_BODY ', '正文换字等式行')
pl0, pl1, pb0, pb1 = re.search(r'LF (\d+) -> (\d+) \(\+3\) bytes (\d+) -> (\d+)', t_pb).groups()
t_pi = line_of(C_FIX, r'(?m)^PMEM_INDEX ', '索引换字等式行')
pilf, pi0, pi1 = re.search(r'LF (\d+) -> \1 \(\d+\) bytes (\d+) -> (\d+)', t_pi).groups()
t_cnt = line_of(C_FIX, r'(?m)^PMEM_COUNTS ', '落点计数行（由订正段自身推导）')
c103, c104 = re.search(r'\(103\)=(\d+) \(104\)=(\d+)', t_cnt).groups()
assert line_of(C_FIX, r'(?m)^MD5_BEFORE=', '改前 md5 不复算那一行')
# 两只载体的**互核**：落地批抄的"改前读数"必须等于订正批等式的左端（不引入新事实，只把两只对上）
assert (pl0, pb0) == re.search(r'LF=(\d+) bytes=(\d+)', t_mem0).groups(), \
    'ABORT: 两只载体对"改前正文"的读数不一致：%s vs %s' % ((pl0, pb0), re.search(r'LF=(\d+) bytes=(\d+)', t_mem0).groups())
assert hashlib.md5(open(PMB, 'rb').read()).hexdigest()[:8] != re.search(r'md5=([0-9a-f]{8})', t_mem0).group(1), \
    'ABORT: 盘上 md5 仍等于落地批抄的改前值 ⇒ 订正从未落盘，前面那些等式都是空的'

# ---------- 现读：末版清单 + 两遍终态复核 + docs/backups 那一格 ----------
mtail = [l.split('\t') for l in rd(MAN).splitlines() if l.startswith(('TOTAL\t', 'TOTAL_BYTES\t', 'BOM_FILES\t'))]
assert len(mtail) == 3, 'ABORT: 末版清单末三行取不到'
m_n, m_b, m_bom = (int(x[1]) for x in mtail)
assert (str(m_n), money(m_b), str(m_bom)) == (gen_total, gen_bytes, gen_bom), \
    'ABORT: 落地批抄的 gen 24 三字段与末版清单不符：%s vs %s' % (gen_total, gen_bytes)


def man_row(rel):
    for ln in rd(MAN).splitlines():
        f = ln.split('\t')
        if len(f) == 5 and f[0] == rel:
            return int(f[1]), f[2]
    raise SystemExit('ABORT: 末版清单里没有 ' + rel)


rm_bytes, rm_md5 = man_row('README.md')
assert (rm_bytes, rm_md5) == (rm_bytes_land, rm_md5_land), \
    'ABORT: 落地批抄的 README 字节/md5 与末版清单那一行不符：%s/%s vs %s/%s' % (rm_bytes, rm_md5, rm_bytes_land, rm_md5_land)
vc1_rc, vc1_ver = None, None
for _vc in (VER24, VER24B):
    rc = line_of(_vc, r'(?m)^VERIFY_RC=(\d+)$', '终态复核退出码', 1)
    ver = line_of(_vc, r'(?m)^VERDICT=(\w+)$', '终态复核裁决', 1)
    assert (rc, ver) == ('0', 'MANIFEST_STILL_TRUE'), 'ABORT: 终态复核不是那句绿：' + os.path.basename(_vc)
    if _vc == VER24:
        vc1_rc, vc1_ver = rc, ver
v2_cut = line_of(VER24B, r'(?m)^CLEAN_UP_TO=(.+?)（', '第二遍终态复核的写载体时刻', 1)
t_v24 = line_of(VER24, r'(?m)^CLEAN_UP_TO=(.+?)（', '首遍终态复核的写载体时刻', 1)

t_rd9 = line_of(C_RD9, r'(?m)^R55 第九次读数', '第九次读数首行')
rd9_run = re.search(r'现跑于 (' + TS + ')', t_rd9).group(1)
assert rd9_run == rd9_at, 'ABORT: 订正载体引的第九次读数时刻与该文件首行不符'
t_docs9 = line_of(C_RD9, r'(?m)^DOCS ', 'docs 第九遍快照行')
docs_n, docs_tbl = re.search(r'^DOCS files=(\d+)\s+表格行=(\d+)', t_docs9).groups()
docs_at = re.search(r'SNAPSHOT_AT=(' + TS + ')', t_docs9).group(1)
gate_of, gate_hits = re.search(r'OF=(\d+) HITS=(\d+)', t_docs9).groups()
assert gate_hits == '0' and int(docs_tbl) + 1 == int(docs_n) == int(gate_of) + 1, 'ABORT: docs 第九遍那格读数不自洽'
assert docs_at in t_docs_land and 'DOCS ' + docs_n + ' 只' in t_docs_land, \
    'ABORT: 两只载体对 docs 第九遍的读数不互核（%s / %s）' % (docs_at, t_docs_land[:40])

# ---------- 现读：四只记忆文件（本遍只复核，不写盘）+ git 现场 + 串口 ----------
s_mb, s_mi, s_ub, s_ui = stat(PMB), stat(PMI), stat(UMB), stat(UMI)
assert s_mb[1] == int(pl1) and s_mb[0] == int(pb1) and s_mi[0] == int(pi1) and s_mi[1] == int(pilf), \
    'ABORT: 订正载体自述的改后值与盘上现状不符：正文 (%d,%d) / 索引 (%d,%d)' % (s_mb[0], s_mb[1], s_mi[0], s_mi[1])
git = lambda *a: subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a),
                                capture_output=True, cwd=REPO).stdout.decode('utf-8', 'replace')
rev = git('rev-list', '--count', 'origin/main..HEAD').strip()
assert rev.isdigit(), 'ABORT: rev-list 读数不是数字：' + rev[:20]
por = [l for l in git('status', '--porcelain').split('\n') if l.strip()]
ports = sorted(__import__('serial.tools.list_ports', fromlist=['comports']).comports(), key=lambda c: c.device)
port_names = ', '.join(p.device for p in ports)
has14 = 'COM14' in port_names

# ---------- 两只待写 CRLF 正文（全部插值自上面现读；正文里零反斜杠）----------
FREQ_HEAD = ('## 2026-09-24（R55 第三批：项目记忆落地 + 同一批里两次自查订正）新增 4 条'
             '（根族：**我把"脚本自己那一次的读数"当成了"被引用那一次动作的读数"，还拿一把期望值靠猜的断言去验已经写进盘的东西**）')
FREQ_LEAD = ['> 一句话总纲：本批屏侧仍然一个字节没动（没烧录、没碰串口、COM14 ' + ('在' if has14 else '不在') + '），',
             '> 四条同根：**读数是真的，但它所属的那一次动作是我脑补的** —— 时刻、裁决、期望值三处各一次。']
FREQ_ENTRIES = [
    [
        '[错误类型] **同一行里并列 N 只时刻，其中一格用了落地脚本自己的 NOW ⇒ 它冒充的是"更早那一次动作的时刻"，读数比真值更新、没有工具会报警（项目记忆 (104)）**',
        '→ 症状：项目记忆 R55 段标题并列四只时刻「12:14:51 §38.18 落盘 → 12:53:39 gen 24 末版 → **13:33:42** docs 第九遍 → **14:07:20** backups/README.md 第九次读数」。前三只各自现读于对应载体，第四只却是正文写盘那一刻；第九次读数真正发生在 **{rd9_at}**（载体 `hardware/r55_backups_readme9.txt` 第 1 行，本遍现读）。分位差 **{gap_min} 分钟**。',
        '→ 形状：与 (69)/(71)「凭证写的时刻不等于它标的那一刻」同族，新出的一层是**错位发生在同一行内部**：并列的四格看着同源，脚本里却只有一个 NOW 变量，它落到哪一格全凭手滑。载体上没有任何字段能反证它 —— 那一格本来就该"是"某个动作的时刻，格式、非空、正则全都放行。',
        '→ 为什么它危险：假时刻读起来比真时刻更"新"也更自洽 ⇒ 下一轮拿它做先后判据会得到**错的因果顺序**（本批就用它算过一次 24 分钟这类量），而"更晚 ⇒ 更新 ⇒ 更可信"这条默认推理刚好被它利用。',
        '→ 正确做法：①脚本里的 NOW **只允许落在点名"本遍现跑 / 本节登记"的那一格**，其余每一格现读**那只动作自己的载体字段**（订正批载体 `hardware/r55_fix_memory_r55.txt` 的 TIME 行就是这么把差值算出来的）；②等长换字（本批时刻那一格各 19 字符）不动字节数只动 md5 ⇒ 修完必须**同时**给行数与 md5，别只报"字节没变"；③同一行里若某格与脚本 NOW 逐字相同，先怀疑来源再怀疑真值。',
        '→ **同族**：项目记忆 (69)（凭证时刻/日期三型）、(71)、(101)、(104)；用户记忆 `feedback-verifiable-acceptance.md`「读数不落盘等于没跑」。',
    ],
    [
        '[错误类型] **取证文件里"上一遍的裁决"与"本遍的裁决"逐字同形 ⇒ 裸子串 search 静默取回上一遍，把一次失败登记成本遍结论（项目记忆 (103)）**',
        '→ 症状：`hardware/ht305_sync/evidence/r55_roundtrip_2.txt` 第 4 行是 `PRIOR_VERDICT=VERDICT=SCP_FAILED`（上一遍转抄），第 18 行才是 `VERDICT=REMOTE_CARRIES_PLAINTEXT`（本遍 {rt_at} 的真结果）。落地器按子串起搜、取第一个匹配 ⇒ 命中第 4 行，并把 `VERDICT=` 一起吞进值里。项目正文与索引两处因此登记成"重跑 SCP_FAILED"，而同一半句的后半写着"服务器那一份仍带明文" ⇒ **一条自相矛盾的话，两只量具全放行**（grep 有值、断言非空）。',
        '→ 形状：与 (63)~(65)「逐字派生会把上一代恰好没踩到的缺陷派生过来」同族，本条是它的**读侧**版本：写侧模板没错，错在解析器只认子串。取证文件天然允许历史同形串（转抄、对照、引用都长这样）⇒ "命中即真"这类判据在读侧根本不成立。',
        '→ 为什么它危险：这句裁决是"服务器侧那份能不能当回滚源"的唯一判据。登记成失败会让下一轮把事实读成"往返根本没跑通"⇒ 重传、重跑往返、又一次拿重跑洗绿；而真实事实是**跑通了、远端带明文**。',
        '→ 正确做法：①**行首锚 + 按行取 + 取末位**（`(?m)^VERDICT=` 然后列表末位）；②与同文件 `PRIOR_VERDICT=` 捕到的值做**互斥断言**——两值同形即说明锚没生效；③值必须落在**在册名单**里才放行；④把**取到的行号**随值一起落册（订正载体 SRC 行第 4 / 第 18 行就是这种形状）；⑤缺陷**当场复现**而不是事后叙述：裸 search 取到哪个值，就把那个值原样打进载体（`NAIVE_PARSER_REPRO`）。',
        '→ **同族**：项目记忆 (63)~(65)、(74)、(82)、(103)；用户记忆 `feedback-verifiable-acceptance.md`「汇总行不许只认一种格式」「否定式断言要配前置钉」。',
    ],
    [
        '[错误类型] **崩溃点在 write 之后：只登记"崩溃那遍不作数"不够 —— 写盘型落地器复跑就是二次追加，必须给它自己装幂等闸**',
        '→ 症状：本批两遍都栽在同一种形状上。第一遍（落地器）四只记忆文件写盘成功，随后在**写载体**那一步崩 `TypeError: %d format: a real number is required, not str` ⇒ 盘上已有新内容、载体零只；第二遍（订正器）换字与三行追加同样落盘成功，随后崩 `AssertionError`（期望值是我猜的，见第 4 条）⇒ 同样没载体。此后任何一次"照着原脚本再跑一遍"都会把 (101)~(104) 再追加一次。',
        '→ 形状：(81)「首跑崩溃的取证脚本也要入库」与 (185)「崩溃那次的读数不作数」合起来还缺最后一环：它们管的是**证据**，没管**副作用**。写盘型脚本的副作用发生在断言之前 ⇒ "不作数"这句话在副作用面前是反的 —— 数不作数，文件已经改了。',
        '→ 为什么它危险：崩溃点越靠后（本批两次都在"业务改动全部做完之后"），复跑的破坏越大，而 traceback 本身把人**指向**"补跑一次就完事"这条错误路径；第二次追加连 grep 都看不出问题（同一段落盘上出现两遍，只有锚点计数用得上）。',
        '→ 正确做法：①落地器自带**幂等闸**：为每处落地内容定一只锚，进入时现读，把"半落地"（锚只中一半）直接 ABORT；②已落地那一遍**跳过写盘**，改从盘上**反推**"追加之前"的读数（截到锚之前）并与已落台账行里的历史数互核 ⇒ 复跑那一遍仍然给全套复核，只是不动盘；③MODE 写进载体首行；④崩溃事实本身作为一行登记进载体（`LANDING_SEQUENCE`），不删不改；⑤无凭证的历史数（改前 md5）写 `NOT_RECORDED` 并说明理由，不编一个数补位。',
        '→ **同族**：项目记忆 (81)、(95)（三步序：体检 / 写盘前零容忍 / 写盘后独立回读）、(185)、(103)；用户记忆 `reference-qoder-tool-mapping.md` 第七类自伤。',
    ],
    [
        '[错误类型] **断言的期望值写成我眼睛数出来的常数 ⇒ 期望本身是错的（(104) 我写 3、实为 4），而这条断言恰好落在写盘之后，等于用一把猜的尺子去否决一次已经生效的落地**',
        '→ 症状：订正器最后一道复核写 `assert rb.count(那条序号) == 3`。盘上真实计数是 **4**：订正段自身 3 处（行首、"上面 (103)-(104) 两条"、"③序数 (101)-(102) → (101)-(104)"）+ 段标题 1 处。3 是我扫了一眼小标题数出来的，没数段内自引的那两处。',
        '→ 形状：与 R39「写最坏值前先证明分项可同时成立」、R40「公布的数必须等于它自己那行分项之和」同族，新层是：**断言里的期望值也是"公布的数"** —— 它同样必须给出算法与分项，否则它和被它检查的那个数一样不可信；而这个数的算法（谁引了谁）就在被检文本里，只有从文本推导才不会漂。',
        '→ 为什么它危险：猜的期望值有两种坏法，本批撞的是第二种 —— 猜**小**了在正常状态上报假红，并且因为崩点在写盘之后而制造"要不要重跑"的错误诱惑（直接接上第 3 条）；猜**大了**永远为真、把缺陷放过去。同一形状在 gen 22 那族（跨秒假红）里已登记过一次，那次是概率，这次是手算。',
        '→ 正确做法：①期望值改写成**由被检文本自身推导**的式子：`全文 (103) = 订正段自身 (103)` ∧ `全文 (104) = 订正段自身 (104) + 1`，其中 +1 那一项点名"段标题那一处"；②加**前置钉**：把订正段整段抹掉之后 `(104)` 必须**恰好 1 处**，让 +1 自己是读数而不是命题；③载体把四个数并列打印（`PMEM_COUNTS` 行），复核者不复跑也能验。',
        '→ **同族**：项目记忆 (57)（裸 `grep -c` 是快照）、(59)、(97)、(104)；用户记忆 `feedback-verifiable-acceptance.md`「数字连算法与漏判」「崩溃那次的读数不作数」。',
    ],
]
LEDGER_TMPL = ('\r\n> **【@T@ 复跑｜R55 第三批 4 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'
               '全文 `^[错误类型]` 条数 = **@BK@**、`wc -l` = **@BL@**；追加之后现算，'
               '**口径 = 含本台账行自身的最终字节串**：`^[错误类型]` = **@AK@**、`wc -l` = **@AL@**'
               '（两把尺都在最终串上数，不数未含台账行的中间串 —— 见 R55 第二遍第 4 条与 (99)）。'
               '本批四条全部出自**同一批自己造成、同一批自己订正**的两处假读数：①②④ 三条互为因果，'
               '正文登记在排查记录 §38.20，取证载体 `hardware/r55_fix_memory_r55.txt`。')

SEC = f'''
### 38.20 R55 第三批 = 项目记忆/用户记忆落地 + **同一批里两次自查订正**（{BODY_AT} 四只记忆文件落盘 → {LAND_AT} 补载体 → {FIX_AT} 换字订正 → {FIX_CARRIER_AT} 补载体 → {{RUN_AT}} 本节登记；**没烧录、没碰串口、没 push、屏侧零进展**）

- **本节登记什么**：§38.19 ⑦ 把"项目记忆 (101)"点名在"本节没做 ⑦"那一格里 ⇒ 本节就是那一步的落账，外加它**当场抓出的两处假读数**和**订正批自己再崩的一次**。四只记忆文件（项目正文、项目索引、用户 `reference-qoder-tool-mapping.md`、用户索引）都在 {BODY_AT} 那一遍写盘；订正在 {FIX_AT}；两只载体分别补齐于 {LAND_AT} 与 {FIX_CARRIER_AT}。本遍**只追加两只 CRLF 文档 + 一只载体**，屏侧一个数没动、归档目录一只没落。
- **① 落进去的内容**：项目正文新增 (101)(102) 两条 + "R55 现场态换代"整段（段末钉"本批定下的 (101)-(104)"）+ 项目索引第 5 行换代；用户侧新增**第七类工具自伤**（非 raw 的 python 串里写 Windows 路径 ⇒ 反斜杠塌成一只隐形 CR，`grep` / Edit / `Read` 三只量具同时看不见 —— §38.18 ③ 那一族的泛化），用户索引随之由"六类自伤"改称"七类自伤"。(101) 讲的是 gen 22 那次跨秒假红（同一次运行取两只 `now()`），(102) 讲的是纯插入式落地器不验节间空行。现值（本遍 stat）：项目正文 {money(s_mb[0])} B / {s_mb[1]} 行 / CR {s_mb[2]} / md5 `{s_mb[3]}…`，项目索引 {money(s_mi[0])} B / {s_mi[1]} 行 / md5 `{s_mi[3]}…`，用户工具映射 {money(s_ub[0])} B / {s_ub[1]} 行，用户索引 {money(s_ui[0])} B / {s_ui[1]} 行 —— 四只 CR 计数全 {s_mb[2] + s_mi[2] + s_ub[2] + s_ui[2]}（纯 LF）。
- **② 落地器第一遍崩在"写载体"那一步，而崩点在写盘之后 ⇒ 复跑等于二次追加**：四只文件已按上面的时刻落盘，随后 `TypeError: %d format: a real number is required, not str`（我把字符串喂给了 `%d`）当场让载体没写出来。修法不是"下次记得先看盘"，而是给落地器装**幂等闸**：锚现读 + 半落地直接 ABORT + MODE 分流，{LAND_AT} 那一遍以 `MODE={LAND_MODE}` 跳过写盘、只复算并补写载体（`hardware/r55_land_memory_r55.txt` 第 1 行在册，其 `LANDING_SEQUENCE` 行点名崩溃事实）。⇒ 新出的一层：(81) 与"崩溃那遍读数不作数"管的都是**证据**，写盘型脚本的**副作用**发生在断言之前 ⇒ "不作数"在副作用面前是反的，必须让脚本自己幂等。
- **③ 落进去的正文里有两处假读数（本批自己造成，订正在 {FIX_AT}）**：(a) **裁决读反**：`evidence/r55_roundtrip_2.txt` 第 4 行 `PRIOR_VERDICT=VERDICT=SCP_FAILED` 与第 18 行 `VERDICT=REMOTE_CARRIES_PLAINTEXT` 逐字同形，裸子串 search 取回的是**上一遍**那个失败值、并把前缀一起吞进值里 ⇒ 项目正文与索引两处登记成"重跑 SCP_FAILED"，而同一半句后半写着"服务器那一份仍带明文" ⇒ 一条自相矛盾的话、两只量具全放行 → 立 **(103)**（行首锚 + 取末位 + 与 PRIOR 互斥 + 值落名单，四件都在执行件里兑现）。(b) **时刻冒充**：段标题四只并列时刻里第四只用了脚本自己的 NOW（{fake_at}），而 backups README 第九次读数真正在 **{rd9_at}**（`hardware/r55_backups_readme9.txt` 第 1 行）⇒ 分位差 {gap_min} 分钟 → 立 **(104)**。换字等式（现读 `hardware/r55_fix_memory_r55.txt` 的 PMEM_BODY / PMEM_INDEX 两行）：项目正文 {money(int(pb0))} → {money(int(pb1))} B、{pl0} → {pl1} 行；索引 {money(int(pi0))} → {money(int(pi1))} B、LF 仍 {pilf}（只在一行内换字）。时刻那一对**等长**（各 19 字符）⇒ 字节数只由裁决串与三行追加决定。
- **④ 订正批自己又崩一次，崩在我猜的常数上**：`assert rb.count((104) 那只序号) == 3` —— 3 是眼睛数出来的，实为 **4**（订正段自身 3 处 + 段标题 1 处），而崩点又在写盘**之后** ⇒ 记忆文件已订正、载体第二次没落。第二遍走同一只脚本的幂等闸（判为 `MODE={FIX_MODE}`，只复算 + 补载体 {FIX_CARRIER_AT}），并把期望值改成**由被检文本推导**：`全文 (103) = 订正段自身 (103)` ∧ `全文 (104) = 订正段自身 (104) + 1`，另加前置钉"订正段之外 (104) 恰好 1 处"。现值 {c103} / {c104}（载体 `PMEM_COUNTS` 行并列四个数）。改前 md5 **不复算**（崩那遍没落载体 ⇒ 无凭证，载体明写 `MD5_BEFORE=不复算`），改前字节/行数从订正段自述等式现读并与盘上现状闭合。⇒ 这条也进了 FreqErr 台账：**断言的期望值同样是"公布的数"，必须带算法**。
- **⑤ 现场态（本遍现跑，不是登记常量）**：`git rev-list --count origin/main..HEAD` = **{rev}**、`git status --porcelain` = **{len(por)} 行**；串口 = `{port_names}` ⇒ **COM14 {"在" if has14 else "仍不在"}**，§38.13 那两行判据样本数照旧 0、肉眼确认 0 次 ⇒ **不播提示音**；指纹（现读 `hardware/r55_land_memory_r55.txt` 第 8 行）：build 产物 md5 `{bin_new[0][:8]}…`（{money(int(bin_new[1]))} B）**≠** 板上 = r43 归档 `4842a3a0…`（{money(int(bin_old[1]))} B）⇒ **"待烧 = 板上"这一格在 R51/R52 之后已换代过一次**（r53 那批编出来的镜像一直没烧），本批**零代码进镜像、也没烧**，`esp_gpio_hold_en()` 照旧等 hold-on 探针的真机读数；这一格的定性（要不要重冻待烧指纹）列为后续义务，本节不替它下结论。
- **⑥ 写盘半径与末版封界**：gen 24 末版三字段（`MANIFEST.txt` 末三行）与落地批载体**逐字互核**通过 = TOTAL {m_n} / {money(m_b)} B / BOM {m_bom}；终态复核**两遍在册都绿** —— `{vc1_ver} / VERIFY_RC={vc1_rc}`（写载体于 {t_v24}）与第二遍（写载体于 {v2_cut}，即 docs 第九遍 + backups 第九次读数之后）⇒ 末版封界到本批 paperwork 之前都没破。本批所有新文件（落地器、订正器、三只载体、本节落地器）一律落 `hardware/` 根 ⇒ **`hardware/ht305_sync/` 一只没多、一只没改**。docs 快照停在第九遍 {docs_n} 只 @{docs_at}（凭据闸 OF {gate_of} / HITS {gate_hits}）、backups README 停在第九次读数 {rd9_run} —— **§38.20 与 FreqErr 这一落让这两格同时过期** ⇒ 第十遍 docs 快照 + 第十次读数是本节之后的义务，读数落各自那一格。
- **⑦ ht305 侧本批不追第 14 代（是决定，不是疏漏）**：服务器那一份停在第 13 代（{sync_n} 只 / {money(int(sync_b))} B / 包 {money(int(pkg_b))} B md5 `{pkg_md5[:8]}…` / 聚合 `{agg_md5[:8]}…` / 解包根 `zsynctest15` / 往返真值 `{TRUE_V}` @{rt_at}）。此后仓库侧已叠了 docs 第九遍、backups 第九次、四只记忆文件、排查记录本节、FreqErr 四条 ⇒ **已知滞后**。不追的理由：现行同步链把每一步证据写进 `hardware/ht305_sync/evidence/`，而那目录刚被 gen 24 封成末版（§38.19 ④）⇒ 同步一次 = 亲手把末版降级成非末版。⇒ **义务（下一批先做）**：要么先把"同步证据落归档外"的机制建起来（与终态复核载体同口径，改落 `hardware/`），要么下一批在 paperwork 之前先同步、再重新冻结一代。上一遍载体第 4 行那句"重跑 SCP_FAILED"（`hardware/r55_land_memory_r55.txt`）同样出自 ③(a) 那只错解析 ⇒ **保留原样、以本遍为准**，不拿重跑洗（(74)(82) 同族）。
- **本节没做（点名）**：① 没烧录、没碰串口（本遍只 `comports()` 只读列口）；② 没 `git push`、零历史重写（rebase / filter-branch / **amend** 都没碰）；③ 没新建备份根（`diff -rq` 那三把尺本批未复跑，仍是义务）；④ 零删除，含 `%TEMP%` 里那只在册明文抓回件；⑤ 提交轮 #9 在本节之后；⑥ 服务器侧那一份**仍带明文** ⇒ ht305 任何一份都**不能当回滚源**；⑦ 屏侧唯一未取到的维度（hold-on 探针真机读数）照旧空着；⑧ 待烧指纹那一格只登记了"两值不等"，未定性。
'''

# ---------- 幂等闸：两只文件各自的锚（半落地直接 ABORT，全落地跳过写盘）----------
freq_old = rd(FREQ)
doc_old = rd(DOC)
for _p, _t in ((FREQ, freq_old), (DOC, doc_old)):
    assert _t.endswith('\r\n'), 'ABORT: %s 不以 CRLF 结尾 ⇒ 追加会造出半行' % os.path.basename(_p)
    crlf_pure(_p)
led_freq = [l for l in freq_old.split('\r\n') if '复跑｜R55 第三批' in l]
led_doc = '### 38.20' in doc_old
assert len(led_freq) <= 1, 'ABORT: 本批台账行已在盘上出现 %d 次 ⇒ 有人二次追加过，先查再落' % len(led_freq)
assert (len(led_freq) == 1) == led_doc, \
    'ABORT: 半落地（FreqErr=%s / §38.20=%s）⇒ 上一遍只写完一半，拒绝补齐' % (bool(led_freq), led_doc)
MODE = 'REWROTE_CARRIER_ONLY' if led_doc else 'LANDED_NOW'
FIX_AT3, PAIRS, INS_ABOVE, TAIL_N = '无（本遍新建）', '三把尺尚未产生', 0, 0
LATER_WHY = '本遍即写盘那一遍，窗口右界 == 文件末尾'
# 写盘那一遍：本批那两段就是文件尾巴 ⇒ 窗口 == 文件，"窗口之外"四格恒为空/0
FREQ_TAIL_REST = DOC_TAIL_REST = ''
DOC_LATER, DOC_LATER_HEADS = 0, 0


def batch_rows(text):
    """本批台账行 + （若已存在的）本批订正行的 0-based 下标。"""
    ls = text.split('\r\n')
    return [i for i, l in enumerate(ls)
            if ('复跑｜R55 第三批' in l) or (l.startswith('> **【订正｜') and 'R55 第三批' in l)]


def gap_above(text):
    """本批台账/订正行上方必须**恰好一只**空行（(102) 族）；返回不满足的行号（1-based）。"""
    ls = text.split('\r\n')
    bad = []
    for i in batch_rows(text):
        n, j = 0, i - 1
        while j >= 0 and not ls[j].strip():
            n, j = n + 1, j - 1
        if n != 1:
            bad.append(i + 1)
    return bad


FIXNUM = re.compile(r'条数 = \*\*(\d+)\*\*、行数 = \*\*(\d+)\*\*')
PAT_B = r'全文 `\^\[错误类型\]` 条数 = \*\*(\d+)\*\*、`wc -l` = \*\*(\d+)\*\*'
PAT_A = r'`\^\[错误类型\]` = \*\*(\d+)\*\*、`wc -l` = \*\*(\d+)\*\*'


def led_pair(seg, pat, why):
    """从台账行的一段里取两个数；**没命中就 ABORT**，不许让 AttributeError 当报错。"""
    m = re.search(pat, seg)
    assert m, 'ABORT: 台账行的 %s 段被解析式判为不同形 ⇒ 写的一侧与读的一侧不是一套：%r' % (why, seg[:70])
    return (int(m.group(1)), int(m.group(2)))


def split_ledger(line):
    parts = line.split('追加之后现算，')
    assert len(parts) == 2, \
        'ABORT: 台账行的分节锚 `追加之后现算，` 出现 %d 次 ⇒ 台账行结构与解析式不同形：%r' % (len(parts) - 1, line[:70])
    return parts


def selftest_ledger(line, exp_b, exp_a):
    """阳性对照：用**读侧同一套解析式**去解**写侧刚产出的那行台账**，两对数必须各自回来。"""
    pre, post = split_ledger(line)
    assert (led_pair(pre, PAT_B, 'BEFORE'), led_pair(post, PAT_A, 'AFTER')) == (exp_b, exp_a), \
        'ABORT: 读侧解析式解不出写侧刚产出的台账行 ⇒ 幂等闸第一次复跑就会崩：(%s) vs (%s)' % (
            (led_pair(pre, PAT_B, 'BEFORE'), led_pair(post, PAT_A, 'AFTER')), (exp_b, exp_a))


if MODE == 'LANDED_NOW':
    RUN_AT = NOW_AT
    body_lines = ['\r\n'.join(e) for e in FREQ_ENTRIES]
    freq_app = '\r\n' + FREQ_HEAD + '\r\n\r\n' + '\r\n'.join(FREQ_LEAD) + '\r\n\r\n' + '\r\n\r\n'.join(body_lines)
    b_kind, b_lines = kinds(freq_old), freq_old.count('\r\n')
    b_bytes, b_md5 = len(freq_old.encode('utf-8')), hashlib.md5(freq_old.encode('utf-8')).hexdigest()[:8]
    PRE_KIND, _witness = '现读', '本遍即写盘那一遍'
    app = freq_app.format(rd9_at=rd9_at, gap_min=gap_min, rt_at=rt_at)
    a_kind, a_lines = kinds(freq_old + app + '\r\n' + LEDGER_TMPL + '\r\n'), \
        (freq_old + app + '\r\n' + LEDGER_TMPL + '\r\n').count('\r\n')
    assert a_kind == b_kind + len(FREQ_ENTRIES), 'ABORT: 台账条数增量不等于本批条数：%d -> %d' % (b_kind, a_kind)
    b_kind_led, a_kind_led = b_kind, a_kind      # 写盘那一遍：台账行的两个数就是本遍现算的数
    ledger = (LEDGER_TMPL.replace('@T@', RUN_AT).replace('@BK@', str(b_kind)).replace('@BL@', str(b_lines))
              .replace('@AK@', str(a_kind)).replace('@AL@', str(a_lines)))
    selftest_ledger(ledger, (b_kind, b_lines), (a_kind, a_lines))   # 写侧/读侧同形，当场自证
    FREQ_NEW = app + '\r\n' + ledger + '\r\n'
    FREQ_LAND = FREQ_NEW
    freq_new = freq_old + FREQ_NEW
    assert (kinds(freq_new), freq_new.count('\r\n')) == (a_kind, a_lines), \
        'ABORT: 把四个数回填进台账之后两把尺漂了 (%d,%d) vs (%d,%d) ⇒ 数算在了中间串上 ((99) 族)' % (
            kinds(freq_new), freq_new.count('\r\n'), a_kind, a_lines)
    assert freq_new.startswith(freq_old + app), 'ABORT: 待写串与 freq_old + 正文块不逐字同构'
    assert not gap_above(freq_new), 'ABORT: 待写的台账行上方不是恰好一只空行 ⇒ (102) 那一族，写盘前拦下：%s' % gap_above(freq_new)
    sec_body = SEC.replace('{RUN_AT}', RUN_AT)
    assert ' → ' + RUN_AT + ' 本节登记' in sec_body
    SEC_LAND = '\r\n' + sec_body.strip('\r\n').replace('\n', '\r\n') + '\r\n'
    doc_new = doc_old + SEC_LAND
    d_pre_str = doc_old
    FREQ_AT_STR, DOC_AT_STR = freq_new, doc_new      # 本批终态串 == 文件（写盘那一遍窗口即全文件）
    heads_before, heads_after = heads(doc_old), heads(doc_new)
    assert heads_after == heads_before + 1, 'ABORT: 标题数没按 +1 走：%d -> %d' % (heads_before, heads_after)
    assert (heads_before, money(len(doc_old.encode('utf-8'))), str(doc_old.count('\r\n'))) == \
        (int(doc_h23_land), doc_bytes_land, doc_lines_land), \
        'ABORT: 落地批在册的"§38.20 之前"三读数与盘上不符 ⇒ 本节之前有人又动了排查记录'
    assert hashlib.md5(doc_old.encode('utf-8')).hexdigest()[:8] == doc_md5_land, \
        'ABORT: 排查记录 md5 与落地批在册值不符 ⇒ 上一遍之后又变过'
    assert not blank_gap_lines(doc_old), 'ABORT: 本节之前就有节标题缺空行，与落地批读数 0 不符'
    assert freq_new.startswith(freq_old) and doc_new.startswith(doc_old), 'ABORT: 不再是纯追加，历史行被改写'
else:
    # 跳过写盘：从盘上**反推**"追加之前"的状态（截到本批锚之前），再与已落台账行里的四数互核
    cut = freq_old.index(FREQ_HEAD)
    freq_before_str = freq_old[:cut].rstrip('\r\n') + '\r\n'
    b_kind, b_lines = kinds(freq_before_str), freq_before_str.count('\r\n')
    b_bytes, b_md5 = len(freq_before_str.encode('utf-8')), hashlib.md5(freq_before_str.encode('utf-8')).hexdigest()[:8]
    PRE_KIND = '反推'   # 本遍没读改前的盘，那一格是从"截到本批锚之前"复原出来的
    assert b_md5 != hashlib.md5(freq_old.encode('utf-8')).hexdigest()[:8], \
        'ABORT: 反推串与盘上现状同 md5 ⇒ 锚点截断没生效，"改前"那一格是假的'
    # witness = 唯一那次 MODE=LANDED_NOW 的载体（只有它是"现读改前的盘"；后面的复跑载体都是反推，不能自证自）
    _wit = [c for c in _self_prior
            if 'MODE=LANDED_NOW' in line_of(os.path.join(HDIR, c), r'(?m)^R55 第三批 paperwork 落地器', '本脚本前序载体首行')]
    assert len(_wit) == 1, 'ABORT: 现存 %d 只前序载体里，写盘那一遍（MODE=LANDED_NOW）的有 %d 只 ⇒ 反推值没有 witness 可核' % (
        len(_self_prior), len(_wit))
    _pl = line_of(os.path.join(HDIR, _wit[0]), r'(?m)^FREQ 追加之前现读 ', '写盘那一遍载体的 FREQ 行')
    _pb, _pm = re.search(r'FREQ 追加之前现读 ([\d,]+) B.*?md5 (\w{8}) -> ', _pl).groups()
    assert money(b_bytes) == _pb, \
        'ABORT: 反推的改前字节 %s != 写盘那一遍现读在册 %s ⇒ 中间别处动过 FreqErr 的字节而行数量没变' % (
            money(b_bytes), _pb)
    assert b_md5 == _pm, \
        'ABORT: 反推串的 md5(%s) != 写盘那一遍在册的改前 md5(%s) ⇒ 复原不逐字，本遍"改前"两格不可信' % (
            b_md5, _pm)
    _witness = os.path.basename(os.path.join(HDIR, _wit[0]))
    RUN_AT = re.search(r'【(' + TS + ') 复跑｜R55 第三批', led_freq[0]).group(1)
    pre_b, post_b = split_ledger(led_freq[0])
    b_kind_led, b_lines_led = led_pair(pre_b, PAT_B, 'BEFORE')
    a_kind_led, a_lines_led = led_pair(post_b, PAT_A, 'AFTER')
    assert (b_kind, b_lines) == (b_kind_led, b_lines_led), \
        'ABORT: 从盘上反推的 BEFORE 两数与台账那一遍现读的不符：(%d,%d) vs (%d,%d) ⇒ 中间有人动过 FreqErr' % (
            b_kind, b_lines, b_kind_led, b_lines_led)
    disk_kind, disk_lines = kinds(freq_old), freq_old.count('\r\n')
    _ls = freq_old.split('\r\n')
    _li = [i for i, l in enumerate(_ls) if '复跑｜R55 第三批' in l][0]
    _nxt = [i for i in range(_li + 1, len(_ls)) if _ls[i].startswith('## ')]
    if (disk_kind, disk_lines) != (a_kind_led, a_lines_led):
        # 落地之后本批窗口内唯一被允许的改动 = 台账行之上补 1 只空行 + 其下纯追加"空行 + 本批订正行"（(102) 族的就地补账）
        # 窗口的右界 = 下一批的批次标题行（含其前那只空行归下一批）；没有下一批就到文件末尾。
        # 不划这个界，任何后续批次一追加就会把本闸染成假红 ⇒ 下一批落地后本脚本必须仍然绿。
        _nh = _nxt[0] if _nxt else len(_ls)
        _end = _nh - 1 if _nh < len(_ls) else len(_ls) - 1     # 本批窗口末行的 1-based 行数
        if _nh < len(_ls):
            assert _ls[_nh - 1].strip() == '' and _ls[_nh].startswith('## '), \
                'ABORT: 窗口右界没落在批次边界上（%r / %r）⇒ 是在半截内容里切的' % (_ls[_nh - 1][:20], _ls[_nh][:20])
        tail = _ls[_li + 1:_end]
        assert all((not l.strip()) or l.startswith('> **【订正｜') for l in tail), \
            'ABORT: 本批窗口内、台账行之后出现了"空行/订正行"以外的内容 ⇒ 不是纯追加：%s' % tail[:2]
        fixl = [l for l in tail if l.startswith('> **【订正｜')]
        ins_above = _li - (a_lines_led - 1)         # 台账行之上净插入的行数（台账当年就在最后一行）
        assert ins_above == 1 and len(fixl) == 1, \
            'ABORT: 窗口末行比台账多 %d 行，但"之上补的空行"=%d 只、订正行=%d 只 ⇒ 还有一处改动没被点名' % (
                _end - a_lines_led, ins_above, len(fixl))
        assert _end - a_lines_led == ins_above + len(tail), \
            'ABORT: 窗口行数差(%d)与盘上物理结构(上 %d + 下 %d)不等 ⇒ 中间别处还动了行' % (
                _end - a_lines_led, ins_above, len(tail))
        pairs = [(int(a), int(b)) for a, b in FIXNUM.findall(fixl[0])]
        assert len(pairs) == 3, 'ABORT: 本批订正行应当并列三把尺（改前/补空行后/终态），实际 %d 把' % len(pairs)
        assert pairs[-1] == (a_kind_led, _end), \
            'ABORT: 订正行登记的终态两数与本批窗口末行不符：%s vs (%d,%d)' % (pairs[-1], a_kind_led, _end)
        assert pairs[0][1] == a_lines_led, \
            'ABORT: 订正行自述的"改前行数"(%d) 不等于台账登记的 AFTER(%d) ⇒ 两行量的不是同一块盘' % (pairs[0][1], a_lines_led)
        assert all(k == a_kind_led for k, _ in pairs), \
            'ABORT: 订正三把尺里有哪一把的条数动了条目：%s vs 台账 %d' % (pairs, a_kind_led)
        FIX_AT3 = re.search(r'订正｜(' + TS + ')', fixl[0]).group(1)
        PAIRS, INS_ABOVE, TAIL_N = pairs, ins_above, len(tail)
    else:
        _end, ins_above, tail = disk_lines, 0, []
        assert not _nxt, 'ABORT: 盘上两把尺与台账 AFTER 相等、却已存在下一批标题 ⇒ 窗口算式与本批状态不自洽'
    LATER_N = len(_nxt)
    LATER_LINES = disk_lines - _end
    assert LATER_LINES >= 0, 'ABORT: 窗口末行(%d) 超过文件行数(%d)' % (_end, disk_lines)
    if LATER_N:
        assert LATER_LINES >= 2, 'ABORT: 有 %d 处下一批标题却只多 %d 行 ⇒ 后续批次只落了半截' % (LATER_N, LATER_LINES)
        LATER_WHY = '本批窗口止于第 %d 行；其后 %d 只后续批次标题、共 %d 行不属于本批断言范围' % (
            _end, LATER_N, LATER_LINES)
    else:
        assert _end == disk_lines and LATER_LINES == 0, \
            'ABORT: 没有后续批次标题，窗口却没到文件末尾（窗口末 %d / 盘上 %d）' % (_end, disk_lines)
        LATER_WHY = '本批之后无后续批次（窗口 == 文件尾）'
    a_kind, a_lines = disk_kind, disk_lines
    freq_new = FREQ_NEW = freq_old
    # 本批断言范围（窗口）止于第 _end 行：FREQ_LAND 只含本批那一段，后续批次一追加就会把 endswith 式的闸染成假红
    _freq_win = '\r\n'.join(_ls[:_end]) + '\r\n'
    assert freq_old.startswith(_freq_win), 'ABORT: 台账窗口不是盘上开头的逐字前缀 ⇒ 行序与字符序对不上'
    FREQ_LAND = _freq_win[cut:]
    FREQ_TAIL_REST = freq_old[len(_freq_win):]
    dcut = doc_old.index('### 38.20')
    _lsd = doc_old.split('\r\n')
    _i20 = [i for i, l in enumerate(_lsd) if l.startswith('### 38.20')]
    assert len(_i20) == 1, 'ABORT: §38.20 在盘上有 %d 处 ⇒ 幂等锚本身不唯一' % len(_i20)
    _dnx = [i for i in range(_i20[0] + 1, len(_lsd)) if _lsd[i].startswith(('### ', '## '))]
    if _dnx:
        assert _lsd[_dnx[0] - 1].strip() == '', \
            'ABORT: §38.20 窗口右界没落在节边界上（前一行 %r）⇒ 是在半截内容里切的' % _lsd[_dnx[0] - 1][:20]
        _dend = _dnx[0] - 1
    else:
        _dend = len(_lsd) - 1
    _doc_win = '\r\n'.join(_lsd[:_dend]) + '\r\n'
    assert doc_old.startswith(_doc_win), 'ABORT: 排查记录窗口不是盘上开头的逐字前缀'
    DOC_LATER = len(_lsd) - 1 - _dend          # 窗口之外的行数（后续小节 + EOF 空行）
    DOC_TAIL_REST = doc_old[len(_doc_win):]
    doc_pre = _doc_win[:dcut].rstrip('\r\n') + '\r\n'
    d_pre_str = doc_pre                       # 载体 DOC 行"改前"那一格必须与它同源
    assert (money(len(doc_pre.encode('utf-8'))), str(doc_pre.count('\r\n')),
            hashlib.md5(doc_pre.encode('utf-8')).hexdigest()[:8]) == \
        re.search(r'DOC ([\d,]+) B / (\d+) 行 / 标题 \d+ -> .*?md5 (\w{8}) -> ',
                  line_of(os.path.join(HDIR, _wit[0]), r'(?m)^DOC ', '写盘那一遍载体的 DOC 行')).groups(), \
        'ABORT: 反推的排查记录"改前"三格与写盘那一遍现读在册的不等 ⇒ 复原不逐字'
    heads_before, heads_after = heads(doc_pre), heads(_doc_win)
    assert (heads_before, heads_after) == (int(doc_h23_land), int(doc_h23_land) + 1), \
        'ABORT: 从盘上反推的"本节之前/本批窗口末"标题数与落地批在册值不符：%d,%d vs %s' % (
            heads_before, heads_after, doc_h23_land)
    assert len(blank_gap_lines(doc_pre)) == 0, 'ABORT: 反推的"本节之前"就有节标题缺空行 ⇒ 前置事实不成立'
    SEC_LAND = _doc_win[dcut:]
    doc_new = doc_old
    # 本批终态串 = 窗口串（不是盘上全文件）：后续批次一追加，"之后"那几格若取盘上值就成了把 B 集合的读数记在本批名下
    FREQ_AT_STR, DOC_AT_STR = _freq_win, _doc_win
    DOC_LATER_HEADS = heads(DOC_TAIL_REST)

# ---------- 待写正文的零容忍闸（两块都按"将被写出 / 已在盘上的那一段"检查，不数中间串）----------
def unlabeled_fake(text):
    """假裁决只允许出现在**同时点名 PRIOR_VERDICT** 的那一行里（(103) 的防线）。"""
    return [i + 1 for i, l in enumerate(text.split('\r\n')) if FAKE_V in l and 'PRIOR_VERDICT' not in l]


assert not unresolved(FREQ_LAND) and not re.search(r'@[A-Z]+@', FREQ_LAND), 'ABORT: FreqErr 待写块有未回填占位'
assert not unresolved(SEC_LAND) and 'None' not in SEC_LAND, 'ABORT: §38.20 有未回填占位：' + repr(unresolved(SEC_LAND)[:3])
assert '\\' not in FREQ_LAND, 'ABORT: FreqErr 待写块里有反斜杠 ⇒ 正是 §38.18 那一族'
assert '\\' not in SEC_LAND, 'ABORT: §38.20 正文里有反斜杠（CR 会静默损坏指针）'
assert not unlabeled_fake(FREQ_LAND) and not unlabeled_fake(SEC_LAND), \
    'ABORT: 待写正文里有没被点名成"上一遍转抄"的失败裁决：%s / %s' % (
        unlabeled_fake(FREQ_LAND), unlabeled_fake(SEC_LAND))

# ---------- 写盘（幂等：REWROTE 模式一律不动盘）----------
if MODE == 'LANDED_NOW':
    open(FREQ, 'w', encoding='utf-8', newline='').write(freq_new)
    open(DOC, 'w', encoding='utf-8', newline='').write(doc_new)

# ---------- 写盘后独立回读（另一次调用，不复用上面那次的字符串）----------
freq_back, doc_back = rd(FREQ), rd(DOC)
freq_raw, doc_raw = open(FREQ, 'rb').read(), open(DOC, 'rb').read()
crlf_pure(FREQ)
crlf_pure(DOC)
if MODE == 'LANDED_NOW':
    assert freq_back.startswith(freq_old) and doc_back.startswith(doc_old), 'ABORT: 独立回读显示不是纯追加'
    assert doc_back == doc_new and freq_back == freq_new, 'ABORT: 回读与待写字节不逐字相同'
assert freq_back.count(FREQ_HEAD) == 1, 'ABORT: 本批台账标题不止一处 ⇒ 二次追加'
assert len([l for l in freq_back.split('\r\n') if '复跑｜R55 第三批' in l]) == 1, 'ABORT: 本批台账行不止一处 ⇒ 二次追加'
assert doc_back.count('### 38.20') == 1, 'ABORT: §38.20 不止一处 ⇒ 二次追加'


def tail_after(text, seg, name):
    """本批那一段必须**逐字在册且只有一处**，其后只许是"空行 + 下一批标题"或 EOF。
    写成 `text.endswith(seg)` 的话，复跑那一遍 seg 本来就是从同一块盘截的尾巴 ⇒ 恒真（自我循环），
    而第四批一落地它又立刻假红。按窗口切才两头都对。"""
    assert text.count(seg) == 1, 'ABORT: 本批%s在回读里出现 %d 次 ⇒ 二次追加或被截断' % (name, text.count(seg))
    r = text[text.index(seg) + len(seg):]
    assert r == '' or (r.startswith('\r\n') and r.split('\r\n')[1].startswith(('## ', '### '))), \
        'ABORT: 本批%s之后紧跟的不是"空行 + 下一批标题"而是 %r ⇒ 落地之后又被就地改过' % (name, r[:40])
    return r


_rest_f = tail_after(freq_back, FREQ_LAND, '台账那一段')
_rest_d = tail_after(doc_back, SEC_LAND, '§38.20 那一段')
if MODE != 'LANDED_NOW':
    assert freq_back.startswith(_freq_win) and doc_back.startswith(_doc_win), \
        'ABORT: 进入时与回读时两次读取的窗口前缀不一致 ⇒ 本遍之间有别处在这块盘上写'
    assert _rest_f == FREQ_TAIL_REST and _rest_d == DOC_TAIL_REST, \
        'ABORT: 回读看到的"窗口之外"与进入时算的不逐字相同（%r / %r）⇒ 后续批次的行在本遍里被挪动过' % (
            _rest_f[:30], _rest_d[:30])
assert kinds(freq_back) == a_kind and freq_back.count('\r\n') == a_lines, \
    'ABORT: 独立回读的两把尺与登记值不符：(%d,%d) vs (%d,%d)' % (kinds(freq_back), freq_back.count('\r\n'), a_kind, a_lines)
DISK_KIND_LATER, DISK_LINES_LATER = kinds(_rest_f), _rest_f.count('\r\n')
assert a_kind_led == b_kind_led + len(FREQ_ENTRIES), \
    'ABORT: 台账自己登记的两把尺相差 %d 条，而本批源文件里是 %d 条 ⇒ 台账行里的数与脚本不同源' % (
        a_kind_led - b_kind_led, len(FREQ_ENTRIES))
assert not gap_above(freq_back), \
    'ABORT: 独立回读显示本批台账/订正行上方不是恰好一只空行 ⇒ (102) 那一族破了：%s' % gap_above(freq_back)
assert heads(doc_back) == heads_after + DOC_LATER_HEADS, \
    'ABORT: 排查记录标题数 %d != 本批窗口内 %d + 窗口外 %d ⇒ 后续小节没按整节追加' % (
        heads(doc_back), heads_after, DOC_LATER_HEADS)
assert not blank_gap_lines(doc_back), \
    'ABORT: 排查记录有节标题上方缺空行 %s（本批之前该量为 0，见 r55_backups_readme9.txt 第 19 行）' % blank_gap_lines(doc_back)
_unlabeled = ['%s:%d' % (_p, i + 1) for _p, _t in (('排查记录', doc_back), ('FreqErr', freq_back))
              for i, l in enumerate(_t.split('\r\n')) if FAKE_V in l and 'PRIOR_VERDICT' not in l]
assert not _unlabeled, 'ABORT: 正文里有没被点名成"上一遍转抄"的失败裁决 ⇒ (103) 的防线破了：%s' % _unlabeled
lns = doc_back.split('\r\n')
h18 = [i + 1 for i, l in enumerate(lns) if l.startswith('### 38.18')]
h19 = [i + 1 for i, l in enumerate(lns) if l.startswith('### 38.19')]
h20 = [i + 1 for i, l in enumerate(lns) if l.startswith('### 38.20')]
assert len(h18) == len(h19) == len(h20) == 1 and h18[0] < h19[0] < h20[0], 'ABORT: 三节号顺序不成立'
b_mb, b_mi, b_ub, b_ui = stat(PMB), stat(PMI), stat(UMB), stat(UMI)
assert (b_mb, b_mi, b_ub, b_ui) == (s_mb, s_mi, s_ub, s_ui), 'ABORT: 本遍动了四只记忆文件（本批口径：归档外、且只读）'
# (104) 的执行者：载体首行的"本遍现跑于"必须是本遍 datetime.now()，只有写盘那一遍它才与台账行头时刻同一
assert (MODE == 'LANDED_NOW') == (RUN_AT == NOW_AT), \
    'ABORT: "本遍现跑于"与"本批台账行头时刻"的不等关系和 MODE 不自洽（%s vs %s / MODE=%s）⇒ 有一格是抄来的时刻' % (
        NOW_AT, RUN_AT, MODE)

# 本批终态（= 窗口串，绝不是盘上全文件）的三格 + md5：载体上"之后"那一侧只许记它
at_bytes, at_kind, at_lines = len(FREQ_AT_STR.encode('utf-8')), kinds(FREQ_AT_STR), FREQ_AT_STR.count('\r\n')
at_md5 = hashlib.md5(FREQ_AT_STR.encode('utf-8')).hexdigest()[:8]
dat_bytes, dat_lines, dat_heads = len(DOC_AT_STR.encode('utf-8')), DOC_AT_STR.count('\r\n'), heads(DOC_AT_STR)
dat_md5 = hashlib.md5(DOC_AT_STR.encode('utf-8')).hexdigest()[:8]
assert (at_lines, at_kind, dat_heads) == (a_lines - DISK_LINES_LATER, a_kind - DISK_KIND_LATER, heads_after), \
    'ABORT: 窗口终态（%d 行 / %d 条 / 标题 %d）与"盘上读数 − 窗口外"或落地批在册标题数不吻合 ⇒ 窗口切点没落在行边界上' % (
        at_lines, at_kind, dat_heads)

lines = [
    'R55 第三批 paperwork 落地器（FreqErr 4 条 + 排查记录 §38.20），本遍现跑于 %s；本批台账行头时刻 = %s；MODE=%s' % (
        NOW_AT, RUN_AT, MODE),
    'FREQ 追加之前%s %s B / %d 条 / %d 行 -> 之后（本批窗口末行 %s） %s B / %d 条 / %d 行 ; md5 %s -> %s ; 行尾=纯 CRLF ; '
    '"改前"四格的来源 = %s ; 盘上现值（含后续批次）%s B / %d 条 / %d 行 / md5 %s…，其中窗口外 %d 条 / %d 行' % (
        PRE_KIND, money(b_bytes), b_kind, b_lines, '文件末尾' if MODE == 'LANDED_NOW' else str(_end),
        money(at_bytes), at_kind, at_lines, b_md5, at_md5, _witness,
        money(len(freq_raw)), kinds(freq_back), freq_back.count('\r\n'), hashlib.md5(freq_raw).hexdigest()[:8],
        DISK_KIND_LATER, DISK_LINES_LATER),
    'FREQ_TAIL 台账行 1 处（含 4 个数：BEFORE %d/%d、AFTER %d/%d，两把尺都在最终串上数；本遍复算的窗口终态 %d/%d）' % (
        b_kind, b_lines, a_kind_led, a_lines_led if MODE != 'LANDED_NOW' else a_lines, at_kind, at_lines),
    'FREQ_FIX 台账行上方空行守卫（(102) 族）：本遍独立回读 = 通过 ; 订正行于 %s，三把尺 %s ; 行数差 = 之上 %d 只 + 之下 %d 只行（台账 AFTER 之后纯追加）; 窗口右界 = %s' % (
        FIX_AT3, PAIRS, INS_ABOVE, TAIL_N, LATER_WHY),
    'DOC %s B / %d 行 / 标题 %d -> %s B / %d 行 / 标题 %d（本批窗口末）; §38.18@%d §38.19@%d §38.20@%d ; 缺空行=0 ; md5 %s -> %s ; '
    '"改前"三格与上面 FREQ 行同源（%s）; 盘上现值（含后续小节）%s B / %d 行 / 标题 %d，其中窗口外 %d 行 / %d 只标题' % (
        money(len(d_pre_str.encode('utf-8'))), d_pre_str.count('\r\n'), heads_before,
        money(dat_bytes), dat_lines, dat_heads, h18[0], h19[0], h20[0],
        hashlib.md5(d_pre_str.encode('utf-8')).hexdigest()[:8], dat_md5, PRE_KIND,
        money(len(doc_raw)), doc_raw.count(b'\n'), heads(doc_back), DOC_LATER, DOC_LATER_HEADS),
    'TIME 正文 %s → 落地器补载体 %s → 订正换字 %s → 订正批补载体 %s → 本节登记 %s（五格各自现读载体，(104) 的执行者）' % (
        BODY_AT, LAND_AT, FIX_AT, FIX_CARRIER_AT, RUN_AT),
    'XCHECK 三处交叉核对全过：落地批抄的改前正文 (%s 行 / %s B) == 订正批等式左端 ; 落地批 DOCS 与 r55_backups_readme9 同值 ; 末版清单 README.md 行 == 落地批抄的 %s B/md5 %s…' % (
        pl0, money(int(pb0)), money(rm_bytes), rm_md5[:8]),
    'GEN24 末版 TOTAL=%d / %s B / BOM %d（清单末三行现读，与落地批载体逐字互核）; 终态复核两遍都绿：%s / VERIFY_RC=%s（首遍写载体 %s、第二遍 %s，载体 hardware/verify_manifest_0924125339.txt 与 _2.txt）' % (
        m_n, money(m_b), m_bom, vc1_ver, vc1_rc, t_v24, v2_cut),
    'SYNC 第 13 代在册：%s 只 / %s B / 包 %s B md5 %s… / 聚合 %s… / 真裁决 %s @%s（裸 search 取到的是上一遍的 %s）⇒ 本批未追第 14 代，理由见 §38.20 ⑦' % (
        sync_n, money(int(sync_b)), money(int(pkg_b)), pkg_md5[:8], agg_md5[:8], TRUE_V, rt_at, FAKE_V),
    'DOCS 快照停在第九遍 %s 只 @%s（闸 OF %s / HITS %s）、backups 停在第九次读数 %s ⇒ §38.20 一落两格即过期，第十遍 + 第十次读数是后续义务' % (
        docs_n, docs_at, gate_of, gate_hits, rd9_run),
    'PMEM 本遍未写盘（只复核 + md5 比对）：正文 %s B / %d 行 / md5 %s ; 索引 %s B / %d 行 / md5 %s ; 用户工具映射 %s B / %d 行 ; 用户索引 %s B / %d 行 ; CR 全 0' % (
        money(s_mb[0]), s_mb[1], s_mb[3], money(s_mi[0]), s_mi[1], s_mi[3], money(s_ub[0]), s_ub[1], money(s_ui[0]), s_ui[1]),
    'MEMO (103)/(104) 落点计数（订正载体在册）= %s / %s ; 时刻那一格真值 vs 冒充值 = %s vs %s 差 %s 分钟' % (c103, c104, rd9_at, fake_at, gap_min),
    'FIELD rev-list=%s porcelain=%d ports=%s COM14=%s ; build md5 %s… / %s B ≠ 板上 %s… / %s B（本批零代码进镜像、未烧，那一格未定性）' % (
        rev, len(por), port_names, 'PRESENT' if has14 else 'ABSENT',
        bin_new[0][:8], money(int(bin_new[1])), bin_old[0][:8], money(int(bin_old[1]))),
    'GUARD 反斜杠进正文=0（两块各自断言）/ 未回填占位=0（花括号哨兵与 @大写字母@ 两类各自扫）/ 纯追加 + 独立回读逐字 / 幂等锚 §38.20=1 本批台账行=1 / 本批台账与订正行上方恰好一只空行（写盘前 + 独立回读各一遍）/ 载体"改前"格与"改后"格同源：反推串另与 MODE=LANDED_NOW 那遍的现读数逐字互核（FreqErr 三格 + md5、排查记录三格 + md5），witness 不为恰好 1 只即 ABORT / '
    '断言范围按批次窗口右界切（本批两段之后只许"空行 + 下一批标题"或 EOF；载体"之后"那一侧记窗口终态、盘上全量另记一格）',
    'VERDICT=' + ('PAPERWORK3_LANDED' if MODE == 'LANDED_NOW' else 'PAPERWORK3_STATE_VERIFIED'),
]
open(CARRIER, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('CARRIER=hardware/' + os.path.basename(CARRIER))
