# backups/README.md 第十三次格就地订正遍（本代第二次动这一格）。
# 为什么要这一遍：首遍（land_r61c_readme13.py + land_r61c_readme13fix.py 核销）把 ①~⑪ 落齐了，
# 但格子里有四处**落笔与盘上事实不符**的话（⑨ 的桶标号丢了前导空格、⑩(c) 把被归类的载体写成另一只、
# ⑩(c) 与 ⑪ 里用了通配名/漏了反引号）。这一族的处置在本仓库只有一种：**就地改掉并在格子里点名改了几次**，
# 不许"留给下一遍"。三条硬规矩照抄落地器：①幂等前置 ②全部裁决排在写盘之前 ③写盘后在真字节上复证。
# 与"插入遍"的差别：本遍是 **k 换 k 的就地替换**（行数不变），所以三段式要换成"逐行 diff 只许命中点名的那几行"。
import ast
import datetime
import glob
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'backups', 'README.md')
EV = os.path.join(REPO, 'hardware', 'r61c_sync', 'evidence')
SRC = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
TOKEN = 'VERDICT=LANDED rc=0'
_T0 = datetime.datetime.now()
PROOF_ONLY = '--proof-only' in sys.argv

# 幂等门：权威判据 = 同前缀载体里有没有写盘后令牌（按行读，不是 endswith —— 那是本批缺陷②）
_prior = [os.path.basename(p) for p in glob.glob(os.path.join(EV, 'r61c_readme13_fix3_*.txt'))
          if TOKEN in io.open(p, encoding='utf-8', errors='replace').read().split('\n')]
assert not _prior, 'ABORT: 本订正遍已经落过一次（%s）⇒ 真幂等门，不叠加' % _prior

raw = io.open(TGT, 'rb').read()
assert raw.count(b'\r') == 0, 'ABORT: README 现读含 CR，行尾口径与在册（全 LF）不符'
assert raw.endswith(b'\n'), 'ABORT: README 末行不以 LF 收尾'
_pimgs = sorted(glob.glob(os.path.join(EV, 'readme_pre13fix_*.md')))
if PROOF_ONLY:
    assert len(_pimgs) == 1, 'ABORT: pre-image 候选 %d 只（应恰 1）⇒ 复核没有唯一基准' % len(_pimgs)
    base_raw = io.open(_pimgs[0], 'rb').read()
    assert base_raw != raw, 'ABORT: pre-image 与现件逐字节等 ⇒ 上一遍根本没动盘，本遍要的是补证而不是复核'
    print('MODE proof-only：基准 = %s（上一遍写盘前原件），被复核对象 = 盘上现件' % os.path.basename(_pimgs[0]))
else:
    assert not _pimgs, 'ABORT: 盘上已有本遍 pre-image %s ⇒ 上一遍已动过盘，本遍必须走 --proof-only 补证' % _pimgs
    base_raw = raw
lines = base_raw.decode('utf-8').split('\n')
assert base_raw.count(b'\r') == 0, 'ABORT: 基准件含 CR ⇒ 行尾口径与在册（全 LF）不符'
assert base_raw.endswith(b'\n'), 'ABORT: 基准件末行不以 LF 收尾'

# ---------- 六处替换（= 本遍改动唯一权威定义；每条锚必须先现读命中恰 1 次、且只落在 1 只行上） ----------
REPL = [
    ('⑨ 桶标号', '（`M` 6 + `??` 51', '（` M` 6 + `??` 51'),
    ('⑩(c) 归因', '现读推翻：`r61c_freqerr19_163104.txt` 末行逐字就是',
     '现读推翻：被归类的那只 = 上一遍载体 `r61c_todo19_fix_20260926_170425.txt`，其末行逐字就是'),
    ('⑩(c) 通配名', '载体 = `r61c_todo19_fix2_*.txt`', '载体 = `r61c_todo19_fix2_20260926_170829.txt`'),
    ('⑪ 反引号 A', '`r61c_freqerr19_163104.txt、`', '`r61c_freqerr19_163104.txt`、`'),
    ('⑪ 反引号 B', '`r61c_todo19_fix2_20260926_170829.txt、`', '`r61c_todo19_fix2_20260926_170829.txt`、`'),
    ('载体行 被动次数', '本代这一格**只被动一次**',
     '本代这一格已被动两次（首遍插入 ①~⑪ → 本遍 `fix_r61c_readme13.py` 就地订正：⑨ 的桶标号、'
     '⑩(c) 的载体归因与通配名、⑪ 的反引号配对，以及本行自己那句"只被动一次"）'),
]
out = base_raw.decode('utf-8')
hits = []
for label, old, new in REPL:
    assert old != new, 'ABORT: 声明 %s 是空替换（old == new）⇒ 名单与改动对不上' % label
    n = out.count(old)
    assert n == 1, 'ABORT: 锚点 %s 现读命中 %d 次（应恰 1），本遍不动盘' % (label, n)
    _lns = [k for k, l in enumerate(lines) if old in l]
    assert len(_lns) == 1, 'ABORT: 锚点 %s 落在 %d 只行上（%s）⇒ 行级归因不唯一' % (label, len(_lns), _lns)
    hits.append((label, _lns[0]))
    out = out.replace(old, new, 1)

# ---------- 写盘前的全部裁决 ----------
nl = out.split('\n')
assert len(nl) == len(lines), 'ABORT: 本遍是就地替换，行数却从 %d 变到 %d' % (len(lines), len(nl))
ch = [(i, a, b) for i, (a, b) in enumerate(zip(lines, nl)) if a != b]
_byrow = {}
for _lb, _i in hits:
    _byrow.setdefault(_i, []).append(_lb)
assert len(set(l for l, _ in hits)) == len(REPL), 'ABORT: 锚点标签有重复 ⇒ 这份名单不能当出处'
# 双向对上：每条声明的落点都必须真的被改到（new==old 那种空声明会让落点多出只行），且每只被改行都必须有声明指着它
assert sorted(_byrow) == [i for i, _, _ in ch], 'ABORT: 锚点落点 %s != 被改行 %s ⇒ 有一处声明没有对象，或有一行被声明之外的手改了' % (
    sorted(_byrow), [i for i, _, _ in ch])
for i, a, b in ch:
    assert b.count('\n') == 0 and a.count('\n') == 0, 'ABORT: 第 %d 行被换进了换行符' % i
    # 每条被改行必须**只**由声明过的替换产生：把该行按声明反向还原，必须逐字等于原行
    back = b
    for label, old, new in REPL:
        back = back.replace(new, old)
    assert back == a, 'ABORT: 第 %d 行含声明之外的改动（还原后不等）' % i

# 内容级闸：只看本遍新写进去的那几行（全册撇号不是本遍的责任，也不许被本遍顺手改掉）
newtxt = '\n'.join(b for _, _, b in ch)
sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(SRC, encoding='utf-8').read()).group(1).encode()
assert sec not in out.encode('utf-8'), 'ABORT: 写出内容含口令明文'
assert chr(39) not in newtxt, 'ABORT: 本遍新写行里有 ASCII 撇号（Python 单引号字面量的自伤族）'
assert not re.search(r'\{[A-Za-z_][A-Za-z0-9_]*\}|%[sd]\b', newtxt), 'ABORT: 本遍新写行里有未插值占位符'
for i, a, b in ch:
    assert b.count(chr(96)) % 2 == 0, 'ABORT: 第 %d 行反引号不成对（本遍正是来修这一族的，别自己再犯）' % i
    _segs = re.findall(r'`([^`]+)`', b)
    assert all(s for s in _segs), 'ABORT: 第 %d 行有空反引号对' % i
    # ⑪ 那句被本遍改过：改完必须是"每只名字各自包一对反引号"，用 `、` 分隔而不是把顿号吞进代码段
    if '、`' in b:
        assert re.search(r'`[^`]+`、`', b), 'ABORT: 第 %d 行的并列代码段分隔符写法仍然错' % i
# 假指针闸：本遍新写行点名的每只"有后缀的名字"必须在全仓（除 .git）按 basename 真存在
_repo_bases = set()
for _r, _ds, _fs in os.walk(REPO):
    if '.git' in _ds:
        _ds.remove('.git')
    _repo_bases.update(_fs)
assert len(_repo_bases) > 100, 'ABORT: 仓库 basename 现读 %d 只 ⇒ 喂给闸的这把尺自己在漏' % len(_repo_bases)
_named = set(re.findall(r'[A-Za-z0-9_.-]+\.(?:txt|md|py|bin|log)', newtxt))
_missing = [x for x in sorted(_named) if x not in _repo_bases]
assert not _missing, 'ABORT: 本遍新写行点名了查无此物的文件：%s' % _missing
# 通配名只许出现在"引用历史崩溃遍"那种场合：本遍把这一格里两处通配都换成了全名，换完必须为 0
assert 'r61c_todo19_fix2_*' not in out, 'ABORT: 通配名没被换掉'
# 这一族自己的反向钉：⑨ 那句里 ` M` 带前导空格（缺陷①量的就是这个前导空格）
assert '（` M` 6 + `??` 51' in out and '（`M` 6' not in out

# 语法体检（本脚本自己）
ast.parse(io.open(__file__, encoding='utf-8').read())

exp = out.encode('utf-8')
print('MODE %s / PLAN %d 处替换 -> 被改行(0-based) %s' % (
    'proof-only' if PROOF_ONLY else 'land', len(REPL), sorted(_byrow)))
print('README 基准 %s B / %d 行 -> 预期 %s B / %d 行（行数等）' % (
    format(len(base_raw), ','), len(lines), format(len(exp), ','), len(nl)))

_tt = _T0.strftime('%Y%m%d_%H%M%S')
if PROOF_ONLY:
    # 补证遍**一律不再写盘、不再造第二只 pre-image**：盘上那份的来历必须只用"基准 + 声明"重算出来核，
    # 重跑写盘等于把"上一遍改了什么"洗成"这一遍改了什么"（本仓库对崩溃遍的处置是不重跑洗绿）。
    PIMG = _pimgs[0]
    print('PRE-IMAGE 沿用上一遍 %s（%s B / md5 前 8 %s）' % (
        os.path.basename(PIMG), format(len(base_raw), ','), hashlib.md5(base_raw).hexdigest()[:8]))
else:
    PIMG = os.path.join(EV, 'readme_pre13fix_%s.md' % _tt)
    assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
    io.open(PIMG, 'wb').write(base_raw)
    assert io.open(PIMG, 'rb').read() == base_raw, 'ABORT: pre-image 回读不等'
    print('PRE-IMAGE %s (%s B / md5 前 8 %s == 写盘前原件)' % (
        os.path.basename(PIMG), format(len(base_raw), ','), hashlib.md5(base_raw).hexdigest()[:8]))
    io.open(TGT, 'wb').write(exp)

chk = io.open(TGT, 'rb').read()
# 这条等式在两种模式下含义不同：落地遍 = 回读自检；补证遍 = **盘上现件确由这套声明产生**（本遍真正的证明）
assert chk == exp, 'ABORT: 盘上现件与"基准 + 声明的 %d 处替换"重算出的终态不等 ⇒ 盘上那份不是这套声明的产物' % len(REPL)
cl = chk.decode('utf-8').split('\n')
assert len(cl) == len(lines), 'ABORT: 回读行数变了'
assert cl == nl, 'ABORT: 盘上逐行 != 内存终态逐行（首个不等在第 %d 行）' % (
    next(k for k in range(len(cl)) if cl[k] != nl[k]) + 1)
assert [i for i, (a, b) in enumerate(zip(lines, cl)) if a != b] == [i for i, _, _ in ch], \
    'ABORT: 出现了计划外的改动行（或有一行没改到）'
for i, a, b in ch:
    assert cl[i] == b and cl[i] != a, 'ABORT: 第 %d 行不在位' % i
    assert a not in cl, 'ABORT: 原句 %d 行仍然在盘上（替换没生效却报成功）' % i
assert chk.count(b'\r') == 0, 'ABORT: 订正后出现 CR，行尾口径破了'
assert '第十三次读数' in chk.decode('utf-8')

# 阳性对照（旧尺必须仍然红）：上一遍崩在 `cl[:i] == lines[:i]` —— 那条判据是从**插入遍**抄来的，
# 对"k 换 k 就地替换"天生不成立：第 1 只被改行之后的每一行都"不等"。这里在同一批真字节上把旧尺再跑一遍，
# 红的形态必须是"除首只被改行外每只都红"——否则"上一遍是尺错、不是盘错"这句归因就没有执行者。
_old_red = [i for i, _, _ in ch if cl[:i] != lines[:i]]
assert _old_red == [i for i, _, _ in ch[1:]], 'ABORT: 旧尺红点形态 %s != "除首只外每只被改行都红" %s ⇒ 归因要重写' % (
    _old_red, [i for i, _, _ in ch[1:]])
print('PROOF k 换 k：%d 只被改行（行数 %d -> %d 等）/ 计划外改动 0 行 / 原句残留 0 只 / 反引号逐行成对 / CR 0' % (
    len(ch), len(lines), len(cl)))
print('OLD-FORM 旧尺在同批真字节上仍然红：%d/%d 只被改行红，首次红在第 %d 行（1-based）⇒ 上一遍 rc=1 是尺错不是盘错' % (
    len(_old_red), len(ch), min(_old_red) + 1))

_md5s = (hashlib.md5(base_raw).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8])
# 崩遍自己有没有留下载体？现扫同前缀（排除上一代的 fix2 核销载体）——0 只 = "记录取证那步自己没落盘"这一族的样本，
# 在这里点名而不含糊过去；"它确实动过盘"的执行者 = 上面那条 `base_raw != raw`（pre-image 与现件逐字节不等）。
_orphan = sorted(b for b in os.listdir(EV) if b.startswith('r61c_readme13_fix') and not b.startswith('r61c_readme13_fix2_'))
if PROOF_ONLY:
    assert not _orphan, 'ABORT: 崩遍居然留下了载体 %s ⇒ "它没落载体"这句要重判' % _orphan
    _pm = datetime.datetime.fromtimestamp(os.path.getmtime(PIMG)).strftime('%Y-%m-%d %H:%M:%S')
    assert os.path.basename(PIMG).startswith('readme_pre13fix_'), 'ABORT: 基准不是本订正遍的 pre-image：' + PIMG
    _crash_note = (
        'DEFECT-本遍自己 上一遍（同一只脚本首跑，时刻 = pre-image mtime %s）rc=1 且**已动盘、没落载体**'
        '（同前缀现扫孤儿载体 %d 只；"已动盘"的执行者 = 盘上现件与 pre-image 逐字节不等，见 MODE 那格）。'
        '红在哪：证明段那条 `cl[:i] == lines[:i]`（"第 i 行之前逐字等"）是从**插入遍**抄来的，'
        '对 k 换 k 就地替换天生不成立 —— 第 1 只被改行之后每一行都"不等"，于是**盘上内容对而证明全红**。'
        '同族第三次（首次 = §38.36 缺陷 (o) 的逐位置比两代行；第二次 = 本代 README 第十三格首遍那句 `+1` 算式）。'
        '本遍不重跑写盘、不洗绿：以 pre-image 为基准重算终态与盘上现件比（PROOF 那格 chk==exp），'
        '并把旧尺在同批真字节上的红跑出来当阳性对照。' % (_pm, len(_orphan)))
    _mode_note = 'MODE proof-only（补证遍）：基准 = 上一遍写盘前原件（pre-image），被核对象 = 盘上现件，本遍**一字节都不写 README.md**'
else:
    _crash_note = 'DEFECT 落地遍：本遍写盘，无补证语义（若日后崩在证明段，另走 --proof-only 补证并在这里点名）'
    _mode_note = 'MODE land（落地遍）：基准 = 写盘前原件，本遍写 README.md 一处'
_carrier_lines = [
    'backups/README.md 第十三次格就地订正遍（本代第二次动这一格），现跑于 %s' % _T0.strftime('%Y-%m-%d %H:%M:%S'),
    _mode_note,
    'WHY 首遍落齐 ①~⑪ 之后仍有四处"落笔与盘上事实不符"：⑨ 把桶标号写成 `M`（丢掉前导空格，而缺陷①量的正是它）/ '
    '⑩(c) 把被归类的载体写成 `r61c_freqerr19_163104.txt`（复核遍现读的是 `r61c_todo19_fix_20260926_170425.txt`）/ '
    '⑩(c) 与 ⑪ 用了通配名 `r61c_todo19_fix2_*.txt` / ⑪ 三只并列名的反引号只开不闭',
    'REPL %d 处（每条锚写盘前 assert 现读命中恰 1 次、且只落 1 只行、new != old）：%s' % (len(REPL), '、'.join(l for l, _ in hits)),
    'PROOF k 换 k / 行数 %d 等 / 盘上逐行 == 内存终态逐行 / 计划外改动 0 行 / 原句残留 0 只 / '
    '还原式（新行按声明反向还原必逐字等于原行）' % len(lines),
    'GATES 明文 HITS=0 / 新写行 ASCII 撇号 0 / 未插值占位符 0 / 反引号逐行成对且无空对 / CR 0 / 通配名残留 0 / '
    '本遍新写行点名的名字 %d 只在全仓（除 .git）按 basename 全部存在' % len(_named),
    'MD5 %s -> %s / %s B -> %s B / 行尾全 LF 两把尺同值' % (
        _md5s[0], _md5s[1], format(len(base_raw), ','), format(len(chk), ',')),
    'PRE-IMAGE %s' % os.path.basename(PIMG),
    'OLD-FORM 旧尺（"第 i 行之前逐字等"）在同批真字节上仍然红：%d/%d 只被改行红，首次红在第 %d 行（1-based）'
    '⇒ 上一遍 rc=1 是**尺错**不是**盘错**（新尺 cl==nl 全等）' % (len(_old_red), len(ch), min(_old_red) + 1),
    _crash_note,
    'NOTE 本遍**只动这一格被点名的 %d 行**（%d 处替换落在 %d 只行上，见上面 REPL 的落点行号），'
    '其余 %d 行逐字未动；零删除、零覆写旧格（被改的 %d 行原件同时在 pre-image 里）' % (
        len(ch), len(REPL), len(ch), len(lines) - len(ch), len(ch)),
]
_car = os.path.join(EV, 'r61c_readme13_fix3_%s.txt' % _tt)
assert not os.path.exists(_car), 'ABORT: 载体目标已存在 ' + _car
_body = ('\n'.join(_carrier_lines) + '\n' + TOKEN + '\n').encode('utf-8')
io.open(_car, 'wb').write(_body)
_back = io.open(_car, 'rb').read()
assert _back == _body, 'ABORT: 载体回读不等'
# 末行令牌：按**行读**比较（`endswith(TOKEN)` 对以换行收尾的文件恒假 = 本批缺陷②，别在自己载体上重犯）
_ls = [l for l in _back.decode('utf-8').split('\n') if l]
assert _ls[-1] == TOKEN, 'ABORT: 本遍载体末行不是令牌（现为 %r）' % _ls[-1]
assert _ls[0].startswith('backups/README.md')
print('CARRIER %s（%d B / md5 前 8 %s / 末行按行读 == 令牌）' % (
    os.path.basename(_car), len(_back), hashlib.md5(_back).hexdigest()[:8]))
print(TOKEN)
