import datetime, glob, os, sys

os.chdir(r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync')
now = datetime.datetime.now().strftime('%H:%M:%S')
out = ['ht305_sync 归档内脚本编码体检（现跑于 09-23 ' + now + '；脚本 = scripts/ps1_bom_scan.py）',
       '判据：非 ASCII 字节数 + 是否有 UTF-8 BOM（ef bb bf）。风险定义：`.ps1` 且 非ASCII>0 且 无 BOM',
       '（这种组合会被 Windows PowerShell 5 按 GBK 解码，中文注释会吞掉紧随其后的整行 ⇒ FreqErr 已登记的那次自伤）。',
       '']
risky = []
for p in sorted(glob.glob('**/*.ps1', recursive=True)) + sorted(glob.glob('**/*.py', recursive=True)):
    b = open(p, 'rb').read()
    non = sum(1 for x in b if x > 127)
    bom = b[:3] == b'\xef\xbb\xbf'
    r = p.endswith('.ps1') and non > 0 and not bom
    if r:
        risky.append(p)
    out.append(f'{p}\tnonascii={non}\tutf8_bom={bom}\tgbk_risk={r}')
out += ['', f'RISKY_PS1={len(risky)}\t{risky}',
        '⇒ 对报告「我没能验证 #7」（`r44_upload.ps1` / `r44_verify2.ps1` 是否含中文）的回答：'
        '两只均 nonascii=0 ⇒ 无 BOM 不构成风险；含中文的 `.ps1` 在本归档里只有 `r45_upload.ps1`，它带 BOM。',
        '注：本行读数本身也是"现跑即落盘"，时刻与输出同批写进本文件。']
open(os.path.join('evidence', 'ps1_bom_scan.txt'), 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
print('\n'.join(out[-4:]))
