# FreqErr.md 第十七批落地器（R61b 收口遍第二段）+ 一处就地订正（第 2254 行 = 第十三批台账行）。
# 被订正那句 = 第十五批回填第十三批台账行时插进去的句尾「见本批第②条与本文件第 2254 行）：
#   "本批"随插入点换了指代（写者是第十五批，句子住在第十三批的行里），那个行号成了自指。
# 缺陷是第十六批落盘后按规矩**把整行读出来**时才看见的（结构尺四把全过）。
# 规矩照旧：幂等门 → 全部裁决排在写盘之前 → pre-image → 写盘后行级差集证明。
import datetime
import glob
import hashlib
import io
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')
MARK = 'R61 第十七批'
BS = chr(92)          # 正文不新增反斜杠 ⇒ 要指代这个字符时由代码给，不写进串里
BS4 = u'本文件第 ' + BS + 'd'   # 指代尺要匹配的正则片段同样由代码拼，源码里不落裸反斜杠

_T0 = time.time()


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）' % (prefix, must, len(hits))
    return hits[0]


def abort_carrier(prefix, marker):
    """上一遍崩在哪只载体：按 mtime 排除**本进程之后**落盘的（本遍自己的载体正在被 tee 写）。"""
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if os.path.getmtime(p) < _T0 and marker in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r 标记 %r 命中 %d 只（应为 1）' % (prefix, marker, len(hits))
    return hits[0]


pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十七批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')

LAND16 = one('r61b_freqerr16_*.txt', 'VERDICT=LANDED rc=0')
PIMG16 = one('freqerr_pre16_*.md')
ABORT16 = abort_carrier('r61b_freqerr16_*.txt', 'AssertionError: ABORT: 全册仍有')
ABORT17 = abort_carrier('r61b_freqerr17_*.txt', 'AssertionError: ABORT: 加粗只数增量')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'
pl = pre.splitlines()
EB = '[错误类型]'.encode('utf-8')
n_before = sum(1 for l in pl if l.startswith(EB))
lines_before = pre.count(b'\n')
bytes_before = len(pre)

# ---------- 就地订正：锚 = 整段，首尾与原段对称（都以 `）。` 收尾），命中恰 1 行、行内恰 1 次 ----------
OLDSEG = '，见本批第②条与本文件第 2254 行）。'
NEWSEG = ('，见**第十五批**第②条；「本批」两字落在**第十三批**的台账行里会被读成第十三批，'
          '而写下这句的是第十五批 ⇒ 指代随插入点漂了，此处按写者点名，那个自指的行号一并摘掉）。')
_hits = [i for i, l in enumerate(pl) if OLDSEG.encode('utf-8') in l]
assert len(_hits) == 1, 'ABORT: 要订正那句命中 %d 行（应为 1）' % len(_hits)
LN1 = _hits[0] + 1
_line = pl[_hits[0]].decode('utf-8')
assert _line.count(OLDSEG) == 1, 'ABORT: 第 %d 行里锚文本出现 %d 次' % (LN1, _line.count(OLDSEG))
assert _line.startswith('**【') and 'R61 第十三批'.encode('utf-8') in pl[_hits[0]], \
    'ABORT: 第 %d 行不是第十三批的台账行 ⇒ 宿主判错，"本批"漂移的说法不成立' % LN1

_mid = pre.replace(OLDSEG.encode('utf-8'), NEWSEG.encode('utf-8'), 1)
assert _mid != pre and _mid.count(b'\n') == lines_before, 'ABORT: 订正没有生效或改了行数'
assert sum(1 for l in _mid.splitlines() if l.startswith(EB)) == n_before, 'ABORT: 订正改了条目数'
D1 = len(NEWSEG.encode('utf-8')) - len(OLDSEG.encode('utf-8'))
assert len(_mid) == bytes_before + D1, 'ABORT: 订正后的尺寸与增量不等'
assert OLDSEG.encode('utf-8') not in _mid, 'ABORT: 旧句仍在'

_after = _mid.splitlines()[_hits[0]].decode('utf-8')
# 指代尺（本遍新装，执行者）：被改那一行改后不许再带"本批第 / 本遍第 / 本文件第+行号"。
_deix = re.findall(u'本批第|本遍第|本文件第 ' + str(LN1) + u' 行|' + BS4 + u'+ 行', _after)
assert not _deix, 'ABORT: 订正后第 %d 行仍带位置相关指代 %s' % (LN1, _deix)
assert '第十五批' in _after and _after != _line, 'ABORT: 改后整行没带上写者点名（正向钉）'
# 预期增量不写字面量：加粗尺的增量必须恰好等于新段自己声明的对数（本遍首跑就栽在这格）。
assert OLDSEG.count('**') == 0, 'ABORT: 旧段自带加粗 ⇒ "增量全来自新段"的等式不成立'
BOLD_BEFORE = _line.count('**')
BOLD_AFTER = _after.count('**')
_PAIRS = NEWSEG.count('**') // 2
assert BOLD_AFTER - BOLD_BEFORE == _PAIRS * 2, 'ABORT: 加粗只数增量 = %d，新段声明 %d 对' % (
    BOLD_AFTER - BOLD_BEFORE, _PAIRS)
INC_HITS = [i + 1 for i, l in enumerate(pl) if '预期增量写成字面量' in l.decode('utf-8')]
assert INC_HITS, 'ABORT: 在册那条「预期增量写成字面量」现读 0 处 ⇒ 正文那格的指针是假的'

_pl_pre16 = io.open(PIMG16, encoding='utf-8').read().splitlines()
_L16 = [l for l in pl if 'R61 第十六批'.encode('utf-8') in l]
assert len(_L16) == 1, 'ABORT: 第十六批台账行现读 %d 只（应为 1）' % len(_L16)
_m16 = re.search(r'\*\*落盘后的终态三格 = 在内存拼好的最终字节串上先数后写\*\*：条 \*\*(\d+)\*\* / 行 \*\*(\d+)\*\* / B \*\*([\d,]+)\*\*',
                 _L16[0].decode('utf-8'))
assert _m16, 'ABORT: 第十六批台账行取不到终态三格'
T16 = (int(_m16.group(1)), int(_m16.group(2)), int(_m16.group(3).replace(',', '')))
assert T16 == (n_before, lines_before, bytes_before), \
    'ABORT: 第十六批台账声称终态 %s != 本遍现读 %s ⇒ 它之后到本遍之间还叠了别的动作' % (T16, (n_before, lines_before, bytes_before))
assert len(_pl_pre16) < lines_before, 'ABORT: pre-image %d 行 >= 盘上 %d 行' % (len(_pl_pre16), lines_before)

ENTRIES = [
    ('**把订正句插进"别人家的台账行"时，句里的"本批"随插入点换了指代，那个行号指针变成自指**'
     '（R61b 实测：第十五批回填第十三批台账行时，句尾落的是「%s」——落笔那一刻"本批"=第十五批、'
     '行号指被订正那一行；这句从此**住在第十三批的台账行（第 %d 行）里**，读者按所在行读，'
     '"本批"就成了第十三批，行号成了自己指自己。宿主（第十三批台账行）由本遍现读该行标题现验）' % (OLDSEG.strip('，。'), LN1),
     '症状：第十六批落盘后我按规矩把**整行**打印出来读，才看见这两处。四把尺寸尺全看不见它 —— '
     '字节、行数、条目数、加粗只数（本遍改前 %d -> 改后 %d，增量恰好 = 新段自己点名的 %d 对名字）；'
     '而它给的是一条**读起来通顺、指向错的**取证指针，比空句更难发现（空句会被占位符闸抓，指代错没有任何闸）。' % (BOLD_BEFORE, BOLD_AFTER, _PAIRS),
     '→ 正确做法：①往**他人的**台账行/正文里插句子时，句内不写「本批 / 本遍 / 本节 / 上一括号」这类**位置相关**指代，'
     '只写**绝对名**（第十五批第②条、本行自身）——写者与被插入宿主不同一时，相对指代必然漂；'
     '②「本文件第 N 行」而 N 恰是这句话所在那一行 = 自指，永真亦永不信息，一律改成按批次名指；'
     '③给这类指代装执行者：订正后对被改那一行扫「本批第」「本遍第」「本文件第+数字+行」三种形状必须 = 0，'
     '正向钉 = 改后整行必须含写者名「第十五批」（只写"别处没有"会在整句缺失时恒真）；'
     '④本遍首跑另有一格红在**另一族**上（该族本遍现读 %d 处：第 %s 行，标题都带「预期增量写成字面量」）：'
     '加粗尺的预期增量我写成字面量 2，而新段点名了两个批次 = 4 ⇒ 预期增量要由"新段自己声明的量"推出；'
     '崩在写盘前、盘上零改动（载体 = 同目录那只本批前缀、带 `ABORT` 的）。'
     % (len(INC_HITS), ', '.join(str(x) for x in INC_HITS)),
     '→ **同族**：本文件第十六批第③条（模板句被复制 ⇒ 锚不唯一，同一族"把上一批的措辞当成这一批的常量"）、'
     '第十五批第②条（回填句必须点名出处，不许假装复算）、项目记忆「指针必须 grep 得到且"第一次"带限定语」'
     '「引用即复跑」「口径越界（A 集合的读数说成 B 集合）」——本条是**指代**层的口径越界。'),
]

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += ['[错误类型] ' + t, s, fix, kin, '']


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十七批 %d 条】** 追加之前现读磁盘（本脚本进入时刻 %s）：'
        '`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B；本批正文 = **%d** 条 / **%d** 行'
        '（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；台账行自身不另加条目；'
        '**同遍就地订正一处**：第 %d 行（第十三批台账行，宿主由现读该行标题确认）%d B -> %d B，'
        '行数与条目数不变，该行加粗只数 %d -> %d（增量 = 新段自己点名的 %d 对，不写字面量）；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**'
        '（盘上证明 = 行级差集：差异行必须恰为第 %d 行，其余行逐字等，尾部追加段逐行等）。'
        '本遍进入前的读数出处 = 同目录 `%s`（第十六批 rc=0）、`%s`（第十六批首次 rc=1）、`%s`（本批首次 rc=1，红在预期增量的字面量）。'
        '口径明文闸 = 追加段与订正段现扫 PROV_PASS 宏值命中 0 才动手；'
        '指代闸 = 被订正那一行改后扫「本批第 / 本遍第 / 本文件第+数字+行」命中 0 且必须含写者名「第十五批」才动手；'
        '正文反斜杠闸 = 本批新写文本含反斜杠字符的行数 = 0（要指代这个字符就写它中文名）。' % (
            ts, len(ENTRIES), ts, n_before, lines_before, format(bytes_before, ','),
            len(ENTRIES), len(rows),
            LN1, len(OLDSEG.encode('utf-8')), len(NEWSEG.encode('utf-8')), BOLD_BEFORE, BOLD_AFTER, _PAIRS,
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ','), LN1,
            os.path.basename(LAND16), os.path.basename(ABORT16), os.path.basename(ABORT17)))


hdr = build(bytes_before + D1)
for _ in range(8):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + D1 + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与 header 自身长度不收敛')

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
exp = _mid + append_bytes
assert sec not in exp, 'ABORT: 本遍写出去的字节含口令明文'
_newtext = append_bytes.decode('utf-8') + '\n' + NEWSEG
_stray = [l for l in _newtext.split('\n') if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*[:,]*\}', l) or re.search(r'%[sd]\b', l)]
assert not _stray, 'ABORT: 本遍新写文本有 %d 行带未插值占位符：%r' % (len(_stray), [l[:70] for l in _stray[:2]])
_bs = [l[:70] for l in _newtext.split('\n') if BS in l]
assert not _bs, 'ABORT: 本批新写文本有 %d 行含反斜杠字符：%r' % (len(_bs), _bs[:2])
exp_entries = sum(1 for l in exp.splitlines() if l.startswith(EB))
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 终态条目数 %d != %d' % (exp_entries, n_before + len(ENTRIES))
assert hdr.encode('utf-8') in exp and ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: 终态字节数与台账行不自洽'
_tt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'freqerr_pre17_%s.md' % _tt)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'
print('整行 %d 改前(尾 170): ...%s' % (LN1, _line[-170:]))
print('整行 %d 改后(尾 330): ...%s' % (LN1, _after[-330:]))

io.open(TGT, 'wb').write(exp)
chk = io.open(TGT, 'rb').read()
cl, ol = chk.splitlines(), pl
assert len(cl) == len(ol) + len(rows) + 1, 'ABORT: 行数增量与预期不等（%d -> %d）' % (len(ol), len(cl))
_diff = [i for i in range(len(ol)) if cl[i] != ol[i]]
assert _diff == [_hits[0]], 'ABORT: 盘上就地改动行号 = %s（预期只第 %d 行）' % ([x + 1 for x in _diff], LN1)
assert cl[len(ol):] == append_bytes.split(b'\r\n')[:-1], 'ABORT: 追加段逐行不等'
post_entries = sum(1 for l in cl if l.startswith(EB))
assert (post_entries, chk.count(b'\n'), len(chk)) == (exp_entries, exp.count(b'\n'), len(exp)), 'ABORT: 盘上复量与内存终态不同值'
assert OLDSEG.encode('utf-8') not in chk, 'ABORT: 旧句仍在盘上'
assert not re.findall(u'本批第|本遍第', cl[_hits[0]].decode('utf-8')), 'ABORT: 盘上那一行仍带位置相关指代'
assert '第十五批'.encode('utf-8') in cl[_hits[0]], 'ABORT: 盘上那一行没有写者点名（正向钉）'
print('PRE-IMAGE %s (%d B / md5 %s == 写盘前原件)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('EOL CRLF=%d bareLF=%d | APPEND=CRLF' % (chk.count(b'\r'), chk.count(b'\n') - chk.count(b'\r')))
print('ENTRIES %d -> %d (本批 +%d) | LINES %d -> %d | BYTES %d -> %d' % (
    n_before, post_entries, len(ENTRIES), lines_before, chk.count(b'\n'), bytes_before, len(chk)))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
