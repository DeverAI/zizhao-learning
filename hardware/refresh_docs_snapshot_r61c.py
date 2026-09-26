# 根 A docs/ 快照刷新（r61c 代 = 第十三遍）：由 hardware/refresh_docs_snapshot_r61b.py（第十二遍脚本）逐字派生，派生器 = hardware/r61c_sync/scripts/derive_docs_r61c.py（替换表见该文件，表外任何一处字节变了它的 difflib 计数就红）。
# 派生源仍与上一代同处一只目录（都在 hardware/，不在 %TEMP%），"派生自"那一句仍是仓库内 grep 得到的路径。
# 对**被派生那只**的改动只有三处，逐处点名见文件末尾 NOTE 的"派生自"那一行。
# 口径：快照非终态（那一刻的工作树）；不含 hardware/ht305_sync/（另有 MANIFEST.txt 那把尺子）、不含代码。
# 本只**故意**写在 hardware/ 而不是 hardware/ht305_sync/scripts/：末版 gen 24 之后往归档里落任何一只 = 亲手把末版降级（UNLISTED 非 0）。
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DST = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
SRC_MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
PRIOR = os.path.join(REPO, 'hardware', 'refresh_docs_snapshot_r61b.py')

SRCS = [
    'FreqErr.md',
    'done.md',
    'todo.md',
    'hardware/20260919_墨水屏点屏排查记录.md',
    'hardware/烧录须知.md',
    'dev_log/20260920.md',
    'dev_log/20260921.md',
    'dev_log/20260922.md',
    'dev_log/20260923.md',
    'dev_log/20260924.md',
    'updates/20260922_墨水屏收尾R43.md',
    'updates/20260923_墨水屏R43真机首烧与归档尾.md',
    'updates/20260923_墨水屏R44同步与ht305三轮收口.md',
    'updates/20260923_墨水屏R47同步与R48只读复读.md',
    'updates/20260923_墨水屏R48第6代同步与假差集.md',
    'updates/20260923_墨水屏R49第7代同步与第一次提交.md',
    'updates/20260924_墨水屏R50第8代同步与gen12冻结.md',
    'updates/20260924_墨水屏R53_GPIO1按住落地与两处自查.md',
    'updates/20260924_墨水屏R54第12代同步与gen20-21冻结.md',
    'updates/20260924_墨水屏R55第13代同步与gen22-24三代.md',
    'updates/20260925_墨水屏R56四臂R57E臂与收口批四遍.md',
    'dev_log/20260925.md',
    'hardware/20260925_R57_E臂判据摘录_v2.txt',
    'hardware/20260921_R33复查报告原文.txt',
    'hardware/20260922_R40复查报告原文.txt',
    'hardware/20260922_R41复查报告原文_code.txt',
    'hardware/20260922_R41复查报告原文_docs.txt',
    'hardware/20260922_R42复查报告原文_code.txt',
    'hardware/20260922_R42复查报告原文_docs.txt',
    'hardware/20260922_R43复查报告原文_code.txt',
    'hardware/20260922_R43第四次复查报告原文_A.txt',
    'hardware/20260922_R43第四次复查报告原文_B.txt',
    'hardware/20260922_R43第四次复查报告原文_C.txt',
    'hardware/20260923_R44复查报告原文.txt',
    'hardware/20260923_R44终态复查报告原文.txt',
    'hardware/20260923_R45复查报告原文.txt',
    'hardware/20260923_重连COM14判据摘录.txt',
    'hardware/20260924_R49复查报告原文.txt',
    'hardware/20260924_mindog首次同步取证.txt',
    'hardware/20260924_未推送历史明文普查.txt',
    'hardware/20260924_ps1编码吞行实验.txt',
    'dev_log/20260926.md',
    'updates/20260926_墨水屏R60版面R61翻页与两件档案补齐.md',
    'updates/20260926_墨水屏R61尾巴提交轮9与第14代同步.md',
    'hardware/20260924_R56真机首烧fb32168a判据摘录_v2.txt',
    'hardware/20260925_R57_F臂判据摘录.txt',
    'hardware/20260925_R59板型鉴定判据摘录.txt',
    'hardware/BOARD_ePaper397.md',
    'hardware/BOARD_S3_ePaper_1_54.md',
    'updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md',
]

# 守卫（r50 代新增，r50b 28→32、r50c 33、r51a 34、r53 35、r54 36、r55 37、r57 40、r61b 48，本代（r61c 代 = 第十三遍）抬到 49）：五只"活文档"必须在清单里，否则说明这份派生清单被截断过。
MUST = ['FreqErr.md', 'done.md', 'todo.md',
        'hardware/20260919_墨水屏点屏排查记录.md', 'hardware/烧录须知.md']
absent = [x for x in MUST if x not in SRCS]
if absent or len(SRCS) < 49:
    print('ABORT: 源清单不完整（缺 %s / 只数 %d < 49）' % (absent, len(SRCS)))
    sys.exit(1)

# 本代另加一道：派生源必须真在仓库里（上一代这句写的是 %TEMP% 那只，仓库侧 grep 不到）。
if not os.path.isfile(PRIOR):
    print('ABORT: 被派生那只不在仓库里，NOTE 的"派生自"会是假指针')
    sys.exit(1)

# 明文凭据闸：口令只从宏本体读出，全程不打印、不进命令文本。命中即 ABORT，不写盘。
m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', open(SRC_MACRO, encoding='utf-8').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏，闸无法自证扫的是真口令')
    sys.exit(1)
secret = m.group(1).encode('utf-8')

missing = [s for s in SRCS if not os.path.isfile(os.path.join(REPO, s.replace('/', os.sep)))]
if missing:
    print('ABORT: 清单里有源文件不存在')
    for x in missing:
        print('  MISSING', x)
    sys.exit(1)

dirty = []
blobs = {}
for s in SRCS:
    b = open(os.path.join(REPO, s.replace('/', os.sep)), 'rb').read()
    blobs[s] = b
    if secret in b:
        dirty.append(s)
if dirty:
    print('ABORT: 明文口令在快照源里命中，一只都不拷')
    for x in dirty:
        print('  PLAINTEXT', x)
    sys.exit(1)
print('CRED_GATE HITS=0 OF', len(SRCS))

if not os.path.isdir(DST):
    print('ABORT: 目标目录不存在')
    sys.exit(1)

rows = []
t0 = datetime.now()
for s in SRCS:
    name = os.path.basename(s)
    dst = os.path.join(DST, name)
    old_bytes = os.path.getsize(dst) if os.path.isfile(dst) else None
    b = blobs[s]
    shutil.copy2(os.path.join(REPO, s.replace('/', os.sep)), dst)
    after = os.path.getsize(dst)
    assert after == len(b), 'copy size mismatch: ' + name
    assert open(dst, 'rb').read() == b, 'copy bytes mismatch: ' + name
    rows.append('%s\t%d\tmd5:%s\t%s -> %d' % (
        name, len(b), hashlib.md5(b).hexdigest()[:8],
        'NEW' if old_bytes is None else str(old_bytes), after))

note = os.path.join(DST, 'SNAPSHOT_NOTE.txt')
with open(note, 'w', encoding='utf-8', newline='\n') as f:
    f.write('本目录 = 备份根 A（backups/r43_20260922_131029/）的 docs/ 快照，刷新时刻 %s。\n'
            % t0.strftime('%Y-%m-%d %H:%M:%S'))
    f.write('口径：**快照非终态** —— 它记的是那一刻工作树里这些文件的字节，之后仓库再改不算它漏。\n')
    f.write('清单逐只记 文件名 / bytes / md5 前 8 位 / 覆盖前大小（NEW = 本目录此前没有这只）-> 覆盖后大小：\n\n')
    f.write('\n'.join(rows))
    f.write('\n\n本快照**不含** hardware/ht305_sync/：那只目录已随提交进 git，磁盘根再存一份只会造出第二把尺子（mtime 不同、清单不同代）；需要时按该目录 MANIFEST.txt 现读。\n')
    f.write('本快照**不含** 代码：源码在上一级 main/（30 只）+ 构建产物 .bin/.elf/.map，见 backups/README.md §6。\n')
    f.write('本快照**不含** backups/README.md 自己：它本来就住在根 A 顶层，不是"拷进 docs/ 的文档"。\n')
    f.write('本快照**不含** dev_log/20260919.md：那只带 1 行 PROV_PASS 明文（09-23 08:22:52 起登记的 5 只里之 ②，未跟踪）'
            '⇒ 拷它等于把明文再复制一份进备份根，与 README §6 那条红线相反；它因此在仓库与备份根两侧都没有副本，只有工作树那一只。\n')
    f.write('拷贝前有一道明文凭据闸（口令由脚本从宏读出、不打印）：%d 只源全扫，命中数必须为 0 才动手；本次 HITS=0。\n' % len(SRCS))
    f.write('派生自 hardware/refresh_docs_snapshot_r61b.py（第十二遍脚本 = r61b 代；两只派生源同在 hardware/，路径 grep 得到，'
            '本代派生器 hardware/r61c_sync/scripts/derive_docs_r61c.py：改动以替换表为准，不靠手抄。'
            '更早的第八遍在 hardware/ht305_sync/scripts/ 里，那是末版 gen 24 之前的事），三处改动：'
            '①SRCS 加 1 只：`updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md`（r61b 收口件的阶段归档，本代唯一新增源；本批无新判据摘录、无新板档案、无新 dev_log 日期文件）；'
            '②完整性守卫的只数下限从 48 抬到 49（守卫本体、MUST 五只、明文凭据闸、逐字节回读断言、'
            "'派生那只必须真在仓库里'那道 r57 新增的闸，全部原样继承，不重写）；"
            '③本行本身（上一代这里写的是"从 r57 派生、加 8 只 + 只数下限 40→48"）。'
            '本 NOTE 里所有只数仍由脚本插值，两道自核照旧：表格行数 == len(rows)、"现读 %d 只源"这句真的在 NOTE 里。'
            '本次运行：源清单现读 %d 只，运行数以 stdout 的 CRED_GATE / FILES / TABLE_ROWS 三行为准。\n' % (len(SRCS), len(SRCS)))

print('SNAPSHOT_AT', t0.strftime('%Y-%m-%d %H:%M:%S'))
print('FILES', len(rows))
note_txt = open(note, encoding='utf-8').read()
table_rows = len([l for l in note_txt.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
assert table_rows == len(rows), 'NOTE 表格行数 %d != rows %d' % (table_rows, len(rows))
assert ('现读 %d 只源' % len(SRCS)) in note_txt, 'NOTE 里的只数没有插值成 SRCS 现读数'
print('TABLE_ROWS', table_rows, '== FILES', len(rows))
print('NEW_ONES', len([r for r in rows if '\tNEW -> ' in r]))
print('NOTE_BYTES', os.path.getsize(note))
