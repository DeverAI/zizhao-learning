$ErrorActionPreference='Stop'
# ASCII-only driver for the R53b (commit round 8) positive control.
# Args: 1 = this round's gate carrier name, forwarded to the python side as argv[1]. See pw_pos_control_r53b.py for the arms and the
# carrier it writes. The SSH password is decoded from DPAPI into an env var only: never printed,
# never placed on a command line. The python side resolves the repo path itself and writes the
# carrier into hardware/ht305_sync/evidence/ (PS must not touch the non-ASCII repo path).
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'
& python (Join-Path $env:TEMP 'pw_pos_control_r53b.py') $args[0]
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE
Write-Output ('PY_EXIT=' + $rc)
exit $rc
