# 第十次提交轮：逐只点名 stage 的清单生成器。派生自 `hardware/r61_sync/scripts/make_staged_list_r61.py`
# （第九次提交轮用的就是那一只），改动三处，逐一点名：
#   ①取证落点 `hardware/r61_sync/evidence` → `hardware/r61b_sync/evidence`，ht305_sync 守卫原样继承；
#   ②EXCLUDE 表按 09-26 14:5x 现场重列（见下面 EXCLUDE 那段的逐条理由）；
#   ③**新装一只执行者**：在册裁决「二进制镜像永不 stage」原来只是一句文档（排查记录第 3792/3886 行），
#     第九轮正因为清单器只认 EXCLUDE 表、不读这条裁决，把两只原厂镜像放了进仓（§38.33 那起事故）。
#     本遍把裁决变成代码：凡 `keep` 里出现二进制扩展名 ⇒ 先按名逐只 DROP 并点名理由，
#     再断言终态 `BINS_IN_KEEP=0`；DROP 数由现读变量插值，不写字面量。
# 其余口径原样继承：modified 取 `git diff --name-only`，untracked 取 `git ls-files --others --exclude-standard`
# （逐只展开，不是 git status 的目录折叠口径）；口令运行时现读、绝不打印；KEEP=0 即 ABORT；
# 排除项若本轮不在候选里必须点名（EXCLUDE_NOT_SEEN）。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
os.chdir(REPO)
if 'ht305_sync' in EV.replace('\\', '/').split('hardware/')[-1]:
    raise SystemExit('ABORT: 取证落点指进了封存归档目录 ' + EV)
if not os.path.isdir(EV):
    raise SystemExit('ABORT: 取证目录不存在，拒绝往未知路径写：' + EV)


def git(*args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args),
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


t0 = datetime.now()
EXCLUDE = {
    'hardware/zizhao-esp32s3/main/provision_ap.c': '带 PROV_PASS 宏值明文，入库即公开（索引侧门会 rc=1）',
    'dev_log/20260919.md': '带 PROV_PASS 明文，第八次提交轮实测 HITS=1',
    'Agent_readme.txt': '外部项目发来的回信，非本仓库产出，等裁决',
    '.workbuddy/memory/2026-09-16.md': '第三方工具状态目录',
    '.workbuddy/r31_record_update.py': '第三方工具状态目录',
}
# 在册裁决的代码化：二进制扩展名一律不许进 keep（要真入库，先点名改这条并说明理由）。
BIN_EXT = ('.bin', '.elf', '.map', '.o', '.a', '.so', '.dll', '.exe', '.gz', '.zip', '.7z', '.xz')

mod = git('diff', '--name-only')
untracked = git('ls-files', '--others', '--exclude-standard')

src = open('hardware/zizhao-esp32s3/main/provision_ap.c', encoding='utf-8').read()
m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', src)
if not m:
    raise SystemExit('ABORT: 读不到 PROV_PASS 宏本体')
secret = m.group(1).encode()
if len(secret) < 4:
    raise SystemExit('ABORT: PROV_PASS 宏的值短得可疑（%d 字节），不做这道门' % len(secret))

keep, dropped = [], []
for f in mod + untracked:
    if f in EXCLUDE:
        dropped.append((f, EXCLUDE[f], 'EXPLICIT'))
        continue
    p = os.path.join(REPO, f.replace('/', os.sep))
    if not os.path.isfile(p):
        dropped.append((f, '清单里有名、盘上无此只（多半是刚被改名的旧载体）', 'GONE'))
        continue
    if f.lower().endswith(BIN_EXT):
        dropped.append((f, '在册裁决「二进制镜像永不 stage」（排查记录 §38.33 那起事故的直接后果）', 'RULING'))
        continue
    hits = open(p, 'rb').read().count(secret)
    if hits:
        dropped.append((f, '现跑明文扫描命中 %d' % hits, 'AUTO'))
        continue
    keep.append(f)

for f, why, how in dropped:
    print('DROP %-70s %s [%s]' % (f, why, how))
assert len(set(keep)) == len(keep), '清单里有重名'
assert 'hardware/zizhao-esp32s3/main/provision_ap.c' not in keep
bins_in_keep = [f for f in keep if f.lower().endswith(BIN_EXT)]
print('BINS_IN_KEEP=%d' % len(bins_in_keep))
assert not bins_in_keep, 'ABORT: 二进制进了 keep：%s' % bins_in_keep[:3]
# 阳性对照（本遍新装）：裁决这只执行者必须真咬过——盘上现读那两只原厂镜像，逐只断言
# 「扩展名命中 BIN_EXT」且「不在候选」（已被 .gitignore 挡住），否则 DROP 分支就是没执行者的装饰。
ruling_probe = [p for p in ('esp32s3_flash_backup_8mb.bin', 'esp32s3_partition_table.bin')]
for p in ruling_probe:
    assert p.lower().endswith(BIN_EXT), 'ABORT: 阳性对照源 %s 竟然不被 BIN_EXT 命中 ⇒ 裁决尺是空的' % p
    assert p not in mod + untracked, 'ABORT: 原厂镜像 %s 又回到候选里 ⇒ .gitignore 那两行失效' % p
    assert os.path.isfile(p), 'ABORT: 盘上找不到 %s ⇒ 「只读未动」这句没法核' % p
print('RULING_PROBE=2/2（两只原厂镜像：扩展名命中 + 已不在候选 + 盘上在位）')
if not keep:
    print('ABORT: KEEP=0（MOD=%d UNTRACKED=%d 全被排除）=> 本轮没有可提交的字节，不写空清单'
          % (len(mod), len(untracked)))
    sys.exit(1)
seen = set(mod) | set(untracked)
for k in EXCLUDE:
    if k not in seen:
        print('EXCLUDE_NOT_SEEN', k)
print('MOD=%d UNTRACKED=%d DROP=%d KEEP=%d' % (len(mod), len(untracked), len(dropped), len(keep)))

lst = os.path.join(EV, 'staged_list_%s.txt' % t0.strftime('%H%M%S'))
assert not os.path.exists(lst), '凭证已存在，不覆盖'
with open(lst, 'w', encoding='utf-8', newline='\n') as f:
    f.write('生成时刻 %s；口径：git diff --name-only(%d) + git ls-files --others --exclude-standard(%d)\n'
            % (t0.strftime('%Y-%m-%d %H:%M:%S'), len(mod), len(untracked)))
    f.write('排除并点名（每条附理由，现跑明文扫描 HITS=0 才进清单）：%d 只\n' % len(dropped))
    for fn, why, how in dropped:
        f.write('  DROP  %s  <- %s [%s]\n' % (fn, why, how))
    f.write('进清单 %d 只：\n' % len(keep))
    for fn in keep:
        f.write('  ADD   %s\n' % fn)
nul = os.path.join(EV, 'staged_paths_%s.bin' % t0.strftime('%H%M%S'))
with open(nul, 'wb') as f:
    f.write(b'\0'.join(k.encode('utf-8') for k in keep))
print('LIST', lst, os.path.getsize(lst), 'md5', hashlib.md5(open(lst, 'rb').read()).hexdigest()[:8])
print('PATHSPEC', nul, os.path.getsize(nul))
