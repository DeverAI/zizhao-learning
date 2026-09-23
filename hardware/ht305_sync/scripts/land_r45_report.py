"""逐字转录 R45 收口空上下文复查报告（`#118`）：从会话存档 jsonl 里取那条 task-notification 的 <result> 正文。
动机：本仓库已经吃过两次"报告只活在会话存档里 ⇒ 下一轮无法引用"的亏（P0-1 那条本身就是这么来的）。
本脚本只做"读 + 切 + 写"，不改动任何已有文件；目标文件若已存在即 ABORT。"""
import datetime, os, sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/2c637e58-0a6e-4412-983d-959b7d542219.jsonl'
DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/20260923_R45复查报告原文.txt'
LN, TASK_ID = 39979, 'a30ea38d2ee6aff52'
if os.path.exists(DST):
    print('ABORT: 目标已存在，不覆盖', DST); sys.exit(1)

import json
raw = open(SRC, encoding='utf-8').readlines()[LN - 1]
d = json.loads(raw)
p = d['attachment']['prompt']
assert TASK_ID in p and p.count('<result>') == 1 and p.count('</result>') == 1, '取到的不是那一条通知'
body = p.split('<result>', 1)[1].split('</result>', 1)[0].strip('\n')
now = datetime.datetime.now().strftime('%H:%M:%S')
head = [
    'R45 收口 · 空上下文故障检测复查报告（只读审计，未改任何文件）——原文逐字转录件',
    '转录时刻：2026-09-23 ' + now + '（本机 `Get-Date`/`datetime.now()` 同一只钟）',
    '来源：会话存档 ' + SRC,
    '      第 ' + str(LN) + ' 行那条 `task-notification`，`task-id` = `' + TASK_ID + '`（'
    + '通知正文里那句 summary 原文是 `Agent "R45 收口空上下文复查" finished`），',
    '      其 `output-file` 指向 `.../tasks/' + TASK_ID + '.output`；本件 = 该通知里 `<result>` 与 `</result>` **之间**的全部内容，',
    '      未删改、未重排（含报告自己的"我没能验证的清单"6 条与"我试着推翻但成立的"那一段）。',
    '转录方式：脚本 `hardware/ht305_sync/scripts/land_r45_report.py`（**先于清单存在 ⇒ 本件与这只脚本都在下一版清单里**，可原地重跑）。',
    '处置：逐条见 `hardware/20260919_墨水屏点屏排查记录.md` **§34.2**（17 行：P0 2 / P1 4 / P2 5 / 没能验证 6）。',
    '' , '⚠ 报告内的行号（如 `done.md:1038`、`dev_log/20260923.md:172`）与只数（59/61 等）都是**它自己量测窗口内**的快照：',
    '  它在头部就声明过"审计期间工作树仍在被编辑，同一只 `MANIFEST.txt` 三次现读不同"⇒ 引用这些数请连窗口一起引，别当实时状态。',
    '=' * 72, '', '',
]
open(DST, 'w', encoding='utf-8', newline='').write('\n'.join(head + [body]) + '\n')
print('WROTE', os.path.basename(DST), 'lines=', len(head) + len(body.splitlines()),
      'bytes=', os.path.getsize(DST), 'at', now)
