# -*- coding: utf-8 -*-
# R54 尾巴归档 paperwork 落地器：done.md 200 + todo.md 第十五遍 + dev_log/20260924.md 新节
# 纪律：校验前置于写盘；纯追加；CRLF/LF 分文件保持；减号列必须为 0（本器不做任何替换）。
import sys, os, time, hashlib

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\david\Documents\all_projects\自招学习'
DRY = '--dry' in sys.argv
NOW = time.strftime('%Y-%m-%d %H:%M:%S')

def rd(p):
    with open(os.path.join(ROOT, p), 'rb') as f:
        return f.read()

def wr(p, b):
    with open(os.path.join(ROOT, p), 'wb') as f:
        f.write(b)
    back = rd(p)
    assert back == b, 'read-back mismatch: ' + p

# ---------------- done.md 200（纯 LF） ----------------
DONE_ADD = '''- [x] 200 **第 12 代 ht305 全量同步 `r54final` + 归档链 gen 20 / gen 21 末版冻结 + 排查记录 §38.17 + `FreqErr.md` 四条（10:47:20 截止拷贝 → 10:47:26 建包 → 10:47:45 远端验 → 10:48:41 往返 → 10:49:36 两把差集尺 → 10:53:43 / 10:54:14 凭证两批落地 → 11:02:31 gen 20 → 11:12:27 gen 21 → ''' + NOW + ''' 本节落笔；**没烧录、没碰串口、未 push**）**（09-24 10:4x~11:3x；任务 #167~#171；**屏侧一个字节没动，本条全是同步 + paperwork**）
  ① **同步读数（逐字取自 `hardware/ht305_sync/evidence/r54_local.txt` / `r54_verify.txt`，不是回忆）**：截止 10:47:20 拷贝、10:47:26 建包 ⇒ 载荷 **509 只 / 4,805,345 B**，包 **1,952,829 B / md5 `a5e1c600c2655089cdf6acde2c8522ff`**；三道前置闸现量而非抄常量：`git-listed (dupes) = 512 / dupes = 0`、`selected = 509 | copy failures = 0 []`、`plaintext in staging = 1 ['hardware/zizhao-esp32s3/main/provision_ap.c']`（那只按既有口径**随包上ht305、不入库**）。远端 = `VERIFY_BEGIN_AT 10:47:39` ⇒ `REMOTE_ZIP_MD5` 与本地**逐字同值**、`EXTRACT_OK=True`、`REMOTE_FILES=509 / REMOTE_BYTES=4805345 / REMOTE_FORBIDDEN=0`、聚合 `3af1f2e01bfdd870e2ed36cd3f31f0c8eb82945f625f6ef41f2ef61b5184c02b`（64 个十六进制字符 = **sha256 全长**）两侧同值、`REMOTE_DONE_AT 10:47:45`。
  ② **上传前探测 + 往返**：10:47:35 `r54_probe.txt` ⇒ `TARGET_EXISTS=False`（本代包在服务器桌面上**第一次落盘就是干净的**，不需要覆盖动作）+ 同一次调用列全桌面 = r 系列 **11** 只 zip 并存（`zizhao_sync_20260923_r43.zip` 1,117,960 一直到 `zizhao_20260924_r53final.zip` 1,861,210）+ 1 只已被冠上 `SUPERSEDED-` 前缀的 `.tar.gz`（1,002,599 B）+ 1 只不相关的 9,762 B zip ⇒ **零删除**。10:48:41 `r54_roundtrip.txt` = "远端到底有没有明文"这句话**唯一的量法**：从远端解包目录 `scp` 抓回 `provision_ap.c`，`SCP_RC=0`、两侧 **10,199 B / md5 `0419bf1628f399f399ca41daf8ed3494`** 同值、脚本现算 `BYTE_EQUAL_TO_WORKTREE=True`、`PROV_PASS_HITS_REMOTE=1` ⇒ `VERDICT=REMOTE_CARRIES_PLAINTEXT`（**登记事实、不是事故**：服务器副本一直带明文，本机 `git grep HEAD` 仍为 0 ⇒ 所以**绝不 `git push`**）。
  ③ **两把差集尺（10:49:36）+ 本代工具首崩的修法**：名单尺 `LOCAL_LINES=509 / REMOTE_LINES=509 / ONLY_IN_LOCAL=0 / ONLY_IN_REMOTE=0`，**且这段之前先落了一段 EOL 前置读数**（LOCAL `bytes=23489 lines=509 CRLF=509 bareLF=0`；REMOTE 剥后 `CRLF=0 bareLF=509`；VERIFY 原件 `CRLF=532 BOM=True`）⇒ 归一行尾再算差集，(56) 那条纪律本代兑现；内容尺 = 508 只 identical + **1 只 `changed_since_cutoff`**，那只正是差集脚本自己（`r54_listdiff.py` ⇒ **派生时刻差**，不是漂移）。同一只脚本首跑 `rc=1`（`AttributeError: 'NoneType' …`，根因 = 子进程把 **GBK** 中文写进 stdout、父进程按 UTF-8 解码抛 `UnicodeDecodeError: 0xc4` ⇒ `d.stdout is None`），修法三句一起写（子进程显式 `env` + `PYTHONUTF8=1` + 父侧解码口径）⇒ **崩溃那次的读数不作数，修完的读数才算数**。
  ④ **凭证落地 = 两批，不是一批**：主批 10:53:43（`r54_land_log.txt`：`FILES=10 BYTES=78,290`、`AGGREGATE_MATCH=YES`）+ 尾件 10:54:14（`r54_extra_land.txt`，`FILES=1` = 往返那只，它在第一批跑完之后才存在 ⇒ 分两批由**时刻决定**、不是遗漏）；两批各带普查，尾件另加 `FETCH_NAME_LEAKED_INTO_REPO=0`（防"从远端抓回的文件名把远端路径带进仓库"这一族污染）。本代另在 10:53:16 跑了 `r54_parse_check.txt`（`FIRST3=239,187,191`、`PARSE_ERRORS=0`、`REMOVE_ITEM_HITS=0`、`SCRIPT_LINES=91`、两侧 md5 `AE56CE97…` 同值、`PS_RC=0`）⇒ 上传脚本的"排除项"是**读代码量出来的**，不是我声称的。
  ⑤ **归档链两遍 + 关系式第二次跨代成立（本代最重要的量具收益）**：gen 20 = 11:01:23 编码体检（`RISKY_PS1=0`）→ 11:02:18 门 `cred_gate_recheck_110218.txt`（860 B）`FILES_SCANNED=343 / PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0 / VERDICT=CLEAN / PY_EXIT=0` → 11:02:31 清单 `TOTAL=342 / TOTAL_BYTES=1,131,371 / BOM_FILES=62`；gen 21（**末版**）= 11:12:08 体检（`ps1_bom_scan.txt` 按设计覆写自身输出，`OVERWROTE=8302 B md5:e80fab36`）→ 11:12:09 门 `..._111209.txt` `FILES_SCANNED=345 / 两计数 0 / CLEAN / PY_EXIT=0` → 11:12:27 清单 `TOTAL=344 / 1,141,974 B / BOM 62` → `verify_manifest.py`（**不接管道**）`ROWS=344 / MISMATCH=0 / MISSING=0 / UNLISTED=0 / VERIFY_RC=0 / VERDICT=MANIFEST_STILL_TRUE`。⇒ **`TOTAL == 本遍门 FILES_SCANNED − 1`** 在 343→342、345→344 **两次独立成立**，且门与清单之间**没有增删任何一只文件**；本条与 §38.17 里**没有任何一个预测的绝对只数**。
  ⑥ **本批我自己造成的四处（前三处升 `FreqErr.md` 错误类型，第四条 = 登记这三条的那只台账行自己撞到）**：(a) 一条**方向反了**的 LF 守卫 `assert t.count('\\n') == t.count('\\r\\n')` —— 真值表是"纯 CRLF ⇒ 真、纯 LF ⇒ 假、空 ⇒ 真"，注释却写它守"README 必须纯 LF" ⇒ 拿它守一只真 LF 文件会**必红**，拿它守一只 CRLF 文件会**永远绿**；(b) 取证行里"见排查记录 §36.5 那一族的守卫"是**假指针**（`grep -n "^### 36\\.5"` 现读那一行是「36.5 本节没做（点名）」），错在**把一个节号当成了它的内容**；(c) gen 19 那句"可证伪预期：门输出只数从 23 只变 24 只（311→312）"里的基数是**手抄快照**——现跑 `ls -1 evidence/cred_gate_recheck_*.txt | wc -l` = **27 / 28**、`TOTAL` = **342** ⇒ 预期方向对、被锚死的数全过期；(d) 追加 (a)(b)(c) 的那只台账行把"追加之后 `wc -l`"算在**它自己之前** ⇒ 写下即差 1（登记 1800 / 实测 1801），修法 = **先数后回填**（占位符在最终字节串上现算再替换）+ 落盘后独立回读，订正句**追加**而不是就地改数。**共同形状**：判据成立的域 ≠ 结论要覆盖的域，而**订正与登记本身也是断言载体**。
  ⑦ **本条没做（点名）**：**没烧录、没碰串口、没接电池、没按电源键、没短接**（11:23:26 与 11:39:17 两次现跑都是 `COM3, COM4, COM5, COM6` ⇒ **COM14 不在**，§38.13 那两行判据的样本数仍为 **0**）⇒ 屏亮**零次**肉眼确认 ⇒ **不播提示音**；`esp_gpio_hold_en()` 故意仍未加（等探针读数）；**未 `git push`**、零历史重写（rebase / filter-branch / amend 一概没碰）；`Agent_readme.txt` / `.workbuddy/` / `dev_log/20260919.md` 三处仍未入库（等裁决 ⇒ 本批所有 `git add` 都是逐只点名，没用过 `-A` / `.`）；**提交轮 #9、`backups/README.md` 第八次读数、docs 快照第八遍、mindog 第二路、空上下文复查都排在本条之后**；本条**没删任何一只文件**（`%TEMP%` 那批执行件仍按既有口径不入库，复算须照载体头部自写）。
'''

# ---------------- todo.md 第十五遍（纯 CRLF，单行） ----------------
TODO_ADD = ('【**' + NOW + ' 第 12 代同步 `r54final` + gen 20 / gen 21 末版冻结 + §38.17 + `FreqErr.md` 四条落地之后复跑（第十五遍）**：'
 '① 两条老命令 ⇒ 未勾选名单与只数**第十五次逐字未变**（仍 `44 46 48 49 50 51 52 54 55 56 57 58 59 60 61 62 63` / **17**），'
 '`grep -n "^## " done.md | tail -1` 末节号仍是 **二十三**，`grep -c "^- \\[x\\] 200" done.md` = **1**，'
 '`git rev-list --count origin/main..HEAD` 现跑 = **17**（11:39:03 现场读，**本行不回填**：提交轮 #9 之后会 +1，届时的数以那一轮自己的载体为准）。'
 '② **本遍抓到一条量具路径错，打在第十三遍自己身上**：那一遍写的是「`docs/` 快照 = **37 只**（`ls -1 docs | wc -l` 现跑，含 `SNAPSHOT_NOTE.txt`）」，'
 '本遍在仓库根现跑同一条命令 = **2**（只有 `letter_from_learningAgent_new_R28.md` 与 `letter_to_learningAgent_new.md`），'
 '那 37 只实际住在 `backups/r43_20260922_131029/docs/`（里面那只 `SNAPSHOT_NOTE.txt` 的刷新时刻 = 09-24 08:43:08）'
 '⇒ **数是对的、命令是错的**：37 是**备份根快照**的只数，仓库根 `docs/` 只有两只 letter。从本行起：引用 docs 快照一律带完整路径，'
 '且任何"某目录 N 只"的读数必须把**当时 cd 在哪个目录**一起写进载体（同族：项目记忆 (74)"汇总行只数对而名单被截断 = 半截取证"）。'
 '③ **同一族路径口径的第二处**：`evidence/` = **235**、`scripts/` = **102** 这两个数活在 `hardware/ht305_sync/` 下面，'
 '仓库根**没有** `evidence/`（本遍现跑 `ls -1 evidence` 直接 `No such file or directory`）⇒ 以后这两只目录的读数一律写成 `hardware/ht305_sync/<dir>`。'
 '④ 冻结链只登记**式子**不登记预测数：`TOTAL == 本遍门 FILES_SCANNED − 1` 在 gen 20（343→342）与 gen 21（345→344）**两次独立成立**；'
 '末版 = 11:12:27 / `TOTAL 344` / `TOTAL_BYTES 1,141,974` / `BOM_FILES 62`，引用前现跑 `verify_manifest.py`（不接管道）。'
 '⑤ 现场态（11:39:03 / 11:39:17 现跑）：`git -c core.quotePath=false status --porcelain` = **11 只 ` M` + 36 只 `??` = 47 行**，'
 '其中 `main/` 侧只有 **1** 只 `provision_ap.c`（mtime 09-19 15:50:08 ⇒ 本批没碰它，它仍因自带 1 处明文每轮被点名 DROP）⇒ **"本批零代码进工作树"成立**；'
 '同一时刻用户端仍报 **66 个未提交变更**，与本行的 47 **两把尺互不可换算**，差值未定性 ⇒ 只登记各自的数，**不得拿 47 去驳回 66**（承接第十三遍⑥）；'
 '`python -m serial.tools.list_ports` = **COM3, COM4, COM5, COM6** ⇒ **COM14 仍不在**，§38.13 那两行判据样本数还是 **0**，'
 '"接电池 + 强制通电 + 短接重烧"仍全在用户侧；`C:/esp/zproj/build/zizhao_esp32s3.bin` 现算 md5 = `fb32168af14d715b354e691edfa39fcd`（**md5，32 位 hex）≠ 板上 `4842a3a0…`** ⇒ 待烧 ≠ 板上仍成立。'
 '⑥ **行数 269 → 270：本行是本遍唯一一处净 +1 行**（第十一~十四遍各声明过一次"唯一"，主语都只限它们自己那一遍）；'
 '两把括号尺（全角 `（）` / 半角 `()` 逐行数不配平的只数）追加前后各测一次 ⇒ **53 / 1** 逐字同值，由脚本末尾断言兑现，不是话术。】')

# ---------------- dev_log/20260924.md 新节（纯 LF） ----------------
DEV_ADD = ('### R54 尾巴（09-24 10:47:20~' + NOW[11:] + '）：第 12 代 ht305 同步 `r54final` + gen 20/gen 21 **末版**冻结 + §38.17 + `FreqErr.md` 四条 —— 纯同步与 paperwork，屏侧零字节\n'
 '\n'
 '- **同步（10:47:20 截止拷贝 → 10:47:26 建包 → 10:47:45 远端验 → 10:48:41 往返 → 10:49:36 两把差集尺 → 10:53:43 / 10:54:14 凭证两批落地）**：'
 '载荷 **509 只 / 4,805,345 B**、包 **1,952,829 B / md5 `a5e1c600…`**、两侧聚合 sha256 `3af1f2e0…c02b` 逐字同值、`REMOTE_FORBIDDEN=0`；'
 '名单尺 `ONLY_IN_LOCAL=0 / ONLY_IN_REMOTE=0`（509/509，两侧行尾先各测一次再归一），内容尺 508 只 identical + **1 只 `changed_since_cutoff`**（差集脚本自己，派生时刻差）；'
 '`TARGET_EXISTS=False` ⇒ 本代包第一次落盘就是干净的，服务器桌面 r 系列 **11 只 zip 并存**、零删除。\n'
 '- **往返 = "远端有没有明文"的唯一量法**：`scp` 抓回 `provision_ap.c`，两侧 **10,199 B / md5 `0419bf16…`** 同值、`BYTE_EQUAL_TO_WORKTREE=True`、`PROV_PASS_HITS_REMOTE=1` ⇒ `VERDICT=REMOTE_CARRIES_PLAINTEXT`'
 '（登记**事实**不是事故：服务器副本一直带明文、本机 `git grep HEAD` 仍是 0 ⇒ **绝不 push**）。\n'
 '- **冻结链两遍 + 关系式跨代第二次成立**：gen 20 = 11:01:23 体检 → 11:02:18 门 `FILES_SCANNED=343` → 11:02:31 `TOTAL=342 / 1,131,371 B / BOM 62`；'
 'gen 21（**末版**）= 11:12:08 体检 → 11:12:09 门 `345` → 11:12:27 `TOTAL=344 / 1,141,974 B / BOM 62` → `verify_manifest.py`（不接管道）'
 '`ROWS=344 / MISMATCH=0 / MISSING=0 / UNLISTED=0 / rc=0 / MANIFEST_STILL_TRUE` ⇒ **`TOTAL == FILES_SCANNED − 1`** 两次独立成立，全篇**没有一个预测的绝对只数**。\n'
 '- **登记落点（每处都现跑核过减号列）**：排查记录 **§38.17**（`git diff --numstat` = **+29 / −0**，3,588 行 / 590,271 B，纯 CRLF 未破）；'
 '`FreqErr.md` **四条**（**+58 / −0**，`^[错误类型]` 175→**179**、`wc -l` 1,773→**1,811**，台账行**先数后回填**）；'
 '`hardware/ht305_sync/README.md`（+16 / −5）、`MANIFEST.txt`（+41 / −8，由 `gen_manifest.py` 生成，非手写）；本文件本节、`done.md` **200**、`todo.md` **第十五遍**、'
 '`updates/20260924_墨水屏R54第12代同步与gen20-21冻结.md`（**本代新建一只，不追加进 R53 那只**）。\n'
 '- **本批我自己造成的四处**：(a) `assert t.count(chr(10)) == t.count(chr(13)+chr(10))` 这条自称"守纯 LF"的守卫**方向反了**（真值表：纯 CRLF⇒真、纯 LF⇒假）；'
 '(b) README NOTE 里"见排查记录 §36.5 那一族的守卫"是**假指针**（现读那行是「36.5 本节没做（点名）」）；'
 '(c) gen 19 那句"可证伪预期：门输出 23→24、只数 311→312"的基数是**手抄快照**（现跑 27 / 28 只、`TOTAL` 342）⇒ 方向对、锚死的数全过期；'
 '(d) 登记 (a)(b)(c) 的那只台账行把"追加之后 `wc -l`"算在**自己之前** ⇒ 写下即差 1（1800 vs 实测 1801）。**共同形状**：判据成立的域 ≠ 结论要覆盖的域，订正与登记本身也是断言载体。\n'
 '- **现场态（11:39:03 / 11:39:17 现跑）**：`rev-list origin/main..HEAD` = **17**（未 push）；`status --porcelain` = **11 ` M` + 36 `??` = 47 行**，'
 '`main/` 侧只有那只每轮被 DROP 的 `provision_ap.c`（mtime 09-19 15:50:08）⇒ 本批零代码进工作树；COM 枚举 = COM3/COM4/COM5/COM6 ⇒ **COM14 不在**；'
 '待烧 `fb32168a…`（md5）≠ 板上 `4842a3a0…`；`hardware/ht305_sync/` 的 `evidence/` = 235、`scripts/` = 102（仓库根**没有** `evidence/`）；'
 'docs 快照那 37 只实际在 `backups/r43_20260922_131029/docs/` ⇒ **todo 第十三遍那句把命令写成了仓库根 `docs/`，第十五遍已点名订正**。\n'
 '- **本批没做**：没烧录 / 没碰串口 / 没接电池 / 没按电源键 / 没短接 / 屏亮 0 次肉眼确认 / 不播提示音 / **未 push** / 历史未脱敏（等裁决）/ `esp_gpio_hold_en()` 故意仍未加 / '
 '提交轮 #9 与 backups 第八次读数、docs 第八遍、mindog 第二路、空上下文复查排在本节之后 / 本批**零删除**。\n')

def rulers(tb):
    L = tb.split('\r\n')
    return (sum(1 for l in L if l.count('\uff08') != l.count('\uff09')),
            sum(1 for l in L if l.count('(') != l.count(')')))

# ---------- 预检 ----------
done_b = rd('done.md')
todo_b = rd('todo.md')
dev_b = rd('dev_log/20260924.md')

assert b'\r' not in done_b, 'done.md 必须是纯 LF'
assert b'\r' not in dev_b, 'dev_log 必须是纯 LF'
assert todo_b.count(b'\r\n') == todo_b.count(b'\n'), 'todo.md 必须是纯 CRLF'
assert done_b.endswith(b'\n\n') and dev_b.endswith(b'\n\n') and todo_b.endswith(b'\r\n')
assert '- [x] 200' not in done_b.decode('utf-8'), 'done 200 已存在'
assert '第十五遍' not in todo_b.decode('utf-8'), '第十五遍已存在'
assert 'R54 尾巴' not in dev_b.decode('utf-8'), 'R54 节已存在'

done_s = done_b.decode('utf-8')
assert DONE_ADD.startswith('- [x] 200')
assert '\r' not in DONE_ADD
done_out = (done_s + DONE_ADD).encode('utf-8')
assert done_out.count(b'\n') == done_b.count(b'\n') + DONE_ADD.count('\n')
assert done_out.count(b'\r') == 0
assert done_out.decode('utf-8').count('- [x] 200') == 1

todo_s = todo_b.decode('utf-8')
assert '\r' not in TODO_ADD and '\n' not in TODO_ADD, 'todo 追加必须是单行'
f0, h0 = rulers(todo_s)
todo_out = (todo_s + TODO_ADD + '\r\n').encode('utf-8')
f1, h1 = rulers(todo_out.decode('utf-8'))
assert (f1, h1) == (f0, h0), '括号尺变了: %s/%s -> %s/%s' % (f0, h0, f1, h1)
assert todo_out.count(b'\r\n') == todo_b.count(b'\r\n') + 1 == todo_out.count(b'\n')

dev_s = dev_b.decode('utf-8')
assert '\r' not in DEV_ADD
dev_out = (dev_s + DEV_ADD).encode('utf-8')
assert dev_out.count(b'\n') == dev_b.count(b'\n') + DEV_ADD.count('\n')
assert dev_out.count(b'\r') == 0
assert dev_out.decode('utf-8').count('\n### R54 尾巴') == 1

print('PRE-CHECK OK  NOW=' + NOW)
print('done.md   lines %d -> %d  bytes %d -> %d' % (done_b.count(b'\n'), done_out.count(b'\n'), len(done_b), len(done_out)))
print('todo.md   lines %d -> %d  bytes %d -> %d  括号尺 全角 %d / 半角 %d (追加前后同值)' % (todo_b.count(b'\n'), todo_out.count(b'\n'), len(todo_b), len(todo_out), f0, h0))
print('dev_log   lines %d -> %d  bytes %d -> %d' % (dev_b.count(b'\n'), dev_out.count(b'\n'), len(dev_b), len(dev_out)))

if DRY:
    raise SystemExit('DRY: 未写盘')

wr('done.md', done_out)
wr('todo.md', todo_out)
wr('dev_log/20260924.md', dev_out)

# ---------- 写后独立回读复核 ----------
d = rd('done.md').decode('utf-8')
t = rd('todo.md').decode('utf-8')
v = rd('dev_log/20260924.md').decode('utf-8')
print('POST done.md  - [x] 200 只数 =', d.count('- [x] 200'), ' / 末节号行 =', [l for l in d.split('\n') if l.startswith('## ')][-1][:20])
print('POST todo.md  行数 =', t.count('\r\n'), ' 第十五遍 =', t.count('第十五遍'), ' 括号尺 =', rulers(t))
print('POST dev_log  R54 节 =', v.count('\n### R54 尾巴'), ' 行数 =', v.count('\n'))
print('POST md5 done/todo/dev =', [hashlib.md5(rd(p)).hexdigest()[:8] for p in ('done.md', 'todo.md', 'dev_log/20260924.md')])
