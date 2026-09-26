# R57 E 臂（COM14 回归后首抓）取证器：把 %TEMP% 抓回件抄进仓库 + 两侧 md5 对表 + 现算判据 + 自落载体。
# 为什么单独成批：C 臂 = 新镜像 + 复位起抓（当时只有 USB）；D 臂 = 新镜像 + USB + 锂电池 + 物理按键（没复位）。
#   E 臂是这两格交集的第一次同时成立：板上 = fb32168a、USB 与锂电池都在位、复位起抓 120s。
# 红线（沿用既有口径）：取证必须进仓库（临时目录里的东西不算取证）；载体由脚本自己在同一次运行里落盘；
#   每个数本遍现算，不抄上一批的话；写盘一律在 hardware/ht305_sync/ 之外（gen 24 是末版）；
#   载体正文不写反斜杠；口令明文只从宏本体读出做命中计数，绝不打印、绝不进载体正文。
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HDIR = HERE
SYNC = os.path.join(HDIR, 'ht305_sync')
SRC = os.path.join(os.environ.get('TEMP', ''), 'r57_E臂_新镜像_锂电池在位_复位起抓120s.log')
DST0 = os.path.join(HDIR, '20260925_R57_E臂新镜像锂电池在位复位起抓120s.log')
CAR0 = os.path.join(HDIR, '20260925_R57_E臂判据摘录.txt')
ARM_B = os.path.join(HDIR, '20260924_R56外部供电复位起抓45s_板上4842a3a0.log')
ARM_C = os.path.join(HDIR, '20260924_R56fb32168a首烧复位起抓90s.log')
ARM_D = os.path.join(HDIR, '20260924_R56按键窗口150s纯读_新镜像fb32168a.log')
MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
BUILD_BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
BINS = {'4842a3a0': os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin'),
        'fb32168a': os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin')}
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

ANSI = re.compile(r'\x1b\[[0-9;]*m')
UP = re.compile(r'[IWE] \((\d+)\)')
PRB = re.compile(r'probe#(\d+)')
PWR = re.compile(r'PWR_OUT pu=(-?\d) pd=(-?\d)')
ACKTOK = re.compile(r'[^N]ACK=(\d+)')
ACKED = re.compile(r'acked:\[([^\]]*)\]')
BUS = re.compile(r'bus scan 0x08-0x77: ACK=(\d+) NACK=(\d+)')
ELF = re.compile(r'ELF file SHA256:\s+([0-9a-f]{16})')


def md5_(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def money(x):
    return '{:,}'.format(int(x))


def git(*a):
    p = subprocess.run(('git',) + a, cwd=REPO, capture_output=True)
    assert p.returncode == 0, 'ABORT: git 失败 ' + ' '.join(a)
    return p.stdout.decode('utf-8', 'replace')


def scan_dir(d):
    n, tot, agg = 0, 0, hashlib.md5()
    for root, _ds, fs in os.walk(d):
        for f in sorted(fs):
            p = os.path.join(root, f)
            b = open(p, 'rb').read()
            n += 1
            tot += len(b)
            agg.update(hashlib.md5(b).hexdigest().encode('ascii'))
    return n, tot, agg.hexdigest()


def parse(path):
    raw = open(path, 'rb').read()
    txt = ANSI.sub('', raw.decode('utf-8', 'replace'))
    lines = [l.rstrip('\r') for l in txt.split('\n') if l.strip()]
    ups = [int(m.group(1)) for m in UP.finditer(txt)]
    prb = [int(m.group(1)) for m in PRB.finditer(txt)]
    st = os.stat(path)
    return dict(
        path=path, name=os.path.basename(path), bytes=len(raw), md5=hashlib.md5(raw).hexdigest(),
        lines=len(lines), rom=txt.count('ESP-ROM'),
        rst=next((l[:70] for l in lines if 'rst:0x' in l), ''),
        elf=sorted(set(m.group(1) for m in ELF.finditer(txt))),
        up0=ups[0] if ups else -1, up1=ups[-1] if ups else -1,
        noreply=sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' in l),
        replies=sum(1 for l in lines if 'AXP@0x34' in l and 'no reply' not in l),
        nprobe=len(prb), pmin=min(prb) if prb else -1, pmax=max(prb) if prb else -1,
        pwr=sorted(set(PWR.findall(txt))), acktok=sorted(set(ACKTOK.findall(txt))),
        acked=sorted(set(ACKED.findall(txt))), bus=sorted(set(BUS.findall(txt))),
        holdon=[l for l in lines if 'hold-on probe' in l],
        panel=sum(1 for l in lines if 'panel silent' in l or 'panel blanked' in l),
        witness=sum(1 for l in lines if 'witness' in l.lower()),
        born=datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
        mtime=datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))


def win(r):
    return round((r['up1'] - r['up0']) / 1000.0, 3)


def per_probe(r):
    return round(win(r) / r['nprobe'], 3) if r['nprobe'] else -1


# ---------------- 前置：源在、明文只从宏读、指纹基准在、构建目录那只仍是 r53 归档那只 ----------------
assert os.path.isfile(SRC), 'ABORT: 抓回件不在 ' + SRC + ' ⇒ 本批没有取证对象，不许凭记忆写数'
_sb = open(SRC, 'rb').read()
assert len(_sb) > 1000, 'ABORT: 抓回件只有 %d B，不像一次完整抓取' % len(_sb)
_mm = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', open(MACRO, encoding='utf-8', errors='replace').read())
assert _mm, 'ABORT: 读不到 PROV_PASS 宏，明文闸无法自证扫的是真口令'
SECRET = _mm.group(1).encode('utf-8')
for _k, _p in BINS.items():
    assert os.path.isfile(_p), 'ABORT: 指纹基准 bin 不存在 ' + _k
FP = {k: dict(md5=md5_(p), size=os.path.getsize(p), fp=open(p, 'rb').read()[176:184].hex()) for k, p in BINS.items()}
assert md5_(BUILD_BIN) == FP['fb32168a']['md5'] and os.path.getsize(BUILD_BIN) == FP['fb32168a']['size'], \
    'ABORT: 构建目录那只与 r53 归档那只不再同值 ⇒ 先查清谁重建了，本批不写身份句'
_pp = subprocess.run((sys.executable, '-m', 'serial.tools.list_ports'), cwd=REPO, capture_output=True)
assert _pp.returncode == 0, 'ABORT: 串口枚举失败'
PORTS = sorted(set(re.findall(r'(?m)^(COM\d+)', _pp.stdout.decode('utf-8', 'replace'))))
COM14 = 'COM14' in PORTS
assert COM14, 'ABORT: 本遍列口里没有 COM14 ⇒ 抓回件身份可疑（不是这遍从 COM14 抓的），先查线'
REV = git('rev-list', '--count', 'origin/main..HEAD').strip()
assert REV.isdigit(), 'ABORT: rev-list 读数不是数字'
ST = [l for l in git('-c', 'core.quotePath=false', 'status', '--porcelain').splitlines() if l.strip()]
MOD_N = len([l for l in ST if l[:2] == ' M'])
UN_N = len([l for l in ST if l[:2] == '??'])
SEAL0 = scan_dir(SYNC)

# ---------------- 抄进仓库（拒绝覆写；已存在则只认与原件同值的那一遍） ----------------
ALREADY = os.path.exists(DST0)
SRC_MD5 = hashlib.md5(_sb).hexdigest()
if ALREADY:
    assert open(DST0, 'rb').read() == _sb, 'ABORT: 仓库里已有同名抓回件而字节不等 ⇒ 不是同一份，拒绝覆写'
    COPIED = 0
else:
    shutil.copyfile(SRC, DST0)
    assert open(DST0, 'rb').read() == _sb, 'ABORT: 拷贝过程动了字节'
    COPIED = 1
DST_MD5 = md5_(DST0)
BYTE_TIE = (SRC_MD5 == DST_MD5)
assert BYTE_TIE, 'ABORT: 两侧 md5 不等'

E, Cc, Dd, Bb = parse(DST0), parse(ARM_C), parse(ARM_D), parse(ARM_B)
assert E['elf'] and E['elf'][0] == FP['fb32168a']['fp'], \
    'ABORT: E 臂 boot 指纹 %s 不等于 fb32168a 那只现算的 [176:184]=%s ⇒ 板上不是这只镜像' % (E['elf'], FP['fb32168a']['fp'])
assert Bb['elf'] and Bb['elf'][0] == FP['4842a3a0']['fp'], 'ABORT: B 臂（旧镜像对照）boot 指纹与 4842a3a0 那只现算值不等'
assert E['rom'] == 1 and 'rst:0x' in E['rst'], 'ABORT: E 臂不是一次复位起抓（ROM banner=%d，rst 行=%r）⇒ "复位起抓"这个标题是假的' % (E['rom'], E['rst'])
assert E['replies'] == 0 and E['acktok'] in (['0'], []), 'ABORT: E 臂出现 0x34 应答（replies=%d ACK=%s）⇒ 全 NACK 判读要整体重写' % (
    E['replies'], E['acktok'])
assert E['pwr'] == [('1', '0')], 'ABORT: E 臂 PWR_OUT 组合不是 pu=1 pd=0（现 %s）⇒ "这根脚始终悬空"那句要重写' % E['pwr']
assert E['holdon'], 'ABORT: E 臂没有 hold-on 探针行 ⇒ R53 那一步"到底进没进镜像并在跑"这一格本批拿不出证据'
SAME_SHAPE = (E['pwr'] == Cc['pwr'] == Dd['pwr']) and (E['acktok'] == Cc['acktok']) and (E['acked'] == Cc['acked']) and (E['bus'] == Cc['bus'])
assert len(set((r['bytes'], r['md5']) for r in (E, Cc, Dd, Bb))) == 4, 'ABORT: 四只日志里有两只字节+md5 同值 ⇒ 抓回件身份重叠，先查清'
ARM_PLAIN = {r['name']: open(r['path'], 'rb').read().count(SECRET) for r in (E, Cc, Dd, Bb)}
PLAIN_E = ARM_PLAIN[E['name']]
DENOM = sorted([f for f in os.listdir(HDIR) if f.endswith('.log')])
DENOM_OFF = [f for f in DENOM if '官方例程' in f]
LOG_TIE = (len(DENOM), len(DENOM_OFF), len(DENOM) - len(DENOM_OFF))

# ---------------- 载体（幂等：已存在即 ABORT，绝不覆写自己的取证件） ----------------
CAR = CAR0 if not os.path.exists(CAR0) else CAR0.replace('.txt', '_v2.txt')
assert not os.path.exists(CAR), 'ABORT: 判据摘录载体已存在（含 v2）⇒ 本工具不许覆写取证原件'

ROWS = []
ROWS.append('R57 E 臂取证器（COM14 回归后首抓）  MODE=' + ('ALREADY-COPIED' if ALREADY else 'COPIED-NOW'))
ROWS.append('本遍现跑于 ' + RUN_AT + '；载体由脚本自己在同一次运行里落盘，落在 hardware/（ht305_sync 之外）')
ROWS.append('COPY 原件 = 临时目录那只（写作 %TEMP%/' + os.path.basename(SRC) + '，绝对路径含反斜杠 ⇒ 按 §38.18 那一族只引用不整抄）/ '
            + money(len(_sb)) + ' B / md5 ' + SRC_MD5 + ' / 原件 mtime '
            + datetime.fromtimestamp(os.stat(SRC).st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
ROWS.append('COPY 仓库件 = hardware/' + E['name'] + ' / ' + money(E['bytes']) + ' B / md5 ' + E['md5']
            + '；两侧逐字相等 = ' + str(BYTE_TIE) + '；本遍执行拷贝动作 = ' + str(COPIED) + ' 只（' + str(1 - COPIED) + ' = 复跑支只核不等写）')
ROWS.append('COPY 时刻口径：仓库件 born ' + E['born'] + ' / mtime ' + E['mtime'] + ' —— 文件名与 mtime 都是拷贝时刻，**不是抓取时刻**；'
            '抓取时刻 = 原件 mtime = ' + datetime.fromtimestamp(os.stat(SRC).st_mtime).strftime('%Y-%m-%d %H:%M:%S') + '（上一句已点名）')
ROWS.append('IDENTITY E 臂 boot 行 ELF 指纹 = ' + E['elf'][0] + ' == fb32168a 那只 bin 现算 bin[176:184] = ' + FP['fb32168a']['fp']
            + ' 成立 = True；同遍现算 4842a3a0 那只 = ' + FP['4842a3a0']['fp'] + '（B 臂 boot 指纹与它相等 = '
            + str(Bb['elf'] and Bb['elf'][0] == FP['4842a3a0']['fp']) + '）⇒ 板上现在跑的是 fb32168a…（md5 ' + FP['fb32168a']['md5'][:8] + '…）')
ROWS.append('E 臂读数：' + money(E['bytes']) + ' B / 非空 ' + str(E['lines']) + ' 行 / ROM banner ' + str(E['rom']) + ' 次 / rst = ' + E['rst'])
ROWS.append('E 臂计数：uptime ' + str(E['up0']) + '→' + str(E['up1']) + ' ms（窗口 ' + str(win(E)) + ' s）/ probe# ' + str(E['nprobe'])
            + ' 次（' + str(E['pmin']) + '~' + str(E['pmax']) + '）/ AXP@0x34 行 ' + str(E['noreply'] + E['replies']) + ' 条，其中应答 '
            + str(E['replies']) + ' 条 / 每 probe 秒数 = ' + str(per_probe(E)) + ' s')
ROWS.append('E 臂对读：PWR_OUT 组合 ' + str(E['pwr']) + '（只此一种）/ 全部 ACK= 读数 ' + str(E['acktok']) + ' / acked 名单 '
            + str(E['acked']) + ' / 全总线路扫 ' + str(E['bus']) + ' / panel silent+blanked ' + str(E['panel']) + ' 行 / witness ' + str(E['witness']) + ' 行')
ROWS.append('E 臂 hold-on 探针在册 = ' + str(len(E['holdon'])) + ' 行；第一行逐字：' + (E['holdon'][0][:170] if E['holdon'] else 'NA'))
ROWS.append('对照臂（同遍现算，不抄上一批的话）：')
for nm, r in (('C 新镜像+复位起抓90s（当时只有 USB）', Cc), ('D 新镜像+USB+锂电池+按键（没复位）', Dd), ('B 旧镜像+复位起抓45s（对照）', Bb)):
    ROWS.append('  ' + nm + ' = ' + r['name'] + ' / ' + money(r['bytes']) + ' B / md5 ' + r['md5'][:8] + '… / 窗口 ' + str(win(r))
                + ' s / probe ' + str(r['nprobe']) + ' 次 / 0x34 行 ' + str(r['noreply'] + r['replies']) + ' 条（应答 ' + str(r['replies'])
                + '）/ PWR ' + str(r['pwr']) + ' / 每 probe ' + str(per_probe(r)) + ' s')
ROWS.append('CMP 同形判据（E vs C 逐格：PWR / ACK 读数 / acked 名单 / 全总线扫）= ' + str(SAME_SHAPE)
            + '；E 与 C 唯一实测差 = 供电档位（C 抓时锂电池未接、E 抓时 USB 与锂电池都在位）与窗口长度')
ROWS.append('VERDICT 判读：E 臂复现"全 NACK"——锂电池在位 + 复位起抓这一格加进来之后，0x34 应答计数仍然是 ' + str(E['replies'])
            + ' 条；按 §14.3 的口径**全 NACK 不定案** ⇒ 本批只把"接不接电池都一样"登记成事实，不结案、不改判 PMIC 本体')
ROWS.append('DENOM 屏侧分母换代（现算）：hardware/ 单层 *.log = ' + str(LOG_TIE[0]) + ' 只 / 其中"官方例程"对照 ' + str(LOG_TIE[1])
            + ' 只不进分母 / 我方 = ' + str(LOG_TIE[2]) + ' 只（上一格在册 9 只，本批 +1 = E 臂）')
ROWS.append('PLAIN 明文半径（口令只从 ' + os.path.relpath(MACRO, REPO).replace(chr(92), '/') + ' 的宏体读出做计数，不打印、不进本载体正文）：'
            + ' / '.join(k + '=' + str(v) + ' 处' for k, v in sorted(ARM_PLAIN.items()))
            + ' ⇒ E 臂入库件**自带明文 ' + str(PLAIN_E) + ' 处**，与 R56 的 B/C 两臂同案 ⇒ 每轮提交逐只点名 DROP、绝不 stage、绝不 push')
ROWS.append('FIELD 现跑：串口枚举 = ' + ', '.join(PORTS) + ' ⇒ COM14 在位 = ' + str(COM14)
            + '（R53~R56 那些"COM14 缺席"的在册句量的是它们各自那一遍，本遍不推翻也不复用）/ git rev-list origin/main..HEAD = '
            + REV + '（未 push）/ git status --porcelain = ' + str(len(ST)) + ' 行（' + str(MOD_N) + ' 只 M + ' + str(UN_N) + ' 只 ??）')
ROWS.append('SEAL 写盘前 hardware/ht305_sync/ = ' + str(SEAL0[0]) + ' 只 / ' + money(SEAL0[1]) + ' B / 聚合 md5 ' + SEAL0[2]
            + '（本批未新建清单代次，gen 24 仍是末版）')
ROWS.append('NOTDONE 本批没做（点名）：没换电池 / 没万用表 / 没第二块板（§38.23 那两条物理分叉仍在用户侧）/ 没改 main/ 源码、没重建固件（板上那只就是 fb32168a）'
            + ' / 没往 hardware/ht305_sync/ 落一字节 / 没新建备份根 / 没 push、没 amend / 零删除（%TEMP% 原件不搬走）'
            + ' / 屏亮肉眼确认仍 0 次 ⇒ 不播提示音 / docs 第十遍、backups README 第十次读数、todo 第十七遍、提交轮 #9、第 14 代同步都在本件之后')

TXT = '\n'.join(ROWS) + '\n'
for _l in ROWS:
    assert chr(92) not in _l, 'ABORT: 载体正文里有反斜杠（§38.18 那一族），只准引用不准整抄：' + _l[:80]
    assert SECRET not in _l.encode('utf-8'), 'ABORT: 载体正文含口令明文'
    assert 'None' not in _l and '<built-in' not in _l and '{' not in _l, 'ABORT: 有没被求值的占位：' + _l[:80]
SEAL1 = scan_dir(SYNC)
assert SEAL1 == SEAL0, 'ABORT: 归档目录被本遍改动了（' + str(SEAL0) + ' -> ' + str(SEAL1) + '）⇒ gen 24 末版被亲手降级'
open(CAR, 'w', encoding='utf-8', newline='\n').write(TXT)
_rb = open(CAR, 'rb').read()
assert _rb.decode('utf-8') == TXT and _rb.count(b'\r') == 0 and SECRET not in _rb, 'ABORT: 载体回读不等或破了纯 LF 或含明文'

print('R57_FLASH1_AT=' + RUN_AT)
print('MODE=' + ('ALREADY-COPIED' if ALREADY else 'COPIED-NOW') + '  拷贝执行=' + str(COPIED) + ' 只')
print('SRC md5=' + SRC_MD5 + ' / ' + money(len(_sb)) + ' B')
print('DST md5=' + DST_MD5 + ' / ' + money(E['bytes']) + ' B  BYTE_TIE=' + str(BYTE_TIE))
print('IDENTITY boot=' + E['elf'][0] + '  fb32168a[176:184]=' + FP['fb32168a']['fp'] + '  4842a3a0[176:184]=' + FP['4842a3a0']['fp'])
print('E probe=%d  0x34行=%d  应答=%d  窗口=%ss  每probe=%ss  PWR=%s  ACK=%s  bus=%s  rst=%s' % (
    E['nprobe'], E['noreply'] + E['replies'], E['replies'], win(E), per_probe(E), E['pwr'], E['acktok'], E['bus'], E['rst'][:40]))
print('CMP C/D/B probe=%d/%d/%d  replies=%d/%d/%d  SAME_SHAPE=%s' % (
    Cc['nprobe'], Dd['nprobe'], Bb['nprobe'], Cc['replies'], Dd['replies'], Bb['replies'], SAME_SHAPE))
print('DENOM all=%d off=%d ours=%d' % LOG_TIE)
print('PLAIN ' + ' / '.join('%s=%d' % (k[:24], v) for k, v in sorted(ARM_PLAIN.items())))
print('FIELD ports=' + ','.join(PORTS) + ' COM14=' + str(COM14) + ' rev-list=' + REV + ' status=%d 行' % len(ST))
print('SEAL before==after = ' + str(SEAL1 == SEAL0) + ' (' + str(SEAL0[0]) + ' 只 / ' + money(SEAL0[1]) + ' B / ' + SEAL0[2][:8] + '…)')
print('CARRIER=hardware/' + os.path.basename(CAR) + '  ROWS=' + str(len(ROWS)) + '  BYTES=' + money(os.path.getsize(CAR)))
print('VERDICT=E-ARM-ALL-NACK BATTERY-IN-PLACE-FROM-RESET REPRODUCES-C-ARM NO-VERDICT-CHANGE')
