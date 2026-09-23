$ErrorActionPreference='Stop'
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'
& python $env:TEMP\cred_gate_recheck.py 'evidence\cred_gate_recheck.txt'
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE
Write-Output ("PY_EXIT=" + $rc)
