# `hardware/ht305_sync/` —— ht305 十轮全量同步的脚本与取证件归档

建立时刻：09-23 10:36:41（首批 49 只复制）→ 10:38:51（+3）→ 10:43~10:47（+门复验脚本、清单生成器、编码体检脚本）
→ 11:06（补 `r43_r44_listdiff.txt`）→ 11:34~11:47（+差集第二代读数、+索引侧明文门及其输出）
→ 11:55~12:0x（**无新增只**：本 README 的"两道门→三道口径"订正，加上门与编码体检脚本自身的两处修订）
→ 12:05~12:0x（+**清单复核器** `verify_manifest.py`、+**门的阴性对照** `cred_gate_selftest.py` 及其输出，门复验脚本改成**按时刻落盘**）
→ 12:09~12:1x（第 4 代同步 `r46final` 跑完，**+13 只** r46 凭证与脚本副本）
→ 13:45~13:5x（第 5 代同步 `r47final` 跑完。入档只数**不写成一句硬数**：现跑 `scripts/arch_delta_r47.py`（13:53:14，证件 `evidence/arch_delta_r47_vs_gen9.txt`）
  拿 gen 9 那份清单与盘上做差集 ⇒ `NEW=17 / GONE=0`，其中 `MANIFEST.txt`（清单不自列）与 `evidence/manifest_gen_log.txt`（代次日志按设计不进清单）两只除外 ⇒ **入清单 +15**；
  而**这份差集自身、它的脚本、以及为它重跑的那道门输出**又是 3 只必然新增 ⇒ 末版 `TOTAL` 只以 `MANIFEST.txt` 末三行现读为准（同下表 gen 9 那格的口径）。
  15 只里逐名：`scripts/` 4 只派生脚本（`sync_r47.py`/`r47_upload.ps1`/`chk_r47.ps1`/`r47_cutoff_delta.py`）+ `evidence/` 10 只 r47 凭证 + 1 只门输出。
→ 21:39~21:40（+**索引侧门的驱动** `gate/run_staged_cred_gate.ps1` 与其**两轮阴性对照**输出 3 只：门由"只打印裁决"改成"打印 + `exit 1`"，随后故意 stage / 故意留空各跑一遍证明**它会响**）
→ 21:46~21:5x（第 6 代同步 `r48final` 跑完 ⇒ 21:53:40 落 **+18 只**：`scripts/` 6 只（4 只同步工具 + 派生器 `derive_r48.py` + 差集器 `r48_listdiff.py`）+ `evidence/` 12 只 r48 凭证（9 只原样复制 + 3 只由它们派生出的名单/汇总）；
  只数**不在这里给硬数**，同上格口径：现跑 `scripts/gen_manifest.py` 后的 `MANIFEST.txt` `TOTAL` 行才是末版。
→ 22:55~22:56（**R44~R48 那批文档的第一次真提交**：`scripts/` 无新增，但 `evidence/staged_list_225525.txt` + `evidence/staged_cred_gate_225541.txt` 两只**索引侧取证**落盘，随后 `git add` 逐只点名 171 只 → `commit 75be24f`（git `%ci` 读数 = 22:56:09），见下节"提交轮"。**"第一次"只在这一定语下成立**：本分支在它之前已有 9 只未推送提交，`040af28` 本身就提交了 68 只 ⇒ 无限定语的"第一次真提交"是错的）
→ 22:59~23:04（第 7 代同步 `r49final` 跑完 ⇒ 用 `scripts/land_r49_evidence.py` 落 **+9 只** r49 凭证（47,072 B 可现跑求和复算）+ 本代派生器与差集器。**那句"23:04:23 落地"在仓库里查无载体**：`land_r49_evidence.py` 的 `LANDED_AT` 只打 stdout 未落盘，9 只文件因 `copy2` 保留源 mtime 而全在 22:59:56~23:00:57 ⇒ 该时刻只是排查记录 §37.3 的叙述。派生器 `derive_r49.py` 首跑在 `r48_listdiff.py` 那一个作业上 **ABORT**（`zsynctest8` 0 命中）⇒ 守卫真的响过，处置见下节）
→ **09-24 00:0x**（R49 复查报告的处置轮：本目录 +1 只 `evidence/r49_parse_check.txt`（00:07:22 **复跑**落盘，不是 23:00:10 那一次的原始副本），报告原文落 `hardware/20260924_R49复查报告原文.txt`（在 `hardware/` 下、不在本目录）⇒ 这一格只动文件、**未冻清单**，冻结链在 00:5x 那几遍，见下表 gen 12 与「末版的三个数」段）
→ **09-24 00:3x~00:4x**（**第 8 代同步 `r50final` 跑完** ⇒ 本代入档 = `scripts/` **8 只**（5 只派生工具 `sync_r50.py`/`r50_upload.ps1`/`chk_r50.ps1`/`r50_cutoff_delta.py`/`r50_listdiff.py` + 派生器 `derive_r50.py` + 落地器 `land_r50_evidence.py` + 尾件取证件 `r50_roundtrip.py`）+ `evidence/` **13 只**（10 只 r50 凭证由 `land_r50_evidence.py` 00:40:45 落盘、合计 50,406 B，落地时刻这次**有载体** = `evidence/r50_land_log.txt`；尾件 `r50_roundtrip.txt` 另由一次性脚本在 00:44:44 落盘，载体 = `evidence/r50_extra_land.txt`）。只数由 `ls -1 evidence/r50_* | wc -l` 这类命令现跑点数即可复算（本行那一遍的输出没有单独立载体 ⇒ **不要**把它读成"某时刻的落盘读数"，同 `FreqErr.md` ht305 段 ㉗ 那格口径）。
  派生这一遍**五只作业首跑全 `DERIVED`、零 `ABORT`**（上一代的教训已经进替换表：给差集器的那一栏不再塞解包根），派生完另加一条 `LEFTOVER_CHECK` 现读"本代字节里还有没有 `r49final`/`zsynctest9`/`第 7 代`" ⇒ 五只均 `CLEAN`。
  包名日期这一代起跟日历走：`zizhao_20260924_r50final`（第 1~7 代都写在 09-23 内，包名里的日期曾经长期等于"同一天"））
→ **09-24 02:1x~04:2x**（**三次提交轮（#4 `c752d0e` / #5 `9a8ac16` / #6 `662fd7e`）的取证 + 第 9 代同步 `r51final`** ⇒ 本目录盘上"有、gen 12 清单没记"的 = **59 只**（`evidence/` 51 + `scripts/` 8；其中 `r51_*` 命名 **25 只** = `evidence/` 17 + `scripts/` 8，其余 34 只是三次提交轮的名单/差集/门/阳性对照/树复扫与两只 `*_try1_*` 失败载体；数取 04:2x 现跑 `verify_manifest.py` 的全量名册，**不再靠本行手点数**——本行那份分类就是它自己说的"手写一次性快照"），另有 **3 只在册件被改写** = 本 README + `scripts/ps1_bom_scan.py` + `scripts/verify_manifest.py`，后两只是 gen 13 那两处工具修正，见下表 gen 13 那格）
  - 第 9 代**第一次真的按新口径派生**：`derive_r51.py` 的作业表把**落地器与尾件回扫**两只一起进表（上一代这两只是表外手抄的 ⇒ "派生器覆盖全部作业"这句话当时不成立）。首跑在作业 5 **ABORT**（替换表里塞了 `r50_listdiff.py` 根本不包含的 TOP 串），前 4 只已写盘 ⇒ 处置不是删（本会话不动删除），而是给派生器加 `SKIP_IDENTICAL`：**目标已存在且与本代派生结果逐字节等 ⇒ 打 `SKIP_IDENTICAL` 放行，不等 ⇒ ABORT**。于是"重跑同一份派生"从破坏性动作变成可复跑的单入口，那 4 只也被**逐字节证明**是本代产物而不是上一遍残留。
  - 本代另两处自抓：① `chk_r51.ps1` 之前的一版差集器 `index_vs_list_r50f.py` 首跑 `rc=1`，因为它去 match 一行**只存在于控制台**、不在名单文件里的汇总行（`MOD=… KEEP=…`）⇒ 失败载体逐字进档 `evidence/index_vs_list_try1_035550_headline_regex_bug.txt`；② 尾件落地器 `extra_land_r51.py` 首跑 `rc=1`，因为它凭"**仓库里与抓回件逐字节相同的只有一只**"这个我凭空设的前提写断言，实测 **28 只**（工作树源头 1 + 备份根 27）⇒ 按规则 (81) 复跑生成失败载体 `evidence/r51_extra_land_try1_wrong_twin_premise.txt` + 那一遍的脚本本体 `..._try1_script.txt`（不是手抄），断言改成**按目录段判**（`OUTSIDE_BACKUPS=0`）。
→ **09-24 04:3x~05:4x**（gen 13 冻结之后的三段：**① 5 只 r51 侧复跑/失败载体**（04:35:56 两只 `*_try1_*` + 04:36:03/04:36:37 两只 `verify_manifest` 复跑 + 04:38:22 派生复读，另 04:13:40/04:14:18 两只本就在 gen 13 内）、**② gen 14 冻结**（05:33:35 ⇒ `TOTAL 247 / TOTAL_BYTES 724,901 / BOM 44`）、**③ 第 10 代同步 `r52final` 全套 + gen 15 冻结**（05:42:29 ⇒ `TOTAL 270 / TOTAL_BYTES 829,336 / BOM 50`）⇒ 相对 gen 13 的 241 只，本目录净入档 **+29 只**（+6、+23 两批，逐名见下表 gen 14 / gen 15 两格）
  - **两批差集的名册不再手点**：`os.walk` 现读"mtime ∈ (上一代清单时刻, 本代清单时刻]" ⇒ gen 13→14 = **6 只、六只都 `birth == mtime`**（即一批里没有任何"覆写在册件"）；gen 14→15 = **24 只被触碰 = 23 只新 + 1 只覆写在册件**，那一只正是 `evidence/ps1_bom_scan.txt`（`birth=09-23 10:38:11`、`mtime=09-24 05:40:11`）⇒ 这就是 gen 13 那格新加的 `OVERWROTE=… md5:…` 自述行的**又一次兑现**：编码体检按设计盖自己那只，只数不变、字节变，`MISMATCH` 只能靠重冻闭合。
  - **三处过期序数是这一格抓出来的**（都不是工具报的，是我抄自己旧话时报的）：本文件首行原写"八轮全量同步"，**自第 9 代 `r51final` 起就已过期**（gen 13 那格登记了那次同步、首行没跟着改）⇒ 本轮改成"十轮"；"清单世代"标题里那句"本表到 13，同步表到 9"同样过期 ⇒ 改成"本表到 15，同步表到 10"；"本归档明确没有做的事"里那句"最新一代是 `zsynctest10`"也晚了**两代** ⇒ 改成 `zsynctest12`。⇒ 与 `FreqErr.md` 台账"引用即复跑"同族：**概览行/标题里的那种序数不会有任何工具报警**，它只在被下一次抄写时暴露。
  - **第 10 代 `r52final` 的读数（逐字取自 `evidence/r52_*.txt`，不是回忆）**：截止拷贝 05:38:05、zip 成型 05:38:10 = **1,773,469 B / md5 `8cb16745146d17e0c509ce49d813119c`**；远端 05:38:23 那只 **同 size 同 md5**、`EXTRACT_OK=True`、`REMOTE_FILES=435 / REMOTE_BYTES=4,367,190 / REMOTE_FORBIDDEN=0`、`REMOTE_AGGREGATE` 与 `LOCAL_AGGREGATE` 逐字符等（`d9b071fc…23bc317`，64 位十六进制 ⇒ 落地器的前置断言过了才打 `AGGREGATE_MATCH=YES`）；双向差集 `LOCAL_LINES=435 / REMOTE_LINES=435 / ONLY_IN_LOCAL=0 / ONLY_IN_REMOTE=0`；包 ↔ 工作树（05:38:48）`staged=435 / identical(sha256 逐字节等)=435 / changed=0 / deleted=0 / new=0`；回扫（05:39:11~05:39:13）`BYTE_EQUAL_TO_WORKTREE=True` + `PROV_PASS_HITS_REMOTE=1` ⇒ `VERDICT=REMOTE_CARRIES_PLAINTEXT`，同批阴性对照 `CONTROL_LANDER_HITS=0`；尾件落地器（05:40:01）`BYTE_TWINS_IN_REPO=28 / SOURCE=hardware/zizhao-esp32s3/main/provision_ap.c / BACKUP_COPIES=27 / OUTSIDE_BACKUPS=1`、`FETCH_NAME_LEAKED_INTO_REPO=0`、12 只 r52 载体明文复扫全 `hits=0`。
  - 派生侧：`derive_r52.py` 的 7 只作业（比上一代多一只 `extra_land_rNN.py` ⇒ 上一代那只尾件落地器**从未作为可复跑脚本进 `scripts/`**，只以正文形式留在 `evidence/r51_extra_land_try1_script.txt`）首跑全 `DERIVED`、**零 ABORT**；`LEFTOVER_CHECK` 那五个串（`r51final` / `zsynctest11` / `第 9 代` / `r51_` / `R51`）本代**已从"只打印"改成"命中即 ABORT"**，跑完 7 只均 `CLEAN`，七只 `.py` 另过 `ast.parse`（不在归档目录里跑 `py_compile`）。

## 清单世代（**单一权威源**：本目录只有一份末版 `MANIFEST.txt`，历世代只在这里登记。本表的序数一律读作"清单 gen N"，与排查记录 §36.1 那张表的"同步第 N 代"是**两套序数**（本表到 15，同步表到 10），同页并存时不要混引）

| 清单 gen | 时刻 | 只数 | 为什么又跑一次 |
| --- | --- | --- | --- |
| 1 | 10:36:41 | 49 | 首批把三代脚本 + 取证件收进来 |
| 2 | 10:38:51 | 52 | 补门复验脚本、清单生成器、编码体检脚本 |
| 3 | 11:06:14 | 58 | 补 `r43_r44_listdiff.txt`（那只在记忆中被我误登记过"已入档"）+ README/清单本批改动 |
| 4 | 11:36:40 | 59 | 收口末复跑"包 ↔ 现状"差集（11:34:01）后把第二代读数进档 |
| 5 | **不可复算**（"只留末版清单"这条口径把 gen 5 自己的时刻覆写掉了；git 里最新一版是 gen 4 的 11:36:40，gen 5 从未入库） | **61** | 把**提交前索引侧明文门**的脚本与其输出进档 ⇒ 门可原地重跑 |
| 6 | 12:00:02 | **61**（只数与 gen 5 同集，11:53 现跑 `find -type f` = 62 只含清单自身 ⇒ 无新增只，只有字节变） | 本节把"两道门"订正成**三道口径**、`evidence/`+`gate/` 两行补登新文件，并给编码体检补了"退出码非 0 但文件已写出"的修法 ⇒ 按上面那**三次动作**的顺序重跑齐 |
| 7 | 12:07:57 | **65** | 落 R45 空上下文复查的三条工具侧修订：**清单复核器** `scripts/verify_manifest.py`（P0-2"快照两字没有执行者"）、**门的阴性对照** `gate/cred_gate_selftest.py` + 其输出（"从没证明门会响"）、门复验输出改成**带时刻、不覆写上一代**（P1-3） |
| 8 | 本目录末版（时刻现读 `MANIFEST.txt` 首行） | 只数**现读 `MANIFEST.txt` 的 `TOTAL` 行**（本批净增 **+13**：r46 的 `scripts/` 4 只 + `evidence/` 9 只；其余增量都是"三次动作"自己的输出） | 第 4 代同步 `r46final`（12:09:14~12:10:40）跑通后把这些 r46 脚本副本与凭证进档 ⇒ 第 4 代的读数从此在仓库里可复算，不再只在 `%TEMP%` |
| 9 | 12:48:05 那次 `verify_manifest.py` 把它判成 **`MANIFEST_STALE`**（点名 `gate/staged_cred_gate.py`、`scripts/collect_ht305_sync.py`）⇒ 本代是**那次漂移的补课**：末版时刻现读 `MANIFEST.txt` 首行 | 只数**现读 `MANIFEST.txt` 的 `TOTAL` 行**（gen 8 = 80 ⇒ 本代末版现读，不写死在这里，**差额也不在这里给序数**——门输出按时刻命名、本代跑出的只数会随重跑增加）。相对 gen 8 **新落入档的**逐名：`scripts/land_r45_report.py`（12:25:23，落上一轮复查报告用的脚本，它落在 gen 8 那份清单**之后** ⇒ gen 8 没记它）、`evidence/ht305_sync_gate_130414.txt`（复制前候选门 13:04:14 复跑）、`evidence/cred_gate_negative_control_130440.txt`（"空候选即 ABORT"那道守卫的阴性对照留档）、`evidence/manifest_gen_log.txt`（本代新增的**代次日志**，见下面那段）、以及**本代这几轮自己带的时刻门输出**（`evidence/cred_gate_recheck_<HHmmss>.txt`，现读目录里 mtime 最新那只 = 末版清单引用的那只）；余下增量都是既有只的字节变化——**多少只不在这里点名**：gen 8 那份清单已被末版覆写，"哪些只只是字节变了"这一层**不可复算**，代价同 gen 5 那一格（而这一层从本代起由代次日志兜住） | 落 R45 复查剩下的工具侧三条 + 本轮自查的一条：**① 门 `PATTERNS` 由"按代枚举"改成跨代通配**（否则 `r46_*` 一只不在名单 ⇒ 扫 0 只也打 `DIRTY 0`）；**② 候选为 0 硬 `ABORT` + `PER_PATTERN`/`DEAD_PATTERNS` 两行读数**（13:04:14 现跑：76 只候选 / 脏 0 / 21 族活 + 2 族死）；**③ 5 只打印非 ASCII 的门/归档工具统一加 `sys.stdout.reconfigure`**；**④ 上一代（gen 8）落完之后我又改了 7 只 .py**，那两次编辑发生在门与清单之间 ⇒ 门没覆盖最新字节，而这件事是 `verify_manifest.py` **自己报出来的**，不是我记得才去查的 |
| 10 | 末版时刻现读 `MANIFEST.txt` 首行 | 只数现读 `MANIFEST.txt` 的 `TOTAL` 行；相对 gen 9 的差集**已在 13:53:14 逐名点名**（`evidence/arch_delta_r47_vs_gen9.txt`：`NEW=17 / GONE=0`，其中 `MANIFEST.txt` 与代次日志两只按设计不入清单 ⇒ 入档 +15），随后必然再加的那几只（差集证件自身、`scripts/arch_delta_r47.py`、为它们重跑的门输出）**不在这里给序数** | 第 5 代同步 `r47final`（13:45:35~13:49:13）跑通 ⇒ 12:09 之后那半天攒下的字节第一次上服务器；顺带把本代自查出的"派生会把缺陷一起派生过来"（`chk_r4*` 对着一只**不存在**的文件照样打 `PARSE_ERRORS=0`）修成"目标不存在即 ABORT + 副本↔原件 md5 等式写进输出" |
| 11 | 末版时刻现读 `MANIFEST.txt` 首行 | 只数现读 `MANIFEST.txt` 的 `TOTAL` 行；相对 gen 10 的**入档动作**已在上面"建立时刻"末尾两格逐名点名（21:39~21:40 的 4 只 = 门驱动 + 三轮对照输出；21:53:40 的 18 只 = r48 的 6 只 `scripts/` + 12 只 `evidence/`），**本行不再给硬数**：代次日志（`evidence/manifest_gen_log.txt`）按设计不入清单，而"清单自身 + 门输出 + 本 README"这三只必然在门之后长出来 ⇒ 差额只以 `TOTAL` 行与代次日志末行互核为准 | 第 6 代同步 `r48final`（21:46:16 读盘 ~ 21:49:21 差集）跑通 ⇒ 13:45:35 之后那整晚的字节（含 §三十五 只读取证、两只 `hardware/20260923_重连COM14*`）第一次上服务器；顺带两件事进档：**① 索引侧明文门补上"命中即 `exit 1`"**（此前它只打印 `VERDICT` 不改退出码 ⇒ "靠我读输出"没有执行者）+ 它的 `.ps1` 驱动与**两轮阴性对照**输出；**② 本轮新写的差集器自己造了一次 `287/287` 假差集**（`rstrip(b'\r')` 漏剥 `\n`），修法留在 `scripts/r48_listdiff.py` 的注释里而不只留在文档里（见排查记录 §36.3 与 `FreqErr.md` ht305 段 ㉑） |
| 12 | 末版时刻现读 `MANIFEST.txt` 首行（本代 = 09-24 00:54 起那几遍，逐遍时刻登记在本节下面那段，不在表格里写死） | 只数现读 `MANIFEST.txt` 的 `TOTAL` 行；相对 gen 11 的**入档动作**已在上面"建立时刻"末两格逐名点名（09-24 00:0x 处置轮 +1 只 `r49_parse_check.txt`；00:3x~00:4x 第 8 代 `scripts/` 8 只 + `evidence/` 13 只），**本行不给硬数**，差额以 `TOTAL` 行与代次日志末行互核 | 把 **第 7 代同步 `r49final`（22:59:52 读盘 ~ 23:00:57 差集）+ R44~R48 那批文档的第一次真提交（`75be24f`）+ R49 空上下文复查报告 12 条的处置轮 + 第 8 代同步 `r50final`（00:38:42 读盘 ~ 00:44:00 尾件）**这四件事冻进归档，判据仍是那条链跑完并且 `verify_manifest.py` 给 `VERDICT=MANIFEST_STILL_TRUE / rc=0` —— **本代已按该判据跑通**（第一遍 00:54:42 那份清单 `ROWS=174 / MISMATCH=0 / MISSING=0 / UNLISTED=0` 且 `rc=0`；因本 README 在清单之后又被改写 ⇒ 末版是随后那一遍，时刻现读首行）。本代另外第一次真的执行了三件**上一代只是"改了脚本"**的东西：**① 归档后明文门的新守卫**（环境缺失即 `ABORT`、`FILES_SCANNED=0` 即 `ABORT`、末行 `VERDICT` + 命中即 `exit 1`）——R49 处置轮改完到 00:01:20 那批复查读数之间它一次都没跑过，本代冻结链才是它的第一个载体；**② `land_r50_evidence.py` 的聚合行前置断言**（缺行 ABORT + 两侧必须是 64 位十六进制才允许打 `AGGREGATE_MATCH`）与它自己写下的 `evidence/r50_land_log.txt`（第 7 代那句"23:04:23 落地"就是因为没有这只文件才成为无载体时刻）；**③ 派生器的 `LEFTOVER_CHECK`**（派生完现读本代字节里还留不留上一代的包名/解包根/序数）。**④ 还有一条新口径**：本代第一次把远端**解包后**的那只带明文源文件 scp 回本机再扫（`scripts/r50_roundtrip.py` ⇒ `evidence/r50_roundtrip.txt`），这样"远端那份带明文"就不再只靠"包 == 工作树"的传递成立——同批带一条**阴性对照**（同一把尺子在落地器字节上数出 0） |
| 13 | 末版时刻现读 `MANIFEST.txt` 首行 | 只数现读 `MANIFEST.txt` 的 `TOTAL` 行；相对 gen 12 的**入档动作**已在上面"建立时刻"末格点名（59 只未在册 + 3 只在册件被改写），**本行不再手点** | 把 **三次提交轮的取证（#4 `c752d0e` 02:55:09 / #5 `9a8ac16` 03:28:12 / #6 `662fd7e` 04:01:5x，均未 push）+ 第 9 代同步 `r51final`（04:05:53 读盘 ~ 04:09:48 尾件回扫）**冻进归档，判据仍是那条链跑完并且 `verify_manifest.py` 给 `VERDICT=MANIFEST_STILL_TRUE / rc=0`。本代同时吸收 gen 12 收口时挂下的**两处工具修正**（排查记录 §38.9 末段那条义务清单）：**① `verify_manifest.py` 的 `UNLISTED` 汇总行不再截断名单**（旧版印 `UNLISTED=12` 而名单只给 10 只 = 半截取证，缺陷恰好藏在"看起来完整"的地方 ⇒ 现在逐行给全表，且汇总行自己说 `shown=/total=`）；**② `ps1_bom_scan.py` 由"只报不响"改成 `RISKY_PS1>0` 即 `exit 1`**，并新增 `OVERWROTE=… md5:…` 一行**自述它覆掉了上一版**（09-24 03:5x 实测：它按设计覆写在册件 `evidence/ps1_bom_scan.txt` ⇒ 当场把 `MISMATCH` 顶成 1，而"我覆掉了哪一版"当时没有任何执行者说得出来）。**③ 本代另有一条新口径落进脚本本体**：派生器 `derive_r51.py` 的 `SKIP_IDENTICAL`（目标已存在且逐字节等 ⇒ 放行、不等 ⇒ ABORT），使"重跑派生"不再是破坏性动作 |
| 14 | 09-24 05:33:35（现读 `MANIFEST.txt` 首行；链条三遍时刻见「末版的三个数」段末三行） | **247 / 724,901 B / BOM 44**（相对 gen 13 的 241 = **+6**，逐名：`evidence/r51_postfreeze_verify_try1_043556.txt`、`…_try1_script_043556.txt`、`evidence/r51_verify_manifest_043603.txt`、`…_043637.txt`、`evidence/r51_derive_reread_043822.txt`、`evidence/cred_gate_recheck_053315.txt`；六只 `birth == mtime` ⇒ 本批**零覆写**） | 把 gen 13 冻结**之后**才落盘的 5 只 r51 侧证件（一次 `verify_manifest` 首跑失败载体 + 它的脚本本体、两遍复跑读数、一遍派生复读）连同本代门输出一起冻住 ⇒ **本代零新同步代码、零串口动作**，是一次纯盘上/清单动作（R44~R51 那八批的共同特征） |
| 15 | 09-24 05:42:29（现读首行） | **270 / 829,336 B / BOM 50**（相对 gen 14 = **+23**：`r52_*` 命名 `scripts/` 9 + `evidence/` 13 中的 12 只新证 + 门输出 `cred_gate_recheck_054012.txt`；另 **1 只覆写**在册件 = `evidence/ps1_bom_scan.txt` ⇒ 只数不含它、字节算它。本代实测 `ROWS=270 / MISMATCH=0 / MISSING=0 / UNLISTED(盘上有、清单没记)=0`，且代次日志末行 `09-24 05:42:29\t270\t829336\t50` 与清单汇总三行逐字段互核 `⇒ OK`） | 把 **第 10 代同步 `r52final`（05:38:05 截止拷贝 ~ 05:40:01 尾件落地器）** 冻进归档；本代第一次把**尾件落地器本体** `scripts/extra_land_r52.py` 写进派生作业表 ⇒ "落地器只在 `%TEMP%`、下一代无法复跑"这条从 gen 9 挂到 gen 13 的残留已闭合。判据不变：那条链跑完 + `verify_manifest.py` 给 `VERDICT=MANIFEST_STILL_TRUE / rc=0` |

末版的 `TOTAL / TOTAL_BYTES / BOM_FILES` 三个数**只以 `MANIFEST.txt` 末三行现读为准**（本 README 若在其后被编辑，清单里那一行的 md5 就过期，
重跑顺序固定为"**改内容 → `scripts/ps1_bom_scan.py` → `gate/run_cred_gate_recheck.ps1 <打包截止时刻>` → `scripts/gen_manifest.py` → `scripts/verify_manifest.py`**，
**三次动作 + 一次复核、不是一次**：编码体检与门各自都要往 `evidence/` 落一只文件，落在清单之前才会被清单记进 md5、落在门之前才会被门扫过；最后那只复核器给的才是"冻住"判据（`VERDICT=MANIFEST_STILL_TRUE / rc=0`）。
gen 9 那一批按这个顺序跑了**五轮**（11:58:27~11:58:28 / 12:07 / 12:19~12:21 / 13:07:59~13:09:00 / **末轮 = gen 9 收口**，其时刻现读 `MANIFEST.txt` 首行，不在这里写死）。
本代（gen 11）把这条链跑了**两遍**：22:21:14/22:21:24/22:21:37 第一遍（编码体检 → 门 → 清单），随后又改了本 README ⇒ 22:22 那一遍重来，末版时刻与只数**现读 `MANIFEST.txt` 首行与 `TOTAL` 行**（这里不写死，理由见上一条括号）。
gen 14（09-24 05:33）**一遍跑通**：05:33:0x 编码体检 → 05:33:15 门（`cred_gate_recheck_053315.txt`：`FILES_SCANNED=248 / PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0 / VERDICT=CLEAN` + 驱动 `PY_EXIT=0`）→ 05:33:35 清单 `TOTAL=247`；本 README 在那一代清单**之前**没动（`mtime=04:32:33` < `05:33:35`）⇒ 这一代的 `MISMATCH` 一次为 0，不需要重跑。
gen 15（09-24 05:42）同型：05:40:11 编码体检（覆写在册件那只 ⇒ `BOM_FILES` 44 → 50）→ 05:40:13 门（`FILES_SCANNED=271`，两计数仍 0、`VERDICT=CLEAN`、`PY_EXIT=0`）→ 05:42:29 清单 `TOTAL=270` → `verify_manifest.py`（**不带管道**那一次）`rc=0 / VERDICT=MANIFEST_STILL_TRUE`。
本 README 是在 05:42:29 那份清单**之后**才改的 ⇒ 它自身那一行的 md5 已过期，且这次编辑没触发重冻：**按上面那条口径，本文件首行时刻之后的编辑交给下一代清单收**（这与 gen 12/13 的处理完全相同，不是新漏洞）。
gen 12（09-24）同样跑了不止一遍，且**第一遍的清单字节已被第二遍覆写**：00:54:19/00:54:28/00:54:42（`TOTAL=174`）→ 改本 README → 00:56:15/00:56:16/00:56:16（`TOTAL=175`）→ 再改本 README（补"提交轮 #2"那一节）→ **末版 = 随后那一遍，时刻现读首行**。两遍的 `TOTAL/TOTAL_BYTES/BOM_FILES` 都还在 `evidence/manifest_gen_log.txt` 里 ⇒ **本代起"代内重跑覆写掉上一遍"不再等于丢失**（这正是代次日志要付的账）。
每次门都比清单多扫 1 只是**结构性的**（清单按设计不自列 `MANIFEST.txt`，门只排除它自己的输出）⇒ 这个 `+1` 历代相同，不要当漂移读。
上一条表格里 gen 5 那一格的"**不可复算**"就是这条口径的**代价**，先算清再沿用：目录里只留一份末版清单 ⇒
中间世代的**首行时刻**必然被后一次覆写（只数与动因还能靠本节叙述留住）。**该代价已于本代（gen 9）用脚本消掉**：
`gen_manifest.py` 现在每跑一次就往 `evidence/manifest_gen_log.txt` **自己追加**一行 `时刻 / TOTAL / TOTAL_BYTES / BOM_FILES`
⇒ 从 13:1x 那一次起"上一代有几只"是机器记的，不再靠本节手写；**gen 1~8 的只数不回填**（回填等于拿"从本节叙述里 recovered 的数"冒充"当时现算"）。
`verify_manifest.py` 同时多了一条交叉核对：**日志末行必须等于本清单的汇总三行**，不等就 `MANIFEST_STALE`。
另加一条**派生字节守卫**（本代自己撞出来的）：我用 `py_compile` 做语法检查，它把两只 `.pyc` 写进了 `scripts/__pycache__/`，
而 13:15:42 那次清单**照单全收**（`TOTAL=88` 里就含这两只，16,088 B）⇒ 现在 `gen_manifest.py` 见到 `.pyc`/`__pycache__` 直接 **`ABORT` 并点名**。
阴性对照已跑：临时放一只假 `.pyc` ⇒ `ABORT: 归档里有 1 只派生字节…scripts/__pycache__/gen_manifest.cpython-314.pyc`、`rc=1`，随后删净。
**通用口径**：语法检查**不许**在归档目录里跑（用 `python -c "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())" <file>`，它不落任何文件）。
顺带一条实测：`ps1_bom_scan.py` 在 GBK 控制台下会因输出里的 `⇒` 崩在**最后那行 `print`**，
而 `evidence/ps1_bom_scan.txt` **早已在崩之前写出**（11:57:51：退出码非 0、文件却是新的）⇒ 只看 `$LASTEXITCODE` 判"没跑成"会误判，
判据是**那只文件的首行时刻**。此缺陷已在脚本里用 `sys.stdout.reconfigure` 修掉。
清单头部**不再**枚举历世代只数：那种硬编码在同一批里连跑两遍就漂了（11:36 / 11:47 两次实测），故代次叙述只留本节。
建立原因：**R44 终态复查报告**（本目录不存这只文件；报告原文在
`hardware/20260923_R44终态复查报告原文.txt`）"我没能验证的清单"末条指出：
本轮全部可复算证据只活在 `%TEMP%`、仓库内无副本 ⇒ 下一轮必然再报一次"锚点不可复算"。
逐条处置见 `hardware/20260919_墨水屏点屏排查记录.md` **§33.5**（采纳该建议这一条）。

## 目录里有什么

| 子目录 | 内容 | 说明 |
| --- | --- | --- |
| `scripts/` | **十代**同步工具的**全部**脚本副本 | 按文件名前缀分代：`ht305_*` + `build_sync.py`/`build_zip.py`/`expected*.py`/`pw_*.py` = **第 1 代**（tar 通道，已判为坏通道）；`sync_r44.py` + `r44_upload.ps1`/`r44_verify2.ps1` + `probe_zip_vs_head*.py` = **第 2 代**（zip + 聚合哈希，但脚本里有 `Remove-Item`、时间戳不落盘）；`sync_r45.py` + `r45_upload.ps1` + `chk_r45.ps1` + `r45_cutoff_delta.py` = **第 3 代**（当前口径的确立：双端"存在即拒"、每条读数带时刻）；`sync_r46.py` + `r46_upload.ps1` + `chk_r46.ps1` + `r46_cutoff_delta.py` = **第 4 代**；`sync_r47.py` + `r47_upload.ps1` + `chk_r47.ps1` + `r47_cutoff_delta.py` = **第 5 代**；`sync_r48.py` + `r48_upload.ps1` + `chk_r48.ps1` + `r48_cutoff_delta.py` + `derive_r48.py` + `r48_listdiff.py` = **第 6 代**；`sync_r49.py` + `r49_upload.ps1` + `chk_r49.ps1` + `r49_cutoff_delta.py` + `r49_listdiff.py` + `derive_r49.py` = **第 7 代**（本代派生器多了那条**分后缀**编码守卫）；`sync_r50.py` + `r50_upload.ps1` + `chk_r50.ps1` + `r50_cutoff_delta.py` + `r50_listdiff.py` + `derive_r50.py` + `land_r50_evidence.py` + `r50_roundtrip.py` = **第 8 代**（派生器再多一条 `LEFTOVER_CHECK`：派生完现读本代字节里还留不留上一代的包名/解包根/序数；尾件 `r50_roundtrip.py` 不是同步工具，是把远端**解包后**的那只源文件 scp 回本机再扫的取证脚本，明文只计数、绝不落仓库）。`sync_r51.py` + `r51_upload.ps1` + `chk_r51.ps1` + `r51_cutoff_delta.py` + `r51_listdiff.py` + `derive_r51.py` + `land_r51_evidence.py` + `r51_roundtrip.py` = **第 9 代**（8 只；派生器首跑在作业 5 `ABORT` ⇒ 见「建立时刻」那格那条 `SKIP_IDENTICAL`；**本代的尾件落地器 `extra_land_r51.py` 未进 `scripts/`**，只以正文留在 `evidence/r51_extra_land_try1_script.txt`）；第 10 代 = 上一代那 8 只的同名派生（`r51`→`r52`）**＋ `extra_land_r52.py`** ⇒ **9 只**，本代起"落地器本体可复跑"这句话对**两只**落地器同时成立。第 4~10 代一律**逐字从上一代派生**（只换包名 / 解包根 / 凭证前缀），派生器对每个替换断言命中数、命中 0 即 `ABORT`；第 6 代起**派生器与差集器本身也入档**（否则下一代只会派生脚本、不会派生"为什么这么派"）。`chk_r47.ps1`/`chk_r48.ps1`/`chk_r49.ps1`/`chk_r50.ps1` 这四代跑完都留 `PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / MD5_BOTH=` 三个读数（见 `evidence/r47_parse_check.txt`、`evidence/r48_parse_check.txt`、`evidence/r49_parse_check.txt`、`evidence/r50_parse_check.txt`；**r49 那只是 09-24 00:07:22 复跑的载体**，第 7 代当场那一次没落盘；r50 这一代在跑完当场就落，不再等下一代补）；另有 `land_r49_evidence.py` / `land_r50_evidence.py`（凭证落地器：目标已存在即拒写 + 含明文即拒收 + 落盘后逐字节读回；**第 8 代起它还会把自己的 `LANDED_AT/FILES/BYTES` 写成 `evidence/r50_land_log.txt`**，并把两侧聚合行读回来断言非空且为 64 位十六进制，才允许打 `AGGREGATE_MATCH=`）与 `make_staged_list.py`（提交轮逐只点名清单生成器，TEMP 原件叫 `make_staged_list_r50.py`，那个 `r50` 是**提交轮序号**、不是同步代次 ⇒ 入档时去掉了这个误导后缀） |
| `evidence/` | 每代跑出来的原始 stdout / stderr / 计数文件 | 含 `r43_r44_listdiff.txt`（r43→r44 逐名差集，`T=08:32:06`、`+1 只 / −0 只`）、`r44_verify2.txt`（第 2 代远端读数）、`r45_verify.txt` 与 `r46_verify.txt`（第 3/4 代远端读数，`REMOTE_*` 行）、`r45_local.txt` / `r46_local.txt`（截止时刻 + 载荷指纹）、`r45_scp_err.txt` / `r46_scp_err.txt`（`SCP_EXIT` 落盘）、`r45_cutoff_delta.txt` + `r45_cutoff_delta_gen2_113401.txt` + `r46_cutoff_delta.txt`（包 ↔ 工作树差集，见排查记录 §33.3①/①-b 与 §三十四）、`r46_diff_and_cred.txt`（第 4 代双向差集 + 包内明文复测，**内含一条行尾踩坑登记**）、`r45_local_names.txt` / `r46_local_names.txt` / `r46_remote_names.txt`（两侧名单）、`cred_recount_0822.txt`（口令计数复跑）、`ps1_bom_scan.txt`（本目录自己的编码体检）、`cred_gate_recheck*.txt`（归档后全量明文门，**文件名带时刻**，`FILES_SCANNED=` 行（**不是末行**）就是它自己那一遍扫了几只）、`staged_cred_gate_114414.txt`（提交前**索引侧**明文门）、`cred_gate_selftest_120548.txt`（门的**阴性对照**：证明"脏了会响"）、`manifest_gen_log.txt`（**代次日志**：由 `gen_manifest.py` 自己每代追加一行 `时刻/TOTAL/TOTAL_BYTES/BOM_FILES` ⇒ 末版清单被覆写之后"上一代有几只"仍可读，自 09-23 gen 9 起有行）；**第 5 代 `r47_*.txt` 11 只**（含 14:01:02 补跑的 `r47_parse_check.txt`）与**第 6 代 `r48_*.txt` 12 只**（含 `r48_parse_check.txt`、`r48_listdiff.txt`）各自成套 = `local / local_names / local_names.sorted / probe / scp_err / verify / run_log / cutoff_delta / remote_names / diff_and_cred`（第 6 代多一只 `listdiff`，因为差集器改成一趟跑完三件读数；只数由 `ls -1 r4{7,8}_*.txt | wc -l` 现跑，别照抄本行）；**第 7 代 `r49_*.txt` 9 只**（由 `land_r49_evidence.py` 原样复制，合计 47,072 B 可现跑求和复算；**"23:04:23 落地"那一遍的 stdout 未落盘 ⇒ 时刻无载体**，9 只 mtime 因 `copy2` 保留源值、全在 22:59:56~23:00:57）= `local / probe / scp_err / verify / run_log / local_names / remote_names / listdiff / cutoff_delta`，**09-24 处置轮再 +1 只 `r49_parse_check.txt`**（00:07:22 复跑，承载 `chk_r49.ps1` 那五个键）⇒ 本代 `ls -1 r49_*.txt | wc -l` 现跑 = **10**；**与第 6 代的差别**：`local_names.sorted` 未再派生（第 6 代那只只是把名单排序，本代 `r49_listdiff.py` 内部自己排序 ⇒ 少一只冗余）；另有 `unpushed_plaintext_hist_212353.txt`（未推送提交的**tree 口径**明文普查）、`staged_list_225525.txt`（**提交轮逐只点名清单**：5 只 DROP 各带理由 + 171 只 ADD）、`staged_cred_gate_225541.txt`（那 171 只的**索引侧**门输出，五行、末行 `VERDICT=CLEAN`；**退出码不在那只文件里**，见"三道口径"第 1 条）、与 `staged_cred_gate_2139*_ctrl_*.txt` 三只 = 索引侧门"命中即 `exit 1`"这条改动的**两轮阴性对照**（一轮空索引、一轮故意 stage 带明文的那只）；**第 8 代 `r50_*.txt` 13 只** = 落地器原样复制的 10 只（`local / probe / scp_err / verify / run_log / local_names / remote_names / listdiff / cutoff_delta / parse_check`，合计 50,406 B 可现跑求和复算）+ 落地器**自己写下**的那只 `r50_land_log.txt`（落地时刻这次**有载体**：`LANDED_AT=2026-09-24 00:40:45`）+ 尾件两只（`r50_roundtrip.txt` 由一次性脚本 00:44:44 落，载体 = `r50_extra_land.txt`）。注意 `r50_parse_check.txt` 在第 8 代是**当场就落**的（捕获副本 mtime 00:39:33），不再像第 7 代那样等下一代补载体。**第 9 代 `r51_*.txt` 22 只**（`os.walk` 现点名 = 同步本体 10（`local / local_names / probe / scp_err / verify / run_log / remote_names / listdiff / cutoff_delta / parse_check`）+ 落地器自身 `r51_land_log.txt` + 尾件两只 + **失败载体 4 只**（`r51_extra_land_try1_wrong_twin_premise.txt` 及其脚本本体、`r51_postfreeze_verify_try1_043556.txt` 及其脚本本体）+ **复跑/名册读数 5 只**（`r51_verify_manifest_041340` / `_043603` / `_043637`、`r51_unlisted_full_roster_041418`、`r51_derive_reread_043822`））；**第 10 代 `r52_*.txt` 13 只**（同上一代口径 = 本体 10 + `r52_land_log.txt` + 尾件两只 `r52_roundtrip.txt` / `r52_extra_land.txt` ⇒ **本代零失败载体**，`ls -1 evidence/r52_*.txt | wc -l` 现跑 = 13）。只数口径同上一代：`ls -1 evidence/r5?_*.txt | wc -l` 现跑，别照抄本行 |
| `gate/` | 进门用的明文门 | `ht305_sync_gate.py`（复制前扫 `PROV_PASS` 宏值）、`ht305_sync_gate_ssh.ps1`（DPAPI 取回 ht305 SSH 口令后在内存里比对）、`cred_gate_recheck.py` + `run_cred_gate_recheck.ps1`（归档后复验全量，输出**带时刻**、不覆写上一代）、`staged_cred_gate.py`（提交前只扫 `git diff --cached` 列出的**已 stage blob 字节**，输出另存 `evidence/staged_cred_gate_<时刻>.txt`；**09-23 21:3x 起裁决同时落 stdout 与退出码**：`TOTAL_HITS>0 ⇒ VERDICT=PLAINTEXT_IN_INDEX + exit 1`，此前它只打印、`rc` 恒 0 ⇒ "靠我读输出"没有执行者）、`run_staged_cred_gate.ps1`（它的**驱动**：DPAPI 解 SSH 口令 → 经环境变量喂给门 → 用完立刻 `Remove-Item Env:` → 打印 `OUT=` / `PY_EXIT=` 并 `exit $rc`；**门自己那份文件不含退出码，所以驱动的打印也必须落盘**）、`cred_gate_selftest.py`（**哨兵阴性对照**：不碰任何真口令，用假哨兵走同一个 `scan()`，断言"命中会亮 / 干净不假响 / 排除项真被排掉"） |
| 本目录自有工具 | `scripts/gen_manifest.py`（重生成 `MANIFEST.txt`）、**`scripts/verify_manifest.py`（清单的复核器：逐行拿盘上现状重算，漂了就点名并返回非 0）**、`scripts/ps1_bom_scan.py`（重生成 `evidence/ps1_bom_scan.txt`）、`scripts/collect_ht305_sync.py`（当初的复制器，内含明文门） | 这些脚本让"归档 + 指纹 + 门"整条链路可在**任何时刻原地重跑**，而不是只留一份跑不动的副本 |

## 三道口径（这批复件为什么可信 / 有什么没覆盖）

1. **明文门（三种口径、各自量不同的集合，三次均 0 命中）**：
   - **复制前**：扫 `%TEMP%` 的 47 只候选 ⇒ `CANDIDATES 47 / DIRTY 0`（10:3x）+ SSH 口令门
     `SSH_SECRET_HITS_FILES=0`；
   - **归档后全量**：扫本目录**当时的全部文件**（含门脚本自身与 README/清单，**排除本输出文件**）⇒
     `PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0`，读数落在 `evidence/cred_gate_recheck_<时刻>.txt`
     （从 12:07 起**文件名带时刻、不覆写上一代**，此前那一只叫 `cred_gate_recheck.txt`；
     它的 `FILES_SCANNED=` 行**不是末行**——09-24 起末行是 `VERDICT=CLEAN|PLAINTEXT_IN_ARCHIVE`。这一行是**快照**，且**同一代内每重跑一遍链就多一只带时刻的输出**（gen 12 到本行下笔已有 `…_005428`（175 只）与 `…_005616`（176 只）两遍）⇒ 引用时现读 `evidence/` 里 mtime 最新那只，别引本行）；
     **这一遍有退出码了**：驱动打 `PY_EXIT=0`、`rc=0`，且这句不再靠"我读了输出"——命中即 `exit 1` 是 09-24 加的结构，**它的第一个真载体就是 00:54:28 这一遍**（此前 R49 处置轮改完脚本一次都没跑过）；
   - **提交前索引侧**：只扫 `git diff --cached` 列出的**已 stage blob 字节**（= 真正会进 commit 的那份，不是工作树）⇒
     `TOTAL_HITS=0`，凭证 `evidence/staged_cred_gate_114414.txt`（`FILES_SCANNED=68`，跑于 11:44:14）；
     **同一道门在 22:55:41/42 又跑了一次、这次管的是真提交**：`evidence/staged_cred_gate_225541.txt` ⇒
     `FILES_SCANNED=171 / PROV_PASS_FILES=0 / SSH_FILES=0 / TOTAL_HITS=0 / VERDICT=CLEAN`（**五行，末行就是 `VERDICT`**）。
     此前这里还跟着一个 `PY_EXIT=0` ⇒ **那是错的口径**：那只文件里没有退出码行，退出码只由驱动 `gate/run_staged_cred_gate.ps1` 第 21 行打到控制台，本代又没落 `_ps` 副本 ⇒ 它只能由 `VERDICT=CLEAN` + 脚本自身的退出码逻辑**推得**，不是一行读数（和本 README「目录里有什么」表里 `gate/` 那一行自己那句"驱动的打印也必须落盘"直接矛盾，本轮按那句办：**第二轮提交起 `staged_cred_gate_<t>_ps.txt` 必须存在**）。
     逐只点名清单本身在 `evidence/staged_list_225525.txt`（5 只 DROP 各带理由 + 171 只 ADD）。
     **这一道在 21:3x 之前只打印裁决、不改退出码**（三条 `ABORT` 分支管的是"读不到宏 / 环境变量没设 / 索引为空"，**没有一条管命中数**）
     ⇒ 现在 `TOTAL_HITS>0` 同时给 `VERDICT=PLAINTEXT_IN_INDEX` **和 `exit 1`**，并**当场跑了两轮阴性对照证明它会响**
     （A 轮空索引 ⇒ `ABORT` + `PY_EXIT=1`，**这一轮盘上没有裁决文件**（它写文件之前就退了）⇒ 驱动的打印本身要落盘；
     B 轮故意 `git add` 那只带宏的源文件 ⇒ `FILES_SCANNED=1 / TOTAL_HITS=1 / VERDICT=PLAINTEXT_IN_INDEX` + `PY_EXIT=1`，随后 `git restore --staged` 复原）。
     三只凭证见 `evidence/staged_cred_gate_2139*_ctrl_*.txt`、`…_214001_ctrl_dirty*.txt`（合起来 `PWD_HITS=0`）；叙述见排查记录 **§三十五-④**。
   - **门的阴性对照（12:05:48 新增，补"三门全 0 命中"这句话本身的可信度）**：上面三道的输出全都是"0 命中"，
     而"0 命中"既可能是**真干净**、也可能是**门根本没在看**（正则写错、宏名对不上、秘密读成空串都会静默放行）。
     `gate/cred_gate_selftest.py` 因此不碰任何真口令，改在临时目录里放一只**假哨兵**（`SENTINEL_CANARY_NOT_A_SECRET_7c1f`），
     走**同一个** `scan()` 函数断言四件事：命中会亮 / 干净不假响 / 排除项真被排掉 / 两种口令同计 ⇒
     `SELFTEST_PASS=4/4`，读数落在 `evidence/cred_gate_selftest_120548.txt`。
     这把"0 命中"从**信念**变成**有对照实验支撑的读数**；它证明的是 `scan()` 会响，**不是**今天这些文件干净（那仍由上面三道各自负责）。
   为什么三种都要：只补第 2 次不够——那 47 只候选里若有一只带明文，它已经在 `%TEMP%` 里躺着了；
   只做前两次也不够——**commit 带走的是索引里那份字节，不是工作树的字节**（本机 `core.autocrlf=true` 在案 ⇒ 二者可以不同；
   本轮 11:53 抽查 `done.md`：`git show HEAD:done.md` 与磁盘同为 152,884 B，所以"不同"是**机制**、不是本轮实测到的差异，
   但门要防的是机制，不是这一轮运气）。
   三道的输出都**只打文件名与命中次数**，口令本身全程不落终端、不落盘
   （门脚本按 `#define PROV_PASS` 现读、按 DPAPI 现解后经环境变量传给子进程，不内嵌字面量）。
2. **逐字节复制 + 终态清单 + 清单复核器**：`shutil.copy2`，不做任何转写；`MANIFEST.txt` 逐只记
   `bytes / md5 / 有无 UTF-8 BOM / mtime`，并在头部按 mtime **现算**"门之后还有哪些只被改写过"。
   清单自称"快照"这两个字**有执行者**：`python scripts/verify_manifest.py` 逐行拿盘上现状重算三元组，
   漂移就点名并 `exit 1`（末行 `VERDICT=MANIFEST_STILL_TRUE|MANIFEST_STALE`）。
   它不是摆设——12:0x 首跑就把刚写完的清单判成 `STALE`（`MISMATCH=1 / UNLISTED=3` ⇒ 正是"README 与门输出在清单之后又被改写"），
   重生成后才 `MISMATCH=0 MISSING=0 UNLISTED=0`。**清单只能自证"我列了谁"，不能自证"盘上还是我列的那样"**，后者就是这只脚本的活。
   一条自我打脸的实测要登记在这里：这只**新写的**复核器第一版带了与 `ps1_bom_scan.py` **完全同族**的缺陷
   （输出里的 `⇒` 在 GBK 控制台下崩在最后那行 `print`，12:20:14：判据行已打完、`rc` 却是 1 ⇒ 会被读成"清单漂了"）。
   也就是说"知道这个坑"和"写新工具时不重犯"之间没有桥，除非把判据写成断言（现在已加 `sys.stdout.reconfigure`，
   并把 `TOTAL/TOTAL_BYTES` 汇总行的核对**并入 `VERDICT`**，不再只印一行"不一致"就放行）。
   判"这轮归档是否已冻住"的口径：`verify_manifest.py` 返回 `rc=0` 且 `VERDICT=MANIFEST_STILL_TRUE`；
   此后**再动本目录任何一只文件**都要重跑那三次动作。
3. **编码体检**：`evidence/ps1_bom_scan.txt` ⇒ 归档内 `.ps1` **非 ASCII 且无 BOM 的组合 = 0 只**，
   顺带回答了报告"没能验证 #7"（`r44_upload.ps1`/`r44_verify2.ps1` 的 `nonascii=0` ⇒ 无 BOM 不构成 GBK 风险）。
   "含中文的 `.ps1` 只有某一只"这类**名单**不写在这里：本批 11:5x 给 `run_cred_gate_recheck.ps1` 补中文注释时，
   上一版那句"只有 `r45_upload.ps1`"就已经过时（现读 = 体检表里 `.ps1` 且 `nonascii>0` 的那些只，逐只看 `utf8_bom`）。

## 复算入口（不在本 README 里重述定义）

聚合判据的**可复算定义**钉在 `hardware/20260919_墨水屏点屏排查记录.md` **§31.2**
（逐只 `sha256(相对路径 + 字节)`、剥顶层目录、**单个 LF 字节 0x0A** 连接排序后的摘要、排除包内 `SYNC_MANIFEST.txt`）；
执行者是 `scripts/ht305_agg.ps1`（第 2/3/4 代沿用它）与 `scripts/sync_r45.py` / `sync_r46.py` / `sync_r47.py` / `sync_r48.py` / `sync_r49.py` / `sync_r50.py`（后六只各自在打包时算本地聚合，`sync_r47.py` 逐字派生自 `sync_r46.py`、`sync_r48.py` 派生自 `sync_r47.py`、`sync_r49.py` 派生自 `sync_r48.py`、`sync_r50.py` 派生自 `sync_r49.py`）。
八轮同步各自的载荷与指纹读数分别在排查记录 **§三十一 / §三十二 / §三十三 / §三十四 / §34.8（第 5 代）/ §三十六（第 6 代，含六代汇总表）/ §三十七（第 7 代 + 提交轮）/ §三十八（第 8 代 + R49 处置轮 + 本代冻结链）**。
第 4 代（`r46final`，12:09:14~12:10:40）读数的原始凭证就在本目录 `evidence/r46_*.txt`：
载荷 **233 只 / 3,198,808 B**、包 `1,269,250 B`（`md5 e4d401059215da499d38bf438cbd10a6`）、
`LOCAL_AGGREGATE == REMOTE_AGGREGATE == 6a49c473…b5c1`、`SCP_EXIT=0`、双向差集 `ONLY_IN_*=0`。
**读这两只名单前先看行尾**：`r46_local_names.txt` 是 python 在 Windows 上写的 **CRLF**，
直接和远端 `tr -d '\r'` 出来的名单比 ⇒ 第一次得出 `233/233` 全不同（假差集）。同一坑与处置登记在
`evidence/r46_diff_and_cred.txt` 正文里，两侧都归一到 LF 之后才是 `ONLY_IN_*=0`。

第 5 代（`r47final`，13:45:35~13:49:13）凭证在 `evidence/r47_*.txt`：载荷 **261 只 / 3,379,481 B**（`git ls-files -c` ∪ `-o --exclude-standard` = 264 命中，`dupes=0`，扣黑名单 3 只 ⇒ 261，copy 失败 0）、
包 **1,349,354 B / md5 `c15f614ea3c087a6f879f5bc3be2a4e5`**、262 条 entries（第 262 只是包内清单）、utf8-flagged 54、
**`LOCAL_AGGREGATE == REMOTE_AGGREGATE == 83efb6fe…e636`**（13:45:38 本地 / 13:47:04 远端）、`SCP_EXIT=0`（13:47:01）、
`REMOTE_FILES=261 / REMOTE_BYTES=3379481 / REMOTE_FORBIDDEN=0`、双向差集 `ONLY_IN_LOCAL=ONLY_IN_REMOTE=0`（13:47:49，
**前置行尾读数已随证件一起落盘**：`r47_local_names.txt` CRLF=261 裸LF=0、`r47_verify.txt` CRLF=284 ⇒ 两侧剥 `\r` 后才比，这是 (56) 那条规矩的**第一次按口径执行**而不是事后补），
包内明文 `provision_ap.c` **1 只 / 261 只内容文件**（包内条目 262，多的那只是清单；与第 4 代那句 `1/233` 同口径，**分母是内容文件、不是条目**）。包 ↔ 工作树差集（13:48:04，`evidence/r47_cutoff_delta.txt`）=
**260 只逐字节等 / 1 只改 / 0 删 / 0 新增**，那 1 只点名 = `hardware/ht305_sync/scripts/chk_r47.ps1`
⇒ 截止时刻 13:45:35 之后我在 13:46 给它补了 UTF-8 BOM（含中文的 `.ps1` 必须 UTF-8 with BOM，本目录的判据就是 `scripts/ps1_bom_scan.py`，动因登记在 R45 收口批那组条目里），**已知、非漂移**。

**本代新立的一条（派生会把缺陷一起派生过来）**：`chk_r47.ps1` 是从 `chk_r46.ps1` **逐字**派生的，它检查的是
`%TEMP%\r47_upload.ps1` —— 而本代的执行副本在那一刻**还不存在**（第 4 代是"先复制到 TEMP 再跑"，所以那一遍是真的扫到了文件）。
结果它照样打出 `PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / SCRIPT_LINES=0`：**读的文件不存在，读数却全绿**——与 (55)"扫 0 只照样打 DIRTY 0" 同形，
差别只是这次是**我自己派生出来的**，而且 `SCRIPT_LINES=0` 是唯一泄密的线索，我第一遍没看。
处置（不是"下次注意"）：`chk_r47.ps1` 现在 ①源脚本不存在即 `ABORT` + `exit 1`；②`Copy-Item` 到 TEMP 后立刻 `Get-FileHash` **两侧比 md5**，
不等即 `ABORT`，并把 `MD5_BOTH=` 打进读数 ⇒ "校验的字节 == 真被执行的字节"这一层从**靠约定**变成**写在输出里**。
**这一条的取证自己也补跑了一遍**：13:54:39 那一次我只把读数打进了 stdout 就写进本段，输出没落盘 ⇒
14:01:02 重跑并落进 `evidence/r47_parse_check.txt`（同一组读数：`FIRST3=239,187,191 / PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / SCRIPT_LINES=91 / MD5_BOTH=8981D2E8…5183 / RC=0`）。
"我在文档里写了时刻"≠"输出有可复算的载体"——这条与"读数不落盘等于没跑"同族，**序数只在 `FreqErr.md` ht305 段那条台账里登记**，本段不复述。
顺带回溯核了第 4 代那一遍：`%TEMP%\r46_upload.ps1`（mtime 12:09:01）与归档 `scripts/r46_upload.ps1` **md5 相等**（13:50:28 现算 `fa418822616155630a8d7671375ac878`）
⇒ gen 4 那次校验**确实**描述的是被执行的那只字节，只是当时没把这条等式写进凭证（今天靠事后补算才闭上，属**可核而当时未核**）。

第 6 代（`r48final`，截止 21:46:16，跑动 21:46:41~21:49:21）凭证在 `evidence/r48_*.txt`：载荷 **287 只 / 3,524,609 B**
（`git ls-files -c` ∪ `-o --exclude-standard` = 290 命中，`dupes=0`，扣黑名单 3 只 ⇒ 287，copy 失败 0）、
包 **1,409,955 B / md5 `ec7389fa6a23690293990857cbf668cf`**、288 条 entries（第 288 只是包内清单）、utf8-flagged 56、
**`LOCAL_AGGREGATE == REMOTE_AGGREGATE == 17279b0c…7319ac`**（本地那只随 `r48_local.txt` 落盘、zip 成于 21:46:21；远端 21:46:50 `VERIFY_FLUSHED`）、`SCP_EXIT=0`（21:46:45 打印，`SCP_AT` 21:46:43）、
解包根 `zsynctest8` 在 scp 前 `TARGET_EXISTS=False`（21:46:41）、`EXTRACT_OK=True`、
`REMOTE_FILES=287 / REMOTE_BYTES=3524609 / REMOTE_FORBIDDEN=0`、双向差集 `ONLY_IN_LOCAL=ONLY_IN_REMOTE=0`（21:49:21），
包内明文 **1 只 / 287 只内容文件**（`main/provision_ap.c`；分母口径与上一段一致 = 内容文件，不是 288 条 entries）。
包 ↔ 工作树差集（21:49:21，`evidence/r48_cutoff_delta.txt`）= **287 只逐字节等 / 0 改 / 0 删 / 0 新增**
⇒ 这是"包 == 打包那一刻现状"这句话**第二次**在真读数上成立（第一次 = 第 4 代 233/0 改）。
**行尾前置读数照样随证件落盘**（本代是第二次按口径执行）：`r48_local_names.txt` CRLF=287 裸LF=0、远端剥 `\r` 后 287 只裸 LF、
`r48_verify.txt` CRLF=310 且带 BOM ⇒ 三段读数与差集写在**同一只** `r48_diff_and_cred.txt` 里。
`chk_r48.ps1`（逐字派生自上一代，因此带着那条 ABORT + md5 双侧比对守卫）：`FIRST3=239,187,191 / PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / SCRIPT_LINES=91 / MD5_BOTH=43C2B524AF76DE029D246EDABFA70D26`。
**本代仍踩到一次"假差集"，只是位置换了**：差集脚本 `r48_listdiff.py` 第一版把远端名单按 `rstrip(b'\r')` 归一 ⇒ 只剥 `\r` 不剥 `\n`，
本地侧是两行一名的 CRLF，于是又打出 `287/287` 全不同。修法是两侧都归一到 LF 后**再**比（21:49:21 那一遍才是真读数），
过程与判据登记在排查记录 **§36.3** 和 `FreqErr.md` ht305 段该族台账；泄密线索与第 5 代同形：**被点名的名单里带字面 `\r\n`**。

第 7 代（`r49final`，截止 22:59:52 读盘，跑动 22:59:44~23:00:57）凭证在 `evidence/r49_*.txt`：载荷 **313 只 / 3,674,973 B**
（`git ls-files -c` ∪ `-o --exclude-standard` = 316 命中，`dupes=0`，扣黑名单 3 只 ⇒ 313，copy 失败 0；这是**提交之后**的第一次读盘，故 316 里 304 只是已跟踪、12 只是未跟踪），
包 **1,471,082 B / md5 `480c162fcc1f954cbd50bea0a3de8b67`**、314 条 entries（第 314 只是包内清单）、utf8-flagged 57、
**`LOCAL_AGGREGATE == REMOTE_AGGREGATE == 85b059bc…1b812d`**（本地 22:59:56 / 远端 23:00:32）、`SCP_EXIT=0`、
解包根 `zsynctest9` 在 scp 前 `TARGET_EXISTS=False`（23:00:19）、`EXTRACT_OK=True`、
`REMOTE_FILES=313 / REMOTE_BYTES=3674973 / REMOTE_FORBIDDEN=0`、双向差集 `ONLY_IN_LOCAL=ONLY_IN_REMOTE=0`（23:00:56），
包 ↔ 工作树差集（23:00:57，`evidence/r49_cutoff_delta.txt`）= **313 只逐字节等 / 0 改 / 0 删 / 0 新增**
⇒ "包 == 打包那一刻现状"这句话**第三次**在真读数上成立（前两次 = 第 4 代 233/0 改、第 6 代 287/0 改）。
包内明文 **1 只 / 313 只内容文件**（`main/provision_ap.c`；分母口径与前两代一致 = 内容文件，不是 314 条 entries。**但这一次的扫描位置不同**：读的是 22:59:52~22:59:56 之间的**暂存区**，不是解包后的远端落盘物 ⇒ 见"没做"一节最后一条的口径差别）。
`chk_r49.ps1`（23:00:10，逐字派生自上一代、带 ABORT + 双侧 md5 守卫）：`FIRST3=239,187,191 / PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / SCRIPT_LINES=91 / MD5_BOTH=DF93891C2CC9F12063B9B47966E60592`，
本代当时**没有**单立 `r49_parse_check.txt` ⇒ 那五个键在 09-24 00:01 被复查报告核出"evidence/ 下 0 命中"（`r49_run_log.txt` 全文只有 `START 23:00:19…VERIFY_FLUSHED 23:00:35` 与远端命令回显，**不含这五个键**）。处置 = 09-24 00:07:22 **复跑** `chk_r49.ps1` 并落 `evidence/r49_parse_check.txt`：同一组读数逐字复现（`MD5_BOTH` 两侧一致 ⇒ 复跑校验的仍是归档里那 91 行字节），但它是**复跑**、不是 23:00:10 那一次的原始副本，那只文件的来源块已经写明这一句。
一条要紧的**自我限制**：本代包在 22:59:52 读盘，而本代那 9 只凭证在**读盘之后**才落地（落地时刻无载体，见上）⇒ **服务器上看不到 r49 凭证自身**（与第 6 代同族的结构，不是遗漏）；要连凭证一起上，得跑第 8 代。

第 8 代（`r50final`，截止 00:38:42 读盘、`CUTOFF_ZIP_MADE` 00:38:48，跑动 00:38:42~00:44:00）凭证在 `evidence/r50_*.txt`：载荷 **334 只 / 3,833,323 B**
（`git ls-files -c` ∪ `-o --exclude-standard` = 337 命中，`dupes=0`，扣黑名单 3 只 ⇒ 334，copy 失败 0）、
包 **1,537,565 B / md5 `510c3f59d9150cf96791da4f840e8f41`**、335 条 entries（第 335 只是包内清单）、utf8-flagged 59、
**`LOCAL_AGGREGATE == REMOTE_AGGREGATE == d7439b287b06829e7235919fb25c1c74…ac51f`**（两侧摘要各写在自己那只凭证里、逐字符等；**这两行本身不带时刻戳**，能引的界是 `CUTOFF_ZIP_MADE = 00:38:48`（本地侧）与 `REMOTE_AT/REMOTE_DONE_AT = 00:39:51 / 00:39:55`（远端侧）。落地器又在 `r50_land_log.txt` 里把这两行**读回来**并断言"非空 + 64 位十六进制"，才允许打 `AGGREGATE_MATCH=YES`）、
`SCP_EXIT=0`（00:39:47 打印，`SCP_AT` 00:39:47）、解包根 `zsynctest10` 在 scp 前 `TARGET_EXISTS=False`（00:39:45）、`EXTRACT_OK=True`、
`REMOTE_FILES=334 / REMOTE_BYTES=3833323 / REMOTE_FORBIDDEN=0`、双向差集 `ONLY_IN_LOCAL=ONLY_IN_REMOTE=0`（00:40:22；
行尾前置读数同批随证件落盘 = **第四次**按口径执行（第 5/6 代各一次并在正文登记了序数，第 7 代做了但**没登记序数** ⇒ 序数只在 `FreqErr.md` 那条台账里，正文不复述）：`r50_local_names.txt` CRLF=334 裸LF=0、远端剥 `\r` 后 334 只裸 LF、`r50_verify.txt` CRLF=357 且带 BOM），
包 ↔ 工作树差集（00:40:22，`evidence/r50_cutoff_delta.txt`）= **334 只逐字节等 / 0 改 / 0 删 / 0 新增**
⇒ "包 == 打包那一刻现状"这句话**第四次**在真读数上成立（前三次 = 第 4/6/7 代）。
`chk_r50.ps1`（00:39:33，逐字派生自上一代、带 ABORT + 双侧 md5 守卫）：`FIRST3=239,187,191 / PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / SCRIPT_LINES=91 / MD5_BOTH=B88D6ED05938401FC2069680D8C899AA / PS_RC=0`，
**这一代当场就落 `evidence/r50_parse_check.txt`**，不再重演第 7 代"五个键在 evidence/ 下 0 命中、下一代补载体"。
本代还结掉两件事：**① 上一代那句"服务器上看不到 r49 凭证 ⇒ 要连凭证一起上，得跑第 8 代"已兑现**——现读 `r50_local_names.txt`（剥 `\r` 后 grep）里有 **10 只 `hardware/ht305_sync/evidence/r49_*.txt`**（含 00:07:22 那只复跑载体），而 `r50_*.txt` 0 只（它们 00:40:45 才落地，晚于 00:38:42 截止 ⇒ 同族结构限制仍在，不是遗漏）；**② "远端那份带明文"第一次有了直接读数**：`scripts/r50_roundtrip.py` 把远端**解包后**的 `…/zsynctest10/zizhao_20260924_r50final/hardware/zizhao-esp32s3/main/provision_ap.c` scp 回 `%TEMP%`（**不落入仓库**）再扫 ⇒ `REMOTE_BYTES=10199 md5=0419bf1628f399f399ca41daf8ed3494` 与本地逐字节等（`BYTE_EQUAL_TO_WORKTREE=True`）、`PROV_PASS_HITS_REMOTE=1`，同批一条**阴性对照** `CONTROL_LANDER_HITS=0`（同一把尺子在落地器自己的字节上数出 0）⇒ `VERDICT=REMOTE_CARRIES_PLAINTEXT`。这句话此前只由"聚合摘要两端相等 + 名单内含那只"两条读数**推**得，本代起它是**测**得的（推导链仍保留在下面"没做"一节，因为它是另一条口径：不等价于本条）。

## 提交轮（22:55~22:56，`commit 75be24f`，**未 push**）

这是 **R44~R48 那批文档 + 配网时代固件源码的第一次真提交**（限定语必须带：本分支此前已有 9 只未推送提交，`040af28` 本身就提交了 68 只 ⇒ 无限定语的"第一次"不成立），口径与同步链独立：
`scripts/make_staged_list.py` 现跑两路清单（`git diff --name-only` 68 只 + `git ls-files --others --exclude-standard` 108 只，重名 0）
⇒ 排除 5 只并**逐只点名理由** ⇒ `KEEP=171`，清单落 `evidence/staged_list_225525.txt`；
`git add --pathspec-from-file=… --pathspec-file-nul`（NUL 分隔，因路径含中文）⇒ 索引 171 只；
索引侧明文门 `gate/run_staged_cred_gate.ps1` 22:55:41/42 ⇒ `evidence/staged_cred_gate_225541.txt`：
`FILES_SCANNED=171 / PROV_PASS_FILES=0 / SSH_FILES=0 / TOTAL_HITS=0 / VERDICT=CLEAN`（**末行即 `VERDICT`，那只文件里没有 `PY_EXIT` 行**；退出码由驱动的打印给出，本代未落 `_ps` 副本 ⇒ 见"三道口径"第 1 条的订正）。

提交后现跑（22:56:47 与 23:08:06 两遍，另 09-24 00:01:20 第三遍）的**四条 residual 事实**，任何后续引用都要连着这几条一起引：
1. `git rev-list --count origin/main..HEAD` = **10**（现场态数字，**不是常量**，三遍现跑都是 10；用了之前先重跑）⇒ 一句 `git push` 仍会把**未推送历史**里的明文一起公开；
2. 明文普查走 `git grep -f <patternfile>`（口令只从宏本体现读、经文件传给 grep，**绝不进终端回显**）：`HEAD` = **0 只**、`origin/main` = **0 只**；
   但 `HEAD`=0 **不等于** push 安全 —— 那 10 只未推送提交里 **6 只各带 2 处明文**。权威载体 = 排查记录 **§三十五-④** + `evidence/unpushed_plaintext_hist_212353.txt`（1,737 B，`UNPUSHED_COMMITS 9 / DIRTY_COMMITS 6 / CLEAN_COMMITS 3`）；
   **两处指针此前都落不到**（本 README 曾指"排查记录'现场态'段"——那里没有以"现场态"命名的段；§37.1 曾推到仓库外的项目记忆文件），现已统一。
   一条必须连着引的**快照口径**：那只凭证取的是 **21:23:53（提交前）**的 9 只快照 ⇒ 下一轮照凭证复算会得 **10**，两者不打架：新增的第 10 只就是 `75be24f`，它干净另由 `git grep HEAD`=0 证（09-24 00:01:20 对 `75be24f`/`040af28` 两棵树再各跑一遍，仍 0 命中）。
3. `git ls-files` = **304**，工作树仍脏 = 1 只 modified + 6 只 untracked（本目录 gen 12 那批就是其主要增量）；
4. **本提交轮的提交信息有一句要订正**：原文写"`.c` 没进"。23:08:06 实测：`main/provision_ap.c` 在 `HEAD` 里是 **42 行 / 1,278 B** 的早期桩、
   **不含 `PROV_PASS` 宏**；工作树那只才是 **238 行 / 10,199 B**、带宏。⇒ 准确说法是"**工作树版**没进，`HEAD` 仍停在 42 行桩"，
   而不是"这个文件没进仓库"。**不改提交信息（不 amend）**，订正只落文档；同族教训见 `FreqErr.md` ht305 段该族台账。

### 提交轮 #2（09-24 00:5x~01:0x，本目录的取证进仓，**未 push**）

第一轮（`75be24f`）**已经带走本目录当时的 84 只**（`git show --stat 75be24f -- hardware/ht305_sync` 读数；更早的 `040af28` 带走第 1~3 代工具）⇒ 本轮 #2 要带的是**那之后**才落地/改写的字节：09-24 处置轮 + 第 8 代全套 + 本 README/清单/门输出。现跑口径 = `git status --porcelain -- hardware/ht305_sync`，本行下笔那一批 = **43 只 `??`（未跟踪）+ 7 只 `M`（改写）**；这个数字是**快照**，冻结链跑完就会漂 ⇒ 引用前现跑，别引本行。第二次提交走同一套口径、多一条本轮新加的载体要求：
`scripts/make_staged_list.py`（同一批 5 只 `EXCLUDE` 名字与理由不变）⇒ 门 `gate/run_staged_cred_gate.ps1`。
**名单跑了两遍，只有后一遍是本次提交用的**：`evidence/staged_list_005929.txt`（`MOD=13 / UNTRACKED=50 / KEEP=58`，**作废** —— 它之后我又改了一次驱动并加了门输出）与 `evidence/staged_list_010108.txt`（`MOD=14 / UNTRACKED=52 / KEEP=61`，本次口径）。作废那一只**不删**（同 `r45_cutoff_delta_gen2_113401.txt` 那条两代读数并存的先例），代价就是这两行必须连"哪一只是本次的"一起引 ⇒ 引用前现读名单首行的生成时刻，别按文件名序数推。
门 `gate/run_staged_cred_gate.ps1` **这次把驱动的打印也落盘**（`evidence/staged_cred_gate_<t>_ps.txt`，两只：门输出 + 驱动 `OUT=/PY_EXIT=` 副本）。
那句"驱动的打印必须落盘"在上一节里是一句**没有执行者的要求**（上一轮就没落）⇒ 本轮把它写成硬性判据：**本轮若查不到 `_ps.txt` 就是未完成**，不许用"`VERDICT=CLEAN` + 脚本逻辑"推出来代替读数。
**一条按构造就闭不掉的残留，先说在这里**：门扫的是"已 stage 的字节"，所以**门自己写出的那几只文件不可能在它写出之前被它扫到** ⇒ `staged_list_*.txt` / `staged_cred_gate_<t>.txt` / `…_ps.txt` 三只（含 `_ps` 那一只）**不进本次提交**，是本次提交的**已知残留**，交给下一次冻结（gen 13）收。这不是"忘了加"：把它们塞进名单等于让索引含一份门没扫过的字节。
本 README 的这一段（连同它的字节）**在**本次提交里，因为它写在冻结链之前，而链的判据是 `verify_manifest.py` ⇒ `VERDICT=MANIFEST_STILL_TRUE / rc=0`。
提交号**不写在本目录里**（写在这里就必须再改本文件 ⇒ 立刻把刚冻好的清单 md5 作废）⇒ 权威载体 = 排查记录 **§三十八** 与 `dev_log/20260924.md`，引用时现读 `git log -1 --format=%h`。

## 一处必须说明的来源差异（否则下一轮会把副本当"当时跑的那一份"）

`scripts/collect_ht305_sync.py` 的 `PATTERNS` 在归档**之后**被补了一项 `r43_*.txt`
⇒ 仓库里这份**不等于**10:36:41 真跑过的那一份（真跑那份只覆盖 47/49 只，没有 r43 那一代）。
补这一项的动因是我先在项目记忆里写了一句"该取证件已在 `evidence/`"，现查发现**只有 `%TEMP%` 有** ⇒
先按"门 0 命中 + `copy2` + md5"把 `r43_r44_listdiff.txt`（79 B，`md5 6d770df2…`）补收进来，再改脚本让**重跑**能复现现在的目录。
可重跑性也说清：`collect_ht305_sync.py` 自带"目标目录已存在即 ABORT"守卫 ⇒ 它只在**空目录**下能整体重建；
日常"清单过期了"要重跑的是 `scripts/gen_manifest.py` 与 `gate/` 里那三道门，不是它。
教训同族：项目记忆 `hardware-epaper397-power.md` **(46)**"安全措辞要对的是动作清单，不是结果"——这里是"清单要对的是现状，不是意图"。

## 本归档明确**没有**做的事

- **不含** `.ht305_pass.xml`、`_askpass_ht305.ps1`、任何凭据文件本体（门脚本只是普通 python/ps1，内嵌零口令）。
- **不含** `*.log`、`backups/`、`.git`（与载荷黑名单同一口径）。
- **没做**远端现场复验：归档里的 `REMOTE_*` 行只是"上一轮从服务器打回来的那段 stdout 的副本"，
  不等于今天服务器桌面仍长这样 ⇒ 任何"远端 = X"的断言引用时**必须点名它出自哪只副本**。
- **没做**自动化接线：这些是可复算的事后凭证，不是会被任何构建/脚本调用的代码；改它们不影响固件。
- **没做**脱敏改写：`r45_local_names.txt` / `r46_local_names.txt` 等按原样存；已核 = 复制前候选全量（10:3x 的 47 只、12:0x 补收 r46 时的 13 只，均 `DIRTY 0`）
  + 归档后终态全量 + 提交前索引侧已 stage blob，三道门（`PROV_PASS` / ht305 SSH 口令）**每次均 0 命中**，
  外加一只**假哨兵阴性对照**证明"脏了会响"（`SELFTEST_PASS=4/4`）⇒ "原样"在这里是安全的。
  **但"每次均 0 命中"这句对归档后那道（`cred_gate_recheck.py`）要按世代拆开**：09-24 之前它既没有"候选=0 即 ABORT"、也没有退出码/`VERDICT`，且 `HT305_TMP_FOR_GATE` 未设时只写 `SSH_TOTAL_HITS=SKIPPED` 就 `rc=0` ⇒ 那几次只保证**扫过**、不保证**扫到**。09-24 补齐（环境缺失 ABORT / `FILES_SCANNED=0` ABORT / `VERDICT=CLEAN|PLAINTEXT_IN_ARCHIVE` + 命中即 `exit 1`），**第一个真载体 = gen 12 冻结链 00:54:28 那一遍**（`cred_gate_recheck_005428.txt`：`FILES_SCANNED=175 / PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0 / VERDICT=CLEAN` + 驱动 `PY_EXIT=0`）⇒ 本代起这句对**该道门**也成立，但它只覆盖**跑的那一刻之前**的字节（清单头部的 `gate_after` 行现算还有几只排在门后）。
  唯一带明文的固件源文件 `main/provision_ap.c` **不在**本归档里，门只是从它现读口令用于比对。
- **没做**远端清理：**八轮**同步在服务器上留下的包与解包根（`%TEMP%\zsynctest*`，最新一代是 `zsynctest12`（第 9 代那只 = `zsynctest11`，两代解包根都留在服务器上）；桌面侧到 **00:39:45 那次探测**（在本次 `scp` **之前**，所以本代那只 `zizhao_20260924_r50final.zip` 不在名单里）可见 **8 只**同步包并存：第 1 代那只 `SUPERSEDED-tar-cjk-mojibake_zizhao_sync_20260923_r43.tar.gz`（1,002,599 B）、`zizhao_sync_20260923_r43.zip`（1,117,960 B）与 `r44final`~`r49final` **六只** zip（1,135,781 / 1,161,539 / 1,269,250 / 1,349,354 / 1,409,955 / 1,471,082 B），另有一只与同步无关的 `zizhao_esp32s3_flash_notice_20260918.zip`（9,762 B），读数在 `evidence/r50_probe.txt`）**一只都没删**【09-24 **05:38:17 第 10 代 `scp` 之前**同口径再探：桌面同步包已并存 **10 只** = 上面那只 tar.gz + **9 只 zip**（`zizhao_sync_20260923_r43.zip` 1,117,960 B 与 `r44final`~`r51final` 八只，新落的两只 = `zizhao_20260924_r50final.zip` **1,537,565 B** / `…_r51final.zip` **1,696,912 B**），同批 `TARGET_EXISTS=False`（= 本代目标包那一刻还没上去），读数在 `evidence/r52_probe.txt` ⇒ **仍一只都没删**】，
  脚本侧从头到尾没有 `Remove-Item`（第 2 代那只有，已随 `chk_r4*.ps1` 的 `REMOVE_ITEM_HITS=0` 判据被排除在当前口径外；且第 6 代的远端命令里两条 `Test-Path … ABORT` 守卫使解包根**已存在即拒跑**，不做任何覆盖/删除）。
  也就是说：服务器上的 `zizhao_*.zip` 里含 `main/provision_ap.c` ⇒ **远端那份是带明文的**，
  本目录的"0 命中"管的是**仓库这一侧**，不要拿它去断言服务器侧干净。**这句"远端带明文"到今天为止有五处读数、口径各不同，别并成一句**：
  ① 12:10:29 的 `1/233` 与 ② 21:49:21 的 `1/287` 都是**本地扫包内条目/解包后的落盘物**（`r46_diff_and_cred.txt`、`r48_diff_and_cred.txt`）；
  ③ 第 7 代 = **打包时的暂存区扫描**（`r49_local.txt` 22:59:5x 打 `plaintext in staging= 1 ['…provision_ap.c']` / 313 只内容文件）、④ 第 8 代同口径再来一次（`r50_local.txt` `plaintext in staging= 1` / 334 只）⇒ ③④ 比 ①② **弱一档**：①② 扫的是解包后的字节，③④ 只扫了打包前的暂存区，服务器侧那两轮回给的只有 `REMOTE_FORBIDDEN=0`（那是黑名单、不是明文）；
  ⑤ **第 8 代新加的这条才是直接测**：`r50_roundtrip.py` 把远端 `zsynctest10` 里**解包后**的那只 `.c` scp 回本机比 md5 并数口令（`PROV_PASS_HITS_REMOTE=1` + `BYTE_EQUAL_TO_WORKTREE=True` + 同批阴性对照 `CONTROL_LANDER_HITS=0`）。
  ⑤ **第 8~10 代每代都跑了同一把回扫**（`r50_roundtrip.txt` / `r51_roundtrip.txt` / `r52_roundtrip.txt`，三次读数都是 `REMOTE_BYTES=10199 md5=0419bf16…` == 本地那只、`BYTE_EQUAL_TO_WORKTREE=True`、`PROV_PASS_HITS_REMOTE=1` ⇒ 三只都是 `VERDICT=REMOTE_CARRIES_PLAINTEXT`），但每一次**仍只覆盖本代那一只包**；第 4~7 代那几只包"远端也是带明文的"，靠的仍是**两条读数的合取**：`REMOTE_AGGREGATE == LOCAL_AGGREGATE`（逐字节等式，见排查记录 §31.2 的定义）+ `main/provision_ap.c` 在那一代的名单内 ⇒ 服务器解包出来的那只字节与本地那只一致，而本地那只现读含宏值。任何一次单独扫描都推不出这句话。
- **没做**"每一代清单都可复算"：见上面"清单世代"一节 gen 5 那格的 `不可复算`。
  gen 12 那一格原本挂的"**尚未冻结**"已于 09-24 00:5x 按判据跑通而摘掉（`verify_manifest.py` ⇒ `VERDICT=MANIFEST_STILL_TRUE / rc=0`），
  但**同一代内**第一遍那份清单（`TOTAL=174`）仍被第二遍覆写 ⇒ 首行时刻这一层照旧不可复算，只数那一层由 `evidence/manifest_gen_log.txt` 兜住（见「末版的三个数」段）。
  还有一层**本代新核出**的没做：`git ls-files` 与 `git show --stat` 只证明"某只文件在某个提交里"，**不证明它当时的字节就是那次冻结的末版**——本轮的提交顺序（清单 → 门 → `git add`）决定了 3 只提交轮取证必然落在末版清单之外，已登记在"提交轮 #2"那一节。
