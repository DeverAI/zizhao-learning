# R55 的**第二遍**体检载体。动因：本代在 12:37:02（gen 23）冻结**之后**又真改了工具
# （`verify_manifest.py` 加终态载体 + `gen_manifest.py` 单一时刻源 + `r55_cred_recount.py` 改半径口径），
# 而 `chk_r55.ps1` 那只只管 `r55_upload.ps1` 一只 —— 改过的工具没有任何一只被解析过就进了下一代清单。
# 红线（本仓库既有口径）：**不在归档目录内跑 `py_compile`**（它往 `scripts/__pycache__/` 落 `.pyc`，
# 而 `gen_manifest.py` 见派生字节即 ABORT）⇒ 这里只用 `ast.parse`，且**不 import** 被检模块。
# 阳性对照：拿一段确定语法错的内存字符串喂同一把尺，必须**报错**才允许打 PARSE_ERRORS=0。
import ast
import hashlib
import os
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DST = os.path.join(REPO, 'hardware', 'ht305_sync')
EV = os.path.join(DST, 'evidence')
TARGETS = ['scripts/verify_manifest.py', 'scripts/gen_manifest.py', 'scripts/r55_cred_recount.py']

# 载体轮换：`evidence/r55_parse_check.txt` 是第一遍（只管 r55_upload.ps1）那只，**不覆盖**。
_cands = ['r55_parse_check_2.txt'] + ['r55_parse_check_2_%d.txt' % i for i in range(3, 11)]
OUT = None
for _c in _cands:
    if not os.path.isfile(os.path.join(EV, _c)):
        OUT = os.path.join(EV, _c)
        break
if OUT is None:
    print('ABORT: 第二遍体检载体名 9 只全被占，拒绝覆写')
    sys.exit(2)

# 阳性对照（只在内存里，不落盘）：真语法错必须被这把尺抓到。
try:
    ast.parse('def f(:\n  pass\n')
    ctrl = 'POSITIVE_CONTROL=FAIL（该报错的字符串没报错 ⇒ 这把尺不响，下面所有 0 都不作数）'
    ctrl_ok = False
except SyntaxError:
    ctrl = 'POSITIVE_CONTROL=OK（同尺在已知坏字符串上抛了 SyntaxError）'
    ctrl_ok = True

lines = ['CHKB_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         'SCOPE=本代冻结后被改写的工具 %d 只（ast.parse，不 import、不 py_compile）' % len(TARGETS),
         'PRIOR=evidence/r55_parse_check.txt（第一遍只覆盖 scripts/r55_upload.ps1 一只）']
bad = []
for rel in TARGETS:
    p = os.path.join(DST, rel.replace('/', os.sep))
    if not os.path.isfile(p):
        bad.append(rel + ' 不存在')
        lines.append('TARGET=%s MISSING' % rel)
        continue
    b = open(p, 'rb').read()
    n_line = len(b.decode('utf-8', 'replace').splitlines())
    try:
        ast.parse(b.decode('utf-8'))
        v = 'AST_OK'
    except SyntaxError as e:
        v = 'AST_FAIL line=%s msg=%s' % (e.lineno, e.msg)
        bad.append(rel + ' ' + v)
    if n_line < 20:
        bad.append(rel + ' 行数=%d 太小（读空文件时读数全绿那一族的哨兵）' % n_line)
        v += ' LINES_TOO_FEW'
    lines.append('TARGET=%s bytes=%d lines=%d md5=%s verdict=%s'
                 % (rel, len(b), n_line, hashlib.md5(b).hexdigest()[:8], v))
lines.append(ctrl)
if not ctrl_ok:
    bad.append('阳性对照未响')
lines.append('VERDICT=' + ('TOOLS_PARSE_CLEAN' if not bad else 'TOOLS_DIRTY'))
for x in bad:
    lines.append('  BAD ' + x)
txt = '\n'.join(lines) + '\n'
open(OUT, 'w', encoding='utf-8', newline='').write(txt)
print(txt)
print('CARRIER=hardware/ht305_sync/evidence/' + os.path.basename(OUT))
sys.exit(0 if not bad else 1)
