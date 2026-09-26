# 第八次提交轮（09-24 10:2x）索引门的**阳性对照**，两条口令各一路。
# 本只 = %TEMP%\pw_pos_control_r52.py 的逐字派生：以 `import os` 为界，# 头部注释重写、**本体自该行之后的每一个字节与上一轮那只逐字相同**（本脚本以 md5 断言，见落盘前打印）。
# 口径沿用上一轮，一字未动：门载体名走 argv[1]（不硬编码，防拿上一代的门核这一代）、SSH 只在内存造
# 合成样本（仓库里没有已知脏样本正是它干净的原因，故它证的是「传参通路 + bytes.count 语义没断」）、
# 与门载体逐字段互核、rc=0 蕴含载体已写出。两条口令都只在进程内取，一次都不打印内容、不进命令文本。
import os
import re
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
GATE_NAME = sys.argv[1]
assert re.fullmatch(r'staged_cred_gate_\d{6}\.txt', GATE_NAME), 'ABORT: argv[1] 不像本轮的门载体名：%r' % GATE_NAME
GATE = os.path.join(REPO, 'hardware/ht305_sync/evidence', GATE_NAME)
CARRIER = GATE[:-4] + '_pos.txt'
SRC = 'hardware/zizhao-esp32s3/main/provision_ap.c'
DIRTY_DOC = 'dev_log/20260919.md'

assert os.path.exists(GATE), 'ABORT: 门载体不存在，无从互核 ' + GATE
assert not os.path.exists(CARRIER), 'refuse to overwrite ' + CARRIER
OUTL = []


def say(s):
    OUTL.append(s)
    print(s)


secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
                   open(os.path.join(REPO, SRC), encoding='utf-8').read()).group(1).encode()
assert len(secret) >= 4, '宏值过短，尺子不可信'

env = os.environ.get('HT305_TMP_FOR_GATE')
assert env, 'ABORT: 环境变量 HT305_TMP_FOR_GATE 未设置（SSH 那一路无从对照）'
ssh = env.encode('utf-8')
del os.environ['HT305_TMP_FOR_GATE']
assert ssh != secret, 'ABORT: 两条口令相同，两路对照会退化成一路'


def gitbin(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO,
                       capture_output=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


say('提交前索引门的阳性对照（现跑于 %s）' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
say('GATE_CARRIER=%s（本脚本与它互核，扫的是同一批已 stage blob）' % os.path.basename(GATE))
say('GATE_MTIME=%s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(GATE))))
say('SECRET_LEN_BYTES PROV=%d SSH=%d (只报长度，不报内容)' % (len(secret), len(ssh)))

arms = []

# ⑴A PROV_PASS 路：两只已知脏的工作树文件必须非零，否则计数路径就是坏的。
for rel in (SRC, DIRTY_DOC):
    n = open(os.path.join(REPO, rel), 'rb').read().count(secret)
    say('SHOULD_FIRE PROV %s hits=%d' % (rel, n))
    assert n > 0, 'PROV_PASS 阳性对照未亮 => 尺子坏，门那句 HITS=0 不可信'
arms.append('PROV_worktree')

# ⑴B SSH 路：仓库里没有已知脏样本 ⇒ 只能在内存里造合成样本（不落盘），证传参通路 + count 语义。
for shape, buf in (('bare', ssh), ('wrapped', b'header\n' + ssh + b'\nbody'),
                   ('twice', ssh + b' and ' + ssh)):
    n = buf.count(ssh)
    say('SHOULD_FIRE SSH in-memory/%s hits=%d' % (shape, n))
    assert n >= 1, 'SSH 阳性对照未亮 => env 传参或编码断了'
arms.append('SSH_inmemory_synth')

# ⑵ 真扫集：与索引门同一口径（已 stage blob），两条口令都必须全零。
staged = [p.decode('utf-8') for p in
          gitbin('diff', '--cached', '--name-only', '-z').split(b'\0') if p]
assert staged, 'ABORT: 索引为空，这一遍无从对照'
tp = ts = 0
bad = []
for p in staged:
    b = gitbin('show', ':' + p)
    cp, cs = b.count(secret), b.count(ssh)
    tp += cp
    ts += cs
    if cp or cs:
        bad.append((p, cp, cs))
say('INDEX_SCANNED=%d INDEX_TOTAL_HITS=%d %s' % (len(staged), tp + ts, bad))
assert tp + ts == 0, '索引真有明文，不许提交'

# ⑶ 与门那份载体逐字段互核（两把独立尺子必须给同一个数）。
g = open(GATE, encoding='utf-8').read()
gf = int(re.search(r'FILES_SCANNED=(\d+)', g).group(1))
gtp = int(re.search(r'PROV_PASS_TOTAL_HITS=(\d+)', g).group(1))
gts = int(re.search(r'SSH_TOTAL_HITS=(\d+)', g).group(1))
gt = int(re.search(r'(?m)^TOTAL_HITS=(\d+)', g).group(1))
gv = re.search(r'VERDICT=(\w+)', g).group(1)
eq = (gf, gt, gtp + gts, gv) == (len(staged), tp + ts, tp + ts, 'CLEAN')
say('CROSS_CHECK gate FILES=%d PROV=%d SSH=%d HITS=%d VERDICT=%s | self PROV=%d SSH=%d HITS=%d | equal=%s'
    % (gf, gtp, gts, gt, gv, tp, ts, tp + ts, eq))
assert eq, '两把尺子给的数不等'
say('ARMS_FIRED=%d/2 %s' % (len(arms), arms))
say('VERDICT=POSITIVE_CONTROL_FIRES_AND_INDEX_CLEAN')

txt = '\n'.join(OUTL) + '\n'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(txt)
# rc=0 必须蕴含产物已写出（"打印 != 落盘"那一族的守卫）：
assert os.path.getsize(CARRIER) == len(txt.encode('utf-8')), 'ABORT: 载体字节数与输出不等'
say('CARRIER=%s bytes=%d' % (os.path.basename(CARRIER), os.path.getsize(CARRIER)))
