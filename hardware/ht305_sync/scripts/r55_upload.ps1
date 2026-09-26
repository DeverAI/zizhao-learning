$ErrorActionPreference = 'Continue'
$env:SSH_ASKPASS = 'C:\Users\david\.ssh\_askpass_ht305.cmd'
$env:SSH_ASKPASS_REQUIRE = 'force'
$env:DISPLAY = ':0'
$tmp = 'C:\Users\david\AppData\Local\Temp'
$ev = 'C:\Users\david\Documents\all_projects\自招学习\hardware\ht305_sync\evidence'
$top = 'zizhao_20260924_r55final'
$local = Join-Path $tmp ($top + '.zip')
$remoteZip = 'C:/Users/Administrator/Desktop/zizhao_20260924_r55final.zip'
$log = Join-Path $ev 'r55_run_log.txt'

# 第 13 代派生自 `scripts/r54_upload.ps1`（第 12 代）。改动三处，逐一点名：
#   ①$top / $remoteZip 换代 r54 -> r55，远端解包根 zsynctest14 -> zsynctest15（每代一个新根，绝不复用、绝不删旧的）；
#   ②取证四只（run_log / probe / scp_err / verify）**直接写进仓库 evidence/**，不再落 %TEMP%
#     ——与 sync_r55.py 同一动因（排查记录 §38.18 缺陷一：补拷那一步没有执行者）。
#     配套 NewEv：目标已存在即 ABORT，不覆盖（与"本机包已存在即 ABORT"同一条红线）。
#   ③其余口径（只读探测先行 / 不覆盖既有产物 / 解包进新根后逐只哈希 / 远端命令整段单引号 here-string）原样继承。

# Every stamp below is written INTO the evidence file, same batch as the reading (FreqErr ht305 第 8 条).
function Stamp($path, $tag) { Add-Content -LiteralPath $path -Encoding UTF8 -Value ($tag + ' ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) }
function W($m) { $line = (Get-Date -Format 'HH:mm:ss') + "`t" + $m; Write-Output $line; Add-Content -LiteralPath $log -Value $line -Encoding UTF8 }
function NewEv($path, $tag) {
    if (Test-Path -LiteralPath $path) { Write-Output ('ABORT: 取证件已存在，不覆盖 ' + $path); exit 1 }
    'evidence header' | Out-File -LiteralPath $path -Encoding utf8
    Stamp $path $tag
}
if (-not (Test-Path -LiteralPath $ev)) { Write-Output ('ABORT: 取证目录不存在 ' + $ev); exit 1 }
NewEv $log 'START'
W ('TOP=' + $top)
if (-not (Test-Path -LiteralPath $local)) { W ('ABORT: 本机包不存在 ' + $local); exit 1 }
W ('LOCAL_SIZE=' + (Get-Item -LiteralPath $local).Length)

# ---- 1) read-only probe: never overwrite an existing artifact on the shared server ----
$probe = @'
$ErrorActionPreference="Continue";
$p="C:\Users\Administrator\Desktop\zizhao_20260924_r55final.zip";
Write-Output ("TARGET_EXISTS="+[bool](Test-Path -LiteralPath $p));
Get-ChildItem "C:\Users\Administrator\Desktop" -File | ForEach-Object { Write-Output ("DESKTOP`t"+$_.Name+"`t"+$_.Length) }
'@
# literal-in-here-string vs $top must agree, else the three paths drift apart silently (r44 缺陷的机器化版本)
if ($probe -notmatch [regex]::Escape($top)) { W 'ABORT: 探测段字面路径与 $top 不一致'; exit 1 }
if ($local -notmatch [regex]::Escape($top)) { W 'ABORT: 本机包名与 $top 不一致'; exit 1 }
NewEv "$ev\r55_probe.txt" 'PROBE_AT'
$pb = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $pb" 2>&1 |
    Out-File -Append -Encoding utf8 "$ev\r55_probe.txt"
if (Select-String -Path "$ev\r55_probe.txt" -Pattern 'TARGET_EXISTS=True' -Quiet) {
    W 'ABORT: 目标文件已存在，不覆盖'; exit 1
}
W 'PROBE_OK'

# ---- 2) upload ----
NewEv "$ev\r55_scp_err.txt" 'SCP_AT'
& scp -o StrictHostKeyChecking=accept-new $local "ht305:$remoteZip" 2>&1 |
    Out-File -Append -Encoding utf8 "$ev\r55_scp_err.txt"
Add-Content -LiteralPath "$ev\r55_scp_err.txt" -Value ('SCP_EXIT=' + $LASTEXITCODE) -Encoding UTF8
W ('SCP_EXIT=' + $LASTEXITCODE)

# ---- 3) verify: extract into a FRESH dir (nothing is deleted), then aggregate ----
# Remote command is loaded whole from a single-quoted here-string -- no manual concatenation (FreqErr ht305 第 7 条).
$cmd = @'
$ProgressPreference="SilentlyContinue";
$z="C:\Users\Administrator\Desktop\zizhao_20260924_r55final.zip";
$root="C:\Users\Administrator\AppData\Local\Temp\zsynctest15";
$d="C:\Users\Administrator\AppData\Local\Temp\zsynctest15\zizhao_20260924_r55final";
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
NewEv "$ev\r55_verify.txt" 'VERIFY_BEGIN_AT'
& ssh -o StrictHostKeyChecking=accept-new ht305 "powershell -NoProfile -EncodedCommand $b64" 2>&1 |
    Out-File -Append -Encoding utf8 "$ev\r55_verify.txt"
Stamp "$ev\r55_verify.txt" 'VERIFY_END_AT'
W 'VERIFY_FLUSHED'
