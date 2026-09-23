import re, os, sys
src = open('hardware/zizhao-esp32s3/main/provision_ap.c', encoding='utf-8').read()
pw = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', src).group(1)
print('len(pw) =', len(pw), ' sha-ish tail =', pw[-2:])
cands = [
 'FreqErr.md','todo.md','done.md','dev_log/20260922.md',
 'updates/20260922_墨水屏收尾R43.md',
 'updates/20260923_墨水屏R43真机首烧与归档尾.md',
 'hardware/20260919_墨水屏点屏排查记录.md',
 'hardware/烧录须知.md',
 'hardware/20260921_R33复查报告原文.txt',
 'hardware/20260922_R43复查报告原文_code.txt',
 'hardware/20260922_R43第四次复查报告原文_A.txt',
 'hardware/20260922_R43第四次复查报告原文_B.txt',
 'hardware/20260922_R43第四次复查报告原文_C.txt',
 'hardware/20260922_R43真机首烧日志_40s.txt',
 'hardware/20260922_R43真机首烧日志_120s.txt',
 'hardware/zizhao-esp32s3/main/axp_panel_power.c',
 'hardware/zizhao-esp32s3/main/eink_display.c',
 'hardware/zizhao-esp32s3/main/epd_driver.c',
]
bad=[]
for f in cands:
    if not os.path.exists(f):
        print('MISSING', f); bad.append(f); continue
    t = open(f, 'rb').read().decode('utf-8', 'replace')
    n = t.count(pw)
    print(('HIT ' if n else 'ok  ') + str(n).rjust(3), f)
    if n: bad.append(f)
print('--- stage candidates:', len(cands), 'with plaintext:', len(bad))
for b in bad: print('   !', b)
