$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$tmp = 'C:\Users\david\AppData\Local\Temp'
$top = 'zizhao_20260923_r44final'
$local = "$tmp\$top.zip"

# 1) upload
& scp -o StrictHostKeyChecking=accept-new $local "ht305:C:/Users/Administrator/Desktop/$top.zip" 2>&1 |
    Out-File -Encoding utf8 "$tmp\r44_scp_err.txt"
Write-Output ("SCP_EXIT=" + $LASTEXITCODE)

# 2) verify landing + extract into a fresh dir + aggregate (same definition as local)
$cmd = '$ProgressPreference="SilentlyContinue"; $top="zizhao_20260923_r44final";' +
  ' $z="C:\Users\Administrator\Desktop\"+$top+".zip"; $d="C:\Users\Administrator\AppData\Local\Temp\zsynctest3\";$top;' +
  ' if (Test-Path $d) { Remove-Item -Recurse -Force $d };' +
  ' $i=Get-Item $z; Write-Output ("REMOTE_ZIP_SIZE="+$i.Length);' +
  ' Write-Output ("REMOTE_ZIP_MD5="+((Get-FileHash $z -Algorithm MD5).Hash.ToLower()));' +
  ' Expand-Archive -LiteralPath $z -DestinationPath "C:\Users\Administrator\AppData\Local\Temp\zsynctest3" -Force;' +
  ' Write-Output ("EXTRACT_EXIT="+$?);' +
  ' $digs=@(); $bytes=0; $bad=@();' +
  ' foreach ($f in (Get-ChildItem -Recurse -File $d)) {' +
  '   $rel=$f.FullName.Substring($d.Length+1).Replace("\","/");' +
  '   if ($rel -eq "SYNC_MANIFEST.txt") { continue };' +
  '   $bytes+=$f.Length;' +
  '   if ($rel -match "\.log$|\.bin$|\.elf$|\.map$|nvs\.csv$|^backups/") { $bad+=$rel };' +
  '   $ms=New-Object IO.MemoryStream; $pb=[Text.Encoding]::UTF8.GetBytes($rel); $ms.Write($pb,0,$pb.Length);' +
  '   $fs=[IO.File]::OpenRead($f.FullName); $fs.CopyTo($ms); $fs.Close(); $ms.Position=0;' +
  '   $digs+=(Get-FileHash -InputStream $ms -Algorithm SHA256).Hash.ToLower(); $ms.Dispose() };' +
  ' $agg=(Get-FileHash -InputStream (New-Object IO.MemoryStream(,[Text.Encoding]::UTF8.GetBytes((($digs|Sort-Object) -join "`n")))) -Algorithm SHA256).Hash.ToLower();' +
  ' Write-Output ("REMOTE_FILES="+$digs.Count); Write-Output ("REMOTE_BYTES="+$bytes);' +
  ' Write-Output ("REMOTE_FORBIDDEN="+$bad.Count); Write-Output ("REMOTE_AGGREGATE="+$agg)'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>&1 |
    Out-File -Encoding utf8 "$tmp\r44_verify.txt"
Write-Output "VERIFY_STEP_DONE"
