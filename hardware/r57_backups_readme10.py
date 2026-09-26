# R57 收口 #187 后半：backups/README.md §1 **第十次读数** + FreqErr 第七批 3 条 + 本格载体。
# 为什么写在 hardware/ 而不是 hardware/ht305_sync/scripts/：末版 gen 24 之后往归档里落任何一只 = 亲手把末版降级。
# 口径：本格每个数都由本脚本现跑现读；"与第九次同值"由代码断言判，不由话术判。
# 本遍不新建备份根的前提 = 五把尺逐字与第九次同值（下面 RULER-SAME 那三道 assert 就是它的执行者）。
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

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
FREQ = os.path.join(REPO, 'FreqErr.md')
RDME = os.path.join(REPO, 'backups', 'README.md')
MAIN = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main')
DOCS = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
BUILD_BIN = r'C:/esp/zproj/build/zizhao_esp32s3.bin'
SRC_MACRO = os.path.join(MAIN, 'provision_ap.c')
VM_LAST = os.path.join(REPO, 'hardware', 'vm_run_20260925_152318.txt')
CARRY = os.path.join(REPO, 'hardware', 'r57_backups_readme10.txt')
AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
assert shutil.which('diff'), 'ABORT: PATH 里没有 diff，五把尺跑不了'
assert not os.path.exists(CARRY), 'ABORT: 本格载体槽位非空，不覆写'
import ast  # 落地三步序第 1 步：先体检自己这一只（本批第八类工具自伤 = Edit 丢尾部换行，只有 parse 看得见）
ast.parse(open(os.path.abspath(__file__), encoding='utf-8').read())


def sh(args):
    p = subprocess.run(args, cwd=REPO, capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def diffrq(root):
    rc, out = sh(('diff', '-rq', os.path.join(REPO, root, 'main'), MAIN))
    assert rc in (0, 1), 'ABORT: diff 非 0/1 退出 = 命令没跑成（rc=%d）' % rc
    return len([l for l in out.split('\n') if l.strip()]), rc


def git(*a):
    rc, out = sh(('git',) + a)
    assert rc == 0, 'ABORT: git 失败 ' + ' '.join(a)
    return out


def money(x):
    return '{:,}'.format(int(x))


def md5_of(p):
    assert os.path.isfile(p), 'ABORT: 该读 md5 的文件不存在 ' + p
    b = open(p, 'rb').read()
    return hashlib.md5(b).hexdigest(), len(b)


# ---------------- 五把尺（现跑） ----------------
ns = [l.split('\t') for l in git('-c', 'core.quotePath=false', 'diff', 'HEAD', '--numstat',
                                 '--', 'hardware/zizhao-esp32s3/main').splitlines() if l.strip()]
r1_n, r1_p, r1_m = len(ns), sum(int(x[0]) for x in ns), sum(int(x[1]) for x in ns)
r1_names = sorted(os.path.basename(x[2]) for x in ns)
r2a = diffrq('backups/r43_20260922_131029')[0]
r2b = diffrq('hardware/zizhao-esp32s3/backups/r43_20260922_131029')[0]
r3a = diffrq('backups/r53_20260924_083929')[0]
r3b = diffrq('hardware/zizhao-esp32s3/backups/r53_20260924_083929')[0]
r5 = diffrq('backups/r44_sourceonly_20260923_084628')[0]
mfiles = sorted(os.listdir(MAIN))
mbytes = sum(os.path.getsize(os.path.join(MAIN, f)) for f in mfiles if os.path.isfile(os.path.join(MAIN, f)))
rev = git('rev-list', '--count', 'origin/main..HEAD').strip()
st = [l for l in git('-c', 'core.quotePath=false', 'status', '--porcelain').splitlines() if l.strip()]
st_m = len([l for l in st if l.startswith(' M')])
st_q = len([l for l in st if l.startswith('??')])
bin_md5, bin_bytes = md5_of(BUILD_BIN)
arc_md5, arc_bytes = md5_of(os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin'))
r53_md5, r53_bytes = md5_of(os.path.join(REPO, 'backups', 'r53_20260924_083929', 'zizhao_esp32s3.bin'))
ports = sorted(set(re.findall(r'(?m)^(COM\d+)',
               subprocess.run((sys.executable, '-m', 'serial.tools.list_ports'), cwd=REPO,
                              capture_output=True).stdout.decode('utf-8', 'replace'))))
dfiles = sorted(os.listdir(DOCS))
dnote = open(os.path.join(DOCS, 'SNAPSHOT_NOTE.txt'), encoding='utf-8').read()
dsrc = len([l for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
dsnap_at = re.search(r'刷新时刻 (.+?)。', dnote).group(1)
dnew = len([l for l in dnote.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)])
dcred = re.search(r'）：(\d+) 只源全扫，命中数必须为 0 才动手；本次 HITS=(\d+)', dnote)
assert dcred and int(dcred.group(1)) == dsrc and dcred.group(2) == '0', 'ABORT: NOTE 里那句凭据闸读数与表格行数不同代'
assert len(dfiles) == dsrc + 1, 'ABORT: docs 目录只数 != 表格行数 + 1（NOTE 之外还有别的？）'
pyc_n = sum(1 for r, d, fs in os.walk(os.path.join(REPO, 'backups'))
            for n in d + fs if n == '__pycache__' or n.endswith('.pyc'))
_vm = open(VM_LAST, encoding='utf-8').read()
vm_row = [l for l in _vm.split('\n') if l.startswith('INNER_ROWS=')][0]

# ---------------- "与第九次同值"由代码判（这三道 assert 就是"不新建备份根"那句的执行者） ----------------
assert (r1_n, r1_p, r1_m) == (1, 210, 14) and r1_names == ['provision_ap.c'], \
    'ABORT: 尺① 与第九次不同值（现 %d/%d/%d %s）⇒ 有代码进了工作树，"不新建根"要重判' % (r1_n, r1_p, r1_m, r1_names)
assert (r2a, r2b, r3a, r3b, r5) == (5, 5, 0, 0, 3), 'ABORT: 尺②③⑤ 与第九次不同值（现 %d/%d/%d/%d/%d）' % (r2a, r2b, r3a, r3b, r5)
assert (len(mfiles), mbytes) == (30, 641444), 'ABORT: 尺④ 与第九次不同值（现 %d 只 / %d B）' % (len(mfiles), mbytes)
assert bin_md5.startswith('fb32168a') and arc_md5.startswith('4842a3a0') and r53_md5 == bin_md5

# ---------------- README §1 第十次读数（纯 LF 追加式插入） ----------------
rd_t = open(RDME, encoding='utf-8', newline='').read()
assert rd_t.count('\r') == 0 and rd_t.count('\n') > 100, 'ABORT: backups/README.md 行尾或体量异常'
assert '第十次读数' not in rd_t, 'ABORT: §1 已经有第十次读数那一格 ⇒ 本脚本不可重跑（会插第二格）'
anchor = '## 2. 命名规则'
assert rd_t.count(anchor) == 1, 'ABORT: §2 锚点不唯一'
BLOCK = (
    '【09-25 **' + AT[11:] + ' 第十次读数**｜**R53→R57 五批零代码进工作树 ⇒ 五把尺逐字与第九次同值（本遍由三道 assert 现判，不靠话术）⇒ 本轮仍不新建备份根**；'
    '本遍另兑现三件事：docs 第十遍快照的读数、F 臂那格串口现场态换代（COM14 回来了）、以及把"未跟踪只数"这把我自己用过无数次的尺量法点名】\n'
    '① **相对 `HEAD`**：`git -c core.quotePath=false diff HEAD --numstat -- hardware/zizhao-esp32s3/main` ⇒ **{r1_n} 只 / +{r1_p} / −{r1_m}**，'
    '名单现读 = **{r1_names}** 那只（自带 1 处明文、每轮被点名 DROP）⇒ 与第九次逐字同值。\n'
    '② **相对 r43 那两根**：`diff -rq` 根 A / 根 B = **{r2a} / {r2b} 行**（与第九次同值 ⇒ 两根仍是 09-22 20:55 那一烧的历史输入，不刷新）。\n'
    '③ **相对 r53 那两根**：同一命令 = **{r3a} / {r3b} 行** ⇒ 两根各 0 行 = 当前待烧镜像的构建输入仍只有 r53 这一根（**第三次独立复跑**，判据与第八、九次同源）。\n'
    '④ **工作树 `main/` 体量**：**{mfiles} 只 / {mbytes} B**（python 现读，与第六、八、九次逐字同值 ⇒ "零代码进工作树"就是这一格量的）。\n'
    '⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main hardware/zizhao-esp32s3/main` ⇒ 仍 **{r5} 行 differ**（不顺手修，动历史镜像等于造第二把尺）。\n'
    '⑥ **配套读数**：`git rev-list --count origin/main..HEAD` 现跑 = **{rev}**（未 push）；`status --porcelain` = **{st} 行**（{st_m} 只 M + {st_q} 只 ??）——'
    '⚠ 这里点名一把尺的量法：`--porcelain` 对**未跟踪目录**默认按目录折叠成一行，而本仓库现在 ?? 只数远大于历代登记（R54 那格 36、R53 那格 43）⇒ '
    '这一格只记"现跑行数"，**不许**跨代换算成"新增了几只文件"；要只数得另跑 `git status --porcelain -uall`，本遍没跑、就不引用它的数。\n'
    '⑦ **docs/ 第十遍快照**（本遍之前刚跑，`hardware/refresh_docs_snapshot_r57.py` = 派生自 `hardware/refresh_docs_snapshot_r55.py`）：'
    '目录现读 **{dfiles} 只** = 表格 **{dsrc} 行** + `SNAPSHOT_NOTE.txt`（自核等式 {dsrc}+1={dfiles} 成立）、`SNAPSHOT_AT {dsnap_at}`、'
    '凭据闸 **{dgate}**、`NEW_ONES {dnew}`（本代新入库的 3 只 = R56/R57 那份 updates + `dev_log/20260925.md` + E 臂判据载体）。'
    'python 走一遍 `backups/` 数 `__pycache__` 与 `.pyc` = **{pyc_n}**。\n'
    '⑧ **指纹三处现算**：构建目录 **{bin_md5}**（**md5，32 位 hex** / {bin_bytes} B）= 根 A r53 那只（**归档 == 待烧** 成立）≠ 根 A r43 与板上那只 **{arc_md5}** / {arc_bytes} B；'
    '"待烧 = 板上"这一格自 R53 起断、R56 首烧后由 E 臂身份等式接回（boot ELF 前 16 位 == bin[176:184]，见 `hardware/20260925_R57_E臂判据摘录_v2.txt` 第 6 行）。\n'
    '⑨ **现场态换代（本格第一次记 COM14 在位）**：`python -m serial.tools.list_ports` 现跑 = `{ports}` ⇒ **COM14 在位 = {has14}**。'
    'R53~R56 那一串"COM14 缺席"到此被覆盖成新读数（不推翻它们各自那一遍）；本遍同时有一臂串口动作在跑（F 臂 = 复位起抓跨 900s 深睡边界），'
    '它的判据读数落 `hardware/20260925_R57_F臂判据摘录.txt`，**本格不预写它的数**。\n'
    '⑩ **末版封界照旧**：本遍未往 `hardware/ht305_sync/` 落一字节、未新建清单代次（gen 24 仍是末版）；'
    '本批最近一次内层复核 = `hardware/vm_run_20260925_152318.txt`：{vm_row}。\n'
    '⇒ 判定不变：**不重建、不重烧、不新建根**。本轮真正落地的 = docs 第十遍 + 本格（第十次读数）+ FreqErr 第七批；'
    '**未 `git push`**、未 amend、**零删除**（含 `%TEMP%` 里各臂抓回原件，本仓库一律用百分比写法而不整抄那条绝对路径）。\n\n')

REPL = dict(r1_n=r1_n, r1_p=r1_p, r1_m=r1_m, r1_names=r1_names[0], r2a=r2a, r2b=r2b, r3a=r3a, r3b=r3b,
            mfiles=len(mfiles), mbytes=money(mbytes), r5=r5, rev=rev, st=len(st), st_m=st_m, st_q=st_q,
            bin_md5=bin_md5, bin_bytes=money(bin_bytes), arc_md5=arc_md5, arc_bytes=money(arc_bytes),
            dfiles=len(dfiles), dsrc=dsrc, dsnap_at=dsnap_at, dnew=dnew,
            dgate=dcred.group(1) + ' 只源全扫 / HITS=' + dcred.group(2),
            pyc_n=pyc_n, ports=', '.join(ports), has14=('True' if 'COM14' in ports else 'False'),
            vm_row=vm_row)
BLINES = BLOCK.format(**REPL).split('\n')
secret = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', open(SRC_MACRO, encoding='utf-8').read()).group(1).encode('utf-8')
for _ln in BLINES:
    assert chr(92) not in _ln, 'ABORT: 正文里有反斜杠：' + _ln[:60]
    assert '{' not in _ln and '}' not in _ln, 'ABORT: 有未求值的占位：' + _ln[:60]
    assert secret not in _ln.encode('utf-8'), 'ABORT: 明文凭据闸命中'
idx = rd_t.index(anchor)
new_rd = rd_t[:idx] + '\n'.join(BLINES) + rd_t[idx:]
open(RDME, 'w', encoding='utf-8', newline='').write(new_rd)
rb = open(RDME, encoding='utf-8', newline='').read()
assert rb.count('\r') == 0
assert rb.startswith(rd_t[:idx]) and rb.endswith(rd_t[idx:]) and rb.count(anchor) == 1
assert rb.count('\n') == rd_t.count('\n') + len(BLINES) - 1, \
    'ABORT: README 行数增量与块行数不符（%d vs %d + %d - 1）' % (rb.count('\n'), rd_t.count('\n'), len(BLINES))
assert rb.count('第十次读数') == rd_t.count('第十次读数') + 1
rd_lines = rb.count('\n')

# ---------------- FreqErr.md 第七批 3 条（先数后回填） ----------------
frq_t = open(FREQ, encoding='utf-8', newline='').read()
assert frq_t.count('\n') == frq_t.count('\r\n') and frq_t.endswith('\r\n')
f_l0 = frq_t.count('\r\n') - 1
f_e0 = sum(1 for l in frq_t.split('\r\n') if l.startswith('[错误类型]'))
TITLE = '## 2026-09-25（R57 第七批：补落遍自己带进来的三只）新增 3 条（根族：**判据的名单取自单一出处** / **裁决句里预写字面量** / **Edit 把下一行粘到本行尾**）'
ROWS = [
    TITLE,
    '',
    '[错误类型] **归属/差集类判据的名单只取"上一遍载体"一个出处** ⇒ 更早各遍在册的件被算成"未归格"，一条本来成立的反证被自己的口径点红'
    '（本遍实测：代落件池 8 只里 3 只"未归格"，ABORT 文案还写着"崩溃遍跑到过 vm_run？归因要重读"，而真相是那 3 只由更早两遍的在册载体点名）',
    '→ 症状：门红了，读起来像"上一批留下脏东西"，去查崩溃遍有没有跑到某一步；实际池子里一只都没漏，漏的是**取名单的范围**。',
    '→ 为什么它危险：①它把**口径缺口**伪装成**事实违例**——红得很有说服力，因为"未归格只数"确实是现算的；'
    '②它的假红排在写盘之前，所以只会浪费一轮排查 + 制造一次假指控，制造出的下一步动作（"重读归因"）本身又是对已落文档的一次改写；'
    '③同一族在本仓库已犯两次（R50 第五次提交轮的 `unlisted[:10]` 截断、R46 的"门只打印不置退出码"），本条的新形态是**出处单一**而不是名单被截。',
    '→ 正确做法：①写归属/差集门之前先问**这个名字被谁登记过**——登记是跨遍的，出处就要跨遍取（本遍改为读今日全部在册载体取并集，8/8 归格）；'
    '②判据的**真正主张**要单独写成一条关系式（本臂的主张是"池子最晚那只 == 上一遍在册最晚 ⇒ 崩溃遍没产代落件"），别把"全部在册"这种大口径当成主张本身；'
    '③红了先复算**门自己的范围**再去改被检物（本遍就是这么抓回来的：被检池一只没动）。',
    '[错误类型] **裁决句里预写字面量**（本遍实测：载体 APPEND 行写了"现跑 ls-files 命中 = False / False 由本遍现算："，后面才接上现算的插值）'
    '⇒ 一句话里同时有**猜出来的**和**量出来的**两个真值，读者按哪个读都对不上另一个',
    '→ 症状：文字先给结论、括号里再给读数；当读数与预写不符时，那句话要么假绿要么假红，而脚本不会红（预写的那两个 False 只是字符，不参与求值）。',
    '→ 为什么它危险：这就是"完成态数字不许预写"那条老规矩的**布尔亚种**——数字被规矩盯着，布尔字面量没人查；'
    '而它偏偏出现在"这把尺不适用"这种**降级声明**里，降级声明一旦说反，下一遍就会拿它当"其实适用过"的依据。',
    '→ 正确做法：①裁决句里的每个真值都必须是**同一个表达式的插值**，不许出现裸 True/False；'
    '②声明"某把尺不适用"必须配一道 assert 它真的不适用（本遍加了 `assert DEV_UNTRACKED and UPD_UNTRACKED`），否则那句话没有执行者；'
    '③同族自查：`assert X == len(Y) and False is False or True`（本遍另一只自纠的恒真式）与它同根——**句子里有没有不参与判定的成分**，落笔时逐句问一遍。',
    '[错误类型] **Edit 的 new_string 比 old_string 少了原串尾部那个换行** ⇒ 下一行被**粘到本行尾**，造出一处语法错而不是内容错'
    '（本遍实测：一次"看似无实质改动"的编辑把 `LASTLINE = ... else <空串>` 那一行的尾部换行丢掉，与下一行 `LAST_UP = ...` 并成一行，`ast.parse` 才抓到）',
    '→ 症状：文件"看起来还是那些行"，但行数少 1；如果两处恰好互相抵消（一行被粘、一行被拆），行数与 grep 都能骗过去。',
    '→ 为什么它危险：用户记忆里那七类 Write/Edit 自伤讲的都是"内容被改写"，本条是**结构被改写且默认无人检查**——尤其当 old_string 是从 Read 输出复制来的，'
    '尾部换行在复制时最容易丢，而 Edit 不会为"少一个换行"报任何警。',
    '→ 正确做法：①以**整行**为单位做 Edit：old 与 new 要么都以换行收尾，要么都不带；只改一行内容时把该行**上下各一行**也放进锚点；'
    '②任何对 `.py` 的编辑之后立刻 `ast.parse` 复跑（本遍就是它抓回来的），别依赖"我能看出来"；'
    '③同族 = 用户记忆"工具映射与环境事实"里的 Edit 七类自伤（本条登记为第八类）。',
]
BODY = [l for l in ROWS if l]
N_NEW = len([l for l in ROWS if l.startswith('[错误类型]')])
assert N_NEW == 3, 'ABORT: 本批正文条数现算 %d 只，不是 3' % N_NEW
TAIL = '\r\n' + '\r\n'.join(ROWS) + '\r\n'
LEDGER = ('>'
          ' **【' + AT + ' 落地｜R57 第七批 ' + str(N_NEW) + ' 条】** 追加之前现读磁盘（本脚本进入时刻 ' + AT + '，AT 在任何产证动作之前取的）：'
          '全文 `^[错误类型]` 条数 = **' + str(f_e0) + '**、行数 = **' + str(f_l0) + '**、字节 = **' +
          format(len(frq_t.encode('utf-8')), ',') + '**；本批正文 = **' + str(N_NEW) + '** 条 / **' +
          str(len(ROWS)) + '** 行（**不含**本台账行、**不含**标题上方那只 glue 空行，两者另计）；'
          '**落盘后的终态三格由本遍载体现数**（完成态数字不许在本行里预写）。'
          '同遍 backups/README 只加 §1 那一格：改前 **' + str(rd_t.count('\n')) + '** 行 -> 改后 **' + str(rd_lines) + '** 行（+**' +
          str(len(BLINES) - 1) + '**，纯 LF、§2 及之后一字节未动）。')
TAIL = TAIL + LEDGER + '\r\n'
for _ln in TAIL.split('\r\n'):
    assert chr(92) not in _ln and '{' not in _ln and '}' not in _ln
    assert secret not in _ln.encode('utf-8')
    assert len(_ln) > 40 or _ln == ''
new_frq = frq_t + TAIL
f_l1 = new_frq.count('\r\n') - 1
f_e1 = sum(1 for l in new_frq.split('\r\n') if l.startswith('[错误类型]'))
assert f_l1 - f_l0 == len(ROWS) + 2, \
    'ABORT: 本遍写盘前现算行增量 %d != 正文 %d + glue 1 + 台账 1' % (f_l1 - f_l0, len(ROWS))
assert f_e1 == f_e0 + N_NEW
open(FREQ, 'w', encoding='utf-8', newline='').write(new_frq)
fb = open(FREQ, encoding='utf-8', newline='').read()
assert fb.startswith(frq_t) and fb.count('\r\n') == new_frq.count('\r\n')
assert sum(1 for l in fb.split('\r\n') if l.startswith('[错误类型]')) == f_e1 == f_e0 + N_NEW
assert fb.count('\n') - 1 == f_l1

# ---------------- 载体最后落（本遍所有完成态数字在这里现数） ----------------
with open(CARRY, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R57 第十次读数 现跑于 ' + AT + '（本文件由 hardware/r57_backups_readme10.py 单次运行写出）\n')
    f.write('RULER1 git diff HEAD --numstat main/ = %d 只 / +%d / -%d  名单=%s\n' % (r1_n, r1_p, r1_m, ','.join(r1_names)))
    f.write('RULER2 diff -rq r43 根A/根B vs main = %d / %d 行\n' % (r2a, r2b))
    f.write('RULER3 diff -rq r53 根A/根B vs main = %d / %d 行\n' % (r3a, r3b))
    f.write('RULER4 工作树 main/ = %d 只 / %d B\n' % (len(mfiles), mbytes))
    f.write('RULER5 diff -rq r44_sourceonly vs main = %d 行\n' % r5)
    f.write('SAME 三道 assert 逐字等于第九次在册值 = True（尺①/尺②③⑤/尺④）⇒ 不新建备份根的判据有执行者\n')
    f.write('FIELD rev-list=%s  porcelain=%d 行（%d M + %d ??）  ports=%s  COM14 在位=%s\n' % (
        rev, len(st), st_m, st_q, ','.join(ports), 'COM14' in ports))
    f.write('BIN build=%s/%d B  r43归档=%s/%d B  r53归档=%s/%d B（归档 == 待烧，r43 那只 = 板上历史格）\n' % (
        bin_md5[:8], bin_bytes, arc_md5[:8], arc_bytes, r53_md5[:8], r53_bytes))
    f.write('DOCS 第十遍 = 目录 %d 只 / 表格 %d 行 / NEW_ONES %d @%s 凭据闸 OF=%s HITS=%s  pyc/pycache=%d\n' % (
        len(dfiles), dsrc, dnew, dsnap_at, dcred.group(1), dcred.group(2), pyc_n))
    f.write('README §1 改前 %d 行 -> 改后 %d 行（块 %d 行，纯 LF，插入未动 §2 及之后）\n' % (rd_t.count('\n'), rd_lines, len(BLINES) - 1))
    f.write('FREQ 错误类型 %d -> %d 条 / 行数 %d -> %d（第七批 %d 条 / %d 行 + 台账 1 行）\n' % (
        f_e0, f_e1, f_l0, f_l1, N_NEW, len(ROWS)))
    f.write('VM_LAST %s\n' % vm_row)
    f.write('NOTDONE 本遍没做（点名）：没新建备份根 / 没重建重烧 / 没改 main/ 源码 / 没往 hardware/ht305_sync/ 落一字节 / 没新建清单代次 / '
            '没跑 git status --porcelain -uall（所以 ⑥ 那只 ?? 只数只记行数不记只数）/ 没 push、没 amend / 零删除 / F 臂判据未预写\n')
    f.write('VERDICT=BACKUPS_README10_DONE  ' + md5_of(RDME)[0][:8] + ' ' + md5_of(FREQ)[0][:8] + '\n')

print('RULER 1=%d只/+%d/-%d %s  2=%d/%d  3=%d/%d  4=%d只/%s B  5=%d' % (
    r1_n, r1_p, r1_m, ','.join(r1_names), r2a, r2b, r3a, r3b, len(mfiles), money(mbytes), r5))
print('FIELD rev-list=%s porcelain=%d(%d M/%d ??) ports=%s COM14=%s' % (rev, len(st), st_m, st_q, ','.join(ports), 'COM14' in ports))
print('DOCS 第十遍 = %d 只 / 表格 %d 行 / NEW %d @%s / pyc=%d' % (len(dfiles), dsrc, dnew, dsnap_at, pyc_n))
print('README_LINES %d -> %d（§1 第十次读数块 %d 行）' % (rd_t.count(chr(10)), rd_lines, len(BLINES) - 1))
print('FREQ 错误类型 %d -> %d 行 %d -> %d（三条，先数后回填）' % (f_e0, f_e1, f_l0, f_l1))
print('CARRY = hardware/r57_backups_readme10.txt (%d B)' % os.path.getsize(CARRY))
print('VERDICT=BACKUPS_README10_DONE')
