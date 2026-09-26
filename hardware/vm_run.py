# 复核器槽位用尽后的第二把尺（R56 第一批复跑遍现场催生）：
#   真跑 hardware/ht305_sync/scripts/verify_manifest.py，把它的**逐字 stdout + rc** 落进一只
#   按本遍时刻命名的载体（`hardware/vm_run_<时刻>.txt`，在归档目录之外 ⇒ 不动 gen 24 封界）。
# 为什么需要它：被复核那一代的时刻固定 ⇒ 内层载体名也固定（verify_manifest_<genstamp>[_2.._9].txt），
#   9 只槽位被历次 paperwork 复跑用掉后，内层**拒绝覆写并 rc=2** —— 裁决只在 stdout、不落盘，
#   正好踩中「读数不落盘等于没跑」。修内层脚本 = 改写已封界的归档件 ⇒ 不走那条路。
# 判决口径：MANIFEST_STILL_TRUE 且内层 rc 能被解释（0 = 自己落了载体；2 = 槽位用尽、由本件代落）⇒ rc 0；
#   MANIFEST_STALE ⇒ rc 1；读数形状不认识 ⇒ rc 3（宁响不静默）。
import os
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
VM = os.path.join(HDIR, 'ht305_sync', 'scripts', 'verify_manifest.py')
GEN_STAMP = '0924125339'                      # 被复核那一代（gen 24）的时刻，与内层载体名同源
_inner = ['verify_manifest_%s.txt' % GEN_STAMP] + \
         ['verify_manifest_%s_%d.txt' % (GEN_STAMP, i) for i in range(2, 10)]
SLOT_USED = len([f for f in _inner if os.path.isfile(os.path.join(HDIR, f))])

now = datetime.now().strftime('%Y%m%d_%H%M%S')
cands = ['vm_run_%s.txt' % now] + ['vm_run_%s_%d.txt' % (now, i) for i in range(2, 10)]
CARRIER = None
for _c in cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 本遍载体名 9 只全被占，拒绝覆写'

_v = subprocess.run([sys.executable, VM], cwd=REPO, capture_output=True, text=True,
                    env=dict(os.environ, PYTHONUTF8='1'))
OUT, ERR, RC = _v.stdout, _v.stderr, _v.returncode
rows = [l for l in OUT.split('\n') if l.startswith('ROWS=')]
verd = [l for l in OUT.split('\n') if l.startswith('VERDICT=')]
car = [l for l in OUT.split('\n') if l.startswith('VERIFY_CARRIER=')]
assert rows and verd, 'ABORT: 内层复核器没打出 ROWS=/VERDICT= 行 ⇒ 它的输出形状变了，本把尺失效\n' + OUT[-400:]
green = verd[0] == 'VERDICT=MANIFEST_STILL_TRUE'
if green and RC == 0 and car:
    SLOT, explanation, orc = 'INNER-CARRIER-WRITTEN', '内层自己落了载体', 0
elif green and RC == 2 and '载体名 9 只全被占' in OUT:
    SLOT, explanation, orc = 'INNER-SLOT-EXHAUSTED', '内层裁决为真但拒绝落第 10 只载体 ⇒ 由本件代落', 0
elif not green and RC == 1:
    SLOT, explanation, orc = 'INNER-STALE', '清单快照过期（不是造假），必须点名漂在哪几只', 1
else:
    SLOT, explanation, orc = 'UNEXPLAINED', 'rc/裁决/载体三者组合不认识 ⇒ 拒绝给结论', 3

lines = [
    'vm_run.py 代内层复核器落盘（外层 rc=%d 见末行 VERDICT）' % orc,
    'RUN_AT=%s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'INNER_SCRIPT=hardware/ht305_sync/scripts/verify_manifest.py（本遍未改写它一字节）',
    'INNER_RC=%d' % RC,
    'INNER_STDOUT_BYTES=%d / INNER_STDERR_BYTES=%d' % (len(OUT.encode('utf-8')), len(ERR.encode('utf-8'))),
    'SLOT=%s（gen %s 的 9 只内层槽位盘上现有 %d 只）' % (SLOT, GEN_STAMP, SLOT_USED),
    'EXPLANATION=%s' % explanation,
    'INNER_ROWS=%s' % rows[0],
    'INNER_VERDICT=%s' % verd[0],
    'INNER_VERIFY_CARRIER=%s' % (car[0] if car else '（内层未落载体）'),
    'CARRIED_INNER_STDOUT_START',
] + OUT.rstrip('\n').split('\n') + [
    'CARRIED_INNER_STDOUT_END',
    'WITNESS=本文件逐字收录内层 stdout，未做任何脱敏或改写；反斜杠若出现来自内层口径，不外层洗。',
    'VERDICT=' + ('VM_RUN_GREEN' if orc == 0 else 'VM_RUN_RED'),
]
with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines) + '\n')

print('VM_RC=%d / %s / %s / SLOT=%s / INNER_RC=%d' % (orc, rows[0], verd[0], SLOT, RC))
print('VM_CARRIER=%s' % os.path.relpath(CARRIER, REPO).replace('\\', '/'))
sys.exit(orc)
