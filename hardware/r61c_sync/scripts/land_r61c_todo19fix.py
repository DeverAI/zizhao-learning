# todo.md 第十九遍**订正遍**：把第一遍落进正文的 porcelain 桶计数换成现跑值，并逐字引用第一遍那句错话。
# 缺陷本体（新错误类型，去向 = `FreqErr.md` 第二十批 + 排查记录 §38.37）：
#   取数助手 `git()` 里那句 `.strip()` 会把 `git status --porcelain` **第一行的前导空格**一起吃掉，
#   而分类尺是 `l[:2] == ' M'` ⇒ 未跟踪桶 `??` 恰好也带前导空格？不，`??` 无前导空格、不受影响，
#   受影响的是未入库修改那一桶：本机第一条恰是 ` M FreqErr.md` ⇒ ` M` 恒少计 1。
#   第一遍因此打出「55 行（` M` 4 + `??` 50）」，而 4 + 50 = 54 != 55 —— "桶之和 == 总数"这一条当时没有执行者。
# 修法两条：①读 porcelain 一律不 strip；②装**桶完备 assert**（总数 == ` M` + `??`，且出现任何未点名前缀立即 ABORT），
#   并给这条 assert 配一把**已知会少计 1 的旧尺**做阳性对照（旧尺必须真的少 1，否则本遍这条 assert 没有牙）。
import datetime
import difflib
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
TOD = os.path.join(REPO, 'todo.md')
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
BS = chr(92)
MARK = '第十九遍'
_T0 = datetime.datetime.now()
_tt = _T0.strftime('%Y%m%d_%H%M%S')


def _raw_porcelain():
    r = subprocess.run(['git', '-c', 'core.quotePath=false', 'status', '--porcelain'],
                       cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT: git status 退出码非 0'
    return r.stdout.decode('utf-8', 'replace')


def _lines(text, do_strip):
    t = text.strip() if do_strip else text
    return [l for l in t.split('\n') if l]


def buckets(ls):
    mods = [l for l in ls if l[:2] == ' M']
    uns = [l for l in ls if l[:2] == '??']
    other = sorted(set(l[:2] for l in ls if l[:2] not in (' M', '??')))
    return mods, uns, other


_raw = _raw_porcelain()
por = _lines(_raw, False)
mods, uns, other = buckets(por)
assert not other, 'ABORT: 出现未点名的前缀桶 %s ⇒ 桶完备 assert 未覆盖该形态' % other
assert len(por) == len(mods) + len(uns), 'ABORT: 总数 != 各桶之和（%d vs %d + %d）' % (
    len(por), len(mods), len(uns))
# 旧尺（带 strip）必须**真的**少计 1 —— 这是本遍这条 assert 的阳性对照，也是"缺陷仍在"的现场证明
b_mods, b_uns, _b_other = buckets(_lines(_raw, True))
assert len(b_mods) == len(mods) - 1 and len(b_uns) == len(uns), \
    'ABORT: 旧尺没有复现出「少计 1」（旧尺 ` M` %d / 新尺 ` M` %d）⇒ 第一遍的成因归因不成立，先别订正' % (
        len(b_mods), len(mods))
print('RULER 新尺 %d 行（` M` %d + `??` %d，桶完备）/ 旧尺（strip）打出 ` M` %d ⇒ 恰好少 1，缺陷现场复现' % (
    len(por), len(mods), len(uns), len(b_mods)))

cur = io.open(TOD, 'rb').read()
assert cur.endswith(b'\r\n'), 'ABORT: 现件末行不以 CRLF 收尾'
cur_txt = cur.decode('utf-8')
assert MARK in cur_txt.split('\r\n')[0], 'ABORT: 现件首行不含本遍序数 ⇒ 被订正的那一遍不在原位'

# 第一遍那句错话：从盘上现读，不手抄（订正句的引文必须由落地器自己读出来并断言）
g = re.search(r'`git -c core\.quotePath=false status --porcelain` = \*\*(\d+) 行\*\*（` M` (\d+) \+ `\?\?` (\d+)；'
              r'[^）]*）', cur_txt)
assert g, 'ABORT: 现件里读不到 porcelain 那整句 ⇒ 没有可订正的锚'
old_span = g.group(0)
v1 = (int(g.group(1)), int(g.group(2)), int(g.group(3)))
assert cur_txt.count(old_span) == 1, 'ABORT: 锚命中 %d 处 ⇒ 就地替换会改到别处' % cur_txt.count(old_span)
assert v1[1] + v1[2] != v1[0], 'ABORT: 第一遍那句竟然自洽（%d + %d == %d）⇒ 少计 1 的成因不在这只锚上，停手重查' % (
    v1[1], v1[2], v1[0])
print('V1-ON-DISK 第一遍那句 = %d 行 / ` M` %d + `??` %d ⇒ 桶和 %d != 总数 %d（缺执行者时的形状）' % (
    v1[0], v1[1], v1[2], v1[1] + v1[2], v1[0]))
_landed = [p for p in glob.glob(os.path.join(EV, 'r61c_todo19_fix_*.txt'))
           if 'VERDICT=LANDED' in io.open(p, encoding='utf-8').read()]
assert not _landed, 'ABORT: 订正遍已落过盘（载体含写盘后令牌）：%s' % _landed

new_span = ('`git -c core.quotePath=false status --porcelain` = **%d 行**（` M` %d + `??` %d；'
            '`??` 含目录折叠行 ⇒ 与文件只数互不可换算；**总数 == 两桶之和这条本遍起有执行者**）。'
            '**订正（现跑于 %s）**：第一遍那句写的是 %d 行 / ` M` %d + `??` %d，桶和 %d != 总数 %d，'
            '成因 = 取数助手里那句 `.strip()` 吃掉了 porcelain 首行的前导空格、而分类尺看的正是前两个字符；'
            '本遍同尺复现 = 旧尺打出 ` M` %d（真值 %d，恰好少 1）') % (
                len(por), len(mods), len(uns), _T0.strftime('%Y-%m-%d %H:%M:%S'),
                v1[0], v1[1], v1[2], v1[1] + v1[2], v1[0], len(b_mods), len(mods)) + '）'

idx = cur_txt.index(old_span)
head, tail = cur_txt[:idx], cur_txt[idx + len(old_span):]
merged = head + new_span + tail
assert merged.count(old_span) == 0 and merged.count(new_span) == 1, 'ABORT: 替换后锚仍在 / 新句不止一处'
assert merged.startswith(head) and merged.endswith(tail), 'ABORT: 头尾未被逐字保持'
for i, l in enumerate(merged.split('\n'), 1):
    assert l.count('`') % 2 == 0, 'ABORT: 第 %d 行反引号不成对：' % i + l[:80]
    assert chr(39) not in l, 'ABORT: 第 %d 行含 ASCII 撇号：' % i + l[:60]
assert BS not in new_span, 'ABORT: 订正句里不该出现反斜杠'
assert chr(39) not in new_span, 'ABORT: 订正句含 ASCII 撇号'
_stray = [l[:70] for l in merged.split('\n') if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 未插值占位符 %d 处：%s' % (len(_stray), _stray[:2])

new = merged.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
assert new.count(b'\r') == new.count(b'\n') == len(new.splitlines()), 'ABORT: CRLF 两把尺不同值（CR %d / LF %d / 行数 %d）' % (
    new.count(b'\r'), new.count(b'\n'), len(new.splitlines()))

PRE = os.path.join(EV, 'todo19_pre_fix_%s.md' % _tt)
assert not os.path.exists(PRE), 'ABORT: pre-image 目标已存在 ' + PRE
io.open(PRE, 'wb').write(cur)
assert io.open(PRE, 'rb').read() == cur, 'ABORT: pre-image 回读不等'

io.open(TOD, 'wb').write(new)
chk = io.open(TOD, 'rb').read()
assert chk == new, 'ABORT: 盘上字节 != 预期终态'
pl, cl = cur.splitlines(), chk.splitlines()
assert len(cl) == len(pl), 'ABORT: 行数变了（本遍只动一行）%d -> %d' % (len(pl), len(cl))
d = [l for l in difflib.unified_diff([x.decode('utf-8') for x in pl], [x.decode('utf-8') for x in cl],
                                     lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
assert len(d) == 2, 'ABORT: 差异不是「一行换一行」而是 %d 行：%s' % (len(d), [x[:40] for x in d])
post = _lines(_raw_porcelain(), False)
pm2, pu2, po2 = buckets(post)
assert not po2 and len(post) == len(pm2) + len(pu2), 'ABORT: 写盘后桶不完备 %s' % po2
print('PROOF 行数 %d 不变 / difflib 恰好 1 换 1 / pre-image %s（%s B）逐字等 / CRLF %d == LF %d / 盘上 == 预期' % (
    len(cl), os.path.basename(PRE), format(len(cur), ','), chk.count(b'\r'), chk.count(b'\n')))
print('CORRECTED 第一遍 %d 行 / ` M` %d ⇒ 订正为 %d 行 / ` M` %d（写盘后再跑一把 = %d 行 / ` M` %d，todo.md 自己已在 ` M` 桶里）' % (
    v1[0], v1[1], len(por), len(mods), len(post), len(pm2)))
print('MD5 %s -> %s / %s B -> %s B' % (hashlib.md5(cur).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8],
                                     format(len(cur), ','), format(len(chk), ',')))

_car = os.path.join(EV, 'r61c_todo19_fix_%s.txt' % _tt)
assert not os.path.exists(_car), 'ABORT: 载体目标已存在 ' + _car
io.open(_car, 'wb').write((
    'todo.md 第十九遍订正遍，现跑于 %s\n' % _T0.strftime('%Y-%m-%d %H:%M:%S') +
    'DEFECT 取数助手里的 .strip() 吃掉 `git status --porcelain` 首行前导空格 ⇒ 按前两个字符分桶时 ` M` 恒少计 1（`??` 不带前导空格，不受影响）\n' +
    'V1-ON-DISK %d 行 / ` M` %d + `??` %d（桶和 %d != 总数 %d，当时"总数 == 各桶之和"没有执行者）\n' % (
        v1[0], v1[1], v1[2], v1[1] + v1[2], v1[0]) +
    'RULER 新尺 %d 行 / ` M` %d + `??` %d（assert 桶完备）· 旧尺同输入打出 ` M` %d ⇒ 阳性对照：少 1 已在现场复现，不是事后编的成因\n' % (
        len(por), len(mods), len(uns), len(b_mods)) +
    'CORRECTED %d 行 / ` M` %d + `??` %d（写盘后再跑 %d 行 / ` M` %d）\n' % (
        len(por), len(mods), len(uns), len(post), len(pm2)) +
    'PRE-IMAGE todo19_pre_fix_%s.md（%s B / %d 行）写盘前原件逐字等\n' % (_tt, format(len(cur), ','), len(pl)) +
    'PROOF 行数不变（%d）/ difflib 恰好 1 换 1 / 盘上字节 == 预期终态 / CRLF 两把尺同值 / 反引号成对 / 撇号 0 / 占位符 0\n' % len(cl) +
    'MD5 %s -> %s\n' % (hashlib.md5(cur).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]) +
    'VERDICT=LANDED rc=0\n').encode('utf-8'))
assert io.open(_car, 'rb').read().endswith('VERDICT=LANDED rc=0'.encode('utf-8')), 'ABORT: 载体末行不是写盘后令牌'
print('CARRIER %s（%d B）' % (os.path.basename(_car), len(io.open(_car, 'rb').read())))
print('VERDICT=LANDED rc=0')
