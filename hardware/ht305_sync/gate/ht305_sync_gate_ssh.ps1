$ErrorActionPreference='Stop'
$str = ([System.IO.File]::ReadAllText((Join-Path $env:USERPROFILE '.ssh\.ht305_pass.xml'), [System.Text.UTF8Encoding]::new($false))).Trim()
if ($str[0] -eq [char]0xFEFF) { $str = $str.Substring(1) }
$sec = $str | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($sec)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
[Runtime.InteropServices.Marshal]::FreeHGlobal($bstr)
Write-Output ("SSH_SECRET_LEN=" + $plain.Length)
$hits = 0
Get-ChildItem $env:TEMP -Include ht305_*.ps1,build_sync.py,build_zip.py,expected*.py,pw_*.py,sync_r4*.py,r44_*.ps1,r44_*.txt,r45_*.ps1,r45_*.txt,r45_*.py,chk_r45.ps1,probe_zip_vs_head*.py,cred_recount_0822.txt,land_r44b_report.py -File | Sort-Object Name | ForEach-Object {
  $b = [System.IO.File]::ReadAllBytes($_.FullName)
  $t = [System.Text.Encoding]::UTF8.GetString($b) + [System.Text.Encoding]::GetEncoding(936).GetString($b)
  $n = ([regex]::Matches($t, [regex]::Escape($plain))).Count
  if ($n -gt 0) { $hits++; Write-Output ("HIT " + $_.Name + " " + $n) }
}
Write-Output ("SSH_SECRET_HITS_FILES=" + $hits)
