# FreqErr.md 第十六批落地器（R61b 收口遍）+ 两处就地订正。
# 两处订正都是**上一遍（第十五批）落盘后自己被抓出来的**：
#   (a) 第十三批台账行里我回填的那段结尾没闭合，把原句尾巴留成一只孤立的 " B，"（半句话读起来像机器拼的）；
#   (b) 第十五批台账行那句"写完后本脚本还在盘上复量一次，两处必须同值"**没跑成** —— 落地器在盘上证明段 ABORT，
#       终态三格是由独立只读复核遍 `verify_freqerr15_r61b.py` 现数复量的（rc=0）。
# 规矩照旧：幂等门 → 全部裁决排在写盘之前 → pre-image → 写盘后**行级**差集证明（不再拿字符偏移猜字节位置）。
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
MARK = 'R61 第十六批'


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）' % (prefix, must, len(hits))
    return hits[0]


# 本遍**自己**的载体正在被 tee 写进来，所以"上一遍崩在哪只载体"必须按 mtime 排除本进程之后落盘的：
# 否则同一句 ABORT 会在下一遍被两只载体同时命中，而那一遍恰恰需要这只名字。
_T0 = time.time()


def abort_carrier(marker):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, 'r61b_freqerr16_*.txt')))
            if os.path.getmtime(p) < _T0 and marker in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 标记 %r 命中 %d 只（应为 1）' % (marker, len(hits))
    return hits[0]


VER = one('r61b_freqerr15_verify_*.txt', 'VERDICT=STILL_TRUE rc=0')
LAND = one('r61b_freqerr15_*.txt', 'ABORT: 订正段逐字不等')     # 第十五批那一遍崩在证明段的载体（名字现扫，不硬编码）
PIMG_OLD = one('freqerr_pre15_*.md')
ABORT0 = abort_carrier('AssertionError: ABORT: 订正 (b) 没有执行者')   # 首遍：锚文本命中 2 行（模板句在册复制）
ABORT1 = abort_carrier('AssertionError: ABORT: 全册仍有')             # 次遍：新装的扫尺打在本批自己的引文上

pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十六批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'

pl = pre.splitlines()
n_before = sum(1 for l in pl if l.startswith('[错误类型]'.encode('utf-8')))
lines_before = pre.count(b'\n')
bytes_before = len(pre)

# ---------- 两处就地订正：整句现读，替换体首尾与原段对称 ----------
def fix_pair(old_sub, new_sub, tag):
    hits = [i for i, l in enumerate(pl) if old_sub.encode('utf-8') in l]
    assert len(hits) == 1, 'ABORT: 订正 %s 的锚文本命中 %d 行（应为 1）' % (tag, len(hits))
    ln = hits[0]
    assert '\n' not in old_sub and '\n' not in new_sub, 'ABORT: 订正 %s 的替换体带换行' % tag
    return ln, old_sub, new_sub


# F2 的锚文本光靠那句模板**不唯一**：`（写完后本脚本还在盘上复量一次，两处必须同值）` 在册 2 处 ——
# 第 2280 行（第十四批，它确实跑到了复量那步，claim 为真，不许动）与第 2311 行（第十五批，claim 为假）。
# 于是锚必须带上**第十五批独有**的那格终态字节数，而那个数由台账行现读，不硬编码。
_TMPL = '（写完后本脚本还在盘上复量一次，两处必须同值）'
_hits = [i for i, l in enumerate(pl) if _TMPL.encode('utf-8') in l]
assert len(_hits) == 2, 'ABORT: 那句模板在册 %d 处（预期 2：第十四批真复量 + 第十五批没复量）' % len(_hits)
_L15 = [l for l in pl if 'R61 第十五批'.encode('utf-8') in l]
assert len(_L15) == 1, 'ABORT: 第十五批台账行现读 %d 只（应为 1）' % len(_L15)
_m15 = re.search(r'B \*\*([\d,]+)\*\*' + _TMPL, _L15[0].decode('utf-8'))
assert _m15, 'ABORT: 第十五批台账行取不到"终态字节数紧邻那句模板"的形状 ⇒ 锚拼不出来'
F2_PRE = 'B **%s**' % _m15.group(1)
F2_OLD = F2_PRE + _TMPL
F2_NEW = (F2_PRE + '（**写完后本脚本没跑到复量那步**：它在盘上证明段 ABORT、rc=1，载体 = 同目录 `%s`；'
          '终态三格由**独立只读复核遍** `verify_freqerr15_r61b.py` 现数复量，两处同值，载体 = 同目录 `%s`）') % (
              os.path.basename(LAND), os.path.basename(VER))
F1_OLD = ('行） B，落盘后同一把尺回读必须逐字相等（本遍实测相等）。')
F1_NEW = ('行）。**这句"实测相等"是第十三批自己写的，而它当时那三格根本没插值 ⇒ 落笔即无法核对**；'
          '14:16 遍把三格回填成 244 / 2254 / 462,106（出处见上一括号），本遍再把被劈开的半句接回去。')
P1 = fix_pair(F1_OLD, F1_NEW, '(a) 孤立 " B，"')
P2 = fix_pair(F2_OLD, F2_NEW, '(b) 没有执行者的"还在盘上复量"')
for ln, o, n in (P1, P2):
    _l = pl[ln].decode('utf-8')
    assert _l.count(o) == 1, 'ABORT: 第 %d 行里锚文本出现 %d 次' % (ln + 1, _l.count(o))
    assert not re.search(r'）\s*B，', n), 'ABORT: 订正 (a) 的新句仍然把单位劈在括号外'
LN1, LN2 = P1[0] + 1, P2[0] + 1
_split = [i + 1 for i, l in enumerate(pl) if re.search(r'）\s*B，'.encode('utf-8'), l)]
assert _split == [LN1], 'ABORT: 写盘前"括号紧跟单位"的被劈开行 = %s（预期只第 %d 行，本批正文那条"命中恰 1 处"说的是这个数）' % (
    _split, LN1)

_mid = pre.replace(F1_OLD.encode('utf-8'), F1_NEW.encode('utf-8'), 1)
_mid = _mid.replace(F2_OLD.encode('utf-8'), F2_NEW.encode('utf-8'), 1)
assert _mid != pre and _mid.count(b'\n') == lines_before, 'ABORT: 订正没有生效或改了行数'
assert sum(1 for l in _mid.splitlines() if l.startswith('[错误类型]'.encode('utf-8'))) == n_before, 'ABORT: 订正改了条目数'
D1, D2 = len(F1_NEW.encode('utf-8')) - len(F1_OLD.encode('utf-8')), len(F2_NEW.encode('utf-8')) - len(F2_OLD.encode('utf-8'))
assert len(_mid) == bytes_before + D1 + D2, 'ABORT: 订正后的尺寸与两处增量之和不等于现读'
assert F1_OLD.encode('utf-8') not in _mid and F2_OLD.encode('utf-8') not in _mid, 'ABORT: 旧句仍在'

# 第②条要说"加粗只数看不见被劈开句"，那这个只数就必须是**三只载体各现读一次**的数，不是我印象里的 24：
# pre-image（第十五批写盘前）/ 盘上现读（第十五批写盘后）/ 本遍订正后，三态同一行的 `**` 只数。
_pl_pre15 = io.open(PIMG_OLD, encoding='utf-8').read().splitlines()
_ap = int(re.search(r'尾部追加 (\d+) 行', io.open(VER, encoding='utf-8').read()).group(1))
assert len(_pl_pre15) + _ap == lines_before, 'ABORT: pre-image %d 行 + 第十五批追加 %d 行 != 盘上现读 %d 行 ⇒ 那只 pre-image 不是这一遍的上一态' % (
    len(_pl_pre15), _ap, lines_before)
B4 = _pl_pre15[LN1 - 1].count('**')
B5 = pl[LN1 - 1].decode('utf-8').count('**')
B6 = pl[LN1 - 1].decode('utf-8').replace(F1_OLD, F1_NEW).count('**')
assert B5 - B4 == 2 and B6 - B5 == 2, 'ABORT: 加粗只数三态增量 = %d/%d（各应为 2）⇒ 第②条那句"配对尺放过它"得重写' % (
    B5 - B4, B6 - B5)
# 第①条要说"证明段停在了行首"，那"停在行首差多少"也得是现读的字节数，不是 ~500 这种印象值。
_L1 = pl[LN1 - 1].decode('utf-8')
OFF_B = len(_L1[:_L1.index(F1_OLD)].encode('utf-8'))
assert OFF_B > 300, 'ABORT: 第 %d 行里替换段距行首只有 %d B ⇒ 第①条"行首偏移差一大截"的说法要重写' % (LN1, OFF_B)

ENTRIES = [
    ('**写盘后的证明段把"整行起始偏移"当成"替换段偏移"用 ⇒ 内容已经正确落盘，证明却红了**'
     '（R61b 实测：`land_r61b_freqerr15.py` 在 `write(exp)` 之后跑三段证明，第一段用 `pre.index(整行)` 得到的 `_i` '
     '去比"替换段"，而替换段在那一行**内部**再往后 %d B（本遍现读该行的段前字节数）⇒ `订正段逐字不等` ABORT，'
     'rc=1，盘上终态其实已是预期内容）' % OFF_B,
     '症状：最坏的一种红 —— 它说的不是"盘错了"，而是"我证明不了盘对"，而我很容易把它读成前者，'
     '于是下一步就是"重跑一遍"；这一遍恰好有幂等门挡着才没造成第二次追加（没有门就是同一节落两份，那族本文件已登记过一次）。'
     '独立复核遍现读：逐行差集 = 就地改 1 行 + 追加 %d 行 / 删除 0 行 ⇒ 盘对、证明错。' % _ap,
     '→ 正确做法：①中部改动的**行级**证明优先于字节偏移证明：`pre.splitlines()` 与 `chk.splitlines()` 逐行比，'
     '要求"差异行数 == 预期"且"其余行逐字等"，本遍复核脚本就是这么写的（它同时抓出了另外两件事，见第②条）；'
     '②偏移版证明必须把偏移算到**被替换的那一段**（`_i + line.index(seg)`），不许停在行首；'
     '③证明段崩了之后，**先用只读脚本判"盘对不对"，再决定要不要动盘** —— 顺序反了就是拿重跑洗绿。',
     '→ **同族**：项目记忆「崩溃那次的读数不作数」「已跑完/已冻结要带 rc + 载体文件名且不许重跑洗绿」'
     '「落地器的字节证明不含位置属性」（那条讲尺寸，本条讲偏移，同一族：证明本身是新的缺陷点）。'),
    ('**回填句的结尾没与原段对称闭合：整句被劈开，留下孤立的 " B，"，而加粗配对与行数两把尺都看不见**'
     '（R61b 实测：第十五批订正第十三批台账行时，替换体以 `）` 收尾，原段却含结尾那对 `**` ⇒ '
     '落盘后那句读作"…第 2254 行） B，落盘后同一把尺回读…"；本批写盘前全册扫 `）\\s*B，` 命中恰 1 处 = 该行）',
     ('症状：第 %d 行的 `**` 只数三态现读 = %d（第十五批写盘前，取自它的 pre-image）-> %d（它写盘后，盘上现读）'
      '-> %d（本遍订正后），每态恰好差一对 ⇒ 加粗配对、行数、条目数三把尺全放过（配对尺只看见"多了一对"，'
      '而那本来就是回填句该有的），坏的是**人读的那一句不通** —— 这类缺陷在语法层，不在结构层。' % (LN1, B4, B5, B6)),
     '→ 正确做法：①替换体的首尾必须与原段**对称**：切进来时带着 `**` 就必须带着 `**` 出去（本遍 `fix_pair` 的锚文本'
     '直接以完整句为段，含标点，不留在括号外半只单位）；②落盘前把**整行**的改前/改后各打印一次自己读一遍'
     '（只打印替换段读不出上下文，本遍打印整行）；③给"被劈开"装一把扫尺 —— 而这把尺的**管辖范围**必须先定：'
     '本遍首跑把它写成"全册 = 0"，结果它**打在了本批第②条自己引用这个形状的引文上**（rc=1，写盘前，盘上零改动）'
     '⇒ 口径改成两条：既有正文（订正后的 `_mid`）= 0 是闸门，全册命中逐行点名且必须**全部落在本批新写的条目区**（引文不是缺陷）。'
     '同一族在第十五批第②条刚登记过（那条是"刻意不写出花括号，写出来就会被本遍那道新门拦下 ⇒ 拿它当阳性对照"），'
     '本遍的增量是：**在没安排阳性对照的那一遍，这道门真的把运行打断了一次**。',
     '→ **同族**：本文件第十五批第②条（同一只回填句的**上一半**缺陷：哨兵没插值）、项目记忆'
     '「订正句本身也是断言载体」（R51/R52 三连犯）、本条是它的第四种形态：订正句**语法**错而不是事实错。'),
    ('**就地订正的锚文本取自上一批的台账模板句 ⇒ 命中 2 行，而这两行的主张一真一假**'
     '（R61b 实测：本批第一次运行 ABORT 在 `ABORT: 订正 (b) 没有执行者的"还在盘上复量" 的锚文本命中 2 行（应为 1）`；'
     '那句 `（写完后本脚本还在盘上复量一次，两处必须同值）` 在册两处 —— 第 2280 行（第十四批，它确实复量过，主张为真）'
     '与第 2311 行（第十五批，它崩在复量之前，主张为假）；两遍均 rc=1、盘上零改动）',
     '症状：台账模板句会被后来的批次当成措辞惯例复制，于是"这句全册只出现一次"这个**没写下来的前提**在下一批就破了。'
     '真正的坏法在下一格：如果我当时图省事把 `replace(..., 1)` 的 `1` 当保险，脚本会**改到第一处**，'
     '也就是把一句真话改成假话，而行数、条目数、加粗配对三把尺全过 —— 尺寸等式对"改错行"这件事完全不敏感。',
     '→ 正确做法：①锚的唯一性由**本批独有的那一格**拼出来（本遍用第十五批的终态字节格作前缀），'
     '不靠替换参数 `1`、也不靠"我以为只有一处"；②那一格的数值必须**从被订正的那一行现读**（本遍 '
     '`re.search` 出台账行里的字节格再拼回锚），既不硬编码也不从别批推；③命中数不为 1 时先把**所有命中行逐行列出**、'
     '判每一行的真假，再决定改哪一行 —— "一真一假"这个结论要写进正文，否则后来者会以为这句惯例整体可疑；'
     '④幂等门与"写盘前全部裁决"是这两遍 rc=1 只损失一次运行的原因，不是可以省掉它们的理由。',
     '→ **同族**：本文件第十五批第①条（同一族：模板句被复制成惯例）、项目记忆「引用即复跑：抄来的行号落笔前自己重跑一遍」'
     '「汇总行不许只认一种格式」（都是**把上一批的措辞当成这一批的常量**）。'),
]

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += ['[错误类型] ' + t, s, fix, kin, '']


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十六批 %d 条】** 追加之前现读磁盘（本脚本进入时刻 %s）：'
        '`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B；本批正文 = **%d** 条 / **%d** 行'
        '（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；台账行自身不另加条目；'
        '**同遍就地订正两处**：第 %d 行 %d B -> %d B、第 %d 行 %d B -> %d B，两处的行数与条目数都不变；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**'
        '（本遍的盘上证明走**行级差集**，不再用字节偏移；两处旧句的残留由 `count == 0` 兜；'
        '"被劈开句"扫尺的口径 = 既有正文 0 是闸门 + 全册命中逐行点名并须全部落在本批条目区，'
        '因为本批第②条自己引用了那个形状）。'
        '本遍落盘之前已两次 rc=1、两次盘上零改动：载体 = 同目录 `%s`（锚命中 2 行）与 `%s`（门打到自己正文）。'
        '口径明文闸 = 追加段与两处订正段现扫 PROV_PASS 宏值命中 0 才动手。' % (
            ts, len(ENTRIES), ts, n_before, lines_before, format(bytes_before, ','),
            len(ENTRIES), len(rows),
            LN1, len(F1_OLD.encode()), len(F1_NEW.encode()), LN2, len(F2_OLD.encode()), len(F2_NEW.encode()),
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ','),
            os.path.basename(ABORT0), os.path.basename(ABORT1)))


hdr = build(bytes_before + D1 + D2)
for _ in range(8):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + D1 + D2 + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与 header 自身长度不收敛')

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
exp = _mid + append_bytes
assert sec not in exp, 'ABORT: 本遍写出去的字节含口令明文'
_newtext = (append_bytes.decode('utf-8') + '\n' + F1_NEW + '\n' + F2_NEW)
_stray = [l for l in _newtext.split('\n') if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本遍新写文本有 %d 行带未插值占位符：%r' % (len(_stray), [l[:70] for l in _stray[:2]])
SPLIT_RE = re.compile(r'）\s*B，')
assert not SPLIT_RE.search(_mid.decode('utf-8')), 'ABORT: 既有正文（两处订正之后）仍有"括号紧跟单位"的被劈开句'
_hits2 = [i + 1 for i, l in enumerate(exp.splitlines()) if SPLIT_RE.search(l.decode('utf-8'))]
assert all(i > lines_before for i in _hits2), 'ABORT: 被劈开形状出现在既有正文区 %s（应只在本批新写的引文里）' % _hits2
print('SPLIT-SHAPE 既有正文(订正后)=0 | 全册=%d 处，行号 %s（都在本批条目区的引文里，不是缺陷）' % (len(_hits2), _hits2))
exp_entries = sum(1 for l in exp.splitlines() if l.startswith('[错误类型]'.encode('utf-8')))
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 终态条目数 %d != %d' % (exp_entries, n_before + len(ENTRIES))
assert hdr.encode('utf-8') in exp and ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: 终态字节数与台账行不自洽'
_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'freqerr_pre16_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'
# 整行改前/改后各打印一次：结构尺看不见的那半句，只能由人读出来（本遍把整行落进载体，事后也可核）
for ln, o, n in (P1, P2):
    _bef = pl[ln].decode('utf-8')
    _aft = _bef.replace(o, n)
    print('整行 %d 改前(尾 120): ...%s' % (ln + 1, _bef[-120:]))
    print('整行 %d 改后(尾 200): ...%s' % (ln + 1, _aft[-200:]))

io.open(TGT, 'wb').write(exp)
chk = io.open(TGT, 'rb').read()
cl, ol = chk.splitlines(), pl
assert len(cl) == len(ol) + len(rows) + 1, 'ABORT: 行数增量与预期不等（%d -> %d）' % (len(ol), len(cl))
_diff = [i for i in range(len(ol)) if cl[i] != ol[i]]
assert _diff == [P1[0], P2[0]], 'ABORT: 盘上就地改动行号 = %s（预期 %s）' % ([x + 1 for x in _diff], [LN1, LN2])
assert cl[len(ol):] == append_bytes.split(b'\r\n')[:-1], 'ABORT: 追加段逐行不等'
post_entries = sum(1 for l in cl if l.startswith('[错误类型]'.encode('utf-8')))
assert (post_entries, chk.count(b'\n'), len(chk)) == (exp_entries, exp.count(b'\n'), len(exp)), 'ABORT: 盘上复量与内存终态不同值'
assert F1_OLD.encode('utf-8') not in chk and F2_OLD.encode('utf-8') not in chk, 'ABORT: 旧句仍在盘上'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('EOL CRLF=%d bareLF=%d | APPEND=CRLF' % (chk.count(b'\r'), chk.count(b'\n') - chk.count(b'\r')))
print('ENTRIES %d -> %d (本批 +%d) | LINES %d -> %d | BYTES %d -> %d' % (
    n_before, post_entries, len(ENTRIES), lines_before, chk.count(b'\n'), bytes_before, len(chk)))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
