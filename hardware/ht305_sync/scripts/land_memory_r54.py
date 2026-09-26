# -*- coding: utf-8 -*-
# 项目记忆追加：R54 尾巴新规 (96)-(100) + 现场态换代（纯追加到 EOF）
import sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')
MEM = r'C:/Users/david/.qoder-cn/projects/C--Users-david-Documents-all-projects-----/memory'
P = os.path.join(MEM, 'hardware-epaper397-power.md')
DRY = '--dry' in sys.argv

t = open(P, encoding='utf-8', newline='').read()
assert '\r' not in t and t.endswith('\n')
for k in ['(96)', '(97)', '(98)', '(99)', '(100)', 'R54 尾巴现场态换代']:
    assert ('\n  ' + k) not in t, k + ' 已存在'

ADD = '''  **R54 尾巴（09-24 10:47:20 第 12 代同步 → 11:12:27 gen 21 末版 → 11:46:25 paperwork 落地 → 11:50:50 docs 第八遍）定下的 (96)-(100)**：
  (96) **可证伪预期必须自带"现跑基数"，绝对数一律不进预期句**：gen 19 那格我写"⇒ 预期：门输出只数 23→24、只数 311→312"，本代现跑 `ls -1 evidence/cred_gate_recheck_*.txt | wc -l` = **27 / 28**、`TOTAL` = **342** ⇒ **方向对、被锚死的数全过期**（同族 (93)：判据只能是关系式）。⇒ 从现在起预期只写成"**式子 + 本遍两端实测**"，永不写"下一代等于几"。本代正面兑现：`TOTAL == 本遍门 FILES_SCANNED − 1` 在 gen 20（343→342）与 gen 21（345→344）**跨代第二次独立成立**。
  (97) **引用节号要连"那一节讲的是什么"一起核**：我在 `ht305_sync/README.md` 的 NOTE 里写"见排查记录 §36.5 那一族的守卫"，`grep -n "^### 36\\.5"` 现读那行是**「36.5 本节没做（点名）」** ⇒ 节号存在、内容不对题。这是**假指针第 2 例**（上一例 `39d3031` 提交信息：一次 `grep -o "38\\.1[3-9]"` 把 2,496 行那个 `38.16 s`（单位**秒**）当成节号）⇒ 判据升级：**引节号 = 标题级 grep + 读那一节的第一个标题行并断言关键词**，只证"存在"不够。
  (98) **台账行的"追加之后"计数必须在最终字节串上算完再回填**：登记 (96)(97) 那三条的那只 FreqErr 台账行首跑写了"`wc -l` = 1800"，落盘实测 **1801** ⇒ 它算的是**不含自己**的那一遍（镜像了 R53 尾巴那族"作用域窄于结论"）。修法两步缺一不可：**先数后回填**（占位符在将被写出的完整字节串上现算再替换）+ **落盘后独立回读**另一次调用比对；订正句**追加**，绝不就地改数。本代收口读数：`^[错误类型]` **179** / `wc -l` **1,811**，两把尺与磁盘独立回读逐字相同。
  (99) **反复出错的文案缺陷，终局是给它装执行者，不是再订正一次**：docs 快照 NOTE 连续两代"末段只数比自身表格晚一代"，本代不再改句子，而是在派生脚本里把**所有只数改成 `len(SRCS)` 插值** + 两道自核（`TABLE_ROWS == len(rows)`、`"现读 N 只源"` 那句必须真在 NOTE 里）。⇒ 与 (86)"规矩写在被违反的文件头上不构成防护"同族，本条是它第一次在**文档生成器**里兑现。
  (100) **"某目录 = N 只"的读数必须连"当时 cd 在哪"一起登记**：`todo.md` 第十三遍写「`docs/` = **37 只**（`ls -1 docs | wc -l` 现跑）」，本遍在**仓库根**跑同一条命令 = **2**（只有两只 letter）⇒ 那 37 只实际住在 `backups/r43_20260922_131029/docs/`（快照非终态，`SNAPSHOT_AT 08:43:08`）——**数是对的、命令是错的**。同族第二处：`evidence/` = 235、`scripts/` = 102 都在 `hardware/ht305_sync/` 下面，仓库根**没有** `evidence/`（现跑直接 `No such file or directory`）。⇒ 引用快照类读数时**路径写全**，写载体时把 `PWD` 一起打进去。
  **R54 尾巴现场态换代（09-24 11:39:03 / 11:51:52 现跑；取代上面"R53 后半批现场态"那一段的 `rev-list`、status 只数、docs 快照、归档 gen 四条）**：`git rev-list --count origin/main..HEAD` = **17**（HEAD = `39d3031`，第八次提交轮，**未 push**、零历史重写）；`git -c core.quotePath=false status --porcelain` = **11 只 ` M` + 36 只 `??` = 47 行**，同一刻用户端报 **66** ⇒ 两把尺互不可换算、差值未定性；` M` 里 `main/` 侧只有 `provision_ap.c`（mtime 09-19 15:50:08）⇒ **R54 尾巴这批零代码进工作树**，"零代码进 commit"那句仍只对点名批次成立（R53 起已被 `39d3031` 破一次）。ht305 侧：服务器已到**第 12 代 `r54final`**（载荷 **509 只 / 4,805,345 B**、包 1,952,829 B / md5 `a5e1c600c2655089cdf6acde2c8522ff`、两侧聚合 sha256 `3af1f2e0…c02b` 同值、双向名单差集 0/0、`REMOTE_FORBIDDEN=0`），且往返实测 `VERDICT=REMOTE_CARRIES_PLAINTEXT`（远端 `provision_ap.c` 10,199 B / md5 `0419bf16…` == 工作树那只 ⇒ **服务器副本一直带明文是事实**，本机 `git grep HEAD` 仍 0 ⇒ **绝不 push**；服务器桌面 r 系列 **11 只 zip 并存、零删除**，从不删 ⇒ 任何一份都不是回滚源）。归档链末版 = **gen 21 @11:12:27 / `TOTAL 344` / `TOTAL_BYTES 1,141,974` / `BOM_FILES 62`**，`verify_manifest.py`（不接管道）`ROWS=344 / MISMATCH=0 / MISSING=0 / UNLISTED=0 / rc=0 / MANIFEST_STILL_TRUE`；`docs/` 快照 = **第八遍 @11:50:50，37 源 + NOTE = 38 只**（`CRED_GATE HITS=0 OF 37`、`NEW_ONES 1`、NOTE 4,626 B、stdout 载体 `%TEMP%\\refresh_docs_r54.txt`）。屏侧：**COM14 缺席**（11:23:26 与 11:39:17 两次现跑都是 COM3/COM4/COM5/COM6）⇒ §38.13 那两行判据样本数仍 **0**、我方日志分母仍是 **8 只 / 6 次上电**（09-23 起没多过一次串口动作）、**屏亮零次肉眼确认 ⇒ 不播提示音**；待烧 md5 `fb32168af14d715b354e691edfa39fcd` ≠ 板上 `4842a3a0c5f41ce2e60e3ceb122e9901`（(92) 那条分裂仍在原位，本批**没重建**）；`esp_gpio_hold_en()` 故意仍未加（等真机探针读数）。本批**零删除**、未新建备份根（判据 = `diff -rq` r53 两根各 **0 行**）。
'''

out = t + ADD
assert out.startswith(t) and out.count('\n') == t.count('\n') + ADD.count('\n')
assert '\r' not in out
b_in = len(t.encode('utf-8')); b_out = len(out.encode('utf-8'))
print('PRE OK  行数 %d -> %d  字节 %d -> %d' % (t.count('\n'), out.count('\n'), b_in, b_out))
if DRY:
    raise SystemExit('DRY: 未写盘')
open(P, 'w', encoding='utf-8', newline='').write(out)
back = open(P, encoding='utf-8', newline='').read()
assert back == out
print('WROTE', P, 'md5', hashlib.md5(back.encode('utf-8')).hexdigest()[:8], 'lines', back.count('\n'))
for k in ['(96)', '(97)', '(98)', '(99)', '(100)', 'R54 尾巴现场态换代']:
    print('POST', k, back.count('\n  ' + k))
