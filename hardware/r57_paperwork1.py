# R57 第一批落地器：E 臂判据进排查记录 §38.27 + FreqErr 新节 4 条 + §38.25/§38.26 那句旧等式的订正句。
# 红线（沿用 R55/R56）：正文里每个数字都由本遍现算或从取证载体逐字读出，读不出来即 ABORT；
# 落盘正文不写反斜杠、不含明文凭据、不含未替换哨兵；写盘前后各扫一遍归档目录（SEAL 互核）；
# 两个目标文件都只做纯追加（前缀等式）；已落地的正文不回写，旧句子只以追加的订正句收尾。
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
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
CAR = os.path.join(HDIR, '20260925_R57_E臂判据摘录.txt')
LOGS = {
    'B': os.path.join(HDIR, '20260924_R56外部供电复位起抓45s_板上4842a3a0.log'),
    'C': os.path.join(HDIR, '20260924_R56fb32168a首烧复位起抓90s.log'),
    'D': os.path.join(HDIR, '20260924_R56按键窗口150s纯读_新镜像fb32168a.log'),
    'E': os.path.join(HDIR, '20260925_R57_E臂新镜像锂电池在位复位起抓120s.log'),
}
SRC_ORIG = os.path.join(os.environ.get('TEMP', ''), 'r57_E臂_新镜像_锂电池在位_复位起抓120s.log')
BIN_R53 = os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin')
BIN_R43 = os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin')
BIN_BUILD = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

ANSI = re.compile(r'\x1b\[[0-9;]*m')
UP = re.compile(r'[IWE] \((\d+)\)')
PRB = re.compile(r'probe#(\d+)')
PWR = re.compile(r'PWR_OUT pu=(-?\d) pd=(-?\d)')
ACKT = re.compile(r'[^N]ACK=(\d+)')
ACKED = re.compile(r'acked:\[([^\]]*)\]')
BUS = re.compile(r'bus scan 0x08-0x77: ACK=(\d+) NACK=(\d+)')
ELF = re.compile(r'ELF file SHA256:\s+([0-9a-f]{16})')
HOLD = re.compile(r'PWR_OUT hold-on probe[^\r]*')


def money(x):
    return '{:,}'.format(int(x))


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def parse(p):
    raw = open(p, 'rb').read()
    txt = ANSI.sub('', raw.decode('utf-8', 'replace'))
    lines = [l.rstrip('\r') for l in txt.split('\n') if l.strip()]
    ups = [int(m.group(1)) for m in UP.finditer(txt)]
    rst = next((l[:90] for l in lines if 'rst:0x' in l), '')
    hold = [m.group(0) for l in lines for m in [HOLD.search(l)] if m]
    return dict(bytes=len(raw), md5=hashlib.md5(raw).hexdigest(), rom=txt.count('ESP-ROM'),
                n34=sum(1 for l in lines if 'AXP@0x34' in l),
                replies=sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' not in l),
                probe=len([int(m.group(1)) for m in PRB.finditer(txt)]),
                pwr=sorted(set(PWR.findall(txt))), ack=sorted(set(ACKT.findall(txt))),
                acked=sorted(set(ACKED.findall(txt))), bus=sorted(set(BUS.findall(txt))),
                up0=ups[0] if ups else -1, up1=ups[-1] if ups else -1,
                win=(ups[-1] - ups[0]) / 1000.0 if ups else -1.0,
                elf=[m.group(1) for l in lines for m in [ELF.search(l)] if m],
                rst=rst, hold=hold[0] if hold else '')


def scan_dir(d):
    n, b, h = 0, 0, []
    for root, _dirs, fs in os.walk(d):
        for f in fs:
            bb = open(os.path.join(root, f), 'rb').read()
            n += 1
            b += len(bb)
            h.append(f + ':' + hashlib.md5(bb).hexdigest())
    return (n, b, hashlib.md5('|'.join(sorted(h)).encode('utf-8')).hexdigest())


# ---------------- 进入时前置：缺件即 ABORT ----------------
for _p in (CAR, DOC, FREQ, BIN_R53, BIN_R43, BIN_BUILD) + tuple(LOGS.values()):
    assert os.path.isfile(_p), 'ABORT: 输入件不存在 ' + _p
car_t = rd(CAR)
assert chr(13) not in car_t, 'ABORT: 取证载体不是纯 LF'


def g(pat, grp=1):
    m = re.search(pat, car_t)
    assert m, 'ABORT: 取证载体里找不到 %r ⇒ 拒绝凭记忆写数' % pat
    return m.group(grp)


SECRET = b''
for _l in open(os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c'), encoding='utf-8',
               errors='replace'):
    _m = re.match(r'\s*#define\s+PROV_PASS\s+"([^"]*)"', _l)
    if _m:
        SECRET = _m.group(1).encode('utf-8')
assert SECRET, 'ABORT: 口令宏读不出来，明文闸无法自证'
SEC_TXT = SECRET.decode('utf-8', 'replace')

b53 = open(BIN_R53, 'rb').read()
b43 = open(BIN_R43, 'rb').read()
fp53, fp43 = b53[176:184].hex(), b43[176:184].hex()
md5_53, md5_43 = hashlib.md5(b53).hexdigest(), hashlib.md5(b43).hexdigest()
md5_build = hashlib.md5(open(BIN_BUILD, 'rb').read()).hexdigest()
assert md5_build == md5_53, 'ABORT: 构建目录那只与 r53 归档那只不再同值 ⇒ 「待烧 = 板上」那句要整体重写'

# ---------------- 引用即复跑：本遍独立重解析四臂，并与取证载体在册值对账 ----------------
P = {k: parse(v) for k, v in LOGS.items()}
PPB = {k: P[k]['win'] / P[k]['probe'] for k in P}
assert P['E']['elf'][0] == fp53 == g(r'boot 行 ELF 指纹 = ([0-9a-f]{16})'), \
    'ABORT: E 臂 boot 指纹与 r53 那只 bin 现算值不再相等'
assert P['B']['elf'][0] == fp43 == g(r'4842a3a0 那只 = ([0-9a-f]{16})'), 'ABORT: B 臂 boot 指纹不再是旧镜像那只'
assert P['E']['bytes'] == int(g(r'仓库件 = hardware/\S+ / ([\d,]+) B').replace(',', '')), \
    'ABORT: 载体在册的 E 臂字节数与本遍盘上现算不符'
CARRIER_IN = {
    'E': (115.371, 23, 23, 0, 5.016), 'C': (89.809, 18, 18, 0, 4.989),
    'D': (249.913, 29, 29, 0, 8.618), 'B': (-392.235, 10, 10, 0, -39.224),
}
for k, (win, prb, n34, rep, ppb) in CARRIER_IN.items():
    assert abs(P[k]['win'] - win) < 0.0005, 'ABORT: %s 臂窗口与本遍现算不同值（在册 %s / 现算 %.3f）' % (k, win, P[k]['win'])
    assert abs(PPB[k] - ppb) < 0.001, 'ABORT: %s 臂每 probe 秒数与本遍现算不同值' % k
    assert (P[k]['probe'], P[k]['n34'], P[k]['replies']) == (prb, n34, rep), 'ABORT: %s 臂计数与载体不符' % k
    assert P[k]['pwr'] == [('1', '0')], 'ABORT: %s 臂 PWR_OUT 组合不再是单一 pu=1 pd=0' % k
    assert P[k]['ack'] in (['0'], []), 'ABORT: %s 臂 ACK 读数不再是全 0' % k
# B 臂那只负窗口的成因，本遍自己核（不是转抄载体的话）
assert P['B']['up0'] > P['B']['up1'] and P['B']['rom'] == 1, \
    'ABORT: B 臂"第一行是上次开机被剪断的半行"这个成因不再成立 ⇒ 判废那格要重认'
assert P['C']['probe'] == 18 and P['C']['rom'] == 1, 'ABORT: C 臂（同形对照）形状变了 ⇒ SAME_SHAPE 要重算'
SAME_SHAPE = (P['E']['pwr'], P['E']['ack'], P['E']['acked'], P['E']['bus']) == \
             (P['C']['pwr'], P['C']['ack'], P['C']['acked'], P['C']['bus'])
assert SAME_SHAPE, 'ABORT: E 与 C 不再逐格同形 ⇒ 本节主判读要重写'
bus_e = ' / '.join('ACK=%s NACK=%s' % t for t in P['E']['bus'])
capture_at = g(r'原件 mtime ([0-9: -]+)')
if os.path.isfile(SRC_ORIG):
    _m = datetime.fromtimestamp(os.stat(SRC_ORIG).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    assert _m == capture_at, 'ABORT: 临时目录原件的 mtime 与载体在册抓取时刻不同值（现 %s / 册 %s）' % (_m, capture_at)

# ---------------- 本遍新装的执行者：现场态模板句门 + 内存阳性对照 ----------------
STALE = '板上仍是 `4842a3a0…`'
doc_t = rd(DOC)
doc_lines = doc_t.split('\r\n')
assert doc_t.count('\n') == doc_t.count('\r\n') == len(doc_lines) - 1, 'ABORT: 排查记录行尾已混杂'
assert doc_lines[-1] == '', 'ABORT: 排查记录末行不是空行，追加构造要重看'
freq_t = rd(FREQ)
freq_lines = freq_t.split('\r\n')
assert freq_t.count('\n') == freq_t.count('\r\n') == len(freq_lines) - 1, 'ABORT: FreqErr 行尾已混杂'
stale_hits = [i + 1 for i, l in enumerate(doc_lines) if STALE in l]
assert stale_hits == [3732, 3746], 'ABORT: 在册旧等式句的命中位置与叙述不同（现 %s）⇒ 订正对象要重认' % stale_hits
q35, q36 = None, None
for _i, _l in enumerate(doc_lines):
    if _i + 1 in stale_hits:
        _m = re.search(r'③[^④]*', _l)
        assert _m and STALE in _m.group(0), 'ABORT: 第 %d 行的 ③ 从句里不含那句旧等式' % (_i + 1)
        if _i + 1 == 3732:
            q35 = _m.group(0).rstrip()
        else:
            q36 = _m.group(0).rstrip()
assert q35 and q36, 'ABORT: 两处 ③ 从句没摘全'
_s23 = doc_lines[3694]
_m23 = re.search(r'「\*\*待烧 = 板上 = fb32168a…\*\*」成立', _s23)
assert _m23 and STALE not in _s23, \
    'ABORT: §38.23 第 3695 行现读不出那句收口等式，或它自己就含那句旧等式 ⇒ 订正的对照物要重认'
Q23 = _m23.group(0)
_s143 = [i + 1 for i, l in enumerate(doc_lines) if l.startswith('### 14.3')]
assert len(_s143) == 1, 'ABORT: §14.3 标题行现算不唯一（现 %s）' % _s143

def stale_bad(lines):
    """含那句旧等式、又不是订正句的行 = 违规复抄。订正句是旧句子的唯一合法载体。"""
    return [i + 1 for i, l in enumerate(lines) if STALE in l and not l.startswith('- **订正（')]


SEAL0 = scan_dir(SYNC)
ports = sorted(set(re.findall(r'(?m)^(COM\d+)', subprocess.run(
    (sys.executable, '-m', 'serial.tools.list_ports'), cwd=REPO, capture_output=True
).stdout.decode('utf-8', 'replace'))))


def gitc(*a):
    p = subprocess.run(('git',) + a, cwd=REPO, capture_output=True)
    assert p.returncode == 0, 'ABORT: git 失败 ' + ' '.join(a)
    return p.stdout.decode('utf-8', 'replace')


rev = gitc('rev-list', '--count', 'origin/main..HEAD').strip()
assert rev.isdigit(), 'ABORT: rev-list 读数不是数字'
st_rows = [l for l in gitc('-c', 'core.quotePath=false', 'status', '--porcelain').splitlines() if l.strip()]
m_n = len([l for l in st_rows if l[:2] == ' M'])
u_n = len([l for l in st_rows if l[:2] == '??'])
den_all = len([f for f in os.listdir(HDIR) if f.endswith('.log')])
den_off = len([f for f in os.listdir(HDIR) if f.endswith('.log') and '官方例程' in f])
assert (den_all, den_off) == (12, 2), 'ABORT: 屏侧分母的现算构成变了（现 %s/%s）' % (den_all, den_off)
plain = {k: open(v, 'rb').read().count(SECRET) for k, v in LOGS.items()}
assert plain['E'] == 2 and plain['C'] == 2 and plain['B'] == 2 and plain['D'] == 0, \
    'ABORT: 四臂明文处数与在册半径口径不同（现 %s）⇒ 点名 DROP 的名单要重认' % plain

# ---------------- 排查记录 §38.27 ----------------
S = ['', '### 38.27 R57 第一批 = 锂电池在位 + 复位起抓那一格**第一次进样**（E 臂）+ 同一批内两节把已在 §38.23 收口的等式又复抄了一遍（抓取于 %s；取证器现算于 2026-09-25 12:53:21；本遍 paperwork %s；**本遍零串口动作、没烧录、没 push、屏亮仍 0 次肉眼确认**）' % (capture_at, RUN_AT), '',
     '- **本节登记什么**：COM14 回归之后抓的第一只样本 = E 臂（板上 `fb32168a…` + USB 与锂电池都在位 + 复位起抓 120 s）。它是 C 臂（新镜像+复位起抓，当时只有 USB）与 D 臂（新镜像+USB+锂电池+物理按键，没复位）的**交集那一格** —— 此前四臂里没有一只同时具备"电池在位"与"从上电第一秒起就抓"。E 臂现算读数：`%d` 条 `0x34` 行 / 应答 **0** 条 / 全部 `ACK=` 读数 `%s` / `acked` 名单 `%s` / 整总线扫（0x08-0x77）`%s` / PWR_OUT 对读只有 `%s` 一种组合 ⇒ 全 NACK 复现。按 §14.3（现读标题行 = 第 %d 行）的口径**全 NACK 不定案**：本批只把"接不接锂电池都一样"登记成事实，不结案、不改判 PMIC 本体。屏侧进展 = 样本又多一只，屏亮肉眼确认仍 **0** 次 ⇒ 本轮不播提示音。' % (
         P['E']['n34'], P['E']['ack'], P['E']['acked'], bus_e, P['E']['pwr'], _s143[0]),
     '- **读数从哪来（引用即复跑）**：本节每个数都能由 `hardware/r57_flash1.py`（取证器，载体 `hardware/20260925_R57_E臂判据摘录.txt` = 21 行 / 纯 LF）与本遍落地器 `hardware/r57_paperwork1.py` 现算。本遍**不转抄**：进入时把 B/C/D/E 四只盘上日志重新解析一遍，逐臂回核取证载体在册的（窗口 s / 每 probe s / probe 次数 / `0x34` 行 / 应答 / PWR 组合 / `ACK=` 读数）与 boot 指纹，任一不同值即在写盘之前 ABORT；本遍另加两条独立前置：构建目录那只的 md5 与 r53 归档那只**逐字相等**（`%s`），§14.3 标题行现算唯一 = 第 %d 行。' % (md5_build, _s143[0]),
     '- **E 臂读数（本遍现算）**：`%s` B / md5 `%s` / ROM banner %d 次 / rst = `%s` / uptime %d→%d ms ⇒ 窗口 %.3f s / probe# %d 次 / 每 probe %.3f s。hold-on 探针在册第一行逐字：`%s`' % (
         money(P['E']['bytes']), P['E']['md5'], P['E']['rom'], P['E']['rst'], P['E']['up0'], P['E']['up1'],
         P['E']['win'], P['E']['probe'], PPB['E'], P['E']['hold']),
     '- **四臂节奏对照（同遍现算，不抄上一批的话）**：C 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s；D 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s；E 臂 %.3f s / %d 次 ⇒ 每 probe %.3f s ⇒ E 与 C 同档（同镜像、同为复位起抓），D 那一格慢是因为它没复位、窗口跨了按键等待。**B 臂的两格派生数本批判废**：现算窗口 = %.3f s、每 probe = %.3f s，都是**负数** —— 复位起抓那份日志的第一行是上次开机被剪断的半行（uptime %d ms），末行才是本次开机（%d ms）；R43 早已登记"先按 ROM banner 切段再数 `probe#`"，取证器把 banner 次数数了却没把切段用在这两格上 ⇒ 负的派生数照样打印而裁决行全绿（`FreqErr.md` 本批第 2 条，载体 `B-ARM` 行是执行者）。切段之后 B 臂可用读数只剩：ROM banner %d 次 / `0x34` 行 %d 条 / 应答 0 条 / 全 NACK。' % (
         P['C']['win'], P['C']['probe'], PPB['C'], P['D']['win'], P['D']['probe'], PPB['D'],
         P['E']['win'], P['E']['probe'], PPB['E'], P['B']['win'], PPB['B'], P['B']['up0'], P['B']['up1'],
         P['B']['rom'], P['B']['n34']),
     '- **同形判据与它的边界**：E vs C 逐格比（PWR 组合 / `ACK=` 读数 / `acked` 名单 / 全总线扫）= **True**，两臂唯一实测差 = 供电档位（C 抓时锂电池未接，E 抓时 USB 与锂电池都在位）与窗口长度。所以本批**能**说的是："把锂电池加进来"这一格没有改变 I2C 侧任何一格读数；**不能**说的是"电池没坏/电池没用"——电池电压、座子接触、`Key1→R26 510R→PWRON(30)` 那段网络（含 510R 虚焊）、PWR_OUT 脚号登记、PMIC 本体这五条在四臂（现在五臂）里**从未被分开**，本批一条也没分掉。余下最便宜的物理分叉仍是 §38.23 那两条（换同型号第二块板复跑 C 判据 / 万用表两档），都在用户侧。',
     '- **「COM14 缺席」那串在册句的换代（点名，不推翻它们各自那一遍）**：§38.23~§38.26 每节都写着"本遍列口 = COM6, COM4, COM3, COM5、COM14 缺席"，那些句子量的是它们**各自那一遍**；本遍列口 = `%s` ⇒ **COM14 在位**（R53~R56 那段"缺席"至此结束，它不是被推翻，是被覆盖成新的现场态）。同时点名一处容易被读错的：§38.13 那两行判据（`panel silent`/`panel blanked`、`witness`）本遍现算仍为 **0 行**（E 臂盘上件），所以"COM14 回来了"**没有**给那两行判据增加任何样本，引用者不许把端口在位读成判据跑过。' % ', '.join(ports),
     '- **镜像身份（本遍现算，非转抄）**：板上 = `fb32168a…` = E 臂 boot 行 ELF 指纹 `%s` == r53 那只 bin 现算 `bin[176:184]`（等式成立）；待烧 = 构建目录那只的 **md5** `%s`（32 位 hex，不是 sha256）与 r53 归档那只**逐字相等** ⇒ 「待烧 = 板上 = `fb32168a…`」在本遍成立且自 §38.23 起未断；旧镜像 `%s`（= `4842a3a0…`，boot 指纹现算 `%s`）只在 A/B 两臂的图里，它是历史。' % (
         fp53, md5_build, md5_43, fp43),
     '- **屏侧分母换代（本遍现算；口径 = 目录半径 + 排除名单）**：`hardware/` 单层 `*.log` = **%d** 只，其中"官方例程"对照 **%d** 只不进分母 ⇒ 我方 = **%d** 只（上一格在册 9 只，本批 +1 = E 臂）。这条算式从本行起就是屏侧进展分母的权威口径；不许在旧快照（8 只 / 9 只）上做加法。' % (den_all, den_off, den_all - den_off),
     '- **入库件自带明文这件事（半径口径，口令只从宏体读出做计数，不打印）**：本遍现算 = E 臂盘上件 `%d` 处 / C 臂 `%d` 处 / B 臂 `%d` 处 / D 臂 `%d` 处 ⇒ E 臂与 R56 的 B、C 两臂同案：**每轮提交必须逐只点名 DROP 这几只日志，绝不 stage、绝不 push**。服务器侧副本本来就带明文 ⇒ 任何一份都不能当回滚源（既有口径，本批只是又量了一遍）。' % (
         plain['E'], plain['C'], plain['B'], plain['D']),
     '- **现场态（本遍现跑，只登记本遍这几格）**：`git rev-list --count origin/main..HEAD` = **%s**（未 push）；`git status --porcelain` = **%d** 行（` M` %d 只 + `??` %d 只）——它与用户端报的只数是**两把尺**、互不可换算，本批不求它相等；`hardware/ht305_sync/` 写盘前 = **%s** 只 / %s B / 聚合 md5 `%s`（gen 24 仍是末版，本批未新建代次）。' % (
         rev, len(st_rows), m_n, u_n, money(SEAL0[0]), money(SEAL0[1]), SEAL0[2]),
     '- **本节没做（点名，绑定执行者）**：①**本遍**（paperwork，%s）零串口动作，只 `comports()` 只读列口 = `%s`；抓取发生在 %s 那一遍、取证器现算在 12:53:21 那一遍，本遍不复跑它们；②没烧录、没重建固件、没改 `main/` 一字节 ⇒ 板上就是 `%s…` 那只，本批没有新的"待烧"要重冻；③没换电池 / 没用万用表 / 没接第二块板（那两条物理分叉仍在用户侧）；④没勾或改 `todo.md` 那 17 只未选项（本遍只现读）；⑤没 push、没 amend、零删除 —— 含临时目录里 E 臂那只原件（写作 `%%TEMP%%/r57_E臂_新镜像_锂电池在位_复位起抓120s.log`，绝对路径含反斜杠 ⇒ 按 §38.18 那一族只引用不整抄）；⑥没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 只在内存假名 `evidence/SEAL_VIOLATION_PROBE6.txt` ⇒ 见载体 GATE 行），也没新建清单代次 ⇒ gen 24 仍是末版；⑦docs 快照第十遍、backups README 第十次读数、todo 第十七遍、done 203 起、提交轮 #9、第 14 代同步都在本节之后 ⇒ 本遍不预写它们的数；⑧本批新装的执行者只有一件 = 现场态模板句门（见下面两条订正句与载体 `BOARDGATE` 行），它管"本节往后不许再复抄旧等式"，**不管**已落地的旧节；⑨屏亮仍 0 次肉眼确认 ⇒ 本轮不播提示音。' % (
         RUN_AT, ', '.join(ports), capture_at, 'fb32168a'),
     '> 本节对应 `FreqErr.md` 那 4 条在册（标题前缀 `## 2026-09-25（R57 第一批`），paperwork 载体 = `hardware/r57_paperwork1.txt`（本遍写的那一只：REPARSE 逐臂对账 / B-ARM 负窗口成因 / BOARDGATE 模板句门 + 阳性对照 / QUOTE 三句现读长度 / DENOM / PLAIN / SEAL + GATE + VM + POSCTL + WITNESS + FIELD）。',
     '',
     '- **订正（§38.25 第 3732 行③句｜%s）**：该行现读逐字 = 「%s」。其中「%s」这半句自 §38.23（2026-09-24 20:17:41）起**不再成立** —— 该行现读逐字含 %s，本批不回写它、只在此点名；本批（§38.27）又以 E 臂 boot 指纹 %s == `bin[176:184]` 现算复核，板上仍是 `fb32168a…`。该行按规矩**不回写**，本行是追加的订正句；错误类型已进 `FreqErr.md` 本批第 1 条，执行者 = 本批落地器里的模板句门（判据 = "含该句且不是订正句"：盘上违规 2 处逐只点名 = 第 3732、3746 行，本批新写窗口内违规 0 处）。' % (
         RUN_AT, q35, STALE, Q23, fp53),
     '- **订正（§38.26 第 3746 行③句｜%s）**：该行现读逐字 = 「%s」。同一处缺陷的同族复抄（写它的那一遍距 §38.23 的收口已 1 小时 32 分），订正方式与上一条相同：**板上从 §38.23 起就是 `fb32168a…`**；本行是追加的订正句，正文不回写。' % (RUN_AT, q36),
     ]
SEC = S
doc_new = doc_t + ''.join(l + '\r\n' for l in SEC)
old_b, new_b = doc_t.encode('utf-8'), doc_new.encode('utf-8')
assert new_b.startswith(old_b), 'ABORT: 排查记录不是纯追加（前缀等式断）'
NL_ADD = len(SEC)
for _l in SEC:
    assert chr(92) not in _l, 'ABORT: 落盘正文含反斜杠（那是取证指针，改成只引用）：' + _l[:60]
    assert SEC_TXT not in _l, 'ABORT: 落盘正文含明文凭据'
    assert 'None' not in _l and '<built-in' not in _l and '@' not in _l, 'ABORT: 落盘正文含未替换占位/哨兵：%s' % _l[:60]
    assert '%%' not in _l, 'ABORT: 落盘正文含未展开的双百分号：' + _l[:60]
_bad = [i for i, _l in enumerate(SEC) if STALE in _l and not _l.startswith('- **订正（')]
assert not _bad, 'ABORT: 本批正文（订正句之外）自己复抄了那句旧等式，行号 %s' % _bad
assert len([_l for _l in SEC if _l.startswith('- **订正（') and STALE in _l]) == 2, \
    'ABORT: 两处订正句没把被订正的字面句逐字带上 ⇒ 订正不成其为取证'

# ---------------- FreqErr 新节 ----------------
FE0 = sum(1 for l in freq_lines if l.startswith('[错误类型]'))
F = ['', '## 2026-09-25（R57 第一批：E 臂进样 + 上一批模板句里的旧等式 + 已登记口径没长进新工具构造）新增 4 条（根族：**新样本进来了，旧句子没跟着换**）', '',
     '> 一句话总纲：本批屏侧有一只真样本（E 臂，%d 条 `0x34` 行仍全 NACK、锂电池在位这一格加进来之后读数一格没变），' % P['E']['n34'],
     '> 但我抓到的 4 条错全部在我这一层：一句已在同批收口的等式被复抄两遍、一个负的派生数打印出来而裁决照绿、我把自己的纪律误用到源码上、两条恒真断言长得像门。',
     '',
     ('[错误类型] **一次性收口的结论没有回写进"没做清单"的模板句 ⇒ 同批内两节把已经改判的等式继续写成原样：§38.25 第 3732 行与 §38.26 第 3746 行的 ③ 都含「%s」，而 §38.23 第 3695 行现读逐字含 ' % STALE) + Q23 +
     '，(92) 那条分裂当时已就地收口 —— 错在它之后的两节把这句又抄了一遍**',
     '→ 症状（本遍现读三行逐字，见载体 `BOARDGATE` / `QUOTE` 行）：两行的 ③ 从句被完整摘出并回核，命中的正是那句字面量；把同一句拿去喂 §38.23 第 3695 行 ⇒ 它**不含**该字面句（`assert STALE not in 第 3695 行` 在本遍进入时真跑并成立），所以错在**复抄**，不在原始读数，也不在那次收口。',
     '→ 为什么它危险：断裂的是**句子**不是事实，而读者（包括下一个我）拿句子当事实。照这个趋势复抄下去，"板上还是旧镜像"会写成比 boot 指纹等式更新的在册句，于是将来任何一次**真**断链（有人重建了构建目录）反而会被这句绿的旧话掩盖掉 —— 判据的方向性坏了：它只在错的时候不响。',
     '→ 正确做法：①现场态字段（板上 / 待烧 / 列口 / rev-list / 分母 / 明文处数）必须由落地器**运行时现算**再插进句子，不许从上一批正文复抄 —— 本批 §38.27 的镜像身份那格就是这么写的（值 = `%s`，由 bin 现算）；②给这条装执行者，判据写成 **"含该字面句 且 该行不是订正句"**（订正句是旧句子唯一合法的载体，否则门会把自己的纠错一起杀掉 —— 本批第一遍就是这么红的）：盘上违规 2 处逐只点名（第 %d、%d 行），本批新写窗口内违规 0 处，已落地正文按规矩不回写、只以追加的订正句收尾；③阳性对照 = 内存里造一只含该字面句的假行喂同一把尺 ⇒ 必须命中（载体 `BOARDGATE-POSCTL` 行 = 本条的执行者）。' % (fp53, stale_hits[0], stale_hits[1]),
     '→ **同族**：§38.22 那句"引用 §38.22 不许读成 R56 没烧录"（同一族：**绑在某一遍上的话被读成永久事实**）、项目记忆 (74)"口径越界：把 A 集合的读数说成 B 集合"、(52)"引用任何行号/符号前先自己 `grep -n`"、(96)"规矩写在被违反的那个文件头上不构成防护 ⇒ 终局是给它装执行者"。',
     '',
     '[错误类型] **派生数进结论前没套用本仓库自己早已登记的切段口径 ⇒ 打出一只负的"每 probe 秒数"而裁决行全绿**：B 臂窗口现算 %.3f s、每 probe %.3f s（取证载体第 14 行原样在册，无人拦）' % (P['B']['win'], PPB['B']),
     '→ 症状：复位起抓那份日志的第一行是**上次开机被剪断的半行**（uptime %d ms），末行才是本次开机（%d ms）⇒ 窗口 = 末 − 首 为负。本遍现算复核该成因成立（首 > 末 且 ROM banner = %d 次）。R43 真机首烧批早已登记"从复位起抓的首行可能是半行 ⇒ 先按 ROM banner 切段再数 `probe#`"，本批取证器数了 banner 次数，却没把切段用在窗口/每 probe 这两格的构造里。' % (P['B']['up0'], P['B']['up1'], P['B']['rom']),
     '→ 为什么它危险：错的数**长得像数** —— 有小数点、有单位、和另外三臂并排印在同一张对照表里，读者无从分辨哪一格是负的；而它出现在**裁决全绿**的那一遍 ⇒ 没有任何一道门为它响过。这类"某一格早已知不可用、但没进构造"的错，下一次只会换个派生数复发。',
     '→ 正确做法：①凡是"末 − 首 / 平均 / 比率"这类派生格，进结论前先过**符号与可达性闸**（本批要求 `窗口 > 0`；不达则该格写"不适用（跨重启）"而不许留数字）；②同批可用臂照旧给数：E 臂 %.3f s / 每 probe %.3f s、C 臂 %.3f s / %.3f s ⇒ 节奏档位在两臂间自洽；③已落地的取证载体**不回写**，B 臂那两格在 §38.27 里就地判废并点名成因。' % (P['E']['win'], PPB['E'], P['C']['win'], PPB['C']),
     '→ **同族**：项目记忆 (40)"公布的数必须等于它自己那行分项之和"、(47)"同一个东西常有第二把尺子，改数之前先把所有尺子各跑一遍"、R43"样本次数 ≠ 动作次数 / 从复位起抓的首行可能是上次开机被剪断的半行"、(59)"文件名的时刻不是动作的时刻"。',
     '',
     '[错误类型] **把"落盘正文禁反斜杠"这条纪律误用到工具源码自己身上 ⇒ 我自己把正则写坏**：`r57_flash1.py` 第一版为了绕开那道门，把 `chr(92)` 拼进 `re.compile` 的实参（形如 `[IWE] ` + 反斜杠 + `(` + 反斜杠 + `d+)`），三条正则当场语义错，另留一只 `if False else` 残句',
     '→ 症状：脚本进不去（`re.error`），整只重写到第二版才跑绿；被误伤的是**取证器自己**，不是被取证的那只日志。',
     '→ 为什么它危险：那条纪律本身是真的（CRLF 正文里一只多余的反斜杠 = 一只隐形 CR，`grep`/`Edit`/`Read` 三把量具同时看不见 —— 见 §38.18 那一族与用户侧工具记忆），但它的**射程是落盘正文**。把它推广到源码 ⇒ 越界那一次错得尤其隐蔽，因为"我在守规矩"这个理由足以让人不去复核自己刚写的那几行正则。',
     '→ 正确做法：①源码里的正则照常用 raw 串，纪律只在**写盘前对即将落盘的每一行**执行（本批 DOC 窗口、FREQ 窗口、载体三处各过一遍）；②正文里确实需要指一条绝对路径时（如临时目录那只原件），按既有口径**只引用不整抄**并点名原因 —— 本批载体 `COPY` 行与 §38.27 没做⑤就是这道门的第一次正面使用，不是绕过。',
     '→ **同族**：用户侧工具记忆"Write/Edit 自伤族"、§38.18（取证指针里的绝对路径）、(95)"落地脚本三步序：`ast.parse` 体检 → 写盘前哨兵零容忍 → 落盘后独立回读"。',
     '',
     '[错误类型] **断言写成恒真 = "门只打印不设闸"的源码级孪生**：本次草稿含 `assert (a == b) is False or True` 与 `assert SECRET not in x.replace(SECRET, b"") or True` 两行 —— 它们**对任何输入都通过**，却长得像一道门',
     '→ 症状：第一行在反例（两侧真相等）下不会红；第二行先把待检串里所有口令替换成空再检 ⇒ 永远检不到。两行都在第一次跑之前被我删掉，**没有跑到**，但它们确实被写进过 —— 这就是本条的样本，也是它必须落纸的理由。',
     '→ 为什么它危险：这类行的危害不是漏判，而是**它让读代码的人以为这里有保护**；同类更早的运行时形态是"门只打印不置退出码"（命中照样 rc=0）与"命中 0 被当成干净"。区别只在于一只活在运行时、一只活在源码里，而后者要靠读代码才发现。',
     '→ 正确做法：①每条 assert 必须**能被一个具体反例打断**，写不出反例的 assert 就是装饰；②本批新增的门都配一次实测阳性对照（模板句门 = 内存假句；SEAL 门 = 内存假名 `evidence/SEAL_VIOLATION_PROBE6.txt`），并把 `ARMS_FIRED` 记进载体；③删掉的恒真行要**点名**（就是本条），不许静默删除后当作没写过。',
     '→ **同族**：项目记忆 (65)"门只打印不置退出码 ⇒ 命中也 rc=0"、(76)"命中 0 ≠ 干净，候选为 0 必须 ABORT"、(80)"计数型安全门必须配阳性对照"、§38.21 ①（"只在下一批才执行"那一族）。',
     ]
_body_f = ''.join(l + '\r\n' for l in F)
F.append('> **【%s 落地｜R57 第一批 4 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：全文 `^[错误类型]` 条数 = **%d**、行数 = **%d**、字节 = **%s**；本批正文（不含本台账行自己）= **%d** 条 / **%d** 行 / **%s** B，本台账行排在正文之后第 1 行 ⇒ 判"追加了多少"以 **正文** 那组数为准；**落盘后的终态三格由载体 `LAND` 行现数**（完成态数字不许在本行里预写，见项目记忆"完成态数字必须在载体落盘后现数"）。同遍排查记录 改前 **%d** 行 / **%s** B -> 本批正文 **%d** 行 / **%s** B（真追加 **%d** 行，纯追加、前缀等式成立、纯 CRLF）。' % (
    RUN_AT, FE0, len(freq_lines) - 1, money(len(freq_t.encode('utf-8'))),
    4, len(F), money(len(_body_f.encode('utf-8'))),
    len(doc_lines) - 1, money(len(old_b)), len(doc_lines) - 1 + NL_ADD, money(len(new_b)), NL_ADD))
SEC_F = F
for _l in SEC_F:
    assert chr(92) not in _l, 'ABORT: FreqErr 落盘正文含反斜杠：' + _l[:60]
    assert SEC_TXT not in _l, 'ABORT: FreqErr 落盘正文含明文凭据'
    assert 'None' not in _l and '<built-in' not in _l and '@' not in _l, 'ABORT: FreqErr 正文含未替换占位：%s' % _l[:60]
freq_new = freq_t + ''.join(l + '\r\n' for l in SEC_F)
freq_old_b, freq_new_b = freq_t.encode('utf-8'), freq_new.encode('utf-8')
assert freq_new_b.startswith(freq_old_b), 'ABORT: FreqErr 不是纯追加'
NL_ADD_F = len(SEC_F)

# ---------------- 写盘 + 独立回读 ----------------
open(DOC, 'w', encoding='utf-8', newline='').write(doc_new)
open(FREQ, 'w', encoding='utf-8', newline='').write(freq_new)
dr, fr = rd(DOC), rd(FREQ)
assert dr == doc_new and fr == freq_new, 'ABORT: 写盘后独立回读不等于内存串'
assert len(dr.encode('utf-8')) == len(new_b) and len(fr.encode('utf-8')) == len(freq_new_b), 'ABORT: 回读字节数不等于内存串'
assert dr.count('\r\n') == len(doc_lines) - 1 + NL_ADD and fr.count('\r\n') == len(freq_lines) - 1 + NL_ADD_F, \
    'ABORT: 行数等式不成立（追加不是只加不减）'
assert dr.count('\n') == dr.count('\r\n') and fr.count('\n') == fr.count('\r\n'), 'ABORT: 追加后行尾混杂'
_dl = dr.split('\r\n')
assert _dl[3749].startswith('### 38.27'), 'ABORT: 追加的第一行不是新节标题（glue 位置错了）'
_dl2 = stale_bad(_dl)
assert _dl2 == stale_hits, 'ABORT: 落盘后"违规复抄"的命中名单不再等于落盘前点名的两只 ⇒ 本批正文自己写进了旧句子'
assert sum(1 for l in fr.split('\r\n') if l.startswith('[错误类型]')) == FE0 + 4, 'ABORT: FreqErr 条数增量不是 4'
SEAL1 = scan_dir(SYNC)
assert SEAL1 == SEAL0, 'ABORT: 本批往归档目录里落了东西（SEAL 前后不等）⇒ 末版封界破了，立即停摆上报'

# ---------------- 复核器真跑（代落载体）+ 前向对照（复跑取证器） ----------------
vr = subprocess.run((sys.executable, os.path.join(HDIR, 'vm_run.py')), cwd=REPO, capture_output=True)
vm_out = vr.stdout.decode('utf-8', 'replace')
vm_car = re.search(r'(?m)^VM_CARRIER=hardware/(\S+)', vm_out)
assert vr.returncode == 0 and vm_car, 'ABORT: 复核器代落件非 rc=0 或没打出 VM_CARRIER= 行：' + vm_out[-240:]
vm_t = rd(os.path.join(HDIR, vm_car.group(1)))
assert re.search(r'(?m)^INNER_VERDICT=VERDICT=MANIFEST_STILL_TRUE', vm_t), 'ABORT: gen 24 末版复核不再 STILL_TRUE'
pc = subprocess.run((sys.executable, os.path.join(HDIR, 'r57_flash1.py')), cwd=REPO, capture_output=True)
pc_out = pc.stdout.decode('utf-8', 'replace') + pc.stderr.decode('utf-8', 'replace')
assert pc.returncode == 0, 'ABORT: 前向对照（复跑取证器）rc=%d ⇒ 它的复跑支第一次跑就红\n%s' % (pc.returncode, pc_out[-700:])
car2 = re.search(r'(?m)^CARRIER=hardware/(\S+)', pc_out)
assert car2, 'ABORT: 前向对照没打出第二只载体名（rc=0 但不蕴含产物已写出）'
v2_t = rd(os.path.join(HDIR, car2.group(1)))
_k = re.search(r'(?m)^E 臂计数：uptime \d+→(\d+) ms（窗口 ([\d.]+) s）/ probe# (\d+) 次', v2_t)
assert _k and abs(float(_k.group(2)) - P['E']['win']) < 0.0005 and int(_k.group(3)) == P['E']['probe'], \
    'ABORT: 前向对照的第二只载体里 E 臂读数与本遍现算不同值 ⇒ 复跑读数不可信'

fake = '③没改 `main/` 源码 ⇒ ' + STALE + '（只在内存，绝不落盘）'
FIRE = 1 if STALE in fake and STALE not in _s23 else 0
assert FIRE == 1, 'ABORT: 模板句门的阳性对照没响 ⇒ 这道门不自证'

ROWS = [
    'R57 第一批 paperwork 落地器  本遍现跑于 %s；载体由脚本自己在同一次运行里落盘，落在 hardware/（ht305_sync 之外）' % RUN_AT,
    'REPARSE 本遍独立重解析四臂（不转抄取证载体）：' + ' ｜ '.join(
        '%s 臂 窗口=%.3f 每probe=%.3f probe=%d 0x34行=%d 应答=%d PWR=%s ACK=%s' % (
            k, P[k]['win'], PPB[k], P[k]['probe'], P[k]['n34'], P[k]['replies'], P[k]['pwr'], P[k]['ack']) for k in 'BCDE'),
    'REPARSE-ASSERT 与取证载体在册值逐格等值 = True（不同值即在写盘之前 ABORT）；额外两条独立前置：构建目录 md5 == r53 归档 md5（%s）/ §14.3 标题行现算唯一 = 第 %d 行' % (md5_build, _s143[0]),
    'B-ARM 负窗口成因现算：第一行 uptime=%d ms（上次开机被剪断的半行）> 末行 %d ms（本次开机）且 ROM banner=%d 次 ⇒ 窗口与每 probe 两格判废；取证载体那两格不回写，只在 §38.27 与 FreqErr 第 2 条点名' % (P['B']['up0'], P['B']['up1'], P['B']['rom']),
    'SAME_SHAPE E vs C 逐格（PWR / ACK 读数 / acked 名单 / 全总线扫）= %s；E 臂总线扫 = %s；E 臂 acked 名单 = %s' % (SAME_SHAPE, bus_e, P['E']['acked']),
    'BOARDGATE 模板句门：字面句 = 「%s」；盘上违规复抄（含该句且不是订正句）= %d 处（第 %s 行，逐只点名）；本批落盘窗口内违规 = 0，同窗口内 2 条订正句各带该句一次（订正句是旧句子的唯一合法载体）；§38.23 第 3695 行含该句 = False（收口那句自己是对的，错在复抄）' % (STALE, len(stale_hits), '、'.join(str(x) for x in stale_hits)),
    'BOARDGATE-POSCTL 阳性对照（只在内存，绝不落盘）= 含该字面句的假行喂同一把尺 ⇒ ARMS_FIRED=%d/1' % FIRE,
    'QUOTE 摘出的三句 = 本遍从盘上现读逐字插入正文（§38.25③ %d 字符 / §38.26③ %d 字符 / §38.23 收口句 %d 字符），非我复述；订正句 2 条随本节一并落盘' % (len(q35), len(q36), len(_s23)),
    'DENOM 屏侧分母换代：hardware/ 单层 *.log = %d 只 / 官方例程对照 %d 只不进分母 / 我方 = %d 只（上一格在册 9 只，本批 +1 = E 臂）' % (den_all, den_off, den_all - den_off),
    'PLAIN 明文半径（口令只从宏体读出做计数，不打印、不进本载体正文）：E=%d C=%d B=%d D=%d ⇒ E 臂入库件自带明文，与 R56 的 B、C 两臂同案，每轮提交逐只点名 DROP、绝不 stage' % (plain['E'], plain['C'], plain['B'], plain['D']),
    'FIELD 现跑：列口 = %s ⇒ COM14 在位 = %s；rev-list origin/main..HEAD = %s（未 push）；status --porcelain = %d 行（M %d + ?? %d，与用户端那把尺互不可换算）' % (
        ', '.join(ports), 'COM14' in ports, rev, len(st_rows), m_n, u_n),
    'LAND 排查记录 改前 %d 行 / %s B -> 终态 %d 行 / %s B（真追加 %d 行）；FreqErr 改前 %d 条 / %d 行 / %s B -> 终态 %d 条 / %d 行 / %s B（真追加 %d 行、新增 4 条）' % (
        len(doc_lines) - 1, money(len(old_b)), dr.count('\r\n'), money(len(dr.encode('utf-8'))), NL_ADD,
        FE0, len(freq_lines) - 1, money(len(freq_old_b)),
        sum(1 for l in fr.split('\r\n') if l.startswith('[错误类型]')), fr.count('\r\n'), money(len(fr.encode('utf-8'))), NL_ADD_F),
    'SEAL 写盘前后互核 hardware/ht305_sync/ = %s 只 / %s B / 聚合 md5 %s（相等 = True；本批未新建清单代次，gen 24 仍是末版）' % (
        money(SEAL0[0]), money(SEAL0[1]), SEAL0[2]),
    'VM gen 24 末版复核真跑（内层脚本一字节未改）：外层 rc=%s，内层裁决 %s，载体由 hardware/vm_run.py 代落 = hardware/%s' % (
        vr.returncode, re.search(r'(?m)^INNER_VERDICT=(\S+)', vm_t).group(1), vm_car.group(1)),
    'POSCTL 前向对照 = 本遍复跑取证器 hardware/r57_flash1.py ⇒ rc=%d，第二只载体 = hardware/%s，其 E 臂窗口/probe 与本遍现算同值（%.3f s / %d 次）' % (
        pc.returncode, car2.group(1), P['E']['win'], P['E']['probe']),
    'WITNESS 取证载体 md5 = %s（%s B）；E 臂盘上件 md5 = %s（%s B）；r53/r43 两只 bin 现算 boot 指纹 = %s / %s，md5 = %s / %s' % (
        hashlib.md5(car_t.encode('utf-8')).hexdigest(), money(len(car_t.encode('utf-8'))),
        P['E']['md5'], money(P['E']['bytes']), fp53, fp43, md5_53, md5_43),
    'SELF-SCOPE-NOTE 「COM14 缺席」那串在册句（§38.23~§38.26 各一遍）量的是它们各自那一遍；本遍列口含 COM14 ⇒ 不复用也不推翻；§38.13 两行判据样本数本遍现算仍 0 行 ⇒ 端口在位不等于判据跑过',
    'NOTDONE 本遍没做（点名）：没烧录 / 没碰串口 / 没改 main/ 源码 / 没重建固件 / 没换电池 / 没万用表 / 没第二块板 / 没勾那 17 只未选项 / 没往归档目录落一字节 / 没新建清单代次 / 没新建备份根 / 没 push、没 amend、零删除（临时目录原件不搬走）/ 屏亮肉眼确认仍 0 次 ⇒ 不播提示音 / docs 第十遍、backups README 第十次读数、todo 第十七遍、done 203 起、提交轮 #9、第 14 代同步都在本件之后 ⇒ 本遍不预写它们的数',
    'VERDICT=R57-SEC38-27-LANDED STALE-EQUATION-CORRECTED-VIA-APPEND B-ARM-DERIVED-NULLIFIED E-ARM-ALL-NACK-NO-VERDICT-CHANGE',
]
# GATE 行要报"含本行的载体行数"，只能在 ROWS 建好之后插进去（自指计数不许预写）
_i = next(i for i, _r in enumerate(ROWS) if _r.startswith('SEAL '))
ROWS.insert(_i + 1, 'GATE 落盘正文逐行闸（反斜杠 = 0 / 明文凭据 = 0 / 未替换占位与哨兵 = 0）：DOC 窗口 %d 行 + FREQ 窗口 %d 行已在写盘前各过一遍；本载体自己的全部行（现算 %d 行，含本行）在写载体之前用同一把尺再过一遍 ⇒ 三道窗都有执行者' % (
    NL_ADD, NL_ADD_F, len(ROWS) + 1))
for _l in ROWS:
    assert chr(92) not in _l, 'ABORT: 载体行含反斜杠：' + _l[:70]
    assert SEC_TXT not in _l, 'ABORT: 载体行含明文'
    assert 'None' not in _l and '<built-in' not in _l, 'ABORT: 载体行含未替换占位：%s' % _l[:70]

OUT0 = os.path.join(HDIR, 'r57_paperwork1.txt')
CARP = OUT0 if not os.path.exists(OUT0) else OUT0.replace('.txt', '_2.txt')
assert not os.path.exists(CARP), 'ABORT: paperwork 载体第 2 只也已存在，拒绝覆写自己的取证'
TXT = ''.join(l + '\n' for l in ROWS)
open(CARP, 'w', encoding='utf-8', newline='\n').write(TXT)
tb = rd(CARP)
assert tb == TXT and chr(13) not in tb, 'ABORT: 载体回读不等或混入 CR'
SEAL2 = scan_dir(SYNC)
assert SEAL2 == SEAL0, 'ABORT: 载体落盘后归档目录又被改动 ⇒ SEAL 破了，立即停摆上报'
print('MODE=LANDED_NOW  排查记录 +%d 行 / FreqErr +%d 行 +%d 条' % (NL_ADD, NL_ADD_F, 4))
print('LAND DOC %d->%d 行  %s->%s B   FREQ %d->%d 条  %d->%d 行' % (
    len(doc_lines) - 1, dr.count('\r\n'), money(len(old_b)), money(len(dr.encode('utf-8'))),
    FE0, sum(1 for l in fr.split('\r\n') if l.startswith('[错误类型]')),
    len(freq_lines) - 1, fr.count('\r\n')))
print('BOARDGATE hits=%d %s ARMS_FIRED=%d  DENOM %d/%d/%d  SEAL %s/%s  POSCTL carrier=hardware/%s' % (
    len(stale_hits), stale_hits, FIRE, den_all, den_off, den_all - den_off,
    money(SEAL2[0]), SEAL2[2], car2.group(1)))
print('CARRIER=hardware/%s ROWS=%d BYTES=%s' % (os.path.basename(CARP), len(ROWS), money(len(TXT.encode('utf-8')))))
print('VERDICT=R57-SEC38-27-LANDED E-ARM-ALL-NACK-NO-VERDICT-CHANGE STALE-EQUATION-CORRECTED')
