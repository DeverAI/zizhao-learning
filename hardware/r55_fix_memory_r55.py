# R55 订正批：把上一遍（14:07:20 那一跑）落到项目记忆里的两处**假读数**就地换字，并为此另立 (103)-(104)
# 派生自 hardware/r55_land_memory_r55.py（那只落地器）。四件事：
#  ①它把"第九次读数"那一格的时刻插成了自己的落地时刻（本遍现跑值冒充了被引用动作的时刻）；
#  ②它用裸 re.search 去 evidence/r55_roundtrip_2.txt 取裁决，而那只文件第 4 行 PRIOR_VERDICT=VERDICT=SCP_FAILED
#    与末行 VERDICT=REMOTE_CARRIES_PLAINTEXT 同形 ⇒ 取回的是**上一遍**的失败；
#  ③被改的只有本批自己那一遍落的四行 + 索引那一行，别人的历史登记一处不碰；
#  ④上一遍载体 hardware/r55_land_memory_r55.txt 里那句假裁决**保留原样**（不拿重跑洗绿），只在本遍载体点名。
# 口径：正文里出现的每一个数都由本遍现跑算出并插值；待追加全段零反斜杠（§38.18 那族），末尾断言兑现。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
PMEM = r'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/memory'
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
RT2 = os.path.join(REPO, 'hardware', 'ht305_sync', 'evidence', 'r55_roundtrip_2.txt')
CAR9 = os.path.join(REPO, 'hardware', 'r55_backups_readme9.txt')
PREV = os.path.join(REPO, 'hardware', 'r55_land_memory_r55.txt')
MAN = os.path.join(REPO, 'hardware', 'ht305_sync', 'MANIFEST.txt')
PMB = os.path.join(PMEM, 'hardware-epaper397-power.md')
PMI = os.path.join(PMEM, 'MEMORY.md')
FIXC = os.path.join(REPO, 'hardware', 'r55_fix_memory_r55.txt')

NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
por = [l for l in subprocess.run(['git', '-c', 'core.quotePath=false', 'status', '--porcelain'],
                                 capture_output=True, cwd=REPO).stdout.decode('utf-8', 'replace')
        .split('\n') if l.strip()]


def stat(p):
    b = open(p, 'rb').read()
    return b.count(b'\n'), len(b), b.count(b'\r'), hashlib.md5(b).hexdigest()[:8]


def read(p):
    return open(p, encoding='utf-8').read()


def write_lf(p, t):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)


# ---------- 三只取证源现读：订正用到的每一个真值都在这里，正文一律插值 ----------
rt2 = read(RT2)
rt2_ls = rt2.split('\n')
prior_i = [i for i, l in enumerate(rt2_ls) if l.startswith('PRIOR_VERDICT=')]
final_i = [i for i, l in enumerate(rt2_ls) if re.match(r'^VERDICT=', l)]
assert len(prior_i) == 1 and len(final_i) == 1, 'PRIOR 行与本遍裁决行各自只 1 行的前提不成立：%s / %s' % (prior_i, final_i)
prior_raw = rt2_ls[prior_i[0]]
prior_val = re.search(r'PRIOR_VERDICT=(\S+)', prior_raw).group(1)
final_val = re.search(r'VERDICT=(\S+)', rt2_ls[final_i[0]]).group(1)
assert prior_val != final_val, 'PRIOR 与本遍裁决同值 ⇒ 本订正前提被推翻：' + prior_val
assert final_val == 'REMOTE_CARRIES_PLAINTEXT', '末行裁决不是期望那只：' + final_val
naive = re.search(r'VERDICT=(\S+)', rt2).group(1)
assert naive == prior_val, '缺陷复现失败：裸 search 取到的不是 PRIOR 那行（取到 %s / PRIOR=%s）' % (naive, prior_val)
rt2_at = re.search(r'RAN_END_AT=(.*)', rt2).group(1).strip()

rd9_now = re.search(r'现跑于 ([0-9-]{10} [0-9:]{8})', read(CAR9)).group(1)
prev_t = read(PREV)
prev_ls = prev_t.split('\n')
landed_now = re.search(r'正文里那些时刻 = ([0-9-]{10} [0-9:]{8})', prev_t).group(1)
prev_verdict_at = [i + 1 for i, l in enumerate(prev_ls) if '重跑 ' + naive in l]
assert len(prev_verdict_at) == 1, '上一遍载体里点名假裁决那一行不唯一：%s' % prev_verdict_at
prev_sync_ln = prev_verdict_at[0]
assert rd9_now != landed_now, '两只时刻同值 ⇒ "冒充"这条不成立，先查是谁改了谁'
gap_min = (int(landed_now[11:13]) - int(rd9_now[11:13])) * 60 + int(landed_now[14:16]) - int(rd9_now[14:16])

man = read(MAN)
man_total = re.search(r'^TOTAL\t(\d+)', man, re.M).group(1)
man_bytes = format(int(re.search(r'^TOTAL_BYTES\t(\d+)', man, re.M).group(1)), ',')
man_bom = re.search(r'^BOM_FILES\t(\d+)', man, re.M).group(1)

b_t = read(PMB)
i_t = read(PMI)
FAKE_HEAD = landed_now + ' backups/README.md 第九次读数'
TRUE_HEAD = rd9_now + ' backups/README.md 第九次读数'
FAKE_V, TRUE_V = naive, 'VERDICT=' + final_val
assert len(FAKE_HEAD) == len(TRUE_HEAD), '两只时刻不等长 ⇒ 下面那条"字节数只由追加与裁决串决定"的等式不成立'
# ---------- 幂等闸（同一脚本崩溃复跑不得二次换字/二次追加）----------
# 第一次跑到本文件末尾的 (103)/(104) 落点计数那条断言时崩了：期望值 (104)=3 是我**猜的**，
# 而崩溃点在 write_lf **之后** ⇒ 换字与三行追加已经落盘、载体没写。本遍只许复算 + 补载体，不许再写一遍。
APPEND_HEAD = '  (103) **裁决类字段必须锚定行首'
MODE = 'CORRECTED_NOW' if b_t.count(FAKE_HEAD) == 1 else 'REWROTE_CARRIER_ONLY'
FIXED_MARKS = [b_t.count(FAKE_HEAD) == 0, b_t.count(TRUE_HEAD) == 1,
               b_t.count('定下的 (101)-(102)**') == 0, i_t.count('R55 收口批另立 (101)-(102)') == 0,
               APPEND_HEAD in b_t, i_t.count(TRUE_V) >= 1]
if MODE == 'CORRECTED_NOW':
    assert sum(FIXED_MARKS) == 0, '四只锚半落地（既没换完又没落到本遍起点）：%s' % FIXED_MARKS
    assert b_t.count(FAKE_V) == 1 and i_t.count(FAKE_V) == 1, '假裁决串两处应各 1：%d / %d' % (b_t.count(FAKE_V), i_t.count(FAKE_V))
    assert b_t.count('定下的 (101)-(102)**') == 1 and i_t.count('R55 收口批另立 (101)-(102)') == 1, '段标题与索引的序数锚各应 1 处'
else:
    assert all(FIXED_MARKS), '判定为"已订正"但锚不全：%s' % FIXED_MARKS
    a_ln = b_t.index(APPEND_HEAD)
    APPEND_DISK = b_t[a_ln:]
    # 正文里假裁决剩下的每一处都必须出自订正段自身（引文），订正段之外 0 处
    assert b_t.count(FAKE_V) == APPEND_DISK.count(FAKE_V) and i_t.count(FAKE_V) == 0, \
        '订正段之外仍残留假读数：正文 %d vs 订正段 %d / 索引 %d' % (b_t.count(FAKE_V), APPEND_DISK.count(FAKE_V), i_t.count(FAKE_V))
assert b_t.endswith('\n') and b_t.count('\r') == 0 and i_t.count('\r') == 0, '目标文件行尾口径不干净'

b_ln0, b_b0, b_cr0, b_m0 = stat(PMB)
i_ln0, i_b0, i_cr0, i_m0 = stat(PMI)
v_delta = len(TRUE_V) - len(FAKE_V)
if MODE == 'REWROTE_CARRIER_ONLY':
    # 改前基线只能从**订正段自己那行等式**里现读（崩溃那遍没落载体 ⇒ 改前 md5 不复算、不编）
    mb = re.search(r'项目正文 (\d+) B → \1 \+ (\d+) = \*\*(\d+) B\*\*、(\d+) 行 → \*\*(\d+) 行\*\*（\+3）', APPEND_DISK)
    mi = re.search(r'索引 (\d+) B → \*\*(\d+) B\*\*、LF 仍 (\d+)', APPEND_DISK)
    assert mb and mi, '订正段里那两条自述等式没读回来 ⇒ 基线无从复算'
    pb0_r, inc_r, pb1_r, pl0_r, pl1_r = [int(x) for x in mb.groups()]
    pi0_r, pi1_r, pil_r = [int(x) for x in mi.groups()]
    assert pb0_r + inc_r == pb1_r and pl0_r + 3 == pl1_r and pi0_r + v_delta == pi1_r, \
        '订正段自述的等式自身不闭合：%s / %s / %s' % ((pb0_r, inc_r, pb1_r), (pl0_r, pl1_r), (pi0_r, pi1_r))
    assert (b_b0, b_ln0) == (pb1_r, pl1_r) and (i_b0, i_ln0) == (pi1_r, pil_r), \
        '盘上现状与订正段自述的改后值不符：正文 (%d,%d) 应 (%d,%d) / 索引 (%d,%d) 应 (%d,%d)' % (
            b_b0, b_ln0, pb1_r, pl1_r, i_b0, i_ln0, pi1_r, pil_r)
    NOW_FIX = NOW
    NOW = re.search(r'R55 落地后自查订正（([0-9-]{10} [0-9:]{8}) 现跑', APPEND_DISK).group(1)
    b_m0 = 'NOT_RECORDED'
    i_m0 = 'NOT_RECORDED'
    b_b0, b_ln0 = pb0_r, pl0_r
    i_b0, i_ln0 = pi0_r, pil_r

# ---------- 待追加三行：先算不含自身的长度，再回填等式（哨兵零容忍兑在末尾） ----------
APPEND = (
    "  (103) **裁决类字段必须锚定行首、取最后一处，并把取到的行号随值一起登记：同一只取证里'上一遍的裁决'与'本遍的裁决'可以逐字同形，裸子串 search 会静默取回上一遍**："
    "本遍 {now} 现读 evidence/r55_roundtrip_2.txt，第 {prior_ln} 行是 {prior_raw}（把上一遍失败转抄进来），第 {final_ln} 行才是 {final_line}（本遍 {rt2_at} 的真结果）。"
    "落地器只按子串 VERDICT= 起搜、取**第一个**匹配 ⇒ 命中的正是第 {prior_ln} 行里 PRIOR_VERDICT= 后面那串，而且捕获组把 VERDICT= 一起吞进值里 ⇒ 于是**项目记忆正文与索引两处**把上一遍的 SCP_FAILED 登记成了本遍裁决，"
    "而同一半句的后半写着'服务器那一份仍带明文' ⇒ 一条**自相矛盾**的登记，两只量具全放行：grep 有值、断言非空。"
    "本遍以三种手段复现并堵住： (?m)^VERDICT= 取末位 + 断言它不等于同行 PRIOR_* 捕到的值 + 断言值落在期望名单里（执行件 hardware/r55_fix_memory_r55.py 三条都兑现，且'裸 search 取到 %s'这一条是当场跑出来的、不是叙述）。"
    "⇒ 泛化：凡'这一行是本遍的结论'型字段，取证文件里天然允许出现历史同形串（转抄、对照、引用都长这样）⇒ 解析器不许只按子串命中，要锚**行首**并把**行号**一起落册；同族 (63)-(65)'逐字派生把上一代恰好没踩到的缺陷派生过来'，本条是它的**读侧**版本。\n"
    "  (104) **一行里并列 N 只时刻 ⇒ 每一只都要有自己的载体来源，'整行同源'是错觉；本遍现跑值只能落在点名'本遍现跑'的那一格**："
    "上一遍落的段标题是「12:14:51 §38.18 落盘 → 12:53:39 gen 24 末版 → 13:33:42 docs 第九遍 → **{landed_now}** backups/README.md 第九次读数」，前三只时刻各自现读于对应载体，第四只却是**落地那一刻**（脚本自己的 NOW），而第九次读数真正发生在 **{rd9_now}**（载体 hardware/r55_backups_readme9.txt 第 1 行）⇒ 差 {gap_min} 分钟（按分位差、不含秒），且冒充的**不是本遍动作**。"
    "表现 = 读起来比真值更'新'，没有工具会报警；抓它的手法只有一条：把'这一格量的是哪个动作'逐格写成**那只动作自己的载体字段**，脚本里的 NOW 只允许出现在'本遍现跑'位置。"
    "⇒ 与 (69)/(71)'凭证写的时刻不等于它标的那一刻'同族：那两条讲的是**文件名/载体**的时刻，本条讲的是**同一行内并列格子的来源错配** ⇒ 越是并列、看着同源的序列，越要逐格点名来源。\n"
    "  **R55 落地后自查订正（{now} 现跑，执行件 hardware/r55_fix_memory_r55.py）**：上面 (103)-(104) 两条就是这次订正立下的。被就地换字的只有**本批自己 {landed_now} 那一遍落的段内文字**（别人的历史登记一处不碰）："
    "①段标题那格时刻 {landed_now} → {rd9_now}（两只都是 19 字符 ⇒ 等长换字、字节数不变、md5 变）；②裁决串 {fake_v} → {true_v} 各 1 处（正文 + 索引，各 +{v_delta} B）；③序数 (101)-(102) → (101)-(104) 各 1 处（等长）；④本段三行纯追加。"
    "现跑等式：项目正文 {pb0} B → {pb0} + {inc_b} = **{pb1} B**、{pl0} 行 → **{pl1} 行**（+3）、md5 {pm0} → 改后值由本遍现算并写进载体；索引 {pi0} B → **{pi1} B**、LF 仍 {pil}（只在一行内换字）。"
    "**点名不作废**：上一遍载体 hardware/r55_land_memory_r55.txt 第 {prev_sync_ln} 行那句'重跑 VERDICT=SCP_FAILED'同样出自这只错解析 ⇒ **保留原样**、以本遍为准（与 (74)(82)'不许拿重跑链把红洗成绿'同族）；该载体第 1 行 MODE=REWROTE_CARRIER_ONLY 仍然成立。"
    "订正**没碰** hardware/ht305_sync/ ⇒ 归档末版仍是 gen 24（TOTAL {man_total} / {man_bytes} B / BOM {man_bom}）、末版封界未破；排查记录 {doc_bytes} B / {doc_lines} 行逐字未动；本批零删除、未 push、屏侧现场态一只数没动。\n"
) % naive

# 追加正文里**自述自己的字节数**（{inc_b} / {pb1}）⇒ 长度与文本互相依赖，只能求不动点；不收敛就 ABORT，不拿估数充数。
R = dict(prior_ln=prior_i[0] + 1, prior_raw=prior_raw, final_ln=final_i[0] + 1,
         final_line=rt2_ls[final_i[0]], rt2_at=rt2_at, landed_now=landed_now, rd9_now=rd9_now,
         gap_min=gap_min, fake_v=FAKE_V, true_v=TRUE_V, v_delta=v_delta, prev_sync_ln=prev_sync_ln,
         now=NOW, man_total=man_total, man_bytes=man_bytes, man_bom=man_bom,
         pb0=b_b0, pb1=0, pl0=b_ln0, pl1=b_ln0 + 3, pm0=b_m0, pi0=i_b0, pi1=i_b0 + v_delta, pil=i_ln0,
         inc_b=0, app_b=0,
         doc_bytes=format(stat(DOC)[1], ','), doc_lines=stat(DOC)[0])


def render(inc):
    return APPEND.format(**dict(R, inc_b=inc, pb1=b_b0 + inc))


if MODE == 'CORRECTED_NOW':
    inc_b = 0
    for _ in range(8):
        new_inc = v_delta + len(render(inc_b).encode('utf-8'))
        if new_inc == inc_b:
            break
        inc_b = new_inc
    else:
        raise AssertionError('字节数不动点未收敛（末值 %d）⇒ 正文自述的数与自身不一致，先查' % inc_b)
    app_b = inc_b - v_delta
    APPEND = render(inc_b)
else:
    # 复算模式：待验正文 = 盘上那三行原样，长度等式反过来用（盘上字节 - 订正段 = 改前基线）
    inc_b = int(inc_r)
    app_b = inc_b - v_delta
    APPEND = APPEND_DISK
    assert len(b_t.encode('utf-8')) - app_b == b_b0 + v_delta, \
        '盘上正文扣掉订正段不等于"改前基线 + 裁决串增量"：%d vs %d' % (
            len(b_t.encode('utf-8')) - app_b, b_b0 + v_delta)
assert len(APPEND.encode('utf-8')) == app_b, '不动点之后长度又漂：%d != %d' % (len(APPEND.encode('utf-8')), app_b)
assert '\\' not in APPEND, '待追加正文里出现了反斜杠 ⇒ 正是 §38.18 那一族'
assert '%' not in APPEND, '待追加正文里残留百分号字面量 ⇒ 上一遍那一处 %%s 没被吃掉'
assert '{' not in APPEND and '}' not in APPEND, '待追加正文里有未解析的插值哨兵'
assert 'True' not in APPEND and 'None' not in APPEND, '待追加正文里有未回填的 python 字面量'

if MODE == 'CORRECTED_NOW':
    nb_t = b_t.replace(FAKE_HEAD, TRUE_HEAD).replace(FAKE_V, TRUE_V) \
             .replace('定下的 (101)-(102)**', '定下的 (101)-(104)**') + APPEND
    ni_t = i_t.replace(FAKE_V, TRUE_V).replace('R55 收口批另立 (101)-(102)', 'R55 收口批另立 (101)-(104)')
    assert len(nb_t.encode('utf-8')) - len(b_t.encode('utf-8')) == v_delta + app_b, \
        '正文增删字节不等于"裁决串 +%d 与三行追加 %d"之和：%d' % (v_delta, app_b, len(nb_t.encode('utf-8')) - len(b_t.encode('utf-8')))
    assert nb_t.count('\n') - b_t.count('\n') == 3, '正文应净增 3 行'
else:
    nb_t, ni_t = b_t, i_t      # 上一遍已换字：本遍只复核、不再写这两只
assert nb_t.count(FAKE_HEAD) == 0 and ni_t.count(FAKE_V) == 0, '换字后仍残留假读数（正文时刻 / 索引裁决）'
# 订正段自己**引**那只假裁决串若干处（PRIOR 原文、复现值、点名那句…）⇒ 判"残留"的口径是"比正文里出现的次数 == 订正段里的次数"，不是"整段为 0"
assert nb_t.count(FAKE_V) == APPEND.count(FAKE_V), '正文里假裁决次数 %d != 订正段自身 %d ⇒ 有一处没换掉' % (nb_t.count(FAKE_V), APPEND.count(FAKE_V))
assert FAKE_HEAD not in nb_t.replace(APPEND, ''), '订正段之外还留着被冒充的那个时刻'
assert ('第 %d 行' % prev_sync_ln) in APPEND and TRUE_V in nb_t, '点名/真裁决没落到位'
# 正向钉：现场态那一格（"重跑 ⇒ <裁决> ⇒ 服务器那一份"）必须已经带着真裁决
nb_wo_app = nb_t.replace(APPEND, '')
PIN = '重跑 ⇒ **' + TRUE_V + '** ⇒ 服务器'
if MODE == 'CORRECTED_NOW':
    assert nb_wo_app.count(TRUE_V) == b_t.count(TRUE_V) + 1 and ni_t.count(TRUE_V) == i_t.count(TRUE_V) + 1, \
        '被订正那一格没换成真裁决：正文（去掉订正段）%d 应 %d / 索引 %d 应 %d' % (
            nb_wo_app.count(TRUE_V), b_t.count(TRUE_V) + 1, ni_t.count(TRUE_V), i_t.count(TRUE_V) + 1)
else:
    # 复算模式没有"改前"可比 ⇒ 钉那一只格：全文件里这句逐字形状只出现 1 次，且不在订正段内
    assert nb_wo_app.count(PIN) == 1 and ni_t.count(TRUE_V) >= 1, \
        '复算模式下那一格没带真裁决：正文（去掉订正段）该形状 %d 处，应 1 处' % nb_wo_app.count(PIN)
assert PIN in nb_t, '真裁决没落在那一格里'
assert nb_t.count('\r') == 0 and ni_t.count('\r') == 0

if MODE == 'CORRECTED_NOW':
    write_lf(PMB, nb_t)
    write_lf(PMI, ni_t)
b_ln1, b_b1, b_cr1, b_m1 = stat(PMB)
i_ln1, i_b1, i_cr1, i_m1 = stat(PMI)
assert b_b1 - b_b0 == inc_b and i_b1 - i_b0 == v_delta and b_ln1 - b_ln0 == 3 and i_ln1 == i_ln0

# ---------- 修后复核（不换尺：仍用字节级 CR 计数 + 逐字回读 + 段结构） ----------
rb = read(PMB)
assert rb.endswith(APPEND), '末段与本次追加的字节不逐字相同'
rls = rb.split('\n')
i55 = [k for k, l in enumerate(rls) if l.startswith('  **R55（')]
assert len(i55) == 1, 'R55 段标题应只 1 处，现 %d' % len(i55)
assert [l.lstrip()[:5] for l in rls[i55[0] + 1:i55[0] + 7]] == ['(101)', '(102)', '**R55', '(103)', '(104)', '**R55'], \
    'R55 段七行结构不符：%s' % [l[:12] for l in rls[i55[0]:i55[0] + 8]]
assert i55[0] + 7 == len(rls) - 1, 'R55 段没有落到 EOF：其后还有 %d 行' % (len(rls) - i55[0] - 7)
# 落点计数**由订正段自身推出来**，不写猜的常数（第一次跑就栽在猜 (104)=3，实为 4）：
#   (103)：订正段 2 处（行首 + '上面 (103)-(104) 两条'）+ 订正段之外 0 处
#   (104)：订正段 3 处（行首 + 同上 + '③序数 (101)-(102) → (101)-(104)'）+ 段标题 '定下的 (101)-(104)**' 1 处 = 4
c103, c104 = rb.count('(103)'), rb.count('(104)')
assert c103 == APPEND.count('(103)') and c104 == APPEND.count('(104)') + 1, \
    '两条新规落点计数与订正段自身不一致：全文 (103)=%d (104)=%d / 订正段 (103)=%d (104)=%d' % (
        c103, c104, APPEND.count('(103)'), APPEND.count('(104)'))
assert rb.replace(APPEND, '').count('(104)') == 1, '订正段之外 (104) 只应出现在段标题那 1 处'
rix = read(PMI)
assert rix.count('\n') == i_ln0 and '(101)-(104)' in rix and '(101)-(102)' not in rix, '索引没换序数或多了行'
for p in (PMB, PMI):
    assert open(p, 'rb').read().count(b'\r') == 0, 'CR 入侵：' + p
doc_ln, doc_b, doc_cr, doc_m = stat(DOC)
assert doc_b == 603376 and doc_ln == 3620, '订正动了排查记录？现跑 %d B / %d 行' % (doc_b, doc_ln)

RUN = NOW_FIX if MODE == 'REWROTE_CARRIER_ONLY' else NOW
with open(FIXC, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R55 落地后自查订正 + 另立 (103)-(104)；订正那三行落盘于 %s；本遍现跑于 %s，MODE=%s\n' % (NOW, RUN, MODE))
    f.write('LANDING_SEQUENCE 第一次跑到本文件的"落点计数"那条断言时崩了：期望值 (104)=3 是我猜的常数、实为 4，'
            '而崩溃点在 write_lf **之后** ⇒ 换字与三行追加已落盘、载体没写。本遍只复算 + 补载体，两只记忆文件未再写盘'
            '（幂等闸：正文里被冒充那格已换成真值 ⇒ 判为 REWROTE_CARRIER_ONLY）\n')
    f.write('SRC evidence/r55_roundtrip_2.txt 第 %d 行 %s ; 第 %d 行 %s ; RAN_END_AT=%s\n'
            % (prior_i[0] + 1, prior_raw, final_i[0] + 1, rt2_ls[final_i[0]], rt2_at))
    f.write('NAIVE_PARSER_REPRO 裸 re.search 取到 %s == PRIOR 那行的值 ⇒ 缺陷当场复现，不是事后叙述\n' % naive)
    f.write('TIME 第九次读数真值 %s（hardware/r55_backups_readme9.txt 第 1 行）vs 冒充值 %s，分位差 %d 分钟\n'
            % (rd9_now, landed_now, gap_min))
    f.write('PMEM_BODY LF %d -> %d (+3) bytes %d -> %d (+%d = 裁决 +%d x1 + 三行追加 %d) md5 %s -> %s\n'
            % (b_ln0, b_ln1, b_b0, b_b1, b_b1 - b_b0, v_delta, app_b, b_m0, b_m1))
    f.write('PMEM_INDEX LF %d -> %d (0) bytes %d -> %d (+%d = 裁决 +%d x1) md5 %s -> %s\n'
            % (i_ln0, i_ln1, i_b0, i_b1, i_b1 - i_b0, v_delta, i_m0, i_m1))
    f.write('MD5_BEFORE=不复算：崩溃那遍没落载体 ⇒ 改前 md5 无凭证，按"读数不落盘等于没跑"不编造；'
            '改前基线的字节/行数两项从订正段自述等式现读并与盘上现状闭合（%d+%d=%d、%d+3=%d）\n'
            % (b_b0, inc_b, b_b1, b_ln0, b_ln1))
    f.write('PMEM_COUNTS 全文 (103)=%d (104)=%d = 订正段自身 %d/%d + 段标题 1 处（判据由订正段推出，不用猜的常数）\n'
            % (c103, c104, APPEND.count('(103)'), APPEND.count('(104)')))
    f.write('DOC 未动 = %s B / %d 行 / CR %d / md5 %s（末版封界未破）\n' % (format(doc_b, ','), doc_ln, doc_cr, doc_m[:8]))
    f.write('MANIFEST 末版 TOTAL=%s / %s B / BOM %s（本遍只读）\n' % (man_total, man_bytes, man_bom))
    f.write('FIELD git status --porcelain = %d 行（本遍现跑，含订正批自己的新文件）\n' % len(por))
    f.write('SUPERSEDED hardware/r55_land_memory_r55.txt 第 %d 行那句假裁决**保留原样**、以本遍为准；该载体第 1 行 MODE=REWROTE_CARRIER_ONLY 仍成立\n' % prev_sync_ln)
    f.write('BACKSLASH_IN_APPENDED_TEXT=0（由末尾断言兑现）\n')
    f.write('VERDICT=MEMORY_CORRECTED\n')

print('MEMORY_CORRECTED_AT %s ; THIS_RUN %s ; MODE %s' % (NOW, RUN, MODE))
print('NAIVE=%s  TRUE=%s  PRIOR@第%d行  FINAL@第%d行' % (naive, final_val, prior_i[0] + 1, final_i[0] + 1))
print('TIME %s(冒充) -> %s(真值，来自 r55_backups_readme9.txt 第 1 行) 差 %d 分钟' % (landed_now, rd9_now, gap_min))
print('BODY LF %d->%d bytes %d->%d md5 %s->%s' % (b_ln0, b_ln1, b_b0, b_b1, b_m0, b_m1))
print('INDEX LF %d->%d bytes %d->%d md5 %s->%s' % (i_ln0, i_ln1, i_b0, i_b1, i_m0, i_m1))
print('DOC UNCHANGED %s B / %d 行 ; MANIFEST 末版 TOTAL %s' % (format(doc_b, ','), doc_ln, man_total))
print('CARRIER=hardware/r55_fix_memory_r55.txt')
