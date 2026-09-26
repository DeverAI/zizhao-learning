# -*- coding: utf-8 -*-
# backups/README.md 两处纯插入：§1 第八次读数 + §6 第八遍 docs 快照。
# 纪律：锚点唯一、纯插入（去掉两只新块必须逐字回到原文）、减号列恒 0。
import sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:/Users/david/Documents/all_projects/自招学习'
P = os.path.join(ROOT, 'backups', 'README.md')
DRY = '--dry' in sys.argv

t = open(P, encoding='utf-8', newline='').read()
assert '\r' not in t, '本只必须是纯 LF'
assert t.endswith('\n')

S1 = '''【09-24 **11:51:52 第八次读数**｜**与第六次相比只有一把尺动了，而且是往回动**：R53 那 3 只可执行代码已在 10:28:45 随 `39d3031` 进 commit ⇒ ① 从"4 只 / +315 / −19"回到 **1 只 / +210 / −14**，其余四把尺逐字未动 ⇒ **本轮不新建备份根**】
① **相对 `HEAD`**：`git -c core.quotePath=false diff HEAD --numstat -- hardware/zizhao-esp32s3/main` ⇒ **1 只 / +210 / −14**，那只仍是 `provision_ap.c`（自带 1 处明文、每轮被点名 DROP；mtime 09-19 15:50:08 ⇒ 本批没碰它）。⚠ 上一格这里是 **4 只 / +315 / −19**，回到 1 只**不是"代码被撤了"**，是那 3 只已进 commit（对账 = `git show --numstat 39d3031` 里 `main/` 侧 3 只 / +105 / −5）。
② **相对 r43 那两根**：`diff -rq` 两根各 **5 行**（与第六次同值 ⇒ r43 两根继续只是历史身份，不是现行镜像）。
③ **相对 r53 那两根**：`diff -rq backups/r53_20260924_083929/main hardware/zizhao-esp32s3/main` 与根 B 同一条 ⇒ **两根各 0 行输出** ⇒ 当前待烧镜像的构建输入仍只有这一根 ⇒ 本代不需要新根（第八次读数的"不新建根"就是这个判据给的）。
④ **工作树 `main/` 体量**：`ls -1 | wc -l` = **30 只**、python 现读字节 = **641,444 B**（与第六次逐字同值 ⇒ 本批零代码进工作树这句话就是这一格量的）。
⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main hardware/zizhao-esp32s3/main` ⇒ 仍 **3 行 differ**（第六次那句"本代过期"没有被"顺手修好"，也不该修——它是历史镜像，动它等于造第二把尺）。
⑥ **配套读数**：`git rev-list --count origin/main..HEAD` = **17**（11:39:03 现跑，未 push；上一格 16）；`md5sum C:/esp/zproj/build/zizhao_esp32s3.bin` = `fb32168af14d715b354e691edfa39fcd`（**md5，32 位 hex**）与 §3 那格逐字同值 ⇒ 本批**没重建**，"待烧 ≠ 板上"这条分裂仍在原位（板上 `4842a3a0…`）；`docs/` **第八遍**快照现 **38 只**（37 源 + `SNAPSHOT_NOTE.txt`，`SNAPSHOT_AT 11:50:50`，明文凭据闸 `HITS=0 OF 37`，明细在 §6 末格）。
⚠ **编号口径点名（本文件自己的历史账）**："第 N 次读数"在本文件**不是一条单一序列**——§1 上一格叫第六次、§7 末那格叫第七次、§5-补 里还有第二次、明文凭据那一族里另有第三次与第四次 ⇒ 引用时**连节号一起引**，不许拿"第七次"当"§1 的下一格"。本格按 §1 自己那一族续到第八次。

'''

S6 = '''- 【09-24 **11:50:50 第八遍 docs/ 快照刷新（r54 代脚本 = `%TEMP%\\refresh_docs_snapshot_r54.py`，由 `%TEMP%\\refresh_docs_snapshot_r53.py` 逐字派生）＝ R54 尾巴那批的归档义务**】载体**两只**：根 A 里的 `backups/r43_20260922_131029/docs/SNAPSHOT_NOTE.txt`（**4,626 B**）＋ 本遍 stdout 落的 `%TEMP%\\refresh_docs_r54.txt` ⇒ `CRED_GATE HITS=0 OF 37` / `SNAPSHOT_AT 2026-09-24 11:50:50` / `FILES 37` / `TABLE_ROWS 37 == FILES 37` / `NEW_ONES 1` / `NOTE_BYTES 4626`。**上一遍那句"本遍 stdout 没有另落载体、四个数是从 NOTE 反读的"在本遍不再适用**（"取证那一步自己没落盘"那一族的第 6 次，这次由执行者顺手把 stdout 重定向了，不是事后补的）。
  **`NEW` 那只**：`updates/20260924_墨水屏R54第12代同步与gen20-21冻结.md` ⇒ 其余 **36 只都是覆盖**，覆盖前后大小逐只成对登记在 NOTE 表里（表 37 行，由脚本的 `TABLE_ROWS == len(rows)` 断言自核，不靠手数）。
  **派生四处改动**：① `SRCS` 加那只 ⇒ 清单 **37** 只由脚本内 `len(SRCS)` 现读；② 完整性守卫只数下限 **35 → 36**（守卫本体、`MUST` 五只活文档、拷贝前明文凭据闸、拷后逐字节回读断言全部原样继承，没重写）；③ **本代新规矩：NOTE 里所有只数一律由脚本插值**，并加两道自核（表格行数 == `len(rows)`、`"现读 37 只源"` 那句必须真的在 NOTE 里）⇒ 上一代那处"NOTE 末段'35 只源'比自身表格晚了一代"**在本代的断言下过不了关**：这一族此前的处理都是订正文字，这次是**给文字装执行者**；④ 派生自述行本身。
  **派生过程自己也响过一次（登记，因为它是纪律的兑现）**：派生器 `%TEMP%\\derive_refresh_docs_r54.py` 首跑 `SyntaxError: '(' was never closed`（我把 ABORT 那句的右括号抄丢了），炸在写盘前的 `ast.parse` ⇒ 目标脚本当时**还不存在**，没有制造半成品。派生读数：父本 7,311 B / md5 前 8 位 `0e504f01`，子本 7,979 B / md5 `45813ba4`，`EDITED_LINES_TOTAL 7`，`difflib` 对照 = **+17 / −10** 行且改动只落在点名的那 6 个区域（头两行自述、`SRCS` 插入、守卫注释、阈值 + ABORT 文案、NOTE 派生自段、尾部自核块）。
  ⚠ **本遍快照的有界窗口（照 §1 那句"快照非终态"再兑一次）**：11:50:50 那一刻已含 11:46:25 落地的 `done.md` 200、`todo.md` 第十五遍、`dev_log/20260924.md` 的 R54 尾巴一节、上面那只新 `updates/` 件，以及 11:26:17 / 11:33:11 的 §38.17 与 FreqErr 四条 ⇒ **不含**本行自己（它 11:5x 之后才落地）与它之后的任何一笔 ⇒ 那几笔由**第九遍**快照收，本行不声称"已追平仓库"。
'''

A1 = '## 2. 命名规则\n'
A2 = '## 7. 归档对"计数类"口径的副作用（R42 实测，R43 扩了范围，务必知道）\n'
assert t.count(A1) == 1, '锚 1 不唯一: %d' % t.count(A1)
assert t.count(A2) == 1, '锚 2 不唯一: %d' % t.count(A2)
assert '第八次读数' not in t and '第八遍 docs/ 快照' not in t

out = t.replace(A1, S1 + A1).replace(A2, S6 + A2)
assert out.replace(S1, '').replace(S6, '') == t, '不是纯插入'
assert out.count('\n') == t.count('\n') + S1.count('\n') + S6.count('\n')
assert '\r' not in out

print('PRE OK  README lines %d -> %d  bytes %d -> %d  新增 %d 行' % (
    t.count('\n'), out.count('\n'), len(t.encode('utf-8')), len(out.encode('utf-8')),
    S1.count('\n') + S6.count('\n')))
if DRY:
    raise SystemExit('DRY: 未写盘')

open(P, 'w', encoding='utf-8', newline='').write(out)
back = open(P, encoding='utf-8', newline='').read()
assert back == out
print('WROTE', P, 'md5', hashlib.md5(back.encode('utf-8')).hexdigest()[:8])
print('POST 第八次读数 =', back.count('第八次读数'), '/ 第八遍 =', back.count('第八遍 docs/ 快照'), '/ 行数 =', back.count('\n'))
