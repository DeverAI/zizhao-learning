$ErrorActionPreference = 'Stop'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; Write-Output ("DESKTOP=" + [Environment]::GetFolderPath("Desktop")); Get-ChildItem ([Environment]::GetFolderPath("Desktop")) | ForEach-Object { Write-Output ($_.Name + "|" + $_.PSIsContainer + "|" + $_.Length + "|" + $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")) }'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null
Write-Output ("EXIT=" + $LASTEXITCODE)
