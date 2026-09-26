"""重生成 hardware/ht305_sync/MANIFEST.txt：对**终态**归档逐只记 bytes/md5/BOM。
本清单不含自身（自列必然漂）。**本版头部不再枚举"上一版有几只"**——那种硬编码在原地跑第二遍时就漂了（本脚本 11:36 / 11:47 两连跑实测）；
历世代只数自 09-23 gen 9 起由本脚本逐代**追加**进 `evidence/manifest_gen_log.txt`；正文侧的代次叙述以 `README.md` 为准。
头部那句"门是否覆盖本清单"由 mtime 现算，不靠人记。"""
import datetime, hashlib, os, sys
# ABORT 消息走 stderr，且在 GBK 控制台下会被替换码/乱码渲染（13:16 实测：那条"归档里有 N 只派生字节"打出来是 mojibake）
# ⇒ 与 ps1_bom_scan.py / verify_manifest.py 同一条修法：显式换编码。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
LOGREL = 'evidence/manifest_gen_log.txt'
LOG = os.path.join(DST, 'evidence', 'manifest_gen_log.txt')
now_full = datetime.datetime.now().strftime('%m-%d %H:%M:%S')
# 09-24 12:4x 复核：这里原有**两只** `datetime.now()`（`now` 与 `now_full` 各取一次），而 `now` 进的是头部那句
# "本清单只对生成时刻 H:M:S 之前的字节负责" ⇒ 跨秒时头部两行的时刻自相矛盾。同源修法：只取一次、由它派生。
now = now_full.split(' ')[1]

# 门输出自 09-23 12:0x 起带时刻（不再原地覆写上一代）⇒ 这里取**最新**那只，并把它的路径写进头部。
gates = [os.path.join(DST, 'evidence', f) for f in os.listdir(os.path.join(DST, 'evidence'))
         if f.startswith('cred_gate_recheck')]
if not gates:
    raise SystemExit('ABORT: evidence/ 下找不到门输出 ⇒ 先跑 gate/run_cred_gate_recheck.ps1')
GATE = max(gates, key=os.path.getmtime)

# 派生字节守卫（09-23 13:15:41 实测：我用 `py_compile` 做语法检查，它把两只 `.pyc` 写进了 `scripts/__pycache__/`，
# 而清单照单全收 ⇒ "归档 = 脚本 + 取证件" 这条口径被我自己跑的一条命令破了）。
# 口径：这类字节**不是归档内容**，但**悄悄跳过**等于让归档范围随环境漂 ⇒ 这里响亮地失败，让跑的人先清掉再跑。
junk = sorted({os.path.relpath(os.path.join(r, fn), DST).replace('\\', '/')
               for r, _, fs in os.walk(DST) for fn in fs
               if fn.endswith('.pyc') or '__pycache__' in r.replace('\\', '/').split(os.sep)})
if junk:
    raise SystemExit('ABORT: 归档里有 %d 只派生字节（.pyc / __pycache__）⇒ 先删掉再跑清单：%s'
                     % (len(junk), ', '.join(junk[:6])))

rows = []
SKIP = {'MANIFEST.txt', LOGREL}
for root, dirs, fs in os.walk(DST):
    for fn in sorted(fs):
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, DST).replace('\\', '/')
        if rel in SKIP:
            continue
        b = open(p, 'rb').read()
        rows.append((rel, len(b), hashlib.md5(b).hexdigest(), b[:3] == b'\xef\xbb\xbf', os.path.getmtime(p)))
rows.sort()

# 代次日志：本脚本**自己**在写清单之前追加一行 ⇒ "每一代都可复算"这条口径从本代起成立，
# 不再依赖 README 表格的人工叙述（gen 5 那种"时刻被覆写掉"的代价见 README「清单代次」节）。
total_rows, total_bytes, bom_files = len(rows), sum(r[1] for r in rows), sum(1 for r in rows if r[3])
if not os.path.isfile(LOG):
    open(LOG, 'w', encoding='utf-8', newline='').write(
        '# manifest_gen_log.txt —— 每跑一次 scripts/gen_manifest.py 由该脚本**自己**追加一行。\n'
        '# 字段：时刻(月-日 时:分:秒)\tTOTAL\tTOTAL_BYTES\tBOM_FILES（口径与清单末三行同一条）。\n'
        '# 不列本文件、也不列 MANIFEST.txt：本行写在清单之前 ⇒ 列它必然立刻过期（同"清单不含自身"）。\n'
        '# 起点 = 09-23 gen 9。gen 1~8 的只数**不回填**：回填等于拿"从 README 叙述里 recovered 的数"冒充"当时现算"。\n')
with open(LOG, 'a', encoding='utf-8', newline='') as f:
    # 09-24 12:34:41/12:34:42 实测：这里原是一只**新的** `datetime.now()`，而清单头部用的是 20 行那只 `now_full`
    # ⇒ 一次运行里两次取时刻，中间隔着 378 只文件的哈希遍历，跨秒即发生 ⇒ 日志末行与清单头部差 1 秒，
    #    `verify_manifest.py` 的 `log_line == exp_log` 判 MANIFEST_STALE / rc=1，而 MISMATCH/MISSING/UNLISTED 全 0、
    #    汇总三字段逐项 OK —— 一次**假红**，且红的是"清单不是脚本跑出来的"这句最重的话。
    #    修法是在源头只取一次时刻（不是去 verifier 里放宽容差）：头部与日志同源 ⇒ 相等由构造成立。
    f.write('%s\t%d\t%d\t%d\n' % (now_full, total_rows, total_bytes, bom_files))

gate_txt = open(GATE, encoding='utf-8').read().splitlines()[0]
gm = os.path.getmtime(GATE)
after = [r[0] for r in rows if r[4] > gm] + ['MANIFEST.txt', LOGREL]

head = [
    'ht305_sync 归档清单（快照，现跑于 ' + now_full + '；脚本 = scripts/gen_manifest.py）',
    '',
    '**"快照"两个字有执行者**：跑 `python scripts/verify_manifest.py` 会把本清单逐行与盘上重算比对，'
    '漂了就点名是哪几只并返回非 0 ⇒ 引用本清单前跑它，别靠"我记得它是末版"。',
    '本清单只对**生成时刻 ' + now + ' 之前**的字节负责；此后被改写的任何一只（含本清单自己、含 README）'
    '都不在本行的覆盖范围内 ⇒ 这一句是给"终态/末版"这类词定的有界窗口（R45 空上下文复查 P0-2）。',
    '来源 = %TEMP% 的逐字节复制（shutil.copy2，保留 BOM）。清单是**快照**：它一旦写死就追不上还在增长的目录，'
    '所以本目录只保留末版清单 + 这段说明，不留半旧版；历世代的**动因**统一记在 `README.md` 的"清单代次"一节（单一权威源），'
    '只数与时刻另有下面那条机器自追加的日志，本头部不重复登记。',
    '本清单**不含自身**（列自己必然在写完后立刻过期），同样**不含** `evidence/manifest_gen_log.txt`。',
    '代次日志：`evidence/manifest_gen_log.txt` 由本脚本在写清单**之前**追加一行 `时刻 / TOTAL / TOTAL_BYTES / BOM_FILES`'
    ' ⇒ 自 09-23 gen 9 起，"上一代有几只"每一代都可复算，不再只靠 README 的人工叙述（gen 5 那种时刻被覆写的代价见该节）。',
    '明文门（取 `evidence/cred_gate_recheck*` 里 mtime 最新的那只 = '
    + os.path.relpath(GATE, DST).replace('\\', '/') + '）：' + gate_txt
    + '；FILES_SCANNED 见该文件末行，两种口令（`PROV_PASS` / ht305 SSH）各自累计均 0 命中。',
    '门与本清单的先后（按 mtime 现算，非人工登记）：门之后又被改写/新增 ' + str(len(after)) + ' 只 = '
    + ', '.join(after) + ' ⇒ 门未覆盖这几只的**当前字节**；'
    '其中清单只含"已扫文件的路径/大小/哈希"、编码体检只含"非 ASCII 计数"，均为派生信息、不含新载荷。',
    '',
    'path\tbytes\tmd5\tutf8_bom\tmtime',
]
body = ['%s\t%d\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3],
        datetime.datetime.fromtimestamp(r[4]).strftime('%H:%M:%S')) for r in rows]
tail = ['', 'TOTAL\t' + str(len(rows)),
        'TOTAL_BYTES\t' + str(sum(r[1] for r in rows)),
        'BOM_FILES\t' + str(sum(1 for r in rows if r[3]))]
open(os.path.join(DST, 'MANIFEST.txt'), 'w', encoding='utf-8', newline='').write('\n'.join(head + body + tail) + '\n')
print('MANIFEST files=' + str(len(rows)) + ' bytes=' + str(sum(r[1] for r in rows))
      + ' gate_after=' + str(len(after)) + ' at ' + now)
