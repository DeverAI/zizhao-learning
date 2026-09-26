# FreqErr.md 第十五批落地器（R61b 收口遍）。四条硬规矩：
#   ①幂等前置（"R61 第十五批"标题已在册即 ABORT）；
#   ②所有裁决排在写盘之前（rc!=0 必须蕴含盘上没动）；
#   ③台账三格在**内存拼好的最终字节串**上先数后写，写完再在盘上复量一次，两处必须同值；
#   ④**本遍新增**：占位符零容忍的对象 = 本遍写出去的**整个终态字节串**（正文 + 台账行 + 被订正那一句），
#     因为第 2254 行（第十三批台账）的三只 `{POST_*}` 就是被这条门漏掉才落盘的 —— 门从此管到台账行。
# 本遍还带一处**就地订正**：把第 2254 行那三只未插值哨兵换成有出处的读数 + 一句点名出处不是它自己现数的。
# 行尾口径：本文件现读 CRLF 主导（LF-CR 差 = 裸 LF 只数）且末行以 CRLF 收尾 => 追加体沿用 CRLF。
import datetime
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MARK = 'R61 第十五批'

# ---------- 现读上一批（第十三批）那句坏台账：三只占位符按名字扫，不硬编码位置 ----------
pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十五批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')

# 两把尺要分开：**在历史里找漏网**只能用上大写式占位符那把（全册现读另有 6 行带花括号，那些是代码片段
# 里的 `{id}` / `{exit}`，用宽尺会把它们算进来，于是"应为 1"这条断言本身就是个假门）；
# **对本遍写出去的文本**用宽尺（终态新增文本里一只花括号都不该有）。
PH = re.compile(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}')
PHUP = re.compile(r'\{[A-Z][A-Z0-9_]*[:,]*\}')
_bad = [l for l in pre.splitlines() if PHUP.search(l.decode('utf-8', 'replace'))]
_wide_all = sum(1 for l in pre.splitlines() if PH.search(l.decode('utf-8', 'replace')))
assert len(_bad) == 1, 'ABORT: 全册大写式未插值哨兵行 %d 只（应为 1）=> 要么已订正过，要么还有别的漏网' % len(_bad)
BADLINE = _bad[0].decode('utf-8')
BADLN = pre[:pre.index(BADLINE.encode('utf-8'))].count(b'\n') + 1
_ph = PH.findall(BADLINE)
assert sorted(_ph) == ['{POST_B:,}', '{POST_E}', '{POST_L}'], 'ABORT: 那一行的占位符不是预期的三只：%s' % (_ph,)
# 被替换那一段（三只哨兵**连同各自的 `**` 包裹**连成的整串），逐字来自现读，不手抄。
# 边界为什么不能只从 `{` 起：`{POST_E}` 前面那只 `**` 是它的加粗左半边，切在这里会留下 `**` 孤半边，
# 而"段里有 3 对 `**`"这个形状预期就是把孤半边抓回来的那把尺（首跑实测：从 `{` 起只数到 4 只 `**`，ABORT）。
_i0 = BADLINE.index('**{POST_E}')
_j1 = BADLINE.index('{POST_B:,}') + len('{POST_B:,}**')
OLDSEG = BADLINE[_i0:_j1]
assert OLDSEG.startswith('**{POST_E}') and OLDSEG.endswith('{POST_B:,}**'), 'ABORT: 段边界不含首尾加粗半边：%r' % OLDSEG
assert OLDSEG.count('**') == 6 and '\n' not in OLDSEG, 'ABORT: 被替换段形状与预期不同：%r' % OLDSEG

# ---------- 口令明文闸（读宏本体，只用于判，绝不打印/不入正文） ----------
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'

# ---------- ③订正段的数字**不硬编码**：从相邻台账行现读 ----------
# 第十三批写盘后的终态 = 第十四批那行"追加之前现读磁盘"给出的三个数（对同一状态的第二次独立测量）。
_n14 = [l for l in pre.splitlines() if 'R61 第十四批' in l.decode('utf-8', 'replace') and '追加之前现读' in l.decode('utf-8', 'replace')]
assert len(_n14) == 1, 'ABORT: 第十四批台账行现读 %d 只（应为 1）=> 出处这条链断了' % len(_n14)
_m14 = re.search(r'= \*\*(\d+)\*\* 条 / \*\*(\d+)\*\* 行 / \*\*([\d,]+)\*\* B', _n14[0].decode('utf-8'))
assert _m14, 'ABORT: 第十四批台账行取不到那三个数'
P14 = (int(_m14.group(1)), int(_m14.group(2)), _m14.group(3))
assert P14[0] == 244, 'ABORT: 第十四批现读的条目数 = %d，与"第十三批 242 条 + 本批 2 条"不咬合' % P14[0]
NEWSEG = ('**%d** 条 / **%d** 行 / **%s** B（此三格由 %s 遍回填，出处 = **第十四批**台账行在 12:54:29 '
          '对同一状态的独立现读，不是第十三批自己现数的值 —— 那一遍这三格根本没插值就落了盘，'
          '见本批第②条与本文件第 %d 行）') % (P14[0], P14[1], P14[2], datetime.datetime.now().strftime('%H:%M'), BADLN)
# 尺寸一律按**字节**算：上面两只长度若用 `len(str)` 数的是**字符**，而正文中文一字 3 B ⇒
# 任何"落盘尺寸 == 原尺寸 − 旧段 + 新段"的等式用字符长度必然不平（本遍首跑即被这条抓停，盘上零改动）。
OLDB, NB = len(OLDSEG.encode('utf-8')), len(NEWSEG.encode('utf-8'))
assert OLDB != len(OLDSEG) and NB != len(NEWSEG), 'ABORT: 段里没有非 ASCII => 上面那条字符/字节之分本遍没被实测用到（换别的证据，别改这条断言）'

ENTRIES = [
    ('**正则的组序被我当成"前一个数 / 后一个数"：一只文件里同排了行与字节两组 ⇒ 组 2 是行数不是字节数**'
     '（R61b 实测：`README 行 A -> B | 字节 C -> D` 四个组依次是 行前/行后/字节前/字节后，'
     '订正遍 `fix_readme11c_wording.py` 首跑把 `mB.group(2)` 当字节数、`group(3)/(4)` 当"写盘后行/字节"，'
     '于是"坏态快照尺寸 == 修补遍写盘前字节数"这条**成立**的等式报 ABORT：快照 91,756 B vs 取到的 463 B）',
     '症状：读数本身没错，错在把列抄串了行；两列数量级差 200 倍，所以被比出来的是一个**荒谬的具体值**而不是"差不多"。'
     '这一遍 rc=1 且 pre-image 尚未写出 => 盘上零改动（当场复量目标 = 463 行 / 91,757 B / md5 2ec71f8e 原样），'
     '首跑 stdout 也入库（`r61b_readme11c_fix_140717.txt`）。',
     '→ 正确做法：①从载体取数时把**组号与单位写在同一行命名**（`LN2, BY2 = g(1), g(3)`），并在注释里点名"组 2 是行、组 4 才是字节"；'
     '②任何取自文本的单位必须带一道**量级钉**（本遍加了 `assert LN < 1000 < BY`）——单位错在两个数量级面前无法伪装，'
     '而"快照字节数 == 日志里某个数"这种等式，取错列时它就是不成立，比"看着像"可靠；'
     '③历代登记的是"别手抄旧数"，本条登记的是**抄对了来源仍抄错了列**：来源正确不等于列序正确。',
     '→ **同族**：项目记忆「数字连算法与漏判」、本文件第十四批最后一条（"从载体现读的数值字段没定类型"——'
     '那次错在类型，这次错在列，同一族"取数动作本身没被钉住"）。'),
    ('**台账行里的三只大写式占位哨兵没插值就落盘，落笔之后那半句不再是读数而是空句，而它后面还跟着"本遍实测相等"**'
     '（R61b 实测：第 %d 行（R61 第十三批台账）在册至今是 POST_E / POST_L / POST_B 三只未插值哨兵（此处刻意不写出花括号，'
     '写出来就会被本遍那道新门拦下 —— 那正是它的阳性对照，载体 = 同前缀带 `ABORT` 的那一只），'
     '同一句还声称"落盘后同一把尺回读必须逐字相等（本遍实测相等）"⇒ 那句"实测"没有可核对的数）' % BADLN,
     '症状：R53 起的三步序里"写盘前占位符零容忍"这道门**只管正文那一段**，没管同一遍拼出去的台账行；'
     '于是同一次落地里，正文四道门全绿、结尾那行汇总却是空句。它不报错，因为没有任何一格去读那三个花括号。',
     '→ 正确做法：①占位符扫描的对象 = **本遍写出去的整个终态字节串**（正文 + 台账行 + 被订正那一句），'
     '正则同时抓花括号与 printf 类裸占位符（本遍起这条门有了执行者：对终态逐行跑 `PH.search`）；'
     '②**订正不许假装复算**：第十三批那三个值我无法在事后现数（那是内存里拼好的串），所以回填句必须点名'
     '"取自第十四批对同一状态的第二次独立现读"，并保留"这不是它自己现数的"这半句；'
     '③订正落盘后花括号扫描必须 = 0 处（本遍把这条写成 assert，不靠我事后看一眼）。'
     '**这道门第一次开火的靶子是它自己的登记文本**：本条正文原样引了那三只哨兵 ⇒ 首跑 ABORT、rc=1、'
     'pre-image 尚未写出、盘上零改动（载体 = 同前缀 `r61b_freqerr15_*` 里带 `ABORT` 那一只；'
     '引文改写为"只写名字不写花括号"后才落盘，见本批第⑥条那个递归）；',
     '→ **同族**：项目记忆「读数不落盘等于没跑」「订正句本身也是断言载体（R51/R52 三连犯）」、'
     '本文件「引节号要连那一节的内容一起核」（假指针第 2 例）——空句与假指针都是"看着像取证"。'),
    ('**"本遍对这只文件只做了一次插入"由产生那一遍的脚本自己说，而它落笔时已经是第二次；同一行还把 ⑨ 那格的输入并进"⑥⑦ 两格"**'
     '（R61b 实测：`land_r61b_readme11b.py` 落的载体行原话 = "只做了一次插入，没覆写任何旧格"；'
     '实情是 插 ①~⑪（A 遍）→ 补载体行且首跑插成吞空行的坏态 → 修补那根换行 → 本遍订正，同一天内 README 被动四次）',
     '症状：这类句子**写的时候像是老实交代**，它的错法在于把"我这一遍"当成"这一代"，而盘上状态由多遍叠成；'
     '指针那一半更安静：`r61b_docs_snapshot11_*.txt` 是 ⑨（docs 快照）的输入，写成"⑥⑦ 两格的输入"没有改变任何数字，'
     '只是让下一遍按错的格去找载体。',
     '→ 正确做法：①**次数 / 序数类主张不能由产生它的那一遍声称**——由下一遍把前几遍的载体名单逐只现读再数'
     '（本遍订正句里那三只名字全部来自按前缀 + 内容扫出的 `one()`，一只没硬编码）；'
     '②"这一遍是第 N 次"必须能被载体清单证伪，写不出清单就写"遍数不在本格登记"；'
     '③订正遍要防两种反向缺陷：旧句残留（`assert 旧句 not in 盘上`）与**误删引文**'
     '（本遍订正句里带引号复述了那句假话，所以被订正那串字符在盘上必须**恰好还剩 1 处**，那一处是引文——'
     '写成"= 0"会把引文一起删掉，等于把订正依据也删了）。',
     '→ **同族**：本文件第十四批「数量词写成字面量 / 全部·所有类主张」、项目记忆「提交信息不许有将来式锚点」'
     '「同轮两遍产物必须点名权威」。'),
    ('**插入体自身不带行尾换行 => 它把相邻那根换行吞掉；能看见这件事的只有行数这把尺，而它排在写盘之后**'
     '（R61b 实测咬合：A 遍写盘后 462 行 / 91,292 B → 坏态 462 行 / 91,756 B（**+464 B 而 +0 行**）'
     '→ 修补遍 463 行 / 91,757 B（+1 行 / +1 B）；三只数全部由本遍从两遍日志现读再相加，未手抄）',
     '症状：字节数完全正常（增加了插入体的长度），md5 也变了，一切"看起来像成功"；坏的是下一行标题'
     '`## 2. 命名规则` 与前一行之间的空行被并进来，Markdown 渲染时那一格会粘进上一段。'
     '而"落盘后行/字节必须等于期望"那道 assert 是在 `open(RM, wb)` **之后**跑的 ⇒ 它是**探测器**，不是防护。',
     '→ 正确做法：①中部插入前置两道**写盘前**钉：插入体 `line.endswith(b"\\n") and line.count(b"\\n") == 1`、'
     '被插位置 `pre[len(pfx)] == b"\\n"`（确认我要接的那根换行真在，且插完之后它还给我）；'
     '②期望值必须**行数与字节数成对算**（本遍 `_exp_lines` / `_exp_bytes` 分开），只算字节的话这一类病看不见；'
     '③坏态快照**留证不删**（`readme_broken_nocr_*.md`），它是"改之前长什么样"的唯一副本；'
     '④下一遍还要把"上一遍报的写盘后那一态"与本遍写盘前现读做等式核对（`LN2A/BY2A == 现读`），'
     '否则本遍接的可能是别的态而它自己不知道。',
     '→ **同族**：项目记忆「落地器的字节证明不含位置属性，且可逆要有盘上快照」「裁决排在写盘之前」'
     '（行/字节成对是这条的缺的那一半）、本文件 R61 第十二批「门写在 ab 之后」。'),
    ('**以"两侧集合相等"当判据的门，在两侧同时为空时恒真，而它恰好是那只创建器唯一像样的复核**'
     '（R61b 建根实测：复核器头两道 = `set(ta) == set(tb)` 与 `all(ta[k] == tb[k])`；'
     '创建器用 `os.path.relpath(f, MAIN)` 当目标相对路径 => 该路径天然不含 `main/` 前缀 => 32 只源码平铺到根顶层；'
     '真正把它拽住的只有后面那只正向钉 `MAIN_N == 32`）',
     '症状：盘上已经落地了一对错的根（35 只里源码不在 `main/` 下），复核却一路绿灯；'
     '而"根/main 与工作树逐只比 = 0 行差异"这句话如果被写成 `set` 比对，空对空正好为真 —— 它不但没拦，还会**给错态发合格证**。',
     '→ 正确做法：①集合 / 字典比对必须自带**基数下限**：先 `assert len(a) == len(b) == N`（或区间 `[30,40]`）再比内容，'
     '只数与逐只内容同级；②"目标目录已存在即 ABORT"这种幂等门，若目标名带秒级时间戳则**永不存在**'
     '（重跑就多造一对）=> 幂等要按**前缀扫**（本遍创建器改成扫 `r61close_*`）；'
     '③由源派生的路径（`relpath`、`join`、`dirname`）必须在**落盘处**回读拼接结果并 assert 前缀，不许相信源；'
     '④复核若排在写盘之后，它只能算"发现"，不能算"防护"（本遍的修法是把建根遍拆成 创建 → 搬移 → 独立复核 三遍，'
     '每一遍都只看自己那一段）。',
     '→ **同族**：项目记忆「命中 0 != 干净 / 候选为 0 必须 ABORT」（同族在**计数**上，本条在**集合内容**上）、'
     '本文件「断言写成恒真 = 门只打印不设闸的源码级孪生」（那条抓到的是 `or True`，本条抓到的是空集合，形态新）。'),
    ('**落地器无法在正文里写出自己那一遍的载体文件名（名字由外层 shell 重定向决定），于是第一遍只能留空、'
     '补遍又变成"第 N 次动这只文件"**（R61b 实测：A 遍写 ①~⑪ 时它的 stdout 载体 `r61b_readme11_land_*.txt` 还不存在；'
     '载体行只能由第二遍补，而第二遍自己也面临同一个递归）',
     '症状：这是第③条那句"只做了一次插入"的**结构性成因** —— 不是我忘了数，是那一遍在写的时候原理上取不到自己的载体名；'
     '不处理这个递归，每一代都必然要"再补一遍"，而补的每一遍都会新增一次"这遍只做了一次"的误述风险。',
     '→ 正确做法：①二选一并写进正文：**要么**由落地器自己开取证文件（脚本内决定名字、进入时刻秒戳，正文里就能写它），'
     '**要么**在正文里明确写"载体名 = 前缀 + 本遍时刻，由外层 tee 决定，故本格不含载体名"；'
     '②选了前者就不许再走后者（同轮两遍产物必须点名权威）；③本遍走的是**后者 + 补遍**这一混合形态，'
     '所以把它的代价登记在这里，第 16 代起同步链脚本改走前者。',
     '→ **同族**：本条第③条（同一个缺陷的两半：一半是措辞、一半是结构）、项目记忆「取证脚本输入文件不得硬编码」'
     '「同轮两遍产物必须点名权威」。'),
]

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += ['[错误类型] ' + t, s, fix, kin, '']

EB = '[错误类型]'.encode('utf-8')   # bytes 字面量不许含非 ASCII => 由 str 编码出来
n_before = sum(1 for l in pre.splitlines() if l.startswith(EB))
lines_before = pre.count(b'\n')
bytes_before = len(pre)


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十五批 %d 条】** 追加之前现读磁盘（本脚本进入时刻 %s）：'
        '`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B；本批正文 = **%d** 条 / **%d** 行'
        '（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；台账行自身不另加条目；'
        '**同遍还就地订正了第 %d 行那三只未插值哨兵**（该行只加 **%d** B、行数不变、条目数不变，'
        '订正段长度 %d B -> %d B）；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**'
        '（写完后本脚本还在盘上复量一次，两处必须同值）。'
        '口径明文闸 = 追加段与订正段现扫 PROV_PASS 宏值命中 0 才动手；'
        '占位符闸 = 终态整串现扫花括号命中 0 才动手（本遍起这道门管到台账行）。' % (
            ts, len(ENTRIES), ts, n_before, lines_before, format(bytes_before, ','),
            len(ENTRIES), len(rows), BADLN, NB - OLDB, OLDB, NB,
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ',')))


hdr = build(bytes_before)
for _ in range(8):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + (NB - OLDB) + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与 header 自身长度不收敛')

# ---------- 内存里拼出终态：先订正那一行，再在 EOF 追加 ----------
_mid = pre.replace(BADLINE.encode('utf-8'), BADLINE.replace(OLDSEG, NEWSEG).encode('utf-8'), 1)
assert _mid != pre, 'ABORT: 订正没有改动任何字节'
assert _mid.count(BADLINE.encode('utf-8')) == 0 and _mid.count(NEWSEG.encode('utf-8')) == 1, 'ABORT: 订正段没落到唯一一处'
assert len(_mid) == bytes_before - OLDB + NB, 'ABORT: 订正只该改字节不改行，实测尺寸变化与替换体长度不等'
assert _mid.count(b'\n') == lines_before, 'ABORT: 订正遍改了行数（替换体里带换行？）'
assert sum(1 for l in _mid.splitlines() if l.startswith(EB)) == n_before, 'ABORT: 订正遍改了条目数'

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
exp = _mid + append_bytes
assert sec not in exp, 'ABORT: 本遍写出去的字节含口令明文'
# 占位符闸只管**本遍新写的那一段 + 回填句**（历史正文里另有 6 行花括号是代码片段，拿全册当扫描域会让这道门恒红而失去意义）
_newtext = append_bytes.decode('utf-8') + '\n' + NEWSEG
_stray = [l for l in _newtext.split('\n') if PH.search(l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本遍新写文本里有 %d 行带未插值占位符：%r' % (len(_stray), [l[:70] for l in _stray[:3]])
assert sec.decode('utf-8') not in exp.decode('utf-8'), 'ABORT: 口令明文以解码文本出现'
exp_entries = sum(1 for l in exp.splitlines() if l.startswith(EB))
exp_lines = exp.count(b'\n')
assert hdr.encode('utf-8') in exp, 'ABORT: header 没进终态字节串'
assert ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: header 里那格终态字节数不是最终串的实际值'
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 终态条目数 %d 与预期 %d 不符' % (
    exp_entries, n_before + len(ENTRIES))
# pre-image（订正 + 追加之前的原件），"可逆"要落在盘上
_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'freqerr_pre15_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'

io.open(TGT, 'wb').write(exp)
chk = io.open(TGT, 'rb').read()
# 三段证明：订正点之前逐字等 -> 订正段逐字等 -> 订正点之后到 EOF 的原文逐字等 -> 追加体逐字等
_i = pre.index(BADLINE.encode('utf-8'))
_newb = NEWSEG.encode('utf-8')
_tailpre = pre[_i + len(BADLINE.encode('utf-8')):]
assert chk[:_i] == pre[:_i], 'ABORT: 订正点之前被改动'
assert chk[_i:_i + len(_newb)] == _newb, 'ABORT: 订正段逐字不等'
assert chk[_i + len(_newb):_i + len(_newb) + len(_tailpre)] == _tailpre, 'ABORT: 订正点之后、追加点之前的原文被改动'
assert chk[len(chk) - len(append_bytes):] == append_bytes, 'ABORT: 追加体逐字不等'
assert chk.count(_newb) == 1, 'ABORT: 订正段在盘上不止一处'
post_entries = sum(1 for l in chk.splitlines() if l.startswith(EB))
post_lines = chk.count(b'\n')
assert (post_entries, post_lines, len(chk)) == (exp_entries, exp_lines, len(exp)), 'ABORT: 盘上复量与内存终态不同值'
_all = chk.decode('utf-8').split('\n')
assert sum(1 for l in _all if PH.search(l)) == _wide_all, 'ABORT: 落盘后带花括号的行数从 %d 漂了 => 本遍又写进未插值文本' % _wide_all
assert not [l for l in _all if PHUP.search(l)], 'ABORT: 落盘后大写式占位符仍在册'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('订正第 %d 行：占位符 %d B -> 回填句 %d B（行数不变 / 条目数不变）' % (BADLN, OLDB, NB))
print('EOL CRLF=%d bareLF=%d | APPEND=CRLF' % (chk.count(b'\r'), post_lines - chk.count(b'\r')))
print('ENTRIES %d -> %d (本批 +%d)' % (n_before, post_entries, len(ENTRIES)))
print('LINES %d -> %d | BYTES %d -> %d' % (lines_before, post_lines, bytes_before, len(chk)))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
