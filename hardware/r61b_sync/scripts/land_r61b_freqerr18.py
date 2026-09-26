# FreqErr.md 第十八批落地器（R61b 收口遍第四段）：登记本遍新暴露的四类缺陷。
# **本脚本自己就是第十八批第①条的执行者**：它是纯追加，写盘后的盘上证明用三段式
# （前缀逐字等 / 追加段逐行等 / 后缀为空），不写「逐位置比两代行」——那种写法在纯插入下
# 会把插入点之后的每一行都判成不等（land_r61b_readme12.py 15:05 那一遍就是这样 rc=1 而盘上内容是对的）。
# 规矩照旧：幂等门 → 全部裁决排在写盘之前 → pre-image → 写盘后行级证明。
import datetime
import glob
import hashlib
import io
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
NEV = os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts')
MARK = 'R61 第十八批'
BS = chr(92)

_T0 = time.time()
pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十八批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
pl = pre.splitlines()
EB = '[错误类型]'.encode('utf-8')
n_before = sum(1 for l in pl if l.startswith(EB))
lines_before = pre.count(b'\n')
bytes_before = len(pre)


def car(prefix, token=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if token is None or token in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 载体前缀 %r（含令牌 %r）命中 %d 只（应为 1）' % (prefix, token, len(hits))
    return hits[0], io.open(hits[0], encoding='utf-8').read()


# ---------- 本批正文里的每个数都必须读自盘上载体，不许手抄 ----------
P151152, pt = car('r61b_readme12_proof_151152.txt', 'VERDICT=PROOF_ONLY_OK rc=0')
P151116, pt116 = car('r61b_readme12_proof_151116.txt')
FIXC, fx = car('r61b_readme12_carrier_fix_*.txt', 'VERDICT=CARRIER_LINE_FIXED rc=0')
L17 = car('r61b_freqerr17_*.txt', 'VERDICT=LANDED rc=0')[1]
PRE12 = os.path.join(EV, 'readme_pre12_20260926_150515.md')
assert os.path.isfile(PRE12), 'ABORT: 第十二格的 pre-image 不在盘上'

_m = re.search(r'README bytes=(\d+) lines=(\d+) / INSERTED (\d+) @(\d+)', pt)
README_B, README_L, INS_N, INS_AT = int(_m.group(1)), int(_m.group(2)), int(_m.group(3)), int(_m.group(4))
_m = re.search(r'PRE=\S+ bytes=(\d+) lines=(\d+)', pt)
PRE_B, PRE_L = int(_m.group(1)), int(_m.group(2))
_m = re.search(r'STATUS_DRIFT (\d+) -> (\d+) / 差 (\d+)；[^=]*= (\d+)：\[(.*?)\]', pt)
d_from, d_to, d_diff, d_n = (int(_m.group(i)) for i in (1, 2, 3, 4))
d_names = [x.strip().strip(chr(39)) for x in _m.group(5).split(',')]
assert _m and d_to - d_from == d_diff == d_n == len(d_names), 'ABORT: 漂移归因等式在载体里就不成立'
_m = re.search(r'PROOF_CARRIERS \[(.*?)\] / AUTHORITY=(\S+)', fx)
carr_names = re.findall(r'(r61b_readme12_proof_\d+\.txt)\((\w+)\)', _m.group(1))
authority = _m.group(2)
assert len(carr_names) == 2 and authority in [c[0] for c in carr_names], 'ABORT: 权威载体不唯一或不在名单里'
_m = re.search(r'README bytes (\d+) -> (\d+) / lines (\d+)（替换 1 行 @(\d+)）', fx)
fx_a, fx_b, fx_l, fx_ln = (int(_m.group(i)) for i in (1, 2, 3, 4))
assert fx_a == README_B, 'ABORT: 订正前字节 != proof 遍读到的 README 字节'
assert fx_b == os.path.getsize(os.path.join(REPO, 'backups', 'README.md')), 'ABORT: 订正后字节 != 盘上 README 现读尺寸'
pre12_b = os.path.getsize(PRE12)
assert pre12_b == PRE_B, 'ABORT: pre-image 现读尺寸 != proof 遍登记的尺寸'
# 落地遍（rc=1）到底有没有写载体？按前缀扫盘上，点名"没有"这件事本身。
land_cars = [os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_readme12_land_*.txt'))
             if os.path.getmtime(p) < _T0]
assert land_cars == [], 'ABORT: 第十二格其实有 rc=1 遍载体（%s）⇒ "没写载体"那句是假的' % land_cars
# 本批自己之前崩掉的那几遍（SyntaxError / TypeError / 两格数接反）：载体由 shell 重定向留在盘上，必须点名。
crash18 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_freqerr18_*.txt'))
                 if os.path.getmtime(p) < _T0)
assert crash18, 'ABORT: 本批之前那几遍 rc=1 没有载体 ⇒ "崩过"这件事无法点名'
# 本批自己崩过的那几遍：按前缀扫、mtime 早于本遍进入时刻（本遍的载体正被 shell 重定向原地写）。
crash18 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61b_freqerr18_*.txt'))
                 if os.path.getmtime(p) < _T0)
for _f in crash18:
    _t = io.open(os.path.join(EV, _f), encoding='utf-8', errors='replace').read()
    assert 'PRE-IMAGE' not in _t and 'VERDICT=LANDED' not in _t, 'ABORT: 前一遍崩溃载体其实动过盘：' + _f
tok116 = re.search(r'VERDICT=(\w+) rc=0', pt116).group(1)
assert tok116 == 'LANDED' and authority.endswith('.txt'), 'ABORT: 令牌误写那格现读不是 LANDED'

ENTRIES = [
    # ① 插入式落地的行级证明
    ('[错误类型] **纯插入式落地的盘上证明写成「逐位置比新旧两份的第 i 行」⇒ 插入点之后每一行都错位：'
     '盘上内容是对的、证明全红，而且红的时候盘已经动了（R61b 实测：README 第十二格那一遍）**',
     '症状：`land_r61b_readme12.py` 15:05:15 那一遍，16 行新块按锚点插进 `backups/README.md` 第 %d 行位置，'
     '写盘后拿 `for i in range(len(旧行)) if 新行[i] != 旧行[i]` 求差集 ⇒ 从插入点起到文件尾**整段报不等**'
     '（盘上 %d 行 / 实际只动了 %d 行插入），脚本 rc=1。'
     '三条同时成立的后果：①它**没写自己的载体**（同目录按 `r61b_readme12_land_*` 前缀现扫 = %d 只，本遍把它钉成断言），'
     '那一遍的读数以"文件存在"为准全部查无；②README **已经**被写成新内容（pre-image 现读 %d B / %d 行 vs 盘上 %d B / %d 行），'
     '所以这不是"崩在写盘前、零改动"那一案，而是"崩在写盘后、改动在盘上"——两者处置完全不同；'
     '③我最初的反应（重跑一遍看绿）会把「盘对而尺错」洗成「重跑即通过」，永远不知道尺是错的。'
     % (INS_AT, README_L, INS_N, len(land_cars), pre12_b, PRE_L, README_B, README_L),
     '→ 正确做法：①**按动作类型选证明形状**：纯插入 / 纯追加只能写成三段 —— 前缀逐字等 `新[:i] == 旧[:i]`、'
     '插入段逐行等 `新[i:i+n] == 新块`、后缀逐字等 `新[i+n:] == 旧[i:]`，再加一条行数等式 `len(新) == len(旧) + n`；'
     '逐位置差集只对**替换型**订正成立（那一类里 `fix_r61b_readme12_carrier.py` 现读差集恰为第 %d 行，是对的用法）；'
     '②修好的判据必须**在真字节上被执行一次**（可达性取证）：给落地器加 `--proof-only` 模式，'
     '让它拿 pre-image 与现件跑同一个 `prove()`，而不是把改进留在从没跑过的分支里；'
     '③重跑那一遍时"本遍时刻"令牌必须**回读成落地时刻**（从 pre-image 文件名里的 %s 解析），'
     '否则拿今天的 status 行数去比对落地那一刻写进正文的数，必然假红；'
     '④易漂行不许靠"整行跳过"糊过去：按构造点名哪几类行会漂（本遍 = 引现跑 status 行数的那格、引载体名的那格），'
     '并要求漂移被**新增取证只数精确解释** —— 现读 %d -> %d / 差 %d == 名单长度 %d，名单逐只点名进正文；'
     '⑤崩在写盘后的那一遍，其盘上态必须由**下一遍的独立回读**判定（本遍用 `os.path.getsize(pre-image)` 与 proof 遍登记的字节互核），'
     '不许由"我以为它写对了"判定。' % (fx_ln, re.search(r'readme_pre12_\d{8}_(\d{6})\.md$', PRE12).group(1),
                                        d_from, d_to, d_diff, d_n),
     '→ **同族**：本文件 R55 段「纯插入式落地器不验节间空行」（同一条链的另一半：那次是插入删了空行，这次是证明不会看插入）；'
     '用户记忆「读数不落盘等于没跑」（这次连"崩的那遍"都没有载体）、「崩溃那次的读数不作数」（本遍再加一层：崩在写盘后时盘上态也要点名）。'),

    # ② 载体行假指针 + 令牌误写
    ('[错误类型] **落地器把"下一遍才会存在的取证载体名"当成本遍的凭证写进正文 ⇒ 载体行成了假指针；'
     '同一族里还有第二格：复核遍的裁决令牌没按模式分支，把 PROOF_ONLY 打印成了 LANDED**',
     '症状：README 第十二格最后那行原样引了一只**盘上从未存在过**的 proof 载体名（写它那遍还没跑到写载体的那一步就崩了）。'
     '发现它的动作是我按规矩去 `os.path.getsize()` 那只载体 —— 它不存在。事后用 `fix_r61b_readme12_carrier.py` 订正为真话版：'
     '盘上真实存在的复核载体是 %s 与 %s（令牌分别是 %s 与 %s），权威 = %s；'
     '而 %s 那遍 stdout 末尾打印的 `VERDICT=LANDED rc=0` 是**字面为假**的一句：那一遍按设计什么都不写，'
     '它却宣称"已落地"。' % (carr_names[0][0], carr_names[1][0], tok116,
                          re.search(r'VERDICT=(\w+) rc=0', pt).group(1), authority, authority),
     '→ 正确做法：①正文里每只载体名，落地那一刻必须能在盘上 `getsize` 到，否则写"本遍没有载体 + 为什么没有"，'
     '绝不写一只将来可能出现的名字（假指针比空白更贵：空白会被看见，指针会被**顺着走**）；'
     '②裁决令牌必须**按模式分支**输出：`VERDICT = PROOF_ONLY_OK if 只复核 else LANDED`，'
     '并在同一段里 assert 本遍**确实没写目标文件**（比对目标字节不变）；'
     '③"哪一遍权威"要由代码挑出来：本遍订正器扫齐同前缀载体、按"VERDICT= 到 rc=0 之间那一段"取令牌、'
     '要求 `PROOF_ONLY_OK` 那只**恰为 1**，把全名单与选中的那只一起印出来（现读 = %d 只 / AUTHORITY=%s）；'
     '④载体行订正本身也要有载体（`%s`），否则"我订正了假指针"这件事又是一次不落盘的读数。'
     % (len(carr_names), authority, os.path.basename(FIXC)),
     '→ **同族**：本文件「记录取证那步自己没落盘」「指针必须 grep 得到」；'
     '用户记忆「rc=0 必须蕴含产物已写出」的**镜像**：这里 rc=0 蕴含的是"我这遍干了正文所说的那件事"，而 `--proof-only` 那遍并没有。'),

    # ③ diff -rq 假绿
    ('[错误类型] **`diff -rq` 的输入目录不存在时只打一行 stderr、stdout 空 ⇒ 按 stdout 行数算的"0 行 differ"照样通过（假绿）**',
     '症状：建根复核里那句"两根各自与工作树 `diff -rq` = 0 行 ⇒ 它是盘上唯一与工作树逐字同值的全根"，'
     '在根 B 家族路径写错时（把 `hardware/zizhao-esp32s3/backups/` 说成 `main/` 下那只）**仍然可以是 0**：'
     'diff 对不存在的目录不产出任何 stdout 行，rc 非 0 而我最初只数行数。'
     '同一形状在 §38.35 那格（`hardware/ht305_sync/` 现读 388 只）也差一点成立 —— 那里我用的是递归只数，'
     '但"最新一只 mtime"那把尺在目录为空时会抛异常而不是返回假数，两种失效方向不同。',
     '→ 正确做法：①任何"差集行数 == 0"的判据必须包一层执行者：先 `assert os.path.isdir(两侧)`，'
     '再跑命令，再 `assert stderr 为空`，最后才数 stdout 行 —— 三只条件缺一即 ABORT，顺序也要在写盘之前；'
     '②同理适用于 `ls | wc -l`、`git ls-files | grep -c`、`glob`：候选集为空时**必须 ABORT**，'
     '这条已在归档链侧登记过（「候选为 0 必须 ABORT」），本遍把它搬到 `diff` 这类"外部命令 + 按行计数"的组合上；'
     '③跨目录核对前先声明**只数区间**（本遍沿用建根那遍的 `MAIN_N 在 [30,40]` 正向钉），'
     '让"两边同时为空/同时不存在"这种恒真态无法通过。',
     '→ **同族**：用户记忆「"命中 0"≠"干净"、候选为 0 必须 ABORT」「否定式断言要配前置钉」；'
     '本文件 R50 段（门只打印不置退出码 ⇒ 命中也 rc=0）——同一条"绿是命令给的，不是判据给的"。'),

    # ④ 单引号里的撇号
    ('[错误类型] **Python 单引号字符串的正文里嵌 ASCII 撇号 ⇒ 字面量在撇号处提前闭合、后半句变成合法表达式，'
     '语法体检照过、运行时才炸成一句与内容毫无关系的 `TypeError`（pow / 幂运算）**',
     '症状：`land_r61b_readme12.py`（README 第十二格落地器）在**写盘之前**的裁决段报 '
     '`TypeError: unsupported operand type(s) for ** or pow()`：某格正文里嵌了一只 ASCII 撇号，'
     '单引号字面量在撇号那一列被截断，剩下的文本里带着两个星号 ⇒ 解释器把它们读成幂运算。'
     '它通过了三步序的第一道（语法体检），因为"提前闭合之后剩下的仍然是合法 Python"；'
     '直到真跑起来才炸，而且炸得与文案内容毫无关系 —— 报的是一行运算符类型错，看不出任何"某句话里有个多余引号"的线索。'
     '那一遍盘上零改动（pre-image 未生成，同目录那只 15:05 的 pre-image 属于后一遍）。',
     '→ 正确做法：①正文里的引号一律用中文「」或全角；撇号（ASCII 单引号）在这个仓库的中文正文里**没有合法用途**，'
     '需要指代它时用 `chr(39)` 现拼、不在源码字面量里出现；'
     '②`ast.parse` 只挡语法，不挡"字面量提前闭合后仍然合法"这一类 ⇒ 落地器要把**内容级**闸排在语法闸之后：'
     '本遍沿用的未插值占位符零容忍 + 反斜杠字符零容忍（正文含该字符的行数 = 0）+ 明文闸 + 撇号零容忍，四道全在写盘前；'
     '③崩在写盘前的那一遍，除点名"崩在哪一行"外，还要点名"它没写盘"（pre-image 未生成 / 目标字节未变），'
     '否则"rc 非 0"和"零改动"是两件事，前者不蕴含后者。',
     '→ **同族**：本文件 R53 段「三步序 = ast.parse → 哨兵零容忍 → 减号列为 0，本批三次栽在中文里嵌 ASCII 双引号」'
     '（同族第一型：双引号，那次被 ast.parse 拦住）；用户记忆「非 raw 串里的反斜杠 = 一只隐形 CR，'
     '三把量具同时瞎」——这一族的共同点是 **Python 词法层吃掉了中文正文，而所有按"内容"设计的尺子都量不到词法层**。'),
]

for _t, _s, _f, _k in ENTRIES:
    for _l in (_t, _s, _f, _k):
        assert chr(39) not in _l, 'ABORT: 正文含 ASCII 撇号，第④条讲的就是这个：' + _l[:60]
        assert BS not in _l, 'ABORT: 正文含反斜杠字符'

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += [t, s, fix, kin, '']


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十八批 %d 条】** 追加之前现读磁盘：`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B；'
        '本批正文 = **%d** 条 / **%d** 行（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；'
        '台账行自身不另加条目；**本遍无就地订正**（纯追加）；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**。'
        '**盘上证明 = 三段式**（第十八批第①条自己就是它的执行者）：前缀 %d 行逐字等 + 追加段 %d 行逐行等 + 后缀为空，'
        '另加行数等式 盘上行 == 前 %d + %d；**本遍不再用逐位置差集**（那种写法在纯插入下把插入点之后每行都判不等，'
        'README 第十二格那一遍就这样 rc=1 而盘上内容是对的）。'
        '本遍进入前的读数出处（每只名都由脚本现读 `getsize` 过，第十八批第②条的闸）：'
        '同目录 `%s`（第十七批 rc=0）、`%s`（第十二格复核权威遍 PROOF_ONLY_OK rc=0）、`%s`（载体行订正遍 rc=0）、'
        '盘上 `%s`（第十二格写盘前原件 / 现读 %s B）、`%s`（本脚本自身）。'
        '**本遍进入前 rc=1 的那几遍**（第十八批自己）= %s，逐只现读其 stdout 不含 PRE-IMAGE 与 LANDED 两个标记 '
        '⇒ 那几遍全部崩在写盘之前、盘上零改动（第十八批第④条第③点的自查）。'
        '本遍新装三道闸（都排在写盘之前）：①**载体存在性闸** = 台账行与正文点名的每只载体现跑 `getsize`，'
        '且按 `r61b_readme12_land_*` 前缀现扫必须为 **0 只**（这一条把"崩的那遍没写载体"钉成断言而不是叙述）；'
        '②**漂移归因闸** = 引 status 行数那格的 %d -> %d / 差 %d 必须由新增取证只数 %d 精确解释，名单逐只点名进正文；'
        '③**内容级闸** = 本批新写文本含 ASCII 撇号的行数 = 0（第十八批第④条：撇号会让单引号字面量提前闭合而 ast.parse 不报）、'
        '含反斜杠字符的行数 = 0、未插值占位符 = 0、PROV_PASS 宏值命中 = 0（口令由脚本从宏现读、全程不打印）。' % (
            ts, len(ENTRIES), n_before, lines_before, format(bytes_before, ','),
            len(ENTRIES), len(rows),
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ','),
            lines_before, len(rows) + 1, lines_before, len(rows) + 1,
            os.path.basename(car('r61b_freqerr17_*.txt', 'VERDICT=LANDED rc=0')[0]),
            os.path.basename(P151152), os.path.basename(FIXC),
            os.path.basename(PRE12), format(pre12_b, ','), os.path.basename(__file__),
            '、'.join('`%s`' % x for x in crash18),
            d_from, d_to, d_diff, d_n))


hdr = build(bytes_before)
for _ in range(10):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与台账行自身长度不收敛')

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
exp = pre + append_bytes
assert sec not in exp, 'ABORT: 本遍写出去的字节含口令明文'
_newtext = append_bytes.decode('utf-8')
_stray = [l for l in _newtext.split('\n') if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本遍新写文本有 %d 行带未插值占位符' % len(_stray)
assert BS not in _newtext, 'ABORT: 本批新写文本含反斜杠字符'
assert chr(39) not in _newtext, 'ABORT: 本批新写文本含 ASCII 撇号'
exp_entries = sum(1 for l in exp.splitlines() if l.startswith(EB))
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 终态条目数 %d != %d' % (exp_entries, n_before + len(ENTRIES))
assert hdr.encode('utf-8') in exp and ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: 终态字节数与台账行不自洽'

_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'freqerr_pre18_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('CARRIER_GATE 点名载体 %d 只全在盘上 / r61b_readme12_land_* 前缀现扫 = %d 只（预期 0）' % (4, len(land_cars)))
print('DRIFT %d -> %d / 差 %d == 新增取证 %d：%s' % (d_from, d_to, d_diff, d_n, d_names))

io.open(TGT, 'wb').write(exp)
chk = io.open(TGT, 'rb').read()
cl, ol = chk.splitlines(), pl
# —— 三段式盘上证明 ——
assert len(cl) == len(ol) + len(rows) + 1, 'ABORT: 行数增量与预期不等（%d -> %d）' % (len(ol), len(cl))
assert cl[:len(ol)] == ol, 'ABORT: 前缀未逐字保持（本遍是纯追加，前缀一字节都不许动）'
_ap = append_bytes.split(b'\r\n')[:-1]
assert cl[len(ol):] == _ap, 'ABORT: 追加段逐行不等'
post_entries = sum(1 for l in cl if l.startswith(EB))
assert (post_entries, chk.count(b'\n'), len(chk)) == (exp_entries, exp.count(b'\n'), len(exp)), 'ABORT: 盘上复量与内存终态不同值'
assert MARK.encode('utf-8') in chk and post_entries == n_before + len(ENTRIES)
print('ENTRIES %d -> %d (本批 +%d) | LINES %d -> %d | BYTES %d -> %d' % (
    n_before, post_entries, len(ENTRIES), lines_before, chk.count(b'\n'), bytes_before, len(chk)))
print('PREFIX %d 行逐字等 / APPEND %d 行逐行等 / 后缀为空（三段式）' % (len(ol), len(_ap)))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
