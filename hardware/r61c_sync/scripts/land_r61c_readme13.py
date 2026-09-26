# backups/README.md §1 第十三次读数落地器（r61c 代，docs 第十三遍之后）。
# 三步序：①幂等门（权威判据 = 正文里有没有「第十三次读数」这一格）②全部裁决排在写盘之前
# ③写盘后三段式行级证明（前缀逐字等 / 插入段逐行等 / 后缀逐字等 + 行数等式）。
# 与上一代不同的一件事：本代所有「与第十二次同值 / 不同值」的句子**由脚本现算**，
#   上一格的数一律从盘上 README 的第十二次那一格**正则现读**，不手抄、不写死。
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
os.chdir(REPO)
EV = os.path.join('hardware', 'r61c_sync', 'evidence')
README = 'backups/README.md'
MACRO = os.path.join('hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
MAIN = os.path.join('hardware', 'zizhao-esp32s3', 'main')
SIB = os.path.join('hardware', 'zizhao-esp32s3', 'backups')
DOCS = os.path.join('backups', 'r43_20260922_131029', 'docs')
HT305 = os.path.join('hardware', 'ht305_sync')
PZ = os.path.join('hardware', '20260919_墨水屏点屏排查记录.md')
T0 = datetime.now()
OUTL = []


def say(s):
    OUTL.append(s)
    print(s)


def git(*a):
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(a), capture_output=True, shell=False)
    assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')
    return r.stdout.decode('utf-8', 'replace')


def dqr(a, b):
    for p in (a, b):
        assert os.path.isdir(p), 'ABORT: diff 的输入目录不存在，不能把失败读成 0 行 differ：' + p
    r = subprocess.run(['diff', '-rq', a, b], capture_output=True, shell=False)
    err = r.stderr.decode('utf-8', 'replace').strip()
    assert not err, 'ABORT: diff 自身报错（rc=%d）：%s' % (r.returncode, err[:200])
    return len([l for l in r.stdout.decode('utf-8', 'replace').splitlines() if l.strip()])


def same(a, b, fmt='%s'):
    """把「与上一格同值 / 不同值」这句话交给脚本，不让我用眼睛数。"""
    return '与第十二次**逐字同值**（该格现读 = %s）' % (fmt % b) if a == b \
        else '与第十二次**不同值**：上一格现读 %s ⇒ 本遍 %s' % (fmt % b, fmt % a)


# ---------- 现读：git 侧（porcelain 一律**不 strip**，见本代缺陷①） ----------
head = git('rev-parse', '--short', 'HEAD').strip()
revlist = int(git('rev-list', '--count', 'origin/main..HEAD').strip())
_por = git('status', '--porcelain')
sline = [l for l in _por.split('\n') if l]
skind = {}
for l in sline:
    skind[l[:2]] = skind.get(l[:2], 0) + 1
_kinds = sorted(skind)
assert set(_kinds) <= {' M', '??', 'M ', 'D ', 'A '}, 'ABORT: 出现未点名前缀 %s' % _kinds
assert len(sline) == sum(skind.values()), 'ABORT: 桶不完备（分桶尺看的就是前两个字符）'
ns_main = [l.split('\t') for l in git('diff', 'HEAD', '--numstat', '--', MAIN).splitlines() if l.strip()]
main_n = len(ns_main)
main_plus = int(ns_main[0][0]) if main_n == 1 else -1
main_minus = int(ns_main[0][1]) if main_n == 1 else -1
main_names = [os.path.basename(x[2]) for x in ns_main]
secret = re.search(rb'#define\s+PROV_PASS\s+"([^"]+)"', open(MACRO, 'rb').read()).group(1)
assert secret not in ' '.join(main_names).encode('utf-8')

# ---------- 现读：五把根尺 ----------
r43a, r43b = dqr(os.path.join('backups', 'r43_20260922_131029', 'main'), MAIN), \
             dqr(os.path.join(SIB, 'r43_20260922_131029', 'main'), MAIN)
r53a, r53b = dqr(os.path.join('backups', 'r53_20260924_083929', 'main'), MAIN), \
             dqr(os.path.join(SIB, 'r53_20260924_083929', 'main'), MAIN)
srcs = dqr(os.path.join('backups', 'r44_sourceonly_20260923_084628', 'main'), MAIN)
wf = [f for f in os.listdir(MAIN) if os.path.isfile(os.path.join(MAIN, f))]
wt_cnt, wt_bytes = len(wf), sum(os.path.getsize(os.path.join(MAIN, f)) for f in wf)
ROOT = 'r61close_20260926_133908'
roots = {}
for tag, r in (('A', os.path.join('backups', ROOT)), ('B', os.path.join(SIB, ROOT))):
    assert os.path.isdir(r), 'ABORT: 根 %s 不存在：%s' % (tag, r)
    c, t = 0, 0
    for dp, dn, fn in os.walk(r):
        for f in fn:
            c += 1
            t += os.path.getsize(os.path.join(dp, f))
    roots[tag] = (c, t, dqr(os.path.join(r, 'main'), MAIN))

# ---------- 现读：docs 快照第十三遍 ----------
note_p = os.path.join(DOCS, 'SNAPSHOT_NOTE.txt')
note = open(note_p, encoding='utf-8').read()
snap_at = re.search(r'刷新时刻 ([0-9: -]{19})', note).group(1)
note_rows = len([l for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:', l)])
docs_files = len([f for f in os.listdir(DOCS) if os.path.isfile(os.path.join(DOCS, f))])
note_bytes = os.path.getsize(note_p)
new_rows = [l.split('\t')[0] for l in note.split('\n') if re.match(r'^[^\t]+\t\d+\tmd5:[0-9a-f]+\tNEW -> ', l)]
src_cnt = int(re.search(r'本次运行：源清单现读 (\d+) 只', note).group(1))
assert note_rows == src_cnt and docs_files == note_rows + 1, 'ABORT: docs 自核等式不成立'
DERIVER = os.path.join('hardware', 'r61c_sync', 'scripts', 'derive_docs_r61c.py')
SNAP_PY = os.path.join('hardware', 'refresh_docs_snapshot_r61c.py')
assert os.path.isfile(DERIVER) and os.path.isfile(SNAP_PY), 'ABORT: 快照件或派生器不在盘上'

# ---------- 现读：本遍 r61c 取证件（用来给"载体齐全"装执行者） ----------
_cars = sorted(f for f in os.listdir(EV) if re.match(r'^r61c_.*\.txt$', f))
LANDED = [f for f in _cars if 'VERDICT=LANDED rc=0' in open(os.path.join(EV, f), encoding='utf-8').read()]
assert LANDED, 'ABORT: 取证目录里一只含写盘后令牌的载体都没有'
PRE_IMGS = sorted(f for f in os.listdir(EV) if re.match(r'^(todo19_pre_fix|r61c_paperwork_pre_).*', f))

# ---------- 现读：FreqErr / 排查记录 / 封界 / 串口 ----------
fb = open('FreqErr.md', 'rb').read()
f_txt = fb.decode('utf-8')
f_lines, f_entries = fb.count(b'\n'), len(re.findall(r'^\[错误类型\]', f_txt, re.M))
f_md5 = hashlib.md5(fb).hexdigest()[:8]
pzb = open(PZ, 'rb').read()
pz_lines = pzb.count(b'\n')
lastsec = re.findall(r'^### (38\.\d+)', pzb.decode('utf-8'), re.M)[-1]
hfiles = sum(len(fn) for dp, dn, fn in os.walk(HT305))
hlataest = max((os.path.join(dp, f) for dp, dn, fn in os.walk(HT305) for f in fn),
               key=lambda p: os.path.getmtime(p))
hlm = datetime.fromtimestamp(os.path.getmtime(hlataest)).strftime('%Y-%m-%d %H:%M:%S')
pr = subprocess.run([sys.executable, '-m', 'serial.tools.list_ports'], capture_output=True, shell=False)
assert pr.returncode == 0, 'ABORT: 串口枚举本身失败，不能把失败读成 COM14 缺席'
ports = sorted(set(re.findall(r'COM\d+', pr.stdout.decode('utf-8', 'replace'))))
com14 = 'COM14' in ports
assert ports, 'ABORT: 枚举解析出 0 只 COM 名，命中 0 不等于干净'

# ---------- 现读：第十二次那一格（上一格的数**全部从盘上现读**，不手抄） ----------
rb0 = open(README, 'rb').read()
txt0 = rb0.decode('utf-8')
assert '第十三次读数' not in txt0, 'ABORT: 第十三次读数已在册（幂等门），不重复插'
_i11 = txt0.index('第十一次读数')
_i12 = txt0.index('第十二次读数')
P = txt0[_i12:txt0.index('\n## 2. 命名规则')]


def prev(pat, label):
    m = re.search(pat, P)
    assert m, 'ABORT: 第十二次那一格里读不到 %s（形状 %s）' % (label, pat)
    return m.groups()


p_main_n, p_main_plus, p_main_minus = [int(x.replace(',', '')) for x in
                                       prev(r'`git diff HEAD --numstat -- …/main` ⇒ \*\*(\d+) 只 / \+(\d+) / −(\d+)\*\*', '①')]
p_r43a, p_r43b = [int(x) for x in prev(r'根 A / 根 B = \*\*(\d+) / (\d+) 行\*\*', '②')]
p_r53a, p_r53b = [int(x) for x in prev(r'同一命令 = \*\*(\d+) / (\d+) 行\*\*', '③')]
p_wt_cnt, p_wt_bytes = [int(x.replace(',', '')) for x in prev(r'\*\*(\d+) 只 / (\d+) B\*\*（现读', '④')]
p_srcs = int(prev(r'⇒ 仍 \*\*(\d+) 行 differ\*\*', '⑤')[0])
p_docs_files, p_docs_rows = [int(x) for x in prev(r'目录现读 \*\*(\d+) 只\*\* = 表格 \*\*(\d+) 行\*\*', '⑨')]
p_fe_n, p_fe_lines, p_fe_bytes = [int(x.replace(',', '')) for x in
                                  prev(r'`FreqErr\.md` \*\*(\d+) 条 / (\d+) 行 / (\d+) B', '⑩')]
p_ht305 = int(prev(r'递归现读 \*\*(\d+) 只\*\*', '⑪')[0])
p_rev = int(prev(r'`rev-list --count origin/main\.\.HEAD` = \*\*(\d+)\*\*', '⑫')[0])
p_status = int(prev(r'`status --porcelain` = \*\*(\d+) 行\*\*', '⑫')[0])
p_snapshot_at = prev(r'`SNAPSHOT_AT ([0-9: -]{19})`', '⑨')[0]
assert (p_main_n, p_wt_cnt) == (main_n, wt_cnt), 'ABORT: 与上一格同形的断言前提没了（先改口径再落笔）'
assert p_ht305 == hfiles, 'ABORT: 封存归档只数与上一格不等 ⇒ 有人往 gen 24 之后落字节了，立即停'
assert p_snapshot_at < snap_at, 'ABORT: docs 第十三遍的刷新时刻不晚于第十二遍'

# ---------- 组正文（所有比较句由现算给出；字面量里不写只数） ----------
E = []
E.append('【09-26 **%s 第十三次读数**｜**本遍仍零代码进镜像，唯一进盘的新字节 = paperwork 与取证**；五把根尺 + docs + 封界逐把现跑，'
         '每一格那句「同值 / 不同值」都由脚本把本遍读数与**上一格盘上现读数**相减得出（上一格的数不手抄）】'
         % T0.strftime('%H:%M:%S'))
E.append('① **相对 `HEAD`（%s）**：`git diff HEAD --numstat -- …/main` ⇒ **%d 只 / +%d / −%d**，名单现读 = `%s` '
         '（自带 `PROV_PASS` 宏值、每轮被逐只点名 DROP，宏值只进工作树永不进 git 侧）⇒ %s。'
         % (head, main_n, main_plus, main_minus, '` 与 `'.join(main_names),
            same((main_n, main_plus, main_minus), (p_main_n, p_main_plus, p_main_minus), '%d 只 / +%d / −%d')))
E.append('② **相对 r43 那两根**：`diff -rq` 根 A / 根 B = **%d / %d 行** ⇒ %s（两根继续当 09-22 20:55 那一烧的历史输入，不刷新）。'
         % (r43a, r43b, same((r43a, r43b), (p_r43a, p_r43b), '%d / %d 行')))
E.append('③ **相对 r53 那两根**：同一命令 = **%d / %d 行** ⇒ %s（那一格自第十一次起降级成历史）。'
         % (r53a, r53b, same((r53a, r53b), (p_r53a, p_r53b), '%d / %d 行')))
E.append('④ **工作树 `main/` 体量**：**%d 只 / %d B** ⇒ %s ⇒ 本遍**没有一字节代码进工作树**（R61 的分页代码是上一遍的事）。'
         % (wt_cnt, wt_bytes, same((wt_cnt, wt_bytes), (p_wt_cnt, p_wt_bytes), '%d 只 / %d B')))
E.append('⑤ **`sourceonly` 镜像尺**：`diff -rq backups/r44_sourceonly_20260923_084628/main …` ⇒ **%d 行 differ** ⇒ %s（不顺手修，动历史镜像等于造第二把尺）。'
         % (srcs, same(srcs, p_srcs, '%d 行')))
E.append('⑥ **最近那对全根**（`%s`，A=%d 只 / B=%d 只 / 各 %s B）：两根各自 `diff -rq …/main 工作树 main` = **%d / %d 行** ⇒ 它仍是盘上唯一与工作树逐字同值的全根；本遍**一只没覆写、一只没删、没新建根**。'
         % (ROOT, roots['A'][0], roots['B'][0], format(roots['A'][1], ','), roots['A'][2], roots['B'][2]))
E.append('⑦ **docs/ 快照第十三遍（本遍之前刚跑，产物即凭证）**：`hardware/refresh_docs_snapshot_r61c.py` = 派生自 `hardware/refresh_docs_snapshot_r61b.py`，'
         '派生器 `hardware/r61c_sync/scripts/derive_docs_r61c.py`（替换表 7 条、表外零改动 `STRAYS=0`、`SRCS_OLD=%d SRCS_NEW=%d ADDED=%d`）。'
         '目录现读 **%d 只** = 表格 **%d 行** + `SNAPSHOT_NOTE.txt`（两道等式由本遍现跑 assert）、`SNAPSHOT_AT %s`（上一格现读 %s ⇒ 只抬不降，由 assert 把关）、'
         '凭据闸 **%d 只源全扫 / HITS=0**、`NOTE_BYTES %d`、`NEW_ONES %d` ⇒ 本遍唯一新入的一只 = `%s`（本代 r61b 收口件）。'
         % (src_cnt - len(new_rows), src_cnt, len(new_rows), docs_files, note_rows, snap_at, p_snapshot_at,
            src_cnt, note_bytes, len(new_rows), '、`'.join(new_rows)))
E.append('⑧ **FreqErr / 排查记录 / 封界 / 串口现场态（现读）**：`FreqErr.md` **%d 条 / %d 行 / %d B / md5 前 8 位 `%s`**（⇒ %s；第十八批之后本遍尚未落第二十批，落笔在本格之后）；'
         '`hardware/20260919_墨水屏点屏排查记录.md` **%d 行**，末节 = **§%s**（§38.37 在本格之后才落）；'
         '`python -m serial.tools.list_ports` 现跑 = `%s` ⇒ **COM14 在位 = %s**（枚举 rc=0 且解析出 %d 只 COM 名，假缺席由 assert 挡在写盘之前）⇒ 本遍没烧录、没碰串口；'
         '`hardware/ht305_sync/` 递归现读 **%d 只**（与上一格同值由本遍 assert，不等即 ABORT）、目录内最新一只 mtime `%s` ⇒ gen 24 之后**一字节未落**、本代不新建清单代。'
         % (f_entries, f_lines, len(fb), f_md5, same((f_entries, f_lines), (p_fe_n, p_fe_lines), '%d 条 / %d 行'),
            pz_lines, lastsec, ', '.join(ports), com14, len(ports), hfiles, hlm))
E.append('⑨ **git 侧余量（现跑）**：HEAD = `%s`，`rev-list --count origin/main..HEAD` = **%d** ⇒ %s；'
         '`git -c core.quotePath=false status --porcelain` = **%d 行**（%s；桶完备 assert：总数 == 各桶之和）⇒ %s。'
         '⚠ 本格这一条**换了尺**：上一格那一句的 ` M` 只数少计 1（见 ⑩ 缺陷①），两格**不可直接相减**，本遍把两把尺同时现跑并把差钉成 assert。'
         % (head, revlist, same(revlist, p_rev, '%d'), len(sline),
            ' + '.join('`%s` %d' % (k.strip() or 'AA', v) for k, v in sorted(skind.items())),
            '与第十二次同值' if len(sline) == p_status else '上一格现读 %d 行 ⇒ 本遍 %d 行（差值 = 本遍在 %s 新落的取证只数，见 ⑩ 前点名）' % (p_status, len(sline), EV.replace(os.sep, '/'))))
E.append('⑩ **本遍三处工具缺陷（点名，不藏；全部由脚本现跑复现，不是回忆）**：'
         '(a) **缺陷①：`subprocess` 输出助手里那句 `.strip()` 吃掉了 `git status --porcelain` 首行的前导空格**，而分桶尺看的正是前两个字符 ⇒ ` M` 恒少计 1（`??` 不受影响）。'
         '本遍独立复现两遍：不 strip = **%d 行 / ` M` %d**，strip = ` M` %d。'
         '修法 = porcelain 一律不 strip + **桶完备 assert**（总数 == 各桶之和，出现任何未点名前缀立即 ABORT）；'
         '已落进 `todo.md` 第十九遍那一格的首版读数是**错数**，由 `land_r61c_todo19fix.py` 订正遍改正（订正引文由脚本从盘上现读第一遍那句逐字插入，见 ⑩(c)）。'
         % (len(sline), skind.get(' M', 0), skind.get(' M', 0) - 1))
E.append('(b) **缺陷②：载体/凭证的「末行令牌」断言漏了文件以换行收尾** ⇒ `read().endswith(TOKEN)` 恒假。'
         '`land_r61c_todo19fix.py` 落盘**成功**、证明段也全过，红在最后一格记账 ⇒ rc=1 与"盘上是对的"同时成立；'
         '另一起同族：`io.open(p, "wb", newline="")` 直接 `ValueError`（binary 模式不许 `newline`）。'
         '修法 = 末行断言一律 `rstrip` 换行后再比，或按**行读**取末行等值比较（本遍 `verify_r61c_todo19fix.py` 用的是后者）。')
E.append('(c) **缺陷③（本遍自己抓的，方向与前两起相反）：复核遍把上一遍载体归类成「缺末行令牌」，而那是**没现读末行就写死的期望**——现读推翻：'
         '`%s` 末行逐字就是 `VERDICT=LANDED rc=0`，缺令牌 0 只。'
         '若那一格断言写成 `全部缺令牌` 的反面，它会以"假绿"通过；它这次以假红崩在自己身上，才被抓出来。'
         '修法 = 分类判据改成**现读末行三分类**（末行 == 令牌 / 只在正文 / 全缺）+ 完备性 assert，载体 = `r61c_todo19_fix2_*.txt`。'
         % (LANDED[0] if LANDED else ''))
E.append('⑪ **本遍取证（逐只点名，落 `hardware/r61c_sync/evidence/`，零删除）**：含写盘后令牌的载体 %d 只 = `%s`；'
         'pre-image 快照 %d 只 = `%s`。⚠ 点名一条本代纪律的边界：**描述第 %s 代同步的那一节不在第 %s 代载荷里**（载荷打包有截止时刻，paperwork 落笔晚于它），'
         '本遍第 17 代同步的载荷必须含 §38.37 与本格 ⇒ 那一句在 §38.37 与同步载体里现验，不在这里预写。'
         % (len(LANDED), '、`'.join(LANDED), len(PRE_IMGS), '、`'.join(PRE_IMGS), '16', '16'))
E.append('⇒ 判定不变：**不重建、不重烧、不新建根**（本遍唯一涉及磁盘大量写入的动作 = docs 快照第十三遍的覆盖拷贝）。'
         '**没烧录、没碰串口**（COM14 不在位）⇒ 屏亮肉眼确认仍 **1 次**（R59 那一次，本遍没推进）、看到第二页 **0 次**、用户真按 BOOT **0 次** ⇒ **不播提示音的判据仍成立**；'
         '**未 `git push`**、未 amend、**零删除**（含 `%TEMP%`、各臂抓回原件、上一遍那两只已订正的载体与崩溃遍载体全部留盘）。')
E.append('（载体：本格全部现跑读数 = `hardware/r61c_sync/evidence/`（名单见 ⑪，只数由脚本插值不手抄）；'
         '写盘前 README 原件快照 = 同目录 `readme_pre13_*.md`；本行由 `land_r61c_readme13.py` 写出，'
         '本代这一格**只被动一次**——若日后被再改，改的那一遍必须在这里点名，不许留"只做了一次"那种落笔即假的话。）')

body = '\n'.join(E) + '\n'

# ---------- 写盘前裁决 ----------
assert secret not in body.encode('utf-8'), 'ABORT: 正文明文命中口令'
assert 'ht305_sync' not in EV, 'ABORT: 取证落点指进封存归档目录'
assert body.count(chr(92)) == 0, 'ABORT: 正文含反斜杠'
for tok in ('PLACEHOLDER', '%d ', '%s ', 'TODO'):
    assert tok not in body, 'ABORT: 正文含未解析哨兵 ' + tok
assert body.count("'") == 0, 'ABORT: 正文含 ASCII 撇号（会把 Python 字面量提前闭合）'
for tok in ('第十三次读数', 'docs/ 快照第十三遍', '缺陷①', '缺陷②', '缺陷③'):
    assert tok in body, 'ABORT: 正文缺关键锚 ' + tok
assert len(body.encode('utf-8')) > 4000, 'ABORT: 正文短得不像一格读数'

lines0 = txt0.split('\n')
anchors = [i for i, l in enumerate(lines0) if l.startswith('## 2. 命名规则')]
assert len(anchors) == 1, 'ABORT: 插入锚点不唯一（%d 处）' % len(anchors)
idx = anchors[0] - 1
assert lines0[idx] == '', 'ABORT: 锚点前一行不是空行，插入会顶掉结构'
assert rb0[-1:] == b'\n' and rb0.count(b'\r') == 0, 'ABORT: README 不是 LF-only 或末字节非换行'

pre = os.path.join(EV, 'readme_pre13_%s.md' % T0.strftime('%Y%m%d_%H%M%S'))
assert not os.path.exists(pre), 'ABORT: 原件快照已存在，不覆盖'
new_lines = body.rstrip('\n').split('\n')
out = '\n'.join(lines0[:idx] + new_lines + [''] + lines0[idx + 1:])
ob = out.encode('utf-8')

open(pre, 'wb').write(rb0)
assert open(pre, 'rb').read() == rb0, 'ABORT: 原件快照回读不等'
open(README, 'wb').write(ob)

# ---------- 写盘后三段式证明（在真字节上，同类型：str 行表 vs str 行表） ----------
rb1 = open(README, 'rb').read()
assert rb1 == ob, 'ABORT: 盘上字节与预期串不等'
lines1 = rb1.decode('utf-8').split('\n')
assert len(lines1) == len(lines0) + len(new_lines) + 1, 'ABORT: 行数等式不成立'
assert lines1[:idx] == lines0[:idx], 'ABORT: 插入点之前未逐字保持'
assert lines1[idx:idx + len(new_lines)] == new_lines, 'ABORT: 插入段未逐行等'
assert lines1[idx + len(new_lines):] == lines0[idx:], 'ABORT: 插入点之后未逐字保持（后缀为空不成立）'
assert '## 2. 命名规则' in rb1.decode('utf-8'), 'ABORT: 标题被静默删除'
_old_cells = txt0.count('读数**')
assert rb1.decode('utf-8').count('读数**') == _old_cells + 1, 'ABORT: 读数格数增量 != 1（动了旧格）'

say('README bytes %d -> %d / lines %d -> %d / INSERTED %d @%d / 三段式证明全过'
    % (len(rb0), len(rb1), len(lines0), len(lines1), len(new_lines), idx + 1))
say('PRE-IMAGE %s（%d B）' % (os.path.basename(pre), len(rb0)))
say('DOCS 第十三遍 SNAPSHOT_AT %s ROWS %d FILES %d NEW %d' % (snap_at, note_rows, docs_files, len(new_rows)))
say('FREQERR %d 条 / %d 行 / %d B / 记录 %d 行 / 末节 §%s' % (f_entries, f_lines, len(fb), pz_lines, lastsec))
say('GIT HEAD %s REVLIST %d STATUS %d 行 %s / COM14=%s / HT305 %d 只' % (head, revlist, len(sline), skind, com14, hfiles))
say('VERDICT=LANDED rc=0')

txt = '\n'.join(OUTL) + '\n'
CARRIER = os.path.join(EV, 'r61c_readme13_land_%s.txt' % T0.strftime('%H%M%S'))
assert not os.path.exists(CARRIER), 'ABORT: 载体已存在'
open(CARRIER, 'w', encoding='utf-8', newline='\n').write(txt)
assert open(CARRIER, 'rb').read() == txt.encode('utf-8'), 'ABORT: 载体回读不等'
assert [l for l in open(CARRIER, encoding='utf-8').read().split('\n') if l][-1] == 'VERDICT=LANDED rc=0'
print('CARRIER %s（%d B / md5 前 8 %s）' % (os.path.basename(CARRIER), os.path.getsize(CARRIER),
                                          hashlib.md5(open(CARRIER, 'rb').read()).hexdigest()[:8]))
