# todo.md 第十九遍订正遍的**复核 + 补载体**（第二遍）。
# 为什么要第三只脚本：上一遍（`land_r61c_todo19fix.py`）**已把订正落进盘**并打印了全部证明，
# 但红在自己最后一步——载体末行断言写成 `endswith('VERDICT=LANDED rc=0')`，而载体本身以换行收尾 ⇒ 恒假。
# 这是"载体/凭证的断言写法"那一族的新形态（末行与换行收尾），去向 = `FreqErr.md` 第二十批。
# 本遍：①现跑两把尺（strip / 不 strip）再复现一次「少计 1」；②拿上一遍的 pre-image 与盘上现件**重新**跑 difflib 证明
# （不是抄上一遍的打印）；③把上一遍那只缺末行令牌的载体逐字点名，另落一只完整载体。
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
TOKEN = 'VERDICT=LANDED rc=0'
_T0 = datetime.datetime.now()
_tt = _T0.strftime('%Y%m%d_%H%M%S')


def _raw():
    r = subprocess.run(['git', '-c', 'core.quotePath=false', 'status', '--porcelain'], cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT: git status 退出码非 0'
    return r.stdout.decode('utf-8', 'replace')


def _lines(text, do_strip):
    t = text.strip() if do_strip else text
    return [l for l in t.split('\n') if l]


def buckets(ls):
    return ([l for l in ls if l[:2] == ' M'], [l for l in ls if l[:2] == '??'],
            sorted(set(l[:2] for l in ls if l[:2] not in (' M', '??'))))


_raw = _raw()
por = _lines(_raw, False)
mods, uns, other = buckets(por)
assert not other and len(por) == len(mods) + len(uns), 'ABORT: 新尺桶不完备（%s）' % other
b_mods, b_uns, _ = buckets(_lines(_raw, True))
assert len(b_mods) == len(mods) - 1 and len(b_uns) == len(uns), \
    'ABORT: 旧尺没复现出少计 1（旧 %d / 新 %d）' % (len(b_mods), len(mods))
print('RULER 新尺 %d 行（` M` %d + `??` %d）/ 旧尺 strip 打出 ` M` %d ⇒ 少 1 现场复现（第二遍独立再跑）' % (
    len(por), len(mods), len(uns), len(b_mods)))

pre_p = sorted(glob.glob(os.path.join(EV, 'todo19_pre_fix_*.md')))
assert len(pre_p) == 1, 'ABORT: 上一遍 pre-image 候选不唯一（%d 只）：%s' % (len(pre_p), pre_p)
pre = io.open(pre_p[0], 'rb').read()
chk = io.open(TOD, 'rb').read()
pl, cl = pre.splitlines(), chk.splitlines()
assert len(cl) == len(pl), 'ABORT: 行数不等（%d vs %d）⇒ 上一遍那句「只动一行」在本遍不可复现' % (len(pl), len(cl))
d = [l for l in difflib.unified_diff([x.decode('utf-8') for x in pl], [x.decode('utf-8') for x in cl],
                                     lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
assert len(d) == 2, 'ABORT: 差异不是 1 换 1 而是 %d 行' % len(d)
assert chk.count(b'\r') == chk.count(b'\n') == len(cl), 'ABORT: 现件 CRLF 两把尺不同值'
assert '**订正（现跑于 ' in chk.decode('utf-8') and TOKEN.encode('utf-8') not in chk, 'ABORT: 现件里没有订正句'
v1 = re.search(r'第一遍那句写的是 (\d+) 行 / ` M` (\d+)', chk.decode('utf-8'))
assert v1, 'ABORT: 订正句里读不到第一遍那两个数 ⇒ 引文不在盘上'
print('PROVE(独立再跑) %s（%s B / %d 行）-> todo.md（%s B / %d 行）：行数等 / difflib 恰好 1 换 1 / CRLF 同值 / 第一遍那句 %s 行 ` M` %s 已在正文里逐字在册' % (
    os.path.basename(pre_p[0]), format(len(pre), ','), len(pl), format(len(chk), ','), len(cl), v1.group(1), v1.group(2)))

bad = sorted(p for p in glob.glob(os.path.join(EV, 'r61c_todo19_fix_*.txt')))
assert bad, 'ABORT: 上一遍的载体一只都不在 ⇒ 它到底落没落盘无从证明'
# 判据换成"现读末行"，且**两种形态分别点名**：末行 == 令牌 / 令牌在正文任一行 / 全都没有。
# 上一遍的红在 `endswith(TOKEN)`（载体以换行收尾 ⇒ 恒假），但那只断言**读的是回读字节**，
# 而字节里令牌一直都在 ⇒ "载体缺令牌"这个归类是我在**没现读**的情况下写进本遍判据的（同族第 3 起）。
def last_line(p):
    ls = [l for l in io.open(p, 'rb').read().decode('utf-8', 'replace').split('\n') if l]
    return ls[-1] if ls else ''


def has_token(p):
    return any(TOKEN in l for l in io.open(p, 'rb').read().decode('utf-8', 'replace').split('\n'))


has_last = [p for p in bad if last_line(p) == TOKEN]
has_body = [p for p in bad if p not in has_last and has_token(p)]
has_none = [p for p in bad if p not in has_last and p not in has_body]
assert len(bad) == len(has_last) + len(has_body) + len(has_none), 'ABORT: 载体三分类不完备'
assert not has_none, 'ABORT: 真缺令牌的载体 %s，本遍才需要补写' % has_none
print('PRIOR-CARRIER 上一遍 %d 只载体逐只现读：**末行就是令牌** %d 只（%s）/ 令牌只在正文 %d 只 / 全缺 %d 只'
      ' ⇒ 本窗先前那句「上一遍载体缺末行令牌」是**未现读写进判据的假事实**（同族第 3 起）' % (
          len(bad), len(has_last), '、'.join('`%s`' % os.path.basename(p) for p in has_last), len(has_body), len(has_none)))

_car = os.path.join(EV, 'r61c_todo19_fix2_%s.txt' % _tt)
assert not os.path.exists(_car), 'ABORT: 载体目标已存在 ' + _car
body = (
    'todo.md 第十九遍订正遍的复核 + 补载体，现跑于 %s\n' % _T0.strftime('%Y-%m-%d %H:%M:%S') +
    'DEFECT-2 上一遍的红在载体末行断言：endswith(TOKEN) 而载体以换行收尾 ⇒ 恒假。崩在**记账那一步**，不在落盘：\n'
    '        todo.md 当时已被订正（本遍拿它的 pre-image 独立再跑 difflib 证明 = 1 换 1 / 行数等 / CRLF 同值）\n' +
    'PRIOR-CARRIER 上一遍 %d 只载体逐只现读末行：%s ⇒ 末行**就是** %s（缺令牌 0 只）\n' % (
        len(bad), '、'.join(os.path.basename(p) for p in bad), TOKEN) +
    'DEFECT-3 本遍起初把上一遍载体归类成「缺末行令牌」并据此要补写 —— 那是**没现读末行**就写死的期望，\n'
    '        现读推翻：令牌一直都在。判据已换成「末行 == 令牌 / 只在正文 / 全缺」三分类 + 完备性 assert（同族第 3 起）\n' +
    'RULER 新尺 %d 行 / ` M` %d + `??` %d（桶完备）· 旧尺（strip）` M` %d ⇒ 少 1 独立复现\n' % (
        len(por), len(mods), len(uns), len(b_mods)) +
    'V1-IN-BODY 第一遍那句 = %s 行 / ` M` %s（正文逐字在册，本遍现读）\n' % (v1.group(1), v1.group(2)) +
    'MD5 pre %s -> now %s / %s B -> %s B\n' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8],
                                             format(len(pre), ','), format(len(chk), ',')) +
    'NOTE 本遍**不改盘上 todo.md**（它已被上一遍订正到位），只落这只复核载体；'
    '上一遍那两只（含令牌的载体 + 已订正的正文）都原样留着，零删除\n')
io.open(_car, 'wb').write((body + TOKEN + '\n').encode('utf-8'))
_back = io.open(_car, 'rb').read()
assert _back == (body + TOKEN + '\n').encode('utf-8'), 'ABORT: 载体回读不等'
assert _back.rstrip(b'\n').endswith(TOKEN.encode('utf-8')), 'ABORT: 补写的载体自己也没有末行令牌（同族第 2 次就别怪尺了）'
print('CARRIER %s（%d B / md5 前 8 %s）' % (os.path.basename(_car), len(_back), hashlib.md5(_back).hexdigest()[:8]))
print(TOKEN)
