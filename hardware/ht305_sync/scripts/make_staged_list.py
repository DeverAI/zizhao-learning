# 第一次真实提交轮：逐只点名 stage 的清单生成器。
# 口径（全部现跑，不引用旧数）：modified 来自 `git diff --name-only`（工作树↔索引），untracked 来自
# `git ls-files --others --exclude-standard`（**逐只展开**口径，不是 `git status` 的目录折叠口径）。
# 排除四组，每条都给理由并现跑明文扫描：
#   hardware/zizhao-esp32s3/main/provision_ap.c  —— 带 PROV_PASS 宏值明文，入库即公开（索引侧门会 rc=1）
#   dev_log/20260919.md                          —— 同上，实测 HITS=1
#   Agent_readme.txt                              —— 外部项目（学习Agent_new）发来的对接回信，非本仓库产出，等用户裁决
#   .workbuddy/ 下 2 只                            —— 第三方工具的状态目录，不是项目源码/文档
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


def git(*args):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args),
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


t0 = datetime.now()
EXCLUDE = {
    'hardware/zizhao-esp32s3/main/provision_ap.c': '带 PROV_PASS 明文（门会 rc=1）',
    'dev_log/20260919.md': '带 PROV_PASS 明文，实测 HITS=1',
    'Agent_readme.txt': '外部项目发来的回信，非本仓库产出，等裁决',
    '.workbuddy/memory/2026-09-16.md': '第三方工具状态目录',
    '.workbuddy/r31_record_update.py': '第三方工具状态目录',
}

mod = git('diff', '--name-only')
untracked = git('ls-files', '--others', '--exclude-standard')

secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"',
                   open('hardware/zizhao-esp32s3/main/provision_ap.c', encoding='utf-8').read()).group(1)

keep, dropped = [], []
for f in mod + untracked:
    if f in EXCLUDE:
        dropped.append((f, EXCLUDE[f], 'not-scanned'))
        continue
    b = open(f, 'rb').read()
    hits = b.count(secret.encode())
    if hits:
        dropped.append((f, '现跑明文扫描命中 %d' % hits, 'AUTO'))
        continue
    keep.append(f)

for f, why, how in dropped:
    print('DROP %-58s %s [%s]' % (f, why, how))

assert len(set(keep)) == len(keep), '清单里有重名'
assert 'hardware/zizhao-esp32s3/main/provision_ap.c' not in keep
# 09-24 R49 复查 P2-3：KEEP=0 时后面那只"清单"是一份空凭证，"门 0 命中"会被下一轮读成"已扫过且干净"。
if not keep:
    print('ABORT: KEEP=0（MOD=%d UNTRACKED=%d 全被排除）=> 本轮没有可提交的字节，不写空清单' % (len(mod), len(untracked)))
    sys.exit(1)
# 排除项若这一轮根本没在候选里出现，必须点名（否则"排掉了 5 只"这句话会随文件消失而静默失效）。
seen = set(mod) | set(untracked)
for k in EXCLUDE:
    if k not in seen:
        print('EXCLUDE_NOT_SEEN', k)
print('MOD=%d UNTRACKED=%d DROP=%d KEEP=%d' % (len(mod), len(untracked), len(dropped), len(keep)))

lst = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence',
                   'staged_list_%s.txt' % t0.strftime('%H%M%S'))
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

nul = os.path.join(os.environ.get('TEMP', '/tmp'), 'staged_paths_%s.bin' % t0.strftime('%H%M%S'))
with open(nul, 'wb') as f:
    f.write(b'\0'.join(k.encode('utf-8') for k in keep))
print('LIST', lst, os.path.getsize(lst), 'md5', hashlib.md5(open(lst, 'rb').read()).hexdigest()[:8])
print('PATHSPEC', nul, os.path.getsize(nul))
with open(os.path.join(os.environ.get('TEMP', '/tmp'), 'staged_paths_latest.txt'), 'w',
          encoding='utf-8', newline='\n') as f:
    f.write(nul)
