# `hardware/ht305_sync/` —— ht305 三轮全量同步的脚本与取证件归档

建立时刻：09-23 10:36:41（首批 49 只复制）→ 10:38:51（+3）→ 10:43~10:47（+门复验脚本、清单生成器、编码体检脚本）。
终态只数与逐只指纹以 `MANIFEST.txt` 为准（**它本身是快照**：本 README 若在其后再被编辑，清单里那一行的 md5 就过期，
重跑 `python scripts/gen_manifest.py` 即可复算）。
建立原因：**R44 终态复查报告**（本目录不存这只文件；报告原文在
`hardware/20260923_R44终态复查报告原文.txt`）"我没能验证的清单"末条指出：
本轮全部可复算证据只活在 `%TEMP%`、仓库内无副本 ⇒ 下一轮必然再报一次"锚点不可复算"。
逐条处置见 `hardware/20260919_墨水屏点屏排查记录.md` **§33.5**（采纳该建议这一条）。

## 目录里有什么

| 子目录 | 内容 | 说明 |
| --- | --- | --- |
| `scripts/` | 三代同步工具的**全部**脚本副本 | 按文件名前缀分代：`ht305_*` + `build_sync.py`/`build_zip.py`/`expected*.py`/`pw_*.py` = **第 1 代**（tar 通道，已判为坏通道）；`sync_r44.py` + `r44_upload.ps1`/`r44_verify2.ps1` + `probe_zip_vs_head*.py` = **第 2 代**（zip + 聚合哈希，但脚本里有 `Remove-Item`、时间戳不落盘）；`sync_r45.py` + `r45_upload.ps1` + `chk_r45.ps1` + `r45_cutoff_delta.py` = **第 3 代**（当前口径） |
| `evidence/` | 每代跑出来的原始 stdout / stderr / 计数文件 | 含 `r43_r44_listdiff.txt`（r43→r44 逐名差集，`T=08:32:06`、`+1 只 / −0 只`）、`r44_verify2.txt`（第 2 代远端读数）、`r45_verify.txt`（第 3 代远端读数，`REMOTE_*` 行）、`r45_local.txt`（截止时刻 + 载荷指纹）、`r45_scp_err.txt`（`SCP_EXIT` 落盘）、`r45_cutoff_delta.txt`（包 ↔ 工作树差集）、`cred_recount_0822.txt`（口令计数复跑）、`ps1_bom_scan.txt`（本目录自己的编码体检）、`cred_gate_recheck.txt`（归档后的明文门复验） |
| `gate/` | 进门用的明文门 | `ht305_sync_gate.py`（复制前扫 `PROV_PASS` 宏值）、`ht305_sync_gate_ssh.ps1`（DPAPI 取回 ht305 SSH 口令后在内存里比对）、`cred_gate_recheck.py` + `run_cred_gate_recheck.ps1`（归档后复验，输出 `evidence/cred_gate_recheck.txt`） |
| 本目录自有工具 | `scripts/gen_manifest.py`（重生成 `MANIFEST.txt`）、`scripts/ps1_bom_scan.py`（重生成 `evidence/ps1_bom_scan.txt`）、`scripts/collect_ht305_sync.py`（当初的复制器，内含明文门） | 这三个脚本让"归档 + 指纹 + 门"整条链路可在**任何时刻原地重跑**，而不是只留一份跑不动的副本 |

## 三道口径（这批复件为什么可信 / 有什么没覆盖）

1. **明文门（跑了两次，两次都要）**：
   - 第 1 次在复制**之前**，扫 `%TEMP%` 的 47 只候选 ⇒ `CANDIDATES 47 / DIRTY 0`（10:3x）+ SSH 口令门
     `SSH_SECRET_HITS_FILES=0`；
   - 第 2 次在归档**之后**，扫归档终态 57 只（含清单、README、两道门脚本自身）⇒
     `PROV_PASS_TOTAL_HITS=0 / SSH_TOTAL_HITS=0`，读数落在 `evidence/cred_gate_recheck.txt`（跑在第 2 遍的那次，时刻见该文件首行）。
     只补第 2 次不够：那 47 只候选里若有一只带明文，它已经在 `%TEMP%` 里躺着了。
   两道的输出都**只打文件名与命中次数**，口令本身全程不落终端、不落盘
   （门脚本按 `#define PROV_PASS` 现读、按 DPAPI 现解后经环境变量传给子进程，不内嵌字面量）。
2. **逐字节复制 + 终态清单**：`shutil.copy2`，不做任何转写；`MANIFEST.txt` 逐只记
   `bytes / md5 / 有无 UTF-8 BOM / mtime`，并在头部按 mtime **现算**"门之后还有哪些只被改写过"。
3. **编码体检**：`evidence/ps1_bom_scan.txt` ⇒ 归档内 `.ps1` **非 ASCII 且无 BOM 的组合 = 0 只**，
   顺带回答了报告"没能验证 #7"（`r44_upload.ps1`/`r44_verify2.ps1` 的 `nonascii=0` ⇒ 无 BOM 不构成 GBK 风险；
   含中文的那只只有 `r45_upload.ps1`，它带 BOM）。

## 复算入口（不在本 README 里重述定义）

聚合判据的**可复算定义**钉在 `hardware/20260919_墨水屏点屏排查记录.md` **§31.2**
（逐只 `sha256(相对路径 + 字节)`、剥顶层目录、**单个 LF 字节 0x0A** 连接排序后的摘要、排除包内 `SYNC_MANIFEST.txt`）；
执行者是 `scripts/ht305_agg.ps1`（第 2/3 代沿用它）与 `scripts/sync_r45.py`。
三轮同步各自的载荷与指纹读数分别在排查记录 **§三十一 / §三十二 / §三十三**。

## 一处必须说明的来源差异（否则下一轮会把副本当"当时跑的那一份"）

`scripts/collect_ht305_sync.py` 的 `PATTERNS` 在归档**之后**被补了一项 `r43_*.txt`
⇒ 仓库里这份**不等于**10:36:41 真跑过的那一份（真跑那份只覆盖 47/49 只，没有 r43 那一代）。
补这一项的动因是我先在项目记忆里写了一句"该取证件已在 `evidence/`"，现查发现**只有 `%TEMP%` 有** ⇒
先按"门 0 命中 + `copy2` + md5"把 `r43_r44_listdiff.txt`（79 B，`md5 6d770df2…`）补收进来，再改脚本让**重跑**能复现现在的目录。
可重跑性也说清：`collect_ht305_sync.py` 自带"目标目录已存在即 ABORT"守卫 ⇒ 它只在**空目录**下能整体重建；
日常"清单过期了"要重跑的是 `scripts/gen_manifest.py` 与 `gate/` 里那两道门，不是它。
教训同族：项目记忆 `hardware-epaper397-power.md` **(46)**"安全措辞要对的是动作清单，不是结果"——这里是"清单要对的是现状，不是意图"。

## 本归档明确**没有**做的事

- **不含** `.ht305_pass.xml`、`_askpass_ht305.ps1`、任何凭据文件本体（门脚本只是普通 python/ps1，内嵌零口令）。
- **不含** `*.log`、`backups/`、`.git`（与载荷黑名单同一口径）。
- **没做**远端现场复验：归档里的 `REMOTE_*` 行只是"上一轮从服务器打回来的那段 stdout 的副本"，
  不等于今天服务器桌面仍长这样 ⇒ 任何"远端 = X"的断言引用时**必须点名它出自哪只副本**。
- **没做**自动化接线：这些是可复算的事后凭证，不是会被任何构建/脚本调用的代码；改它们不影响固件。
- **没做**脱敏改写：`r45_local_names.txt` 等按原样存；已核 = 复制前 47 只候选 + 归档后终态全量，
  两道门（`PROV_PASS` / ht305 SSH 口令）**两次均 0 命中** ⇒ "原样"在这里是安全的。
  唯一带明文的固件源文件 `main/provision_ap.c` **不在**本归档里，门只是从它现读口令用于比对。
