"""明文门的**阴性对照**（哨兵 selftest）：证明这道门"脏了会响"，而不只是"扫过干净集合"。
动机：R45 空上下文复查"我没能验证 #4"——历次 `TOTAL_HITS=0` 只证明被扫的集合干净，
从未证明计数与 `HIT` 报告这条路径在**真命中**时会亮。

做法：用**哨兵串**（不是任何真口令）造一棵临时目录树，喂进与真门**同一个** `scan()`，
断言 ⑴ 只数对、⑵ 命中的正是那只、⑶ 干净树 0 命中、⑷ `exclude_rel` 真的把指定那只排掉。
真口令（`PROV_PASS` / ht305 SSH）在本脚本里**一次都不出现**，也不读 `provision_ap.c`。
"""
import os, shutil, sys, tempfile

# GBK 控制台下的非 ASCII print 会崩（见 `FreqErr.md` ht305 段"`rc≠0` 被读成'没产出'"那条）
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

sys.dont_write_bytecode = True  # import 同门脚本会在 gate/ 落下 __pycache__ ⇒ 归档里不许出现构建副产物
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cred_gate_recheck import scan  # noqa: E402  —— 与真门共用同一段计数代码

CANARY = b'SENTINEL_CANARY_NOT_A_SECRET_7c1f'
d = tempfile.mkdtemp(prefix='cred_gate_selftest_')
try:
    open(os.path.join(d, 'clean_a.txt'), 'wb').write(b'nothing here\n')
    open(os.path.join(d, 'clean_b.txt'), 'wb').write(CANARY[:8] + b' <- only a prefix, must NOT match\n')
    dirty = os.path.join(d, 'dirty.txt')
    open(dirty, 'wb').write(b'header\n' + CANARY + b'\nbody ' + CANARY + b'\n')

    n, tot, rows = scan(d, [('CANARY', CANARY)])
    assert n == 3, n
    assert tot['CANARY'] == 2, tot
    assert rows == ['HIT dirty.txt CANARY=2'], rows
    print('T1 命中会亮           OK  files=%d hits=%d rows=%s' % (n, tot['CANARY'], rows))

    n2, tot2, rows2 = scan(d, [('CANARY', b'ABSENT_XX')])
    assert (n2, tot2['CANARY'], rows2) == (3, 0, []), (n2, tot2, rows2)
    print('T2 干净集合不假响      OK  files=%d hits=%d' % (n2, tot2['CANARY']))

    n3, tot3, rows3 = scan(d, [('CANARY', CANARY)], exclude_rel='dirty.txt')
    assert (n3, tot3['CANARY'], rows3) == (2, 0, []), (n3, tot3, rows3)
    print('T3 排除项真的被排掉    OK  files=%d hits=%d' % (n3, tot3['CANARY']))

    n4, tot4, rows4 = scan(d, [('A', CANARY), ('B', b'ABSENT_XX')])
    assert n4 == 3 and tot4 == {'A': 2, 'B': 0} and rows4[0].startswith('HIT dirty.txt A=2 B=0'), (n4, tot4, rows4)
    print('T4 两种口令同时计      OK  %s' % tot4)
    print('SELFTEST_PASS=4/4  (哨兵串，未触碰任何真口令)')
finally:
    shutil.rmtree(d, ignore_errors=False)
