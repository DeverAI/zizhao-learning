$ErrorActionPreference = 'Stop'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$local = 'C:\Users\david\AppData\Local\Temp\zizhao_sync_20260923_r43.tar.gz'
$remote = 'C:/Users/Administrator/Desktop/zizhao_sync_20260923_r43.tar.gz'
& scp -o StrictHostKeyChecking=accept-new $local ("ht305:" + $remote) 2>$null
Write-Output ("SCP_EXIT=" + $LASTEXITCODE)

$cmd = '$ProgressPreference="SilentlyContinue"; $f="C:\Users\Administrator\Desktop\zizhao_sync_20260923_r43.tar.gz"; $t="C:\Users\Administrator\AppData\Local\Temp\zsynctest"; if (Test-Path $f) { $i=Get-Item $f; Write-Output ("REMOTE_SIZE=" + $i.Length); Write-Output ("REMOTE_MD5=" + (Get-FileHash $f -Algorithm MD5).Hash.ToLower()); New-Item -ItemType Directory -Force -Path $t | Out-Null; tar.exe -xzf $f -C $t; Write-Output ("TAR_EXIT=" + $LASTEXITCODE); Write-Output ("EXTRACTED_FILES=" + (Get-ChildItem -Recurse -File $t | Measure-Object).Count); Write-Output ("TOPLEVEL=" + ((Get-ChildItem ($t + "\zizhao_20260923") | ForEach-Object { $_.Name }) -join ",")) } else { Write-Output "REMOTE_MISSING" }'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null
Write-Output ("SSH_EXIT=" + $LASTEXITCODE)
