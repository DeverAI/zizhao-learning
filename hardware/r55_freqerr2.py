# R55 尾巴批的 FreqErr 落地器（本批 6 条新错误类型 + 台账行）。
# 位置：`hardware/`（**归档目录之外**）—— gen 24 已于 12:53:39 冻成末版，此后任何一只文件落进
# `hardware/ht305_sync/` 都会把 `verify_manifest.py` 的 `UNLISTED` 顶成非 0 ⇒ 末版自动降级（§38.19 ④ 那条新规）。
# 纪律（全部来自本台账已有条目）：①正文里不写反斜杠（(1813) 那族：CR 会静默损坏指针）；
# ②台账的"之后"两个数一律对**将被写出的完整字节串**现算，先占位、数完回填、回填后再数要求不变 ((99))；
# ③写盘后独立回读另一次调用比对；④纯 CRLF 文件按 CRLF 追加；⑤载体不覆写，重跑另起 `_2`。
import hashlib
import os
import re
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
DOC = os.path.join(REPO, 'FreqErr.md')
HDIR = os.path.join(REPO, 'hardware')
_cands = ['r55_freqerr2.txt'] + ['r55_freqerr2_%d.txt' % i for i in range(2, 10)]
CARRIER = None
for _c in _cands:
    if not os.path.exists(os.path.join(HDIR, _c)):
        CARRIER = os.path.join(HDIR, _c)
        break
assert CARRIER, 'ABORT: 载体名 9 只全被占，拒绝覆写'

ENTRIES = [
    [
        '[错误类型] **同一次运行里取了两次 `now()` ⇒ 中间隔一趟全目录哈希遍历就跨秒，把"清单是不是脚本跑出来的"这句最重的话判成假红（gen 22 首咬，判据已潜伏 12 个世代）**',
        '→ 症状：`evidence/r55_verify_manifest_gen22_stale.txt`（12:34:xx 那次）同一行里 `ROWS=378 / MISMATCH=0 / MISSING=0 / UNLISTED=0`、汇总三字段逐项 `OK`，裁决却是 `MANIFEST_STALE`；**全绿的一行给了红**。现读根因：清单头部时刻 12:34:41、代次日志末行 12:34:42 —— 差 1 秒。',
        '→ 形状：**判据把"展示用的时刻"当成了"同源证据"**。`gen_manifest.py` 里 `now_full`（进头部）与写日志那次 `datetime.now()`（进日志）是**两只独立调用**，中间隔着 378 只文件的 md5 遍历 ⇒ 跨秒是概率事件，不是错误路径。判据本身（"日志末行逐字符 == 清单汇总行"）自 gen 9 就在，**它只在跨秒那一瞬才假**。',
        '→ 为什么它比一般假红贵：①红的那句是"清单不是脚本跑出来的"——整条冻结链最重的一句，一次假红会让下一轮**真红**没人信；②潜伏 12 代说明"平时不响的尺"不等于"对的尺"，概率性判据在归档链上根本不该进判决。',
        '→ 正确做法：①一次运行**只取一次**时刻，其余位置由它派生（`now = now_full.split(" ")[1]`）⇒ 两边相等**由构造保证**，不再靠运气；②**判决与展示分家**：进判据的只有三个数字字段（只数 / 字节 / BOM 只数），时刻只并列打印、不参与判决（旧日志行仍可能跨秒，宽容差放在 verifier 是错的）；③写"必须逐字符相等"的判据前先问一句：**两端是不是同一个变量的两次读？**',
        '→ **同族**：项目记忆 (57)（裸 `grep -c` 是快照，会随引用漂）、(97)（预期只写成"式子 + 本遍两端实测"）、用户记忆 `feedback-verifiable-acceptance.md`「数字连算法与漏判」「汇总行不许只认一种格式」。',
    ],
    [
        '[错误类型] **"跑绿了却没留证据"：冻结链最后一步 `verify_manifest.py` 的裁决只打在 stdout ⇒ 那句 `rc=0` 事后不可复算（gen 23），而"由人抄 rc"这一环从来没有载体覆盖过它自己**',
        '→ 症状：gen 23（12:36:53 门 `FILES_SCANNED=381` → 12:37:02 清单 `TOTAL=380`，关系式成立）复核 `rc=0 / MANIFEST_STILL_TRUE`，我把它抄进 README。12:40:15 之后 `evidence/` 又落 2 只 ⇒ 今天拿这份清单回验 gen 23 只会给 STALE，**那句绿已经永久无法证明**。',
        '→ 形状：与 (64)"记录取证那一步自己没落盘"同族，但这次多出**定位**这一层：同一条链上的**门**与**清单**早就各自把读数写进 `evidence/`，**只有末端那一步没有** ⇒ 缺陷不在"我忘了抄"，在"抄 rc 的那个人是唯一执行者"。人抄的读数天生不可复算。',
        '→ 为什么它危险：**末端恰好是唯一有资格宣布"这一代可引"的那一步**，它没有载体 ⇒ 前面所有载体都在为一句无证据的话背书；而"重跑一遍让它变绿"在这条链上是零成本、且重跑本身就会被本条定罪。',
        '→ 正确做法：①**工具自己落盘**：verifier 在给出裁决的**同一次运行**里把整段 stdout 写进 `hardware/verify_manifest_<被复核那代时刻>.txt`（归档目录**之外**，故不参与 `UNLISTED` 口径），并把裁决写进 `VERIFY_RC=` 行、`sys.exit(_rc)`；②登记句必须**同时**给 `rc` 与载体文件名，缺一不登记；③对已经丢掉的绿**不重跑洗**，改立"红原件"当物证：12:46 那遍对 gen 23 清单给出 `VERIFY_RC=1 / MANIFEST_STALE`（`hardware/verify_manifest_0924123702.txt`），这条红的可复算性，就是那句绿不可复算性的替代证据。',
        '→ **同族**：项目记忆 (49)（取证必须进仓库）、(64)、(75)（登记"已跑完"前先跑一次并抄 `rc`）、(81)（首跑崩溃的取证脚本也要入库）、(96)。',
    ],
    [
        '[错误类型] **为了让计数"看起来干净"而静默排除某一只目标 ⇒ 造了一把看不见的尺（明文复扫首跑把"声明该文件名的脚本自己"排掉，载体上只剩一个数、看不出半径被缩过）**',
        '→ 症状：`scripts/r55_cred_recount.py` 第一版在判"抓回件文件名有没有被写进仓库"时，跳过声明该名的脚本本身。首跑因此给出 `FETCH_NAME_LEAKED_INTO_REPO=1`，而它同时**把要判的那类目标从分母里删掉了**——即"排掉的那只到底该不该算"这件事没有任何读数。原件不覆盖，留盘 `evidence/r55_cred_recount.txt`（`VERDICT=DIRTY`），由重跑的 `evidence/r55_cred_recount_2.txt` 用 `PRIOR_ATTEMPT` / `PRIOR_VERDICT` 点名。',
        '→ 形状：与 (55)/(71)"候选为 0 装绿"同族而**方向相反**：那是候选集天然为空却输出"命中 0"，这是**候选被写死在脚本里删掉**。两者在载体上的表现一模一样（一个漂亮的数字），差别只在有人去读代码。',
        '→ 为什么它危险：排除项**不在判据文本里**⇒ 复核者只能看到结果数；一旦排除条件写错（本例：连"取证载体自己打印了该文件名"也一起被当成排除），门会稳定给出一个**语义已变**却与"干净"逐字同形的裁决。',
        '→ 正确做法：①**不静默排除任何一只**，改按**半径**分桶并各写一行读数：`FETCH_NAME_IN_REPO_INSIDE_SYNC_SCOPE=3`（同步目录内，按构造合法：声明它的脚本 + 打印它的取证载体）/ `FETCH_NAME_LEAKED_OUTSIDE_SYNC_SCOPE=0`（目录外才是事故），**退出码只认后者**；②首跑口径写错的那遍**留在盘上**，重跑另起一只并由新载体点名前一只及其裁决；③名册口径本身也要有哨兵：`NAMES_SCANNED=565` 配 `assert len(names) > 400`。',
        '→ **同族**：项目记忆 (55)、(71)、(76)、(83)（差集判据要写成 `expect = listed ∪ LATE_ADDED`）、用户记忆 `feedback-verifiable-acceptance.md`「命中 0 ≠ 干净」。',
    ],
    [
        '[错误类型] **把"自己已经 assert 过的等式"原样打印进载体 ⇒ 这一行永远为真、operands 一个数字都没有，等于没打印；紧接着同一批里肉眼又抓到 3 处它没拦住的缺陷**',
        '→ 症状：`evidence/r55_land_readme_2.txt` 里那行 `PURE_INSERT_PROOF=行数差 == 插入行数 ∧ 表格行差 == 3 ∧ 五处过期读数均已消失`——三个子句全是脚本内已 assert 的命题，**没有一个操作数**。而落地后我自己回读 README 又抓到 3 处排版缺陷（载体指针缺 `evidence/` 前缀 / 日期被写了两遍 / `| 23 |` 那格时刻缺日期），这行照样显示为"绿"。',
        '→ 形状：与"否定式断言要配前置钉"同族，新层是**证明行必须是读数，不是命题**：命题由 `assert` 负责（它的失败会中断脚本），载体负责让**下一个人不复跑就能验**。两者写成同一行、且只给命题，就把两件事一起取消了。',
        '→ 为什么它危险：一行永远为真的 "PROOF" 比没有这行更糟——它让复核者**以为已经有人证过**，而它证的恰是脚本自己已经做完的事；真正没被证的（本批那 3 处排版缺陷）落在这行的覆盖范围**之外**，且没有任何读数指向那个范围，于是缺陷只能靠肉眼回读撞上。',
        '→ 正确做法：①证明行一律带 operands：同一载体现存 `LINES=311 -> 316（+5 行，全部是插入；表格行 29 -> 32）`、`README_BEFORE_BYTES=98056 md5:18ad0916…`；②**落地器自述的 AFTER 数字在它自己写盘之后还可以被推翻**：本批实测末版清单里 `README.md` 的权威值是 105,343 B，与自述的 105,334 差 `+9 B` = 第一处那 9 个字符 `evidence/` 的长度，另两处一加一减互相抵消 ⇒ **"归档内某只文件的当前字节"只能引末版清单那一行，不引任何落地器的自述**（§38.18 已立过这条，这次是它自己的落地器撞上）；③`assert` 与打印同一来源、同一次调用，且打印里必须出现那两个操作数。',
        '→ **同族**：项目记忆 (58)（打印 ≠ 裁决）、(85)、(86)、(99)、用户记忆 `feedback-verifiable-acceptance.md`「打印 ≠ 裁决」「口径读数不得冒充语义构成」。',
    ],
    [
        '[错误类型] **同代第二次踩在同一形状的语法错上（`b\'…中文…\'` 早已有条目）⇒ 台账只被当作"修错前读物"，没被当作"新写前查物"**',
        '→ 症状：本批两处。①`scripts/r55_cred_recount.py` 的阳性对照样本先写成 bytes 字面量拼接中文 ⇒ `SyntaxError: bytes can only contain ASCII literal characters`，**这条形状台账里已有登记**，注释里我自己标了"本代第二次踩在同一行形状上（写的时候没查台账）"；②`scripts/land_r55_readme2.py` 里正文含字面 `%TEMP%` 又走 `%` 格式化 ⇒ `ValueError: unsupported format character \'T\' at index 541`（须 `%%TEMP%%`）。',
        '→ 形状：与 (95) 那族"作者层字符与格式语言冲突"同类。真正的缺口不在语法知识，在**读取时机**：阶段0 规约写的是"修复前先读 `FreqErr.md`"，作用域是**修错**；重复错发生在**新写那一句**的时候，而那一步没有任何规约要求查台账。',
        '→ 为什么它比第一次踩贵：第一次是知识缺口（可原谅），第二次是**流程缺口**——台账里已经写了正确做法，说明"知道"与"敲那一行时被调用"之间没有任何机制。而本项目的整套纪律就建在台账上 ⇒ 一条只写不读的台账会把"这条我们已经登记过"变成虚假的安全感。',
        '→ 正确做法：①把"新写前先 grep 台账"并入阶段0（写中文相关的 bytes / 正则 / 格式串前，先按关键字查一遍 `FreqErr.md`）；②中文文本模板**一律 f-string 或三引号**，不用 `%` 格式化（占位符数与参数数错配是另一族自伤，本批第二处即由"改成 f-string"根除）；③非 ASCII 的 bytes 只能走 `.encode(\'utf-8\')`；④语法类改动落地前先 `ast.parse`，**不在归档目录内用 `py_compile`**（它落 `.pyc`，`gen_manifest.py` 见派生字节即 ABORT）。',
        '→ **同族**：项目记忆 (95)、(91)~(93) 段（转义与吞行）、用户记忆 `reference-qoder-tool-mapping.md`「Write/Edit 自伤清单」——本条新增两型：**`%`-格式串里的字面 `%`** 与 **bytes 字面量里的中文**。',
    ],
    [
        '[错误类型] **把"末版"理解成"我承诺不再改" ⇒ 冻结之后仍把落地器/载体写进归档目录，亲手把刚登记完的末版降级成非末版（这条链 README 自己数到第 7 次，本批是它的封界型）**',
        '→ 症状：gen 24 于 12:53:39 冻结（`TOTAL=386 / TOTAL_BYTES=1,392,176 / BOM=69`，`verify` `rc=0`）。本批在它之后还剩排查记录 §38.19、`done.md`、`dev_log`、`updates`、backups README、docs 快照、项目记忆一整套 paperwork ⇒ 若 §38.19 的落地器仍写进 `hardware/ht305_sync/scripts/`，`UNLISTED` 立刻非 0，**gen 24 那句话当场失效**。',
        '→ 形状：前 6 次是"清单写完又被改写"（**内容漂**，同一只文件的字节变了），这次是"清单之后新落了一只文件"（**名册漂**，多出一只没人记的）。同一把尺的两端，而此前规矩只写在"改内容"那一端 ⇒ 光守"不再改旧文件"完全不够。',
        '→ 为什么它危险：`UNLISTED` 是这条链上唯一能发现"归档外多了东西"的读数；把它顶成非 0 的**恰恰是登记动作本身** ⇒ 越勤快收口、末版越假，且失败模式是"绿色的 paperwork 让红名单继续增长"。',
        '→ 正确做法：①"末版"给**可执行定义**：**此后所有写盘动作一律落在 `hardware/ht305_sync/` 之外**（落地器、stdout 载体、终态复核载体都放仓库 `hardware/` 根，与 `hardware/20260924_ps1编码吞行实验.txt` 同口径）；②终态复核的载体在归档外是**刻意设计**（落进 `evidence/` 会被下一代少记一只 ⇒ `UNLISTED` 顶非 0，把"清单是否仍真"这件正事污染掉）；③登记句里显式写出这条封界，让人能拿它当检查项：§38.19 ④ 那句"本批后续 paperwork 全部在归档目录之外"。',
        '→ **同族**：项目记忆 (55)~(62)（清单/门/内容互为快照，要钉顺序）、(94)（**门与清单之间**动了文件 ⇒ 分子分母量的不是同一份盘）、(97)。',
    ],
]

LEDGER_TMPL = (
    '> **【@T@ 复跑｜R55 第二遍 6 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：'
    '全文 `^[错误类型]` 条数 = **@BEFORE_KIND@**、`wc -l` = **@BEFORE_LINES@**；'
    '追加之后现算，**口径 = 含本台账行自身的最终字节串**：`^[错误类型]` = **@AFTER_KIND@**、'
    '`wc -l` = **@AFTER_LINES@**（两把尺都在 `final` 上数，不数未含台账行的 `out`——见本批第 4 条与 (99)）。'
)

old = open(DOC, encoding='utf-8', newline='').read()
raw_old = old.encode('utf-8')
assert raw_old.count(b'\r\n') == raw_old.count(b'\n'), 'ABORT: 台账不是纯 CRLF，先停下'
assert old.endswith('\r\n'), 'ABORT: 台账不以 CRLF 结尾，追加会造出半行'

before_kind = len(re.findall(r'(?m)^\[错误类型\]', old))
before_lines = raw_old.count(b'\n')
assert before_kind == 181, 'ABORT: 追加前端数 181 变了（实测 %d）⇒ 先查是谁加的' % before_kind

# 上一遍（R55 第一遍）台账行开头那段 `@T@` **没有被替换过** ⇒ 落地时"时刻"这一路没有执行者。
# 现读定位（不硬编码行号），并把它写成本批的订正句（追加，绝不就地改旧行——见项目记忆 (99)）。
_ols = old.split('\r\n')
_ph = [i + 1 for i, l in enumerate(_ols) if l.startswith('> **【@T@')]
assert len(_ph) == 1, 'ABORT: 未替换的 @T@ 台账行有 %d 处，与"上一遍 1 处"不符' % len(_ph)
RUN_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
FIX = ('> **【订正｜' + RUN_AT + '】** 本文件第 **'
       + str(_ph[0]) + '** 行（R55 第一遍台账）开头那段 `@T@` 是一处**从未被替换**的占位符 ⇒ 上一遍落地时"时刻"这一路根本没有执行者。'
       '本批模板由那一遍**逐字派生**而来 ⇒ 同一缺陷连同一条**专门放过它的断言**（`assert` 里用 `.replace` 把 `@T@` 豁免掉）一起被带了过来；'
       '现已在同一次运行内把它填成本批时刻（**上面**那格的开头），并把那条豁免换成对 `@BEFORE` / `@AFTER` / `@T@` 三种占位的逐一检查。'
       '**旧行不就地改**：改了就没有"上一遍没填时刻"这件事实的物证，由本行点名（口径同项目记忆 (99)「订正句追加、绝不就地改数」'
       '与 (63)「逐字派生会把上一代恰好没踩到的缺陷一起派生过来」）。')

blocks = []
for ent in ENTRIES:
    assert len(ent) == 6, 'ABORT: 每条必须是 症状/形状/为什么/正确做法/同族 + 标题 = 6 行'
    for ln in ent:
        assert '\\' not in ln, 'ABORT: 正文里出现反斜杠（(1813) 那族，改用 CR/CRLF 等词）'
    blocks.append('\r\n'.join(ent))
body = ('\r\n' + '\r\n\r\n'.join(blocks) + '\r\n\r\n') if blocks else ''

# **占位只在拼接前解析**：`old` 里上一遍那行台账本身就带一段字面 `@T@`（正是被订正的那处），
# 若在拼好的 `final` 上做 `replace`，第一下命中的是**历史那一行** ⇒ 就地改了旧物证（订正句声明不许做的事）。
scaffold = old + body + LEDGER_TMPL + '\r\n\r\n' + FIX + '\r\n'
after_kind = len(re.findall(r'(?m)^\[错误类型\]', scaffold))
after_lines = scaffold.encode('utf-8').count(b'\n')
assert after_kind == before_kind + len(ENTRIES), 'ABORT: 条数增量不等于本批条数'

ledger = (LEDGER_TMPL.replace('@T@', RUN_AT, 1)
          .replace('@BEFORE_KIND@', str(before_kind)).replace('@BEFORE_LINES@', str(before_lines))
          .replace('@AFTER_KIND@', str(after_kind)).replace('@AFTER_LINES@', str(after_lines)))
final = old + body + ledger + '\r\n\r\n' + FIX + '\r\n'
assert final.startswith(old), 'ABORT: 追加不再是纯追加，历史行被改写过'
_ols2 = final.split('\r\n')
assert _ols2[_ph[0] - 1].startswith('> **【@T@'), 'ABORT: 旧台账行第 %d 行的 @T@ 不在了 ⇒ 刚把历史就地洗了一次' % _ph[0]
_ld = [l for l in _ols2 if '复跑｜R55 第二遍' in l]
assert len(_ld) == 1, 'ABORT: 本批台账行有 %d 处，占位检查无从下手' % len(_ld)
assert '@' not in _ld[0], 'ABORT: 本批台账行里还有未回填的占位：' + _ld[0][:60]
# 订正句 FIX **按设计**含 `@T@` / `@BEFORE` / `@AFTER` 字面量（它们是被描述的对象，不是占位）
# ⇒ 检查只能钉在台账那一行上；上一遍正是把这条豁免写成了"整份文件放过 @T@"，才让未替换的占位落盘。
rebuilt_b = final.encode('utf-8')
assert len(re.findall(r'(?m)^\[错误类型\]', final)) == after_kind, 'ABORT: 回填后条数漂了'
assert rebuilt_b.count(b'\n') == after_lines, 'ABORT: 回填后行数漂了（数字位数变了？）'
assert rebuilt_b.count(b'\r\n') == rebuilt_b.count(b'\n'), 'ABORT: 行尾混杂'

open(DOC, 'w', encoding='utf-8', newline='').write(final)

back = open(DOC, encoding='utf-8', newline='').read()
raw = open(DOC, 'rb').read()
assert back.startswith(old), 'ABORT: 不是纯追加'
crlf, lf = raw.count(b'\r\n'), raw.count(b'\n')
assert crlf == lf, 'ABORT: 落盘后行尾混杂 CRLF=%d LF=%d' % (crlf, lf)
assert len(re.findall(r'(?m)^\[错误类型\]', back)) == after_kind, 'ABORT: 独立回读的条数与写盘前算的不一致'
assert raw.count(b'\n') == after_lines, 'ABORT: 独立回读的行数与写盘前算的不一致'

lines = [
    'FREQERR2_AT=' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'DOC_BEFORE_BYTES=%d DOC_AFTER_BYTES=%d APPENDED=%d' % (len(raw_old), len(raw), len(raw) - len(raw_old)),
    'KIND_COUNT=%d->%d（本批新增 %d 条）' % (before_kind, after_kind, len(ENTRIES)),
    'WC_L=%d->%d' % (before_lines, after_lines),
    'CRLF_PURE=CRLF==LF(%d)' % crlf,
    'PURE_APPEND=正文以旧字节整体开头（独立回读另一次调用比对）',
    'DOC_MD5=' + hashlib.md5(raw).hexdigest(),
    'ENTRIES=1 同一次运行两只 now() 跨秒假红 / 2 跑绿了却没载体(gen 23) / 3 静默排除=造隐形尺 / '
    '4 打印已 assert 过的等式=半绿 / 5 同代第二次踩 b-中文 / 6 末版封界(冻结后写进归档=亲手降级)',
    'NOTE=台账行自身的两条"之后"数在**将被写出的完整字节串**上现算，回填后复数两把尺均不变；'
    '本载体与 §38.19 落地器、终态复核载体同批落在 hardware/（归档目录之外）。',
    'VERDICT=LANDED_FREQERR2',
]
open(CARRIER, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('CARRIER=hardware/' + os.path.basename(CARRIER))
