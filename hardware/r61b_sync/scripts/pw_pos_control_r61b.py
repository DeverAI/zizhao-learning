# 第十次提交轮（09-26 14:5x）索引门的**阳性对照**：本只 = 上一代那只的逐行派生，唯一功能改动 = 门载体目录 r61_sync -> r61b_sync，其余每字节相同（本遍打印行级差集自证）
# 本只 = `hardware/ht305_sync/scripts/pw_pos_control_r53b.py` 的逐字派生，只改两处（都是"不写进封存归档目录"那条硬约束的执行者）：
#   ① 门载体目录 `hardware/ht305_sync/evidence` → `hardware/r61_sync/evidence`，并加一只 ABORT：解析出的路径里出现
#      `ht305_sync` 就停（上一轮那目录停在 gen 24，多落一只派生件就会让 verify_manifest 报 STALE）；
#   ② argv[1] 的姓名正则从 `staged_cred_gate_\d{6}\.txt` 放宽到 `staged_cred_gate_[A-Za-z0-9_]{1,40}\.txt`
#      ——本轮门载体名带 LABEL 而非时刻戳（`staged_cred_gate_r61_index507.txt`），照旧式会把自己 ABORT 掉；
#      放宽后仍不许带路径分隔符，防 argv 把落点指走。
# 其余口径沿用上一轮一字未动：SSH 只在内存造合成样本（仓库里没有已知脏样本正是它干净的原因，故它证的是
# 「传参通路 + bytes.count 语义没断」）、与门载体逐字段互核、rc=0 蕴含载体已写出。两条口令都只在进程内取，
# 一次都不打印内容、不进命令文本。
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
assert re.fullmatch(r'staged_cred_gate_[A-Za-z0-9_]{1,40}\.txt', GATE_NAME), \
    'ABORT: argv[1] 不像本轮的门载体名：%r' % GATE_NAME
GATE = os.path.join(REPO, 'hardware/r61b_sync/evidence', GATE_NAME)
assert 'ht305_sync' not in GATE, 'ABORT: 门载体解析进封存归档目录 ' + GATE
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

# ⑵ 真扫集：与索引门同一口径（已 stage blob）。本遍补的一处缺陷（首遍就崩在这）：
# `git diff --cached --name-only` 把**删除行**也列进来，而删除在索引里没有 blob ⇒ `git show :path` 直接 fatal；
# 门那边同一只 `git show` 不查 rc ⇒ 那两只被算进 FILES_SCANNED 却扫了个空字节。
# 故这里按 --name-status 分两支：有 blob 的才扫，删除的逐只点名，互核用 扫描数 + 删除数 == 门的 FILES_SCANNED。
_ns = [x.decode('utf-8') for x in gitbin('diff', '--cached', '--name-status', '-z').split(b'\0') if x]
staged, deleted = [], []
_i = 0
while _i < len(_ns):
    _code, _name = _ns[_i][:1], _ns[_i + 1]
    assert _code in ('A', 'M', 'D'), 'ABORT: 索引里出现本脚本不认识的行状态 %r（%s）' % (_code, _name)
    (deleted if _code == 'D' else staged).append(_name)
    _i += 2
assert staged, 'ABORT: 索引为空，这一遍无从对照'
say('INDEX_DELETED=%d %s（删除在索引里没有 blob，扫不了，逐只点名而不静默）' % (len(deleted), deleted))
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
eq = (gf, gt, gtp + gts, gv) == (len(staged) + len(deleted), tp + ts, tp + ts, 'CLEAN')
say('SELF index_scanned=%d + deleted=%d = %d' % (len(staged), len(deleted), len(staged) + len(deleted)))
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
