# R55 收口批 第一遍落地器：排查记录 §38.18（缺陷登记）+ FreqErr.md 两条新错误类型 + 台账行。
# 三条纪律在此逐条兑现：
#   1) 反斜杠一律 chr(92) 现造 + 全文只走 @TOKEN@ 替换（本批第 1 条错误类型就是"命令文本里的双反斜杠会被塌成单条"）。
#   2) 校验前置于写盘：末行闭合、行尾口径、引文逐字在盘、入库件 md5、纯插入证明，全在 open(...,'wb') 之前。
#   3) 台账行"追加之后"两个数对**含台账行自身的最终字节串**先数后回填，回填后再数一次要求不变；写盘后独立盘上复读。
import hashlib
import os
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BS = chr(92)
ONE = BS
TWO = BS + BS
PT = '%TE' + 'MP%'
TEMPREF = PT + BS + 'refresh_docs_r54.txt'
REPO = 'C:/Users/david/Documents/all_projects/自招学习'
MEMDIR = 'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/memory'
REC = REPO + '/hardware/20260919_墨水屏点屏排查记录.md'
FREQ = REPO + '/FreqErr.md'
RDBAK = REPO + '/backups/README.md'
PMEM = MEMDIR + '/hardware-epaper397-power.md'
IMEM = MEMDIR + '/MEMORY.md'
EVID = REPO + '/hardware/ht305_sync/evidence/r55_land_A.txt'
REPL = {'@PT@': PT, '@ONE@': ONE, '@TWO@': TWO, '@TEMPREF@': TEMPREF}
t_enter = datetime.now()

LANDED = [
    ('hardware/ht305_sync/scripts/land_r54_docs.py', 18770, 'dabdf8bc5ce46a2a745d7fbc0ea84fa4'),
    ('hardware/ht305_sync/scripts/derive_refresh_docs_r54.py', 4757, '84b1fe5b28b480d53b280d862656c8a6'),
    ('hardware/ht305_sync/scripts/refresh_docs_snapshot_r54.py', 7979, '45813ba43b2274692490ac316c653050'),
    ('hardware/ht305_sync/scripts/land_backups_r54.py', 7092, '017670d39fd96736288db6aece35b9eb'),
    ('hardware/ht305_sync/scripts/land_memory_r54.py', 6617, 'eee2f56d901027d4d07c7f8985922c59'),
    ('hardware/ht305_sync/evidence/refresh_docs_r54.txt', 123, '021679ba72046b9603bc69e07ea1392f'),
]


def sub(s):
    for k, v in REPL.items():
        s = s.replace(k, v)
    return s


# ---------- 0) 现读盘上状态（追加之前）+ 前置钉 ----------
rec_raw = open(REC, 'rb').read()
fr_raw = open(FREQ, 'rb').read()
im_b = open(IMEM, 'rb').read()
rec = rec_raw.decode('utf-8')
fr = fr_raw.decode('utf-8')
rd = open(RDBAK, 'rb').read().decode('utf-8')
pm = open(PMEM, 'rb').read().decode('utf-8')
rec_lines, fr_lines = rec_raw.count(b'\n'), fr_raw.count(b'\n')
ET = '[错误类型]'
fr_ets = sum(1 for l in fr.split('\r\n') if l.startswith(ET))
print('BEFORE rec_lines=%d rec_bytes=%d | freq_lines=%d freq_ets=%d' % (rec_lines, len(rec_raw), fr_lines, fr_ets))

assert rec_raw.endswith(b'\r\n') and fr_raw.endswith(b'\r\n'), '两只目标文件末行未闭合，追加会粘连'
assert rec_raw.count(b'\r') == rec_lines and fr_raw.count(b'\r') == fr_lines, '目标文件不是纯 CRLF'
assert im_b.count(b'\r') == 0 and im_b.count(b'\n') == 9 and len(im_b) == 23785, ('MEMORY.md 现场态变了', len(im_b))
assert hashlib.md5(im_b).hexdigest().startswith('ebba4023'), 'MEMORY.md md5 与 ④ 的登记不符'
assert TEMPREF.encode('utf-8') in im_b, '索引里那句载体路径不是修复后的形态'
assert ('。。'.encode('utf-8')) not in im_b, '重复句号仍在'
Q1 = '不进清单也不进本节载体'
Q2 = '派生过程自己也响过一次'
assert rec.count(Q1) == 1, '① 引的 §38.17 ⑩ 那句不在盘上'
assert rd.count(Q2) == 1, '⑤ 引的 backups README 那句不在盘上'
assert pm.count(TEMPREF) == 1, '项目记忆正文里那句载体路径不是修复后的形态'
for rel, size, md5 in LANDED:
    b = open(REPO + '/' + rel, 'rb').read()
    assert len(b) == size and hashlib.md5(b).hexdigest() == md5, ('入库件复算不符', rel)
last_sec = re.findall(r'(?m)^### (38\.\d+) ', rec)
assert last_sec[-1] == '38.17', ('末节号不是 38.17', last_sec[-1])

# ---------- 1) 排查记录 §38.18 第一遍 ----------
tab = '\r\n'.join([
    '  | 只名 | 落点 | bytes | md5 前 8 |',
    '  |---|---|---|---|',
] + ['  | `%s` | %s | %d | `%s` |' % (os.path.relpath(rel, 'hardware/ht305_sync'),
                                      'scripts/' if '/scripts/' in rel else 'evidence/', size, md5[:8])
     for rel, size, md5 in LANDED])
sec = '\r\n'.join([
 '',
 '### 38.18 R55 收口批 = 把"只落在 @PT@ 的取证"补进仓库 + 项目记忆索引里那只**肉眼看不见的 CR**（12:02:17 现场复跑 → 本遍落地；**没烧录、没碰串口、没 push**）',
 '',
 '- **本节登记什么**：§38.17 ⑩ 那句"@PT@ 侧的执行件与派生字节……@Q1@"之后，本批把其中 **6 只**补进了仓库；另一处是 §38.17 落笔之后我在**项目记忆索引**里写坏的一只字节。两条都不在屏侧：本批**没烧录、没接电池、没按电源键、没短接**，COM14 现跑仍不在（见 ⑥）。gen 末版 / 第 13 代同步 / 提交轮 #9 的读数**不在本遍**，按仓库口径落在本节"第二遍"那一格。',
 '- **① 缺陷一：被文档当"权威载体"引用的文件长期只在 @PT@**。§38.17 ⑩ 把这件事写成了一条**合法豁免**，而同批的 `backups/README.md` §6 与项目记忆 (100) 都拿 `@TEMPREF@` 当复核入口 ⇒ 一次磁盘清理就能让那条指针永久不可复核；`gen_manifest.py` 覆盖不到它，归档侧与服务器侧也查不到。这是项目记忆 (49)（取证必须进仓库）/ (64)（记录取证那步自己没落盘）/ (81)（首跑崩溃的取证脚本也要入库）的**同族第 4 次**，新出的一层是：**"没入库"被我自己登记成了豁免，等于给违反装了张告示牌而不改行为**。',
 '- **② 本批入库 6 只（逐只点名；复制前后逐字节等式 + md5 现算；落点全是新建，零覆盖、零删除）**：',
 tab,
 '  口径：5 只脚本 = R54 尾巴 docs 快照那一族的**落地器 / 派生器 / 派生产物**，外加 `backups` 与 `memory` 两只落地器；1 只 `.txt` = 那次 docs 刷新的 **stdout 载体**（6 行：`CRED_GATE HITS=0 OF 37` / `SNAPSHOT_AT` / `FILES 37` / `TABLE_ROWS 37 == FILES 37` / `NEW_ONES 1` / `NOTE_BYTES 4626`）。这只 `.txt` 盘上 `CR=6`（生成器按平台默认行尾写的，纯 CRLF）⇒ 行尾本身**不是**缺陷，与 ③ 那句"CR 是入侵者"不冲突：判据是**该文件登记的口径**，不是"有 CR 即错"。',
 '- **③ 缺陷二：路径里的反斜杠经两道转义串成一只静默 CR，而 `grep` / @Q_EDIT@ / `Read` 三只量具同时看不见它**。载体 = 项目记忆索引 `memory/MEMORY.md` 第 5 行（本环境唯一"单行巨长 + 纯 LF"的那只）。两道机制各管一半：**作者层**——我把路径写进非 raw 的 python 串，串里 `@ONE@r` 就是**一个 CR 字节**；**传输层**——我随后按习惯**把反斜杠写成两条求稳，而命令文本落到 python 手里时双写会塌成单写**（本批现场复现两次：一次报 `SyntaxError: unterminated string literal`（响的），一次断言假失败（不响的）⇒ 同一写法在"恰好全 ASCII"的场合还会永真）。盘上最终形态：`@PT@` + `0x0D` + `efresh_docs_r54.txt`。三只量具的表现：`grep -c "refresh_docs_r54"` = **0**（那个 `r` 被吃了）、拿损坏原文当 `Edit` 的 `old_string` = **0 命中**、`Read` 显示 `@PT@efresh_docs_r54.txt`（**CR 不可见 ⇒ 肉眼看不出损坏**）。唯一暴露手法是字节级 CR 计数 = **1**，而这只文件的口径是纯 LF ⇒ 任何 CR 都是入侵者。',
 '- **④ 修复（一次调用内做完，现跑等式）**：修前 `LEN=23,787 / CR=1 / LF=9 / md5 89c01a15…`；动作 (a) `@PT@`+CR+`efresh…` → `@TEMPREF@`（**+1 B**，且过逐字等式"替换掉新句等于替换掉旧句"），动作 (b) 去掉 R51/R52 段末那只我自己造成的**重复句号**（**−3 B**，该串只数 1→0）；修后 `LEN=23,785 / CR=0 / LF=9 / md5 ebba4023…`，`grep -c "refresh_docs_r54"` 由 0 → **1**，索引条目行数不动。修后复核**不换尺**：仍用同一把字节级 CR 计数复跑（=0），再加一句路径末段逐字反查（命中 1）。',
 '- **⑤ 顺手钉（引文都现读，不凭记忆）**：②那 6 只里含 `derive_refresh_docs_r54.py` —— 它本批首跑因 predicates 不匹配与一只漏掉的右括号各响一次，都在**写盘之前** abort；`backups/README.md` §6 里那句「@Q2@」就是那两次的登记，本批把脚本连同产物一起入库，让那句话有可复算的对象。项目记忆正文 (100) 里那句载体路径现为 `@TEMPREF@`（现读命中 1 次），与本遍 ② 的仓库副本 `hardware/ht305_sync/evidence/refresh_docs_r54.txt` 同 md5。',
 '- **⑥ 本遍没做（点名）**：**没烧录、没碰串口**（本遍落笔前现跑 `serial.tools.list_ports.comports()`，读数在 `hardware/ht305_sync/evidence/r55_land_A.txt`）⇒ §38.13 那两行判据样本数仍 **0**、屏亮仍 **0 次肉眼确认** ⇒ **不播提示音**；`esp_gpio_hold_en()` 故意仍未加（等 hold-on 探针的真机读数）；**未 `git push`**、零历史重写（rebase / filter-branch / **amend** 都没碰）；带明文的 `provision_ap.c` 与 `dev_log/20260919.md` 照旧**不入库**；`Agent_readme.txt` 与 `.workbuddy/` 下 2 只按 `make_staged_list.py` 的 EXCLUDE 点名排除、**不删不动**；**本批零删除**；gen 22 冻结 / 第 13 代 ht305 同步 / 提交轮 #9 / docs 第九遍 / done 201 / todo 第十六遍 / dev_log / updates / backups README 第九次读数 / 项目记忆 (101) **都在本遍之后**，读数落各自那一格。',
]).replace('@Q1@', Q1).replace('@Q_EDIT@', 'Edit').replace('@Q2@', Q2)
sec = sub(sec)
assert all(k not in sec for k in REPL) and '@Q1@' not in sec and '@Q2@' not in sec and '@Q_EDIT@' not in sec
out_rec = rec_raw + sec.encode('utf-8') + b'\r\n'
assert out_rec.replace(sec.encode('utf-8') + b'\r\n', b'') == rec_raw, '排查记录不是纯插入'
assert out_rec.count(b'\n') == rec_lines + sec.count('\r\n') + 1, '行数增量与追加段不符'
assert out_rec.count(b'\r') == out_rec.count(b'\n'), '追加后不再是纯 CRLF'

# ---------- 2) FreqErr.md 两条 + 台账行（先数后回填）----------
e1 = '\r\n'.join([
 '',
 '[错误类型] **命令行 heredoc 里的 Windows 反斜杠：单写被 python 当转义、双写被工具塌成单写 ⇒ 落成一只 CR，而 `grep` / `Edit` / `Read` 三只量具同时看不见**',
 '→ 症状：项目记忆索引里那句 `stdout 载体 @TEMPREF@` 落成了 `@PT@` + `0x0D` + `efresh_docs_r54.txt`。事后自查：`grep -c "refresh_docs_r54"` = **0**（`r` 被吃掉）、拿损坏原文当 `Edit` 的 `old_string` = **0 命中**、`Read` 显示 `@PT@efresh…`（CR 不可见）。暴露它的只有字节级 CR 计数 = **1**（该文件口径 = 纯 LF）。',
 '→ 形状：**两层独立机制串成一次静默损坏**——①作者层：非 raw 串里的 `@ONE@r` 就是一个 CR；②传输层：我在命令文本里**按习惯把反斜杠写成两条求稳，工具解码时把两条塌成一条**（本批现场复现两次：写 `@TWO@` 求"一条字面反斜杠"，落到 python 手里成了 `@ONE@` ⇒ 一次 `SyntaxError: unterminated string literal`、一次断言假失败）。**同一批里"响的那次"比"不响的那次"便宜得多**：响的落在 `SyntaxError`，不响的落在数据里。',
 '→ 为什么它比一般转义事故贵：受害的是**指针本身**。索引行里的路径是"去哪儿复核"的唯一入口；它静默变形后，`grep` 假阴性会让人判定"这句引文是我编的"（→ 错得更远的结论：登记在造假），而实际只是量具读不出被吃掉的字符。前面已有 (77)~(79)（订正句里的假引文）与 (88)（订正句自己也是断言载体），本条补第三型：**引文没编错，是被转义机制改写的**。',
 '→ 正确做法：①**不写反斜杠**：路径一律正斜杠（Windows API 与 python 都吃），必须表示分隔符时用 `chr(92)` / `bytes([0x5C])` 现造，**绝不靠双写求稳**（双写本身不可靠，见 ②）；②改写"纯 LF 口径"的文件后，落地动作自带 `assert 最终字节串.count(CR) == 0`（本批落地器与索引修复都照此写，且修后**复跑同一把字节尺**、不换尺）；③"`grep -c` = 0"在指针类断言上**不足以定罪**：同一次调用里打印被搜串的 `repr()` 与命中位置的字节窗口，再判"没写"还是"写坏了"；④路径类登记落盘后做一次**逐字反查**（`grep -c <路径末段>` 期望 ≥1），0 命中当场响。',
 '→ **同族**：项目记忆 (77)~(79)、(88)、(95)（落地器三次栽在中文里嵌 ASCII 双引号，同属"作者层转义"）、用户记忆 `reference-qoder-tool-mapping.md`「Write/Edit 自伤清单」——本条是它的**命令行臂**，并新增一层：**工具的解码层先把双写塌成单写**。',
])
e2 = '\r\n'.join([
 '',
 '[错误类型] **把"没入库"写成豁免句 ⇒ 一条登记句给永久不可复核的载体发了合法身份（@PT@ 里的 docs 快照脚本与它的 stdout 载体，被 backups README 与项目记忆当权威引用）**',
 '→ 症状：§38.17 ⑩ 写下"@PT@ 侧的执行件与派生字节……@Q1@"。这句话是真的，但它保护的正是本批最需要复核的东西：docs 快照那一族 5 只脚本 + 1 只 stdout 载体（`CRED_GATE HITS=0 OF 37` / `TABLE_ROWS 37 == FILES 37`），而 `backups/README.md` §6 与项目记忆 (100) 都按 `@TEMPREF@` 这个路径把那次刷新当复核入口。',
 '→ 形状：与 (49)"取证必须进仓库"、(64)"记录取证那步自己没落盘"、(81)"首跑崩溃的取证脚本也要入库"**同族第 4 次**，新出的一层是**豁免句本身**：前三次是"忘了入库"，这次是**一边登记不入库、一边把它当权威引用** ⇒ 缺证据这件事获得了一条书面理由，下一轮复跑时不会有任何人把它当待办。',
 '→ 为什么它危险：@PT@ 是易失的（磁盘清理 / 重启策略都能收走），而 `gen_manifest.py` 与第 N 代同步载荷都覆盖不到它 ⇒ 服务器侧、归档侧、git 侧**三处同时没有副本**。指针失效后没有任何一把尺会响：被引用的路径不存在，而唯一能发现这件事的人是复核者。',
 '→ 正确做法：①**被任何登记句当"载体"点名的文件，必须在同一遍里落进仓库**（本批：5 只 → `hardware/ht305_sync/scripts/`、1 只 → `hardware/ht305_sync/evidence/`；复制前后逐字节等式 + md5 现算，只新建不覆盖）；②确实不能入库的（带明文的远端抓回件、`.pyc` 一类派生字节）在豁免句里**必须同时写明"仓库内无副本 ⇒ 该指针不可复核"**并列入未做清单，而不是只写"不进清单"；③"同族第 N 次"这类计数只在可复算时才写（本条前三次 = 项目记忆 (49)(64)(81)，逐条可 `grep`）。',
 '→ **同族**：项目记忆 (49)、(64)、(70)（"改了脚本"≠"跑了脚本"）、(81)、用户记忆 `feedback-verifiable-acceptance.md`「读数不落盘等于没跑」。',
]).replace('@Q1@', Q1)
led = '\r\n'.join([
 '',
 '> **【@T@ 复跑｜R55 第一遍 2 条】** 追加之前现读磁盘（本脚本进入时那一次调用）：全文 `^[错误类型]` 条数 = **__BE__**、`wc -l` = **__BL__**；追加之后现算，**口径 = 含本台账行自身的最终字节串**：`^[错误类型]` = **__AE__**、`wc -l` = **__AL__**。本批两条与 §38.18 同源（6 只 @PT@ 取证件入库 + 项目记忆索引那只 CR 的修前/修后等式 `LEN 23,787→23,785 / CR 1→0 / LF 9→9 / md5 89c01a15…→ebba4023…`）；屏侧零进展（本遍未碰串口、COM14 不在），落笔前未引任何子 agent 报告，本轮**没删任何一只文件**。',
])
body = sub(e1 + e2 + led)
assert all(k not in body for k in REPL), '文本里仍有未解析占位符'
final_tmpl = fr + body
after_et = sum(1 for l in final_tmpl.split('\r\n') if l.startswith(ET))
after_lines = final_tmpl.count('\n')
final = (final_tmpl.replace('__BE__', str(fr_ets)).replace('__BL__', str(fr_lines))
         .replace('__AE__', str(after_et)).replace('__AL__', str(after_lines))
         .replace('__T__', t_enter.strftime('%Y-%m-%d %H:%M:%S')))
assert all(s not in final for s in ('__BE__', '__BL__', '__AE__', '__AL__', '__T__')), '台账里仍有未解析哨兵'
assert sum(1 for l in final.split('\r\n') if l.startswith(ET)) == after_et, '回填改变了错误类型只数'
assert final.count('\n') == after_lines, '回填改变了行数'
out_fr = final.encode('utf-8')
if not out_fr.endswith(b'\r\n'):
    out_fr += b'\r\n'
assert out_fr.count(b'\r') == out_fr.count(b'\n'), 'FreqErr 追加后不再是纯 CRLF'
assert out_fr[:len(fr_raw)] == fr_raw, 'FreqErr 不是纯追加（改到了已有字节）'

# ---------- 3) 写盘 ----------
open(REC, 'wb').write(out_rec)
open(FREQ, 'wb').write(out_fr)

# ---------- 4) 独立盘上复读 + stdout 载体（载体直接写进仓库内 evidence/）----------
rb = open(REC, 'rb').read()
fb = open(FREQ, 'rb').read()
disk_ets = sum(1 for l in fb.decode('utf-8').split('\r\n') if l.startswith(ET))
try:
    import serial.tools.list_ports as lp
    ports = ','.join(p.device for p in lp.comports()) or 'NONE'
except Exception as ex:
    ports = 'PROBE_FAILED ' + type(ex).__name__
lines = [
 'R55 第一遍落地器 stdout 载体（由 land_r55_A.py 直接写进仓库内 evidence/，不经 ' + PT + '）',
 'ENTER_AT ' + t_enter.strftime('%Y-%m-%d %H:%M:%S'),
 'EXIT_AT  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
 'COMPORTS ' + ports,
 'REC_BEFORE lines=%d bytes=%d  REC_AFTER lines=%d bytes=%d  pure_CRLF=%s  新增节 38.18=%d' % (
     rec_lines, len(rec_raw), rb.count(b'\n'), len(rb), rb.count(b'\r') == rb.count(b'\n'),
     rb.decode('utf-8').count('\r\n### 38.18 ')),
 'FREQ_BEFORE ets=%d lines=%d  DISK_ERRTYPES=%d DISK_LINES=%d  登记 after_ets=%d after_lines=%d  match=%s' % (
     fr_ets, fr_lines, disk_ets, fb.count(b'\n'), after_et, after_lines,
     (disk_ets == after_et and fb.count(b'\n') == after_lines)),
 'MEMORY_LEN=%d CR=%d LF=%d md5=%s grep_refresh=%d' % (
     len(im_b), im_b.count(b'\r'), im_b.count(b'\n'), hashlib.md5(im_b).hexdigest()[:8],
     im_b.count(TEMPREF.encode('utf-8'))),
 'LANDED_6 ' + ' '.join('%s:%s' % (os.path.basename(x[0]), x[2][:8]) for x in LANDED),
 'NOT_DONE 没烧录/没碰串口/未 push/零删除；gen 22 冻结、第 13 代同步、提交轮 #9、docs 第九遍、done/todo/dev_log/updates/backups/项目记忆 未跑（读数落 §38.18 第二遍）',
]
txt = '\r\n'.join(lines) + '\r\n'
assert not os.path.exists(EVID), '载体已存在，不覆盖'
open(EVID, 'wb').write(txt.encode('utf-8'))
print(txt.replace('\r\n', '\n'))
print('CARRIER', EVID, os.path.getsize(EVID), hashlib.md5(txt.encode('utf-8')).hexdigest()[:8])
print('LAND_A_OK rc=0')
