# R56 真机首烧批（四臂判据落地）的收口落地器：一次调用落 2 只 CRLF 文档 + 1 只 LF 载体
#   ① hardware/20260919_墨水屏点屏排查记录.md（CRLF）—— 新增 §38.23（含两条订正行）
#   ② FreqErr.md（CRLF）—— 本批 5 条新错误类型 + 台账行（两把尺在最终串上现算，(99)）
#   ③ hardware/r56_paperwork2.txt（LF，载体，本脚本自己落盘，在归档目录之外）
# 引用口径：本批四臂的每一个数都**从取证载体逐字解析**（`..._判据摘录_v2.txt`）并回核盘上 md5，不重打字面量；
#   那两处行号 + 一处节号由本脚本在**改前正文**上独立再查一遍，与生成器各查各的，两遍同值才算过
#   （为什么必须是"改前正文"：本批正文自己会引用这些串，拿全文件查锚点就会命中 2 处 = 自指，R42 那一族）。
# 幂等：`### 38.23` 已在盘上 ⇒ MODE=REWROTE_CARRIER_ONLY，一字节都不写那两只 CRLF 文件。
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
MAN = os.path.join(SYNC, 'MANIFEST.txt')
GLOG = os.path.join(SYNC, 'evidence', 'manifest_gen_log.txt')
SNOTE = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs', 'SNAPSHOT_NOTE.txt')
P1 = os.path.join(HDIR, 'r56_paperwork1.py')
EV = os.path.join(HDIR, '20260924_R56真机首烧fb32168a判据摘录_v2.txt')
TOFLASH = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
BIN_R43 = os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin')
BIN_R53 = os.path.join(HDIR, 'zizhao-esp32s3', 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin')

TS = '[0-9-]{10} [0-9:]{8}'
SEC = '### 38.23'
SECNUM = '38.23'
SEC22 = '### 38.22'
FSEC = '## 2026-09-24（R56 第二批'
NOW_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
N_ENTRY = 5

_cands = ['r56_paperwork2.txt'] + ['r56_paperwork2_%d.txt' % i for i in range(2, 60)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 %d 只全被占，拒绝覆写' % len(_cands)


def money(x):
    return format(x, ',')


def rd(p):
    return open(p, encoding='utf-8').read()


def lf(t):
    return t.replace('\r\n', '\n')


def crlf(t):
    return lf(t).replace('\n', '\r\n')


def crlf_pure(p):
    b = open(p, 'rb').read()
    return b.count(b'\r\n') == b.count(b'\n')


def kinds(t):
    return len([l for l in lf(t).split('\n') if l.startswith('[错误类型]')])


def nl(t):
    return lf(t).count('\n')


def starts(text, anchor):
    return [i for i, l in enumerate(lf(text).split('\n')) if l.startswith(anchor)]


def md5_8(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]


def md5_(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


# ---------- 进入时现读两只 CRLF 文件 + 幂等闸（锚点必须在**改前正文**上查，见文件头） ----------
for p in (FREQ, DOC):
    assert crlf_pure(p), 'ABORT: %s 不是纯 CRLF ⇒ 追加会造出混行尾' % p
freq_disk, doc_disk = rd(FREQ), rd(DOC)
_hf, _hd = starts(freq_disk, FSEC), starts(doc_disk, SEC)
assert len(_hf) <= 1 and len(_hd) <= 1, 'ABORT: 本批标题命中 %d / %d 处 ⇒ 已重复追加' % (len(_hf), len(_hd))
MODE = 'REWROTE_CARRIER_ONLY' if _hf or _hd else 'LANDED_NOW'
assert bool(_hf) == bool(_hd), 'ABORT: §38.23 与本批 FreqErr 节"存在性"不一致 ⇒ 上一遍落了一半'
_fl = lf(freq_disk).split('\n')
if MODE == 'REWROTE_CARRIER_ONLY':
    _led = [i for i, l in enumerate(_fl) if l.startswith('> **【') and '落地｜R56 第二批 %d 条】**' % N_ENTRY in l]
    assert len(_led) == 1 and _led[0] > _hf[0], 'ABORT: 本批台账行命中 %d 只 / 不在本批标题之下 ⇒ 反推不了"改前"'
    freq_pre = '\n'.join(_fl[:_hf[0]]).rstrip('\n') + '\n'
    doc_pre = '\n'.join(lf(doc_disk).split('\n')[:_hd[0]]).rstrip('\n') + '\n'
else:
    freq_pre, doc_pre = freq_disk, doc_disk
K0, L0 = kinds(freq_pre), nl(freq_pre)
DOC_ROWS0, DOC_B0 = nl(doc_pre), len(doc_pre.encode('utf-8'))
GLUE_F = GLUE_D = TAIL_KF = TAIL_D = None
_rec = lf(doc_pre).split('\n')          # = 改前正文；它同时是盘上正文的逐字前缀，所以行号与全文件一致
assert '\n'.join(_rec) and doc_disk.replace('\r\n', '\n').startswith('\n'.join(_rec)), \
    'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 反推失败，锚点行号无从解释'


def anchor(s):
    hits = [i + 1 for i, l in enumerate(_rec) if s in l]
    assert len(hits) == 1, 'ABORT: 锚点 %r 在改前正文里命中 %d 处（%s）⇒ 指针不唯一' % (s, len(hits), hits)
    return hits[0]


# ---------- 取证载体：本批所有四臂读数从这里逐字解析（载体不在 ⇒ 本脚本无从落地） ----------
assert os.path.isfile(EV), 'ABORT: 取证载体不在 %s ⇒ 四臂的数没地方取，不许凭记忆打字面量' % EV
ev = rd(EV)
EV_LINES = ev.split('\n')
EV_AT = re.search(r'^生成时刻 (' + TS + ')', ev, re.M).group(1)
EV_VERDICT = [l for l in EV_LINES if l.startswith('VERDICT=')][-1]
assert EV_VERDICT.startswith('VERDICT=FOUR-ARMS-ALL-NACK'), 'ABORT: 载体裁决不是四臂全 NACK：%s' % EV_VERDICT

ARMS = {}
for _i, _l in enumerate(EV_LINES):
    _m = re.match(r'^([ABCD]) (.+)$', _l)
    if _m and _m.group(2).startswith(('旧镜像', '新镜像')):
        k = _m.group(1)
        car = re.search(r'载体=(\S+) / (\d+) B / md5=([0-9a-f]{32})', EV_LINES[_i + 1])
        up = re.search(r'uptime (\d+) 至 (\d+) ms / probe#(\d+) 至 probe#(\d+) 共 (\d+) 条 0x34 行：no reply=(\d+) 应答=(\d+)',
                       EV_LINES[_i + 2])
        assert car and up, 'ABORT: 载体里 %s 臂的"载体/uptime"两行不再合式 ⇒ 解析器要跟着载体一起改，不能少读数' % k
        ARMS[k] = dict(title=_m.group(2), rel=car.group(1), size=int(car.group(2)), md5=car.group(3),
                       n=int(up.group(5)), noreply=int(up.group(6)), replies=int(up.group(7)),
                       banner=('ROM banner 1 次' in EV_LINES[_i + 1]))
assert set(ARMS) == set('ABCD'), 'ABORT: 载体里解析到 %s 臂，不是 A/B/C/D 四臂' % sorted(ARMS)
for k in 'ABCD':
    assert ARMS[k]['replies'] == 0 and ARMS[k]['noreply'] == ARMS[k]['n'], 'ABORT: %s 臂应答口径变了' % k
    _ap = os.path.join(REPO, ARMS[k]['rel'].replace('/', os.sep))
    assert os.path.isfile(_ap), 'ABORT: %s 臂在册载体 %s 不在盘上' % (k, ARMS[k]['rel'])
    assert md5_(_ap) == ARMS[k]['md5'], 'ABORT: %s 臂载体盘上 md5 与在册那行不等 ⇒ 取证件与被解读者已分叉' % k
ARM_N = sum(ARMS[k]['n'] for k in 'ABCD')
REPLIES = sum(ARMS[k]['replies'] for k in 'ABCD')
BOOTS = sum(1 for k in 'ABCD' if ARMS[k]['banner'])
FP_ONBOARD = sorted(set(re.findall(r'boot ELF 指纹=([0-9a-f]{16}) == bin\[176:184\]=\1 成立', ev)))
assert len(FP_ONBOARD) == 2, 'ABORT: 载体里 boot 指纹等式不是恰好 2 格（B 与 C）：%s' % FP_ONBOARD
D_LINE = [l for l in EV_LINES if l.startswith('D：')][0]
D_WIN = re.search(r'窗口 ([0-9:]{8}) 至 ([0-9:]{8})', D_LINE)
assert D_WIN, 'ABORT: 载体 D 行不再含"窗口 HH:MM:SS 至 HH:MM:SS" ⇒ 抓取窗口无从引用'

# ---------- 三处指针：本脚本独立再查一遍，与在册载体比对（两把量具同值才算过） ----------
L_PWRON = anchor('Key1→R26 510R→PWRON(30) 脚')
L_PWROUT = anchor('它是 AXP2101 的开机状态输出')
_NACK_LN = anchor('判读文本越权')
_NACK_SECT = re.match(r'#{2,4} +([0-9]+(?:\.[0-9]+)?)', _rec[_NACK_LN - 1]).group(1)
EV_CIT = re.findall(r'现读第 (\d+) 行', ev)
assert EV_CIT[:2] == [str(L_PWRON), str(L_PWROUT)], \
    'ABORT: 本遍独立查到的行号(%d,%d) 与取证载体在册的(%s) 不等 ⇒ 两把量具分叉' % (L_PWRON, L_PWROUT, ','.join(EV_CIT))
EV_SECT = re.search(r'现读 §([0-9.]+)（第 (\d+) 行标题）', ev)
assert EV_SECT and EV_SECT.groups() == (_NACK_SECT, str(_NACK_LN)), \
    'ABORT: 节号两遍不同值：载体在册 %s vs 本遍 (%s, %d)' % (EV_SECT.groups() if EV_SECT else None, _NACK_SECT, _NACK_LN)
FAKE_PTR_HITS = len([l for l in _rec if '§13-2' in l])
assert FAKE_PTR_HITS == 0, 'ABORT: v1 那句 `§13-2` 在改前排查记录里其实命中 %d 处 ⇒ 它不是假指针，本批第 3 条要重写' % FAKE_PTR_HITS

# ---------- 镜像身份：待烧（构建目录）↔ 归档 r53 ↔ 板上（boot 指纹在册于取证载体）三格等式 ----------
for p in (TOFLASH, BIN_R43, BIN_R53):
    assert os.path.isfile(p), 'ABORT: 指纹基准缺失 %s' % p
MD5_TF, MD5_R53, MD5_R43 = md5_(TOFLASH), md5_(BIN_R53), md5_(BIN_R43)
assert MD5_TF == MD5_R53, 'ABORT: 构建目录 bin 与归档 r53 那只不等（%s vs %s）⇒ (92) 收口第一格就不成立' % (MD5_TF, MD5_R53)
FP_TF = open(TOFLASH, 'rb').read()[176:184].hex()
ONBOARD_OK = FP_TF in FP_ONBOARD
assert ONBOARD_OK, 'ABORT: 板上 boot 指纹 %s 不含待烧现算值 %s ⇒ "待烧 = 板上"还没落地，本节不能写收口' % (FP_ONBOARD, FP_TF)

# ---------- 封界门 + 只在内存的阳性对照 ----------
_glog_last = [l for l in rd(GLOG).split('\n') if l.strip() and not l.startswith('#')][-1]
GEN_STAMP, GEN_TOTAL, GEN_BYTES, GEN_BOM = _glog_last.split('\t')
_dt = datetime.strptime('2026 ' + GEN_STAMP, '%Y %m-%d %H:%M:%S')
SEAL_AT = _dt.strftime('%Y-%m-%d %H:%M:%S')
SEAL_EPOCH = _dt.timestamp()
_rows = dict((p, int(n)) for p, n in re.findall(r'^([^\t]+)\t(\d+)\t[0-9a-f]{32}\t', rd(MAN), re.M))
_disk = []
for root, dirs, fs in os.walk(SYNC):
    dirs.sort()
    for f in sorted(fs):
        p = os.path.join(root, f)
        _disk.append((os.path.relpath(p, SYNC).replace(os.sep, '/'), os.path.getsize(p), os.path.getmtime(p)))
DISK_N, DISK_B = len(_disk), sum(n for _, n, _ in _disk)
_by = dict((p, (n, mt)) for p, n, mt in _disk)
NOT_LISTED = sorted(set(_by) - set(_rows))
assert DISK_N == len(_rows) + len(NOT_LISTED) and not (set(_rows) - set(_by)), 'ABORT: 封界算式不闭合'
EXCL = {'MANIFEST.txt', 'evidence/manifest_gen_log.txt'}


def seal_gate(extra=()):
    viol = sorted(p for p, (n, mt) in _by.items() if int(mt) > int(SEAL_EPOCH)) + sorted(extra)
    unnamed = sorted(p for p in NOT_LISTED if p not in EXCL)
    return (not viol and not unnamed and DISK_N - len(NOT_LISTED) == len(_rows)), viol, unnamed


ok_real, viol_real, unnamed_real = seal_gate()
assert ok_real, 'ABORT: 封界门本遍就红：%s / %s' % (viol_real, unnamed_real)
PROBE = 'evidence/SEAL_VIOLATION_PROBE2.txt'
ok_probe, viol_probe, _u2 = seal_gate((PROBE,))
assert not ok_probe, 'ABORT: 阳性对照没亮 ⇒ 这道门不可信'
ARMS_FIRED = 'ARMS_FIRED=%d/1' % (0 if ok_probe else 1)
assert not os.path.exists(os.path.join(SYNC, PROBE)), 'ABORT: 假名竟在盘上'

_v = subprocess.run([sys.executable, os.path.join(HDIR, 'vm_run.py')], cwd=REPO,
                    capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8='1'))
_vm_rows = [l for l in _v.stdout.split('\n') if l.startswith('VM_RC=')]
_vm_car = [l for l in _v.stdout.split('\n') if l.startswith('VM_CARRIER=')]
assert _v.returncode == 0 and _vm_rows and _vm_car, 'ABORT: vm_run 本遍没跑绿 rc=%d' % _v.returncode
VM_ROWS = _vm_rows[0].split(' / ')[1]
VM_VERDICT = _vm_rows[0].split(' / ')[2]
VM_CARRIER = _vm_car[0].split('=', 1)[1]

# ---------- 现场态 ----------
_rev = subprocess.run(['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
assert _rev.isdigit(), 'ABORT: rev-list 不是数字：' + _rev[:20]
_com = subprocess.run([sys.executable, '-c', 'import serial.tools.list_ports as L;'
                       'print(", ".join(p.device for p in L.comports()))'],
                      capture_output=True, text=True).stdout.strip()
# 本遍只读列口。板上那只镜像的身份**不由本遍列口决定**（它的取证在 @EV_AT@ 那一遍的 boot 指纹），
# 所以 COM14 在不在只登记、不断言 —— 断言它会等于"拿今天的口列表证明昨晚的烧录"。
COM14_NOW = 'COM14' in _com
COM14_TXT = '在场' if COM14_NOW else '缺席'

# 槽位池容量逐只现读：本批第 1 条登记的就是"没有一处登记过复跑预算"，所以那句"池已统一到 59 只"
# 必须由本遍从每只工具源码现读得出，而不是我抄自己上一遍说的话。
_POOL = {}
for _f in sorted(os.listdir(HDIR)):
    if not _f.endswith('.py'):
        continue
    _m = re.search(r"_cands = \[.*?range\(2, (\d+)\)", rd(os.path.join(HDIR, _f)))
    if _m:
        _POOL[_f] = int(_m.group(1)) - 1
assert len(_POOL) >= 5, 'ABORT: 池扫描只命中 %d 只工具 ⇒ "哪些工具有槽位池"这句话没有对象' % len(_POOL)
POOL_UNI = sorted(k for k, v in _POOL.items() if v == len(_cands))
POOL_OTHER = sorted('%s(%d)' % (k, v) for k, v in _POOL.items() if v != len(_cands))
assert len(POOL_UNI) >= 5, 'ABORT: 达到本批容量 %d 只的工具只有 %d 只 ⇒ 正文那句"统一到"不能成立' % (
    len(_cands), len(POOL_UNI))
_sn = rd(SNOTE).split('\n')
SNAPSHOT_AT = re.search(r'刷新时刻 (' + TS + ')', _sn[0]).group(1)
SNAPSHOT_ROWS = len([l for l in _sn if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
_log_all = sorted(f for f in os.listdir(HDIR) if f.endswith('.log'))
_log_official = [f for f in _log_all if '官方例程' in f]
LOG_OURS = [f for f in _log_all if f not in _log_official]
LOG_R56 = [f for f in LOG_OURS if f.startswith('20260924_R56')]
LOG_OLD = [f for f in LOG_OURS if f not in LOG_R56]
LOG_BOOT_OLD = sum(1 for f in LOG_OLD if 'ESP-ROM' in rd(os.path.join(HDIR, f)))

# ---------- 两处订正目标的原文：按内容现读、逐字插入 ----------
Q21_LN = anchor('载体名池也从 9 只扩到 19 只')
Q21 = _rec[Q21_LN - 1].strip()
Q22 = _rec[starts(doc_pre, SEC22)[0]]
assert Q21 and Q22.startswith(SEC22), 'ABORT: 两处订正目标的原文没取到'
_T22 = re.search(TS, Q22)
assert _T22, 'ABORT: §38.22 标题里不再含时刻 ⇒ "隔多久"无从现算'
GAP_MIN = int((datetime.strptime(EV_AT, '%Y-%m-%d %H:%M:%S')
               - datetime.strptime(_T22.group(0), '%Y-%m-%d %H:%M:%S')).total_seconds() // 60)
assert GAP_MIN > 0, 'ABORT: 取证时刻早于 §38.22 落地时刻（%d 分）⇒ 时间线自相矛盾' % GAP_MIN

# ---------- FreqErr 本批段（正文 5 条） ----------
FREQ_SEC = """@H@

> 一句话总纲：本批屏侧仍然一个像素没动（四臂合计 @ARM_N@ 条 `0x34` 行、应答 @REPLIES@ 条），
> 但抓到五条**跟硬件无关**的错：它们全在我自己的"引用与自述"这一层 —— 一条假节号，四条会被复跑、时间、口径变化打假的句式。

[错误类型] **给"复跑必新增一只"的载体名设固定槽位池 ⇒ 复跑次数一多，池子先被撑爆，而它染红的是**别人**的前向对照链（本批实测：归档内层复核器 `verify_manifest.py` 那 9 只槽位被历次复跑占满 ⇒ 它打印完裁决后 `rc=2` 拒写第 10 只，把第一批落地器当场判红；`r55_paperwork3.py` 等 4 只工具的 19 只池同样被撑满）**
→ 症状：判据本身**没变红**（清单仍 `MANIFEST_STILL_TRUE`），红的是"它跑绿了没有"这件事。一个纯命名/占位问题伪装成"归档被改动"级别的事故，而 §38.19 已禁掉"拿重跑链把 RED 洗成 GREEN"，所以我不能靠再跑一遍把它消掉。
→ 为什么它危险：这类池的容量隐含一个预算 =「这一代被复跑几次」，而**没有任何一处登记过这个预算**；于是下一次复跑必然踩，踩到的那一遍看起来是"新批次自己的错"。更糟的修法是把归档件的池改大 —— 那是亲手改 gen 24 封界里的执行件（`verify_manifest.py` 就在归档目录内）。
→ 正确做法：①撞到上限时报错点名候选只数（盘上现读：@POOL_N@ 只带槽位池的落地器已统一到 @POOL@ 只候选 = @POOL_UNI@；其余仍停在 @POOL_OTHER@ ⇒ 下一遍若要复跑它们，会先在这里看到容量而不是一句"名字全被占"）；②给复跑留**按时刻命名**的旁路而不改被归档件（本批 = `hardware/vm_run.py`，把内层 stdout + rc 逐字代落 `hardware/vm_run_<时刻>.txt`，归档目录零写入）；③"前向对照"那一步的 `rc` 与判据的 `rc` 分开登记，别把前者当后者。
→ **同族**：项目记忆 (76)"命中 0 ≠ 干净"、(80)-(82)"计数型安全门必须配阳性对照"；`feedback-verifiable-acceptance.md`"rc=0 必须蕴含产物已写出"（本条是它的反向：判据为真但产物写不出 ⇒ rc 非 0，红的是执行者不是判据）。

[错误类型] **在批次文档里写"本批没做 X"这种批级否定式自述 ⇒ 同批后续动作必然把它变成假话（本批实测：§38.22 的标题与"本节没做 ①"都写着"没烧录、没碰串口"，而它落盘 @GAP@ 分钟之后同一批的真机首烧就把 fb32168a 烧进了 COM14 并做完四臂抓取）**
→ 症状：句子写下那一刻它是**真**的，所以任何"落笔前复核"都救不了 —— 它不是事实错，是**量的是哪一遍**没说清。第一批的载体因此补了一只 `SCOPE-订正` 行，但那句在 CRLF 正文里仍在原位，引用者（包括未来的我）读标题就会读到假话。
→ 为什么它危险：否定式自述是"我做了什么/没做什么"的唯一入口。一旦它可被同批后续动作推翻，整套"没做什么（点名，不省略）"就从**保证**退化成**快照**；而快照必须带时刻，不带时刻的快照会被读成永久事实。
→ 正确做法：①自述绑定执行者：写"本遍（paperwork，@T@）没有串口动作"，不写"本批没做串口"；②同批已发生的动作必须在同一节点名在册物 + 它的生成时刻（本批见载体 `SELF-SCOPE-NOTE` 行）；③标题格里放了否定式，正文就要同时放一条"本批口径 = 分两半"的说明，并补一只订正行（本节就是那条订正落到 CRLF 正文里的版本）；④引用旧节时先读它的落地器载体，再读它的标题。
→ **同族**：项目记忆 (85)"提交信息不许有将来式锚点"、(88)"订正句本身也是断言载体"；`feedback-verifiable-acceptance.md`"'已跑完/已冻结'要带 rc + 载体名"。

[错误类型] **取证正文里的指针写成"第 N 行 / §X-Y"而不做锚点唯一性复核 ⇒ 行号随任何一次插入漂掉，节号可能是盘上根本不存在的串（本批实测：真机首烧取证件 v1 那句"按排查记录 §13-2 的分流口径"，在改前排查记录里命中 @FAKE@ 处 = 真·假指针，同族第 3 例；另两处行号 @L2@ / @L1@ 当时恰好仍真实，只因为插入点正好在它们之后）**
→ 症状：数字看着比文字可信，所以我当时没查它。假指针那句想指的其实是 §14.3"判读文本越权（全 NACK 说得太满）"，而盘上真存在的 §13.2 讲的是"长按 4 秒开机口径撤回" —— 同案相关但**不是**分流口径。
→ 为什么它危险：与 (64)/(88) 两族同形但方向不同：那两族是"引号里的话没出处"，这一族是"出处有格式、没内容"。`§13-2` 长得完全像合法节号（连格式被写错成 dash 都没被发现），任何格式检查都拦不住它，它只会误导下一次引用者。行号那一半更隐蔽：**它对的那一刻是真的**，于是"我当时 grep 过"成立，而结论仍然脆。
→ 正确做法：①指针由**生成器运行时现查**：锚点文本必须在被引文件里恰好 1 命中，否则拒绝生成（v2 载体就是这个形状，节号连标题行号一起印）；②落地器**独立再查一遍**并与在册载体比对（本批两把量具同值才算过，见载体 `CITE` 行）；③号旁注一句"本文件只对生成时刻的盘上状态负责"；④引节号必读那一节的**标题文字**，不许只看编号 —— R54 (97) 已立过一次，本批是同族第二次；⑤`§X-Y` 这种写法在本仓库里**一个都不存在**（节号一律 `X.Y`），所以它本身就是可疑信号。
→ **同族**：项目记忆 (97)"引节号要连那一节的内容一起核（假指针第 2 例）"、(64)"订正句里的假引文"；`feedback-verifiable-acceptance.md`"行号与比对结论也是取证口径"。

[错误类型] **在文件头部写"全部读数运行时现算、无手抄"这类**自证式元声明**，却不在落笔时与正文对账 ⇒ 声明本身成了该文件里第一条未经核对的断言（本批实测：v1 头部就这么写，而它的 D 臂抓取窗口、四臂条数、"5 个邻居""112 个地址""467/770 ms"全是手打字面量）**
→ 症状：这类句子是"给读者省事的承诺"，读者正因为信它才不复核 ⇒ 错一次就让整份取证件的可信度按**声明**而不是按**证据**结算；而它最难被动发现，因为被它罩住的每个数字单独看都对。
→ 为什么它危险：它与我这一代立的其他规矩**形式上完全一致**（都在要求"现算、别手抄"），差别只在它是**关于其他句子的句子** —— 元断言没有自己的取证行，除非我把它降格成可核范围。
→ 正确做法：①声明必须点名"哪几类字段"是现算的并**点名例外**（v2 头部改成：凡带"读数"二字的字段一律现算，非读数只有两类 —— 抓取手段那节的流程描述 = 操作记录、用户口述那一行 = 输入前提）；②能变成断言的就变成断言：本批把窗口时刻改为 TEMP 原件 ctime→mtime 现算、行号节号改为锚点现查、邻居名单/hold 时刻/地址数改为解析日志；③剩下真变不了的**逐类点名**，不许笼统说"全部"。
→ **同族**：项目记忆 (88)"订正句本身也是断言载体"、(95)"落地脚本三步序"；`feedback-verifiable-acceptance.md`"口径读数不得冒充语义构成"。

[错误类型] **台账里一个分母只有数、没有"怎么数出来的"⇒ 新批次无法安全地往上加（本批现算 `hardware/` 单层 = 我方 @LOG_OURS@ 只，与在册那格 "@OLD_LOG@ 只 / @OLD_BOOT@ 次上电" 怎么组合都对不上，即我复算不出它的构成）**
→ 症状：想登记"本批新增 @LOG_R56@ 只 ⇒ 分母换代"，落笔前必须先知道旧那格数的是哪些只。现跑结果：盘上 `hardware/*.log` = @LOG_ALL@ 只，去掉"官方例程"对照 @LOG_OFF@ 只 ⇒ 我方 @LOG_OURS@ 只，其中本批 @LOG_R56@ 只；三种组合法都拼不出 @OLD_LOG@。
→ 为什么它危险：分母是**结论的形状**（"屏侧 @OLD_BOOT@ 次上电仍全 NACK"这类话全靠它）。一旦它不可复算，后续每次引用都在把一个猜测当基准累加；而工具不会报警，因为没有任何检查是"两个数能不能互相解释"。
→ 正确做法：①分母登记必须同时登记**口径算式**（目录半径 + 排除名单 + "一次上电"的定义），本批起权威口径 = `hardware/` 单层 `*.log`、排除文件名含"官方例程"的对照件、"上电" = 该只文件内 ROM banner 命中数；②复算不出旧值构成 ⇒ **就地降级为不可复算的旧快照**并禁止在它上面做加法（本遍就是这样，见 §@SECNUM_DOTTED@ 与载体 `DENOM` 行）；③新分母由新算式现算，不与旧快照混写在同一句里。
→ **同族**：项目记忆 (89)"台账自己的序数计数不复算就就地降级"、(41)"报两侧不一致先读产生那个数的命令"；`feedback-verifiable-acceptance.md`"数字连算法与漏判"。
""".replace('@H@', FSEC + '：真机首烧四臂落地）新增 %d 条（根族：**硬件一个数没动，我这层的引用口径动了 5 处**）' % N_ENTRY)

# ---------- 排查记录 §38.23 ----------
SEC_BODY = """@SEC@ R56 真机首烧批 = (91) 那条根因**第一次被实测否证** + D 臂第一个真样本 + (92) 那条"待烧≠板上"就地收口（四臂抓取于 @EV_AT@；本遍 paperwork @T@；**本遍零串口动作，抓取发生在 @EV_AT@ 那一遍**）

- **本节登记什么**：COM14 第一次烧进新镜像 `fb32168a…`（= R53 那一步"补官方 `esp_gpio_Init` 同档的 GPIO1 拉住"的产物），并从四臂串口抓取判出三件事：①那一步**确实进了镜像并在跑**；②它**没能救回 0x34** ⇒ (91) 那条因果链被否证；③用户接上 USB + 锂电池、确认真按过电源键之后 PMIC 仍不宣布开机 ⇒ 但按 §@NACK_SECT@ 的口径**全 NACK 不定案**，所以只降级、不结案。屏侧进展本身仍是零：屏亮肉眼确认 @BLANK@ 次。
- **读数从哪来（引用即复跑）**：本节每个数都逐字取自取证载体 `hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt`（生成时刻 @EV_AT@，裁决 @EV_VERDICT@），而那只载体的读数由 `hardware/r56_flash1.py` 运行时现算。本遍落地器另做三件复核：把载体**重新解析一遍**并逐臂回核盘上 md5；把里面三处指针**独立再查一遍**并与在册值比对；把 §38.21 那句"扩到 19 只"与本遍池容量 @POOL@ 只对上账。
- **镜像身份三格等式（(92) 就地收口）**：待烧 = 构建目录那只的 **md5** `@MD5_TF@`（32 位 hex，非 sha256）；归档 = `hardware/zizhao-esp32s3/backups/r53_20260924_083929/` 那只的 md5 `@MD5_R53@`；板上 = 取证载体 B/C 两臂那行 `boot ELF 指纹=@FP_TF@ == bin[176:184]=@FP_TF@ 成立`（由 bin 现算，非转抄）。前两把尺逐字相等，第三把是 boot 行与 `bin[176:184]` 的关系式 ⇒ 从本批起「**待烧 = 板上 = fb32168a…**」成立，(92) 那条分裂（`fb32168a…` vs 板上 `4842a3a0…`）**就地收口**；旧镜像 `@MD5_R43@`（= `4842a3a0…`，R43 那只）降级为历史，它同时是 A/B 两臂的图。
- **四臂读数（本遍从载体解析：合计 @ARM_N@ 条 `0x34` 行，应答 @REPLIES@ 条，其中复位起抓（ROM banner 命中）@BOOTS@ 臂）**：
@ARM_ROWS@
- **判读 ①（否证，带范围）**：C 臂（新镜像，复位起抓 @C_N@ 条）里 hold-on 探针把 GPIO1 从"输入+上拉"升成"推挽输出高"之后，0x34 仍不应答、已知邻居全 NACK、整条总线 0x08-0x77 仍 0 应答 ⇒「GPIO1 没被拉住 ⇒ PMIC 没上电 ⇒ 全 NACK」这条链在**外部 5V 已接**的前提下不成立。**边界**：那一档是一次性短时推挽高，不等于"从上电第一秒起持续按住"，所以本条否证止于"补这一档没用"，**不含**"任何更长/更早的按住都没用"。方向也读反了：GPIO1 是 PMIC 的开机状态**输出**（改前排查记录现读第 @L_PWROUT@ 行），电源键走 `Key1→R26 510R→PWRON(30)`、**不接任何 GPIO**（现读第 @L_PWRON@ 行）⇒ 固件本来就模拟不了那次按下，所以 D 臂改用物理按键。
- **判读 ②（第一个真样本，不结案）**：D 臂 = USB + 锂电池都在位 + 按键确认真按过，窗口 @D_WIN@（现算自 `%TEMP%` 原件的 ctime→mtime；仓库内那只拷贝的这两个时刻已被拷贝动作重置）：@D_N@ 条 `0x34` 仍全 no reply，全程 PWR_OUT 对读只有 `pu=1 pd=0` 一种组合 = 这根脚始终悬空 = PMIC 从头到尾没宣布自己开机。按 §@NACK_SECT@（标题行 = 现读第 @_NACK_LN@ 行）**全 NACK 不定案** ⇒ 只能说"按键没把 PMIC 带进开机态（就这次按下而言）"。四条未分开：电池电压/座子接触、`Key1→PWRON` 那段网络（含 510R 虚焊）、PWR_OUT 脚号登记是否对、PMIC 本体。
- **判读 ③（口述那行的证据等级）**："按了，但板上没有任何反应" = 用户口述，本批当**输入前提**登记（D 臂靠它才成立），不当取证读数 —— 我方固件按图纸读不到按键，没有任何独立手段能证明那次按下的时长与落点。它在本节是承重墙，所以单独点名一次。
- **余下最便宜的物理分叉（我方软件侧已到尽头）**：a）换一块同型号板复跑同一条 C 臂判据（同 bin 比 `pull compare` 与 ACK 计数，一次烧录、不用仪器）；b）万用表两档：电池座两端电压、PWRON(30) 按下时的电平；c）a 与 b 都指回这块板，才谈"PMIC/主板级"结论。**⇒ 从本行起这两条是我方拿不出来的东西，要用户动手。**
- **分母口径换代 + 就地降级**：上一格在册"我方日志 @OLD_LOG@ 只 / @OLD_BOOT@ 次上电"本遍**复算不出构成** ⇒ 按本批 FreqErr 第 5 条降级为**不可复算的旧快照**，引用者不许在它上面做加法。新口径现算：`hardware/` 单层 `*.log` = @LOG_ALL@ 只，其中"官方例程"对照 @LOG_OFF@ 只不进分母 ⇒ 我方 @LOG_OURS@ 只，本批新增 @LOG_R56@ 只；本批之前的 @LOG_OLD@ 只里 ROM banner 命中 @LOG_BOOT_OLD@ 只。这条算式（目录半径 + 排除名单 + "一次上电"的定义）从本行起就是"屏侧进展分母"的权威口径。
- **两处订正（本遍按内容现读原文、逐字插入，不改写原句一字节）**：
  - §38.21 那句（改前正文现读第 @Q21_L@ 行，逐字）：`@Q21@` ⇒ 本批把它统一到 **@POOL@ 只候选**（本遍从每只工具源码现读容量：已达该容量的 @POOL_N@ 只 = @POOL_UNI@，未达的 = @POOL_OTHER@）；**并且**新报一处：归档内层复核器 `verify_manifest.py` 的 9 只槽位已被历次复跑占满 ⇒ 它打印完裁决后 `rc=2` 拒写第 10 只。归档件**不改**（那是 gen 24 封界本身），改由 `hardware/vm_run.py` 按时刻代落载体（本遍 = `@VM_CARRIER@`，`rc=0`）。
  - §38.22 的标题（现读逐字）：`@Q22@` ⇒ 其中"没烧录、没碰串口"量的是**写它的那一遍**（@T2@），不是整个 R56 批：它落盘 @GAP@ 分钟后同批的真机首烧就完成了烧录与四臂抓取，就是本节。引用 §38.22 时不许读成"R56 没烧录"。第一批载体的 `SCOPE-订正` 行已点过一次名，本行是它落到 CRLF 正文里的版本。
- **本节没做（点名，全部绑定执行者）**：①**本遍**（paperwork，@T@）零串口动作、零烧录 —— 只 `comports()` 只读列口 = `@COM@`，其中 COM14 **@COM14@**；"没开口"这一格本遍拿不出外部证据（只读列口是自述），按本批 FreqErr 第 2 条在此点名"无法证明"。COM14 @COM14@ 与上面"板上 = `fb32168a…`"那句**不矛盾**（那条等式的取证在 @EV_AT@ 那一遍的 boot 指纹与四臂日志，不在本遍的口列表），但它也**不等于**"线被拔了"：候选有两条 —— 深睡使原生 USB 从总线消失（项目记忆 `hardware-epd397-com-port-absence`）/ 真的断电或拔线，本遍只读列口，**没有手段把它们分开** ⇒ 此处只登记"缺席"这个读数，不定因；②没换电池、没用万用表、没接第二块板（= 上面 a/b 两条，我方拿不出）；③没改任何 `main/` 源码、没重建固件 ⇒ 板上就是 `@MD5_TF@` 这只，本批没有新的"待烧"要重冻；④没往 `hardware/ht305_sync/` 落一字节（SEAL 门 + 只在内存假名 `@PROBE@` 就是这条的执行者，本遍 @ARMS@），也没新建清单代次 ⇒ gen 24 仍是末版；⑤没 push、没 amend、零删除 —— **含 `%TEMP%` 里 D 臂那只原件**（它现在是抓取时刻的唯一权威，本批刻意不搬走、不删）；⑥提交轮 #9、docs 快照第十遍、backups README 第十次读数、第 14 代服务器同步都在本节之后 ⇒ 本遍不预写它们的数（docs 快照停在 @SNAP@，表格 @SRN@ 行）；⑦屏亮仍 0 次肉眼确认 ⇒ 本轮不播提示音。
> 本节对应 `FreqErr.md` 那 @N@ 条在册（标题前缀 `@FSEC@`），paperwork 载体 = `hardware/@CAR@`（本遍写的那一只：EV 解析行 + CITE 两遍同值行 + IDENTITY 三格等式行 + DENOM 分母行 + SEAL/GATE/VM/POSCTL/WINDOW/WITNESS/SELF-SCOPE-NOTE）。另：四臂原始取证件 = `hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt`（取代 v1；**v1 不删** —— 它那句假节号与那些手抄字面量就是本批 FreqErr 第 3、4 条的样本，删掉就没证据了）。
""".replace('@SEC@', SEC).replace('@T@', NOW_AT).replace('@N@', str(N_ENTRY))

ARM_ROWS = []
for k in 'ABCD':
    a = ARMS[k]
    ARM_ROWS.append('  - **%s 臂**（%s）：`%s` / %s B / md5=%s / %s 条 `0x34` 行、应答 0 条%s' % (
        k, a['title'], a['rel'], money(a['size']), a['md5'], a['n'],
        '（复位起抓）' if a['banner'] else '（未复位）'))

SUBS = {'@CAR@': os.path.basename(CARRIER), '@EV_AT@': EV_AT, '@EV_VERDICT@': EV_VERDICT,
        '@ARM_ROWS@': '\n'.join(ARM_ROWS).lstrip('\n'), '@ARM_N@': str(ARM_N), '@REPLIES@': str(REPLIES),
        '@BOOTS@': str(BOOTS), '@A_N@': str(ARMS['A']['n']), '@B_N@': str(ARMS['B']['n']),
        '@C_N@': str(ARMS['C']['n']), '@D_N@': str(ARMS['D']['n']),
        '@D_WIN@': '%s 至 %s' % D_WIN.groups(), '@MD5_TF@': MD5_TF, '@MD5_R53@': MD5_R53,
        '@MD5_R43@': MD5_R43, '@FP_TF@': FP_TF, '@L_PWRON@': str(L_PWRON), '@L_PWROUT@': str(L_PWROUT),
        '@L1@': str(L_PWRON), '@L2@': str(L_PWROUT), '@NACK_SECT@': _NACK_SECT, '@_NACK_LN@': str(_NACK_LN),
        '@FAKE@': str(FAKE_PTR_HITS), '@Q21@': Q21, '@Q21_L@': str(Q21_LN), '@Q22@': Q22,
        '@POOL@': str(len(_cands)), '@POOL_N@': str(len(POOL_UNI)),
        '@POOL_UNI@': ' + '.join(POOL_UNI), '@POOL_OTHER@': ' + '.join(POOL_OTHER) or '（无）',
        '@VM_CARRIER@': VM_CARRIER, '@ARMS@': ARMS_FIRED, '@PROBE@': PROBE,
        '@COM@': _com, '@SNAP@': SNAPSHOT_AT, '@SRN@': str(SNAPSHOT_ROWS),
        '@GAP@': str(GAP_MIN), '@BLANK@': '0', '@FSEC@': FSEC,
        '@LOG_ALL@': str(len(_log_all)), '@LOG_OFF@': str(len(_log_official)),
        '@LOG_OURS@': str(len(LOG_OURS)), '@LOG_R56@': str(len(LOG_R56)),
        '@LOG_OLD@': str(len(LOG_OLD)), '@LOG_BOOT_OLD@': str(LOG_BOOT_OLD),
        '@OLD_LOG@': '8', '@OLD_BOOT@': '6', '@SECNUM_DOTTED@': SECNUM,
        '@T@': NOW_AT, '@COM14@': COM14_TXT}
LED_TS = NOW_AT if MODE == 'LANDED_NOW' else re.match(
    r'^> \*\*【(' + TS + ')', _fl[_led[0]]).group(1)
SUBS['@T2@'] = LED_TS
for _k, _val in SUBS.items():
    SEC_BODY = SEC_BODY.replace(_k, _val)
    FREQ_SEC = FREQ_SEC.replace(_k, _val)

LED_TPL = ("> **【@T@ 落地｜R56 第二批 @N@ 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：全文 `^[错误类型]` 条数 = **@K0@**、"
           "`wc -l` 行数 = **@L0@**；追加之后现算，**口径 = 含本台账行自身的最终字节串（本批窗口内，不含后续批次）**："
           "`^[错误类型]` 条数 = **@K1@**、`wc -l` 行数 = **@L1@**（两把尺都在最终串上数 —— (99)）。"
           "本批五条 = **①固定槽位载体池被复跑撑爆、染红的是别人的前向对照链；②批级否定式自述（\"本批没做 X\"）被同批后续动作打假；"
           "③取证正文里的指针没做锚点唯一性复核（实测 v1 那句 `§13-2` 在改前排查记录里 0 命中 = 假指针第 3 例）；"
           "④\"全部现算、无手抄\"这类元声明未与正文对账；⑤分母只数不带算式 ⇒ 新批次无法安全累加**"
           "（正文登记在排查记录 §@SN@，paperwork 载体在 `hardware/@CAR@`；四臂原始取证件 = `..._判据摘录_v2.txt`，v1 不删 —— 它就是第 3、4 条的样本）。\n")


def build(freq_pre_t, doc_pre_t):
    base = lf(freq_pre_t).rstrip('\n') + '\n\n' + lf(FREQ_SEC) + '\n'
    k1, l1 = kinds(base), nl(base) + 1
    led = LED_TPL
    for _k, _val in {'@T@': LED_TS, '@N@': str(N_ENTRY), '@K0@': str(K0), '@L0@': str(L0),
                     '@K1@': str(k1), '@L1@': str(l1), '@CAR@': SUBS['@CAR@'], '@SN@': SECNUM}.items():
        led = led.replace(_k, _val)
    final = crlf(base + led)
    assert kinds(final) == k1 and nl(final) == l1, 'ABORT: 台账行在册的两把尺与最终串不等 ⇒ (99) 那句是假话'
    assert '§' + SECNUM in led, 'ABORT: 台账行没点名本节节号 ⇒ 引用者无从跳转'
    dfin = crlf(lf(doc_pre_t).rstrip('\n') + '\n\n' + lf(SEC_BODY))
    return final, dfin


assert not re.search(r'@[A-Za-z0-9_]+@', SEC_BODY), 'ABORT: §38.23 里还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', SEC_BODY)[:4]
assert not re.search(r'@[A-Za-z0-9_]+@', FREQ_SEC), 'ABORT: FreqErr 本批段还有未回填的 @占位@：%s' % re.findall(r'@[A-Za-z0-9_]+@', FREQ_SEC)[:4]
assert 'zizhao1' not in SEC_BODY and 'zizhao1' not in FREQ_SEC, 'ABORT: 正文含 SoftAP 口令明文'
# 新增的第二道闸：本批正文里每一处 `§X.Y` 式节号引用，都必须在改前排查记录里真有一个那样的标题行
_SECTREF = re.compile(r'§(\d+(?:\.\d+)+)')
QUOTED_FAKE_SECTS = {'13-2'}          # 唯一允许出现 dash 式节号的地方 = 逐字引用 v1 那句假指针
for _t, _tag in ((SEC_BODY, '§38.23'), (FREQ_SEC, 'FreqErr 本批段')):
    for _n in sorted(set(_SECTREF.findall(_t))):
        if _n == SECNUM:
            continue                      # 本批自己那一节：写完之后才存在
        assert any(re.match(r'#{2,4} +' + re.escape(_n) + r'(?![0-9])', l) for l in _rec), \
            'ABORT: %s 里引用了 §%s，但改前排查记录里没有这个标题行 ⇒ 这正是本批第 3 条要拦的错' % (_tag, _n)
    _dash = sorted(set(re.findall(r'§(\d+(?:-\d+)+)', _t)))
    # 唯一豁免 = 本批**逐字引用**的那句假节号（v1 里的 `§13-2`）；豁免的前置条件就是它被证明盘上不存在。
    assert set(_dash) <= QUOTED_FAKE_SECTS and FAKE_PTR_HITS == 0, \
        'ABORT: %s 里出现 `§%s` 这种本仓库不存在的节号写法（本批只允许逐字引用 %s，且须 FAKE_PTR_HITS==0）' % (
            _tag, ','.join(_dash), ','.join(sorted(QUOTED_FAKE_SECTS)))

if MODE == 'LANDED_NOW':
    freq_final, doc_final = build(freq_pre, doc_pre)
    assert LED_TS == NOW_AT, 'ABORT: 写侧标题时刻与本遍 NOW_AT 不等'
    assert re.match(r'^> \*\*【' + TS + ' 落地｜R56 第二批', lf(freq_final).split('\n')[-2]), 'ABORT: 台账行没落在文件末行前'
else:
    freq_final, doc_final = freq_disk, doc_disk
    assert _fl[-1] == '', 'ABORT: 盘上 FreqErr 末行不是空行 ⇒ 两把尺与行索引的恒等式不成立'
    _lt = _fl[_led[0]]
    _m = re.search(r'条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*.*?条数 = \*\*(\d+)\*\*、`wc -l` 行数 = \*\*(\d+)\*\*', _lt)
    assert _m, 'ABORT: 本批台账行不再合"改前两把尺 + 终态两把尺"句式'
    assert (K0, L0) == (int(_m.group(1)), int(_m.group(2))), \
        'ABORT: 反推的"改前"两把尺(%d,%d) != 台账行在册(%s,%s)' % (K0, L0, _m.group(1), _m.group(2))
    GLUE_F = 1 if _fl[_hf[0] - 1].strip() == '' else 0
    assert GLUE_F == 1, 'ABORT: 本批 FreqErr 标题上方没有空行 ⇒ 追加形状变了'
    _tail_f = _fl[_led[0] + 1:-1]
    TAIL_KF = len([l for l in _tail_f if l.startswith('[错误类型]')])
    # 行数等式里**不能再加 GLUE_F**：在册的 AFTER 行数本身就把"本批标题上方那只空行"数进去了（它是本批写下的），
    # 而 _tail_f 是从本批台账行的**下一行**起算的，后面那一批的空行天然落在 _tail_f 里。
    # 这一格在 LANDED_NOW 那一遍永远不会被执行（§38.21 ① 那一族的第 3 次命中）：本批第一次复跑 paperwork2 时才炸。
    assert (kinds(freq_disk), nl(freq_disk)) == \
        (int(_m.group(3)) + TAIL_KF, int(_m.group(4)) + len(_tail_f)), \
        'ABORT: 台账行在册终态(%s,%s) + 窗口外两笔(TAIL=%d 行 %d 条) != 盘上现算(%d,%d)' % (
            _m.group(3), _m.group(4), len(_tail_f), TAIL_KF, kinds(freq_disk), nl(freq_disk))
    assert len([l for l in _fl[_hf[0]:_led[0]] if l.startswith('[错误类型]')]) == N_ENTRY, \
        'ABORT: 本批尾段的 `[错误类型]` 不是 %d 条' % N_ENTRY
    _dl_all = lf(doc_disk).split('\n')
    _dnx = [i for i in range(_hd[0] + 1, len(_dl_all) - 1) if _dl_all[i].startswith(('## ', '### '))]
    _dwin_end = _dnx[0] if _dnx else len(_dl_all) - 1
    WIN_D = _dl_all[_hd[0]:_dwin_end]
    TAIL_D = len(_dl_all) - 1 - _dwin_end
    GLUE_D = 1 if _dl_all[_hd[0] - 1].strip() == '' else 0
    assert nl(doc_disk) == DOC_ROWS0 + GLUE_D + len(WIN_D) + TAIL_D, \
        'ABORT: 排查记录盘上行数 %d != 改前 %d + 上方空行 %d + 本批节 %d 行 + 本节之后 %d 行' % (
            nl(doc_disk), DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)
WIN_F = (lf(freq_final).split('\n')[L0:] if MODE == 'LANDED_NOW' else _fl[_hf[0]:_led[0] + 1])
WIN_D = (lf(doc_final).split('\n')[DOC_ROWS0:] if MODE == 'LANDED_NOW' else WIN_D)
WIN_D = (lf(doc_final).split('\n')[DOC_ROWS0:] if MODE == 'LANDED_NOW' else WIN_D)
assert '\\' not in '\n'.join(WIN_F), 'ABORT: 本批 FreqErr 追加段里有反斜杠（§38.18 那一族）：%r' % [l for l in WIN_F if '\\' in l][:2]
assert '\\' not in '\n'.join(WIN_D), 'ABORT: 本批 §38.23 追加段里有反斜杠：%r' % [l for l in WIN_D if '\\' in l][:2]
assert (kinds(freq_final) - K0 == N_ENTRY) if MODE == 'LANDED_NOW' \
    else (kinds(freq_disk) - K0 == N_ENTRY + TAIL_KF), 'ABORT: 本批正文 `[错误类型]` 增量不是 %d' % N_ENTRY
_bare = [l for l in WIN_D if l.strip() and not l.strip().startswith(('-', '>', '#'))]
assert not _bare, 'ABORT: §38.23 追加段里有裸行（非列表/引用）：%r' % _bare[:2]

print('MODE=%s EV=%s / %s 条 0x34 行 / 应答 %d / 复位起抓 %d 臂' % (
    MODE, os.path.basename(EV), ARM_N, REPLIES, BOOTS))
print('CITE 两遍同值: PWRON=%d, PWR_OUT=%d, 分流节=§%s(第%d行) / 载体在册=%s,%s / 假节号 §13-2 命中 %d 处' % (
    L_PWRON, L_PWROUT, _NACK_SECT, _NACK_LN, EV_CIT, list(EV_SECT.groups()), FAKE_PTR_HITS))
print('IDENTITY 待烧=%s 归档r53=%s 板上含指纹 %s ⇒ 收口=%s / 旧镜像 r43=%s' % (
    MD5_TF, MD5_R53, FP_ONBOARD, ONBOARD_OK, MD5_R43))
print('DENOM hardware/*.log=%d 官方=%d 我方=%d 本批新增=%d 旧%d只里ROM banner=%d / 旧在册格 %s 只 %s 次上电=复算不出' % (
    len(_log_all), len(_log_official), len(LOG_OURS), len(LOG_R56), len(LOG_OLD), LOG_BOOT_OLD, '8', '6'))
print('SEAL rows=%d disk=%d GATE %s / VM rc=%d %s %s' % (len(_rows), DISK_N, ARMS_FIRED, _v.returncode, VM_ROWS, VM_VERDICT))
print('FREQ 改前 %d 条 / %d 行 -> %d 条 / %d 行 / GAP(§38.22→取证)=%d 分钟' % (
    K0, L0, kinds(freq_final), nl(freq_final), GAP_MIN))

if MODE == 'LANDED_NOW':
    open(FREQ, 'wb').write(freq_final.encode('utf-8'))
    open(DOC, 'wb').write(doc_final.encode('utf-8'))

_r = subprocess.run([sys.executable, P1], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
_pos = [l for l in _r.stdout.split('\n') if l.startswith(('MODE=', 'VERDICT=', 'FREQ '))]
_pos_short = ' | '.join(l[:110] for l in _pos)
assert _r.returncode == 0 and _pos, 'ABORT: 前向对照（复跑第一批落地器）rc=%d ⇒ 本批追加把它弄红了，先查再落' % _r.returncode

_now2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
PRE_EQ_F = lf(freq_disk).startswith(lf(freq_pre).rstrip('\n'))
PRE_EQ_D = lf(doc_disk).startswith(lf(doc_pre).rstrip('\n'))
assert PRE_EQ_F and PRE_EQ_D, 'ABORT: 改前正文不是盘上正文的逐字前缀 ⇒ 本批不只做了追加'
_window_row = ('复跑差额账目（"口径 = 本批窗口内、不含后续批次"的可复算证明）：FreqErr 本批台账行之下另有 %d 行 / %d 条'
               '（本批标题上方空行现读 %d 只，它已在册于本批 AFTER 行数之内 ⇒ 不进这条等式）；'
               '排查记录 §38.23 标题上方空行 %d 只、本节之后 %d 行 ⇒ '
               '盘上行数 = 改前 %d + 上方空行 %d + 本批节 %d 行 + 之后 %d 行' % (
                   len(_tail_f), TAIL_KF, GLUE_F, GLUE_D, TAIL_D, DOC_ROWS0, GLUE_D, len(WIN_D), TAIL_D)) \
    if MODE == 'REWROTE_CARRIER_ONLY' else \
    ('写盘支：本批尾段 = FreqErr %d 行（首行 [%s]）+ §38.23 %d 行（首行 [%s]）；'
     '之前那一批的读数不在本行口径内' % (len(WIN_F), WIN_F[0][:24], len(WIN_D), WIN_D[0][:24]))
_lines = [
    'R56 真机首烧批 paperwork 落地器  MODE=%s' % MODE,
    '本遍现跑于 %s（台账行标题时刻 = %s；载体由脚本自己落盘，在归档目录之外）' % (_now2, LED_TS),
    'EV 取证载体=%s / %s B / md5=%s（**md5**，32 位 hex）/ 生成时刻 %s / 裁决 %s' % (
        os.path.basename(EV), os.path.getsize(EV), md5_(EV), EV_AT, EV_VERDICT),
    'EV 四臂解析（逐字取自那只载体，并回核盘上 md5 相等）=%s' % ' ; '.join(
        '%s=%s 条/%s B/md5=%s…' % (k, ARMS[k]['n'], money(ARMS[k]['size']), ARMS[k]['md5'][:8]) for k in 'ABCD'),
    'EV 合计=%s 条 0x34 行 / 应答 %d 条 / 复位起抓（ROM banner 命中）%d 臂 / D 窗口=%s 至 %s（现算自 TEMP 原件 ctime→mtime）' % (
        ARM_N, REPLIES, BOOTS, D_WIN.group(1), D_WIN.group(2)),
    'CITE 两把量具独立现查（本遍 vs 取证载体在册）：PWRON 行 %d/%s、PWR_OUT 行 %d/%s、分流节 §%s(第 %d 行)/§%s(第 %s 行)；'
    '锚点一律查在**改前正文**上（本批正文自己会引用这些串，拿全文件查就自指）；'
    '同一遍反查 v1 那句 `§13-2` 在改前排查记录里命中 %d 处 ⇒ 假指针成立 = 本批 FreqErr 第 3 条' % (
        L_PWRON, EV_CIT[0], L_PWROUT, EV_CIT[1], _NACK_SECT, _NACK_LN,
        EV_SECT.group(1), EV_SECT.group(2), FAKE_PTR_HITS),
    'IDENTITY 三格等式：待烧(构建目录)md5=%s / 归档 r53 md5=%s / 板上 boot 指纹=%s 且它出现在 %s 里 ⇒ (92) 收口成立 = %s；'
    '旧镜像 r43 md5=%s 降级为历史（A/B 两臂的图）' % (MD5_TF, MD5_R53, FP_TF, FP_ONBOARD, ONBOARD_OK, MD5_R43),
    'DENOM 新口径现算：hardware/ 单层 *.log=%d 只 / 其中"官方例程"对照 %d 只不进分母 / 我方=%d 只 / 本批新增 %d 只 / '
    '本批之前 %d 只里 ROM banner 命中 %d 只；上一格在册 "8 只 / 6 次上电" 本遍复算不出构成 ⇒ 就地降级为不可复算的旧快照（禁止在它上面做加法）' % (
        len(_log_all), len(_log_official), len(LOG_OURS), len(LOG_R56), len(LOG_OLD), LOG_BOOT_OLD),
    'SEAL 清单在册=%d 行 / 目录全量=%d 只 / %s B / 差集逐只点名=%s / 两只 mtime 秒数 == 末版那一秒 %s' % (
        len(_rows), DISK_N, money(DISK_B), ' + '.join(NOT_LISTED), SEAL_AT),
    'GATE %s（假名 %s 只在内存；盘上反查不存在 = True）' % (ARMS_FIRED, PROBE),
    'VM 本遍真跑（内层 verify_manifest 的 gen 24 槽位已用满 ⇒ 由 hardware/vm_run.py 逐字代落载体）rc=%d / %s / %s / VM_CARRIER=%s' % (
        _v.returncode, VM_ROWS, VM_VERDICT, VM_CARRIER),
    'POOL 槽位池容量逐只现读（本遍从每只工具源码正则读出，非抄上一遍的话）：达本批容量 %d 只的 %d 只 = %s / 未达 = %s；'
    '命中池定义的落地器共 %d 只（少于 5 只即 ABORT）' % (
        len(_cands), len(POOL_UNI), ' + '.join(POOL_UNI), ' + '.join(POOL_OTHER) or '（无）', len(_POOL)),
    'FIELD rev-list=%s / comports=%s（COM14 %s）/ docs 快照=%s（表格 %d 行）/ 屏亮肉眼确认 0 次 / §38.22→取证 间隔 %d 分钟' % (
        _rev, _com, COM14_TXT, SNAPSHOT_AT, SNAPSHOT_ROWS, GAP_MIN),
    'FREQ 改前 %d 条 / %d 行 -> %s %d 条 / %d 行' % (K0, L0, '本遍写盘终态' if MODE == 'LANDED_NOW' else '盘上在册终态',
                                                kinds(freq_final), nl(freq_final)),
    'DOC 改前 %d 行 / %s B -> %s %d 行 / %s B（两格同尺 = 行尾 CRLF 的落盘字节数；反查 crlf(终态串) 长度 == 盘上现读大小 = %s）' % (
        DOC_ROWS0, money(len(crlf(doc_pre).encode('utf-8'))),
        '本遍写盘终态' if MODE == 'LANDED_NOW' else '盘上在册终态', nl(doc_final), money(os.path.getsize(DOC)),
        len(crlf(doc_final).encode('utf-8')) == os.path.getsize(DOC)),
    _window_row,
    'WINDOW 前缀等式（"只追加、正文一字未改"的可复算证明）：FreqErr 改前 %d 行是盘上 %d 行的逐字前缀 = %s / '
    '排查记录 %d -> %d 行 = %s；本批窗口 = FreqErr %d 行 + §38.23 %d 行' % (
        nl(freq_pre), nl(freq_disk), PRE_EQ_F, DOC_ROWS0, nl(doc_disk), PRE_EQ_D, len(WIN_F), len(WIN_D)),
    'POSCTL 复跑第一批落地器 rc=%d / %s' % (_r.returncode, _pos_short),
    'SELF-SCOPE-NOTE 本行的"零串口动作"只描述本遍（paperwork，%s）。同批真机首烧的四臂抓取确实发生过'
    '（在册 = `%s`，生成时刻 %s，间隔 §38.22 落地 %d 分钟）⇒ 不许把本行读成"R56 没烧录"。'
    '"本遍没开口"这一格拿不出外部证据（comports 只读列口 = 自述），按本批 FreqErr 第 2 条在此点名"无法证明"。' % (
        _now2, os.path.basename(EV), EV_AT, GAP_MIN),
    'WITNESS FREQ md5=%s / DOC md5=%s（本遍结束时现算）' % (md5_8(FREQ), md5_8(DOC)),
    'NOTDONE 本遍（%s）没做：串口 / 烧录 / 换电池 / 万用表 / 第二块板 / 改 main 源码 / 重建固件 / 新建备份根 / '
    '新建清单代次 / push / amend / 删除 —— 屏亮 0 次肉眼确认 ⇒ 未播提示音；'
    '提交轮#9、docs 第十遍、backups README 第十次读数、第 14 代同步在本节之后 ⇒ 本遍不预写它们的数' % _now2,
    'VERDICT=%s（两只 CRLF 目标里本遍写盘 %d 只 + 载体 1 只）' % (
        'OK-LANDED' if MODE == 'LANDED_NOW' else 'OK-CARRIER-ONLY', 2 if MODE == 'LANDED_NOW' else 0),
]
_self_made = [l for l in _lines if not l.startswith('POSCTL')]
assert '\\' not in '\n'.join(_self_made), 'ABORT: 本脚本自造的载体行里有反斜杠（自造行数=%d）：%r' % (
    len(_self_made), [l for l in _self_made if '\\' in l][:2])
assert 'zizhao1' not in '\n'.join(_lines), 'ABORT: 载体含口令明文'
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(_lines) + '\n')
print('VERDICT=OK CARRIER=%s' % os.path.basename(CARRIER))
print('POSCTL rc=%d %s' % (_r.returncode, _pos_short))
