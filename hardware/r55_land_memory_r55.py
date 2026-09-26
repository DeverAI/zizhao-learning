# R55 收口批 · 项目记忆 (101)-(102) + 现场态换代 + 用户记忆"工具自伤第七类"
# 派生自 hardware/ht305_sync/scripts/land_memory_r54.py（R54 尾巴那只），三处不同：
#  ①落点在归档目录之外（`hardware/`），因为 gen 24 是末版 ⇒ 任何写盘都不许进 `hardware/ht305_sync/`；
#  ②本脚本引用的每一个数都由本遍现跑算出并插值，正文里**不出现一个反斜杠**（§38.18 那处 CR 事故的直接防线），末尾断言兑现；
#  ③除了项目侧两只文件（正文 + 索引），还动用户侧两只（`reference-qoder-tool-mapping.md` 正文 + 用户索引第五行）。
# 口径：记忆是"跨会话的规矩"，不是台账 ⇒ 每条只写"形状 + 现跑等式 + 载体指针"。
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
UMEM = r'C:/Users/david/.qoder-cn/memory'
DOC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
SYNC = os.path.join(REPO, 'hardware', 'ht305_sync')
DOCS = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
CARRIER = os.path.join(REPO, 'hardware', 'r55_land_memory_r55.txt')


def sh(*args):
    return subprocess.run(args, capture_output=True, cwd=REPO).stdout.decode('utf-8', 'replace')


def md5(path):
    b = open(path, 'rb').read()
    return hashlib.md5(b).hexdigest(), len(b)


def read(p):
    return open(p, encoding='utf-8').read()


def write_lf(p, txt):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


# ---------- 现跑读数（每一个被写进记忆的数都在这里算，不在正文里手抄） ----------
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rev = sh('git', 'rev-list', '--count', 'origin/main..HEAD').strip()
por = [l for l in sh('git', '-c', 'core.quotePath=false', 'status', '--porcelain').split('\n') if l.strip()]
por_m = len([l for l in por if l[:2] == ' M'])
por_q = len([l for l in por if l[:2] == '??'])
assert por_m + por_q == len(por), 'status 分项 %d+%d != 总数 %d' % (por_m, por_q, len(por))

try:
    from serial.tools import list_ports
    ports = ', '.join(p.device for p in list_ports.comports()) or '(none)'
except Exception as e:
    ports = 'ERR:' + type(e).__name__

b_doc = open(DOC, 'rb').read()
doc_lines = b_doc.count(b'\n')
heads = [m.start() for m in re.finditer(rb'(?m)^#+ ', b_doc)]
heads23 = len(re.findall(rb'(?m)^#{2,3} ', b_doc))
no_blank = [b_doc[:i].count(b'\n') + 1 for i in heads
            if i > 0 and not (b_doc[max(0, i - 4):i].endswith(b'\r\n\r\n') or b_doc[max(0, i - 2):i].endswith(b'\n\n'))]
doc_md5, doc_bytes = md5(DOC)
sec18 = 1 + b_doc[:b_doc.find('### 38.18 '.encode())].count(b'\n')
sec19 = 1 + b_doc[:b_doc.find('### 38.19 '.encode())].count(b'\n')
assert not no_blank, '仍有 %d 只标题前缺空行：%s' % (len(no_blank), no_blank[:5])

# ---------- 上一遍（13:43:38 那次结构修复）的载体：修前/修后读数现读，正文里一个手抄数都不留 ----------
prev = open(os.path.join(REPO, 'hardware', 'r55_backups_readme9.txt'), encoding='utf-8').read()
pb_ = re.search(r'DOC_BEFORE bytes=(\d+) md5=([0-9a-f]+) lines=(\d+)\s+标题=(\d+)\s+缺空行=(\d+)', prev)
pa_ = re.search(r'DOC_AFTER\s+bytes=(\d+) md5=([0-9a-f]+) lines=(\d+)\s+缺空行=(\d+).*?§38\.18/19 行号=(\d+)/(\d+)', prev)
assert pb_ and pa_, '上一遍载体里读不到 DOC_BEFORE / DOC_AFTER 两行'
rd9_now = re.search(r'现跑于 ([0-9-]{10} [0-9:]{8})', prev).group(1)
doc_b0, doc_m0, doc_l0, heads0, nb0 = pb_.groups()
doc_b1, doc_m1, doc_l1, nb1, s18b, s19b = pa_.groups()
assert int(doc_b0) + 4 == int(doc_b1), '修复等式不成立（应 +4 = 两只 CRLF）：%s -> %s' % (doc_b0, doc_b1)
assert int(doc_l1) - int(doc_l0) == 2, '行数差不是 +2：%s -> %s' % (doc_l0, doc_l1)
assert nb0 == '2' and nb1 == '0', '缺空行数应 2 -> 0，载体里是 %s -> %s' % (nb0, nb1)
CROSS = (int(doc_b1), doc_m1, int(doc_l1), int(heads0))
PRESENT = (doc_bytes, doc_md5[:8], doc_lines, len(heads))
assert CROSS == PRESENT, '两把尺交叉核不过：现跑 %s vs 上一遍载体 %s' % (PRESENT, CROSS)
assert (sec18, sec19) == (int(s18b), int(s19b)), '节号行号与载体不符：%s/%s vs %s/%s' % (sec18, sec19, s18b, s19b)
assert len(heads) == heads23 + 1, '标题口径不自证：%d 只以 # 起始 vs %d 只二/三级 ⇒ 一级主标题应当正好 1 只' % (len(heads), heads23)

man = read(os.path.join(SYNC, 'MANIFEST.txt'))
man_total = re.search(r'^TOTAL\t(\d+)', man, re.M).group(1)
man_bytes = format(int(re.search(r'^TOTAL_BYTES\t(\d+)', man, re.M).group(1)), ',')
man_bom = re.search(r'^BOM_FILES\t(\d+)', man, re.M).group(1)
vr = read(os.path.join(REPO, 'hardware', 'verify_manifest_0924125339_2.txt'))
vr_rc = re.search(r'VERIFY_RC=(\d+)', vr).group(1)
vr_rows = re.search(r'ROWS=(\d+)', vr).group(1)
vr_unl = re.search(r'UNLISTED[^\d]*(\d+)', vr).group(1)
vr_verdict = re.findall(r'VERDICT=(\S+)', vr)[-1]
assert vr_rc == '0' and vr_rows == man_total and vr_unl == '0', '末版复核不自证：rc=%s rows=%s/%s unlisted=%s' % (vr_rc, vr_rows, man_total, vr_unl)

loc = read(os.path.join(SYNC, 'evidence', 'r55_local.txt'))
sel = re.search(r'selected\s+= (\d+)', loc).group(1)
payload_b = re.search(r'staged files\s+= \d+ \| bytes = (\d+)', loc).group(1)
zip_line = re.search(r'zip size/md5\s+= (\d+) ([0-9a-f]{32})', loc)
agg = re.search(r'LOCAL_AGGREGATE\s+= ([0-9a-f]{64})', loc).group(1)
rt2 = read(os.path.join(SYNC, 'evidence', 'r55_roundtrip_2.txt'))
# 这只文件里 **两只** 裁决同形：第 4 行 PRIOR_VERDICT=VERDICT=SCP_FAILED（上一遍转抄）、末行 VERDICT=REMOTE_CARRIES_PLAINTEXT（本遍）
# ⇒ 裸 re.search('VERDICT=(\S+)') 取到的是**上一遍**那一行（且连 'VERDICT=' 一起捕进组里）。必须行首锚 + 取最后一处。
rt2_verdict = re.findall(r'(?m)^VERDICT=(\S+)', rt2)[-1]
rt2_prior = re.search(r'(?m)^PRIOR_VERDICT=(\S+)', rt2).group(1)
assert rt2_verdict != rt2_prior, '本遍裁决与 PRIOR 那行同值 ⇒ 锚没生效：%s' % rt2_verdict
assert rt2_verdict == 'REMOTE_CARRIES_PLAINTEXT', '重跑裁决不是 REMOTE_CARRIES_PLAINTEXT：' + rt2_verdict
rt2_at = re.search(r'RAN_END_AT=(.*)', rt2).group(1).strip()

docfiles = sorted(f for f in os.listdir(DOCS) if f != 'SNAPSHOT_NOTE.txt')
note = read(os.path.join(DOCS, 'SNAPSHOT_NOTE.txt'))
note_rows = len([l for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
snap_at = re.search(r'刷新时刻 ([0-9: -]+)', note).group(1).strip()
gate_of = re.search(r'（口令由脚本从宏读出、不打印）：(\d+) 只源全扫', note).group(1)
note_hits = re.search(r'HITS\s*=\s*(\d+)', note)
assert note_hits and note_hits.group(1) == '0', 'docs 快照明文凭据闸读数不是 0：' + (note_hits.group(1) if note_hits else 'NOTE 里读不到 HITS')
assert len(docfiles) == int(gate_of) == note_rows, 'docs 三口径不符：目录 %d / NOTE 表格行 %d / 闸自述 OF %s' % (len(docfiles), note_rows, gate_of)

BUILD = 'C:/esp/zproj/build/zizhao_esp32s3.bin'
bin_md5, bin_bytes = md5(BUILD)
arc_md5, arc_bytes = md5(os.path.join(REPO, 'backups', 'r43_20260922_131029', 'zizhao_esp32s3.bin'))
rm_md5, rm_bytes = md5(os.path.join(SYNC, 'README.md'))
pyc = sum(1 for root, ds, fs in os.walk(os.path.join(REPO, 'backups'))
          for x in fs + ds if x == '__pycache__' or x.endswith('.pyc'))

R = dict(now=NOW, rd9_now=rd9_now, rev=rev, por=len(por), por_m=por_m, por_q=por_q, ports=ports,
         doc_b0=format(int(doc_b0), ','), doc_b1=format(int(doc_b1), ','),
         doc_l0=format(int(doc_l0), ','), doc_l1=format(int(doc_l1), ','),
         doc_m0=doc_m0, doc_m1=doc_m1, nb0=nb0, s18b=format(int(s18b), ','), s19b=format(int(s19b), ','),
         heads=len(heads), heads23=heads23, sec18=sec18, sec19=sec19, man_total=man_total, man_bytes=man_bytes,
         man_bom=man_bom, vr_rows=vr_rows, vr_unl=vr_unl, vr_verdict=vr_verdict,
         sel=sel, payload_b=format(int(payload_b), ','), zip_b=format(int(zip_line.group(1)), ','),
         zip_md5=zip_line.group(2)[:8], agg=agg[:8], rt2_verdict=rt2_verdict, rt2_at=rt2_at,
         docs_n=len(docfiles) + 1, docs_src=len(docfiles), snap_at=snap_at, gate_of=gate_of,
         bin_md5=bin_md5, bin_bytes=format(bin_bytes, ','), arc_md5=arc_md5, arc_bytes=format(arc_bytes, ','),
         rm_md5=rm_md5, rm_bytes=format(rm_bytes, ','), pyc=pyc, no_blank=len(no_blank))

# ---------- 待追加正文（**全段零反斜杠**：§38.18 那处静默 CR 的直接防线） ----------
BODY = (
    "  **R55（09-24 12:14:51 §38.18 落盘 → 12:53:39 gen 24 末版 → 13:33:42 docs 第九遍 → {rd9_now} backups/README.md 第九次读数）定下的 (101)-(102)**（本脚本落盘之后另有一遍订正，把这一段改成 (101)-(104) ⇒ **本脚本正文与盘上末段不再逐字相同，这是点名的差异、不是待修的漂移**）：\n"
    "  (101) **同一份取证里取两只独立时刻 = 造了一把只在跨边界那一瞬才假的尺**：归档链 gen 22 那遍 rc=1 / MANIFEST_STALE，可同一行里 ROWS=378 / MISMATCH=0 / MISSING=0 / UNLISTED=0 与汇总三字段逐项 OK ⇒ **数字全清白、裁决却红**。根因现读得出：scripts/gen_manifest.py 一次运行取了**两只** datetime.now()（清单头部与代次日志行各一只），中间隔着 378 只文件的哈希遍历 ⇒ 头部 12:34:41、日志末行 12:34:42，跨了一秒。那条判据（日志末行必须逐字符等于清单汇总）自 gen 9 就在 ⇒ **潜伏 12 个世代才第一次咬人**，因为它只在跨秒那一瞬才假。修法 = **只取一次时刻、另一只由它派生**（相等改由构造保证，不再由两次采样保证）+ verifier 把**判决与展示分家**（三字段进判据，时刻只并列打印）。⇒ 泛化：凡是 A 必须逐字等于 B 的判据，若 A 与 B 各来自一次独立采样，则**任何跨边界都会让它假红**；在考虑要不要放宽判据之前，先问这两个值是不是同一只变量。红的那遍原件入库、不重跑洗绿：hardware/ht305_sync/evidence/r55_verify_manifest_gen22_stale.txt。\n"
    "  (102) **纯插入式落地器只验正文没被吞，不验节与节之间那只空行 ⇒ 连续两代自己的落地器各写坏一次 Markdown 结构**：09-24 13:43 现跑，排查记录 {heads} 只标题（口径 = 每行以 # 起始，含 1 只一级主标题；二/三级 {heads23} 只）里有 **{nb0}** 只前面缺空行（### 38.17 紧跟 §38.16 末要点、### 38.19 紧跟 §38.18 ⑥），而这两只标题分别是 **R54 / R55 两代自己的落地器**写进去的 ⇒ 两代都栽在同一形状上。表现 = Read 与 grep 都不报错（标题仍是标题），只有渲染与'上一条列表项的续行'会静默吞掉它；抓它的量具只有一条：每只 ^### 标题的前一行必须是空行。修法 = 各补 1 只空行，现跑等式 {doc_b0} B → {doc_b1} B（+4 = 两只 CRLF）、{doc_l0} 行 → {doc_l1} 行、md5 {doc_m0} → {doc_m1}，复跑同一把量具 ⇒ 缺空行标题数 {nb0} → **{no_blank}**（本次现跑）。同族 (66)-(68) '跨行锚点 Edit 会静默删除原有结构' 讲的是**删**、本条讲的是**不加** ⇒ 落地器对周围结构的断言必须双向：既验没吞掉原有行，也验该给的空行给了。⚠ 第二层后果：这次修复**推翻了三处别人已登记的读数**（done.md 202 ⑥ 与 hardware/r55_sec38_19_check.txt 里的 {doc_b0} B / {doc_l0} 行 / §38.19 标题第 {s19b} 行）⇒ 结构类修复**不就地改历史登记**，只点名（与 (74)(82) '不许拿重跑链把红洗成绿' 同族），并连'节号随插行顺移'一起登记：§38.18 {s18b}→{sec18}、§38.19 {s19b}→{sec19}。\n"
    "  **R55 现场态换代（{now} 现跑；取代上面 R54 尾巴现场态那一段的 rev-list、status 只数、同步代次、归档 gen 末版、docs 快照五条）**："
    "git rev-list --count origin/main..HEAD = **{rev}**（HEAD 仍是 39d3031，第九次提交轮在本段之后）；"
    "git -c core.quotePath=false status --porcelain = **{por_m} 只 M + {por_q} 只 ?? = {por} 行**（{now}），同一刻用户端仍报 **66** ⇒ 三把尺互不可换算（承接第十三、十五、十六遍那条 ⚠，只登记各自的数、不拿 {por} 去驳回 66）；"
    "M 里 main/ 侧仍只有 provision_ap.c（mtime 09-19 15:50:08）⇒ **R54/R55 两批零代码进工作树**。"
    "ht305 侧：服务器已到**第 13 代 r55final**（载荷 **{sel} 只 / {payload_b} B**、包 **{zip_b} B / md5 {zip_md5}…**、两侧聚合 sha256 **{agg}…**（64 位 hex，非截断）逐字等、双向名单差集 0-0、解包根 zsynctest15（一根只喂一代）、scp 之前桌面探测 13 只同步包并存 + TARGET_EXISTS=False ⇒ 仍零删除）；"
    "往返 12:26:11 首跑 SCP_RC=255 失败（原件留册 evidence/r55_roundtrip.txt）、12:27:39 重跑 ⇒ **{rt2_verdict}** ⇒ 服务器那一份**仍带明文**，任何一代都**不是回滚源**。"
    "归档链末版 = **gen 24 @12:53:39 / TOTAL {man_total} / {man_bytes} B / BOM {man_bom}**，终态复核（不接管道）VERIFY_RC=0 / {vr_verdict} / ROWS={vr_rows} / MISMATCH=0 / MISSING=0 / UNLISTED={vr_unl}，且 13:4x 拿同一把尺复跑逐字同值（载体 hardware/verify_manifest_0924125339_2.txt）⇒ **gen 24 之后归档目录一只都没再落**（本批所有写盘都在 hardware/ 与仓库根）。"
    "docs/ 快照 = **第九遍 @{snap_at}，{docs_src} 源 + NOTE = {docs_n} 只**（明文凭据闸 HITS=0 OF {gate_of}、NEW_ONES 1），执行件这次**在仓库内** = hardware/refresh_docs_snapshot_r55.py ⇒ §38.18 缺陷一（取证只落在 TEMP）由源头堵住，不再靠'落地器搬进来'；backups/ 下 __pycache__ 与 .pyc 现跑 = **{pyc}**。"
    "屏侧：**COM14 缺席**（12:14:51 / 13:31:55 / 13:43:38 三次现跑都是 {ports}）⇒ §38.13 两行判据样本数仍 **0**、我方日志分母仍是 8 只 / 6 次上电、屏亮 **0 次肉眼确认** ⇒ **不播提示音**；"
    "待烧 {bin_md5}（**md5，32 位 hex，不是 sha256**）/ {bin_bytes} B ≠ 板上与 r43 归档那只 {arc_md5} / {arc_bytes} B ⇒ (92) 那条分裂仍在原位、本批**没重建**；esp_gpio_hold_en() 故意仍未加（等 hold-on 探针真机读数）。"
    "hardware/ht305_sync/README.md = {rm_bytes} B / md5 {rm_md5} 与末版清单那一行同值 ⇒ **归档内某只文件的当前字节只引末版清单那一行**，不引任何落地器的自述（§38.19 ⑥ 那条的第二遍）。"
    "本批**零删除**；**不新建备份根**的判据这次是 diff -rq r53 两根各 **0 行** 的**第二次独立复跑**（§38.19 本节没做 ② 欠的那次），五把尺与第八次读数逐字同值见 backups/README.md §1 第九次读数那一格（载体 hardware/r55_backups_readme9.txt）。\n"
).format(**R)

assert '\\' not in BODY, '待追加正文里出现了反斜杠 ⇒ 正是 §38.18 那一族'

IDX = (" **R55 收口批另立 (101)-(102)**：同一份取证取两只独立时刻 = 只在跨边界那一瞬才假的尺（gen 22 假红，判据潜伏 12 个世代）⇒ 相等要由构造保证；纯插入式落地器不验节间空行（连续两代各写坏一次，修复又推翻三处已登记读数 ⇒ 不就地改数、只点名）。"
       "**R55 现场态换代**：rev-list = {rev} / 第 13 代 r55final {sel} 只 {payload_b} B、解包根 zsynctest15、{rt2_verdict} ⇒ 服务器侧仍非回滚源 / gen 24 末版 TOTAL {man_total} / {man_bytes} B / BOM {man_bom}，VERIFY_RC=0 复跑同值 ⇒ 归档之后零污染 / docs 第九遍 {docs_n} 只 @{snap_at}、执行件已在仓库内 / COM14 三次现跑缺席 ⇒ 屏亮 0 次肉眼确认、不播提示音 / 待烧 {bin_md5} ≠ 板上 {arc_md5} / diff -rq r53 两根各 0 行 ⇒ 不新建根、零删除。")\
    .format(**R)

USER_T = ("- **命令行 / 非 raw python 串里的 Windows 反斜杠会把路径吃成一只**肉眼不可见的 CR**（第七类自伤，2026-09-24 实证）**："
          "把 TEMP 目录路径写进**非 raw** 的串 ⇒ 那个反斜杠加 r 就是**一个 CR 字节**；随后按习惯把反斜杠**双写**求稳，命令文本落到 python 时双写又塌成单写 ⇒ 两种写法殊途同归（同一写法在'恰好全 ASCII'的场合还会让断言永真）。"
          "盘上最终形态 = 目录名 + `0x0D` + 丢了首字母的文件名，而**三只量具同时看不见**：grep 那只文件名 = **0 命中**（首字母被吃了）、拿损坏原文当 Edit 的 old_string = **0 命中**、Read 显示时 **CR 不可见**。"
          "唯一暴露手法 = **字节级 CR 计数**；判据是**该文件登记的行尾口径**（纯 LF 的文件里任何 CR 都是入侵者；纯 CRLF 的 stdout 载体 6 只 CR 合法），**不是'有 CR 即错'**。"
          "对策：路径一律 raw 串或正斜杠；改纯 LF 文件前后各数一次 CR 并要求 0；落地脚本末尾加一句'待追加文本里不许出现反斜杠'的断言。\n")

# ---------- 落地（四只文件，全是 LF 追加/行内替换，零删除） ----------
targets = [
    (os.path.join(PMEM, 'hardware-epaper397-power.md'), 'append-eof', BODY),
    (os.path.join(PMEM, 'MEMORY.md'), 'line5-append', IDX),
    (os.path.join(UMEM, 'reference-qoder-tool-mapping.md'), 'bullet-before-tail', USER_T),
    (os.path.join(UMEM, 'MEMORY.md'), 'six2seven', None),
]
before = {}
for p, kind, txt in targets:
    b = open(p, 'rb').read()
    before[p] = (b.count(b'\n'), len(b), b.count(b'\r'), hashlib.md5(b).hexdigest()[:8], b.decode('utf-8'))

# 幂等闸：本脚本要在"落地已完成"的状态下复跑（上一次跑到写载体时格式崩了），
# 所以先判四只文件是不是**全部**已落地；半落地直接 ABORT，不猜。
MARK = ['  (102) **纯插入式落地器', 'R55 收口批另立 (101)-(102)', '- **命令行 / 非 raw python 串里的 Windows 反斜杠', 'Write/Edit 七类自伤']
landed = [m in before[p][4] for (p, _k, _t), m in zip(targets, MARK)]
assert sum(landed) in (0, 4), '四只文件半落地（landed=%s）⇒ 先人工核对再跑' % landed
MODE = 'REWROTE_CARRIER_ONLY' if all(landed) else 'LANDED_NOW'
_pb0 = before[os.path.join(PMEM, 'hardware-epaper397-power.md')][4]
_bn = re.search(r'\*\*R55 现场态换代（([0-9-]{10} [0-9:]{8}) 现跑', _pb0)
assert MODE == 'LANDED_NOW' or _bn, '跳过写盘却读不到"落地那一遍"的时刻 ⇒ 载体无法点名'
BODY_NOW = _bn.group(1) if _bn else NOW

out = []
for p, kind, txt in targets:
    old_ln, old_b, old_cr, old_md5, old_t = before[p]
    if MODE == 'REWROTE_CARRIER_ONLY':
        out.append('FILE %s\n  now   LF=%d bytes=%d md5=%s（本遍未写盘，落地由 @%s 那一遍完成）\n'
                   % (os.path.basename(p) if os.path.basename(p) != 'MEMORY.md' else p.split('/')[-3] + '/MEMORY.md',
                      old_ln, old_b, old_md5, BODY_NOW))
        continue
    if kind == 'append-eof':
        assert old_t.endswith('\n'), p + ' 末行没有换行'
        new_t = old_t + txt
    elif kind == 'line5-append':
        ls = old_t.split('\n')
        assert len(ls) > 5 and ls[4].startswith('- [墨水屏板供电现状]'), p
        ls[4] = ls[4] + txt
        new_t = '\n'.join(ls)
    elif kind == 'bullet-before-tail':
        anchor = '。\n\n关联：[[feedback-engineering-workflow]]'
        assert old_t.count(anchor) == 1, p + ' 锚点不唯一'
        new_t = old_t.replace(anchor, '。\n' + txt + '\n关联：[[feedback-engineering-workflow]]')
    else:
        old_s = 'Write/Edit 六类自伤（参数逐字入库、全行锚点、表行被换行劈开、尾行改名、**相邻结构被静默删除**）'
        new_s = 'Write/Edit 七类自伤（参数逐字入库、全行锚点、表行被换行劈开、尾行改名、**相邻结构被静默删除**、**非 raw 串里的反斜杠 = 一只隐形 CR，grep/Edit/Read 三把量具同时瞎**）'
        assert old_t.count(old_s) == 1, p + ' 六类那句不唯一'
        new_t = old_t.replace(old_s, new_s)
    assert new_t.count('\r') == 0 and old_cr == 0, p + ' 引入 CR'
    assert '\\' not in txt if txt else True, p + ' 追加文本含反斜杠'
    write_lf(p, new_t)
    nb = open(p, 'rb').read()
    out.append('FILE %s\n  before LF=%d bytes=%d md5=%s\n  after  LF=%d bytes=%d md5=%s\n'
               % (os.path.basename(p) if os.path.basename(p) != 'MEMORY.md' else p.split('/')[-3] + '/MEMORY.md',
                  old_ln, old_b, old_md5, nb.count(b'\n'), len(nb), hashlib.md5(nb).hexdigest()[:8]))

# ---------- 修后复核（不换尺：仍用字节级 CR 计数 + 逐字回读被追加的那段） ----------
checks = []
pb = read(os.path.join(PMEM, 'hardware-epaper397-power.md'))
for m in ['(101)', '(102)', 'R55 现场态换代']:
    checks.append('%s 命中 %d' % (m, pb.count(m)))
assert pb.count('(101)') == 2 and pb.count('(102)') == 2 and pb.count('R55 现场态换代') == 1, \
    '两条新规应各命中 2 次（段标题那一处 + 条目自己那一处）：' + ' '.join('%s=%d' % (m, pb.count(m)) for m in ['(101)', '(102)', 'R55 现场态换代'])
ls_pb = pb.split('\n')
i55 = [k for k, l in enumerate(ls_pb) if l.startswith('  **R55（')]
assert len(i55) == 1, '排查正文里 R55 段标题应有且只有 1 处，现 %d 处' % len(i55)
i55 = i55[0]
assert [l.lstrip()[:5] for l in ls_pb[i55 + 1:i55 + 4]] == ['(101)', '(102)', '**R55'], \
    'R55 那一段的四行结构不符：%s' % [l[:12] for l in ls_pb[i55:i55 + 4]]
assert i55 + 4 == len(ls_pb) - 1, 'R55 段没有落到 EOF：后面还有 %d 行' % (len(ls_pb) - i55 - 5)
if MODE == 'LANDED_NOW':
    assert pb.endswith(BODY), '项目正文末段与本次追加的字节不逐字相同'
ix = read(os.path.join(PMEM, 'MEMORY.md'))
assert 'R55 收口批另立 (101)-(102)' in ix and ix.count('\n') == before[os.path.join(PMEM, 'MEMORY.md')][0], '索引行多了行'
ub = read(os.path.join(UMEM, 'reference-qoder-tool-mapping.md'))
assert ub.count('第七类自伤') == 1, '用户正文那一类没落地'
ui = read(os.path.join(UMEM, 'MEMORY.md'))
assert '七类自伤' in ui and '六类自伤' not in ui, '用户索引没换口径'
for p, kind, txt in targets:
    b = open(p, 'rb').read()
    assert b.count(b'\r') == 0, 'CR 入侵：' + p

with open(CARRIER, 'w', encoding='utf-8', newline='\n') as f:
    f.write('R55 项目记忆 (101)-(102) + 现场态换代 + 用户记忆第七类，本遍现跑于 %s；MODE=%s（正文里那些时刻 = %s）\n'
            % (NOW, MODE, BODY_NOW))
    f.write('FIELD rev-list=%s porcelain=%d(M%d+??%d) ports=%s\n' % (rev, len(por), por_m, por_q, ports))
    f.write('DOC heads=%d（其中二/三级 %d） 缺空行=%d 节号 38.18=%d 38.19=%d bytes=%s lines=%s md5=%s\n'
            % (len(heads), heads23, len(no_blank), sec18, sec19, format(doc_bytes, ','), doc_lines, doc_md5[:8]))
    f.write('SYNC 13 代 %s 只 / %s B / 包 %s B md5 %s / 聚合 %s… / 重跑 %s @%s\n'
            % (sel, payload_b, zip_line.group(1), zip_line.group(2), agg, rt2_verdict, rt2_at))
    f.write('GEN24 TOTAL=%s / %s B / BOM %s ; VERIFY2 rc=%s ROWS=%s UNLISTED=%s %s\n'
            % (man_total, man_bytes, man_bom, vr_rc, vr_rows, vr_unl, vr_verdict))
    f.write('DOCS %s 只（%s 源 + NOTE）@%s 闸 OF %s HITS 0 ; pyc/pycache=%s\n'
            % (R['docs_n'], R['docs_src'], snap_at, gate_of, pyc))
    f.write('CROSSCHECK DOC_AFTER(上一遍载体) %s/%s/%s 标题=%s vs 现跑 %d/%s/%d 标题=%d ; 缺空行 载体=%s 现跑=%d\n'
            % (doc_b1, doc_m1, doc_l1, heads0, doc_bytes, doc_md5[:8], doc_lines, len(heads), nb1, len(no_blank)))
    f.write('README %s B md5 %s ; BIN build md5=%s / %s B != 板上归档 md5=%s / %s B\n'
            % (rm_bytes, rm_md5, bin_md5, bin_bytes, arc_md5, arc_bytes))
    f.write('BACKSLASH_IN_APPENDED_TEXT=0（§38.18 CR 事故的直接防线，由末尾断言兑现）\n')
    f.write('LANDING_SEQUENCE 第一次跑到这一步（同一脚本、正文已落盘）在写本载体的 CROSSCHECK 那一行崩在 TypeError: %%d 遇到 str'
            '⇒ 载体当场没写；本遍 MODE=%s 用幂等闸跳过四只文件的写盘、只复算并复核后补写本载体\n' % MODE)
    f.write(''.join(out))
    f.write('VERDICT=%s\n' % ('MEMORY_LANDED' if MODE == 'LANDED_NOW' else 'MEMORY_VERIFIED_CARRIER_WRITTEN'))

print('MODE', MODE, 'BODY_NOW', BODY_NOW, 'CARRIER_NOW', NOW)
print('REV', rev, 'PORCELAIN', len(por), '=', por_m, 'M +', por_q, '??')
print('DOC_HEADS', len(heads), 'NO_BLANK_BEFORE', len(no_blank), 'SEC38.18@', sec18, 'SEC38.19@', sec19)
print('GEN24 TOTAL', man_total, 'VERIFY2_RC', vr_rc, 'UNLISTED', vr_unl)
print('DOCS', R['docs_n'], 'SRC', R['docs_src'], '@', snap_at, 'GATE_OF', gate_of)
print('BACKSLASH_CHECK=0 IN ALL APPENDED TEXTS')
print('CARRIER=hardware/r55_land_memory_r55.txt')
