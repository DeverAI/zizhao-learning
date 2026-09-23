$ErrorActionPreference='Stop'
# 09-23 11:5x 订正：原先跑的是 `$env:TEMP\cred_gate_recheck.py`（归档外的一份副本）⇒
# 归档里那只 .ps1 从来没有真正的执行者。现在直接调同目录的 .py，链路上不再有"仓库外的原件"。
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'
# 参数 1 = 载荷打包截止时刻（HH:MM:SS），门把它写进输出头部当快照口径钉。
$cut = if ($args.Count -gt 0) { $args[0] } else { '' }
# 输出**带时刻**、不原地覆写：上一代的字节必须留在仓库里，否则被引用的那一代永远不可复核（R45 复查 P1-3）。
$out = Join-Path $PSScriptRoot ('..\evidence\cred_gate_recheck_' + (Get-Date -Format 'HHmmss') + '.txt')
& python (Join-Path $PSScriptRoot 'cred_gate_recheck.py') $out $cut
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE   # 环境变量，不是文件：本目录"Remove-Item 计数 = 0"这把尺子只管 `r45_upload.ps1` 那类**删文件**动作
Write-Output ("OUT=" + (Split-Path -Leaf $out))
Write-Output ("PY_EXIT=" + $rc)
