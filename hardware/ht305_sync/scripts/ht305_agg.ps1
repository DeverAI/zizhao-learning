$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$cmd = '$ProgressPreference="SilentlyContinue"; $d="C:\Users\Administrator\AppData\Local\Temp\zsynctest2\zizhao_20260923"; $digs=@(); foreach ($f in (Get-ChildItem -Recurse -File $d)) { $rel = $f.FullName.Substring($d.Length+1).Replace("\","/"); if ($rel -eq "SYNC_MANIFEST.txt") { continue }; $ms = New-Object IO.MemoryStream; $pb = [Text.Encoding]::UTF8.GetBytes($rel); $ms.Write($pb,0,$pb.Length); $fs = [IO.File]::OpenRead($f.FullName); $fs.CopyTo($ms); $fs.Close(); $ms.Position = 0; $hh = (Get-FileHash -InputStream $ms -Algorithm SHA256).Hash.ToLower(); $ms.Dispose(); $digs += $hh }; $digs = $digs | Sort-Object; $joined = $digs -join "`n"; $b2 = [Text.Encoding]::UTF8.GetBytes($joined); $m2 = New-Object IO.MemoryStream(,$b2); $agg = (Get-FileHash -InputStream $m2 -Algorithm SHA256).Hash.ToLower(); Write-Output ("REMOTE_FILES=" + $digs.Count); Write-Output ("REMOTE_AGGREGATE=" + $agg)'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>$null | Out-File -Encoding utf8 'C:\Users\david\AppData\Local\Temp\ht305_agg.txt'
Write-Output "AGG_DONE"
