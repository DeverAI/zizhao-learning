# FreqErr.md 第十四批落地器（R61 尾巴遍）。三条硬规矩继承 `land_r61_38.py`：
#   ①幂等前置（"R61 第十四批"标题已在册即 ABORT，于是"格式化炸了再来一遍"不需要记忆参与判断）；
#   ②所有裁决排在写盘之前（rc≠0 必须蕴含盘上没动）；
#   ③台账三格在**内存拼好的最终字节串**上先数后写，写完再在盘上复量一次，两处必须同值。
# 行尾口径：本文件现读 CRLF 主导（LF-CR 差值 = 裸 LF 只数）且末行以 CRLF 收尾 ⇒ 追加体沿用 CRLF。
import datetime
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

REPO = r'C:/Users/david/Documents/all_projects/自招学习'
TGT = os.path.join(REPO, 'FreqErr.md')
MACRO = os.path.join(REPO, 'hardware', 'zizhao-esp32s3', 'main', 'provision_ap.c')
MARK = 'R61 第十四批'

pre = io.open(TGT, 'rb').read()
if MARK.encode('utf-8') in pre:
    raise SystemExit('ABORT: 第十四批已在册（幂等门），本遍不叠加')
if not pre.endswith(b'\r\n'):
    raise SystemExit('ABORT: 末行不以 CRLF 收尾，本脚本的 CRLF 追加体会粘行')

sec = re.search(r'#define\s+PROV_PASS\s+"([^"]+)"', io.open(MACRO, encoding='utf-8').read()).group(1).encode()
assert len(sec) >= 4, 'ABORT: 读不到 PROV_PASS 宏本体'

ENTRIES = [
    ('**一条写进排查记录的永久裁决「永不 stage」被下一批的逐只点名清单器无声推翻，而明文门全绿**（R61 尾巴实测：'
     '排查记录第 3792 行 09-25 R58 落的那句「两只都是用户资料…且永不 stage」是在册裁决；'
     '本轮 `make_staged_list_r61.py` 的 EXCLUDE 表只有它自己那 5 条硬编码项 ⇒ 两只原厂整片镜像（8,388,608 B + 3,072 B）'
     '照样进了 `c7de970`；索引侧门那两遍 `TOTAL_HITS=0 / VERDICT=CLEAN` 与「两只进去了」是**同时成立**的）',
     '症状：清单器打印「排除并点名（5 条，每条附理由）」，看起来像逐只审过，实际审的是**我此刻想得起来的脏件**；'
     '门的口径是口令明文，它压根不量「在册裁决」这一维 ⇒ 三只量具（清单、门、我的记忆）全绿，裁决却已经破了。'
     '这一族的坏法不是报错，是**没有任何一格会变红**。',
     '→ 正确做法：①**排除表必须以裁决为源**，不能以印象为源 —— 永久排除项要么从 `.gitignore` 现读、'
     '要么从记录里那句「永不 stage / 永不入库」grep 出来喂给清单器；②给提交轮加一道**裁决门**：'
     '拿 stage 清单问「这 N 条在册永久排除项在不在里面」，命中即 rc=1，且这道门自己要有阳性对照；'
     '③事后处置守「不改历史」：本遍只做 `git rm --cached` + 准确文件名写进 `.gitignore`（不用 `*.bin` 通配，'
     '通配会无声吞掉以后真要入库的二进制），并把「blob 永久留在本地历史」这条代价**点名**而不是隐藏。',
     '→ **同族**：项目记忆「命中 0 ≠ 干净」、「计数型安全门必须配阳性对照」、「门只打印不置退出码」、'
     '本文件 R61 第十二批那条「取证脚本漏抽一整类行而读数全绿」（同一形态换了动作：那次漏的是**行**，这次漏的是**规则**）。'),
    ('**`git diff --numstat` 对二进制行打的是 `-\\t-\\t路径`：汇总器把它当整数就崩，当 0 就「只数对、构成说错」**'
     '（R61 尾巴实测：`land_r61_38.py` 首跑 `ValueError: invalid literal for int() with base 10` 崩在写盘前 ⇒ 盘上零改动；'
     '若当时顺手写成 `int(x or 0)`，正文就变成「517 只 / +30,991 / −368」而**没人说明那 2 只是二进制**）',
     '症状：一把尺对一类输入返回**非数字哨兵**而不是 0。只数仍然对（它走的是行数），错的是「这些 +/- 覆盖了几只文件」这个构成陈述。',
     '→ 正确做法：①解析器按行**分桶**（数字行相加、哨兵行逐只点名），不许把 `-` 折叠成 0；'
     '②正文那句「+A / −B」必须同时带上「文本 N 只 / 二进制 M 只」这一对分母；'
     '③同类哨兵先查被解析工具的手册（`--numstat` 的 `-`、`--shortstat` 的省略、`ls-files -s` 的八进制 mode）。',
     '→ **同族**：项目记忆「汇总行不许只认一种格式」、「命令文本含被搜串 ⇒ 计数自指永不为真」'
     '（都是**把量具输出当成同一种格式**）。'),
    ('**落地器正文里的数量词写成字面量，其中一处落盘后被自己现数推翻**（R61 尾巴实测：同一次落地里三处 —— '
     '标题写死「517 只」而 N9 本是现读变量；把 5 个字段的互核写成「**六个**两侧独立读数」；'
     '「第 14 代**全部** 6 只脚本」而该目录此刻实有 11 只工具（`scripts/` 10 + `gate/` 1））',
     '症状：三处都不是算错 —— 517 恰好等于现读值、那 5 个字段的 assert 逐字全过、那 6 只脚本也确实各带一条守卫；'
     '坏在**措辞的主张范围比证据大**（「全部」vs「同步链那 6 只」）与**字面量没有出处**（N9 一变，标题不会跟着变）。',
     '→ 正确做法：①正文里**每一个**数量词都必须是现读变量的插值，写不出变量的句子就不写数；'
     '②带「全部 / 所有 / 都」的句子必须能被一条现跑的量具证伪 —— 本遍的改法是把「全部 6 只脚本」降级成「同步链那 6 只」，'
     '并在同一句里点名另外 5 只是什么、声明守卫不覆盖它们；③落盘**之后**再拿被落盘的那一句现数一遍，'
     '不成立就地订正并写明订正依据（第三条就是这么抓到的）。',
     '→ **同族**：项目记忆「口径越界（A 集合的读数说成 B 集合）」、「裸 grep -c 是快照会随引用漂」、'
     '「半截取证 = 汇总行只数对而名单被截断」、「可证伪预期不得写绝对数」。'),
    ('**往 `%` 格式串里塞带 `%` 的字面量（`%TEMP%`），以及占位符个数与参数个数不匹配**'
     '（R61 尾巴实测：同一只落地器连炸两次 —— `ValueError: unsupported format character` 与 '
     '`TypeError: not enough arguments for format string`；崩溃遍每次落盘前 `wc -l` 复量目标 = 3,879 行原样）',
     '症状：这类错误**只会响不会静默**，看起来无害；真正的坑是它逼我「再跑一遍」，而重复跑同一只**追加器** = 同一节落两份'
     '（R61 第十三批刚登记过那一族；本遍的增量只有一条：幂等门让「再跑一遍」从危险变成安全）。',
     '→ 正确做法：①正文里的字面 `%` 一律写 `%%`（或改用不带裸 `%` 的拼接方式）；'
     '②追加器一律先装**幂等前置门**（本节标题已在册即 ABORT），于是「再来一遍」不需要我记得上一遍有没有落盘；'
     '③崩溃那几遍的「盘上没动」要**当场量**并写进结论，不许事后声称。',
     '→ **同族**：本文件第十三批第①条（幂等前置第一次拿到执行者）、项目记忆「崩溃那次的读数不作数」、'
     '「同轮两遍产物必须点名权威」。'),
    ('**从载体现读的数值字段没定类型 ⇒ 字符串与整数相比恒不等，一条本该平的账报成不平**'
     '（R61 尾巴实测：`KEEP = field(LST, r"进清单 (\\d+) 只")` 漏了第三个参数 `int`，'
     '于是 `MOD + UNT - DROP == KEEP`（23+489−5=507）这条**成立的**等式报 ABORT）',
     '症状：读数本身完全正确，量具也真的在量，唯一缺陷是它的返回类型。'
     '危险在它会把我推向「怀疑清单」而不是「怀疑比较两端的类型」——而清单是对的。',
     '→ 正确做法：①凡参与算术或相等比较的载体字段，取数处显式 cast，并把 cast 当作这个读数字段的一部分；'
     '②断言失败时**先把两侧类型与 repr 打出来**再怀疑数据；③「门是好的、门的输入没定型」比门缺失更骗人，'
     '因为它给出的是一个**具体而错误的数值结论**。',
     '→ **同族**：项目记忆「数字连算法与漏判」、「量具数值对而过程未自证比报错数更危险」（R50 那条）。'),
]

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows = []
for t, s, fix, kin in ENTRIES:
    rows += ['[错误类型] ' + t, s, fix, kin, '']

EB = '[错误类型]'.encode('utf-8')   # bytes 字面量不许含非 ASCII ⇒ 由 str 编码出来
n_before = sum(1 for l in pre.splitlines() if l.startswith(EB))
lines_before = pre.count(b'\n')
bytes_before = len(pre)


def build(size_hint):
    return (
        '**【%s 落地｜R61 第十四批 %d 条】** 追加之前现读磁盘（本脚本进入时刻 %s）：'
        '`^[错误类型]` = **%d** 条 / **%d** 行 / **%s** B；本批正文 = **%d** 条 / **%d** 行'
        '（每条 4 行：标题 / 症状 / 正确做法 / 同族，条间以空行分隔）；台账行自身不另加条目；'
        '**落盘后的终态三格 = 在内存拼好的最终字节串上先数后写**：条 **%d** / 行 **%d** / B **%s**'
        '（写完后本脚本还在盘上复量一次，两处必须同值）。'
        '口径明文闸 = 追加段现扫 PROV_PASS 宏值命中 0 才动手。' % (
            ts, len(ENTRIES), ts, n_before, lines_before, format(bytes_before, ','),
            len(ENTRIES), len(rows),
            n_before + len(ENTRIES), lines_before + len(rows) + 1, format(size_hint, ',')))


hdr = build(bytes_before)
for _ in range(6):
    app = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
    nh = build(bytes_before + len(app))
    if nh == hdr:
        break
    hdr = nh
else:
    raise SystemExit('ABORT: 终态字节数与 header 自身长度不收敛')

append_bytes = ('\r\n'.join(rows) + '\r\n' + hdr + '\r\n').encode('utf-8')
assert sec not in append_bytes, 'ABORT: 追加段含口令明文'
exp = (pre + append_bytes)
exp_entries = sum(1 for l in exp.splitlines() if l.startswith(EB))
exp_lines = exp.count(b'\n')
assert exp_entries == n_before + len(ENTRIES), 'ABORT: 拼好的终态条目数 %d 与预期 %d 不符' % (
    exp_entries, n_before + len(ENTRIES))
assert hdr.encode('utf-8') in exp, 'ABORT: header 没进终态字节串'
assert ('B **%s**' % format(len(exp), ',')) in hdr, 'ABORT: header 里那格终态字节数不是最终串的实际值'

io.open(TGT, 'ab').write(append_bytes)
chk = io.open(TGT, 'rb').read()
assert chk[:bytes_before] == pre, 'ABORT: 前缀被改动'
post_entries = sum(1 for l in chk.splitlines() if l.startswith(EB))
post_lines = chk.count(b'\n')
assert (post_entries, post_lines, len(chk)) == (exp_entries, exp_lines, len(exp)), 'ABORT: 盘上复量与内存终态不同值'
print('EOL CRLF=%d bareLF=%d | APPEND=CRLF' % (chk.count(b'\r'), post_lines - chk.count(b'\r')))
print('ENTRIES %d -> %d (本批 +%d)' % (n_before, post_entries, len(ENTRIES)))
print('LINES %d -> %d | BYTES %d -> %d' % (lines_before, post_lines, bytes_before, len(chk)))
print('MD5 %s -> %s' % (hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('VERDICT=LANDED rc=0')
