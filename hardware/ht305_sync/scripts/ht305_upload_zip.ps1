$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$local = 'C:\Users\david\AppData\Local\Temp\zizhao_sync_20260923_r43.zip'
$remote = 'ht305:C:/Users/Administrator/Desktop/zizhao_sync_20260923_r43.zip'
& scp -o StrictHostKeyChecking=accept-new $local $remote 2>&1 | Out-Null
Write-Output ("SCP_EXIT=" + $LASTEXITCODE)
$cmd = '$ProgressPreference="SilentlyContinue"; $f="C:\Users\Administrator\Desktop\zizhao_sync_20260923_r43.zip"; Write-Output ("EXISTS=" + (Test-Path $f)); if (Test-Path $f) { $i=Get-Item $f; Write-Output ("REMOTE_SIZE=" + $i.Length); Write-Output ("REMOTE_MD5=" + (Get-FileHash $f -Algorithm MD5).Hash.ToLower()) }'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null | Out-File -Encoding utf8 'C:\Users\david\AppData\Local\Temp\ht305_zipchk.txt'
Write-Output "UPLOAD_STEP_DONE"
