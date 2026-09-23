"""清单的**复核器**：把 `MANIFEST.txt` 里每行的 `bytes/md5/utf8_bom` 与**盘上现状**逐一重算比对。
动机（R45 空上下文复查 P0-2）：清单自称"终态快照"，但**没有任何执行者**去验它是否仍与盘上一致 ⇒
"末版"这两个字在清单写下后的第一次编辑起就悄悄失效（本轮实测：`README.md` 记 6,689/实 7,694、
`gen_manifest.py` 记 2,730/实 2,843，两行 md5 均不符，`TOTAL_BYTES` 差 1,118 B）。
判据不是"记住别再引旧数"，而是**这条命令一跑就把不一致的行点名**。
退出码：0 = 全行与盘上一致；1 = 有漂移（stdout 列出漂在哪几只）。
"""
import hashlib, os, sys
# 显式换 stdout 编码：本脚本输出里有 `⇒`，在 GBK 控制台下会崩在 print 上（12:20:14 实测：
# 判据行已经打完了、进程仍以 rc=1 退出 ⇒ 会被误读成"清单漂了"）。同族缺陷见 ps1_bom_scan.py。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
MAN = os.path.join(DST, 'MANIFEST.txt')
if not os.path.isfile(MAN):
    print('ABORT: 找不到 MANIFEST.txt'); sys.exit(2)

rows, total_line, bytes_line, bom_line, gen_line = [], None, None, None, ''
for ln in open(MAN, encoding='utf-8').read().splitlines():
    if ln.startswith('ht305_sync 归档清单'):
        gen_line = ln
    elif ln.startswith('TOTAL\t'):
        total_line = ln
    elif ln.startswith('TOTAL_BYTES\t'):
        bytes_line = ln
    elif ln.startswith('BOM_FILES\t'):
        bom_line = ln
    elif '\t' in ln and not ln.startswith('path\t'):
        f = ln.split('\t')
        if len(f) == 5 and f[1].isdigit():
            rows.append(f)

bad, missing = [], []
for rel, size, md5, bom, mtime in rows:
    p = os.path.join(DST, rel.replace('/', os.sep))
    if not os.path.isfile(p):
        missing.append(rel); continue
    b = open(p, 'rb').read()
    got = (str(len(b)), hashlib.md5(b).hexdigest(), str(b[:3] == b'\xef\xbb\xbf'))
    if got != (size, md5, bom):
        bad.append('%s 清单=%s/%s/%s 盘上=%s/%s/%s' % (rel, size, md5[:8], bom, got[0], got[1][:8], got[2]))

disk = [os.path.relpath(os.path.join(r, fn), DST).replace('\\', '/')
        for r, _, fs in os.walk(DST) for fn in fs]
# 与 gen_manifest.py 同一条排除口径：清单不含自身，也不含代次日志（日志由清单脚本在写清单之前追加）。
LOGREL = 'evidence/manifest_gen_log.txt'
unlisted = sorted(set(disk) - set(r[0] for r in rows) - {'MANIFEST.txt', LOGREL})

# 代次日志的末行 == 本清单的汇总三行？不一致 ⇒ 有人在清单之外手改过其中一只，或清单不是脚本跑出来的。
log_line = ''
if os.path.isfile(os.path.join(DST, 'evidence', 'manifest_gen_log.txt')):
    lines = [l for l in open(os.path.join(DST, 'evidence', 'manifest_gen_log.txt'), encoding='utf-8').read().splitlines() if l and not l.startswith('#')]
    log_line = lines[-1] if lines else ''
exp_log = (gen_line.split('现跑于 ')[1].split('；')[0] + '\t'
           + (total_line or '').replace('TOTAL\t', '') + '\t'
           + (bytes_line or '').replace('TOTAL_BYTES\t', '') + '\t'
           + (bom_line or '').replace('BOM_FILES\t', ''))

print(gen_line)
print('ROWS=%d  MISMATCH=%d  MISSING=%d  UNLISTED(盘上有、清单没记)=%d %s'
      % (len(rows), len(bad), len(missing), len(unlisted), unlisted[:10]))
for x in bad + ['MISSING ' + m for m in missing]:
    print('  ' + x)
print('GEN_LOG 末行=%s / 清单汇总应为=%s ⇒ %s'
      % (log_line, exp_log, 'OK' if log_line == exp_log else '不一致（日志与清单不同代或被手改）'))
totals_ok = True
if total_line and bytes_line:
    s = sum(int(r[1]) for r in rows)
    totals_ok = (total_line == 'TOTAL\t%d' % len(rows) and bytes_line == 'TOTAL_BYTES\t%d' % s)
    print('TOTAL 行=%s / TOTAL_BYTES 行=%s / 逐行求和=%d ⇒ %s'
          % (total_line, bytes_line, s, 'OK' if totals_ok else '不一致'))
clean = not (bad or missing or unlisted) and totals_ok and log_line == exp_log
print('VERDICT=' + ('MANIFEST_STILL_TRUE' if clean else
                    'MANIFEST_STALE(下面几只已漂或汇总行不符，重跑 scripts/gen_manifest.py)'))
sys.exit(0 if clean else 1)
