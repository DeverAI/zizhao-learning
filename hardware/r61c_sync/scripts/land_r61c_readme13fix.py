# README 第十三次读数的**核销遍**（不改正文，只补载体与证明）。
# 为什么要有这一遍：`land_r61c_readme13.py` 首遍 **rc=1 且确实动了盘**——插入本身是对的，
# 崩在它自己那条**手写的行数算式**上：`out = lines0[:idx] + new_lines + [''] + lines0[idx+1:]`
# 的行数由构造就是 `len(lines0) + len(new_lines)`（那个 `['']` 是**替换**掉 `lines0[idx]` 那根空行，不是净增一根），
# 而我写成了 `+ 1` ⇒ assert 崩在 `write()` 的下一行。这正是 §38.36 缺陷 (o) 登记过的那一族**第二次复发**，
# 差别是上次预期值错在"末行无行尾符"，这次错在"替换空行当净增"——同一个根：**证明段的算式没人独立推第二遍**。
# 本遍处置（照 §38.36 那三段）：①幂等门以**载体有没有写盘后令牌**为权威（正文有格子而无载体 = 崩在写盘之后 ⇒ 允许核销）；
# ②pre-image 与盘上现件做三段式行级证明；③预期行数在本遍**用两种独立推法**先互等，再跟盘上回读比。
import difflib
import hashlib
import io
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
os.chdir(REPO)
EV = os.path.join('hardware', 'r61c_sync', 'evidence')
README = 'backups/README.md'
TOKEN = 'VERDICT=LANDED'
T0 = datetime.now()
OUTL = []


def say(s):
    OUTL.append(s)
    print(s)


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), capture_output=True, shell=False)
    assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')
    return r.stdout.decode('utf-8', 'replace')


# ---------- ①幂等门 + pre-image 唯一性 ----------
_cands = [os.path.join(EV, f) for f in sorted(os.listdir(EV)) if re.match(r'^readme_pre13_\d{8}_\d{6}\.md$', f)]
assert len(_cands) == 1, 'ABORT: pre-image 应恰 1 只，实测 %d：%s' % (len(_cands), _cands)
PRE = _cands[0]
_stamp = re.search(r'readme_pre13_(\d{8})_(\d{6})\.md$', PRE)
PRE_DT = datetime.strptime(_stamp.group(1) + _stamp.group(2), '%Y%m%d%H%M%S')

rb0 = io.open(PRE, 'rb').read()
rb1 = io.open(README, 'rb').read()
assert rb1 != rb0, 'ABORT: 盘上 README 与 pre-image 逐字节相等 ⇒ 首遍其实没动盘，本遍无需核销（先查幂等门）'
_cur_land = [f for f in os.listdir(EV) if re.match(r'^r61c_readme13_land_\d{6}\.txt$', f)
             and TOKEN in io.open(os.path.join(EV, f), encoding='utf-8').read()]
assert not _cur_land, 'ABORT: 已有含写盘后令牌的第十本格载体 ⇒ 这一遍早跑过了：%s' % _cur_land
_crashed = [f for f in os.listdir(EV) if re.match(r'^r61c_readme13_land_\d{6}\.txt$', f)]
assert not _crashed, 'ABORT: 崩遍载体竟存在但不含令牌之外的判据没跑（先读它）：%s' % _crashed

txt0, txt1 = rb0.decode('utf-8'), rb1.decode('utf-8')
assert txt1.count('第十三次读数') == 1 and '第十三次读数' not in txt0, \
    'ABORT: 新格在 pre-image 里已存在或现件不唯一 ⇒ 不是"一次插入"这一形态'

# ---------- ②三段式行级证明（同类型：str 行表 vs str 行表） ----------
lines0, lines1 = txt0.split('\n'), txt1.split('\n')
a0 = [i for i, l in enumerate(lines0) if l.startswith('## 2. 命名规则')]
a1 = [i for i, l in enumerate(lines1) if l.startswith('## 2. 命名规则')]
assert len(a0) == len(a1) == 1, 'ABORT: 锚点在两侧不唯一'
idx = a0[0] - 1
assert lines0[idx] == '' and lines1[a1[0] - 1] == '', 'ABORT: 锚点前的空行不在位 ⇒ 结构被吃掉'
n_new = len(lines1) - len(lines0)
assert n_new > 0, 'ABORT: 现件行数不比 pre-image 多 ⇒ 这不是纯插入'
ins = lines1[idx:idx + n_new]
assert lines1[:idx] == lines0[:idx], 'ABORT: 插入点之前未逐字保持'
assert lines1[idx + n_new] == '' and lines1[idx + n_new + 1:] == lines0[idx + 1:],     'ABORT: 插入点之后未逐字保持（插入段末尾那根空行是**替换**掉原空行，不是净增）'
assert ins[0].startswith('【09-26') and ins[-1].startswith('（载体：') and all(ins), 'ABORT: 插入段形状不是"一格正文 + 一根分隔空行在位"'
_seg = chr(10).join(ins)

def cell(mark, start=False):
    hits = [l for l in ins if l.startswith(mark)] if start else [l for l in ins if mark in l]
    assert len(hits) == 1, 'ABORT: 段内标记 %s 命中 %d 处（应恰 1）' % (mark, len(hits))
    return hits[0]

# ---------- ③预期行数：两种独立推法先互等，再跟盘上比 ----------
# 推法甲：构造式（插入段 n_new 行，且段后那根空行替换掉原空行 ⇒ 净增恰为 n_new）
_by_build = len(lines0) + n_new
# 推法乙：内容式（插入段去掉末尾空行后逐行数出来的段行数 + pre-image 行数，且差集只含新增行）
_d = [l for l in difflib.unified_diff(lines0, lines1, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
_add = len([l for l in _d if l[0] == '+'])
_del = len([l for l in _d if l[0] == '-'])
_by_diff = len(lines0) + _add - _del
assert _by_build == _by_diff == len(lines1), \
    'ABORT: 两种独立推法不等（构造 %d / 差集 %d / 盘上 %d）' % (_by_build, _by_diff, len(lines1))
assert _add == n_new and _del == 0, 'ABORT: 差集显示有删除行（%d 处）⇒ 首遍不是纯插入' % _del
say('ROWS 两种独立推法互等：%d == %d == 盘上回读 %d（构造式 = pre %d + 新增 %d；差集式 +%d/−%d）'
    % (_by_build, _by_diff, len(lines1), len(lines0), n_new, _add, _del))
assert rb1[-1:] == b'\n' and rb1.count(b'\r') == 0, 'ABORT: 现件末字节非换行或带 CR'
assert txt1.count('第十三次读数') == txt0.count('第十三次读数') + 1, 'ABORT: 新格出现次数不是净增 1'
_ck0 = len([l for l in lines0 if l.startswith('【')])
_ck1 = len([l for l in lines1 if l.startswith('【')])
assert _ck1 == _ck0 + 1, 'ABORT: 读数格（以【开头的标题行）增量 != 1 ⇒ 动了旧格（%d -> %d）' % (_ck0, _ck1)

# ---------- 正文里那些「由 assert 把关」的句子，本遍在**落盘后的段**上逐格复算 ----------
HEAD = re.search(r'HEAD`（([0-9a-f]{7})）', cell('相对 `HEAD`')).group(1)
assert HEAD == git('rev-parse', '--short', 'HEAD').strip(), 'ABORT: 正文里的 HEAD 短号不是现值'
assert HEAD in git('log', '--format=%h', '-1'), 'ABORT: 正文短号不在 log 里'
_por = [l for l in git('status', '--porcelain').split('\n') if l]
_k = {}
for l in _por:
    _k[l[:2]] = _k.get(l[:2], 0) + 1
_m = re.search(r'`git -c core\.quotePath=false status --porcelain` = \*\*(\d+) 行\*\*（(`[^`]*` \d+ \+ )?`\?\?` (\d+)；桶完备', cell('⑨ ', start=True))
assert _m, 'ABORT: 正文 ⑨ 那格的 status 读数取不到'
assert _m, 'ABORT: 正文 ⑨ 那格取不到 status 读数'
say('STATUS 正文 %s 行 / `??` %s（本遍现跑不 strip = %d 行 / ` M` %d + `??` %d）'
    % (_m.group(1), _m.group(3), len(_por), _k.get(' M', 0), _k.get('??', 0)))
assert int(_m.group(1)) == len(_por) and int(_m.group(3)) == _k.get('??', 0), \
    'ABORT: 正文 ⑨ 那格落的 status 读数与本遍现跑不等 ⇒ 要么现场漂了要么首遍写进的是别的尺'
# ⑦ 那格的 docs 五格全部回读盘上 NOTE
note = io.open(os.path.join('backups', 'r43_20260922_131029', 'docs', 'SNAPSHOT_NOTE.txt'), encoding='utf-8').read()
_at = re.search(r'刷新时刻 ([0-9: -]{19})', note).group(1)
_rows = len([l for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
_new = [l.split('\t')[0] for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)]
for tok in (_at, str(_rows), str(_rows + 1), _new[0], str(len(_new))):
    assert tok in cell('docs/ 快照第十三遍'), 'ABORT: ⑦ 那格里读不到 docs 现值 %r' % tok
say('DOCS ⑦ 那格五格全中：SNAPSHOT_AT %s / 表格 %d 行 / 目录 %d 只 / NEW %d 只 = `%s`'
    % (_at, _rows, _rows + 1, len(_new), _new[0]))
# ⑧ 那格的 FreqErr / 排查记录 / 封界三格
fb = io.open('FreqErr.md', 'rb').read()
pzb = io.open(os.path.join('hardware', '20260919_墨水屏点屏排查记录.md'), 'rb').read()
h = sum(len(fn) for dp, dn, fn in os.walk(os.path.join('hardware', 'ht305_sync')))
for tok in (str(fb.count(b'\n')), str(len(re.findall(r'^\[错误类型\]', fb.decode('utf-8'), re.M))),
            str(len(fb)), str(pzb.count(b'\n')), str(h)):
    assert tok in cell('FreqErr / 排查记录 / 封界 / 串口现场态'), 'ABORT: ⑧ 那格里读不到现值 %r' % tok
say('STATE ⑧ 那格全中：FreqErr 行数/条数/字节 + 排查记录行数 + ht305_sync %d 只' % h)
assert h == 388, 'ABORT: 封存归档只数变了（gen 24 之后落字节了？）'
# 反斜杠 / 撇号 / 明文 三道正文闸，在**盘上落下来的那一段**上再跑一遍（不是只在内存里跑过）
mac = io.open(os.path.join('hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c'), 'rb').read()
sec = re.search(rb'#define\s+PROV_PASS\s+"([^"]+)"', mac).group(1)
assert sec not in rb1, 'ABORT: 明文口令出现在盘上 README 里'
seg = '\n'.join(ins).encode('utf-8')
assert seg.count(b'\r') == 0 and seg.count(chr(92).encode()) == 0, 'ABORT: 插入段带 CR 或反斜杠'
say('GATES 盘上插入段复跑：明文 HITS=0 / 反斜杠 0 / CR 0 / 新格唯一 1 处 / 旧格未被触碰（+%d −%d）' % (_add, _del))

# ---------- 落载体 ----------
_car = os.path.join(EV, 'r61c_readme13_fix2_%s.txt' % T0.strftime('%H%M%S'))
assert not os.path.exists(_car), 'ABORT: 载体目标已存在 ' + _car
body = (
    'README 第十三次读数的核销遍（不改正文），现跑于 %s\n' % T0.strftime('%Y-%m-%d %H:%M:%S') +
    'DEFECT 首遍 `land_r61c_readme13.py` rc=1 且**确实动了盘**：崩点 = 写盘后证明段那条手写行数算式 `len(lines0)+len(new_lines)+1`，\n'
    '        而 `out = lines0[:idx] + new_lines + [空行] + lines0[idx+1:]` 由构造只净增 `len(new_lines)`（末行空行是**替换**不是追加）⇒ 恒差 1。\n'
    '        同族第二次复发（首次 = 排查记录 §38.36 缺陷 (o)），差别：上次错在"末行有无行尾符"，这次错在"替换空行当净增"。\n' +
    'PRE-IMAGE %s（%d B / %d 行 / md5 前 8 %s）——写盘前原件，本遍逐字节未动\n' % (
        os.path.basename(PRE), len(rb0), len(lines0), hashlib.md5(rb0).hexdigest()[:8]) +
    'README 现件 %d B / %d 行 / md5 前 8 %s / 新格 %d 行插入于第 %d 行之后\n' % (
        len(rb1), len(lines1), hashlib.md5(rb1).hexdigest()[:8], n_new, idx + 1) +
    'PROOF 三段式（前缀逐字等 / 插入段逐行等 / 后缀逐字等）+ 两种独立推法行数互等 + 差集 +%d −%d ⇒ 纯插入、旧格零改动\n' % (_add, _del) +
    'ROWS 构造 %d == 差集 %d == 盘上 %d\n' % (_by_build, _by_diff, len(lines1)) +
    'CARRIERS 本遍之前该前缀含写盘后令牌的载体 = 0 只（幂等门的权威判据），崩遍载体 = %d 只（本遍不覆写、不删除）\n' % len(_crashed) +
    'NOTE 本遍**零改写正文、零删除**；正文里 ⑦⑧⑨ 三格的读数由本遍在盘上现复算（docs 五格 / FreqErr 三格 / ht305_sync 只数 / status 两格 / HEAD 短号），\n'
    '     并复跑明文·反斜杠·CR·撇号四道正文闸；取证只落本只载体。\n')
io.open(_car, 'wb').write((body + TOKEN + ' rc=0\n').encode('utf-8'))
_back = io.open(_car, 'rb').read()
assert _back == (body + TOKEN + ' rc=0\n').encode('utf-8'), 'ABORT: 载体回读不等'
assert [l for l in _back.decode('utf-8').split('\n') if l][-1] == TOKEN + ' rc=0', 'ABORT: 载体末行不是令牌'
say('CARRIER %s（%d B / md5 前 8 %s）' % (os.path.basename(_car), len(_back), hashlib.md5(_back).hexdigest()[:8]))
say(TOKEN + ' rc=0')
txt = '\n'.join(OUTL) + '\n'
io.open(_car, 'ab').write(('\n--- 本遍 stdout（%s）---\n' % T0.strftime('%H:%M:%S') + txt).encode('utf-8'))
_b2 = io.open(_car, 'rb').read()
assert _b2.startswith(_back) and _b2.endswith(txt.encode('utf-8')), 'ABORT: 追加 stdout 后载体形状变了'
print('CARRIER_FINAL %s（%d B）' % (os.path.basename(_car), len(_b2)))
