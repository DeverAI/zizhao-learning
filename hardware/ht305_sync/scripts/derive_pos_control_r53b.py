# -*- coding: utf-8 -*-
"""派生第八次提交轮的阳性对照两只（py + ps1）：本体逐字来自 r52 那两只，只改头部口径行。"""
import hashlib
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
T = r'C:/Users/david/AppData/Local/Temp'
PY_SRC = T + '/pw_pos_control_r52.py'
PY_DST = T + '/pw_pos_control_r53b.py'
PS_SRC = T + '/run_pos_control_r52.ps1'
PS_DST = T + '/run_pos_control_r53b.ps1'

for p in (PY_SRC, PS_SRC):
    assert io.open(p, encoding='utf-8').read(), 'ABORT: 源为空 ' + p
assert not re.search(r'\bR53b?\b', io.open(PS_SRC, encoding='utf-8').read()), 'ABORT: PS 源已带本轮标记'

# ---- python 侧：以 import os 为界，头部注释重写、本体逐字保留 ----
raw = open(PY_SRC, 'rb').read()
text = raw.decode('utf-8')
marker = 'import os'
i = text.index('\n' + marker + '\n')
head_old, body_old = text[:i + 1], text[i + 1:]
assert body_old.startswith(marker + '\n'), 'ABORT: 本体切点不对'

HEAD = '\n'.join([
    '# 第八次提交轮（09-24 10:2x）索引门的**阳性对照**，两条口令各一路。',
    '# 本只 = %TEMP%\\pw_pos_control_r52.py 的逐字派生：以 `import os` 为界，'
    '# 头部注释重写、**本体自该行之后的每一个字节与上一轮那只逐字相同**（本脚本以 md5 断言，见落盘前打印）。',
    '# 口径沿用上一轮，一字未动：门载体名走 argv[1]（不硬编码，防拿上一代的门核这一代）、SSH 只在内存造',
    '# 合成样本（仓库里没有已知脏样本正是它干净的原因，故它证的是「传参通路 + bytes.count 语义没断」）、',
    '# 与门载体逐字段互核、rc=0 蕴含载体已写出。两条口令都只在进程内取，一次都不打印内容、不进命令文本。',
    '',
])
out = (HEAD + body_old).encode('utf-8')

def md5(b):
    return hashlib.md5(b).hexdigest()

print('PY_SRC=%s bytes=%d md5=%s' % (PY_SRC, len(raw), md5(raw)))
print('PY_BODY bytes=%d md5=%s（派生前后必须逐字相同）' % (len(body_old.encode()), md5(body_old.encode())))
assert out == HEAD.encode('utf-8') + body_old.encode('utf-8')
assert out.endswith(b'\n')

# ---- PS 侧：只改本轮名与轮次号，且必须保持 ASCII-only ----
ps = open(PS_SRC, 'rb').read().decode('utf-8')
assert max(ord(c) for c in ps) < 128, 'ABORT: PS 源非 ASCII'
pairs = [
    ('ASCII-only driver for the R52 (commit round 7) positive control.',
     'ASCII-only driver for the R53b (commit round 8) positive control.'),
    ('pw_pos_control_r52.py', 'pw_pos_control_r53b.py'),
]
ps2 = ps
for old, new in pairs:
    assert ps2.count(old) >= 1, 'ABORT: 锚点不在 PS 源里 ' + old
    ps2 = ps2.replace(old, new)
assert 'pw_pos_control_r52.py' not in ps2, 'ABORT: PS 仍指向上轮脚本'
assert max(ord(c) for c in ps2) < 128, 'ABORT: PS 派生后非 ASCII'
ps_out = ps2.encode('ascii')

# 落地：只新建，绝不覆盖
for p in (PY_DST, PS_DST):
    assert not __import__('os').path.exists(p), 'refuse to overwrite ' + p
open(PY_DST, 'wb').write(out)
open(PS_DST, 'wb').write(ps_out)
print('WROTE %s bytes=%d md5=%s' % (PY_DST, len(out), md5(out)))
print('WROTE %s bytes=%d md5=%s' % (PS_DST, len(ps_out), md5(ps_out)))
