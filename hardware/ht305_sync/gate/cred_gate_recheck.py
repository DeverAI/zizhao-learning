"""明文门·复验版：扫 hardware/ht305_sync/ 归档后的**全部**文件（而不是 %TEMP% 候选）。
只写文件名 + 命中次数 + 总只数，绝不写/打印口令。
用法：由 gate/run_cred_gate_recheck.ps1 设置环境变量 HT305_TMP_FOR_GATE 后调用：
      python cred_gate_recheck.py <输出文件路径>
"""
import datetime, os, re, sys

DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
SRC = r'C:/Users/david/Documents/all_projects/自招学习/hardware/zizhao-esp32s3/main/provision_ap.c'

m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
if not m:
    print('ABORT: 读不到 PROV_PASS 宏本体'); sys.exit(1)
prov = m.group(1)

env = os.environ.get('HT305_TMP_FOR_GATE')
ssh = env.encode('utf-8') if env else None
if env:
    del os.environ['HT305_TMP_FOR_GATE']

now = datetime.datetime.now().strftime('%H:%M:%S')
lines = ['ht305_sync 归档后的明文门复验（现跑于 09-23 ' + now + '，脚本 = gate/cred_gate_recheck.py）',
         '判据：字节级 count(口令明文)。PROV_PASS 由脚本按 `#define PROV_PASS` 现读；'
         'SSH 口令由 PS 侧 DPAPI 现解后经环境变量传入 —— 两侧都不内嵌字面量。',
         '口径：扫的是**归档后**的全部文件（含本门脚本自身与 README/MANIFEST），排除本输出文件。', '']

n = hits_p = hits_s = 0
for root, dirs, fs in os.walk(DST):
    for fn in sorted(fs):
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, DST).replace('\\', '/')
        if rel.startswith('evidence/cred_gate_recheck'):
            continue
        b = open(p, 'rb').read()
        n += 1
        hp = b.count(prov)
        hs = b.count(ssh) if ssh else 0
        hits_p += hp
        hits_s += hs
        if hp or hs:
            lines.append('HIT ' + rel + ' PROV_PASS=' + str(hp) + ' SSH=' + str(hs))
lines += ['', 'FILES_SCANNED=' + str(n),
          'PROV_PASS_TOTAL_HITS=' + str(hits_p),
          'SSH_TOTAL_HITS=' + (str(hits_s) if ssh else 'SKIPPED(环境变量未设置)')]

out_path = os.path.join(DST, sys.argv[1])
open(out_path, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
print('WROTE', os.path.basename(out_path), '|', lines[-3], lines[-2], lines[-1])
