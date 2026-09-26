"""R56 真机首烧取证件生成器：把四臂串口日志现算成一份可复算摘录。

用法：python hardware/r56_flash1.py
输入 = 下列四只日志（路径 + 字节数在运行时现算并打进输出，任一缺失即 ABORT）；
输出 = hardware/20260924_R56真机首烧fb32168a判据摘录.txt（纯 LF，不含任何口令明文）。
"""
import os
import re
import sys
import hashlib
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HDIR = os.path.join(REPO, 'hardware')
TMP = os.path.join(os.environ.get('TEMP', ''), 'r56_btn4.log')   # D 臂**原件**：只有它保有真实抓取时刻
DLOG = '20260924_R56按键窗口150s纯读_新镜像fb32168a.log'

ARMS = [
    ('A 旧镜像+外部供电连续读（未复位）',
     os.path.join(HDIR, '20260924_R56外部供电连续读45s_未复位_板上4842a3a0.log'),
     '4842a3a0'),
    ('B 旧镜像复位起抓 45s',
     os.path.join(HDIR, '20260924_R56外部供电复位起抓45s_板上4842a3a0.log'),
     '4842a3a0'),
    ('C 新镜像 fb32168a 复位起抓 90s',
     os.path.join(HDIR, '20260924_R56fb32168a首烧复位起抓90s.log'),
     'fb32168a'),
    ('D 新镜像 + USB 和锂电池都在 + 按键真按过（150s 纯读）',
     os.path.join(HDIR, DLOG),
     'fb32168a'),
]
OUT0 = os.path.join(HDIR, '20260924_R56真机首烧fb32168a判据摘录.txt')
OUT = OUT0 if not os.path.exists(OUT0) else OUT0.replace('.txt', '_v2.txt')
assert not os.path.exists(OUT), 'ABORT: 判据摘录 v2 也已存在，拒绝覆写自己的取证件'

BINS = {
    '4842a3a0': os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin'),
    'fb32168a': os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin'),
}

ANSI = re.compile(r'\x1b\[[0-9;]*m')
UP = re.compile(r'[IWE] \((\d+)\)')
PROBE = re.compile(r'probe#(\d+)')
PWR = re.compile(r'PWR_OUT pu=(-?\d) pd=(-?\d)')
ACKTOK = re.compile(r'[^N]ACK=(\d+)')
ACKED = re.compile(r'acked:\[([^\]]*)\]')
HOKV = re.compile(r'known ACK=(\d+) NACK=(\d+)')
KNOWNL = re.compile(r'known ((?:0x[0-9a-fA-F]{2}/)+0x[0-9a-fA-F]{2}): ACK=(\d+) NACK=(\d+)')


def _u(line):
    m = UP.search(line)
    return int(m.group(1)) if m else -1

missing = [(n, p) for n, p, _ in ARMS if not os.path.isfile(p)]
if missing:
    for n, p in missing:
        print('ABORT: 输入日志不存在 %s = %s' % (n, p))
    raise SystemExit(2)
for k, p in BINS.items():
    if not os.path.isfile(p):
        print('ABORT: 指纹基准 bin 不存在 %s = %s' % (k, p))
        raise SystemExit(2)


def bootfp():
    """现算两只 bin 的开机指纹：boot 行 ELF file SHA256 的前 16 位 hex == bin[176:184]。"""
    r = {}
    for k, p in BINS.items():
        b = open(p, 'rb').read()
        r[k] = dict(md5=hashlib.md5(b).hexdigest(), size=len(b), fp=b[176:184].hex(),
                    sha256=hashlib.sha256(b).hexdigest()[:16])
    return r


def relp(p):
    r = os.path.relpath(p, REPO)
    return r.replace('\\', '/') if os.sep == '\\' else r


FP = bootfp()
rows = []
all_ack_vals = set()
for name, path, img in ARMS:
    raw = open(path, 'rb').read()
    txt = ANSI.sub('', raw.decode('utf-8', 'replace'))
    lines = [l.rstrip('\r') for l in txt.split('\n') if l.strip()]
    ups = [int(m.group(1)) for m in UP.finditer(txt)]
    probes = [int(m.group(1)) for m in PROBE.finditer(txt)]
    noreply = sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' in l)
    replies = sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' not in l)
    ackvals = set(ACKTOK.findall(txt))
    all_ack_vals |= ackvals
    acked = set(ACKED.findall(txt))
    pwr = sorted(set(PWR.findall(txt)))
    elf = [m.group(1) for l in lines for m in [re.search(r'ELF file SHA256:\s+([0-9a-f]{16})', l)] if m]
    holdl = [l for l in lines if 'PWR_OUT(GPIO1) hold = input+pull-up' in l]
    hol = [l for l in lines if 'hold-on probe' in l]
    hokv = HOKV.search(hol[0]) if hol else None
    klines = [KNOWNL.search(l) for l in lines]
    klines = [m for m in klines if m]
    kn_addr = sorted(set(a for mm in klines for a in mm.group(1).split('/')))
    kn_pairs = sorted(set((mm.group(2), mm.group(3)) for mm in klines))
    rows.append(dict(
        name=name, path=path, rel=relp(path), img=img, bytes=len(raw), lines=len(lines),
        md5=hashlib.md5(raw).hexdigest(),
        born=datetime.fromtimestamp(os.stat(path).st_ctime).strftime('%H:%M:%S'),
        mtime=datetime.fromtimestamp(os.stat(path).st_mtime).strftime('%H:%M:%S'),
        rom=txt.count('ESP-ROM'), rst=('' if txt.count('ESP-ROM') == 0 else
                                       next(l[:60] for l in lines if 'rst:0x' in l)),
        up0=ups[0] if ups else -1, up1=ups[-1] if ups else -1, ups3=ups[:3],
        nprobe=len(probes), p0=probes[0] if probes else -1, p1=probes[-1] if probes else -1,
        noreply=noreply, replies=replies, ackvals=sorted(ackvals), acked=sorted(acked), pwr=pwr,
        hold_up=_u(holdl[0]) if holdl else -1,
        ho_up=_u(hol[0]) if hol else -1,
        ho_ack=int(hokv.group(1)) if hokv else -1,
        ho_nack=int(hokv.group(2)) if hokv else -1,
        kn_addr=kn_addr, kn_pairs=kn_pairs, kn_lines=len(klines),
        elf=elf, busy_high=sum(1 for l in lines if 'stayed HIGH' in l),
        holdon=sum(1 for l in lines if 'hold-on probe' in l),
        pp_run=sum(1 for l in lines if 'PP-SCL' in l and '跳过' not in l),
        pp_skip=sum(1 for l in lines if 'PP-SCL' in l and '跳过' in l),
        scan_all=sorted(set(re.findall(r'bus scan 0x08-0x77: ACK=(\d+) NACK=(\d+)', txt))),
    ))

for r in rows:
    if r['elf']:
        assert r['elf'][0] == FP[r['img']]['fp'], \
            'ABORT: %s 的 boot 指纹 %s 不等于 %s 那只 bin 现算的 [176:184]=%s' % (
                r['name'], r['elf'][0], r['img'], FP[r['img']]['fp'])
    assert r['replies'] == 0, 'ABORT: %s 里出现 0x34 应答行 %d 条，判读要整体重写' % (r['name'], r['replies'])
    assert r['ackvals'] == ['0'] or r['ackvals'] == [], \
        'ABORT: %s 的 ACK= 读数不是全 0：%s' % (r['name'], r['ackvals'])
    assert all(a.strip() in ('none', '') for a in r['acked']), \
        'ABORT: %s 出现非 none 的 acked 名单：%s' % (r['name'], r['acked'])
    assert r['pwr'] == [('1', '0')], 'ABORT: %s 的 PWR_OUT 对读不止一种组合：%s（判据要分臂重写）' % (r['name'], r['pwr'])

# D 臂的**抓取时刻**只有 %TEMP% 那只原件保有：仓库内那只是拷贝，它的 ctime/mtime 已被拷贝动作重置（R44 那一族）。
# 所以这里现算三件事：原件在不在、拷贝与原件是否逐字节等、窗口 = 原件 ctime → mtime。
assert os.path.isfile(TMP), 'ABORT: D 臂原件不在 %s ⇒ 抓取窗口无从现算（不许改用手抄时刻）' % TMP
_draw = open(TMP, 'rb').read()
_drow = next(r for r in rows if r['path'] == os.path.join(HDIR, DLOG))
assert hashlib.md5(_draw).hexdigest() == _drow['md5'], \
    'ABORT: D 臂仓库件与 TEMP 目录原件 md5 不等 ⇒ 拷贝不可信，读数不能算作同一份抓取'
_ds = os.stat(TMP)
D_BORN_DT = datetime.fromtimestamp(_ds.st_ctime)
D_BORN = D_BORN_DT.strftime('%H:%M:%S')
D_MTIME = datetime.fromtimestamp(_ds.st_mtime).strftime('%H:%M:%S')
assert _drow['bytes'] == _ds.st_size, 'ABORT: D 臂两只是不同大小 ⇒ 不是同一份抓取'
# 窗口开始前那次重启的 wall-clock 估计 = 窗口起点 − 首条**完整**行的 uptime（第一只是被剪断的 289 ms 片段）
assert _drow['ups3'][0] == 289 and _drow['ups3'][1] == 105339, \
    'ABORT: D 臂开头两只 uptime 不再是 289 / 105339 ⇒ 剪断片段的判读要重写：%s' % _drow['ups3']
D_REBOOT = (D_BORN_DT - timedelta(milliseconds=_drow['ups3'][1])).strftime('%H:%M:%S')

# 判读 1) 2) 4) 要印的时刻与计数一律从臂行里取，取不到就 ABORT（不许留成"恰好还抄对"的字面量）
C_ROW = next(r for r in rows if r['name'].startswith('C '))
D_ROW = next(r for r in rows if r['name'].startswith('D '))
assert C_ROW['hold_up'] > 0 and C_ROW['ho_up'] > C_ROW['hold_up'], \
    'ABORT: C 臂的 hold / hold-on 时刻取不到（%d / %d）⇒ 判读 1) 不能印' % (C_ROW['hold_up'], C_ROW['ho_up'])
assert C_ROW['ho_ack'] == 0 and C_ROW['ho_nack'] > 0, \
    'ABORT: C 臂 hold-on 那一行的 known ACK/NACK 不是"全 NACK"：%s' % C_ROW['ho_up']
C_SCAN = C_ROW['scan_all']
assert len(C_SCAN) == 1 and C_SCAN[0][0] == '0', 'ABORT: C 臂全扫行不止一种读数或含 ACK：%s' % C_SCAN
C_ADDR = int(C_SCAN[0][0]) + int(C_SCAN[0][1])
assert C_ADDR == 0x77 - 0x08 + 1, \
    'ABORT: C 臂全扫 ACK+NACK 合计 %d 与 0x08-0x77 的 %d 不等 ⇒ 全扫口径变了，正文里的范围文字要重写' % (
        C_ADDR, 0x77 - 0x08 + 1)
assert C_ROW['kn_pairs'] == [('0', str(len(C_ROW['kn_addr'])))], \
    'ABORT: C 臂已知邻居读数不是"全 NACK 且数量自洽"：%s / %s' % (C_ROW['kn_pairs'], C_ROW['kn_addr'])
C_NB = len(C_ROW['kn_addr'])
assert D_ROW['replies'] == 0 and D_ROW['holdon'] == 0

# 判读 3) 与 4) 引用的排查记录**行号/节号** = 运行时按唯一锚点现查（R54 那一族：引指针要连内容一起核）
REC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
assert os.path.isfile(REC), 'ABORT: 排查记录不在 %s ⇒ 三处指针无从现查' % REC
_rec = open(REC, encoding='utf-8').read().split('\n')


def anchor(s):
    hits = [i + 1 for i, l in enumerate(_rec) if s in l]
    assert len(hits) == 1, 'ABORT: 锚点 %r 在排查记录里命中 %d 处（%s）⇒ 指针不唯一，行号不许印' % (s, len(hits), hits)
    return hits[0]


def sect_of(n):
    for i in range(n - 1, -1, -1):
        m = re.match(r'#{2,4} +([0-9]+(?:\.[0-9]+)?)', _rec[i])
        if m:
            return m.group(1)
    raise AssertionError('ABORT: 第 %d 行往上没有带编号的标题' % n)


L_PWRON = anchor('Key1→R26 510R→PWRON(30) 脚')
L_PWROUT = anchor('它是 AXP2101 的开机状态输出')
_NACK_LN = anchor('判读文本越权')
_NACK_SECT = sect_of(_NACK_LN)

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
L = []
w = L.append
w('R56 真机首烧 fb32168a 判据摘录（四臂；凡"读数"两字的字段一律由 hardware/r56_flash1.py 运行时现算，')
w('  非读数的只有两类：①下面"抓取手段"一节的流程描述（谁按的键、拉线拉多久）＝操作记录，②用户口述那一行＝输入前提）')
w('生成时刻 %s；本文件纯 LF；不含 SoftAP 口令明文（生成器只从 axp / epd / eink 三类行里取数）' % now)
w('')
w('== 抓取手段（四臂同一台 COM14、同一台主机、波特率 115200）==')
w('A：脚本先开串口再拉住 RTS 0.3 秒后松开 —— 实测这一遍**没有复位**（无 ROM banner、uptime 连续），')
w('   所以 A 的标题按实改成"连续读"，不叫复位起抓（原判据把一次失败的复位当成了复位）。')
w('B/C：C:/esp/cap_serial_reset.py（dtr=False + rts 拉 0.15 秒再松）—— 两遍都拿到 ROM banner 与 rst:0x15 USB_UART_CHIP_RESET。')
w('D：纯读 150 秒、不碰复位线，窗口 %s 至 %s（现算自 TEMP 目录原件的 ctime → mtime；仓库内那只拷贝的这两个时刻已被拷贝动作重置）；'
  '末字节比"脚本宣告完成"早约 5 s，本行取字节口径。' % (D_BORN, D_MTIME))
w('   期间用户按了电源键（时长与次数 = 用户口述前提，日志里无任何一侧能复算，本文件全程当输入前提不当读数）；'
  '口述内容 = "按了，但板上没有任何反应"。')
w('   D 窗口的第一行是被剪断的半行（uptime 289 的 esp_image 片段直接粘在 uptime 105339 那条 axp 行前面），')
w('   ⇒ 说明本窗口开始前板子已经重启过一次（估计 %s，算式 = 窗口起点 %s 减首条完整行的 uptime %d ms；'
  '原因**未定性**，不记成按键的后果，只记同时刻发生过一次重启）。' % (D_REBOOT, D_BORN, _drow['ups3'][1]))
w('')
w('== 镜像身份（开机指纹由 bin 现算，不是转抄）==')
for k in ('4842a3a0', 'fb32168a'):
    f = FP[k]
    w('%s 那只：md5=%s / %d B / bin[176:184]=%s（boot 行 ELF file SHA256 前 16 位应等于它）/ 文件=%s'
      % (k, f['md5'], f['size'], f['fp'], relp(BINS[k])))
w('')
w('== 四臂读数（每臂一行，全部现算）==')
for r in rows:
    w('%s' % r['name'])
    w('   载体=%s / %d B / md5=%s（**md5**，32 位 hex）/ 入库件 ctime %s → mtime %s / 非空行 %d / 图=%s / ROM banner %d 次%s' % (
        r['rel'], r['bytes'], r['md5'], r['born'], r['mtime'], r['lines'], r['img'], r['rom'],
        (' / ' + r['rst']) if r['rst'] else ''))
    w('   uptime %d 至 %d ms / probe#%d 至 probe#%d 共 %d 条 0x34 行：no reply=%d 应答=%d' % (
        r['up0'], r['up1'], r['p0'], r['p1'], r['nprobe'], r['noreply'], r['replies']))
    w('   ACK= 读数集合=%s / acked 名单集合=%s / 全扫行=%s / 已知邻居=%s 读数=%s（%d 条 known 行）' % (
        r['ackvals'], r['acked'], r['scan_all'] or '本臂无 bus scan 0x08-0x77 全扫行',
        '/'.join(r['kn_addr']) or '本臂无带名单的 known 行', r['kn_pairs'] or '-', r['kn_lines']))
    w('   PWR_OUT 对读组合=%s（1/0 = 悬空）/ hold-on 探针行 %d 条 / PP-SCL 实跑 %d 跳过 %d / BUSY stayed HIGH %d 条' % (
        r['pwr'], r['holdon'], r['pp_run'], r['pp_skip'], r['busy_high']))
    if r['elf']:
        w('   boot ELF 指纹=%s == bin[176:184]=%s 成立' % (r['elf'][0], FP[r['img']]['fp']))
    w('')
w('== 判读（只写这几臂能支撑的话）==')
w('1）C 臂证明 R53 那一步"补官方 esp_gpio_Init 同档的 GPIO1 拉住"**确实进了镜像并且在跑**：')
w('   boot 指纹对得上 + 开机 %d ms 有 PWR_OUT(GPIO1) hold = input+pull-up 这一行 + %d ms 有一次 hold-on 探针'
  '（两个时刻现算自 C 臂日志，非手抄）。' % (C_ROW['hold_up'], C_ROW['ho_up']))
w('2）同一个 C 臂把 R53 的**根因判定否证**了：hold-on 探针把 GPIO1 从"输入+上拉"升成"推挽输出高"之后，')
w('   0x34 仍不应答、%d 个已知邻居（%s）ACK=%d NACK=%d、随后整条总线 %d 个地址（0x08-0x77 全扫）仍 0 应答。'
  % (C_NB, '/'.join(C_ROW['kn_addr']), C_ROW['ho_ack'], C_ROW['ho_nack'], C_ADDR))
w('   ⇒ "GPIO1 没被拉住所以 PMIC 没上电所以全 NACK"这一条因果链，在**外部 5V 已接**的前提下不成立。')
w('   边界（同一条判据只覆盖探针那**一档**）：hold-on 是一次性的短时推挽高，不等于"从上电第一秒起持续按住"，')
w('   所以本条否证的范围止于"补这一档没用"，不含"任何更长/更早的按住都没用"。')
w('3）排查记录现读第 %d 行本来就有图纸口径：电源键走 Key1 经 R26 510R 到 PWRON(30) 脚，**不接任何 GPIO**；' % L_PWRON)
w('   现读第 %d 行：官方 pcf85063_bsp.h 里 PWR_OUT_PIN = GPIO1 是 AXP2101 的**开机状态输出**（输入+内部上拉读它）。' % L_PWROUT)
w('   ⇒ GPIO1 是"PMIC 说它开没开"的脚，不是"固件叫 PMIC 开机"的脚。R53 把方向读反了；')
w('   C 臂那一步等价于官方同档（输入+上拉），**无害**，但它不可能改变 PMIC 的开机状态，所以 D 臂改用物理按键。')
w('4）D 臂是**第一个真样本**（USB + 锂电池都在位、按键确认真按过）：%d 条 0x34 行仍全 no reply，' % D_ROW['noreply'])
w('   全程 PWR_OUT 对读只有一种组合 pu=1 pd=0 = 这根脚始终悬空 = PMIC 从头到尾没有宣布自己开机。')
w('   按排查记录现读 §%s（第 %d 行标题）的分流口径：**全 NACK 不定案**，' % (_NACK_SECT, _NACK_LN))
w('   所以这里只能说"按键没有把 PMIC 带进开机态（就本次这次按下而言）"，')
w('   不能定案是"PMIC 坏"，因为还有三条没分开：电池电压/座子接触、Key1 到 PWRON 那段网络（含 510R 虚焊）、PWR_OUT 脚号登记是否对。')
w('5）"按了但板上没有任何反应"这句是用户口述，本文件把它当**输入前提**登记（D 臂靠它才成立），不当取证读数；')
w('   我方固件按图纸读不到按键（PWRON 不接 GPIO），所以没有任何独立手段能证明这次按下的时长与落点。')
w('6）上面三处指针（两个行号 + 一个节号）由本脚本现查：每个锚点在排查记录里必须**恰好 1 命中**，否则本文件不生成；')
w('   所以"生成之后那几行被后续批次挤动"会让**下一次复跑**失败，而不是让本文件打出一个悄悄漂了的旧号——')
w('   本文件内的号只对生成时刻 %s 的盘上状态负责。' % now)
w('')
w('== 本轮余下唯一便宜的物理分叉（按代价从小到大）==')
w('a）换一块同型号板复跑同一条 C 臂判据（同 bin 比 pull compare 与 ACK 计数）—— 一次烧录，不用仪器；')
w('b）万用表两档：电池座两端电压（判"有没有电进去"）、PWRON(30) 脚在按下时的电平（判"按键网络通不通"）；')
w('c）若 a 与 b 都指回这块板，才是"PMIC/主板级"结论。')
w('')
w('== 没做什么（点名，不省略）==')
w('没换电池 / 没用万用表 / 没接第二块板 / 没改任何 main/ 源码 / 没重建固件（板上现在就是 fb32168a，')
w('   待烧与板上自本批起**重新相等**，(92) 那条分裂就地收口）/ 没有 push / 没有 amend / 零删除 /')
w('   没有往 hardware/ht305_sync/ 写一字节（gen 24 末版封界不动）/ 屏亮仍 0 次肉眼确认 / 未播提示音。')
w('VERDICT=FOUR-ARMS-ALL-NACK R53-ROOT-CAUSE-REFUTED PHYSICAL-KEY-ARM-FIRST-SAMPLE')

body = '\n'.join(L) + '\n'
BS = chr(92)
_hits = [l for l in body.split('\n') if BS in l]
assert not _hits, 'ABORT: 自写正文里出现反斜杠（§38.18 族）: %r' % (_hits[:3],)
assert 'zizhao1' not in body, 'ABORT: 正文含 SoftAP 口令明文'
open(OUT, 'w', encoding='utf-8', newline='').write(body)
back = open(OUT, 'rb').read().decode('utf-8')
assert back == body, 'ABORT: 独立回读与待写字节不逐字相同'
print('WROTE %s / %d B / %d 行 / md5=%s' % (
    os.path.relpath(OUT, REPO), os.path.getsize(OUT), back.count('\n'),
    hashlib.md5(open(OUT, 'rb').read()).hexdigest()))
print('ARMS=%d ALL_ACK_ZERO=%s PWR_COMBOS=%s' % (
    len(rows), sorted(all_ack_vals) == ['0'], sorted(set(p for r in rows for p in r['pwr']))))
print('PROBE_TOTALS=%s' % [(r['name'][:2], r['nprobe'], r['replies']) for r in rows])
