$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; $f="C:\Users\Administrator\Desktop\zizhao_sync_20260923_r43.zip"; $t="C:\Users\Administrator\AppData\Local\Temp\zsynctest2"; if (Test-Path $t) { Remove-Item -Recurse -Force $t }; New-Item -ItemType Directory -Force -Path $t | Out-Null; Expand-Archive -LiteralPath $f -DestinationPath $t -Force; $d = $t + "\zizhao_20260923"; $files = Get-ChildItem -Recurse -File $d | Where-Object { $_.Name -ne "SYNC_MANIFEST.txt" }; $sum = ($files | Measure-Object -Property Length -Sum).Sum; $rel = $files | ForEach-Object { $_.FullName.Substring($d.Length+1).Replace("\","/") }; $joined = ($rel | Sort-Object) -join "`n"; $bytes = [Text.Encoding]::UTF8.GetBytes($joined); $ms = New-Object IO.MemoryStream(,$bytes); $h = (Get-FileHash -InputStream $ms -Algorithm SHA256).Hash.ToLower(); Write-Output ("COUNT=" + $files.Count); Write-Output ("BYTES=" + $sum); Write-Output ("PATHSHA256=" + $h); Write-Output ("MANIFEST_LINES=" + ((Get-Content ($d + "\SYNC_MANIFEST.txt")).Count)); Write-Output ("NAMESHA16=" + $h.Substring(0,16))'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null | Out-File -Encoding utf8 'C:\Users\david\AppData\Local\Temp\ht305_extract2.txt'
Write-Output "EXTRACT_STEP_DONE"
