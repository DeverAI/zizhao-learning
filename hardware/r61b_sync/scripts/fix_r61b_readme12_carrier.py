# 订正 README 第十二格的载体行：落地遍 rc=1 没写出载体，那一行引的载体名当时并不存在。
# 这是"替换一行"（行数不变），所以证明可以用逐位置差集 —— 恰 1 行。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
os.chdir(REPO)
EV = os.path.join('hardware', 'r61b_sync', 'evidence')
README = 'backups/README.md'
T0 = datetime.now()
OUTL = []


def say(s):
    OUTL.append(s)
    print(s)


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a),
                       capture_output=True, shell=False)
    assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')
    return r.stdout.decode('utf-8', 'replace')


# 现读：本代已存在的 proof 载体，且必须逐只现读它的 VERDICT 行（不猜哪只是权威）
profs = []
for f in sorted(os.listdir(EV)):
    if not re.match(r'^r61b_readme12_proof_\d+\.txt$', f):
        continue
    t = open(os.path.join(EV, f), encoding='utf-8').read()
    v = re.search(r'VERDICT=(\w+) rc=0', t)
    profs.append((f, v.group(1) if v else 'NONE'))
assert len(profs) >= 1, 'ABORT: 一只 proof 载体都没有，订正就没有依据'
authority = [f for f, v in profs if v == 'PROOF_ONLY_OK']
assert len(authority) == 1, 'ABORT: PROOF_ONLY_OK 的权威载体应恰 1 只，实测 %d' % len(authority)
named = ['%s(%s)' % (f, v) for f, v in profs]
pre_imgs = sorted(f for f in os.listdir(EV) if re.match(r'^readme_pre12_\d{8}_\d{6}\.md$', f))
assert len(pre_imgs) == 1, 'ABORT: 原件快照应恰 1 只，实测 %d' % len(pre_imgs)

# 现读：复核遍的 status 行数（它就在 proof 载体里）
pt = open(os.path.join(EV, authority[0]), encoding='utf-8').read()
rev_now = int(re.search(r'REVLIST \d+ STATUS_LINES (\d+)', pt).group(1))
drift = re.search(r'STATUS_DRIFT (\d+) -> (\d+) / 差 (\d+)；[^=]*= (\d+)：\[(.*)\]', pt)
assert drift, 'ABORT: proof 载体里读不到那条归因行'
d_from, d_to, d_diff, d_n, d_names = (int(drift.group(1)), int(drift.group(2)),
                                      int(drift.group(3)), int(drift.group(4)), drift.group(5))
assert d_to - d_from == d_diff == d_n, 'ABORT: 那条归因行自身的三个数不自洽'
assert len([x for x in d_names.split(', ') if x.strip()]) == d_n, 'ABORT: 归因名单只数与差值不等'

rb0 = open(README, 'rb').read()
assert rb0.count(b'\r\n') == 0 and rb0[-1:] == b'\n', 'ABORT: README 行尾口径变了，先停下'
lines0 = rb0.decode('utf-8').split('\n')
tgt = [i for i, l in enumerate(lines0)
       if l.startswith('（载体：本格 ①~⑬ 全部现跑读数 = ') and '第十二次读数' not in l]
assert len(tgt) == 1, 'ABORT: 要订正的载体行应恰 1 行，实测 %d' % len(tgt)
i0 = tgt[0]
assert 'r61b_readme12_land_' in lines0[i0], 'ABORT: 那一行不含待订正的假载体名'
secret = re.search(rb'#define\s+PROV_PASS\s+"([^"]+)"',
                   open(os.path.join('hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c'), 'rb').read()).group(1)

NEW = ('（载体：本格 ①~⑬ 的现跑读数**分两遍才落齐**。落地遍 `land_r61b_readme12.py` **rc=1 且没写出载体**——它写盘后的证明段用的是"逐位置比两代行"，'
       '纯插入会把插入点之后每一行都错位，于是**盘上内容是对的而证明全红**（这一族登记进 FreqErr 第十八批）；修好的三段式证明（前缀逐字等 + 插入段逐行等 + 后缀逐字等）'
       '由同一只脚本的 `--proof-only` 遍跑在真字节上，本代该遍载体共 %d 只：%s，权威那只是 `%s`。'
       '写盘前的 README 原件快照 = `%s`（md5 前 8 位 `%s`）。'
       '⑫ 那格的 `status --porcelain` 行数是**落地那一刻**（%d 行）的快照，复核遍现读 %d 行，差 %d 只由本遍自己在 `hardware/r61b_sync/evidence/` 新落的 %d 只载体精确解释（逐只点名：%s）——'
       '这条归因由脚本 assert 把关，不是事后解释。'
       '**本格在本代被动两次**（插入 → 本遍订正载体行），两遍都没覆写任何旧格、零删除。）')

NEWL = NEW % (len(profs), '、'.join('`%s`' % x for x in named), authority[0], pre_imgs[0],
              hashlib.md5(open(os.path.join(EV, pre_imgs[0]), 'rb').read()).hexdigest()[:8],
              d_from, rev_now, d_diff, d_n, d_names.replace("'", ''))
assert secret not in NEWL.encode('utf-8'), 'ABORT: 正文含口令'
assert NEWL.count(chr(92)) == 0, 'ABORT: 正文含反斜杠'
assert '%d' not in NEWL and '%s' not in NEWL, 'ABORT: 正文含未解析哨兵'
# 前置钉：被订正的那句里的两个现场态数必须是现读来的，不是手抄
assert ('%d 行' % rev_now) in NEWL and ('%d 行）' % d_from) in NEWL, 'ABORT: 现读值没进正文'

lines1 = list(lines0)
lines1[i0] = NEWL
ob = '\n'.join(lines1).encode('utf-8')
open(README, 'wb').write(ob)

rb1 = open(README, 'rb').read()
assert rb1 == ob, 'ABORT: 盘上字节与预期串不等'
chk = rb1.decode('utf-8').split('\n')
assert len(chk) == len(lines0), 'ABORT: 替换遍不该改行数（%d -> %d）' % (len(lines0), len(chk))
diff = [i for i in range(len(lines0)) if chk[i] != lines0[i]]
assert diff == [i0], 'ABORT: 差集应恰为被订正那一行，实测 %s' % diff
assert chk[i0] == NEWL, 'ABORT: 订正行未逐字落盘'
assert rb1.count(b'\r\n') == 0 and rb1[-1:] == b'\n', 'ABORT: 写盘造出了 CR 或丢了末行换行'
for anchor in ('## 2. 命名规则', '【09-26 ', '第十二次读数'):
    assert rb1.decode('utf-8').count(anchor) >= 1, 'ABORT: 结构锚 %s 不在了' % anchor

say('README bytes %d -> %d / lines %d（替换 1 行 @%d）' % (len(rb0), len(rb1), len(chk), i0 + 1))
say('PROOF_CARRIERS %s / AUTHORITY=%s' % (named, authority[0]))
say('STATUS %d -> %d / DRIFT %d == 新增取证 %d' % (d_from, rev_now, d_diff, d_n))
say('VERDICT=CARRIER_LINE_FIXED rc=0')

txt = '\n'.join(OUTL) + '\n'
CARRIER = os.path.join(EV, 'r61b_readme12_carrier_fix_%s.txt' % T0.strftime('%H%M%S'))
assert not os.path.exists(CARRIER), 'ABORT: 载体已存在'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(txt)
assert os.path.getsize(CARRIER) == len(txt.encode('utf-8')), 'ABORT: 载体字节数与输出不等'
print('CARRIER', CARRIER, os.path.getsize(CARRIER))
