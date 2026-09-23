import json, os, datetime, sys

tmp = os.path.join(os.environ['TEMP'], 'r44b_report_raw.txt')
content = json.loads(open(tmp, encoding='utf-8').read())[0]['content']
now = datetime.datetime.now().strftime('%H:%M:%S')
dst = r'C:/Users/david/Documents/all_projects/自招学习/hardware/20260923_R44终态复查报告原文.txt'
if os.path.exists(dst):
    print('ABORT: target already exists', dst)
    sys.exit(1)

lines = [
    'R44 终态复查（空上下文故障检测子 agent）报告原文（逐字转录，未删改）',
    '',
    '转录动作时刻：`python -c datetime.now()` = 09-23 ' + now + '（本文件自身的生成时刻；'
    '报告交回时刻以下面正文里的读数为准，不在此重复指认）。',
    '来源：对话存档里那条 `tool_result` 的 `content` 字段（副本落在 `%TEMP%\\r44b_report_raw.txt`，'
    '14,707 B / 解码后 ' + str(len(content)) + ' 字符），由本脚本 JSON 解码后直接写入，未经人工转写。',
    '处置：逐条复核与采纳/驳回见 `hardware/20260919_墨水屏点屏排查记录.md` §33.5，本文件是该表的原文依据。',
    '口径提示：正文引用的 `%TEMP%` 取证件（`ht305_agg.ps1`、`sync_r45.py`、`r45_upload.ps1` 等）'
    '当时只在临时目录、仓库内无副本 ⇒ 报告末条建议「把它们收进项目」已采纳，落地位置见 §33.5 末行。',
    '-' * 72,
]
open(dst, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n\n' + content + '\n')
print('WROTE', dst, os.path.getsize(dst), now)
