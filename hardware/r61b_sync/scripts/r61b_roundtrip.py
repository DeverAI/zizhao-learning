# 第 15 代往返复核：派生自 `hardware/r61_sync/scripts/r61_roundtrip.py`（第 14 代）。
# 改动三处：①TOP/REMOTE 换代（zizhao_20260926_r61bfinal / zsynctest17）；
# ②报告落进 `hardware/r61b_sync/evidence/`，并新装守卫：解析路径含 `ht305_sync` 即 ABORT
#   （那边停在 gen 24 的 SEAL，本代不新建清单代 ⇒ 不落派生字节日）；
# ③阴性对照件换成本代真实存在、且按宏名读口令的脚本 `scripts/sync_r61b.py`，"对照件不存在即 ABORT" 原样保留
#   （(63) 那族：读一只不存在的载体 ⇒ 读数全绿）。
# 抓回来的**带明文原件**仍留 %TEMP%：**绝不进仓库**（它带 PROV_PASS 宏值，进去等于把明文复制进 git 侧）。
# 口令只从宏本体现读、只打计数与摘要，绝不打印内容。
import datetime
import hashlib
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TMP = os.environ.get('TEMP', 'C:/Users/david/AppData/Local/Temp')
REL = 'hardware/zizhao-esp32s3/main/provision_ap.c'
TOP = 'zizhao_20260926_r61bfinal'
REMOTE = 'ht305:C:/Users/Administrator/AppData/Local/Temp/zsynctest17/' + TOP + '/' + REL
FETCH = os.path.join(TMP, 'r61b_remote_provision_ap.c')
CTRL = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts', 'sync_r61b.py')

_ev = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
for _p in (_ev, REMOTE, CTRL):
    if 'ht305_sync' in _p:
        raise SystemExit('ABORT: 路径指进了封存归档目录 ' + _p)

# 输出名不许占用已存在的载体：首跑失败的读数**留在盘上**，后继跑另起一只，并在里面点名前一只。
# （直接覆写 = 把"这次没跑成"洗成"从来就是绿的"，(75) 那条不许拿重跑链洗绿的同一族。）
_cands = ['r61b_roundtrip.txt'] + ['r61b_roundtrip_%d.txt' % i for i in range(2, 10)]
_prior = None
for _c in _cands:
    if not os.path.exists(os.path.join(_ev, _c)):
        OUT = os.path.join(_ev, _c)
        break
    _prior = _c
else:
    raise SystemExit('ABORT: r61b_roundtrip 载体名 9 只全被占，先人工看首只')

if os.path.exists(FETCH):
    print('ABORT: 抓回件已存在，不覆盖', FETCH)
    sys.exit(1)
if not os.path.isfile(CTRL):
    print('ABORT: 阴性对照件不存在，这一把尺没有样本：' + CTRL)
    sys.exit(1)


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


lines = ['R61_ROUNDTRIP_AT=' + now(), 'REMOTE=' + REMOTE]
if _prior:
    lines.append('PRIOR_ATTEMPT=evidence/%s（那一只的读数不作数，本只是重跑；两只都留在盘上，见脚本头部注释）' % _prior)
    lines.append('PRIOR_VERDICT=%s' % [l for l in open(os.path.join(_ev, _prior), encoding='utf-8')
                                       if l.startswith('VERDICT=')][0].strip())
env = dict(os.environ)
env['SSH_ASKPASS'] = r'C:\Users\david\.ssh\_askpass_ht305.cmd'
env['SSH_ASKPASS_REQUIRE'] = 'force'
env['DISPLAY'] = ':0'
# 瞬时失败不再要人重跑整脚本：原地重试一次，两次的 rc 与 **stderr 正文**都登记（gen 13 那遍 255 的教训）。
attempts = []
for i in (1, 2):
    p = subprocess.run(['scp', '-o', 'StrictHostKeyChecking=accept-new', REMOTE, FETCH],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    attempts.append((i, p.returncode, p.stderr))
    lines += ['SCP_ATTEMPT=%d RC=%d STDERR_LINES=%d' % (i, p.returncode, len(p.stderr.splitlines()))]
    for s in p.stderr.splitlines():
        lines.append('  STDERR%d| %s' % (i, s))
    if p.returncode == 0 and os.path.isfile(FETCH):
        break
    if i == 1:
        import time
        time.sleep(3)
if attempts[-1][1] != 0 or not os.path.isfile(FETCH):
    lines.append('VERDICT=SCP_FAILED')
    open(OUT, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1)

rb = open(FETCH, 'rb').read()
lb = open(os.path.join(REPO, REL.replace('/', os.sep)), 'rb').read()
sec = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', lb).group(1)
lines += [
    'REMOTE_BYTES=%d md5=%s' % (len(rb), hashlib.md5(rb).hexdigest()),
    'LOCAL_BYTES=%d md5=%s' % (len(lb), hashlib.md5(lb).hexdigest()),
    'BYTE_EQUAL_TO_WORKTREE=%s' % (rb == lb),
    'PROV_PASS_HITS_REMOTE=%d' % rb.count(sec),
    'PROV_PASS_HITS_LOCAL=%d' % lb.count(sec),
    'MACRO_LINE_REMOTE=%d' % len(re.findall(rb'#define\s+PROV_PASS', rb)),
    'RAN_END_AT=' + now(),
]
# 阴性对照：同一把尺子在一个**已知不含**该串的文件上必须数出 0，否则"命中 1"不说明任何事。
ctrl = open(CTRL, 'rb').read()
lines.append('CONTROL_LANDER_HITS=%d (应 0；这只文件按宏名读口令、不含宏值)' % ctrl.count(sec))
# 阳性对照：同一把尺在**已知含**该串的工作树原件上必须数出 >0，否则 0 命中什么都不能排除。
lines.append('POSITIVE_CONTROL_WORKTREE_HITS=%d (应 >0)' % lb.count(sec))
lines.append('VERDICT=' + ('REMOTE_CARRIES_PLAINTEXT' if rb.count(sec) else 'REMOTE_CLEAN_UNEXPECTED'))
txt = '\n'.join(lines) + '\n'
open(OUT, 'w', encoding='utf-8', newline='').write(txt)
print(txt)
