$ErrorActionPreference = 'Stop'
# gen-14 版：由 `hardware/ht305_sync/scripts/chk_r55.ps1`（第 13 代）派生。改动三处，逐一点名：
#   ①$src/$p/$ev 三处名字换代 r55 -> r61，且 $src 指向 r61_sync/scripts、$ev 指向 **r61_sync/evidence**；
#   ②新装守卫：$src / $ev 规范化后含 `ht305_sync` 即 ABORT（同 sync_r61.py ②，封存目录不落派生字节日）；
#   ③继承不动的三条：读"实际会被执行的那只副本"（(63) 那族：校验脚本读一只还不存在的执行副本 ⇒ 读数全绿，
#     唯一线索 SCRIPT_LINES=0）、副本 md5 必须 == 原件、SCRIPT_LINES < 50 即 ABORT（哨兵），读数自带写进载体
#     （"记录取证那一步自己没落盘"那一族，(64)）。
$src = 'C:\Users\david\Documents\all_projects\自招学习\hardware\r61_sync\scripts\r61_upload.ps1'
$p   = 'C:\Users\david\AppData\Local\Temp\r61_upload.ps1'
$ev  = 'C:\Users\david\Documents\all_projects\自招学习\hardware\r61_sync\evidence\r61_parse_check.txt'
if (([IO.Path]::GetFullPath($src)) -like '*ht305_sync*') { 'ABORT: 被检件在封存归档目录 ' + $src; exit 1 }
if (([IO.Path]::GetFullPath($ev))  -like '*ht305_sync*') { 'ABORT: 载体落点在封存归档目录 ' + $ev; exit 1 }
if (-not (Test-Path -LiteralPath $src)) { 'ABORT: 本代脚本不存在 ' + $src; exit 1 }
if (Test-Path -LiteralPath $ev) { 'ABORT: 载体现已存在，不覆盖 ' + $ev; exit 1 }
Copy-Item -LiteralPath $src -Destination $p -Force
if (-not (Test-Path -LiteralPath $p)) { 'ABORT: 执行副本未落盘，后面的读数将全部无意义'; exit 1 }
$hs = (Get-FileHash -LiteralPath $src -Algorithm MD5).Hash
$hp = (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash
if ($hs -ne $hp) { 'ABORT: 副本与原件不一致 ' + $hs + ' vs ' + $hp; exit 1 }
$e = $null
[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $p), [ref]$e) | Out-Null
$nCopy = (Get-Content $p).Count
$nSrc  = (Get-Content $src).Count
$b3 = (Get-Content -Encoding Byte -TotalCount 3 $p) -join ','
$hasBom = ($b3 -eq '239,187,191')
$lines = @(
    ('CHK_AT=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('SRC=' + $src),
    ('FIRST3=' + $b3),
    ('UTF8_BOM=' + $hasBom),
    ('PARSE_ERRORS=' + $e.Count),
    ('REMOVE_ITEM_HITS=' + @(Select-String -Path $p -Pattern 'Remove-Item').Count),
    ('SCRIPT_LINES=' + $nCopy),
    ('SRC_LINES=' + $nSrc),
    ('MD5_BOTH=' + $hs)
)
if ($nCopy -ne $nSrc) { $lines += 'ABORT: 副本行数 != 原件行数'; $lines | Out-File -LiteralPath $ev -Encoding utf8; exit 1 }
if ($nCopy -lt 50) { $lines += 'ABORT: SCRIPT_LINES 太小（(63) 那族的哨兵：读到空文件时读数全绿）'; $lines | Out-File -LiteralPath $ev -Encoding utf8; exit 1 }
if (-not $hasBom) { $lines += 'ABORT: 含中文的 .ps1 必须 UTF-8 with BOM，否则 GBK 解码会吞掉下一整行（本机第三次复发）'; $lines | Out-File -LiteralPath $ev -Encoding utf8; exit 1 }
$lines += 'LINES_MATCH=SRC_EQ_COPY'
$lines += 'NOTE=本代实际执行的是归档那一只（直接 -File 仓库路径），这只 TEMP 副本只是"逐字节同孪生"的第二把尺 ⇒ md5 两侧同值即证明下面的解析结果描述的就是被执行的那只。'
$lines | Out-File -LiteralPath $ev -Encoding utf8
$lines
'OUT=' + $ev
