# 第 13 代同步的双向差集 + 包↔工作树差集 + 行尾前置读数，一次跑完。
# 派生自 `scripts/r54_listdiff.py`，改动三处：①三只输入/两只输出全部换成本代名字；
# ②**输入/输出都取仓库 evidence/**（§38.18 缺陷一）；③本脚本自跑 rc 与输出路径同批落盘（(65) 那条：裁决同时落 stdout 与退出码）。
# 继承不动的口径：两侧先剥 \r 再比（(56)）、名单为空即 ABORT（R49 P2-3）、子进程显式给编码不靠环境。
import datetime
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
EV = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence')
OUT = os.path.join(EV, 'r55_listdiff.txt')


def eol(p):
    b = open(p, 'rb').read()
    n = b.count(b'\n')
    c = b.count(b'\r\n')
    return 'bytes=%d lines=%d CRLF=%d bareLF=%d BOM=%s' % (len(b), n, c, n - c, b[:3] == b'\xef\xbb\xbf')


loc = os.path.join(EV, 'r55_local_names.txt')
ver = os.path.join(EV, 'r55_verify.txt')
rem = os.path.join(EV, 'r55_remote_names.txt')
for p in (loc, ver):
    if not os.path.isfile(p):
        print('ABORT: 输入取证件不存在（先跑 sync_r55.py / r55_upload.ps1）', p)
        sys.exit(1)
if os.path.exists(OUT):
    print('ABORT: 取证件已存在，不覆盖', OUT)
    sys.exit(1)

raw = open(ver, 'rb').read()
keep, inside = [], False
for line in raw.split(b'\n'):
    s = line.rstrip(b'\r')
    if s == b'REMOTE_NAMES_BEGIN':
        inside = True
        continue
    if s == b'REMOTE_NAMES_END':
        inside = False
        continue
    if inside and s:
        keep.append(s)
# 只落"剥完 \r 的名单"这一种形态：原始远端字节的行尾读数取自 r55_verify.txt 本体（那才是传输产物），
# 不另存一份"我用 \r\n 重新写出来的 raw"——那是一把自造的尺子，不是前置读数。
open(rem, 'wb').write(b'\n'.join(keep) + b'\n')

# 本行第一版写的是 `l.rstrip(b'\r')` —— 漏掉行尾那个 `\n` ⇒ 本地 287 只全成了 `.gitignore\n` 这种形状，
# 当场造出 287/287 假差集（与 (56) 同族，当时栽在**那一代新写的差集脚本**自己身上（本文件是逐字派生的产物，这句说的是它的祖先、不是本代），泄密线索同样是点名列表里的字面 `\r\n`）。
lr = sorted(l.rstrip(b'\r\n').decode('utf-8') for l in open(loc, 'rb') if l.strip())
rr = sorted(x.decode('utf-8') for x in keep)
# 09-24 R49 复查 P2-3：两侧都空时 ONLY_IN_LOCAL=0/ONLY_IN_REMOTE=0 与"全等"逐字同形 ⇒ 空名单不是证据。
if not lr or not rr:
    print('ABORT: 名单为空 LOCAL=%d REMOTE=%d，差集无意义（不写输出）' % (len(lr), len(rr)))
    sys.exit(1)
only_l = sorted(set(lr) - set(rr))
only_r = sorted(set(rr) - set(lr))
if only_l or only_r:
    print('注意：本脚本**不截断**点名列表（(82) 半截取证那条），下面把两侧名单整段写出。')

d = subprocess.run(['python', os.path.join(REPO, 'hardware/ht305_sync/scripts/r55_cutoff_delta.py')],
                   capture_output=True, text=True, encoding='utf-8',
                   # 09-24 10:4x 首跑崩在这里：子进程按 GBK 往管道打印中文（`identical(包内…` 那行），
                   # 父进程以 utf-8 解码 ⇒ UnicodeDecodeError ⇒ d.stdout 为 None ⇒ 下一段 rstrip 报 AttributeError。
                   # 修法是显式给子进程定编码，**不依赖调用方 shell 里恰好有 PYTHONUTF8=1**（那种"能跑"是环境给的，不是脚本给的）。
                   env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
assert d.stdout is not None, 'ABORT: 子进程无输出（解码失败时 stdout 为 None，不许拿 None 当空串往下写）'
assert d.returncode == 0, 'ABORT: 子进程 rc=%d %s' % (d.returncode, (d.stderr or '')[-400:])
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
verdict = 'VERDICT=LISTDIFF_EQUAL' if (not only_l and not only_r) else 'VERDICT=LISTDIFF_MISMATCH'
lines = ['第 13 代同步（r55final）双向差集 + 行尾前置读数，现跑于 %s' % now,
         '口径：两侧先剥 \\r 再比（(56) 那条），行尾原样登记在下一段，不事后归一。',
         'EOL  LOCAL %s' % eol(loc),
         'EOL  REMOTE(剥后名单) %s' % eol(rem),
         'EOL  VERIFY(远端 stdout 落盘原件，差集就是从它切的) %s' % eol(ver),
         'LOCAL_LINES=%d REMOTE_LINES=%d' % (len(lr), len(rr)),
         'ONLY_IN_LOCAL=%d %s' % (len(only_l), only_l),
         'ONLY_IN_REMOTE=%d %s' % (len(only_r), only_r),
         '', '--- 包 ↔ 工作树差集（r55_cutoff_delta.py 同批现跑）---',
         d.stdout.rstrip(),
         '', verdict]
txt = '\n'.join(lines) + '\n'
open(OUT, 'w', encoding='utf-8').write(txt)
print(txt)
print('OUT', OUT, 'RC', d.returncode, verdict)
sys.exit(0 if verdict == 'VERDICT=LISTDIFF_EQUAL' else 1)
