$ErrorActionPreference='Stop'
# ASCII-only driver for the R61 (commit round 9) positive control.
# Arg 1 = this round's gate carrier file name, forwarded to python as argv[1]; see pw_pos_control_r61.py for the arms
# and the carrier it writes. The SSH password is decoded from DPAPI into an env var only: never printed, never placed
# on a command line. The python side resolves the repo path itself and writes the carrier next to the gate file
# (PS must not touch the non-ASCII repo path). Derived from ht305_sync/scripts/run_pos_control_r53b.ps1; the one
# delta is that the target script is read from THIS repo dir instead of %TEMP% (a forensic script that only lives in
# %TEMP% disappears on the next machine -- see FreqErr "archive the carrier").
$credFile = Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'
$str = [System.IO.File]::ReadAllText($credFile, [System.Text.UTF8Encoding]::new($false)).Trim()
if ($str.Length -gt 0 -and $str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
if ($plain.Length -lt 4) { Write-Output 'ABORT: decoded ssh credential too short, refusing'; exit 1 }
$env:HT305_TMP_FOR_GATE = $plain
$env:PYTHONIOENCODING = 'utf-8'
$py = Join-Path $PSScriptRoot 'pw_pos_control_r61.py'
if (-not (Test-Path -LiteralPath $py)) { Write-Output 'ABORT: positive-control script missing'; exit 1 }
& python $py $args[0]
$rc = $LASTEXITCODE
Remove-Item Env:HT305_TMP_FOR_GATE
Write-Output ('PY_EXIT=' + $rc)
exit $rc
