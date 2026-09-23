"""提交前明文门：扫 git **索引**里已 stage 的每一只 blob，只对**已 stage 的内容**负责。
口令两侧都现读（PROV_PASS 从 provision_ap.c 正则、SSH 口令从环境变量），只打印命中计数、绝不打印口令。
"""
import datetime, os, re, subprocess, sys

# GBK 控制台下的非 ASCII print 会崩（见 `FreqErr.md` ht305 段"`rc≠0` 被读成'没产出'"那条）
# stdout 与 stderr **都要** reconfigure：只补 stdout 的那版守卫本身就是同一族缺陷的一次复发点。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SRC = os.path.join(REPO, 'hardware/zizhao-esp32s3/main/provision_ap.c')
# 输出路径可由 argv[1] 指定（跑完要能把读数落进 `evidence/`：只打 stdout = 这一遍不可复算，见 (64)）。
OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:/Users/david/AppData/Local/Temp/staged_cred_gate.txt'

m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏本体'); sys.exit(1)
prov = m.group(1)
env = os.environ.get('HT305_TMP_FOR_GATE')
ssh = env.encode('utf-8') if env else None
if env:
    del os.environ['HT305_TMP_FOR_GATE']
if ssh is None:
    print('ABORT: 环境变量 HT305_TMP_FOR_GATE 未设置'); sys.exit(1)

r = subprocess.run(['git', '-c', 'core.quotePath=false', 'diff', '--cached', '--name-only', '-z'],
                   cwd=REPO, capture_output=True, shell=False)
paths = [p.decode('utf-8') for p in r.stdout.split(b'\0') if p]
if not paths:
    print('ABORT: 索引里没有已 stage 的文件'); sys.exit(1)

lines = ['提交前明文门（索引侧，现跑于 %s）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         'LABEL=%s' % (sys.argv[2] if len(sys.argv) > 2 else 'index'),
         '判据：字节级 count(口令明文)；PROV_PASS 现读宏本体、SSH 口令现解 DPAPI 后经环境变量传入，两侧都不内嵌字面量。',
         '口径：扫的是 `git diff --cached --name-only -z` 列出的**已 stage blob**（即真正会进 commit 的那份字节），不是工作树。', '']
hit_prov, hit_ssh, tot_p, tot_s = [], [], 0, 0
for p in paths:
    b = subprocess.run(['git', 'show', ':' + p], cwd=REPO, capture_output=True, shell=False).stdout
    cp, cs = b.count(prov), b.count(ssh)
    tot_p += cp; tot_s += cs
    if cp:
        hit_prov.append(p)
    if cs:
        hit_ssh.append(p)
lines += ['FILES_SCANNED=%d' % len(paths),
          'PROV_PASS_FILES=%d PROV_PASS_TOTAL_HITS=%d %s' % (len(hit_prov), tot_p, hit_prov),
          'SSH_FILES=%d SSH_TOTAL_HITS=%d %s' % (len(hit_ssh), tot_s, hit_ssh),
          'TOTAL_HITS=%d' % (tot_p + tot_s),
          # 裁决写进输出**和退出码**：只打印不置码 = "命中了但没人读输出"照样提交（见排查记录 §三十五-④）。
          'VERDICT=%s' % ('CLEAN' if (tot_p + tot_s) == 0 else 'PLAINTEXT_IN_INDEX')]
txt = '\n'.join(lines) + '\n'
open(OUT, 'w', encoding='utf-8').write(txt)
print(txt)
raise SystemExit(0 if (tot_p + tot_s) == 0 else 1)
