$ErrorActionPreference = 'Stop'
# gen-12 was derived by derive_r54.py into the archive; check the copy that will actually be executed,
# and prove it is byte-identical to the archive original (otherwise the parse result describes a different file).
$src = 'C:\Users\david\Documents\all_projects\自招学习\hardware\ht305_sync\scripts\r54_upload.ps1'
$p   = 'C:\Users\david\AppData\Local\Temp\r54_upload.ps1'
if (-not (Test-Path -LiteralPath $src)) { 'ABORT: 归档原脚本不存在 ' + $src; exit 1 }
Copy-Item -LiteralPath $src -Destination $p -Force
if (-not (Test-Path -LiteralPath $p)) { 'ABORT: 执行副本未落盘，后面的读数将全部无意义'; exit 1 }
$hs = (Get-FileHash -LiteralPath $src -Algorithm MD5).Hash
$hp = (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash
if ($hs -ne $hp) { 'ABORT: 副本与原件不一致 ' + $hs + ' vs ' + $hp; exit 1 }
$e = $null
[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $p), [ref]$e) | Out-Null
'FIRST3=' + ((Get-Content -Encoding Byte -TotalCount 3 $p) -join ',')
'PARSE_ERRORS=' + $e.Count
'REMOVE_ITEM_HITS=' + @(Select-String -Path $p -Pattern 'Remove-Item').Count
'SCRIPT_LINES=' + (Get-Content $p).Count
'MD5_BOTH=' + $hs
