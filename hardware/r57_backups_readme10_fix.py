# R57 #187 补落遍 = 收"backups README 第十次读数"那一遍留下的半状态（正文已落 / 凭证与 FreqErr 未落）。
# 崩溃形状：那一遍的门写成 `rb.count(词) == rd_t.count(词) + 1`，而**被插的那一格自己合法地把那个词写了两次**
#   （标题一处 + 末句"本格（第十次读数）"一处）⇒ 增量应为 +2，门把**预期增量写死成字面量 1**，量的是"我猜它出现几次"，不是盘上现算。
# 本遍三件事：①现读盘核那一格已落且形状没错（结构复核 + 尺①②③④⑤复跑，因为 README 里那句"与第九次逐字同值"是它替我主张的）；
#   ②FreqErr 第七批 4 条（原 3 条 + 本遍这只门）+ 排查记录 §38.28 补 1 行登记；③落载体。
# 红线：正文不回写（README 那一格一字节不改）；不往 hardware/ht305_sync/ 落一字节；不新建备份根；不 push；零删除。
import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

_T0 = datetime.now()
AT = _T0.strftime('%Y-%m-%d %H:%M:%S')

REPO = 'C:/Users/david/Documents/all_projects/自招学习'
HDIR = os.path.join(REPO, 'hardware')
SYNC = os.path.join(HDIR, 'ht305_sync')
RDME = os.path.join(REPO, 'backups', 'README.md')
FREQ = os.path.join(REPO, 'FreqErr.md')
DOC = os.path.join(HDIR, '20260919_墨水屏点屏排查记录.md')
MAIN = os.path.join(HDIR, 'zizhao-esp32s3', 'main')
DOCS = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
SRC_MACRO = os.path.join(MAIN, 'provision_ap.c')
BIN = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
CRASH_TOOL = os.path.join(HDIR, 'r57_backups_readme10.py')
VMRUN = os.path.join(HDIR, 'vm_run.py')
CARRY = os.path.join(HDIR, 'r57_backups_readme10_fix.txt')
TOOL = os.path.abspath(__file__)
PROBE = 'evidence/SEAL_VIOLATION_PROBE13.txt'
WORD = '第十次读数'


def rd(p):
    return open(p, encoding='utf-8', newline='').read()


def rb(p):
    return open(p, 'rb').read()


def mdb(b):
    return hashlib.md5(b).hexdigest()


def sh(args):
    p = subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def money(x):
    return '{:,}'.format(int(x))


def diffrq(root):
    rc, out = sh(('diff', '-rq', os.path.join(REPO, root, 'main'), MAIN))
    assert rc in (0, 1), 'ABORT: diff 非 0/1 退出 = 命令没跑成（rc=' + str(rc) + '）'
    return len([l for l in out.split('\n') if l.strip()])


def fold_a(d, extra=()):
    files = []
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            files.append(os.path.join(root, n))
    h = hashlib.md5()
    tot = 0
    for f in sorted(files):
        b = rb(f)
        tot += len(b)
        h.update(mdb(b).encode('ascii'))
    for e in extra:
        h.update(mdb(e.encode('utf-8')).encode('ascii'))
    return len(files) + len(extra), tot, h.hexdigest()


def fold_b(d, extra=()):
    parts = []
    tot = 0
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            p = os.path.join(root, n)
            b = rb(p)
            tot += len(b)
            parts.append(os.path.relpath(p, d).replace(os.sep, '/') + ':' + mdb(b))
    for e in extra:
        parts.append(e + ':' + mdb(e.encode('utf-8')))
    return len(parts), tot, mdb('\n'.join(sorted(parts)).encode('utf-8'))


assert shutil.which('diff'), 'ABORT: PATH 里没有 diff，五把尺跑不了'
assert not os.path.exists(CARRY), 'ABORT: 本遍载体槽位非空，不覆写'
ast.parse(rd(TOOL))
for _p in (RDME, FREQ, DOC, CRASH_TOOL, SRC_MACRO, BIN, VMRUN, DOCS):
    assert os.path.exists(_p), 'ABORT: 缺件 ' + _p
assert os.path.getmtime(CRASH_TOOL) < _T0.timestamp(), 'ABORT: 崩溃遍工具不早于本遍进入时刻'

# ---------------- ①崩溃遍"死在哪一行"由盘上现读，不叙述 ----------------
CL = rd(CRASH_TOOL).split('\n')
_g = [i for i, l in enumerate(CL) if ".count('" + WORD + "')" in l and '+ 1' in l]
assert len(_g) == 1, 'ABORT: 崩溃遍那道门现读 ' + str(len(_g)) + ' 只命中 ⇒ 归因没有出处'
GLINE = _g[0] + 1
_w = [i for i, l in enumerate(CL) if l.startswith("open(RDME, 'w'")]
assert len(_w) == 1 and GLINE > _w[0], 'ABORT: 那道门不在写盘之后 ⇒ "正文已落 / 凭证未落"这句没有证据'
_w2 = [i for i, l in enumerate(CL) if l.startswith('open(FREQ, ')]
assert len(_w2) == 1 and _w2[0] > GLINE, 'ABORT: FreqErr 的写盘并不在崩溃门之后 ⇒ "FreqErr 未落"这句要重读'
assert not os.path.exists(CRASH_TOOL.replace('.py', '.txt')), 'ABORT: 崩溃遍其实落了载体 ⇒ 半状态归因不成立'

# ---------------- ②那一格已落在盘上，且形状没错（纯复核，不改写） ----------------
rd_t = rd(RDME)
assert rd_t.count('\r') == 0, 'ABORT: README 行尾混进 CR'
rd_l0 = rd_t.count('\n')
assert WORD in rd_t, 'ABORT: README 里读不到那一格 ⇒ 崩溃遍根本没写进去，本格要重落'
assert rd_t.count(WORD) == 2, 'ABORT: README 现读 ' + WORD + ' 出现 ' + str(rd_t.count(WORD)) + ' 次，不是 2 ⇒ 那一格落歪了'
_i1 = rd_t.index(WORD)
_i2 = rd_t.index(WORD, _i1 + 1)
_blk_head = rd_t[_i1 - 60:_i1 + 200]
assert '【09-25' in _blk_head, 'ABORT: 第一处该词不在 09-25 那一格标题里 ⇒ 命中的是别人的话'
assert '本格（' + WORD + '）' in rd_t[_i2 - 30:_i2 + 10], 'ABORT: 第二处该词不是末句"本格（第十次读数）"⇒ 增量算法要重算'
BLK_WORD_HITS = 2
anchor = '## 2. 命名规则'
assert rd_t.count(anchor) == 1, 'ABORT: §2 锚点不唯一'
idx = rd_t.index(anchor)
assert _i2 < idx, 'ABORT: 那一格跑到 §2 之后 ⇒ 插入点错了'
i_blk = rd_t.index('【09-25')
blk = rd_t[i_blk:idx]
BLK_LINES = blk.count('\n')
assert blk.endswith('\n') and BLK_LINES == 13, 'ABORT: 那一格现读 ' + str(BLK_LINES) + ' 只换行，不是在册的 13'
HEADS = ['## 2. 命名规则', '## 3. 当前板上镜像', '## 4. 最近一次有记录的烧录', '## 5. 有 bin / 无 bin',
         '## 5-补. R43 真机首烧批次', '## 6. 不进 ', '## 7. 归档对"计数类"口径的副作用']
RL = rd_t.split('\n')
hn = []
for h in HEADS:
    hit = [i + 1 for i, l in enumerate(RL) if l.startswith(h)]
    assert len(hit) == 1, 'ABORT: 标题 ' + h + ' 现读 ' + str(len(hit)) + ' 只 ⇒ §2 之后被动过'
    hn.append(hit[0])
assert hn == sorted(hn), 'ABORT: §2~§7 顺序不单调'
assert hn[0] == len(rd_t[:idx].split('\n')), 'ABORT: §2 行号与其前正文行数不自洽 ⇒ §1 之内被多写或少写了行'
ninth = rd_t.count('第九次读数')
assert ninth >= 1, 'ABORT: §1 里读不到第九次读数那一格（上一代的正文被动了？）'
assert rd_t.count('## 1. 两根备份根') == 1 and i_blk > rd_t.index('## 1. 两根备份根'), 'ABORT: 那一格不在 §1 之内'

# ---------------- ③"旧行未动"这把尺**不适用**，当场点名（README 被 git 忽略 ⇒ numstat 恒空） ----------------
ig_rc, ig_out = sh(('git', 'check-ignore', '-v', 'backups/README.md'))
assert ig_rc == 0, 'ABORT: README 并没有被忽略 ⇒ 那把可复算尺其实适用，得改跑它'
_ig = ig_out.rstrip('\n').split(':')
assert len(_ig) >= 3, 'ABORT: check-ignore 输出形状不是 文件:行号:规则<TAB>路径：' + repr(ig_out[:80])
IG_RULE = _ig[0] + ' 第 ' + _ig[1] + ' 行 ' + _ig[2].split('\t')[0]
assert sh(('git', 'ls-files', '--', 'backups/README.md'))[1].strip() == '', 'ABORT: 该件其实已被跟踪 ⇒ "尺不适用"要改成"尺可用"'
NS = sh(('git', '-c', 'core.quotePath=false', 'diff', '--numstat', '--', 'backups/README.md'))[1]
assert NS == '', 'ABORT: 未跟踪件读出了 diff ⇒ 本遍的"不适用"结论要重判'

# ---------------- ④README 那一格替我主张的两件事，本遍复跑 ----------------
ns = [l.split('\t') for l in sh(('git', '-c', 'core.quotePath=false', 'diff', 'HEAD', '--numstat',
                                 '--', 'hardware/zizhao-esp32s3/main'))[1].splitlines() if l.strip()]
r1_n, r1_p, r1_m = len(ns), sum(int(x[0]) for x in ns), sum(int(x[1]) for x in ns)
r1_names = sorted(os.path.basename(x[2]) for x in ns)
r2a = diffrq('backups/r43_20260922_131029')
r2b = diffrq('hardware/zizhao-esp32s3/backups/r43_20260922_131029')
r3a = diffrq('backups/r53_20260924_083929')
r3b = diffrq('hardware/zizhao-esp32s3/backups/r53_20260924_083929')
r5 = diffrq('backups/r44_sourceonly_20260923_084628')
mfiles = sorted(os.listdir(MAIN))
mbytes = sum(os.path.getsize(os.path.join(MAIN, f)) for f in mfiles if os.path.isfile(os.path.join(MAIN, f)))
assert (r1_n, r1_p, r1_m) == (1, 210, 14) and r1_names == ['provision_ap.c'], 'ABORT: 尺① 与第九次不同值（现 %d/%d/%d %s）⇒ README 那句要订正' % (r1_n, r1_p, r1_m, r1_names)
assert (r2a, r2b, r3a, r3b, r5) == (5, 5, 0, 0, 3), 'ABORT: 尺②③⑤ 与第九次不同值（现 %d/%d/%d/%d/%d）' % (r2a, r2b, r3a, r3b, r5)
assert (len(mfiles), mbytes) == (30, 641444), 'ABORT: 尺④ 与第九次不同值（现 %d 只 / %d B）' % (len(mfiles), mbytes)
bin_md5, bin_bytes = mdb(rb(BIN)), os.path.getsize(BIN)
arc_md5 = mdb(rb(os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin')))
assert bin_md5.startswith('fb32168a') and arc_md5.startswith('4842a3a0')

# ---------------- ⑤现场态 + docs 读数（README ⑦⑨ 两格引用的就是这些） ----------------
rev = sh(('git', 'rev-list', '--count', 'origin/main..HEAD'))[1].strip()
st = [l for l in sh(('git', '-c', 'core.quotePath=false', 'status', '--porcelain'))[1].splitlines() if l.strip()]
st_m = len([l for l in st if l.startswith(' M')])
st_q = len([l for l in st if l.startswith('??')])
ports = sorted(set(re.findall(r'(?m)^(COM\d+)', sh((sys.executable, '-m', 'serial.tools.list_ports'))[1])))
has14 = 'COM14' in ports
dfiles = sorted(os.listdir(DOCS))
dnote = rd(os.path.join(DOCS, 'SNAPSHOT_NOTE.txt'))
dsrc = len([l for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
dnew = len([l for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)])
dsnap_at = re.search(r'刷新时刻 (.+?)。', dnote).group(1)
dcred = re.search(r'）：(\d+) 只源全扫，命中数必须为 0 才动手；本次 HITS=(\d+)', dnote)
assert dcred and int(dcred.group(1)) == dsrc and dcred.group(2) == '0'
assert len(dfiles) == dsrc + 1 and dnew == 3, 'ABORT: docs 现读 %d 只 / 表格 %d 行 / NEW %d 与 README ⑦ 那句不同值' % (len(dfiles), dsrc, dnew)
_rows = [l.split('\t')[0] for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)]
assert len(_rows) == 3
R59_AT = re.search(r'【09-25 \*\*([0-9:]{8})', blk).group(1)
ST_LINE = [i + 1 for i, l in enumerate(RL) if l.startswith('【09-25')][0]
assert ST_LINE < hn[0], 'ABORT: 那一格起点行号不在 §2 之前'

# ---------------- ⑥明文凭据闸 ----------------
_m = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC_MACRO))
assert _m, 'ABORT: 读不到 PROV_PASS 宏'
secret = _m.group(1).encode('utf-8')

# ---------------- ⑦SEAL 双尺：写盘前读数 + 阳性对照（只造在内存） ----------------
S0 = fold_a(SYNC)
T0 = fold_b(SYNC)
assert S0[:2] == T0[:2], 'ABORT: 两把尺公共量互核失败'
PA, PB = fold_a(SYNC, (PROBE,)), fold_b(SYNC, (PROBE,))
assert PA[2] != S0[2] and PB[2] != T0[2] and not os.path.exists(os.path.join(SYNC, PROBE))
FIRED = 2

# ================= 正文：FreqErr 第七批 4 条（原 3 条 + 本遍这只门） =================
T7 = '## 2026-09-25（R57 第七批：补落遍自己带进来的四只）新增 {N} 条（根族：**判据的名单取自单一出处** / **裁决句里预写字面量** / **Edit 把下一行粘到本行尾** / **门的预期增量写成字面量**）'
FREQ_ROWS = [
    T7,
    '',
    '[错误类型] **归属/差集类判据的名单只取"上一遍载体"一个出处** ⇒ 更早各遍在册的件被算成"未归格"，一条本来成立的反证被自己的口径点红'
    '（R57 part B 补落遍实测：代落件池 8 只里 3 只"未归格"，ABORT 文案还写着"崩溃遍跑到过 vm_run？归因要重读"，而真相是那 3 只由更早两遍的在册载体点名）',
    '→ 症状：门红了，读起来像"上一批留下脏东西"，于是去查崩溃遍有没有跑到某一步；实际池子里一只都没漏，漏的是**取名单的范围**。',
    '→ 为什么它危险：①它把**口径缺口**伪装成**事实违例**——红得很有说服力，因为"未归格只数"确实是现算的；'
    '②它的假红排在写盘之前，所以只浪费一轮排查 + 制造一次假指控，而它建议的下一步动作（"重读归因"）本身又是对已落文档的一次改写；'
    '③同一族在本仓库已犯两次（R50 第五次提交轮的 `unlisted[:10]` 截断、R46 的"门只打印不置退出码"），本条的新形态是**出处单一**而不是名单被截。',
    '→ 正确做法：①写归属/差集门之前先问**这个名字被谁登记过**——登记是跨遍的，出处就要跨遍取（该遍改为读今日全部在册载体取并集，8/8 归格）；'
    '②判据的**真正主张**要单独写成一条关系式（那一遍的主张是"池子最晚那只 == 上一遍在册最晚 ⇒ 崩溃遍没产代落件"），别把"全部在册"这种大口径当成主张本身；'
    '③红了先复算**门自己的范围**再去动被检物（该遍就是这么抓回来的：被检池一只没动）。',
    '[错误类型] **裁决句里预写字面量**（R57 part B 崩溃遍实测：载体 APPEND 行写了"现跑 ls-files 命中 = False / False 由本遍现算："，后面才接上现算的插值）'
    '⇒ 一句话里同时有**猜出来的**和**量出来的**两个真值，读者按哪个读都对不上另一个',
    '→ 症状：文字先给结论、括号里再给读数；当读数与预写不符时，那句话要么假绿要么假红，而脚本不会红（预写的那两个 False 只是字符，不参与求值）。',
    '→ 为什么它危险：这是"完成态数字不许预写"那条老规矩的**布尔亚种**——数字被规矩盯着，布尔字面量没人查；'
    '而它偏偏出现在"这把尺不适用"这种**降级声明**里，降级声明一旦说反，下一遍就会拿它当"其实适用过"的依据。',
    '→ 正确做法：①裁决句里的每个真值都必须是**同一个表达式的插值**，不许出现裸 True/False；'
    '②声明"某把尺不适用"必须配一道 assert 它真的不适用（该遍补了 `assert DEV_UNTRACKED and UPD_UNTRACKED`），否则那句话没有执行者；'
    '③同族自查：句子里有没有**不参与判定的成分**（该遍另一只自纠的恒真式 `and False is False or True` 同根），落笔时逐句问一遍。',
    '[错误类型] **Edit 的 new_string 少带一个换行 ⇒ 把下一行粘到本行尾**（造结构缺陷而不是内容缺陷）；'
    '本遍另实测到它的**近亲**：一次以整行为锚点的 Edit 把**上一行尾部那只引号**吃掉，`ast.parse` 才抓到（R57 落地器第 24 行，2026-09-25 实测）',
    '→ 症状：文件"看起来还是那些行"，但行内容变了；被吃掉的是一个引号或一个换行这类**不承载语义字符的边界字符**，'
    'grep 关键词、肉眼看 diff 都容易过去，只有解释器/解析器会红。',
    '→ 为什么它危险：用户记忆里那七类 Write/Edit 自伤讲的都是"内容被改写"，本条是**结构被改写且默认无人检查**——'
    '尤其当 old_string 是从 Read 输出复制来的，尾部换行在复制时最容易丢，而 Edit 不会为"少一个换行/少一个引号"报任何警。',
    '→ 正确做法：①以**整行**为单位做 Edit：old 与 new 要么都以换行收尾，要么都不带；只改一行内容时把该行**上下各一行**也放进锚点；'
    '②任何对 `.py` 的编辑之后立刻 `ast.parse` 复跑（本遍两次都是它抓回来的），别依赖"我能看出来"；'
    '③同族 = 用户记忆"工具映射与环境事实"里的 Edit 七类自伤（本条登记为第八类，并把"吃引号"并进来）。',
    '[错误类型] **门的"预期增量"写成字面量而不是现算**（R57 第十次读数遍实测：门 `rb.count(词) == rd_t.count(词) + 1` 假设那一格只把'
    '自己的名字说一次，而被插正文里"本格（' + WORD + '）"是第二处合法出现 ⇒ 真增量 = **' + str(BLK_WORD_HITS) + '**，门恒红）',
    '→ 症状：README 那一格**已经正确落盘**（前缀等式、行号增量、§2 唯一性三道门都在它之前跑过了），红的是最后那道"自指计数门"，'
    '于是现场变成"正文已落 / FreqErr 未落 / 载体未落"的半状态——同族第 3 次：**裁决类门排在 open() 之后**，而且这次连"门本身算错"都叠上去了。',
    '→ 为什么它危险：①"预期增量"是这段脚本里**唯一没被任何现跑数据支撑的常数**，别的数字错了会红在别处，这个错了只能靠运气；'
    '②它伪装成"我在核自指"，读起来比不核更让人放心；③它排在写盘之后 ⇒ 红的时候**已经改过盘**，本遍必须按半状态收口，多花一整遍。',
    '→ 正确做法：①增量类判据的**期望值必须由同一把尺现算**（本遍写成 `== 被插块里该词出现次数`，并把该次数落进载体）；'
    '②能在写盘前判的一律前置（本遍把 FreqErr 的行增量等式全部挪到 `open()` 之前）；'
    '③"这一格出现几次"这种**自指计数**要么不算、要么给出现算出处，不许拿"我记得它只出现一次"当判据；'
    '④半状态不回写正文，只由补落遍**追加登记 + 新落载体**（本遍就是这么收的），并把崩溃遍那道的行号、被插块的真实行数、被吃掉的常数一起落盘。',
]
N_NEW = len([l for l in FREQ_ROWS if l.startswith('[错误类型]')])
assert N_NEW == 4, 'ABORT: 本批正文条数现算 ' + str(N_NEW) + ' 只，不是 4'
FREQ_ROWS[0] = T7.replace('{N}', str(N_NEW))
FRQ_T = rd(FREQ)
DOC_T = rd(DOC)
assert FRQ_T.count('\n') == FRQ_T.count('\r\n') and FRQ_T.endswith('\r\n'), 'ABORT: FreqErr 行尾不是纯 CRLF'
assert DOC_T.endswith('\r\n') and DOC_T.count('\n') == DOC_T.count('\r\n')
FL0 = FRQ_T.split('\r\n')
f_e0 = len([l for l in FL0 if l.startswith('[错误类型]')])
f_l0 = len(FL0) - 1
DOCL0 = len(DOC_T.split('\r\n')) - 1

DOC_ROW = ('- **登记（§38.28 补落遍｜' + AT + '）**："backups/README 第十次读数"那一遍（工具 `hardware/r57_backups_readme10.py`，'
           '其 mtime 按秒对齐 = ' + datetime.fromtimestamp(os.path.getmtime(CRASH_TOOL)).strftime('%Y-%m-%d %H:%M:%S') + '）把**正文落了盘**、'
           '死在自己最后一道上：`' + WORD + '` 的**自指计数门**把预期增量写成字面量 1，而那一格合法地把它说 **' + str(BLK_WORD_HITS) + '** 次'
           '（标题 + 末句"本格（' + WORD + '）"）。现读该遍工具：那道门在第 **' + str(GLINE) + '** 行，README 的写在第 **' + str(_w[0] + 1) + '** 行，'
           'FreqErr 的写在第 **' + str(_w2[0] + 1) + '** 行（崩溃点之前）⇒ 形状 = **正文已落 / FreqErr 未落 / 载体未落**，'
           '且崩溃遍自己的三道**有效**门（前缀等式、§2 唯一、行数增量 = 13）都排在它之前并且跑过了（控制流证据，本遍按规矩不拿它当读数）。'
           '本遍**不回写那一格**，只做两件事：①现读复核它落在原位（§1 内、§2 之前第 **' + str(ST_LINE) + '** 行起、块 **' + str(BLK_LINES) + '** 只换行、'
           '§2~§7 六只标题各 1 只且行号单调 ' + str(hn[0]) + '/' + str(hn[1]) + '/' + str(hn[2]) + '/' + str(hn[3]) + '/' + str(hn[4]) + '/' + str(hn[5]) + '/' + str(hn[6]) + '、'
           '全文 CR = 0、`第九次读数` 那一格仍在），并把它替我主张的两件事复跑：五把尺逐字 = **' + str(r1_n) + '**/**+' + str(r1_p) + '**/**−' + str(r1_m) + '** 与 '
           '**' + str(r2a) + '/' + str(r2b) + '/' + str(r3a) + '/' + str(r3b) + '/' + str(r5) + '** 与 **' + str(len(mfiles)) + ' 只 / ' + money(mbytes) + ' B**（三道 assert 全过 ⇒ "不新建根"那句成立）；'
           '②FreqErr 第七批 **' + str(N_NEW) + '** 条（原三条 + 本遍这只门）与本行、载体 `hardware/r57_backups_readme10_fix.txt`。'
           '⚠ 一处"这把尺不适用"当场点名：README 被 `.gitignore:` 规则 **' + IG_RULE + '** 忽略 ⇒ `git diff --numstat` 对它是**空串**（本遍现跑 rc 空 = 已核），'
           '所以"旧行未动"在本件上**只有控制流证据 + 结构复核**，没有字节级复算尺——这与项目记忆 (94) 同案，不是本遍偷懒。')

_payloads = DOC_ROW + ''.join(FREQ_ROWS)
for _s in ('%s', '%d', '@@', '{N}', 'PLACEHOLDER'):
    assert _s not in _payloads, 'ABORT: 本遍新落正文含未替换哨兵 ' + _s
assert secret not in _payloads.encode('utf-8'), 'ABORT: 明文进了正文'

LEDGER = ('>'
          ' **【' + AT + ' 落地｜R57 第七批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（本脚本进入时刻 ' + AT + '，_T0 取在任何产证动作之前）：'
          '全文 `^[错误类型]` 条数 = **' + str(f_e0) + '**、行数 = **' + str(f_l0) + '**、字节 = **' +
          format(len(FRQ_T.encode('utf-8')), ',') + '**；本批正文 = **' + str(N_NEW) + '** 条 / **' + str(len(FREQ_ROWS)) + '** 行'
          '（**不含**本台账行、**不含**标题上方那只 glue 空行，两者另计）；**落盘后的终态由本遍载体现数**（完成态数字不在本行预写）。'
          '同遍排查记录改前 **' + str(DOCL0) + '** 行 -> 本遍真追加 1 行登记 + 1 只 glue 空行；'
          'backups/README.md 本遍**一字节未改**（崩溃遍那一格原样保留，见 `hardware/20260919_墨水屏点屏排查记录.md` 末行登记）。')

GLUE_DOC = ''
TAIL = '\r\n' + '\r\n'.join(FREQ_ROWS) + '\r\n' + LEDGER + '\r\n'
new_frq = FRQ_T + TAIL
f_l1 = len(new_frq.split('\r\n')) - 1
f_e1 = len([l for l in new_frq.split('\r\n') if l.startswith('[错误类型]')])
assert f_e1 == f_e0 + N_NEW, 'ABORT: 写盘前条数等式不成立'
assert f_l1 - f_l0 == len(FREQ_ROWS) + 2, 'ABORT: 写盘前行增量现算 ' + str(f_l1 - f_l0) + ' != 正文 ' + str(len(FREQ_ROWS)) + ' + glue + 台账'
DOC_NEW = DOC_T + GLUE_DOC + DOC_ROW + '\r\n'
assert DOC_NEW.startswith(DOC_T) and new_frq.startswith(FRQ_T), 'ABORT: 前缀等式不成立，本遍不是纯追加'
for _ln in (TAIL + DOC_ROW).split('\r\n'):
    assert secret not in _ln.encode('utf-8'), 'ABORT: 明文写进盘'
    assert '{' not in _ln and '}' not in _ln, 'ABORT: 未求值占位：' + _ln[:60]
    assert chr(92) not in _ln, 'ABORT: 本遍新落正文含反斜杠（作用域 = 本遍正文，不是整只文件）：' + _ln[:60]

open(FREQ, 'w', encoding='utf-8', newline='').write(new_frq)
open(DOC, 'w', encoding='utf-8', newline='').write(DOC_NEW)
fb, db = rd(FREQ), rd(DOC)
assert fb == new_frq and db == DOC_NEW, 'ABORT: 回读与内存串不等'
assert fb.count('\n') == fb.count('\r\n') and db.count('\n') == db.count('\r\n'), 'ABORT: 写后不再是纯 CRLF'
N_TOTAL = len([l for l in fb.split('\r\n') if l.startswith('[错误类型]')])
L_TOTAL = len(fb.split('\r\n')) - 1
DOC_LN = len(db.split('\r\n')) - 1
assert N_TOTAL == f_e1 and L_TOTAL == f_l1, 'ABORT: 写后现数与写前算式不等'
assert DOC_LN == DOCL0 + 1, 'ABORT: 排查记录现算加 ' + str(DOC_LN - DOCL0) + ' 行，不是 1 行'
S1, T1 = fold_a(SYNC), fold_b(SYNC)
assert S1 == S0 and T1 == T0, 'ABORT: 本遍动过 hardware/ht305_sync/'

_vm = subprocess.run((sys.executable, VMRUN), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_vm_out = _vm.stdout.decode('utf-8', 'replace')
_mc = re.search(r'VM_CARRIER=(\S+)', _vm_out)
assert _vm.returncode == 0 and _mc, 'ABORT: 内层复核器本遍没跑绿 rc=' + str(_vm.returncode)
VM_C = _mc.group(1).replace('\\', '/').split('/')[-1]
INNER = [l for l in rd(os.path.join(HDIR, VM_C)).split('\n') if l.startswith('INNER_ROWS=')][0]

rd_after = rd(RDME)
assert rd_after == rd_t, 'ABORT: 本遍改到了 README'

with open(CARRY, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R57 第十次读数 补落遍  MODE=README10-FIX  本遍现跑于 ' + AT + '（进入时刻 _T0 取在任何产证动作之前）\n')
    f.write('CRASH 崩溃遍现读：工具 hardware/' + os.path.basename(CRASH_TOOL) + ' mtime=' +
            datetime.fromtimestamp(os.path.getmtime(CRASH_TOOL)).strftime('%Y-%m-%d %H:%M:%S') +
            '，那一格自登记的进入时刻 = ' + R59_AT + '（早于本遍 ' + AT[11:] + '）；那道自指计数门在第 ' + str(GLINE) + ' 行，README 的写在第 ' + str(_w[0] + 1) + ' 行、FreqErr 的写在第 ' + str(_w2[0] + 1) +
            ' 行 ⇒ 崩溃时**正文已落 / FreqErr 未落 / 载体未落**；门的错在**预期增量写了字面量 1**，而那一格把 ' + WORD + ' 合法说了 ' + str(BLK_WORD_HITS) + ' 次（标题 + 末句"本格（…）"）\n')
    f.write('BLOCK 那一格盘上现读：起于 §1 第 ' + str(ST_LINE) + ' 行、止于 §2 之前、块内 ' + str(BLK_LINES) + ' 只换行、全文 ' + WORD + ' 出现 ' +
            str(rd_t.count(WORD)) + ' 次、`第九次读数` 在册 ' + str(ninth) + ' 次、CR=' + str(rd_t.count(chr(13))) + '\n')
    f.write('STRUCT §2~§7 七只标题现读行号 = ' + ' / '.join(str(x) for x in hn) +
            '（各 1 只、单调，§2 那一只与"其前正文行数"自洽 = True）⇒ 那一格起于第 ' + str(ST_LINE) + ' 行、止于 §2 之前，块内 ' + str(BLK_LINES) +
            ' 只换行；本遍一字节未改（写后逐字节回读等值 = ' + str(rd_after == rd_t) + '；全文件行数 写前 ' + str(rd_l0) + ' = 写后 ' + str(rd_after.count('\n')) + '）\n')
    f.write('APPEND 尺不适用（点名，不是偷懒）：`git check-ignore -v backups/README.md` 现跑命中规则 ' + IG_RULE +
            ' ⇒ 该件未跟踪，`git diff --numstat -- backups/README.md` 现跑输出为空串（长度 ' + str(len(NS)) + '）⇒ "旧行未动"只有控制流证据 + 结构复核（标题序 + 前缀等式 + 行数增量）\n')
    f.write('RULER 复跑（README 那一格替我主张的）：①=' + str(r1_n) + '只/+ ' + str(r1_p) + '/−' + str(r1_m) + ' 名单=' + ','.join(r1_names) +
            '  ②=' + str(r2a) + '/' + str(r2b) + '  ③=' + str(r3a) + '/' + str(r3b) + '  ④=' + str(len(mfiles)) + '只/' + money(mbytes) +
            ' B  ⑤=' + str(r5) + ' ⇒ 三道 assert 与第九次在册值逐字同值，判据成立 = True\n')
    f.write('FIELD rev-list=' + rev + '  porcelain=' + str(len(st)) + ' 行（' + str(st_m) + ' M + ' + str(st_q) + ' ??）  ports=' +
            ', '.join(ports) + '  COM14 在位=' + str(has14) + '  AT=' + AT[11:] + '\n')
    f.write('DOCS 第十遍 盘上现读 = 目录 ' + str(len(dfiles)) + ' 只 / 表格 ' + str(dsrc) + ' 行 / NEW_ONES ' + str(dnew) + '（' +
            ' / '.join(_rows) + '）@' + dsnap_at + ' 凭据闸 OF=' + dcred.group(1) + ' HITS=' + dcred.group(2) + '\n')
    f.write('FREQ 错误类型 ' + str(f_e0) + ' -> ' + str(N_TOTAL) + ' 条 / 行数 ' + str(f_l0) + ' -> ' + str(L_TOTAL) +
            '（第七批 ' + str(N_NEW) + ' 条 / ' + str(len(FREQ_ROWS)) + ' 行 + glue 1 + 台账 1；写盘前算式 = 写盘后现数）\n')
    f.write('DOC 排查记录 ' + str(DOCL0) + ' -> ' + str(DOC_LN) + ' 行（本遍真加 1 行登记 = §38.28 补落遍）；改前 md5 ' + mdb(DOC_T.encode('utf-8'))[:12] +
            ' / 改后 ' + mdb(db.encode('utf-8'))[:12] + '\n')
    f.write('VM 本遍现跑内层复核器：rc=' + str(_vm.returncode) + ' / ' + INNER + ' / 代落件 = hardware/' + VM_C + '\n')
    f.write('SEAL 两条同尺比较 + 一条公共量互核：FOLD-A 写前 ' + S0[2] + ' == 写后 ' + S1[2] + ' = ' + str(S0 == S1) +
            '；FOLD-B 写前 ' + T0[2] + ' == 写后 ' + T1[2] + ' = ' + str(T0 == T1) + '；公共量互核 = ' + str(S0[:2] == T0[:2]) +
            '（' + str(S0[0]) + ' 只 / ' + money(S0[1]) + ' B）；内存假名 ' + PROBE + ' 使两把尺双红 = ' + str(FIRED) +
            '（盘上无那只 = True）⇒ gen 24 仍是末版\n')
    f.write('WITNESS 本遍现读 md5（前 12 位）：本遍工具 ' + mdb(rb(TOOL))[:12] + ' / 崩溃遍工具 ' + mdb(rb(CRASH_TOOL))[:12] +
            ' / backups README ' + mdb(rd(RDME).encode('utf-8'))[:12] + ' / FreqErr(改前) ' + mdb(FRQ_T.encode('utf-8'))[:12] +
            ' / 待烧 bin ' + bin_md5[:12] + '（' + money(bin_bytes) + ' B）/ 板上历史格 ' + arc_md5[:12] + '\n')
    f.write('NOTDONE 本遍没做（点名）：没回写崩溃遍那一格正文 / 没新建备份根 / 没重建重烧 / 没改 main/ 源码 / 没往 hardware/ht305_sync/ 落一字节 / '
            '没新建清单代次 / 没跑 git status --porcelain -uall / 没刷新 docs 快照（快照非终态：本遍之后 FreqErr 与排查记录又变了，口径内，不重跑洗绿）/ '
            '没 push、没 amend / 零删除（含 %TEMP% 里各臂原件）/ F 臂判据未预写（本遍跑它时它还在窗口里）/ 屏亮肉眼确认仍 0 次 ⇒ 不播提示音\n')
    f.write('GATE-COUNT 本载体行数（所有行追加完之后才求值）= ' + str(len(open(CARRY, encoding='utf-8').read().split('\n')) - 1) + ' 行\n')
    f.write('VERDICT=README10_FIX_DONE\n')

print('CRASH gate line=%d  README-write@%d  FREQ-write@%d  block-hits=%d' % (GLINE, _w[0] + 1, _w2[0] + 1, BLK_WORD_HITS))
print('BLOCK lines=%d  start=%d  heads=%s  CR=%d' % (BLK_LINES, ST_LINE, ','.join(map(str, hn)), rd_t.count(chr(13))))
print('RULER 1=%d只/+%d/-%d  2=%d/%d  3=%d/%d  4=%d只/%s B  5=%d' % (r1_n, r1_p, r1_m, r2a, r2b, r3a, r3b, len(mfiles), money(mbytes), r5))
print('FIELD rev=%s porcelain=%d ports=%s COM14=%s' % (rev, len(st), ','.join(ports), has14))
print('DOCS %d 只 / %d 行 / NEW %d @%s' % (len(dfiles), dsrc, dnew, dsnap_at))
print('FREQ %d -> %d 条 / %d -> %d 行    DOC %d -> %d 行' % (f_e0, N_TOTAL, f_l0, L_TOTAL, DOCL0, DOC_LN))
print('VM rc=%d %s' % (_vm.returncode, VM_C))
print('SEAL %s == %s  /  %s == %s' % (S0[2][:8], S1[2][:8], T0[2][:8], T1[2][:8]))
print('CARRY = hardware/%s (%d B)' % (os.path.basename(CARRY), os.path.getsize(CARRY)))
print('VERDICT=README10_FIX_DONE')
