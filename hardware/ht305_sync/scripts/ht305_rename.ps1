$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; $a="C:\Users\Administrator\Desktop\zizhao_sync_20260923_r43.tar.gz"; $b="C:\Users\Administrator\Desktop\SUPERSEDED-tar-cjk-mojibake_zizhao_sync_20260923_r43.tar.gz"; if ((Test-Path $a) -and -not (Test-Path $b)) { Rename-Item -LiteralPath $a -NewName "SUPERSEDED-tar-cjk-mojibake_zizhao_sync_20260923_r43.tar.gz"; Write-Output "RENAMED=1" } else { Write-Output ("RENAMED=0 SRC=" + (Test-Path $a) + " DST=" + (Test-Path $b)) }; Get-ChildItem "C:\Users\Administrator\Desktop" -Filter "zizhao*" | ForEach-Object { Write-Output ($_.Name + "|" + $_.Length) }; Get-ChildItem "C:\Users\Administrator\Desktop" -Filter "SUPERSEDED*" | ForEach-Object { Write-Output ($_.Name + "|" + $_.Length) }'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null | Out-File -Encoding utf8 'C:\Users\david\AppData\Local\Temp\ht305_rename.txt'
Write-Output "RENAME_STEP_DONE"
