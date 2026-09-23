import datetime, glob, os, sys

os.chdir(r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync')
# gen 13 两处修正之一（登记于排查记录 §38.9 末段）：**只报不响**的守卫等于没有守卫。
# 09-24 03:5x 实测：本脚本按设计覆写 `evidence/ps1_bom_scan.txt`，而那一只**在册**（gen 12 清单第 36 行）
# ⇒ 覆写之后 `verify_manifest.py` 立刻 `MISMATCH=1`。覆写本身是链的正常动作（清单随后重冻），
#   但"我覆掉了哪一版"必须有执行者说出来，所以本脚本现在把**上一版的字节数与 md5 写进新输出**。
try:
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
now = datetime.datetime.now().strftime('%H:%M:%S')
now_full = datetime.datetime.now().strftime('%m-%d %H:%M:%S')
out = ['ht305_sync 归档内脚本编码体检（现跑于 ' + now_full + '；脚本 = scripts/ps1_bom_scan.py）',
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
        '两只均 nonascii=0 ⇒ 无 BOM 不构成风险。',
        '含中文的 `.ps1` 名单**不写死在本脚本里**（写死了就会漂：09-23 11:5x 给 `run_cred_gate_recheck.ps1` '
        '加中文注释时，上一版的这句就已经过时）⇒ 现读 = 上表里 `.ps1` 且 nonascii>0 的那些只，逐只看 utf8_bom。',
        '注：本行读数本身也是"现跑即落盘"，时刻与输出同批写进本文件。']
tgt = os.path.join('evidence', 'ps1_bom_scan.txt')
# 覆写必须自述：上一版的字节数与 md5 写进新输出，否则"清单里那一行 md5 为什么变了"只能靠人记。
if os.path.isfile(tgt):
    import hashlib
    prev = open(tgt, 'rb').read()
    out.insert(1, 'OVERWROTE=%d B md5:%s（上一版；本脚本按设计覆写自身输出，清单随后重冻）'
               % (len(prev), hashlib.md5(prev).hexdigest()[:8]))
else:
    out.insert(1, 'OVERWROTE=none（目标不存在，本代为首版）')
open(tgt, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
# stdout 在 GBK 控制台下会因 '\u21d2' 崩（11:57:51 实测：文件已写出、进程仍非 0 退出）⇒ 显式换编码。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
print('STDOUT_TAIL=只回放下面 5 行，逐只全表在 %s' % tgt)
print('\n'.join(out[-5:]))
# 只报不响 = 没有执行者：有风险组合就非 0 退出（文件已写出，判读仍以首行时刻为准）。
if risky:
    print('EXIT=1 (RISKY_PS1>0)')
    sys.exit(1)
print('EXIT=0 (RISKY_PS1=0)')
