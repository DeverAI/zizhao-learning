$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; Write-Output ("TAR=" + (Get-Command tar.exe -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })); Write-Output ("HASHTYPE=" + (Get-Command Get-FileHash -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })); $d=[Environment]::GetFolderPath("Desktop"); Write-Output ("EXIST_zipsync=" + (Test-Path ($d + "\zizhao_sync_20260923_r43.tar.gz"))); Write-Output ("FREE_MB=" + [math]::Round((Get-PSDrive ($d.Substring(0,1))).Free/1MB,1))'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null
Write-Output ("EXIT=" + $LASTEXITCODE)
