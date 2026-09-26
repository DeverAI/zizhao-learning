# R57 F 臂取证器：COM14 本遍现读**在位**（E 臂之后第一次），抓住这个窗口跑一格从未跑过的实验 ——
#   复位起抓 1000s，跨过固件里那条 boot_idle_sec = 900s 的深睡边界，看两件事：
#   ①板子到点是否真的 esp_deep_sleep_start()（盘上日志停在哪一秒、之后端口还在不在）；
#   ②§38.13 那两行判据（panel silent / panel blanked / witness）在 1000s 窗口里到底出不出得来（历代 10 只样本全为 0 行）。
# 为什么值得单独跑：`串口消失 = 深睡` 这条自 R33 起一直在被引用，但**从来没有一次现场观测**，
#   R53~R56 那几段"COM14 缺席"到底算深睡还是算线被拔了，靠的就是这条未验证假设 ⇒ 本臂要么给它第一个正样本，要么把它证伪。
# 红线（沿用既有口径）：只读串口，不烧录、不改源码、不重建；抓回件必须抄进仓库（临时目录里的东西不算取证）；
#   载体由脚本自己在同一次运行里落盘；写盘一律在 hardware/ht305_sync/ 之外（gen 24 是末版）；
#   载体正文不写反斜杠；口令明文只从 provision_ap.c 的宏体读出做命中计数，绝不打印、绝不进载体正文。
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

_T0 = time.time()
RUN_AT = datetime.fromtimestamp(_T0).strftime('%Y-%m-%d %H:%M:%S')

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HDIR = HERE
SYNC = os.path.join(HDIR, 'ht305_sync')
PORT = 'COM14'
SEC = 1000
IDF_PY = 'C:/Users/david/.espressif/python_env/idf5.1_py3.11_env/Scripts/python.exe'
TMPLOG = os.path.join(os.environ.get('TEMP', ''), 'r57_F臂_复位起抓1000s_跨900s深睡边界.log')
DSTLOG = os.path.join(HDIR, '20260925_R57_F臂复位起抓1000s跨900s深睡边界.log')
CARRIER = os.path.join(HDIR, '20260925_R57_F臂判据摘录.txt')
CAR_E2 = os.path.join(HDIR, '20260925_R57_E臂判据摘录_v2.txt')
MACRO = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'provision_ap.c')
PWRP = os.path.join(HDIR, 'zizhao-esp32s3', 'main', 'power_policy.c')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'

for _p in (IDF_PY, CAR_E2, MACRO, PWRP, BIN, SYNC):
    assert os.path.exists(_p), 'ABORT: 缺件 ' + _p
assert not os.path.exists(TMPLOG), 'ABORT: 临时目录槽位非空，不覆写 ' + TMPLOG
assert not os.path.exists(DSTLOG), 'ABORT: 仓库日志槽位非空，不覆写'
assert not os.path.exists(CARRIER), 'ABORT: 载体槽位非空，不覆写'

import serial
from serial.tools import list_ports


def ports():
    return sorted([x.device for x in list_ports.comports() if x.device.startswith('COM')])


P0 = ports()
assert PORT in P0, 'ABORT: 进入时 ' + PORT + ' 不在，本臂不成立（列口 = ' + ', '.join(P0) + '）'

# ---- 复位（esptool read_mac 是只读动作，退出时 --after hard_reset 把板子放回运行态）
_rp = subprocess.run([IDF_PY, '-m', 'esptool', '--chip', 'esp32s3', '-p', PORT, '-b', '115200',
                      '--before', 'default_reset', '--after', 'hard_reset', 'read_mac'],
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
RESET_RC = _rp.returncode
RESET_OUT = _rp.stdout.decode('utf-8', 'replace')
MAC = re.search(r'MAC: ([0-9a-f:]{17})', RESET_OUT)
assert RESET_RC == 0 and MAC, 'ABORT: 复位那步没成 rc=' + str(RESET_RC) + ' ⇒ 抓到的不是复位起抓'
RESET_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# ---- 抓：边读边写（崩在半路也留下已读的字节，不制造"跑了但没产物"）
sp = None
for _i in range(60):
    try:
        sp = serial.Serial(PORT, 115200, timeout=0.2)
        break
    except Exception:
        sp = None
        time.sleep(0.08)
assert sp is not None, 'ABORT: 复位后端口打不开（试了 60 次）'
_f = open(TMPLOG, 'wb')
_sw = time.time()
_tail = b''
while time.time() - _sw < SEC:
    try:
        b = sp.read(4096)
    except Exception:
        break
    if b:
        _f.write(b)
        _f.flush()
        _tail = (_tail + b)[-4096:]
    else:
        time.sleep(0.01)
CAP_END = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
CAP_SECS = round(time.time() - _sw, 3)
try:
    sp.close()
except Exception:
    pass
_f.close()
assert os.path.getsize(TMPLOG) > 0, 'ABORT: 一只字节都没抓到'

# ---- 端口在位性：抓完立刻再列一次（这一格是本臂的主判决之一）
P1 = ports()
PORT_AFTER = PORT in P1

# ---- 抄进仓库 + 两侧对表
shutil.copyfile(TMPLOG, DSTLOG)
_a = open(TMPLOG, 'rb').read()
_b = open(DSTLOG, 'rb').read()
assert _a == _b, 'ABORT: 仓库件与临时目录件不逐字相等'
md5 = hashlib.md5(_b).hexdigest()


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


ANSI = re.compile(r'\x1b\[[0-9;]*m')
TXT = ANSI.sub('', _b.decode('utf-8', 'replace'))
ROWS_L = TXT.splitlines()
UP = [int(m.group(1)) for m in re.finditer(r'[IWEF] \((\d+)\)', TXT)]
PRB = [int(m.group(1)) for m in re.finditer(r'probe#(\d+)', TXT)]
AXP34 = len([l for l in ROWS_L if 'AXP@0x34' in l])
ACKED = len([l for l in ROWS_L if 'acked:' in l and 'acked:[none]' not in l])
BUS = re.findall(r'bus scan 0x08-0x77: ACK=(\d+) NACK=(\d+)', TXT)
PWR = sorted(set(re.findall(r'PWR_OUT pu=(-?\d) pd=(-?\d)', TXT)))
BANNER = TXT.count('ESP-ROM')
MARK = {'复位原因(USB_UART)': TXT.count('rst:0x15'),
        'login ok': TXT.count('login ok'),
        'board MAC': TXT.count('board MAC'),
        'clock page': TXT.count('clock page'),
        'panel silent': TXT.count('panel silent'),
        'panel blanked': TXT.count('panel blanked'),
        'witness': TXT.count('witness'),
        'low_no_high': TXT.count('low_no_high'),
        'Deep sleep': TXT.count('Deep sleep'),
        '按时关机': TXT.count('按时关机'),
        '请现场配网': TXT.count('请现场配网'),
        '配网分支字样': TXT.count('softap') + TXT.count('AP ') + TXT.count('provision')}
# 最后一条带 uptime 的行 = 板子安静下来之前最后一句话（深睡判据的落点）
LASTLINE = [l for l in ROWS_L if l.strip()][-1][:220] if any(l.strip() for l in ROWS_L) else ''
LAST_UP = max(UP) if UP else -1
GAP_TAIL = round(CAP_SECS - LAST_UP / 1000.0, 3) if UP else -1.0

_secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(MACRO))
assert _secret, 'ABORT: 读不到 PROV_PASS 宏'
secret = _secret.group(1)
HITS = TXT.count(secret)
assert secret not in rd(PWRP)
# 末行照抄进载体前先按口径就地略去明文与反斜杠（略去这个动作本身在载体里点名，不假装它没发生）
LASTLINE_SAFE = LASTLINE.replace(secret, '<口令略>').replace(chr(92), '<反斜杠略>')

# 屏侧分母换代（现算，不抄 E 臂那句）
LOGS = sorted([f for f in os.listdir(HDIR) if f.endswith('.log')])
OFFICIAL = [f for f in LOGS if '官方' in f or '例程' in f]
OURS = len(LOGS) - len(OFFICIAL)

BOOT16 = re.search(r'ELF 指纹 = ([0-9a-f]{16})', rd(CAR_E2)).group(1)
BIN16 = open(BIN, 'rb').read()[176:184].hex()
BIN_MD5 = hashlib.md5(open(BIN, 'rb').read()).hexdigest()


def fold(d):
    files = []
    for root, _dirs, names in os.walk(d):
        for n in names:
            files.append(os.path.join(root, n))
    h = hashlib.md5()
    tot = 0
    for f in sorted(files):
        bb = open(f, 'rb').read()
        tot += len(bb)
        h.update(hashlib.md5(bb).hexdigest().encode('ascii'))
    return len(files), tot, h.hexdigest()


S0 = fold(SYNC)

ROWS = []
ROWS.append('R57 F 臂取证器（跨 900s 深睡边界）  MODE=CAPTURE-1000s')
ROWS.append('本遍现跑于 ' + RUN_AT + '；复位那步 ' + RESET_AT + '（rc=' + str(RESET_RC) + '，esptool read_mac = 只读动作 + hard_reset）；抓取窗口 = ' +
            str(CAP_SECS) + ' s，结束于 ' + CAP_END)
ROWS.append('PORT 进入前列口 = ' + ', '.join(P0) + ' ⇒ ' + PORT + ' 在位 = True；抓完立刻再列 = ' + ', '.join(P1) + ' ⇒ 端口仍在线 = ' + str(PORT_AFTER) +
            '（这一格是本臂主判决之一：板子若真进了深睡，原生 USB 会从总线消失）')
ROWS.append('COPY 原件 = 临时目录那只（引用名 r57_F臂_复位起抓1000s_跨900s深睡边界.log）/ ' + str(len(_b)) + ' B / md5 ' + md5)
ROWS.append('COPY 仓库件 = hardware/20260925_R57_F臂复位起抓1000s跨900s深睡边界.log / ' + str(len(_b)) + ' B / md5 ' + md5 + '；两侧逐字相等 = True')
ROWS.append('MAC 复位那步现读 = ' + (MAC.group(1) if MAC else '') + '（两块同款板靠它自证身份，不看 COM 号）')
ROWS.append('READINGS 原始 ' + str(len(_b)) + ' B / ' + str(len(ROWS_L)) + ' 行 / ROM banner ' + str(BANNER) + ' 次 / probe# 计数 ' + str(len(PRB)) +
            ' 次（1~' + str(max(PRB) if PRB else 0) + '）/ AXP@0x34 行 ' + str(AXP34) + ' 条，其中应答 ' + str(ACKED) + ' 条 / 全总线路扫读数 ' + str(BUS) +
            ' / PWR_OUT 组合 ' + str(PWR))
ROWS.append('READINGS uptime 跨度 = ' + str(min(UP)) + '~' + str(LAST_UP) + ' ms；最后一条非空行（截 220 字符，其中口令明文与反斜杠已按口径就地略去 = ' +
            str(LASTLINE_SAFE != LASTLINE) + '）= ' + LASTLINE_SAFE)
ROWS.append('SLEEP 深睡边界判决：boot_idle_sec 从 main/power_policy.c 现读 = ' + re.search(r'boot_idle_sec = (\d+)', rd(PWRP)).group(1) + ' s；' +
            '抓取窗口 ' + str(CAP_SECS) + ' s；最后一条日志的 uptime = ' + str(LAST_UP) + ' ms ⇒ 若端口消失且日志在 900s 后停住，本臂给出**第一个正样本**；' +
            '否则点名"到点没睡"。尾部静默 = ' + str(GAP_TAIL) + ' s（窗口长度减最后一条 uptime）')
ROWS.append('MARK 分支标记逐格计数 = ' + ' / '.join([k + '=' + str(v) for k, v in MARK.items()]))
ROWS.append('GATE §38.13 那两行判据本臂样本数 = panel silent ' + str(MARK['panel silent']) + ' 行 / panel blanked ' + str(MARK['panel blanked']) +
            ' 行 / witness ' + str(MARK['witness']) + ' 行（历代 10 只样本这三格全为 0 行 ⇒ 出得来就是换代，出不来就照旧点名）')
ROWS.append('DENOM 屏侧分母现算换代：hardware/ 单层 *.log = ' + str(len(LOGS)) + ' 只 / 官方例程对照 ' + str(len(OFFICIAL)) + ' 只不进分母 / 我方 = ' +
            str(OURS) + ' 只（上一格在册 ' + re.search(r'我方 = ([0-9]+) 只', rd(CAR_E2)).group(1) + ' 只）')
ROWS.append('IDENTITY 板上那只现算：boot ELF 前 16 位（E 臂在册）= ' + BOOT16 + ' / 当前 build 产物 bin[176:184] = ' + BIN16 + ' ⇒ 同一种 = ' +
            str(BOOT16 == BIN16) + '；build 产物 md5 = ' + BIN_MD5 + '（32 个十六进制字符 = md5，不是 sha256）')
ROWS.append('PLAIN 明文半径（口令只从 main/provision_ap.c 的宏体读出做计数，不打印、不进本载体正文）：本臂入库件命中 ' + str(HITS) +
            ' 处 ⇒ 命中 > 0 就照旧**不 stage、不 push、不删**')
ROWS.append('SEAL 写盘前 hardware/ht305_sync/ = ' + str(S0[0]) + ' 只 / ' + str(S0[1]) + ' B / 聚合 md5 ' + S0[2] + '（本批未新建清单代次，gen 24 仍是末版）')
ROWS.append('NOTDONE 本臂没做（点名）：没烧录 / 没改 main/ 源码 / 没重建固件 / 没换电池 / 没万用表 / 没第二块板 / 没往 hardware/ht305_sync/ 落一字节 / ' +
            '没新建备份根 / 没 push、没 amend / %TEMP% 原件不搬走不删 / 屏亮肉眼确认仍待用户回报 ⇒ 未确认就不播提示音')
body = '\n'.join(ROWS) + '\n'
assert secret not in body and chr(92) not in body, 'ABORT: 载体正文含明文或反斜杠'
open(CARRIER, 'w', encoding='utf-8', newline='').write(body)
_c = rd(CARRIER)
assert _c == body and '\r' not in _c, 'ABORT: 载体回读不等或非纯 LF'
S1 = fold(SYNC)
assert S0 == S1, 'ABORT: 归档目录被动过'

print('CARRIER hardware/20260925_R57_F臂判据摘录.txt', len(_c.rstrip('\n').split('\n')), 'rows', os.path.getsize(CARRIER), 'B')
print('LOG', len(_b), 'B md5', md5)
print('PORT_AFTER', PORT_AFTER, 'CAP_SECS', CAP_SECS, 'LAST_UP', LAST_UP, 'GAP_TAIL', GAP_TAIL)
print('PROBE', len(PRB), 'AXP34', AXP34, 'ACKED', ACKED, 'PS', MARK['panel silent'], 'PB', MARK['panel blanked'], 'WI', MARK['witness'])
print('SEAL', S1[0], S1[1], S1[2])
