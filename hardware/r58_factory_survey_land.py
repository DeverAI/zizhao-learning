# R58 正文遍 = 原厂 8 MB 整片固件的勘察 + 真机首烧（第一次烧**别人**的固件）判读落纸。
# 本轮三件事：①只读勘察两只原厂件（分区表/板名/凭据/AXP 代码量）；②COM14 整片烧原厂件 + 复位起抓 120 s；
# ③把读到的**板型改判**落进 排查记录 §38.29 + 烧录须知 〇-补4 + FreqErr 第九批，并把 120 s 日志按明文闸条件复制进仓库。
# 红线：两只原厂 .bin 是用户资料，**只读、一字节不改**；不往 hardware/ht305_sync/ 落一字节（gen 24 封界）；
#   不 push；不 amend；零删除；PROV_PASS 一律符号锚，绝不进命令文本与正文。
import ast
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

_T0 = datetime.now()
AT = _T0.strftime('%Y-%m-%d %H:%M:%S')

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
GUIDE = os.path.join(HDIR, '烧录须知.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
MAIN = os.path.join(HDIR, 'zizhao-esp32s3', 'main')
SRC_MACRO = os.path.join(MAIN, 'provision_ap.c')
VMRUN = os.path.join(HDIR, 'vm_run.py')
TOOL = os.path.abspath(__file__)
CARRY = os.path.join(HDIR, 'r58_factory_survey_land.txt')
PROBE = 'evidence/SEAL_VIOLATION_PROBE14.txt'

# ---- 原厂件（用户资料，只读）----
DUMP = os.path.join(REPO, 'esp32s3_flash_backup_8mb.bin')
PPT = os.path.join(REPO, 'esp32s3_partition_table.bin')
# ---- 本遍产证（都在 %TEMP%，不进仓库除非过闸）----
LOG = 'C:/Users/david/AppData/Local/Temp/r58_factory_boot_120s.log'
SNAP = 'C:/Users/david/AppData/Local/Temp/r58_preflash_8mb.bin'
# ---- 对照物 ----
V397_FIRMWARE = 'C:/esp/vendor_demo/ESP32-S3_e-Paper-3.97/Firmware/01_ESP32-S3_e-Paper-3.97.bin'
OUR_BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
TRANSCRIPT = ('C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/'
              '2c637e58-0a6e-4412-983d-959b7d542219.jsonl')
LOGDST = os.path.join(HDIR, '20260925_R58_原厂1_54固件启动120s.log')


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def mdb(b):
    return hashlib.md5(b).hexdigest()


def sh1(b):
    return hashlib.sha256(b).hexdigest()


def money(x):
    return '{:,}'.format(int(x))


def cnt_ff(b):
    return sum(1 for x in b if x != 0xFF)


# ================= 进入即装的门（全部排在任何 open(, w) 之前） =================
assert not os.path.exists(CARRY), 'ABORT: 本遍载体槽位非空，拒绝覆写'
assert not os.path.exists(LOGDST), 'ABORT: 仓库里已有同名日志，不覆写'
ast.parse(rd(TOOL))
for _p in (DUMP, PPT, LOG, SNAP, DOC, GUIDE, FREQ, SRC_MACRO, VMRUN, TRANSCRIPT, OUR_BIN):
    assert os.path.exists(_p), 'ABORT: 缺件 ' + _p

# ================= ①原厂件解剖：一切数字由本遍现读，不抄上一轮 =================
db = rb(DUMP)
PB = rb(PPT)
D_SIZE, D_MD5, D_SH = len(db), mdb(db), sh1(db)
D_NONFF = cnt_ff(db)
assert D_SIZE == 8388608, 'ABORT: 原厂整片件不是 8 MiB，现读 ' + str(D_SIZE)
assert mdb(PB) == 'ce84da71239a89d1a530c39589b3aca5', 'ABORT: 分区表小件指纹变了，上一轮的勘察不成立'
assert PB == db[0x8000:0x8000 + len(PB)], 'ABORT: 分区表小件 != 整片件 0x8000 处那 3,072 B'


def parse_pt(buf, base):
    rows = []
    for i in range(0, len(buf) - 31, 32):
        e = buf[i:i + 32]
        if int.from_bytes(e[:2], 'big') != 0xAA50:
            continue
        off = int.from_bytes(e[4:8], 'little')
        size = int.from_bytes(e[8:12], 'little')
        label = e[12:28].split(b'\x00')[0].decode('ascii', 'replace')
        rows.append((label, e[2], e[3], base + off, size))
    return rows


PT_ROWS = parse_pt(db[0x8000:0x8000 + 3072], 0)
assert len(PT_ROWS) == 3, 'ABORT: 分区表现读 ' + str(len(PT_ROWS)) + ' 只在册分区，不是 3'
PT_TXT = ' + '.join('%s@0x%X/0x%X' % (r[0], r[3], r[4]) for r in PT_ROWS)
_app = [r for r in PT_ROWS if r[0] == 'factory']
assert len(_app) == 1 and _app[0][3] == 0x10000
APP_OFF, APP_SIZE = _app[0][3], _app[0][4]
assert APP_OFF + APP_SIZE <= D_SIZE, 'ABORT: factory 分区超出 8 MiB ⇒ 这份表本身读歪了'

V397 = rb(V397_FIRMWARE)
V397_PT = parse_pt(V397[0x8000:0x8000 + 3072], 0)
V397_SPANS = max(r[3] + r[4] for r in V397_PT)
assert V397_SPANS > D_SIZE, 'ABORT: 3.97 原厂件那套分区并不超出 8 MiB ⇒ "刷不进我们这片"那句要重判'

# ================= ②AXP 代码量：本板原厂件 vs 3.97 原厂件（同一把尺） =================
def axp_words(buf):
    low = buf.lower()
    return {k.decode(): low.count(k) for k in (b'axp2101', b'axp192', b'axp_power', b'epd', b'epaper')}


D_AXP = axp_words(db)
V_AXP = axp_words(V397)
assert D_AXP['axp2101'] == 0 and D_AXP['axp192'] == 0 and D_AXP['axp_power'] == 0, \
    'ABORT: 原厂整片件里现读出 AXP 驱动字符串 %s ⇒ "本板无 AXP 代码"这句要重判' % D_AXP
assert V_AXP['axp2101'] > 0, 'ABORT: 3.97 那只原厂件里读不到 axp2101 ⇒ 对照臂失效，两臂同 0 不构成证据'
assert D_AXP['epaper'] > 0, 'ABORT: 原厂整片件里连 epaper 都读不到 ⇒ 读的可能是错的那只文件'
AXP_TXT = ('原厂整片件 axp2101=%d / axp192=%d / axp_power=%d / epaper=%d；'
           '3.97 那只 axp2101=%d / epaper=%d' %
           (D_AXP['axp2101'], D_AXP['axp192'], D_AXP['axp_power'], D_AXP['epaper'],
            V_AXP['axp2101'], V_AXP['epaper']))

# ================= ③120 s 日志：引文逐字从盘上现读，不凭记忆 =================
LB = rb(LOG)
LT = LB.decode('utf-8', 'replace')
LINES = [l.rstrip('\r') for l in LT.split('\n') if l.strip()]
LOG_SIZE, LOG_MD5, LOG_LN = len(LB), mdb(LB), len(LINES)
assert LOG_SIZE == 9604 and LOG_LN == 172, 'ABORT: 日志现读 %d B / %d 行，与在册 9,604 B / 172 行不符' % (LOG_SIZE, LOG_LN)

Q_PROJ = [l for l in LINES if 'Project name:' in l and '02_ePaper' in l]
Q_I2C = [l for l in LINES if l.startswith('i2c: {')]
Q_SHTC = [l for l in LINES if 'shtc3: ID:' in l]
Q_PA = [l for l in LINES if l.startswith('in_out: {')]
Q_MAC = [l for l in LINES if 'calibration data MAC check failed' in l]
Q_FSZ = [l for l in LINES if 'SPI Flash Size' in l]
Q_FWARN = [l for l in LINES if 'larger than the size in the binary image header' in l]
Q_RET = [l for l in LINES if 'Returned from app_main()' in l]
Q_LVGL = [l for l in LINES if 'Install LVGL tick timer' in l]
Q_SD = [l for l in LINES if 'send_op_cond' in l]
Q_SPI = [l for l in LINES if 'Initialize SPI' in l]
Q_G8 = [l for l in LINES if 'GPIO[8]' in l]
for _n, _g in (('Project name', Q_PROJ), ('i2c', Q_I2C), ('shtc3 ID', Q_SHTC), ('in_out', Q_PA),
               ('cal MAC', Q_MAC), ('SPI Flash Size', Q_FSZ), ('flash warn', Q_FWARN),
               ('Returned from app_main', Q_RET), ('LVGL tick', Q_LVGL), ('sdmmc', Q_SD),
               ('Initialize SPI', Q_SPI), ('GPIO[8]', Q_G8)):
    assert len(_g) == 1, 'ABORT: 日志里 ' + _n + ' 现读 ' + str(len(_g)) + ' 只命中，不是 1 ⇒ 引文没有唯一出处'

GPIO_RE = re.compile(r'GPIO\[(\d+)\]\| InputEn: (\d)\| OutputEn: (\d)\| OpenDrain: (\d)\| Pullup: (\d)\| Pulldown: (\d)')
GPIO_ROWS = [(int(g[0]), int(g[1]), int(g[2]), int(g[4])) for g in GPIO_RE.findall('\n'.join(LINES))]
GPIO_N = len(GPIO_ROWS)
GPIO_UNI = sorted(set(p for p, _i, _o, _u in GPIO_ROWS))
assert GPIO_N == 18 and len(GPIO_UNI) == 15, 'ABORT: GPIO 普查现读 %d 行 / %d 只不同编号，与在册 18 行 / 15 只不符' % (GPIO_N, len(GPIO_UNI))
OUTP = [p for p, i, o, u in GPIO_ROWS if o == 1]
INP = [p for p, i, o, u in GPIO_ROWS if i == 1]
SPI_GROUP = [p for p, i, o, u in GPIO_ROWS if o == 1 and p in (9, 10, 11)]
assert sorted(SPI_GROUP) == [9, 10, 11] and 8 in INP, 'ABORT: "Initialize SPI 之后 9/10/11 输出 + 8 输入"那格现读不成立 ⇒ 引脚改判要重读'
assert 46 in OUTP and 3 in OUTP, 'ABORT: 46/3 在原厂日志里并不是以输出出现的 ⇒ 与我方 EPD_RST/EPD_BUSY 的冲突句要重判'

OUR_MAP = rd(os.path.join(MAIN, 'epd_driver.c'))


def our_pin(name):
    m = re.search(r'#define\s+' + name + r'\s+\((\d+)\)', OUR_MAP)
    if not m:
        m = re.search(r'#define\s+' + name + r'\s+(\d+)', OUR_MAP)
    assert m, 'ABORT: 我方 epd_driver.c 里读不到 ' + name
    return int(m.group(1))


OP = {k: our_pin('EPD_' + k + '_PIN') for k in ('SCLK', 'MOSI', 'CS', 'DC', 'RST', 'BUSY')}
assert [OP[k] for k in ('SCLK', 'MOSI', 'CS', 'DC')] == [11, 12, 10, 9], 'ABORT: 我方 SPI 四根在册值变了：' + str(OP)
assert (OP['RST'], OP['BUSY']) == (46, 3), 'ABORT: 我方 RST/BUSY 在册值变了：' + str(OP)

# ---- 我方引脚表与 3.97 官方例程的逐字对照（这条链的来源要落在盘上，不落在记忆里）----
# 注：本遍第一版把出处写成 `epaper_port.c`，门直接红了（那只 .c 里 GPIO_NUM_ 命中 0 只）——
#     六根常量的真出处是**同一目录的 epaper_port.h**。
EPP = 'C:/esp/vendor_demo/ESP32-S3_e-Paper-3.97/ESP-IDF/08_ESP32-S3_e-Paper-3.97/components/epaper_port/epaper_port.h'
epp = rd(EPP)
EPP_PINS = [int(x) for x in re.findall(r'#define\s+EPD_(?:SCLK|MOSI|CS|DC|RST|BUSY)_PIN\s+\(?\s*(\d+)', epp)]
assert EPP_PINS == [11, 12, 10, 9, 46, 3], 'ABORT: 3.97 官方 epaper_port.h 那六根现读 ' + str(EPP_PINS) + ' 不是 11/12/10/9/46/3，来源链要重读'

# ================= ④明文凭据闸（口令只从宏体读出做计数，绝不打印） =================
_m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _m, 'ABORT: 读不到 PROV_PASS 宏'
secret = _m.group(1).encode('utf-8')
assert 8 <= len(secret) <= 63, 'ABORT: PROV_PASS 长度读数不像口令，正则可能吃多了'
DIRTY = b'softap ap ssid zizhao-esp32s3 pass ' + secret + b'\n'
assert DIRTY.count(secret) == 1, 'ABORT: 阳性对照自己不命中 ⇒ 这道闸没有执行者'
LOG_HITS = LB.count(secret)
POSCTL = 1
assert LOG_HITS == 0, 'ABORT: 120 s 日志含明文 ' + str(LOG_HITS) + ' 处 ⇒ 本遍不得把它复制进仓库'

# ================= ⑤esptool 侧引文：从会话记录里现 grep 逐字取回 =================
TR = rb(TRANSCRIPT)
QT_PROJ = b'02_ePaper_1_54_Test'
QT_WROTE = b'Wrote 8388608 bytes (1090314 compressed) at 0x00000000 in 30.6 seconds (effective 2195.5 kbit/s)...'
QT_HASH = b'Hash of data verified'
QT_CMD = b'--chip esp32s3 -p COM14 -b 921600 --before default_reset --after no_reset write_flash 0x0'
for _q in (QT_WROTE, QT_HASH, QT_CMD):
    assert _q in TR, 'ABORT: 会话记录里 grep 不到这条引文 ⇒ 它没有出处，不许落纸：' + _q[:40].decode()

# ================= ⑥烧录前快照（回滚三件套之一） =================
SB = rb(SNAP)
S_SIZE, S_MD5, S_NONFF = len(SB), mdb(SB), cnt_ff(SB)
assert S_SIZE == 8388608 and S_NONFF > 0
SNAP_PT = parse_pt(SB[0x8000:0x8000 + 3072], 0)
OURPT = rb('C:/esp/zproj/build/partition_table/partition-table.bin')
assert parse_pt(OURPT[0:3072], 0) == SNAP_PT, 'ABORT: 快照里的分区表 != 我方构建目录那只 ⇒ 回滚链的第一环没对上'
OUR_MD5 = mdb(rb(OUR_BIN))
ARC_MD5 = mdb(rb(os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin')))
R53ROOT = mdb(rb(os.path.join(REPO, 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin')))
assert R53ROOT == OUR_MD5, 'ABORT: r53 那根备份根里的镜像 != 待烧那只（现读 ' + R53ROOT + ' vs ' + OUR_MD5 + '）'
assert OUR_MD5.startswith('fb32168a') and ARC_MD5.startswith('4842a3a0')
assert db[APP_OFF:APP_OFF + 4096] != rb(OUR_BIN)[:4096], 'ABORT: 原厂件 app 起点与我方 bin 头部逐字相同 ⇒ 对照逻辑写歪了'

# ================= ⑦SEAL 双尺（写盘前读数 + 只在内存造阳性对照） =================
def fold_a_(d, extra=()):
    files = []
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            files.append(os.path.join(root, n))
    h = hashlib.md5()
    tot = 0
    for f in sorted(files):
        b = rb(f)
        tot += len(b)
        h.update(mdb(b).encode('ascii'))
    for e in extra:
        h.update(mdb(e.encode('utf-8')).encode('ascii'))
    return len(files) + len(extra), tot, h.hexdigest()


def fold_b_(d, extra=()):
    parts = []
    tot = 0
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            p = os.path.join(root, n)
            b = rb(p)
            tot += len(b)
            parts.append(os.path.relpath(p, d).replace(os.sep, '/') + ':' + mdb(b))
    for e in extra:
        parts.append(e + ':' + mdb(e.encode('utf-8')))
    return len(parts), tot, mdb('\n'.join(sorted(parts)).encode('utf-8'))


S0, T0 = fold_a_(SYNC), fold_b_(SYNC)
assert S0[:2] == T0[:2], 'ABORT: 两把尺公共量互核失败'
PA, PB2 = fold_a_(SYNC, (PROBE,)), fold_b_(SYNC, (PROBE,))
assert PA[2] != S0[2] and PB2[2] != T0[2] and not os.path.exists(os.path.join(SYNC, PROBE))
SEAL_A = '%d 只 / %s B / %s' % (S0[0], money(S0[1]), S0[2])
SEAL_B = '%d 只 / %s B / %s' % (T0[0], money(T0[1]), T0[2])

# ================= ⑧现场态（全部现跑） =================
def sh(args):
    p = subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


REV = sh(('git', 'rev-list', '--count', 'origin/main..HEAD'))[1].strip()
ST = [l for l in sh(('git', '-c', 'core.quotePath=false', 'status', '--porcelain'))[1].splitlines() if l.strip()]
ST_M = len([l for l in ST if l.startswith(' M')])
ST_Q = len([l for l in ST if l.startswith('??')])
HEAD = sh(('git', 'rev-parse', '--short', 'HEAD'))[1].strip()
assert re.fullmatch(r'\d+', REV) and HEAD, 'ABORT: git 读数形状不认识'

# ================= 正文 A：排查记录 §38.29（CRLF，纯追加在 EOF） =================
SEC = [
    '### 38.29 R58（本遍进入 ' + AT + '）：原厂 8 MB **整片**固件到手 + 第一次真机烧**别人的**固件 ⇒ **板型改判**：'
    '板上那颗是 `S3_ePaper_1_54`，我方全部引脚/几何/PMIC 前提来自 `ESP32-S3_e-Paper-3.97` 那一包 —— '
    'R24~R43 那几十次位碰探针**全测在不是本板的总线上**（现跑于 ' + AT + '；本遍**烧了原厂件**、**我方镜像已从板上取下**、屏亮肉眼确认仍 0 次、未 push）',
    '',
    '- **来源与身份（用户 2026-09-25 提供，放在仓库根）**：`esp32s3_flash_backup_8mb.bin` = **' + money(D_SIZE) + ' B**（整片 8 MiB，'
    '非 FF 字节 **' + money(D_NONFF) + '**）/ md5 **' + D_MD5 + '** / sha256 前 16 位 `' + D_SH[:16] + '`；'
    '`esp32s3_partition_table.bin` = ' + money(len(PB)) + ' B / md5 **' + mdb(PB) + '**，'
    '本遍现读它 **逐字等于** 整片件 `0x8000` 处那 3,072 B（一道 assert）⇒ 两只是一对，不是两次不同时间的备份。'
    '**两只都是用户资料，本遍只读、一字节未改，且永不 stage。**',
    '- **分区解剖（本遍现读整片件 `0x8000`，32 字节一项、`>H` 魔数 0xAA50）**：' + PT_TXT +
    '。`factory` 起点 **0x%X**、跨度 **0x%X** ⇒ 整片件里 app 从 `0x10000` 起，与我方那套（bootloader@0x0 / pt@0x8000 / app@0x20000）**不同**：'
    '对方是**单 app 分区**布局，我方是 OTA 双槽布局。' % (APP_OFF, APP_SIZE),
    '- **为什么不能拿 3.97 那只原厂件做 A/B（本遍现读对照臂）**：`01_ESP32-S3_e-Paper-3.97.bin` 的分区跨度合计 **0x%X** > 本片 0x800000 ⇒ '
    '它是**面向 16 MB flash** 建的，烧不进我们这片 8 MB；而本次到手的 `02_ePaper_1_54_Test` 分区合计正好落在 4 MiB 内 ⇒ 与板上这片 8 MB 兼容。'
    % V397_SPANS,
    '- **板型改判的第一条正样本（运行时打印，逐字）**：日志第 ' + str(LINES.index(Q_PROJ[0]) + 1) + ' 行 `' + Q_PROJ[0].strip() + '`，'
    '第 ' + str(LINES.index(Q_I2C[0]) + 1) + ' 行 `' + Q_I2C[0].strip() + '`，第 ' + str(LINES.index(Q_SHTC[0]) + 1) + ' 行 `' + Q_SHTC[0].strip() + '`。'
    '我方 R24~R43 的**全部** I²C 探针都在 **SDA=41 / SCL=42** 上扫 **0x34**（`main/axp_panel_power.c:28-30` 在册），读数一直是"全 NACK"。'
    '本板真正的总线在 **47/48**，而 47/48 上有一颗 SHTC3 **回了 `ID:0887`** —— 那是本项目**第一个正向 I²C 应答**。',
    '- **`ID:0887` 为什么算正样本（出处在原厂件的第三方源码里，不是我的推测）**：厂商 `i2c_equipment.cpp:78-103` 里 `shtc3_id` '
    '**只在 `ESP_OK` 且 CRC 通过**那条分支才被赋值，非 `ESP_OK` 走 `ACK_ERROR` ⇒ 打印出非零 ID = 真做过一次读事务。'
    '**结论范围只到这里**：它证明 47/48 这条总线活着、有一颗 0x70 器件应答；它**不**证明屏活着。',
    '- **AXP 前提当场降级（同一把尺量两臂，本遍现算）**：' + AXP_TXT + '。⇒ 烧进本板的这份原厂固件里**没有任何 AXP 代码**，'
    '"屏电必须经 AXP2101 ALDO3 开出来"（烧录须知 〇 节、项目记忆 (91)）是 **3.97 那一包的 SDK 主张**，不是本板事实。'
    'R53 那条"PWR_OUT=GPIO1 是 AXP 电源自锁线"的根因**继承同一前提**，本遍**不回写它**（那是已落地正文），只在此点名：它的适用范围是"3.97 那颗板型"，本板未验证。',
    '- **原厂件里的 GPIO 普查（本遍从日志现读 ' + str(GPIO_N) + ' 行 / ' + str(len(GPIO_UNI)) + ' 只不同编号：' +
    '/'.join(str(p) for p in GPIO_UNI) + '）**：其中输出 = ' + '/'.join(str(p) for p in sorted(OUTP)) +
    '，输入（带上拉）= ' + '/'.join(str(p) for p in sorted(INP)) + '。'
    '而原厂件里**没有** MISO/CS 之外的第二组脚——即 `driver: Initialize SPI`（日志第 ' + str(LINES.index(Q_SPI[0]) + 1) + ' 行）之后紧跟的四行是 '
    '**GPIO9 / GPIO10 / GPIO11 配成输出 + GPIO8 配成输入带上拉**（第 ' + str(LINES.index(Q_SPI[0]) + 2) + '~' + str(LINES.index(Q_G8[0]) + 1) + ' 行、1064~1084 ms 段）—— '
    '而 **MOSI=12** 因为走硬件 SPI 的 iomux、不经 `gpio_config`，所以原厂日志里**不会**打印它 ⇒ "12 没出现"**不能**读成"12 不是 MOSI"。',
    '- **两条引脚冲突（本遍能确定的只有"冲突"本身）**：我方 `epd_driver.c:16-21` 在册 RST=**' + str(OP['RST']) + '**、BUSY=**' + str(OP['BUSY']) + '**；'
    '而原厂件把 **46** 打印为音频功放 `pa`（`' + Q_PA[0].strip() + '`）并以输出驱动，把 **3** 配成**输出**（`Returned from app_main()` 之后那一行，'
    + str(LINES.index(Q_RET[0]) + 1) + ' 行附近）。⇒ 若本板沿用我方引脚表，固件会**去拉扯功放使能脚**当复位、**去读一根被对方当输出驱动的脚**当 BUSY。'
    'BUSY 最强候选是原厂件里唯一"输入 + 上拉 + 位于 SPI 初始化组内"的那只 **GPIO8**。',
    '- **本遍仍未确立（点名，不猜）**：① 屏的物理尺寸与分辨率（固件自报 `1_54`，但我方素材系统 UI 按 800×480 排版；两者谁真，肉眼一看便知，本遍没有读数）；'
    '② 本板 EPD 的 MOSI/RST/BUSY **三只都未确立** —— 上面只是"候选 + 冲突"，不是判定；③ 120 s 日志里**没有任何一行**能证明原厂 demo 真的刷过屏'
    '（LVGL tick 装了、`Returned from app_main()` 有，但墨水屏刷新不发日志）⇒ **屏亮肉眼确认累计仍 0 次**，本遍**不播提示音**；'
    '④ 47/48 上除 0x70 外还有哪些器件、0x18 那次"初始化成功"是否真应答，本遍**未扫**（要等我自己那把尺，见下一节）。',
    '- **烧录与回滚（命令原文，逐字从会话记录现 grep 回来并断言存在）**：'
    '`esptool --chip esp32s3 -p COM14 -b 921600 --before default_reset --after no_reset write_flash 0x0 ' + os.path.basename(DUMP) + '` ⇒ '
    '`' + QT_WROTE.decode() + '` + `' + QT_HASH.decode() + '`。回滚三件套：'
    '① 烧前整片快照 `%TEMP%\\r58_preflash_8mb.bin`（' + money(S_SIZE) + ' B / md5 **' + S_MD5 + '** / 非 FF **' + money(S_NONFF) + '** 字节，'
    '其 `0x8000` 处分区表与我方构建目录那只**逐字相同**（一道 assert））；'
    '② 我方三件套 `C:/esp/zproj/build/`（app md5 **' + OUR_MD5 + '** 应落 `0x20000`、pt@`0x8000`、bootloader@`0x0`、ota_data@`0x15000`）；'
    '③ 归档件 `backups/r43_20260922_131029/zizhao_esp32s3.bin`（md5 **' + ARC_MD5 + '**，即上一代在板那只；本遍另现读 `backups/r53_20260924_083929/` 那根里的镜像 == 待烧那只 ' + R53ROOT[:8] + '…）。'
    '**⇒ 自本遍起"待烧 = 板上"这条等式第二次断裂，且这次断在相反方向**：板上是**原厂** `' + D_MD5[:8] + '…`，待烧仍是我方 `' + OUR_MD5[:8] + '…`。',
    '- **顺带读出的两件（不是我方的，但会影响后续判断）**：'
    '`' + Q_FSZ[0].strip() + '` + `' + Q_FWARN[0].strip()[:78] + '…` ⇒ 那份镜像的 header 声明 **4 MB**，这片 flash 实测 **8 MB**；'
    '`' + Q_MAC[0].strip()[:74] + '…` ⇒ **整片件来自另一台机器**（其 NVS 里存的 MAC 是 `70:04:1d:d7:b1:08`，本板是 `70:04:1d:d8:75:8c`），'
    '所以随镜像进来的还有**别人的 NVS / Wi-Fi 配置 / BLE 密钥**（cal_data 键含凭据）⇒ **本遍我方自己的配网配置已被覆盖**，'
    '且这两只 .bin 内含凭据键，**永不 stage、永不 push、值不外泄**。',
    '- **本遍没做（点名，绑定执行者）**：没换电池、没上万用表、没接第二块板；**没改 `main/` 任何一字节源码、没重建我方固件**'
    '（`C:/esp/zproj/build` 那只仍是 R56 那 `fb32168a…`）；没做 47/48 全地址扫描、没做 EPD 候选引脚判定 ⇒ 这两件都排进"再搞新固件"；'
    '没往 `hardware/ht305_sync/` 落一字节（SEAL 见载体）、没新建清单代次、没新建备份根；'
    '**没动那两只原厂 .bin，也没删 `%TEMP%` 里任何一件**；未 push、未 amend。',
]
DOC_T = rd(DOC)
assert DOC_T.endswith('\r\n') and DOC_T.count('\n') == DOC_T.count('\r\n'), 'ABORT: 排查记录不是纯 CRLF'
DOCL0 = len(DOC_T.split('\r\n')) - 1
assert re.search(r'(?m)^### 38\.28 ', DOC_T), 'ABORT: 盘上最后一节不是 38.28 ⇒ 节号要重取'
assert not re.search(r'(?m)^### 38\.29 ', DOC_T), 'ABORT: §38.29 已在盘上，本遍不是纯追加'
DOC_SEC_LN = len(SEC)

# ================= 正文 B：烧录须知 〇-补4（LF，插在 ## 一、 之前） =================
GT = rd(GUIDE)
assert GT.count('\r') == 0 and GT.endswith('\n'), 'ABORT: 烧录须知不是纯 LF'
ANCH = '## 一、当前固件的真实状态'
assert GT.count(ANCH) == 1, 'ABORT: 须知插入锚不唯一'
GL0 = len(GT.split('\n')) - 1
GSEC = [
    '### 〇-补4、R58（2026-09-25 16:0x~16:1x 真机）：**烧的是原厂件** ⇒ 板型改判为 `S3_ePaper_1_54`，本节把"该看哪几行日志"换成**别人固件的指纹**',
    '',
    '> 为什么这一节存在：本仓库此前所有判据（〇、〇-补、〇-补2、〇-补3）都建立在"板上跑我方固件、屏电走 AXP2101@0x34、I²C 在 41/42"这套前提上。'
    'R58 把用户提供的**原厂整片固件**烧进 COM14 后，固件自己把板型打印了出来 —— 那套前提里属于 3.97 的部分**不适用于本板**。'
    '**下面这张表是"板上仍是原厂件"期间的读法；一旦回滚我方固件，回到 〇-补3 那节。**',
    '',
    '| 日志行（原厂件，逐字匹配用） | 这一行证明了什么 | 不能读成什么 |',
    '|---|---|---|',
    '| `Project name:     02_ePaper_1_54_Test` | 板上跑的是**别人**的固件，不是我方那只 | 不证明屏被刷过 |',
    '| `i2c: {sda: 47, scl: 48}` | 本板 I²C 总线在 **47/48**（我方探针一直在 41/42） | 不证明 41/42 上什么都没有（本遍未扫） |',
    '| `shtc3: ID:0887` | **本项目第一条正向 I²C 应答**；厂商源码里 ID 只在 `ESP_OK`+CRC 通过时才被赋值 | 不证明屏活着 |',
    '| `in_out: {codec: ES8311, pa: 46, ...}` | **GPIO46 在本板是功放使能**，而我方 `EPD_RST_PIN=46` | 不证明 46 一定不是屏复位（原厂那份 profile 可能是继承来的） |',
    '| `GPIO[3] ... OutputEn: 1` / `GPIO[8] ... InputEn: 1 Pullup: 1` | 我方 `EPD_BUSY_PIN=3` 在一根被当输出驱动的脚上；**BUSY 最强候选 = 8** | 不证明 8 就是 BUSY，要我方固件自己读 |',
    '| `SPI Flash Size : 4MB` + `Detected size(8192k) larger than ...` | 镜像 header 声明 4 MB、这片实为 8 MB ⇒ 原厂件按 4 MB 布局 | 不证明我方 8 MB 配置错 |',
    '| `calibration data MAC check failed: expected ..., found 70:04:1d:d7:b1:08` | **整片件来自另一台机器**（MAC 不同）⇒ 里面带别人的 NVS/凭据 | 不证明本板 MAC 被改 |',
    '',
    '- **回滚三件套与命令原文（本遍实测可用）**：'
    '`python -m esptool --chip esp32s3 -p COM14 -b 921600 --before default_reset --after hard_reset write_flash 0x0 C:/esp/zproj/build/bootloader/bootloader.bin` '
    '+ `... 0x8000 partition_table/partition-table.bin` + `... 0x20000 zizhao_esp32s3.bin`；'
    '整片回滚则 `write_flash 0x0 %TEMP%\\r58_preflash_8mb.bin`（md5 `' + S_MD5 + '`）。'
    '**注意：整片件烧法会连 NVS/phy/cal 一起换掉，我方配网配置随之丢失（本遍已经发生一次）。**',
    '- **本遍状态**：**COM14 在位**（本遍现跑枚举）、原厂件 `' + D_MD5[:8] + '…` 已写入并跑起来；'
    '我方待烧仍为 md5 `fb32168a…` 那只（`C:/esp/zproj/build/zizhao_esp32s3.bin`，本遍现读），**不在板上**；'
    '屏亮肉眼确认累计 **0 次** ⇒ 本遍**不播提示音**；两只原厂 .bin 与含凭据的镜像**永不 stage / 永不 push**。',
    '',
]
GUIDE_NEW = GT[:GT.index(ANCH)] + '\n'.join(GSEC) + '\n' + GT[GT.index(ANCH):]
GL1 = len(GUIDE_NEW.split('\n')) - 1
assert GUIDE_NEW.startswith(GT[:GT.index(ANCH)]) and GUIDE_NEW.endswith(GT[GT.index(ANCH):])
assert GL1 - GL0 == len(GSEC), 'ABORT: 须知行增量 ' + str(GL1 - GL0) + ' != 正文 ' + str(len(GSEC))

# ================= 正文 C：FreqErr 第九批 =================
T9 = ('## 2026-09-25（R58 第九批：烧了别人的固件之后浮出来的四只）新增 {N} 条'
      '（根族：**前提来自另一 SKU 的官方包** / **"板上是谁"从不验证** / **通用组件表里的多板型常量当本板事实** / '
      '**半截 UTF-8 输出被当成读到文件结尾**）')
FREQ_ROWS = [
    T9,
    '',
    '[错误类型] **整份引脚表 / 几何 / PMIC 前提来自另一 SKU 的官方 SDK，且此后所有"官方怎么做"的引用都落在错的官方包上**'
    '（R58 实测：本仓库 30 余轮、几十次位碰探针都在 SDA=41/SCL=42 上扫 0x34，'
    '出处是 `ESP32-S3_e-Paper-3.97` 那包的 `epaper_port.h`；而板上那颗自报 `02_ePaper_1_54_Test`、真总线是 47/48、里面**一字节 AXP 代码都没有**）',
    '→ 症状：每一次"我查过官方了"都是真的——官方代码存在、行号能 grep 到、注释写得清清楚楚；红的全落在物理世界：'
    '扫描永远 NACK、BUSY 永远不释放、屏永远不亮，于是排查方向被一层层加到"总线是不是死了/屏是不是坏了/供电是不是不够"。',
    '→ 为什么它危险：①它**自带免疫** —— 引用能落地、包名能对上文件、文件能读到，唯一没核的是"那包描述的是不是这块板"；'
    '②它让**后续所有维度排除法失效**（R34~R43 那六臂探针是在错误前提下测的，结论只能降到"在那条总线上没测到"）；'
    '③它成本极高：**鉴定板型最便宜的办法是烧一份会自报板型的第三方固件（30 秒），而我方选择了给自己的固件加第六个探针维度（数天）**。',
    '→ 正确做法：①凡"官方/原厂"字样的引用，登记时必须带 **包名 + 该包自报的板名**，并与**板上运行时打印的板名**对表；'
    '②任何"硬件维度已排除完毕"的结论，先回答"你凭什么确定这块板就是那颗板型"，答不出 ⇒ 结论上限写成"在这块**未鉴定**的板上没测到"；'
    '③拿不到原厂固件时，用**第三方会自报配置的固件**做一次性鉴定，再决定要不要继续给自己的固件加探针。',
    '[错误类型] **把"板上跑的就是我认的那块板 / 那个镜像"当默认前提，从不验证**（R58 之前"待烧 = 板上"这条等式被写过两次，'
    '两次都是**我猜的**；本遍第一次真烧别人的件，才发现连"板上是谁"这件事从来没有第二个出处）',
    '→ 症状：所有推理都成立，唯独它站的那块地基（"板上那只就是 fb32168a…"）没有任何一次被独立量过；'
    '日志里的 `ELF file SHA256` 明明是能白拿的身份证，被当成"顺便打出来的东西"。',
    '→ 为什么它危险：这是"完成态数字必须在载体落盘后现数"那条老规矩的**镜像亚种**——数字类断言被规矩盯着，'
    '"身份类"断言（这块板/这个镜像/这台机器是谁）反而无人取证；一旦身份错，**基于它的全部读数和全部结论一起作废**，而且不作废得很难看（它们各自内部都自洽）。',
    '→ 正确做法：①身份类断言要**指名由哪一行运行时输出支撑**（boot 行 `ELF file SHA256` / `Project name:` / MAC），拿不到就写成"未验证"；'
    '②跨轮引用身份时必须带**当轮现算的指纹**（md5/sha + 尺寸），不许只写"那只"；'
    '③本遍的正面样板：整片件的 MAC 与 cal_data 里的 MAC 一比，"这是另一台机器的备份"这条**免费**结论就出来了。',
    '[错误类型] **把通用组件 rodata 里那张"多板型 profile 表"当成"本板配置表"** —— 同一张表里同时躺着 `Board: ESP32S3_BOX` 的 '
    '`i2s/pa/lcd: {controller: st7789, cs: ext3, dc: 2, clk: 1, mosi: 0}` 与本板真正被打印的 `i2c: {sda: 47, scl: 48}`（R58 勘察原厂镜像时实测）',
    '→ 症状：静态扫二进制能搜出一堆"看起来像本板引脚"的行，行行都有出处；把 `pa: 46` 之外的 `dc: 2 / clk: 1 / mosi: 0` 也抄进台账，'
    '就等于凭空多出三只"官方在册"的引脚。',
    '→ 为什么它危险：它跟本批第 1 只是同一根族的**上半段**——第 1 只是"引用了错的包"，本只是"在同一个包里读出了不属于本板的那些行"；'
    'rodata 里的字符串**不会告诉你哪几行才是运行时真被打印的**，而它偏偏长得最像一手资料。',
    '→ 正确做法：①**只有日志里真出现过的那一行**才可进台账（判别式 = 逐字去运行时日志里 grep，命中 1 次才算）；'
    '②对二进制字符串的读法要写成"该镜像**含**此串"，不许写成"本板**是**此配置"；'
    '③多臂对照（本遍就是这么把 3.97 那包的 `axp2101` 与本包的 0 次放在一起，"无 AXP"这句话才有两条腿）。',
    '[错误类型] **`python -c` 打印含中文/箭头的 UTF-8 文本时，GBK 控制台下 `UnicodeEncodeError` 发生在已经打印了若干行之后** ⇒ '
    '半截输出很容易被读成"文件到这儿就读完了"（R58 本遍实测：先打完 695/696 两行才炸在 698 行那句 `⇒`）',
    '→ 症状：命令非零退出，但 stdout 里有**真实内容**；不看退出码时，那段真实内容像极了一次成功的读取。',
    '→ 为什么它危险：本仓库已登记过"编码守卫必须 stdout **与** stderr 都 reconfigure"那一族（第 5 次），'
    '本只是它在**一次性命令行读数**上的复发形态——落地脚本里都装了 reconfigure，随手写的 `python -c` 没有；'
    '而读数的现场态恰恰全靠这些一次性命令。',
    '→ 正确做法：①**任何**要打印中文/非 ASCII 的读数命令都进门就 `sys.stdout.reconfigure(encoding="utf-8")`（含 `-c` 一行流），'
    '或统一带 `PYTHONUTF8=1` 环境变量跑；②读文件的命令必须把**退出码**与输出一起看，非零就当"没读到"重跑；'
    '③同一族的第三种防护：把需要读的东西写进脚本而不是 shell 一行流（本遍 §38.29 里那 18 行 GPIO 就是这么来的）。',
]
N_NEW = len([l for l in FREQ_ROWS if l.startswith('[错误类型]')])
assert N_NEW == 4, 'ABORT: 本批正文现算 ' + str(N_NEW) + ' 条，不是 4'
FREQ_ROWS[0] = T9.replace('{N}', str(N_NEW))

FRQ_T = rd(FREQ)
assert FRQ_T.endswith('\r\n') and FRQ_T.count('\n') == FRQ_T.count('\r\n'), 'ABORT: FreqErr 不是纯 CRLF'
FL0 = FRQ_T.split('\r\n')
FE0 = len([l for l in FL0 if l.startswith('[错误类型]')])
FLN0 = len(FL0) - 1
assert re.search(r'(?m)^## 2026-09-25（R57 第七批', FRQ_T), 'ABORT: FreqErr 末批不是 R57 第七批 ⇒ 本批批号要重取'

LEDGER = ('>'
          ' **【' + AT + ' 落地｜R58 第九批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（本脚本进入时刻 ' + AT + '，_T0 取在任何产证动作之前）：'
          '全文 `^[错误类型]` 条数 = **' + str(FE0) + '**、行数 = **' + str(FLN0) + '**、字节 = **' + money(len(FRQ_T.encode('utf-8'))) + '**；'
          '本批正文 = **' + str(N_NEW) + '** 条 / **' + str(len(FREQ_ROWS)) + '** 行（**不含**本台账行、**不含**标题上方那只 glue 空行，两者另计）；'
          '**落盘后的终态由本遍载体现数**（完成态数字不在本行预写）。'
          '同遍排查记录改前 **' + str(DOCL0) + '** 行 -> 本遍真追加 §38.29 共 **' + str(DOC_SEC_LN) + '** 行 + 1 只 glue 空行；'
          '烧录须知改前 **' + str(GL0) + '** 行 -> 本遍在 `## 一、` 之前插入 **' + str(len(GSEC)) + '** 行；'
          '两只原厂 .bin 与 120 s 日志的明文读数：日志 HITS=' + str(LOG_HITS) + '（阳性对照在内存里 = ' + str(POSCTL) + '）⇒ 满足"0 命中"才复制进仓库。')

TAIL = '\r\n' + '\r\n'.join(FREQ_ROWS) + '\r\n' + LEDGER + '\r\n'
new_frq = FRQ_T + TAIL
FLN1 = len(new_frq.split('\r\n')) - 1
FE1 = len([l for l in new_frq.split('\r\n') if l.startswith('[错误类型]')])
assert FE1 == FE0 + N_NEW, 'ABORT: 写盘前条数等式不成立'
assert FLN1 - FLN0 == len(FREQ_ROWS) + 2, 'ABORT: 写盘前行增量现算 ' + str(FLN1 - FLN0)

DOC_NEW = DOC_T + '\r\n' + '\r\n'.join(SEC) + '\r\n'
DOCL1 = len(DOC_NEW.split('\r\n')) - 1
assert DOC_NEW.startswith(DOC_T) and new_frq.startswith(FRQ_T), 'ABORT: 前缀等式不成立，本遍不是纯追加'
assert DOCL1 - DOCL0 == DOC_SEC_LN + 1, 'ABORT: 排查记录行增量现算 ' + str(DOCL1 - DOCL0)

_payload = '\n'.join(SEC) + '\n'.join(GSEC) + ''.join(FREQ_ROWS) + LEDGER
for _s in ('%s', '%d', '@@', '{N}', 'PLACEHOLDER', 'TODO'):
    assert _s not in _payload, 'ABORT: 本遍新落正文含未替换哨兵 ' + _s
assert secret.decode() not in _payload, 'ABORT: 明文进了正文'
for _ln in _payload.split('\n'):
    assert chr(92) not in _ln or 'r58_preflash_8mb' in _ln, 'ABORT: 正文出现计划外反斜杠：' + _ln[:70]

# ================= 写盘：先日志副本 -> 三本文 -> 载体最后 =================
open(LOGDST, 'wb').write(LB)
lg = rb(LOGDST)
assert lg == LB and lg.count(secret) == 0, 'ABORT: 复制进仓库的那只日志字节不等或含明文'

open(FREQ, 'w', encoding='utf-8', newline='').write(new_frq)
open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
open(GUIDE, 'w', encoding='utf-8', newline='').write(GUIDE_NEW)

fb, db2, gb = rd(FREQ), rd(DOC), rd(GUIDE)
assert fb == new_frq and db2 == DOC_NEW and gb == GUIDE_NEW, 'ABORT: 回读与内存串不等'
assert fb.count('\n') == fb.count('\r\n') and db2.count('\n') == db2.count('\r\n'), 'ABORT: 写后不再是纯 CRLF'
assert gb.count('\r') == 0, 'ABORT: 烧录须知写后混进 CR'
N_TOTAL = len([l for l in fb.split('\r\n') if l.startswith('[错误类型]')])
L_TOTAL = len(fb.split('\r\n')) - 1
DOC_LN = len(db2.split('\r\n')) - 1
GUIDE_LN = len(gb.split('\n')) - 1
assert N_TOTAL == FE1 and L_TOTAL == FLN1, 'ABORT: 写后现数与写前算式不等'
assert DOC_LN == DOCL0 + DOC_SEC_LN + 1 and GUIDE_LN == GL1, 'ABORT: 写后行号与写前算式不等'
assert re.search(r'(?m)^### 38\.29 ', db2), 'ABORT: 写后读不到 §38.29 标题'
assert db2.count('### 38.29') == 1, 'ABORT: §38.29 出现不止一次 ⇒ 落重了'
S1, T1 = fold_a_(SYNC), fold_b_(SYNC)
assert S1[:2] == S0[:2], 'ABORT: 本遍动过 hardware/ht305_sync/ 的文件数或字节量'
assert open(DUMP, 'rb') and mdb(rb(DUMP)) == D_MD5 and mdb(rb(PPT)) == mdb(PB), 'ABORT: 原厂件被动过 ⇒ 用户资料红线破了'

_vm = subprocess.run((sys.executable, VMRUN), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=' + str(_vm.returncode)
VM_C = _mc.group(1).replace('\\', '/').split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_C)).split('\n') if l.startswith('INNER_ROWS=')]
assert INNER, 'ABORT: 内层载体里读不到 INNER_ROWS'

with open(CARRY, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R58 正文遍  MODE=FACTORY-SURVEY-LAND  本遍进入时刻 _T0 = ' + AT + '（_T0 取在任何产证动作之前）\n')
    f.write('DUMP 原厂整片件：' + os.path.basename(DUMP) + ' = ' + money(D_SIZE) + ' B / md5 ' + D_MD5 + ' / sha256[:16] ' + D_SH[:16] +
            ' / 非FF ' + money(D_NONFF) + ' 字节；分区表小件 = ' + money(len(PB)) + ' B / md5 ' + mdb(PB) + ' == 整片件 0x8000 处 3,072 B（逐字 assert）\n')
    f.write('PT 现读 3 只：' + PT_TXT + '；factory 跨度 0x%X；对照臂 3.97 原厂件分区合计 0x%X > 0x800000 ⇒ 16 MB 目标，刷不进本片\n' % (APP_SIZE, V397_SPANS))
    f.write('AXP 两臂同尺：' + AXP_TXT + '（原厂件 axp* 全 0、3.97 那只 >0 ⇒ 两臂不同值，对照有效）\n')
    f.write('LOG 120s：' + money(LOG_SIZE) + ' B / md5 ' + LOG_MD5 + ' / 非空行 ' + str(LOG_LN) + '；引文逐字现读并 assert 唯一命中 '
            '10 只（Project name / i2c / shtc3 / in_out / cal MAC / SPI Flash Size / flash warn / Returned from app_main / LVGL tick / sdmmc）\n')
    f.write('GPIO 普查现读 ' + str(GPIO_N) + ' 行 / ' + str(len(GPIO_UNI)) + ' 只：' + '/'.join(str(p) for p in GPIO_UNI) +
            '；输出组 ' + '/'.join(str(p) for p in sorted(OUTP)) + '；输入组 ' + '/'.join(str(p) for p in sorted(INP)) +
            '；SPI 组 ' + '/'.join(str(p) for p in sorted(SPI_GROUP)) + '（我方在册 SCLK/MOSI/CS/DC/RST/BUSY = ' + '/'.join(str(OP[k]) for k in ('SCLK', 'MOSI', 'CS', 'DC', 'RST', 'BUSY')) + '）\n')
    f.write('SOURCE 我方六根的来源链：3.97 官方 epaper_port.h 现读 EPD_*_PIN 六只 = 11/12/10/9/46/3（与我方 epd_driver.c:16-21 逐只相同；本遍第一版把出处写成 epaper_port.c，被这道门当场点红）⇒ 移植是忠实的，错在板型不是移植\n')
    f.write('FLASH 引文（从会话记录现 grep 并 assert 存在）：cmd 含 "' + QT_CMD.decode() + '"；"' + QT_WROTE.decode() + '"；"' + QT_HASH.decode() + '"\n')
    f.write('ROLLBACK 三件套：快照 %TEMP%\\r58_preflash_8mb.bin = ' + money(S_SIZE) + ' B / md5 ' + S_MD5 + ' / 非FF ' + money(S_NONFF) +
            '（其 0x8000 处分区表 == 我方构建目录那只，assert 过）；我方待烧 ' + OUR_MD5 + '（r53 那根备份现读逐字相同 = ' + R53ROOT + '）；上一代在板归档件 ' + ARC_MD5 + '\n')
    f.write('GATE 明文闸：PROV_PASS 长度现读 ' + str(len(secret)) + ' 字符（值不落纸）；120s 日志 HITS=' + str(LOG_HITS) +
            '；阳性对照只在内存（45 B 一只脏样本）命中 ' + str(POSCTL) + ' ⇒ 0 命中才复制，本遍已复制进 ' + os.path.basename(LOGDST) + '（回读逐字等 + 再验 HITS=0）\n')
    f.write('SEAL 写盘前 FOLD-A=' + SEAL_A + ' / FOLD-B=' + SEAL_B + '；写盘后复跑公共量等式 assert 通过（未动归档目录）；阳性对照 PROBE=' + PROBE + ' 两尺异值 FIRED=2\n')
    f.write('INNER 内层复核器 rc=' + str(_vm.returncode) + ' 载体 hardware/' + VM_C + '：' + INNER[0].strip() + '\n')
    f.write('FREQ 写前 ' + str(FE0) + ' 条 / ' + str(FLN0) + ' 行 -> 本批 +' + str(N_NEW) + ' 条 / +' + str(len(FREQ_ROWS)) + ' 正文行 + glue + 台账 -> 写后现数 **' + str(N_TOTAL) + ' 条 / ' + str(L_TOTAL) + ' 行**\n')
    f.write('DOC 写前 ' + str(DOCL0) + ' 行 -> §38.29 追加 ' + str(DOC_SEC_LN) + ' 行 + glue -> 写后现数 ' + str(DOC_LN) + ' 行；§38.29 标题现读 1 只\n')
    f.write('GUIDE 写前 ' + str(GL0) + ' 行 -> 〇-补4 插入 ' + str(len(GSEC)) + ' 行（在 ## 一、 之前）-> 写后现数 ' + str(GUIDE_LN) + ' 行；纯 LF 复验 CR=0\n')
    f.write('现场态：rev-list=' + REV + ' / HEAD=' + HEAD + ' / status --porcelain = ' + str(ST_M) + ' M + ' + str(ST_Q) + ' ?? = ' + str(len(ST)) +
            ' 行；板上那只 = 原厂 ' + D_MD5[:8] + '…，待烧 = 我方 ' + OUR_MD5[:8] + '… ⇒ "待烧 = 板上"本遍第二次断裂（方向相反）\n')
    f.write('NOTDONE 没换电池 / 没万用表 / 没第二块板 / 未改 main/ 一字节 / 未重建我方固件 / 未做 47-48 全地址扫描 / 未判 EPD 引脚 / 屏亮肉眼确认 0 次 ⇒ 不播提示音 / '
            '未新建备份根 / 未新建清单代次 / 未 push / 未 amend / 两只原厂 .bin 与含凭据镜像永不 stage / %TEMP% 快照与原件不搬走不删 / 零删除\n')

print('VERDICT=R58_LAND_OK rc=0 载体=hardware/' + os.path.basename(CARRY))
print('FREQ ' + str(FE0) + ' -> ' + str(N_TOTAL) + ' 条 / ' + str(L_TOTAL) + ' 行')
print('DOC ' + str(DOCL0) + ' -> ' + str(DOC_LN) + ' 行（§38.29）  GUIDE ' + str(GL0) + ' -> ' + str(GUIDE_LN) + ' 行（〇-补4）')
print('LOGCOPY ' + os.path.basename(LOGDST) + ' ' + money(os.path.getsize(LOGDST)) + ' B HITS=' + str(LOG_HITS) + ' POSCTL=' + str(POSCTL))
print('SEAL FOLD-A ' + SEAL_A)
