$ErrorActionPreference = 'Stop'
# gen-13 版：由 `scripts/chk_r54.ps1`（第 12 代）派生。改动三处，逐一点名：
#   ①$src/$p 换代 r54 -> r55；
#   ②**读数当场写进仓库 `evidence/r55_parse_check.txt`**（原第 1~11 代是"脚本只打到 stdout，由人来捕获"
#     ⇒ "记录取证那一步自己没落盘"那一族的入口；本代起这只脚本自带载体，捕获那一步不再是独立动作）；
#     配套：目标已存在即 ABORT，不覆盖。
#   ③头部那句"check the copy that will actually be executed"原样保留（第 12 代抓到的 (63) 同族缺陷：
#     校验脚本读一只还不存在的执行副本 ⇒ 读数全绿，唯一线索 SCRIPT_LINES=0 ⇒ 下面 SCRIPT_LINES 那行仍在，且新增 == $src 行数的互核）。
$src = 'C:\Users\david\Documents\all_projects\自招学习\hardware\ht305_sync\scripts\r55_upload.ps1'
$p   = 'C:\Users\david\AppData\Local\Temp\r55_upload.ps1'
$ev  = 'C:\Users\david\Documents\all_projects\自招学习\hardware\ht305_sync\evidence\r55_parse_check.txt'
if (-not (Test-Path -LiteralPath $src)) { 'ABORT: 归档原脚本不存在 ' + $src; exit 1 }
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
$lines = @(
    ('CHK_AT=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('SRC=' + $src),
    ('FIRST3=' + ((Get-Content -Encoding Byte -TotalCount 3 $p) -join ',')),
    ('PARSE_ERRORS=' + $e.Count),
    ('REMOVE_ITEM_HITS=' + @(Select-String -Path $p -Pattern 'Remove-Item').Count),
    ('SCRIPT_LINES=' + $nCopy),
    ('SRC_LINES=' + $nSrc),
    ('MD5_BOTH=' + $hs)
)
if ($nCopy -ne $nSrc) { $lines += 'ABORT: 副本行数 != 原件行数'; $lines | Out-File -LiteralPath $ev -Encoding utf8; exit 1 }
if ($nCopy -lt 50) { $lines += 'ABORT: SCRIPT_LINES 太小（(63) 那族的哨兵：读到空文件时读数全绿）'; $lines | Out-File -LiteralPath $ev -Encoding utf8; exit 1 }
$lines += 'LINES_MATCH=SRC_EQ_COPY'
$lines += 'NOTE=本代**实际执行的是归档那一只**（12:25:29 直接 `-File` 归档路径），这只脚本的 TEMP 副本只是"逐字节同孪生"的第二把尺 ⇒ md5 两侧同值即证明下面的解析结果描述的就是被执行的那只。'
$lines | Out-File -LiteralPath $ev -Encoding utf8
$lines
'OUT=' + $ev
