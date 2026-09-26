# 订正遍（第十一次读数的载体行）：上一遍插进去那行有**两处说不通的话**，逐处点名：
#   (a) "⑥⑦ 两格的输入 = `r61b_verify_root_*` 与 `r61b_docs_snapshot11_*`" —— 后一只是 **⑨** 那格（docs 快照）的输入，
#       不是 ⑥⑦ 的；把两只并成"两格的输入"= 指针指错。
#   (b) "本遍对 README 只做了一次插入" —— **落笔即假**：那一遍自己第一跑就把行插成吞空行的坏态（补丁遍又插了一根 `\n`），
#       本遍是**第三次**动这一只文件。这正是历代登记的"注释/正文里的将来式与绝对数没有执行者"同族。
# 规矩照旧：幂等门（旧句还在才动手）→ 全部裁决排在写盘之前 → 三段字节证明 → 只数从上一遍日志现读再相加，不手抄。
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
RM = os.path.join(REPO, 'backups', 'README.md')
EV = os.path.join(REPO, 'hardware', 'r61b_sync', 'evidence')


def one(prefix, must=None):
    hits = [p for p in sorted(glob.glob(os.path.join(EV, prefix)))
            if must is None or must in io.open(p, encoding='utf-8', errors='replace').read()]
    assert len(hits) == 1, 'ABORT: 前缀 %r（含 %r）命中 %d 只（应为 1）' % (prefix, must, len(hits))
    return hits[0]


# 三只载体现读点名（不硬编码名字：按前缀 + 内容各扫一只）
LOG_A = one('r61b_readme11_land_*.txt', 'VERDICT=LANDED rc=0')
LOG_B = one('r61b_readme11b_fix_*.txt', 'VERDICT=NEWLINE_REPAIRED rc=0')
VR = one('r61b_verify_root_*.txt', 'VERDICT=ROOT_VERIFIED')
DS = one('r61b_docs_snapshot11_*.txt', 'TABLE_ROWS')
BAD = one('readme_broken_nocr_*.md')
mA = re.search(r'README 行 (\d+) -> (\d+) \| 字节 (\d+) -> (\d+)', io.open(LOG_A, encoding='utf-8').read())
mB = re.search(r'README 行 (\d+) -> (\d+) \| 字节 (\d+) -> (\d+)', io.open(LOG_B, encoding='utf-8').read())
assert mA and mB, 'ABORT: 前两遍日志取不到行列'
LN1, BY1 = int(mA.group(2)), int(mA.group(4))          # A 遍（插 ①~⑪）写盘后：组 2 = 行、组 4 = 字节
LN2, BY2 = int(mB.group(1)), int(mB.group(3))          # 修补遍写盘前 = A 遍写盘后的坏态：组 1 = 行、组 3 = 字节
LN2A, BY2A = int(mB.group(2)), int(mB.group(4))        # 修补遍写盘后 = 本遍要接的那一态：组 2 = 行、组 4 = 字节
# 正则的组序是"行前/行后/字节前/字节后"，不是"前一个数/后一个数"——拿错组会把行数当字节数，而这两只数量级差 200 倍。
assert LN2 < 1000 < BY2 and LN2A < 1000 < BY2A, 'ABORT: 行/字节两组取反了（行 %d/%d、字节 %d/%d）' % (LN2, LN2A, BY2, BY2A)
assert BY2 == os.path.getsize(BAD), 'ABORT: 坏态快照 %d B != 修补遍写盘前 %d B ⇒ 那只快照不是本遍要接的那一态' % (
    os.path.getsize(BAD), BY2)
assert LN1 == LN2 and BY2 > BY1, 'ABORT: 行数没停在 A 遍的 %d（或字节没涨）⇒ 坏态形状与登记不同' % LN1

# 旧句按**现读到的载体名**拼出来（不硬编码文件名，但锚文本必须与盘上逐字一致 ⇒ 后面 count == 1 兜住）
OLD = ('⑥⑦ 两格的输入 = 同目录 `%s` 与 `%s`；本行本身由 `land_r61b_readme11b.py` 写出'
       ' ⇒ **本遍对 README 只做了一次插入，没覆写任何旧格**。）') % (
           os.path.basename(VR), os.path.basename(DS))
NEW = ('⑥⑦ 两格的输入 = 同目录 `%s`，**⑨ 那格**的输入 = 同目录 `%s`；'
       '本行本身由 `land_r61b_readme11b.py` 写出，又由 `fix_readme11b_newline.py` 补过一根行尾换行'
       '（坏态取证 = 同目录 `%s`）⇒ **本行是这只 README 在本代被动的第三次**（插 ①~⑪ → 补载体行 → 本遍订正），'
       '上一版那句"只做了一次插入"落笔即假，在此改掉。**三遍都没覆写任何旧格、零删除。**）') % (
           os.path.basename(VR), os.path.basename(DS), os.path.basename(BAD))

pre = io.open(RM, 'rb').read()
p0 = pre.decode('utf-8')
# 修补遍报的"写盘后"那一态必须就是**本遍现读的 README**（那一遍只加了 1 行 / 1 B），否则本遍接的是别的态。
assert (LN2A, BY2A) == (pre.count(b'\n'), len(pre)), \
    'ABORT: 修补遍写盘后 %d 行/%d B != 本遍现读 %d 行/%d B ⇒ 中间还叠了别的动作' % (
        LN2A, BY2A, pre.count(b'\n'), len(pre))
assert p0.count(OLD) == 1, 'ABORT: 要订正那句命中 %d 处（应为 1）⇒ 幂等门/现场态有一个不成立' % p0.count(OLD)
# 正向钉：先确认那句确实**在**（只写"别处没有"那条在整句缺失时会恒真），再确认它只在 OLD 这一处。
assert p0.count('只做了一次插入') == 1, 'ABORT: "只做了一次插入"全册 %d 处（应为 1）⇒ 订正范围与预期不同' % p0.count('只做了一次插入')
assert '只做了一次插入' not in p0.replace(OLD, ''), 'ABORT: "只做了一次插入"还在别处 ⇒ 订正没覆盖全'
_ob = OLD.encode('utf-8')
_nb = NEW.encode('utf-8')
_i = pre.index(_ob)
post = pre[:_i] + _nb + pre[_i + len(_ob):]
assert b'\n' not in _ob and b'\n' not in _nb, 'ABORT: 替换体带换行 ⇒ 本遍"行数不变"的预期不成立'
_exp_lines = pre.count(b'\n')
_exp_bytes = len(pre) - len(_ob) + len(_nb)

ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
PIMG = os.path.join(EV, 'readme_pre11c_%s.md' % ts)
assert not os.path.exists(PIMG), 'ABORT: pre-image 目标已存在，不覆写 ' + PIMG
io.open(PIMG, 'wb').write(pre)
assert io.open(PIMG, 'rb').read() == pre, 'ABORT: pre-image 回读不等'

io.open(RM, 'wb').write(post)
chk = io.open(RM, 'rb').read()
assert chk[:_i] == pre[:_i], 'ABORT: 替换点之前被改动'
assert chk[_i + len(_nb):] == pre[_i + len(_ob):], 'ABORT: 替换点之后被改动'
assert chk[_i:_i + len(_nb)] == _nb, 'ABORT: 替换体逐字不等'
assert (chk.count(b'\n'), len(chk)) == (_exp_lines, _exp_bytes), 'ABORT: 落盘后行/字节与期望不符'
assert OLD.encode('utf-8') not in chk, 'ABORT: 旧句仍在盘上 ⇒ 本遍没改掉它'
# 订正句里**引**了一遍那句假话（带引号），所以"只做了一次插入"这串字符本遍之后仍应有且只有 1 处 —— 那一处是引文，不是断言。
assert chk.count('只做了一次插入'.encode('utf-8')) == 1, 'ABORT: 落盘后那串字符 != 1 处 ⇒ 引文与旧句的边界没了'
assert chk.count(b'\r') == 0 and chk[:3] != b'\xef\xbb\xbf'
print('订正 %d B -> %d B | README 行 %d（不变）| 字节 %d -> %d | md5 %s -> %s' % (
    len(_ob), len(_nb), chk.count(b'\n'), len(pre), len(chk),
    hashlib.md5(pre).hexdigest()[:8], hashlib.md5(chk).hexdigest()[:8]))
print('PRE-IMAGE %s (%d B / md5 %s)' % (os.path.basename(PIMG), len(pre), hashlib.md5(pre).hexdigest()[:8]))
print('三遍咬合（全部现读，无手抄）：A 写盘后 %d 行/%d B → 坏态 %d 行/%d B（+%d B 而 +%d 行 ⇒ 插进去那行没带行尾换行）'
      '→ 修补遍写盘后 %d 行/%d B（+%d 行/+%d B）= 本遍写盘前读数' % (
          LN1, BY1, LN2, BY2, BY2 - BY1, LN2 - LN1, LN2A, BY2A, LN2A - LN2, BY2A - BY2))
print('VERDICT=CARRIER_LINE_CORRECTED rc=0')
