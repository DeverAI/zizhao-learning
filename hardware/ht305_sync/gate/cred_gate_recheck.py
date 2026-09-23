"""明文门·复验版：扫 hardware/ht305_sync/ 归档后的**全部**文件（而不是 %TEMP% 候选）。
只写文件名 + 命中次数 + 总只数，绝不写/打印口令。

用法：由 gate/run_cred_gate_recheck.ps1 设置环境变量 HT305_TMP_FOR_GATE 后调用：
      python cred_gate_recheck.py <输出文件路径> [打包截止时刻 HH:MM:SS]
第二个参数是**口径钉**：输出里若不带"本批清单/门是在载荷截止时刻 T 之前还是之后跑的"，
下一轮就会把这个快照当成实时状态引用（本机已因此被订正过一次，见排查记录 §31.2）。

【09-23 12:1x 两处结构修订（R45 空上下文复查 P1-3 + 没能验证 #4）】
 ⑴ 本模块把"扫一个目录"抽成 `scan()`，`gate/cred_gate_selftest.py` 用**哨兵口令**走同一个 `scan()` ⇒
    证明"脏了会响"，而不只是"扫过干净集合"。真口令从不经手 selftest。
 ⑵ 输出**不再原地覆写**上一代 ⇒ 文件名带时刻（由调用方给），否则被引用的那一代读数在仓库里查无此字节。
"""
import datetime, os, re, sys

# GBK 控制台下打印 `⇒` 会崩（见 `FreqErr.md` ht305 段"`rc≠0` 被读成'没产出'"那条）⇒ 输出编码显式化，别等 rc≠0 再查。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

DST = r'C:/Users/david/Documents/all_projects/自招学习/hardware/ht305_sync'
SRC = r'C:/Users/david/Documents/all_projects/自招学习/hardware/zizhao-esp32s3/main/provision_ap.c'


def scan(root, secrets, exclude_rel=''):
    """root 下全部文件的字节里逐只 count 每个口令。返回 (只数, {口令名: 累计命中}, 命中行)。
    secrets = [(名字, bytes), ...]；exclude_rel = 相对 root 要跳过的那只（本门自己的输出）。"""
    n = 0
    tot = {name: 0 for name, _ in secrets}
    rows = []
    for r, dirs, fs in os.walk(root):
        for fn in sorted(fs):
            p = os.path.join(r, fn)
            rel = os.path.relpath(p, root).replace('\\', '/')
            if rel == exclude_rel.replace('\\', '/'):
                continue
            b = open(p, 'rb').read()
            n += 1
            got = {name: b.count(s) for name, s in secrets}
            for name, c in got.items():
                tot[name] += c
            if any(got.values()):
                rows.append('HIT ' + rel + ' ' + ' '.join('%s=%d' % (k, v) for k, v in got.items()))
    return n, tot, rows


if __name__ == '__main__':
    m = re.search(rb'#define\s+PROV_PASS\s+"([^"]*)"', open(SRC, 'rb').read())
    if not m:
        print('ABORT: 读不到 PROV_PASS 宏本体'); sys.exit(1)
    env = os.environ.get('HT305_TMP_FOR_GATE')
    secrets = [('PROV_PASS_TOTAL_HITS', m.group(1))]
    if env:
        secrets.append(('SSH_TOTAL_HITS', env.encode('utf-8')))
        del os.environ['HT305_TMP_FOR_GATE']

    now = datetime.datetime.now().strftime('%H:%M:%S')
    lines = ['ht305_sync 归档后的明文门复验（现跑于 09-23 ' + now + '，脚本 = gate/cred_gate_recheck.py）',
             '判据：字节级 count(口令明文)。PROV_PASS 由脚本按 `#define PROV_PASS` 现读；'
             'SSH 口令由 PS 侧 DPAPI 现解后经环境变量传入 —— 两侧都不内嵌字面量。',
             '口径：扫的是**归档后**的全部文件（含本门脚本自身与 README/MANIFEST），排除本输出文件。']
    if len(sys.argv) > 2:
        lines.append('快照口径：本批"内容 → 门 → 清单"以 **打包截止时刻 ' + sys.argv[2] + '** 为界；'
                     '早于它的字节进包，晚于它的改动（含本门输出与清单自身）**不在**同步包里 ⇒'
                     '引用本文件时请连这个界一起引。')
    else:
        lines.append('快照口径：未传截止时刻参数 ⇒ 本文件**不带界**，引用时必须自己现跑并补时刻。')
    lines.append('只留末版已作废：本文件名带时刻 ⇒ 每一代的字节都在仓库里，被引用的那一代可复核。')
    lines.append('')

    out_path = os.path.join(DST, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    rel_out = os.path.relpath(out_path, DST).replace('\\', '/')
    n, tot, rows = scan(DST, secrets, exclude_rel=rel_out)
    lines += rows
    lines += ['', 'FILES_SCANNED=' + str(n)]
    for name, _ in secrets:
        lines.append(name + '=' + str(tot[name]))
    if not env:
        lines.append('SSH_TOTAL_HITS=SKIPPED(环境变量未设置)')

    open(out_path, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
    print('WROTE', os.path.basename(out_path), '| FILES_SCANNED=' + str(n),
          ' '.join('%s=%d' % (k, v) for k, v in tot.items()))
