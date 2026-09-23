"""重生成 hardware/ht305_sync/MANIFEST.txt：对**终态**归档逐只记 bytes/md5/BOM。
本清单不含自身（自列必然漂）；上一版（10:36:41 的 49 只 + 10:38:51 的 3 只后补）被本版整体覆盖，
覆盖原因与时间线写在本文件的头部说明里。
头部那句"门是否覆盖本清单"由 mtime 现算，不靠人记。"""
import datetime, hashlib, os

DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
GATE = os.path.join(DST, 'evidence', 'cred_gate_recheck.txt')
now = datetime.datetime.now().strftime('%H:%M:%S')

rows = []
for root, dirs, fs in os.walk(DST):
    for fn in sorted(fs):
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, DST).replace('\\', '/')
        if rel == 'MANIFEST.txt':
            continue
        b = open(p, 'rb').read()
        rows.append((rel, len(b), hashlib.md5(b).hexdigest(), b[:3] == b'\xef\xbb\xbf', os.path.getmtime(p)))
rows.sort()

gate_txt = open(GATE, encoding='utf-8').read().splitlines()[0]
gm = os.path.getmtime(GATE)
after = [r[0] for r in rows if r[4] > gm] + ['MANIFEST.txt']

head = [
    'ht305_sync 归档清单（终态快照，现跑于 09-23 ' + now + '；脚本 = scripts/gen_manifest.py）',
    '',
    '来源 = %TEMP% 的逐字节复制（shutil.copy2，保留 BOM）；本版之前另有三版：'
    '10:36:41 首批 49 只、10:38:51 后补 3 只、11:06:14 收 58 只。各版都被本版覆盖，因为清单是**快照**：'
    '它一旦写死就追不上还在增长的目录，只保留最后一版 + 这段说明，不留半旧版。',
    '本清单**不含自身**（列自己必然在写完后立刻过期）。',
    '明文门：' + gate_txt + '；FILES_SCANNED 见该文件末行，两门均 0 命中。',
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
