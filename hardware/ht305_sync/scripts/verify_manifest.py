"""清单的**复核器**：把 `MANIFEST.txt` 里每行的 `bytes/md5/utf8_bom` 与**盘上现状**逐一重算比对。
动机（R45 空上下文复查 P0-2）：清单自称"终态快照"，但**没有任何执行者**去验它是否仍与盘上一致 ⇒
"末版"这两个字在清单写下后的第一次编辑起就悄悄失效（本轮实测：`README.md` 记 6,689/实 7,694、
`gen_manifest.py` 记 2,730/实 2,843，两行 md5 均不符，`TOTAL_BYTES` 差 1,118 B）。
判据不是"记住别再引旧数"，而是**这条命令一跑就把不一致的行点名**。
退出码：0 = 全行与盘上一致；1 = 有漂移（stdout 列出漂在哪几只）。
"""
import datetime, hashlib, os, sys
# 显式换 stdout 编码：本脚本输出里有 `⇒`，在 GBK 控制台下会崩在 print 上（12:20:14 实测：
# 判据行已经打完了、进程仍以 rc=1 退出 ⇒ 会被误读成"清单漂了"）。同族缺陷见 ps1_bom_scan.py。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 每行输出同时进 stdout 与一份内存副本，副本随裁决一起落载体（见文件末）。
_OUT_LINES = []


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    _OUT_LINES.append(s)

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
# 候选为 0 不给"干净"裁决（(55)/(71) 那一族）；头部缺"现跑于"则载体名也无从派生。
if not rows or '现跑于 ' not in gen_line:
    print('ABORT: 清单里没有逐只行（ROWS=%d）或头部缺"现跑于"时刻 ⇒ 拒绝给出"仍与盘上一致"' % len(rows))
    sys.exit(2)
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

P(gen_line)
# gen 13 修正之二（登记于排查记录 §38.9 末段，缺陷本体见规则 (82)）：汇总行曾印 `UNLISTED=12` 而名单只给 10 只
# ⇒ "看起来完整"的截断视图。现在名单全量逐行输出，且汇总行自己说"印了几只 / 共几只"。
P('UNLISTED_NAMES shown=%d total=%d（下面逐行列全表，不再截断）' % (len(unlisted), len(unlisted)))
for u in unlisted:
    P('  UNLISTED ' + u)
P('ROWS=%d  MISMATCH=%d  MISSING=%d  UNLISTED(盘上有、清单没记)=%d'
  % (len(rows), len(bad), len(missing), len(unlisted)))
for x in bad + ['MISSING ' + m for m in missing]:
    P('  ' + x)
# 09-24 12:34 假红的另一半修法：判"同一代"的是**三个数字字段**（只数 / 字节 / BOM 只数），时刻只**并列打印**、不进判据。
# 时刻同源已由 `gen_manifest.py` 那处修好（一次运行只取一次 `now_full`），但**旧日志行**里仍可能有跨秒的那一代，
# 把时刻当判据 = 让"清单不是脚本跑出来的"这句最重的话由一次秒级抖动触发 ⇒ 判据与展示分家。
_log_cols = log_line.split('\t')
_exp_cols = exp_log.split('\t')
log_nums = _log_cols[1:] if len(_log_cols) == 4 else _log_cols
exp_nums = _exp_cols[1:] if len(_exp_cols) == 4 else _exp_cols
P('GEN_LOG 末行=%s / 清单汇总应为=%s ⇒ 数字三字段%s（时刻 %s vs %s，只并列不参与判决）'
  % (log_line, exp_log, 'OK' if log_nums == exp_nums else '不一致（日志与清单不同代或被手改）',
     _log_cols[0] if _log_cols else '-', _exp_cols[0] if _exp_cols else '-'))
totals_ok = True
if total_line and bytes_line:
    s = sum(int(r[1]) for r in rows)
    totals_ok = (total_line == 'TOTAL\t%d' % len(rows) and bytes_line == 'TOTAL_BYTES\t%d' % s)
    P('TOTAL 行=%s / TOTAL_BYTES 行=%s / 逐行求和=%d ⇒ %s'
      % (total_line, bytes_line, s, 'OK' if totals_ok else '不一致'))
clean = not (bad or missing or unlisted) and totals_ok and log_nums == exp_nums
P('VERDICT=' + ('MANIFEST_STILL_TRUE' if clean else
                'MANIFEST_STALE(下面几只已漂或汇总行不符，重跑 scripts/gen_manifest.py)'))
_rc = 0 if clean else 1

# 09-24 12:4x（gen 23 的账）：本脚本的裁决**只打在 stdout**，靠人抄进 README ⇒ "读数不落盘等于没跑"那一族
# 在归档链的**最后一步**还开着一个口子（gen 23 那次 `rc=0` 事后已无法复算：12:40 之后盘上又多了只文件）。
# 载体落在**归档目录之外**、仓库之内（`hardware/`，与 `hardware/20260924_ps1编码吞行实验.txt` 同一口径）：
# 落在 `evidence/` 里会被下一代清单少记一只 ⇒ `UNLISTED` 顶成非 0、把"清单是否仍真"这件正事污染掉；
# 落在仓库外则等于没落盘。名字带上它所复核那一代的时刻 ⇒ 一代一只、不覆写；已存在另起 `_2`。
_gen_stamp = ''.join(c for c in gen_line.split('现跑于 ')[1].split('；')[0] if c.isdigit())
assert len(_gen_stamp) == 10, 'ABORT: 被复核那代的时刻没解析出 10 位数字，载体名无从派生：%r' % gen_line
_cand = 'verify_manifest_%s.txt' % _gen_stamp
_cands = [_cand] + [_cand.replace('.txt', '_%d.txt' % i) for i in range(2, 10)]
_out = None
for _c in _cands:
    _p = os.path.join(os.path.dirname(DST.rstrip('/\\')), _c)
    if not os.path.isfile(_p):
        _out, _path = _c, _p
        break
if _out is None:
    print('ABORT: 复核载体名 9 只全被占，拒绝覆写')
    sys.exit(2)
with open(_path, 'w', encoding='utf-8', newline='') as _fh:
    _fh.write('\n'.join([
        'verify_manifest.py 对本代清单的终态裁决（载体由脚本自己落盘，09-24 12:4x 起）',
        'CLEAN_UP_TO=' + datetime.datetime.now().strftime('%m-%d %H:%M:%S') + '（本行是写载体的时刻，与被复核那代的时刻不同源）',
        'VERIFIED_MANIFEST=' + gen_line,
        'NOTE=本载体记录的是"写它那一刻"盘上现状 vs 该代清单的比对；若被复核那代之后盘上又动过，'
        '这里给 STALE 是**快照过期**、不是清单造假（清单头部那句"只对生成时刻之前的字节负责"就是为它留的界）。',
        'CARRIED_OUTPUT_START',
        *_OUT_LINES,
        'CARRIED_OUTPUT_END',
        'VERIFY_RC=%d' % _rc,
    ]) + '\n')
print('VERIFY_CARRIER=hardware/%s（在归档目录之外 ⇒ 不参与本清单的 UNLISTED 口径）' % _out)
sys.exit(_rc)
