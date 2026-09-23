# 第 10 代同步工具派生：逐字从第 9 代（r51*）派生，**对每个替换断言命中数**、**源不存在即 ABORT**、
# **目标已存在且逐字节不等即 ABORT**（SKIP_IDENTICAL 让整代可复跑）。口径来自 §34.8-② / §36.2 / gen 12 那格。
# 本代比上一代多一件事：**派生之后再把"只在上一代为真"的措辞改对**（下面每个文件第二条替换就是干这个的）。
# 动机：派生器会把上一代"恰好没踩到"的缺陷一起派生过来（FreqErr ht305 段那一格），而这次要派的是**自述句** ——
# "本代第一次真的执行""本代补的更强口径""这次栽在本轮新写的脚本身上"这三句在 r52 字节里都会变成假话。
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
SCR = os.path.join(REPO, 'hardware', 'ht305_sync', 'scripts')

TOP_OLD = 'zizhao_20260924_r51final'
TOP_NEW = 'zizhao_20260924_r52final'

GEN_SYNC = [(TOP_OLD, TOP_NEW), ('r51', 'r52')]
GEN_RTEST = [(TOP_OLD, TOP_NEW), ('zsynctest11', 'zsynctest12'), ('r51', 'r52')]

JOBS = [
    ('sync_r51.py', 'sync_r52.py', GEN_SYNC, 'utf-8'),
    ('r51_upload.ps1', 'r52_upload.ps1', GEN_RTEST, 'utf-8-sig'),
    ('chk_r51.ps1', 'chk_r52.ps1', [('gen-9', 'gen-10'), ('r51', 'r52')], 'utf-8-sig'),
    ('r51_cutoff_delta.py', 'r52_cutoff_delta.py', GEN_SYNC, 'utf-8'),
    ('r51_listdiff.py', 'r52_listdiff.py',
     [('第 9 代', '第 10 代'), ('r51', 'r52'),
      ('这次栽在**本轮新写的差集脚本**自己身上',
       '当时栽在**那一代新写的差集脚本**自己身上（本文件是逐字派生的产物，这句说的是它的祖先、不是本代）')],
     'utf-8'),
    ('land_r51_evidence.py', 'land_r52_evidence.py',
     [('第 9 代', '第 10 代'), ('r51', 'r52'),
      ('# 本代是 R49 复查给 `land_r49_evidence.py` 补的两条守卫（聚合行缺失即 ABORT + 摘要必须是 64 位十六进制 + 落地记录自己落盘）\n'
       '# **第一次真的执行**：上一代那一次跑的是不含守卫的旧字节，所以"守卫写好了"在那一代只是盘上事实、不是运行过的事实。',
       '# 本代跑的是 R49 复查给 `land_r49_evidence.py` 补的那两条守卫（聚合行缺失即 ABORT + 摘要必须是 64 位十六进制 + 落地记录自己落盘）：\n'
       '# 它们的**首个真载体是第 8 代**（README 代次表 gen 12 那格②），本代只是延续 ⇒ 不自称"第一次真的执行"（派生会把上一代的自述句一起派过来）。')],
     'utf-8'),
    ('r51_roundtrip.py', 'r52_roundtrip.py',
     [(TOP_OLD, TOP_NEW), ('zsynctest11', 'zsynctest12'), ('第 9 代', '第 10 代'), ('R51', 'R52'), ('r51', 'r52'),
      ('# 第 10 代同步补的一条**更强口径**：',
       '# 第 8 代补、第 10 代仍在跑的一条**更强口径**：'),
      ('# 本脚本让第 10 代的"远端那份带明文"这一句重新拿到**从远端带回的字节**作依据，而不是靠"包 == 工作树"传递。',
       '# 本脚本自第 8 代起每代都跑，让"远端那份带明文"这一句始终拿到**从远端带回的字节**作依据（本代 = 第 10 代），而不是靠"包 == 工作树"传递。')],
     'utf-8'),
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
    want = txt.encode(enc)          # utf-8-sig 时含 BOM，与下面写盘的字节同一算法
    if os.path.exists(dp):
        # 目标已存在时：只有"逐字节就等于本代会产出的那份"才允许跳过（让整代派生可复跑，
        # 不必为了重跑而删文件）；任何差异一律 ABORT，不覆盖。
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
    # 只有 .ps1 必须带 BOM（PowerShell 5.1 按 GBK 解码无 BOM 的 UTF-8）；.py 不带 BOM 才对
    need_bom = dst.endswith('.ps1')
    ok = (bom if need_bom else not bom) and (nonascii or not need_bom)
    print('DERIVED', dst, len(raw), 'B |', ' '.join(counts),
          '| BOM=%s NONASCII=%s NEED_BOM=%s OK=%s' % (bom, nonascii, need_bom, ok))
    if not ok:
        print('ABORT: 编码形态不符合本代口径', dst)
        sys.exit(1)

# 派生完把"本代不再引用上一代解包根/上一代包名"这件事读一遍：上一代栽过的地方（把 zsynctest8 喂给差集器）
DESTS = [d for _, d, _, _ in JOBS]
PREV = ['r51final', 'zsynctest11', '第 9 代', 'r51_', 'R51']
for dst in DESTS:
    t = open(os.path.join(SCR, dst), encoding='utf-8-sig').read()
    left = [k for k in PREV if k in t]
    print('LEFTOVER_CHECK', dst, left if left else 'CLEAN')
    if left:
        print('ABORT: 本代字节里还留着上一代的标识', dst, left)
        sys.exit(1)

# 语法体检一律用 ast.parse —— 不在归档目录里跑 py_compile（它会落 .pyc，与清单 md5 脱钩，见 FreqErr 本段"检查动作污染被检查物"）
for dst in DESTS:
    if dst.endswith('.py'):
        import ast
        ast.parse(open(os.path.join(SCR, dst), encoding='utf-8').read())
        print('AST_OK', dst)
