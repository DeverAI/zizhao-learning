$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$tmp = 'C:\Users\david\AppData\Local\Temp'

# Literal here-string: no local expansion, no quoting-ambiguity class of bug.
$cmd = @'
$ProgressPreference = "SilentlyContinue"
$top = "zizhao_20260923_r44final"
$z   = "C:\Users\Administrator\Desktop\" + $top + ".zip"
$t   = "C:\Users\Administrator\AppData\Local\Temp\zsynctest4"
$d   = $t + "\" + $top
if (Test-Path $t) { Remove-Item -Recurse -Force $t }
New-Item -ItemType Directory -Force -Path $t | Out-Null
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
Write-Output ("EXTRACT_OK=" + (Test-Path $d))
$files = @(Get-ChildItem -Recurse -File $d)
Write-Output ("RAW_FILES=" + $files.Count)
$kept = @($files | Where-Object { $_.FullName.Substring($d.Length + 1).Replace("\", "/") -ne "SYNC_MANIFEST.txt" })
$digs = @(); $names = @(); $bytes = 0; $bad = @()
foreach ($f in $kept) {
  $rel = $f.FullName.Substring($d.Length + 1).Replace("\", "/")
  $names += $rel
  $bytes += $f.Length
  if ($rel -match "\.log$|\.bin$|\.elf$|\.map$|nvs\.csv$|^backups/") { $bad += $rel }
  $ms = New-Object IO.MemoryStream
  $pb = [Text.Encoding]::UTF8.GetBytes($rel)
  $ms.Write($pb, 0, $pb.Length)
  $fs = [IO.File]::OpenRead($f.FullName); $fs.CopyTo($ms); $fs.Close()
  $ms.Position = 0
  $digs += (Get-FileHash -InputStream $ms -Algorithm SHA256).Hash.ToLower()
  $ms.Dispose()
}
$agg = (Get-FileHash -InputStream (New-Object IO.MemoryStream(, [Text.Encoding]::UTF8.GetBytes(($digs | Sort-Object) -join "`n"))) -Algorithm SHA256).Hash.ToLower()
Write-Output ("REMOTE_FILES=" + $digs.Count)
Write-Output ("REMOTE_BYTES=" + $bytes)
Write-Output ("REMOTE_FORBIDDEN=" + $bad.Count)
Write-Output ("REMOTE_AGGREGATE=" + $agg)
Write-Output "REMOTE_NAMES_BEGIN"
($names | Sort-Object) | ForEach-Object { Write-Output $_ }
Write-Output "REMOTE_NAMES_END"
'@

$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>&1 |
    Out-File -Encoding utf8 "$tmp\r44_verify2.txt"
Write-Output "VERIFY2_DONE"
