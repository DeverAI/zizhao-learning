$ErrorActionPreference='Stop'
# R61b 提交轮 #10 的索引侧明文门驱动。派生自 hardware/r61_sync/gate/run_staged_cred_gate_r61.ps1，改动两处：
#   ① $evdir 随 $PSScriptRoot 自然落到 r61b_sync/evidence（本只放在自己的 gate/ 下）；
#   ② args[0] 原来相对 $PSScriptRoot 解析（= gate/ 目录本身），本轮改成相对 $evdir ⇒ 门输出恒在取证目录，
#      不再需要调用方传 `..\evidence\...` 这种带分隔符的名字（带分隔符就能把落点指走，本遍另加一道 ABORT）。派生自 `hardware/ht305_sync/gate/run_staged_cred_gate.ps1`，
# 只改两处、且两处都是"不写进封存归档目录"这一条硬约束的执行者：
#   ① 门脚本本身沿用 ht305_sync 里那一只（单一权威源，不复制第二份门；运行主脚本不产出 .pyc，不会往封存目录落派生字节）；
#   ② 驱动的 ps-copy 原来硬编码 `..\evidence\` = `hardware/ht305_sync/evidence/`（那是 gen 24 之后的第 25 只派生件 ⇒
#      会让 `verify_manifest.py` 报 MANIFEST_STALE，而这正是"检查动作污染被检查物"那一族）。本遍落到 r61_sync/evidence/。
# 口令两侧都只活在环境变量里：绝不出现在命令行、stdout、本文件或任何落盘件。
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
if ($plain.Length -lt 4) { Write-Output 'ABORT: SSH 口令解出来过短，不跑门'; exit 1 }
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'

$stamp = Get-Date -Format 'HHmmss'
$gate = Join-Path $PSScriptRoot '..\..\ht305_sync\gate\staged_cred_gate.py'
if (-not (Test-Path -LiteralPath $gate)) { Write-Output 'ABORT: 门脚本不存在'; exit 1 }
$evdir = Join-Path $PSScriptRoot '..\evidence'
if (-not (Test-Path -LiteralPath $evdir)) { Write-Output ('ABORT: 取证目录不存在 ' + $evdir); exit 1 }

$leaf = if ($args.Count -gt 0 -and $args[0]) { $args[0] } else { ('staged_cred_gate_' + $stamp + '.txt') }
if ($leaf -match '[\\/]') { Write-Output ('ABORT: args[0] 带路径分隔符，拒绝把它拼进取证目录：' + $leaf); exit 1 }
$out = Join-Path $evdir $leaf
$label = if ($args.Count -gt 1) { $args[1] } else { 'index-' + $stamp }

# 只判"路径字符串里有没有 ht305_sync"太脆（相对路径可以绕）；这里先规范化再比。
$outFull = [System.IO.Path]::GetFullPath($out)
if ($outFull -like '*ht305_sync*') { Write-Output ('ABORT: 门输出落点指进封存归档目录 ' + $outFull); exit 1 }
if (Test-Path -LiteralPath $outFull) { Write-Output ('ABORT: 取证已存在，不覆盖 ' + $outFull); exit 1 }

& python $gate $outFull $label
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE
Write-Output ("OUT=" + (Split-Path -Leaf $outFull))
Write-Output ("PY_EXIT=" + $rc)
$pscopy = Join-Path $evdir ('staged_cred_gate_' + $stamp + '_ps.txt')
if (Test-Path -LiteralPath $pscopy) { Write-Output ('ABORT: ps-copy exists, refuse to overwrite ' + $pscopy); exit 1 }
@(('DRIVER_PS_COPY ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')), ('LABEL=' + $label), ('OUT=' + (Split-Path -Leaf $outFull)), ('PY_EXIT=' + $rc)) | Set-Content -LiteralPath $pscopy -Encoding ascii
Write-Output ('PS_COPY=' + (Split-Path -Leaf $pscopy))
exit $rc
