$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$tmp = 'C:\Users\david\AppData\Local\Temp'
$top = 'zizhao_20260923_r45final'
$local = Join-Path $tmp ($top + '.zip')
$remoteZip = 'C:/Users/Administrator/Desktop/zizhao_20260923_r45final.zip'
$log = Join-Path $tmp 'r45_run_log.txt'

# Every stamp below is written INTO the evidence file, same batch as the reading (FreqErr ht305 第 8 条).
function Stamp($path, $tag) { Add-Content -LiteralPath $path -Encoding UTF8 -Value ($tag + ' ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) }
function W($m) { $line = (Get-Date -Format 'HH:mm:ss') + "`t" + $m; Write-Output $line; Add-Content -LiteralPath $log -Value $line -Encoding UTF8 }
Set-Content -LiteralPath $log -Value ('START ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -Encoding UTF8
W ('TOP=' + $top)
if (-not (Test-Path -LiteralPath $local)) { W ('ABORT: 本机包不存在 ' + $local); exit 1 }
W ('LOCAL_SIZE=' + (Get-Item -LiteralPath $local).Length)

# ---- 1) read-only probe: never overwrite an existing artifact on the shared server ----
$probe = @'
$ErrorActionPreference="Continue";
$p="C:\Users\Administrator\Desktop\zizhao_20260923_r45final.zip";
Write-Output ("TARGET_EXISTS="+[bool](Test-Path -LiteralPath $p));
Get-ChildItem "C:\Users\Administrator\Desktop" -File | ForEach-Object { Write-Output ("DESKTOP`t"+$_.Name+"`t"+$_.Length) }
'@
# literal-in-here-string vs $top must agree, else the three paths drift apart silently (r44 缺陷的机器化版本)
if ($probe -notmatch [regex]::Escape($top)) { W 'ABORT: 探测段字面路径与 $top 不一致'; exit 1 }
if ($local -notmatch [regex]::Escape($top)) { W 'ABORT: 本机包名与 $top 不一致'; exit 1 }
"evidence header" | Out-File -Encoding utf8 "$tmp\r45_probe.txt" ; Stamp "$tmp\r45_probe.txt" 'PROBE_AT'
$pb = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $pb" 2>&1 |
    Out-File -Append -Encoding utf8 "$tmp\r45_probe.txt"
if (Select-String -Path "$tmp\r45_probe.txt" -Pattern 'TARGET_EXISTS=True' -Quiet) {
    W 'ABORT: 目标文件已存在，不覆盖'; exit 1
}
W 'PROBE_OK'

# ---- 2) upload ----
"evidence header" | Out-File -Encoding utf8 "$tmp\r45_scp_err.txt" ; Stamp "$tmp\r45_scp_err.txt" 'SCP_AT'
& scp -o StrictHostKeyChecking=accept-new $local "ht305:$remoteZip" 2>&1 |
    Out-File -Append -Encoding utf8 "$tmp\r45_scp_err.txt"
Add-Content -LiteralPath "$tmp\r45_scp_err.txt" -Value ('SCP_EXIT=' + $LASTEXITCODE) -Encoding UTF8
W ('SCP_EXIT=' + $LASTEXITCODE)

# ---- 3) verify: extract into a FRESH dir (nothing is deleted), then aggregate ----
# Remote command is loaded whole from a single-quoted here-string -- no manual concatenation (FreqErr ht305 第 7 条).
$cmd = @'
$ProgressPreference="SilentlyContinue";
$z="C:\Users\Administrator\Desktop\zizhao_20260923_r45final.zip";
$root="C:\Users\Administrator\AppData\Local\Temp\zsynctest5";
$d="C:\Users\Administrator\AppData\Local\Temp\zsynctest5\zizhao_20260923_r45final";
Write-Output ("REMOTE_AT="+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'));
if (Test-Path -LiteralPath $root) { Write-Output "ABORT: 解包根已存在，不删不改"; exit 1 }
if (Test-Path -LiteralPath $d) { Write-Output "ABORT: 解包目录已存在，不删不改"; exit 1 }
New-Item -ItemType Directory -Force -Path $root | Out-Null;
$i=Get-Item -LiteralPath $z;
Write-Output ("REMOTE_ZIP_SIZE="+$i.Length);
Write-Output ("REMOTE_ZIP_MD5="+((Get-FileHash -LiteralPath $z -Algorithm MD5).Hash.ToLower()));
Expand-Archive -LiteralPath $z -DestinationPath $root;
Write-Output ("EXTRACT_OK="+$?);
$digs=@(); $bytes=0; $bad=@(); $names=@();
foreach ($f in (Get-ChildItem -LiteralPath $d -Recurse -File)) {
  $rel=$f.FullName.Substring($d.Length+1).Replace("\","/");
  if ($rel -eq "SYNC_MANIFEST.txt") { continue }
  $bytes+=$f.Length;
  $names+=$rel;
  if ($rel -match "\.log$|\.bin$|\.elf$|\.map$|nvs\.csv$|^backups/") { $bad+=$rel }
  $ms=New-Object IO.MemoryStream;
  $pb=[Text.Encoding]::UTF8.GetBytes($rel); $ms.Write($pb,0,$pb.Length);
  $fs=[IO.File]::OpenRead($f.FullName); $fs.CopyTo($ms); $fs.Close(); $ms.Position=0;
  $digs+=(Get-FileHash -InputStream $ms -Algorithm SHA256).Hash.ToLower(); $ms.Dispose()
}
$sorted=$digs | Sort-Object;
$agg=(Get-FileHash -InputStream (New-Object IO.MemoryStream(,[Text.Encoding]::UTF8.GetBytes(($sorted -join "`n")))) -Algorithm SHA256).Hash.ToLower();
Write-Output ("REMOTE_FILES="+$digs.Count);
Write-Output ("REMOTE_BYTES="+$bytes);
Write-Output ("REMOTE_FORBIDDEN="+$bad.Count);
Write-Output ("REMOTE_AGGREGATE="+$agg);
Write-Output ("REMOTE_DONE_AT="+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'));
Write-Output "REMOTE_NAMES_BEGIN"; ($names | Sort-Object) | ForEach-Object { Write-Output $_ }; Write-Output "REMOTE_NAMES_END"
'@
if ($cmd -notmatch [regex]::Escape($top)) { W 'ABORT: 校验段字面路径与 $top 不一致'; exit 1 }
W '---- remote command (for the record) ----'
W $cmd
W '-----------------------------------------'
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
"evidence header" | Out-File -Encoding utf8 "$tmp\r45_verify.txt" ; Stamp "$tmp\r45_verify.txt" 'VERIFY_BEGIN_AT'
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>&1 |
    Out-File -Append -Encoding utf8 "$tmp\r45_verify.txt"
Stamp "$tmp\r45_verify.txt" 'VERIFY_END_AT'
W 'VERIFY_FLUSHED'
