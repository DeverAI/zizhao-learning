# 第 12 代同步工具派生（r53* -> r54*）：逐字派生，**对每个替换断言命中数**、**源不存在即 ABORT**、
# **目标已存在且逐字节不等即 ABORT**（SKIP_IDENTICAL 让整代可复跑）。口径来自 derive_r53.py（第 11 代那一次）。
# 本代没有新增"自述句订正"：上一代（r53）已经把三处"只在上一代为真"的句子改成了**跨代成立**的写法
# （"首个真载体是第 8 代、本代只是延续""这句说的是它的祖先、不是本代""自第 8 代起每代都跑"），
# 所以 generic 的 `第 11 代 -> 第 12 代` 不会造出假话。这一点在本脚本末尾用 LEFTOVER_CHECK 反证。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

TOP_OLD = 'zizhao_20260924_r53final'
TOP_NEW = 'zizhao_20260924_r54final'

GEN_SYNC = [(TOP_OLD, TOP_NEW), ('r53', 'r54')]
GEN_RTEST = [(TOP_OLD, TOP_NEW), ('zsynctest13', 'zsynctest14'), ('r53', 'r54')]
GEN_GEN = [('第 11 代', '第 12 代')]

JOBS = [
    ('sync_r53.py', 'sync_r54.py', GEN_SYNC, 'utf-8'),
    ('r53_upload.ps1', 'r54_upload.ps1', GEN_RTEST, 'utf-8-sig'),
    ('chk_r53.ps1', 'chk_r54.ps1', [('gen-11', 'gen-12'), ('r53', 'r54')], 'utf-8-sig'),
    ('r53_cutoff_delta.py', 'r54_cutoff_delta.py', GEN_SYNC, 'utf-8'),
    # 注意：上一代的 listdiff 里**没有**完整包名（现跑 `txt.count(TOP_OLD)` = **0**，只有 `r53final` 这一小截），
    # 所以这里不列 TOP_OLD —— 列了会被下面那条"0 命中即 ABORT"的闸拦住。包名换代由 'r53'->'r54' 一条覆盖。
    ('r53_listdiff.py', 'r54_listdiff.py', GEN_GEN + [('r53', 'r54')], 'utf-8'),
    ('land_r53_evidence.py', 'land_r54_evidence.py', GEN_GEN + [('r53', 'r54')], 'utf-8'),
    ('r53_roundtrip.py', 'r54_roundtrip.py',
     [(TOP_OLD, TOP_NEW), ('zsynctest13', 'zsynctest14')] + GEN_GEN + [('R53', 'R54'), ('r53', 'r54')], 'utf-8'),
    # 09-24 08:5x 补的作业：本代首跑**漏了这只尾件落地器** ⇒ `r54_roundtrip.txt` 只活在 %TEMP%、
    # evidence/ 里查无载体（FreqErr (59)/(63) 那一族的第 4 次：取证那一步自己没落盘）。
    # 第 11 代已把它的本体入档，所以这一代起它是**派生表里的常任作业**，不再靠我记得手动拷。
    ('extra_land_r53.py', 'extra_land_r54.py', GEN_GEN + [('r53', 'r54')], 'utf-8'),
]

for src, dst, reps, enc in JOBS:
    sp, dp = os.path.join(SCR, src), os.path.join(SCR, dst)
    if not os.path.isfile(sp):
        print('ABORT: 派生源不存在', src)
        sys.exit(1)
    txt = open(sp, encoding='utf-8' if enc == 'utf-8' else 'utf-8-sig').read()
    counts = []
    for a, b in reps:
        n = txt.count(a)
        if n == 0:
            print('ABORT: 替换串在本代源里 0 命中 %s -> %s (%s)' % (a, b, src))
            sys.exit(1)
        txt = txt.replace(a, b)
        counts.append('%s->%s:%d' % (a[:18], b[:18], n))
    want = txt.encode(enc)
    if os.path.exists(dp):
        if open(dp, 'rb').read() == want:
            print('SKIP_IDENTICAL', dst, len(want), 'B')
            continue
        print('ABORT: 目标已存在且与本代派生结果不等，不覆盖', dst)
        sys.exit(1)
    with open(dp, 'w', encoding=enc, newline='') as f:
        f.write(txt)
    raw = open(dp, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    nonascii = any(x > 0x7F for x in raw)
    need_bom = dst.endswith('.ps1')
    ok = (bom if need_bom else not bom) and (nonascii or not need_bom)
    print('DERIVED', dst, len(raw), 'B |', ' '.join(counts),
          '| BOM=%s NONASCII=%s NEED_BOM=%s OK=%s' % (bom, nonascii, need_bom, ok))
    if not ok:
        print('ABORT: 编码形态不符合本代口径', dst)
        sys.exit(1)

DESTS = [d for _, d, _, _ in JOBS]
PREV = ['r53final', 'zsynctest13', '第 11 代', 'r53_', 'R53']
for dst in DESTS:
    t = open(os.path.join(SCR, dst), encoding='utf-8-sig').read()
    left = [k for k in PREV if k in t]
    print('LEFTOVER_CHECK', dst, left if left else 'CLEAN')
    if left:
        print('ABORT: 本代字节里还留着上一代的标识', dst, left)
        sys.exit(1)

# 语法体检一律 ast.parse（不在归档目录里跑 py_compile：它会落 .pyc，与清单 md5 脱钩）
for dst in DESTS:
    if dst.endswith('.py'):
        import ast
        ast.parse(open(os.path.join(SCR, dst), encoding='utf-8').read())
        print('AST_OK', dst)

# 阳性对照：LEFTOVER_CHECK 用的那把尺子必须**能**报警 —— 拿上一代（r53_*）字节喂同一份 PREV 名单，
# 命中数必须 > 0。缺这一步，"CLEAN"就只是"尺子读不到东西"的同义反复（FreqErr (76) 那条的同类）。
for src in ['r53_upload.ps1', 'land_r53_evidence.py']:
    t = open(os.path.join(SCR, src), encoding='utf-8-sig').read()
    hit = [k for k in PREV if k in t]
    print('CONTROL_OLDGEN', src, len(hit), hit[:3])
    if not hit:
        print('ABORT: 阳性对照失败 —— PREV 名单在上一代字节里也 0 命中，这把尺恒绿')
        sys.exit(1)
