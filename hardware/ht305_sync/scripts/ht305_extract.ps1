$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; $f="C:\Users\Administrator\Desktop\zizhao_sync_20260923_r43.tar.gz"; $t="C:\Users\Administrator\AppData\Local\Temp\zsynctest"; New-Item -ItemType Directory -Force -Path $t | Out-Null; tar.exe -xzf $f -C $t 2>&1 | Out-Null; Write-Output ("TAR_EXIT=" + $LASTEXITCODE); Write-Output ("EXTRACTED_FILES=" + (Get-ChildItem -Recurse -File $t | Measure-Object).Count); Write-Output ("TOPLEVEL=" + ((Get-ChildItem ($t + "\zizhao_20260923") | ForEach-Object { $_.Name }) -join "|")); $u = $t + "\zizhao_20260923\updates"; if (Test-Path $u) { Write-Output ("UPDATES_COUNT=" + (Get-ChildItem $u | Measure-Object).Count); Write-Output ("UPDATES_SAMPLE=" + ((Get-ChildItem $u | Select-Object -First 3 | ForEach-Object { $_.Name }) -join "|")) }'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null | Out-File -Encoding utf8 'C:\Users\david\AppData\Local\Temp\ht305_extract.txt'
Write-Output "DONE"
