# `hardware/ht305_sync/` —— ht305 六轮全量同步的脚本与取证件归档

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

## 清单代次（**单一权威源**：本目录只有一份末版 `MANIFEST.txt`，历世代只在这里登记）

| 代 | 时刻 | 只数 | 为什么又跑一次 |
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

末版的 `TOTAL / TOTAL_BYTES / BOM_FILES` 三个数**只以 `MANIFEST.txt` 末三行现读为准**（本 README 若在其后被编辑，清单里那一行的 md5 就过期，
重跑顺序固定为"**改内容 → `scripts/ps1_bom_scan.py` → `gate/run_cred_gate_recheck.ps1 <打包截止时刻>` → `scripts/gen_manifest.py` → `scripts/verify_manifest.py`**，
**三次动作 + 一次复核、不是一次**：编码体检与门各自都要往 `evidence/` 落一只文件，落在清单之前才会被清单记进 md5、落在门之前才会被门扫过；最后那只复核器给的才是"冻住"判据（`VERDICT=MANIFEST_STILL_TRUE / rc=0`）。
gen 9 那一批按这个顺序跑了**五轮**（11:58:27~11:58:28 / 12:07 / 12:19~12:21 / 13:07:59~13:09:00 / **末轮 = gen 9 收口**，其时刻现读 `MANIFEST.txt` 首行，不在这里写死）。
本代（gen 11）把这条链跑了**两遍**：22:21:14/22:21:24/22:21:37 第一遍（编码体检 → 门 → 清单），随后又改了本 README ⇒ 22:22 那一遍重来，末版时刻与只数**现读 `MANIFEST.txt` 首行与 `TOTAL` 行**（这里不写死，理由见上一条括号）。
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
| `scripts/` | **六代**同步工具的**全部**脚本副本 | 按文件名前缀分代：`ht305_*` + `build_sync.py`/`build_zip.py`/`expected*.py`/`pw_*.py` = **第 1 代**（tar 通道，已判为坏通道）；`sync_r44.py` + `r44_upload.ps1`/`r44_verify2.ps1` + `probe_zip_vs_head*.py` = **第 2 代**（zip + 聚合哈希，但脚本里有 `Remove-Item`、时间戳不落盘）；`sync_r45.py` + `r45_upload.ps1` + `chk_r45.ps1` + `r45_cutoff_delta.py` = **第 3 代**（当前口径的确立：双端"存在即拒"、每条读数带时刻）；`sync_r46.py` + `r46_upload.ps1` + `chk_r46.ps1` + `r46_cutoff_delta.py` = **第 4 代**；`sync_r47.py` + `r47_upload.ps1` + `chk_r47.ps1` + `r47_cutoff_delta.py` = **第 5 代**；`sync_r48.py` + `r48_upload.ps1` + `chk_r48.ps1` + `r48_cutoff_delta.py` + `derive_r48.py` + `r48_listdiff.py` = **第 6 代**。第 4~6 代一律**逐字从上一代派生**（只换包名 / 解包根 / 凭证前缀），派生器对每个替换断言命中数、命中 0 即 `ABORT`；第 6 代起**派生器与差集器本身也入档**（否则下一代只会派生脚本、不会派生"为什么这么派"）。`chk_r47.ps1`/`chk_r48.ps1` 这两代跑完都留 `PARSE_ERRORS=0 / REMOVE_ITEM_HITS=0 / MD5_BOTH=` 三个读数（见 `evidence/r47_parse_check.txt`、`evidence/r48_parse_check.txt`） |
| `evidence/` | 每代跑出来的原始 stdout / stderr / 计数文件 | 含 `r43_r44_listdiff.txt`（r43→r44 逐名差集，`T=08:32:06`、`+1 只 / −0 只`）、`r44_verify2.txt`（第 2 代远端读数）、`r45_verify.txt` 与 `r46_verify.txt`（第 3/4 代远端读数，`REMOTE_*` 行）、`r45_local.txt` / `r46_local.txt`（截止时刻 + 载荷指纹）、`r45_scp_err.txt` / `r46_scp_err.txt`（`SCP_EXIT` 落盘）、`r45_cutoff_delta.txt` + `r45_cutoff_delta_gen2_113401.txt` + `r46_cutoff_delta.txt`（包 ↔ 工作树差集，见排查记录 §33.3①/①-b 与 §三十四）、`r46_diff_and_cred.txt`（第 4 代双向差集 + 包内明文复测，**内含一条行尾踩坑登记**）、`r45_local_names.txt` / `r46_local_names.txt` / `r46_remote_names.txt`（两侧名单）、`cred_recount_0822.txt`（口令计数复跑）、`ps1_bom_scan.txt`（本目录自己的编码体检）、`cred_gate_recheck*.txt`（归档后全量明文门，**文件名带时刻**，`FILES_SCANNED=` 行（**不是末行**）就是它自己那一遍扫了几只）、`staged_cred_gate_114414.txt`（提交前**索引侧**明文门）、`cred_gate_selftest_120548.txt`（门的**阴性对照**：证明"脏了会响"）、`manifest_gen_log.txt`（**代次日志**：由 `gen_manifest.py` 自己每代追加一行 `时刻/TOTAL/TOTAL_BYTES/BOM_FILES` ⇒ 末版清单被覆写之后"上一代有几只"仍可读，自 09-23 gen 9 起有行）；**第 5 代 `r47_*.txt` 11 只**（含 14:01:02 补跑的 `r47_parse_check.txt`）与**第 6 代 `r48_*.txt` 12 只**（含 `r48_parse_check.txt`、`r48_listdiff.txt`）各自成套 = `local / local_names / local_names.sorted / probe / scp_err / verify / run_log / cutoff_delta / remote_names / diff_and_cred`（第 6 代多一只 `listdiff`，因为差集器改成一趟跑完三件读数；只数由 `ls -1 r4{7,8}_*.txt | wc -l` 现跑，别照抄本行）；另有 `unpushed_plaintext_hist_212353.txt`（未推送提交的**tree 口径**明文普查）与 `staged_cred_gate_2139{42,4001}_ctrl_*` 三只 = 索引侧门"命中即 `exit 1`"这条改动的**两轮阴性对照**（一轮空索引、一轮故意 stage 带明文的那只） |
| `gate/` | 进门用的明文门 | `ht305_sync_gate.py`（复制前扫 `PROV_PASS` 宏值）、`ht305_sync_gate_ssh.ps1`（DPAPI 取回 ht305 SSH 口令后在内存里比对）、`cred_gate_recheck.py` + `run_cred_gate_recheck.ps1`（归档后复验全量，输出**带时刻**、不覆写上一代）、`staged_cred_gate.py`（提交前只扫 `git diff --cached` 列出的**已 stage blob 字节**，输出另存 `evidence/staged_cred_gate_<时刻>.txt`；**09-23 21:3x 起裁决同时落 stdout 与退出码**：`TOTAL_HITS>0 ⇒ VERDICT=PLAINTEXT_IN_INDEX + exit 1`，此前它只打印、`rc` 恒 0 ⇒ "靠我读输出"没有执行者）、`run_staged_cred_gate.ps1`（它的**驱动**：DPAPI 解 SSH 口令 → 经环境变量喂给门 → 用完立刻 `Remove-Item Env:` → 打印 `OUT=` / `PY_EXIT=` 并 `exit $rc`；**门自己那份文件不含退出码，所以驱动的打印也必须落盘**）、`cred_gate_selftest.py`（**哨兵阴性对照**：不碰任何真口令，用假哨兵走同一个 `scan()`，断言"命中会亮 / 干净不假响 / 排除项真被排掉"） |
| 本目录自有工具 | `scripts/gen_manifest.py`（重生成 `MANIFEST.txt`）、**`scripts/verify_manifest.py`（清单的复核器：逐行拿盘上现状重算，漂了就点名并返回非 0）**、`scripts/ps1_bom_scan.py`（重生成 `evidence/ps1_bom_scan.txt`）、`scripts/collect_ht305_sync.py`（当初的复制器，内含明文门） | 这些脚本让"归档 + 指纹 + 门"整条链路可在**任何时刻原地重跑**，而不是只留一份跑不动的副本 |

## 三道口径（这批复件为什么可信 / 有什么没覆盖）

1. **明文门（三种口径、各自量不同的集合，三次均 0 命中）**：
   - **复制前**：扫 `%TEMP%` 的 47 只候选 ⇒ `CANDIDATES 47 / DIRTY 0`（10:3x）+ SSH 口令门
     `SSH_SECRET_HITS_FILES=0`；
   - **归档后全量**：扫本目录**当时的全部文件**（含门脚本自身与 README/清单，**排除本输出文件**）⇒
     `PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0`，读数落在 `evidence/cred_gate_recheck_<时刻>.txt`
     （从 12:07 起**文件名带时刻、不覆写上一代**，此前那一只叫 `cred_gate_recheck.txt`；
     它的 `FILES_SCANNED=` 行（**不是末行**，末行是 `SSH_TOTAL_HITS`）是**快照**：本行下笔时最新一只 = 65，跑于 12:07:57；目录再长就再跑一次，别引本行）；
   - **提交前索引侧**：只扫 `git diff --cached` 列出的**已 stage blob 字节**（= 真正会进 commit 的那份，不是工作树）⇒
     `TOTAL_HITS=0`，凭证 `evidence/staged_cred_gate_114414.txt`（`FILES_SCANNED=68`，跑于 11:44:14）。
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
执行者是 `scripts/ht305_agg.ps1`（第 2/3/4 代沿用它）与 `scripts/sync_r45.py` / `sync_r46.py` / `sync_r47.py` / `sync_r48.py`（后四只各自在打包时算本地聚合，`sync_r47.py` 逐字派生自 `sync_r46.py`、`sync_r48.py` 逐字派生自 `sync_r47.py`）。
六轮同步各自的载荷与指纹读数分别在排查记录 **§三十一 / §三十二 / §三十三 / §三十四 / §34.8（第 5 代）/ §三十六（第 6 代，含六代汇总表）**。
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
  唯一带明文的固件源文件 `main/provision_ap.c` **不在**本归档里，门只是从它现读口令用于比对。
- **没做**远端清理：**六轮**同步在服务器上留下的包与解包根（`%TEMP%\zsynctest*`，最新一代是 `zsynctest8`；桌面侧到 21:46:41 那次探测时可见 `zizhao_20260923_r44final.zip`/`r45final`/`r46final`/`r47final` 四只 zip 与第 1 代那只 tar.gz **全部并存**，读数在 `evidence/r48_probe.txt`）**一只都没删**，
  脚本侧从头到尾没有 `Remove-Item`（第 2 代那只有，已随 `chk_r4*.ps1` 的 `REMOVE_ITEM_HITS=0` 判据被排除在当前口径外；且第 6 代的远端命令里两条 `Test-Path … ABORT` 守卫使解包根**已存在即拒跑**，不做任何覆盖/删除）。
  也就是说：服务器上的 `zizhao_*.zip` 里含 `main/provision_ap.c` ⇒ **远端那份是带明文的**，
  本目录的"0 命中"管的是**仓库这一侧**，不要拿它去断言服务器侧干净（12:10:29 实测包内明文 1/233；21:49:21 第二次实测 **1/287**）。
- **没做**"每一代清单都可复算"：见上面"清单代次"一节 gen 5 那格的 `不可复算`。
