$ErrorActionPreference='Stop'
# 提交前明文门（索引侧）驱动：口令只活在环境变量里，绝不出现在命令行、stdout 或本文件。
# 参数 1 = 输出相对本目录的路径（默认 ..\evidence\staged_cred_gate_<HHmmss>.txt），参数 2 = LABEL（本轮是正式跑还是阴性对照）。
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'
$stamp = Get-Date -Format 'HHmmss'
if ($args.Count -gt 0 -and $args[0]) { $out = Join-Path $PSScriptRoot $args[0] }
else { $out = Join-Path $PSScriptRoot ('..\evidence\staged_cred_gate_' + $stamp + '.txt') }
$label = if ($args.Count -gt 1) { $args[1] } else { 'index-' + $stamp }
& python (Join-Path $PSScriptRoot 'staged_cred_gate.py') $out $label
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE   # 环境变量，不是文件：本目录"Remove-Item 计数 = 0"这把尺子只管删文件动作
Write-Output ("OUT=" + (Split-Path -Leaf $out))
Write-Output ("PY_EXIT=" + $rc)
# 09-24 提交轮 #2：这两行打印必须落盘。上一轮（22:55:41）只留下了门自己那份输出，退出码只在控制台
# ⇒ README 里那句"驱动的打印也必须落盘"当时没有执行者（同 FreqErr 的"打印 != 裁决"一族）。
$pscopy = Join-Path $PSScriptRoot ('..\evidence\staged_cred_gate_' + $stamp + '_ps.txt')
if (Test-Path -LiteralPath $pscopy) { Write-Output ('ABORT: ps-copy exists, refuse to overwrite ' + $pscopy); exit 1 }
@(('DRIVER_PS_COPY ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')), ('LABEL=' + $label), ('OUT=' + (Split-Path -Leaf $out)), ('PY_EXIT=' + $rc)) | Set-Content -LiteralPath $pscopy -Encoding ascii
exit $rc
