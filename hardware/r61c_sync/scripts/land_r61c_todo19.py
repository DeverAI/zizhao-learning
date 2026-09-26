# todo.md 第十九遍重写落地器（R61c 收口尾巴）。
# 三步序照排查记录在册口径：①幂等门看写盘后令牌 ②全部裁决排在写盘之前 ③写盘后独立回读证明。
# 本只是**重写**（不是纯追加），所以证明段做的是"快照 == 旧字节 + 新件 == 预期字节 + 行尾两把尺同值"，
# 旧原件先复制到仓库外 C:\esp\（用户红线：不覆写、不删除，重写前必留副本）。
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
TOD = os.path.join(REPO, 'todo.md')
DON = os.path.join(REPO, 'done.md')
FE = os.path.join(REPO, 'FreqErr.md')
REC = os.path.join(REPO, 'hardware', '20260919_墨水屏点屏排查记录.md')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
BIN = r'C:/esp/zproj/build/zizhao_esp32s3.bin'
ESP = r'C:\esp'
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
BS = chr(92)
MARK = '第十九遍'
_T0 = datetime.datetime.now()


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), cwd=REPO, capture_output=True)
    assert r.returncode == 0, 'ABORT git %s: %s' % (a, r.stderr.decode('utf-8', 'replace')[:200])
    return r.stdout.decode('utf-8', 'replace').strip()


def rb(p):
    return io.open(p, 'rb').read()


# ---------- 现跑读数 ----------
pre = rb(TOD)
assert pre.endswith(b'\r\n'), 'ABORT: 现件末行不以 CRLF 收尾'
old_lines = pre.count(b'\n')
old_cr = pre.count(b'\r')
old_b = len(pre)
assert old_cr == old_lines, 'ABORT: 现件行尾混排（CR %d != LF %d）⇒ 本遍的 CRLF 前提不成立' % (old_cr, old_lines)

rev = git('rev-list', '--count', 'origin/main..HEAD')
head = git('rev-parse', '--short', 'HEAD')
por = [l for l in git('status', '--porcelain').split('\n') if l]
pm = sum(1 for l in por if l[:2] == ' M')
pq = sum(1 for l in por if l[:2] == '??')
fe_b, fe_l = len(rb(FE)), rb(FE).count(b'\n')
fe_n = sum(1 for l in rb(FE).decode('utf-8').split('\n') if l.startswith('[错误类型]'))
rc_b, rc_l = len(rb(REC)), rb(REC).count(b'\n')
dn_b, dn_l = len(rb(DON)), rb(DON).count(b'\n')
bin_b = os.path.getsize(BIN)
bin_md5 = hashlib.md5(rb(BIN)).hexdigest()
# 明文半径：口令只从宏现读，全程不打印、不进命令文本
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', rb(SRC).decode('utf-8')).group(1).encode('utf-8')
tops = [f for f in os.listdir(ESP) if os.path.isfile(os.path.join(ESP, f))]
hits = [f for f in tops if sec in rb(os.path.join(ESP, f))]
assert hits, 'ABORT: C:\\esp\\ 顶层一只都没命中 ⇒ 明文尺的扫描对象不对，读数无意义'
_tt = _T0.strftime('%Y%m%d_%H%M%S')
SNAP = os.path.join(ESP, 'todo_r61c_before_%s.md' % _tt)
assert not os.path.exists(SNAP), 'ABORT: 重写前快照目标已存在 ' + SNAP

# ---------- 新正文（每个数字都由插值来自上面的现跑值） ----------
body = '''# todo.md · 墨水屏线（R19~**R61**）第{mark}：R61b/R61c 两代收口只剩尾巴，硬骨头全在「要么等物理动作、要么等用户裁决」

> **一句话现状**：在机板定案为 **Waveshare S3_ePaper_1_54**（200×200、屏电 GPIO6 低有效、整板无 AXP2101），
> 屏**已亮过并被肉眼确认**（2026-09-25 18:5x），配网页/时钟页/状态页/消息分页**都在真机跑过**；
> 待烧 == 板上 == `C:/esp/zproj/build/zizhao_esp32s3.bin`（**{bin_b} B / md5 `{bin_md5}`**，本遍现读，本遍没重建、没烧录）。
> 引脚/版面/未确立项的单一档案 = `hardware/BOARD_S3_ePaper_1_54.md`。
>
> 【口径变更，R59 起】本文件顶部此前那三行"引脚/控制器依据：官方包 `ESP32-S3_e-Paper-3.97`…**已作废**——那套前提的对象是 3.97，
> 不是在机这块板。作废过程见排查记录 §38.29~§38.30 与 `烧录须知.md` 第 3 行那条订正。
> 重写前的旧文本副本（都在仓库外、不入库、不删）：{old_prev_lines} 行原件 = `C:{bs}esp{bs}todo_r61_before_20260926.md`（R61 第十八遍前），
> 本遍 {old_lines} 行原件 = `C:{bs}esp{bs}todo_r61c_before_{tt}.md`。

## 还没做的（每条都点名，按「谁能做」分组）

### A. 只有用户能做/需要用户裁决的
- [ ] **A1 真按一次 BOOT 键，肉眼看到第二页**（任务 210 剩的那半条）。目前"能翻页"的强度：算式与渲染已被真机读数逐字证同
      （`hardware/r61_evidence_diag_full_20260926_110814.txt`），页面环已被注入式走通一圈并闭合（`RING_CLOSED`，5 格），
      但**驱动环的是 `buttons_inject`，它跳过 `pressed()`/`debounce()`** ⇒ 实物键那条腿只有代码依据。
      要看的三件事：第二页内容对不对、右下角页码在不在位、行间是否重叠。
- [ ] **A2 产品级陷阱改不改**：1800 s 配网闸门 + 900 s/6 h 深睡（深睡会把原生 USB 从总线摘掉，COM14 就"消失"）。
      这条已反复点名七轮，属产品裁决，不是缺陷未定位。
- [ ] **A3 屏的确切料号 / 第二块同型号板对读**：判"固件 vs 板损"最便宜的手段仍是同 bin 烧第二块板比 `pull compare`。

### B. 软件侧真缺陷（未定位/未实装）
- [ ] **B1 SD 挂载仍卡 `send_op_cond 0x107`**（本板 CLK39/CMD41/D0=40 从未挂上，离线文本只在 NVS/RAM）。
- [ ] **B2 局刷从未开过**：`ENABLE_EINK_PARTIAL 0`，代码在镜像里但 0 个调用者 ⇒ 每次翻页都是全刷（实测一次约 1.8~2.2 s 量级）。
- [ ] **B3 学习内容那一页从未显示过**：`offline_store_load_text` 显示侧 0 个调用者。
- [ ] **B4 GPIO6 的"屏电"归属只到原厂代码口径**：v6 那遍对照臂自己没兑现判据（`armB_on_tr=1 armC_off_tr=1`，
      三条件里两条不成立）⇒ 没能钉死；见 `BOARD_S3_ePaper_1_54.md` 末节。
- [ ] **B5 `PWR_BUTTON=18` 在本板走什么电路从未实测**（`buttons.c:12-17` 因此故意不配它）。

### C. 收尾动作（本遍之内要做完的，写在下面以便核对）
- [ ] **C1 排查记录 §38.37**：登记第 16 代同步 + 第十九批 + 本遍 paperwork + 两起工具层改判
      （崩遍分类被成功遍的引用污染、写盘后证明拿 str 行表比 bytes 行表）。
- [ ] **C2 docs/ 快照第十三遍 + backups README 第十三次读数**（任务 223 / 224）：由 `refresh_docs_snapshot_r61b.py` 派生，
      把本遍新建的 updates 件并入 SRCS、抬只数下限、NOTE 只数继续插值。
- [ ] **C3 提交轮 #11**（任务走 #217 同族）：明文门 + 阳性对照 + 逐只点名 stage → 提交，**不 push、不 amend**，提交信息里不许有将来式锚点。
- [ ] **C4 ht305 第 17 代全量同步**（用户指令：「把所有整理好的证据、代码等上传同步HT305服务器桌面」）：
      载荷必须含 §38.37 与本遍 paperwork，远端解包根用新的 `zsynctest19`，服务器侧零删除。
      **要在汇报里点名**：描述第 16 代的那一节（§38.37）不在第 16 代载荷里，它随第 17 代入库。
- [ ] **C5 项目记忆 (105)+ 与用户记忆「工具自伤」类目补齐**（任务 218 / 177）。
- [ ] **C6 空上下文故障检测子AGENT复查本遍全部落地**（强制最后一步，任务 219）。

## 台账（本遍现场态；下面这些数字取在**本文件重写之前**，重写之后 stdout 另打一把）
`git rev-list --count origin/main..HEAD` = **{rev}**（快照，权威源是现跑而不是这一行）· HEAD `{head}` ·
`git -c core.quotePath=false status --porcelain` = **{por} 行**（` M` {por_m} + `??` {por_q}；`??` 含目录折叠行 ⇒ 与文件只数互不可换算）·
排查记录 **{rc_l:,} 行 / {rc_b:,} B** · `FreqErr.md` **{fe_n} 条 / {fe_l:,} 行 / {fe_b:,} B** ·
`done.md` **{dn_l:,} 行 / {dn_b:,} B** · 本文件重写前 **{old_lines} 行 / {old_b:,} B**（CRLF {old_cr} == LF {old_lines}）·
屏亮肉眼确认累计 **1 次**（R59）· 看到第二页 **0 次** · 真按 BOOT **0 次** ⇒ **不播提示音** ·
含 `PROV_PASS` 明文的**原始**串口日志 **{plain} 只**只在 `C:{bs}esp{bs}` 顶层（现扫 {tops} 只文件），永不 stage / 永不 push / 永不删除
⇒ 串口原始日志不在 ht305 载荷里，载荷里有的是脱敏取证件 · **不 push**。
'''.format(mark=MARK, bin_b=format(bin_b, ','), bin_md5=bin_md5, old_prev_lines=273, tt=_tt,
           bs=BS, old_lines=old_lines, old_b=old_b, old_cr=old_cr, rev=rev, head=head, por=len(por),
           por_m=pm, por_q=pq, rc_l=rc_l, rc_b=rc_b, fe_n=fe_n, fe_l=fe_l, fe_b=fe_b, dn_l=dn_l, dn_b=dn_b,
           plain=len(hits), tops=len(tops))

# ---------- 内容闸（写盘之前） ----------
for i, l in enumerate(body.split('\n'), 1):
    assert chr(39) not in l, 'ABORT: 第 %d 行含 ASCII 撇号：' % i + l[:60]
    assert sec.decode('utf-8') not in l, 'ABORT: 第 %d 行含口令明文：' % i + l[:60]
    assert l.count('`') % 2 == 0, 'ABORT: 第 %d 行反引号不成对：' % i + l[:80]
    if BS in l:
        assert ('C:' + BS + 'esp' + BS) in l, 'ABORT: 第 %d 行有意外反斜杠：' % i + l[:80]
_stray = [(i + 1, l[:70]) for i, l in enumerate(body.split('\n'))
          if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 未插值占位符 %d 处：%s' % (len(_stray), _stray[:3])
assert MARK in body.split('\n')[0], 'ABORT: 首行没有本遍序数'
assert body.count('`C:' + BS + 'esp' + BS) >= 3, 'ABORT: C:\\esp\\ 指针少于三处（快照副本没被点名）'
# 273 行那只前一份副本的只数不许写字面量：现读那只文件
assert os.path.isfile(os.path.join(ESP, 'todo_r61_before_20260926.md')), 'ABORT: 第十八遍前那份快照不在盘上'
_prev_lines = rb(os.path.join(ESP, 'todo_r61_before_20260926.md')).count(b'\n')
assert ('%d 行原件' % _prev_lines) in body, 'ABORT: 正文里那份旧快照的只数 != 现读（现读 %d）' % _prev_lines

new = body.replace('\n', '\r\n').encode('utf-8')
exp_cr = new.count(b'\r')
exp_lf = new.count(b'\n')
assert exp_cr == exp_lf == body.count('\n'), 'ABORT: CRLF 转换后两把尺不同值（CR %d / LF %d / 应有 %d）' % (
    exp_cr, exp_lf, body.count('\n'))

# ---------- 幂等门：同前缀载体里有没有写盘后令牌 ----------
_prior = glob.glob(os.path.join(EV, 'r61c_todo19_*.txt'))
_landed = [p for p in _prior if 'VERDICT=LANDED' in rb(p).decode('utf-8', 'replace')]
assert not _landed, 'ABORT: 第十九遍已落过盘（载体含写盘后令牌）：%s' % _landed
assert MARK.encode('utf-8') not in pre, 'ABORT: 现件首行已含第十九遍 ⇒ 本遍的 pre-image 读数已被自己污染'

# ---------- 写盘 ----------
io.open(SNAP, 'wb').write(pre)
assert rb(SNAP) == pre, 'ABORT: 快照回读不等'
io.open(TOD, 'wb').write(new)
chk = rb(TOD)
assert chk == new, 'ABORT: 盘上字节 != 预期终态'
assert chk != pre and len(chk) > 0, 'ABORT: 新件与旧件同字节（本遍是重写，不许无变化）'
assert rb(SNAP) == pre, 'ABORT: 重写后旧原件与快照不再逐字等（零丢失未成立）'
post = [l for l in git('status', '--porcelain').split('\n') if l]
print('PRE-IMAGE C:%sesp%stodo_r61c_before_%s.md（旧原件 %s B / %d 行 / CRLF %d == LF %d，仓库外，不入库不删）' % (
    BS, BS, _tt, format(old_b, ','), old_lines, old_cr, old_lines))
print('LIVE rev-list %s / HEAD %s / porcelain %d 行（` M` %d + `??` %d）· FreqErr %d 条 %d 行 %s B · 记录 %d 行 %s B · done %d 行 %s B' % (
    rev, head, len(por), pm, pq, fe_n, fe_l, format(fe_b, ','), rc_l, format(rc_b, ','), dn_l, format(dn_b, ',')))
print('PLAINTEXT 现扫 C:\\esp\\ 顶层 %d 只文件 ⇒ 含明文 %d 只（口令只从宏现读，未打印）' % (len(tops), len(hits)))
print('LANDED todo.md %d 行 / %s B / md5 %s -> %s / CR %d == LF %d' % (
    chk.count(b'\n'), format(len(chk), ','), hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8],
    chk.count(b'\r'), chk.count(b'\n')))
print('POST-WRITE porcelain %d 行（` M` %d + `??` %d）⇒ 本遍自己让 ` M` 从 %d 变 %d（todo.md 由净转变）' % (
    len(post), sum(1 for l in post if l[:2] == ' M'), sum(1 for l in post if l[:2] == '??'), pm,
    sum(1 for l in post if l[:2] == ' M')))

_car = os.path.join(EV, 'r61c_todo19_%s.txt' % _tt)
assert not os.path.exists(_car), 'ABORT: 载体目标已存在 ' + _car
io.open(_car, 'wb', newline='').write((
    'todo.md 第十九遍重写，现跑于 %s\n' % _T0.strftime('%Y-%m-%d %H:%M:%S') +
    'PRE-IMAGE C:%sesp%stodo_r61c_before_%s.md（%s B / %d 行 / CRLF %d == LF %d）\n' % (
        BS, BS, _tt, format(old_b, ','), old_lines, old_cr, old_lines) +
    'LIVE rev-list %s / HEAD %s · FreqErr %d 条 / %d 行 / %s B · 记录 %d 行 / %s B · done %d 行 / %s B · bin %s B / md5 %s\n' % (
        rev, head, fe_n, fe_l, format(fe_b, ','), rc_l, format(rc_b, ','), dn_l, format(dn_b, ','),
        format(bin_b, ','), bin_md5) +
    'PORCELAIN 写盘前 %d 行（` M` %d + `??` %d）/ 写盘后 %d 行（` M` %d + `??` %d）⇒ 增量 = todo.md 自己\n' % (
        len(por), pm, pq, len(post), sum(1 for l in post if l[:2] == ' M'), sum(1 for l in post if l[:2] == '??')) +
    'PLAINTEXT 顶层 %d 只文件 / 含明文 %d 只（扫描对象 = C:%sesp 顶层文件，不含子目录）\n' % (len(tops), len(hits), BS) +
    'PROOF 新件逐字节 == 预期字节串 / CRLF 两把尺同值 / 快照 == 旧原件（零丢失）/ 内容闸四道全过\n'
    'VERDICT=LANDED rc=0\n').encode('utf-8'))
assert rb(_car).endswith('VERDICT=LANDED rc=0'.encode('utf-8')) and rb(_car) == io.open(_car, 'rb').read(), 'ABORT: 载体回读不等'
print('CARRIER %s（%d B）' % (os.path.basename(_car), len(rb(_car))))
print('VERDICT=LANDED rc=0')
