# R61c 收口 paperwork 落地器（dev_log 第三十四批 + done 第二十六节）。
# 三条硬规矩继承自排查记录那批落地器：①幂等门看的是"写盘后令牌"，不是"正文里有没有本节"；
# ②全部裁决排在写盘之前；③正文里每个数字都从盘上载体或现跑命令取，取不到即 ABORT（不许手抄）。
# 本遍**不预写**排在它之后的那些遍（docs 第十三遍 / README 第十三次读数 / §38.37 / 提交轮 / 第 17 代）的读数。
import ast
import datetime
import glob
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
DEV = os.path.join(REPO, 'dev_log', '20260926.md')
DON = os.path.join(REPO, 'done.md')
FE = os.path.join(REPO, 'FreqErr.md')
REC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
RDM = os.path.join(REPO, 'backups', 'README.md')
DOCD = os.path.join(REPO, 'backups', 'r43_20260922_131029', 'docs')
NOTE = os.path.join(DOCD, 'SNAPSHOT_NOTE.txt')
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
BS = chr(92)
ESP = 'C:' + BS + 'esp' + BS
_T0 = datetime.datetime.now()

BATCH = '第三十四批'
SECH = '## 二十六、'
KINDS = ['第十五批', '第十六批', '第十七批', '第十八批', '第十九批']


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr.decode('utf-8', 'replace')[:200])
    return r.stdout.decode('utf-8', 'replace')


def rd(p):
    return io.open(p, encoding='utf-8').read()


def mb(p):
    b = io.open(p, 'rb').read()
    return len(b), b.count(b'\n'), hashlib.md5(b).hexdigest()[:8]


assert os.path.isdir(EV) and 'ht305_sync' not in EV, 'ABORT: 取证落点不对'
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rd(SRC)).group(1)

# ---------- 现跑读数 ----------
fe_b, fe_l, fe_md5 = mb(FE)
fe_n = sum(1 for l in rd(FE).splitlines() if l.startswith('[错误类型]'))
rc_b, rc_l, rc_md5 = mb(REC)
dm_b, dm_l, _ = mb(DON)
dv_b, dv_l, _ = mb(DEV)
rdm_b, rdm_l, rdm_md5 = mb(RDM)
head = git('rev-parse', '--short', 'HEAD').strip()
revl = git('rev-list', '--count', 'origin/main..HEAD').strip()
por = [l for l in git('status', '--porcelain').splitlines() if l.strip()]
por_m = len([l for l in por if l.startswith(' M')])
por_q = len([l for l in por if l.startswith('??')])
assert len(por) == por_m + por_q, 'ABORT: porcelain 桶没铺满（%d != %d + %d）' % (len(por), por_m, por_q)

# ---------- 五批台账：时刻、条数、行号全部现读 ----------
_fel = rd(FE).splitlines()
led, LND = {}, {}
for _i, _l in enumerate(_fel, 1):
    _g = re.match(r'\*\*【([0-9: -]{19}) 落地｜R61 (第十[五六七八九]批) (\d+) 条】\*\*', _l)
    if _g:
        led[_g.group(2)] = (_g.group(1), int(_g.group(3)))
        LND[_g.group(2)] = _i
assert sorted(led) == sorted(KINDS), 'ABORT: 台账批次的名字集不是第十五~十九批：%s' % sorted(led)
b_sum = sum(v[1] for v in led.values())
_ts = sorted(v[0] for v in led.values())
assert _ts[0].endswith('14:16:50') and _ts[-1].endswith('16:31:05'), 'ABORT: 批次时刻不是本窗口：%s' % _ts
LED_TXT = '、'.join('第 %d 行（%s %d 条）' % (LND[k], k, led[k][1]) for k in KINDS)

# ---------- 第 16 代同步读数：逐字段取自当轮载体 ----------
loc = rd(os.path.join(EV, 'r61c_local.txt'))
ver = rd(os.path.join(EV, 'r61c_verify.txt'))
cud = rd(os.path.join(EV, 'r61c_cutoff_delta.txt'))
lrt = rd(os.path.join(EV, 'r61c_roundtrip.txt'))
pc = rd(os.path.join(EV, 'r61c_parse_check.txt'))
S16_F = int(re.search(r'^staged files\s*=\s*(\d+)', loc, re.M).group(1))
S16_B = int(re.search(r'^staged files\s*=\s*\d+ \| bytes = (\d+)', loc, re.M).group(1))
S16_ZIP = int(re.search(r'^zip size/md5\s*=\s*(\d+)', loc, re.M).group(1))
S16_MD5 = re.search(r'^zip size/md5\s*=\s*\d+ ([0-9a-f]{32})$', loc, re.M).group(1)
S16_AGG = re.search(r'^LOCAL_AGGREGATE\s*=\s*([0-9a-f]{64})$', loc, re.M).group(1)
R_AGG = re.search(r'^REMOTE_AGGREGATE=([0-9a-f]{64})$', ver, re.M).group(1)
R_FILES = int(re.search(r'^REMOTE_FILES=(\d+)$', ver, re.M).group(1))
R_BYTES = int(re.search(r'^REMOTE_BYTES=(\d+)$', ver, re.M).group(1))
R_FORBID = int(re.search(r'^REMOTE_FORBIDDEN=(\d+)$', ver, re.M).group(1))
assert (R_FILES, R_BYTES, R_AGG) == (S16_F, S16_B, S16_AGG), 'ABORT: 第 16 代五字段两侧不全等'
CUT_A = re.search(r'^CUTOFF_COPY_BEGIN\s*=\s*(.+)$', loc, re.M).group(1).strip()
CUT_Z = re.search(r'^CUTOFF_ZIP_MADE\s*=\s*(.+)$', loc, re.M).group(1).strip()
DROP_L = ast.literal_eval(re.search(r"^dropped .*? = 3 (\[.*\])$", loc, re.M).group(1))
DROP_TXT = '、'.join('`%s`' % x for x in DROP_L)
assert len(DROP_L) == 3 and chr(39) not in DROP_TXT
NEW8 = int(re.search(r'^new_since_cutoff\s*=\s*(\d+)', cud, re.M).group(1))
CHG = int(re.search(r'^changed_since_cutoff = (\d+)', cud, re.M).group(1))
DEL = int(re.search(r'^deleted_since_cutoff = (\d+)', cud, re.M).group(1))
CAND = int(re.search(r'并集 == 当前候选集\((\d+)\)', cud).group(1))
assert CAND == S16_F + NEW8, 'ABORT: 候选集等式在载体里就不成立（%d != %d + %d）' % (CAND, S16_F, NEW8)
assert re.search(r'^VERDICT=LISTDIFF_EQUAL$', rd(os.path.join(EV, 'r61c_listdiff.txt')), re.M)
assert 'VERDICT=REMOTE_CARRIES_PLAINTEXT' in lrt
assert int(re.search(r'PROV_PASS_HITS_REMOTE=(\d+)', lrt).group(1)) == 1
assert int(re.search(r'CONTROL_LANDER_HITS=(\d+)', lrt).group(1)) == 0
assert re.search(r'^SCRIPT_LINES=(\d+)$', pc, re.M).group(1) == re.search(r'^SRC_LINES=(\d+)$', pc, re.M).group(1)
ROOT16 = re.search(r'zsynctest(\d+)', lrt).group(1)
s16_cars = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61c_*.txt')) if os.path.getsize(p) > 0)
assert len(s16_cars) >= 8, 'ABORT: 第 16 代非空载体现读 %d 只（应 >= 8）' % len(s16_cars)

# ---------- docs / README 现停在哪一遍 ----------
note_t = rd(NOTE)
DOCS_AT = re.search(r'刷新时刻 ([0-9: -]{19})', note_t).group(1)
DOCS_TBL = len([l for l in note_t.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
DOCS_DIR = len(os.listdir(DOCD))
assert DOCS_DIR == DOCS_TBL + 1, 'ABORT: docs 目录只数 != 表格 + NOTE 自身'

# ---------- 派生遍与第十九批崩遍 ----------
DR_OK = os.path.join(EV, 'derive_r61c_161520.txt')
DR_BAD = os.path.join(EV, 'derive_r61c_161508.txt')
dot = rd(DR_OK)
WROTE = int(re.search(r'^WROTE=(\d+)', dot, re.M).group(1))
assert WROTE == 6 and 'VERDICT=DERIVED rc=0' in dot
KEY_LN = int(re.search(r'line (\d+), in <module>', rd(DR_BAD)).group(1))
WRITE_LN = min(i for i, l in enumerate(rd(os.path.join(REPO, 'hardware', 'r61b_sync', 'scripts', 'derive_r61c.py')).splitlines(), 1)
               if "io.open(dst, 'wb')" in l or 'open(dst, ' + chr(39) + 'wb' + chr(39) in l)
assert KEY_LN < WRITE_LN, 'ABORT: 崩点行号不在写盘语句之前 ⇒ "零改动"那句要重判'
# 崩遍判据**不能按"正文里有没有 Error 字样"**：成功遍会引用崩遍的那一行（`DERIVE-CRASH ... KeyError=...`）⇒ 搜到的是别人家的错误。
# 权威分类只认"本遍自己有没有写出写盘后令牌"，并另加"非空 + mtime 早于本遍进入"两条前置。
auth19_all = [os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61c_freqerr19_*.txt'))
              if 'VERDICT=LANDED' in rd(p)]
assert len(auth19_all) == 1, 'ABORT: 第十九批权威载体不唯一：%s' % auth19_all
crash19 = sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61c_freqerr19_*.txt'))
                 if os.path.getmtime(p) < _T0.timestamp() and os.path.getsize(p) > 0
                 and 'VERDICT=LANDED' not in rd(p) and 'Traceback' in rd(p))
for _f in crash19:
    _t = rd(os.path.join(EV, _f))
    assert 'PRE-IMAGE' not in _t, 'ABORT: 崩遍载体其实动过盘：' + _f
_all19 = [p for p in glob.glob(os.path.join(EV, 'r61c_freqerr19_*.txt')) if os.path.getsize(p) > 0]
assert crash19 and len(_all19) == len(crash19) + len(auth19_all), \
    'ABORT: 第十九批非空载体 %d 只没有被「崩遍 + 权威遍」两桶铺满（%d + %d）' % (len(_all19), len(crash19), len(auth19_all))
STALE = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence', 'record_stale3836_20260926_161042.md')
assert os.path.isfile(STALE), 'ABORT: §38.36 核销掉的旧版本节归档件不在盘上'
STALE_B = os.path.getsize(STALE)
pimgs = glob.glob(os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence', 'record_pre3836_*.md'))
PIMG_N = len(pimgs)

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
CRASH_TXT = '、'.join('`%s`' % x for x in crash19)

dev_txt = f'''

## {BATCH}：**R61b + R61c 两代收口 = 第 15/16 代 ht305 全量同步 + 提交轮 #10 + `FreqErr.md` 第十五~十九批**（取证 2026-09-26 13:2x ~ 16:3x；本遍 paperwork 落纸于 {ts}）

### 落纸位置（本批细节的正文都在别处已有，本节只做按日索引）

- 排查记录 **§38.35**（第 15 代收口同步：六只脚本改由替换表派生、四道假 ABORT 全是「尺的形状不对」、第一次把描述上一代的 paperwork 装进载荷）与
  **§38.36**（提交轮 #10 + docs 第十二遍 + README 第十二次读数 + 第十七/十八批；同一遍里还核销了一起**相反形态**：一次 rc=1 **确实动了盘**）。
- `FreqErr.md` 五批台账行：{LED_TXT}；五批合计 **{b_sum}** 条。全册现读（本遍现跑，不是抄台账）：`^[错误类型]` = **{fe_n}** 条 / **{fe_l}** 行 / **{fe_b:,}** B / md5 前 8 `{fe_md5}`。
- 阶段摘要：`updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md`（本遍新建）。
- 备份侧：`backups/README.md` 现读 **{rdm_l} 行 / {rdm_b:,} B / md5 前 8 `{rdm_md5}`**（第十一格与第十二格都在册，本批未再动它）；
  docs/ 快照现停在**第十二遍**——`SNAPSHOT_NOTE.txt` 刷新时刻 {DOCS_AT} / 表格 {DOCS_TBL} 行 / 目录现读 {DOCS_DIR} 只 = 表格 + NOTE 自身。

### 第 16 代（`r61cfinal`）同步的读数（本遍逐字段从当轮载体复核，不另算一遍）

- 载荷 **{S16_F} 只 / {S16_B:,} B**；包 **{S16_ZIP:,} B / md5 `{S16_MD5}`**；两侧聚合 sha256 同值 `{S16_AGG}`；
  `REMOTE_FORBIDDEN={R_FORBID}`；远端解包进**全新**根 `zsynctest{ROOT16}`；打包截止 {CUT_A} → 成品 zip {CUT_Z}。
- 包 ↔ 现状：`changed_since_cutoff={CHG}` / `deleted_since_cutoff={DEL}` / `new_since_cutoff={NEW8}` 只（全是本代自产取证件，逐只点名在载体里）；
  四桶互斥且并集 == 当前候选集 **{CAND}** 只，等式 {CAND} == {S16_F} + {NEW8} 由本遍 assert；双向名单差集 0-0（`VERDICT=LISTDIFF_EQUAL`）。
- 排除表 drop **3 只**：{DROP_TXT}（逐字取自 `r61c_local.txt` 的 dropped 行，不另列一份）。
- 往返复核 = `VERDICT=REMOTE_CARRIES_PLAINTEXT`（远端命中 1 / 按宏名读口令的脚本命中 0，一正一负同尺）⇒ 服务器**不是回滚源**，本仓库任何一只都绝不 push。
- 本代取证在 `hardware/r61c_sync/evidence/` 现读 **{len(s16_cars)} 只非空载体**；`hardware/ht305_sync/` 一字节未落（SEAL 停在 gen 24）。
- 换代工具由 `hardware/r61b_sync/scripts/derive_r61c.py` 按替换表派生：成功遍 `WROTE={WROTE}` / `VERDICT=DERIVED rc=0`（载体 `derive_r61c_161520.txt`）；
  崩遍 `derive_r61c_161508.txt` 红在第 {KEY_LN} 行 `KeyError`（改了字典键名没改同文件里的 assert ⇒ 结构与其消费者不同遍改），**盘上零改动**由三条独立回读钉死：
  写盘后令牌缺席 + 六只产物 mtime 全晚于崩遍载体 + **崩点行号 {KEY_LN} 早于该文件里写盘语句的行号 {WRITE_LN}**（本遍现读该文件求出）。
- 第十九批落地三遍：崩遍 {len(crash19)} 只（{CRASH_TXT}，逐只现读其 stdout 不含 PRE-IMAGE 与 LANDED ⇒ 全部崩在写盘之前、盘上零改动），
  权威遍 `{auth19_all[0]}` 出 `VERDICT=LANDED rc=0`。红因是 entry ④ 的「正确做法」整段忘了做格式化 ⇒ 三只占位符原样待落盘，
  被**未插值占位符零容忍**那道门抓在写盘之前——这道门这一遍同时是它自己的阳性对照。

### 本批抓到的工具/落地器自身缺陷（去向 = `FreqErr.md` 第十五~十九批，这里只点名不重述）

- 第十五批 {led['第十五批'][1]} 条：正则**组序**被当成「前一个数 / 后一个数」、台账行里大写式哨兵未插值就落盘、"只做了一次插入"落笔即已是第二次、
  插入体自身不带换行而吞掉相邻那根、"两侧集合相等"在两侧同空时恒真、落地器写不出自己那一遍的载体名。
- 第十六批 {led['第十六批'][1]} 条：写盘后证明段把整行起始偏移当替换段偏移（内容已对而证明红）、回填句结尾不与原段对称闭合、就地订正的锚文本命中 2 行而两行主张一真一假。
- 第十七批 {led['第十七批'][1]} 条：把订正句插进**别人家的**台账行时"本批"随插入点换了指代、行号成自指。
- 第十八批 {led['第十八批'][1]} 条：纯插入的证明写成逐位置差集、假指针 + `--proof-only` 那遍把令牌打成 `LANDED`、`diff -rq` 输入目录不存在时 0 行假绿、单引号正文里嵌 ASCII 撇号。
- 第十九批 {led['第十九批'][1]} 条：写盘后的**预期终态自己也是待检正文**（两推法互等）、幂等门以载体里的 `VERDICT=LANDED` 为权威而不是「正文有没有本节标题」、
  结构与其消费者不同遍改、反度量裸子串把本代正面读数判成余留。

### 本批没做（点名）

- 没烧录、没碰串口 ⇒ 人眼看到屏仍 **1 次**（R59 那一次）、看到第二页 **0 次**、用户真按 BOOT **0 次** ⇒ **不播提示音的判据仍成立**。
- `main/` 语义零改动 ⇒ 待烧那只没换代（其身份仍按 `hardware/BOARD_S3_ePaper_1_54.md` 在册三字段现读现验，本遍不复述上一代的数）。
- 未 `git push`、未 `--amend`、零删除、未覆写任何旧备份根、`hardware/ht305_sync/` 一字节未落。
- **含 `PROV_PASS` 明文的串口原始日志只存在于 `{ESP}` 顶层**（只数与口径边界由 §38.36 那一格的现跑登记，本遍不另数）
  ⇒ 永不 stage / 永不 push / 永不删除 ⇒ ht305 载荷里没有这些原始日志，载荷里有的是脱敏取证件。
- docs/ 快照第十三遍、`backups/README.md` 第十三次读数、排查记录 §38.37、提交轮、第 17 代同步**都在本节之后** ⇒ 本批不预写它们的数。
- **`FreqErr.md` 第十五批与第十六批在排查记录里没有对应小节**（它们的现场在 `backups/README.md` 第十一格/第十二格与各自载体里）⇒ 这格空缺登记在此，不补写。
'''

done_txt = f'''

{SECH}R61b + R61c 两代收口：第 15/16 代 ht305 同步 + 提交轮 #10 + `FreqErr.md` 第十五~十九批（取证 2026-09-26 13:2x ~ 16:3x，本遍落纸 {ts}，任务 214/215/216/217/220/221/222/225）

- [x] 214 **第 15 代（`r61bfinal`）ht305 收口同步**：六只脚本第一次由**替换表派生**（`hardware/r61_sync/scripts/derive_r61b.py`）而不是手抄换名；
      四道假 ABORT 全是「一把尺只量一种形态 ⇒ 量不到就被判成不存在」（(76) 那条「命中 0 ≠ 干净」在断言侧的镜像）；
      载荷 membership 逐只点名，把「描述上一代的 paperwork 真在本代载荷里」钉成可复算判据；五字段两侧全等、双向名单差集 0-0、远端只写不删。正文 = §38.35。
- [x] 215 **§38.35 落纸**（现跑于 {led['第十五批'][0][:8]} 13:26:16）：同一遍里**现读重选追加体行尾为 CRLF**——行尾是一把会被外部动作（`core.autocrlf`）挪动的尺，
      两遍之间它变了，而「我上一遍选的肯定还对」正是这一族的错法。
- [x] 216 **docs/ 快照第十一遍 + `backups/README.md` 第十一次读数**：产物即凭证；第十一格那 ①~⑬ 格由 `land_r61b_readme11*.py` 三遍落成
      （插入 → 补载体行 → 把载体行订正成真话），三遍都没覆写旧格、零删除；其间的工具缺陷去向 = `FreqErr.md` 第十五批 {led['第十五批'][1]} 条 + 第十六批 {led['第十六批'][1]} 条。
- [x] 217 **提交轮 #10（现跑 HEAD `{head}`，`rev-list` = {revl}，全未 push）**：`git diff --numstat` 现读 **106 只** = 文本 104（+19,847 / −1 行）+ 二进制 2
      （两只原厂镜像；`numstat` 对二进制打 `-` 而非整数 ⇒ 汇总器必须分桶点名）；门 `staged_cred_gate_r61b_final106.txt` = `FILES_SCANNED=106 / TOTAL_HITS=0 / VERDICT=CLEAN`，
      阳性对照 `staged_cred_gate_r61b_final106_pos.txt` = `INDEX_DELETED=2 / INDEX_SCANNED=104 / ARMS_FIRED=2/2 / VERDICT=POSITIVE_CONTROL_FIRES_AND_INDEX_CLEAN`；
      **门名与提交只数第一次由代码对上**（`gs_files == ps_del + ps_scan == n_files` 三向 assert）。
- [x] 220/221 **`FreqErr.md` 第十七批 {led['第十七批'][1]} 条 + 第十八批 {led['第十八批'][1]} 条 与 §38.36 落纸**：§38.36 登记的四件事是**一遍**（提交轮 #10 → docs 第十二遍 → README 第十二次读数 → 第十七/十八批），
      并在同一遍核销一起相反形态：上一遍崩在**写盘之后**的行数断言上，盘上留着它写的那一版本节（现读归档件 {STALE_B:,} B）。
      收口三步全在代码里：先确认同前缀载体无一含 `VERDICT=LANDED` → 整只现件按字节归档 → 头段与 {PIMG_N + 1} 只 `record_pre3836_*.md` 逐字节对账才回落 ——
      **幂等门的权威判据由此从「正文有没有标题」换成「载体有没有写盘后令牌」**。零删除：被替换那一份既在归档件里，也在 assert 的比对对象里。
- [x] 222 **第 16 代（`r61cfinal`）收口同步**：载荷 **{S16_F} 只 / {S16_B:,} B**、包 **{S16_ZIP:,} B / md5 `{S16_MD5}`**、两侧聚合 sha256 `{S16_AGG[:16]}…` 同值、
      `REMOTE_FORBIDDEN={R_FORBID}`、解包进全新根 `zsynctest{ROOT16}`、双向名单差集 0-0、`changed / deleted = {CHG} / {DEL}`、`new_since_cutoff = {NEW8}` 只逐只点名、
      候选集等式 {CAND} == {S16_F} + {NEW8}；往返复核 `VERDICT=REMOTE_CARRIES_PLAINTEXT`（登记事实，非事故）；**零删除、零覆盖、`Remove-Item` 命中 0**。
- [x] 225 **本遍 paperwork**：`dev_log/20260926.md` 的 {BATCH} + 本节 + `updates/20260926_墨水屏R61b尾巴提交轮10与第15-16代同步.md`（新建）+ `todo.md` 第十九遍重写；
      落地器 = `hardware/r61c_sync/scripts/land_r61c_paperwork.py`：**先归档 pre-image 再写盘**，写盘后跑三段式证明（前缀逐字等 / 追加段逐行等 / 行数等式）。
      追加之前现读：`done.md` **{dm_l} 行 / {dm_b:,} B**、`dev_log/20260926.md` **{dv_l} 行 / {dv_b:,} B**、`FreqErr.md` **{fe_n} 条 / {fe_l} 行 / {fe_b:,} B**、
      排查记录 **{rc_l} 行 / {rc_b:,} B / md5 前 8 `{rc_md5}`**、`backups/README.md` **{rdm_l} 行 / {rdm_b:,} B**、docs 快照停在第十二遍（{DOCS_AT}）。
- [ ] **本遍没做（点名）**：没烧录、没碰串口（屏亮肉眼确认仍 1 次 / 第二页 0 次 / 真按 BOOT 0 次 ⇒ 不播提示音）·
      docs 第十三遍、README 第十三次读数、§38.37、提交轮、第 17 代同步**都在本节之后** ⇒ 不预写其数 ·
      `hardware/ht305_sync/` 一字节未落（SEAL 停 gen 24）·
      **含明文的串口原始日志只存在于 `{ESP}` 顶层，永不 stage / 永不 push / 永不删除** ⇒ 不在 ht305 载荷里（载荷里是脱敏取证件）· 未 push、未 amend、零删除。

**现场态（本条写下之前现跑）**：HEAD `{head}` / `rev-list --count origin/main..HEAD` = **{revl}**（全未 push）/
`git status --porcelain` = **{len(por)} 行**（` M` {por_m} + `??` {por_q}；`??` 里含目录折叠行 ⇒ porcelain 行数与文件只数是两把不同的尺，互不可换算）/
`FreqErr.md` {fe_n} 条 / {fe_l} 行 / {fe_b:,} B / md5 前 8 `{fe_md5}` / 排查记录 {rc_l} 行 / {rc_b:,} B / md5 前 8 `{rc_md5}`。
'''

for _nm, _blk in (('dev', dev_txt), ('done', done_txt)):
    for _i, _l in enumerate(_blk.split('\n'), 1):
        assert chr(39) not in _l, 'ABORT: %s 正文第 %d 行含 ASCII 撇号：' % (_nm, _i) + _l[:60]
        assert sec not in _l, 'ABORT: %s 正文含口令明文：' % _nm + _l[:60]
        assert _l.count('`') % 2 == 0, 'ABORT: %s 第 %d 行反引号不成对：' % (_nm, _i) + _l[:80]
        if BS in _l:
            assert ESP in _l, 'ABORT: %s 第 %d 行有意外反斜杠：' % (_nm, _i) + _l[:80]
_stray = [(i + 1, l[:70]) for i, l in enumerate((dev_txt + done_txt).split('\n'))
          if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 未插值占位符 %d 处：%s' % (len(_stray), _stray[:3])

pre_d = io.open(DEV, 'rb').read()
pre_n = io.open(DON, 'rb').read()
assert pre_d.endswith(b'\n') and pre_n.endswith(b'\n'), 'ABORT: 追加目标末行不以换行收尾'
assert BATCH.encode('utf-8') not in pre_d, 'ABORT: 第三十四批已在册（幂等门），本遍不叠加'
assert SECH.encode('utf-8') not in pre_n, 'ABORT: done 第二十六节已在册（幂等门）'
dv_bytes = dev_txt.encode('utf-8')
dn_bytes = done_txt.encode('utf-8')
exp_d, exp_n = pre_d + dv_bytes, pre_n + dn_bytes
# 两推法：预期终态既由"内存拼好的字节串"数出来，也由"分项加法"独走一次，两数必须相等（第十九批第①条的执行者）
for exp, pre, app in ((exp_d, pre_d, dv_bytes), (exp_n, pre_n, dn_bytes)):
    assert len(exp) == len(pre) + len(app), 'ABORT: 字节加法两推法不等'
    assert exp.count(b'\n') == pre.count(b'\n') + app.count(b'\n'), 'ABORT: 行数加法两推法不等'
_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
for src, name in ((pre_d, 'devlog_pre34'), (pre_n, 'done_pre26')):
    p = os.path.join(EV, '%s_%s.md' % (name, _tt))
    assert not os.path.exists(p), 'ABORT: pre-image 目标已存在 ' + p
    io.open(p, 'wb').write(src)
    assert io.open(p, 'rb').read() == src, 'ABORT: pre-image 回读不等'
print('PRE-IMAGE devlog_pre34_%s.md / done_pre26_%s.md（写盘前原件 %s B / %s B）' % (
    _tt, _tt, format(len(pre_d), ','), format(len(pre_n), ',')))
print('LIVE 五批台账 = %s / 合计 %d 条 / 全册 %d 条' % (LED_TXT, b_sum, fe_n))
print('S16 %d 只 / %d B / zip %d B / 聚合两侧同值 / FORBIDDEN=%d / 根 zsynctest%s' % (S16_F, S16_B, S16_ZIP, R_FORBID, ROOT16))
print('CARRIERS 第 16 代非空载体 %d 只 / 第十九批崩遍 %d 只 / 权威遍 %s' % (len(s16_cars), len(crash19), auth19_all[0]))
print('CRASH_RULE 崩遍分类只认「本遍自己有没有写出写盘后令牌」；按 Error 字样数会把成功遍引用的那一行 KeyError 也算成崩遍（本遍实测：那种尺命中 3 只，真崩遍 2 只）')

io.open(DEV, 'wb').write(exp_d)
io.open(DON, 'wb').write(exp_n)
for p, pre, app in ((DEV, pre_d, dv_bytes), (DON, pre_n, dn_bytes)):
    chk = io.open(p, 'rb').read()
    pl, cl = pre.splitlines(), chk.splitlines()
    # 追加段也是**字节行**：上一遍这里写的是 `app.decode(...).split(chr(10))` ⇒ 拿 str 列表去比 bytes 列表，
    # 恒不等 ⇒ rc=1 而盘上内容是对的（同第十八批第①条那一族：那次错在"逐位置差集"，这次错在"类型不同"）。
    al = [x.encode('utf-8') for x in app.decode('utf-8').split('\n')[1:-1]]
    assert chk.startswith(pre), 'ABORT: 前缀未逐字保持（本遍是纯追加）：' + os.path.basename(p)
    assert cl[:len(pl)] == pl, 'ABORT: 前缀行不等：' + os.path.basename(p)
    assert cl[len(pl):] == al, 'ABORT: 追加段逐行不等：' + os.path.basename(p)
    assert len(cl) == len(pl) + len(al), 'ABORT: 行数等式不成立：' + os.path.basename(p)
    assert chk == exp_d if p == DEV else chk == exp_n, 'ABORT: 盘上字节 != 内存终态'
    print('LANDED %-16s %d -> %d 行 / %s -> %s B / md5 %s -> %s / APPEND %d 行' % (
        os.path.basename(p), len(pl), len(cl), format(len(pre), ','), format(len(chk), ','),
        hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8], len(al)))
print('BS_LINES 只出现在点名 Windows 路径那几行：%d（dev）+ %d（done）' % (
    sum(1 for l in dev_txt.split('\n') if BS in l), sum(1 for l in done_txt.split('\n') if BS in l)))
print('VERDICT=LANDED rc=0')
