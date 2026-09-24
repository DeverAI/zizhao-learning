# 第 8 代补、第 11 代仍在跑的一条**更强口径**：把远端**解包后**的那只带明文源文件 scp 回本机，逐字节比 + 就地数口令。
# 动机（README"没做"一节第 6 代起就登记着的那格）：第 4/6 代扫的是解包后的落盘物，第 7 代只扫了打包前的暂存树 ⇒ 弱一档。
# 本脚本自第 8 代起每代都跑，让"远端那份带明文"这一句始终拿到**从远端带回的字节**作依据（本代 = 第 11 代），而不是靠"包 == 工作树"传递。
# 口令只从宏本体现读、只打计数与摘要，绝不打印内容；抓回来的原件留在 %TEMP%，**不进仓库**。
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
TOP = 'zizhao_20260924_r53final'
REMOTE = 'ht305:C:/Users/Administrator/AppData/Local/Temp/zsynctest13/' + TOP + '/' + REL
FETCH = os.path.join(TMP, 'r53_remote_provision_ap.c')
OUT = os.path.join(TMP, 'r53_roundtrip.txt')

if os.path.exists(FETCH):
    print('ABORT: 抓回件已存在，不覆盖', FETCH)
    sys.exit(1)


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


lines = ['R53_ROUNDTRIP_AT=' + now(), 'REMOTE=' + REMOTE]
env = dict(os.environ)
env['SSH_ASKPASS'] = r'C:\Users\david\.ssh\_askpass_ht305.cmd'
env['SSH_ASKPASS_REQUIRE'] = 'force'
env['DISPLAY'] = ':0'
p = subprocess.run(['scp', '-o', 'StrictHostKeyChecking=accept-new', REMOTE, FETCH],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
lines += ['SCP_RC=%d' % p.returncode, 'SCP_STDERR_LINES=%d' % len(p.stderr.splitlines())]
if p.returncode != 0 or not os.path.isfile(FETCH):
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
ctrl = open(os.path.join(REPO, 'hardware/ht305_sync/scripts/land_r53_evidence.py'), 'rb').read()
lines.append('CONTROL_LANDER_HITS=%d (应 0；这只文件按宏名读口令、不含宏值)' % ctrl.count(sec))
lines.append('VERDICT=' + ('REMOTE_CARRIES_PLAINTEXT' if rb.count(sec) else 'REMOTE_CLEAN_UNEXPECTED'))
txt = '\n'.join(lines) + '\n'
open(OUT, 'w', encoding='utf-8', newline='').write(txt)
print(txt)
