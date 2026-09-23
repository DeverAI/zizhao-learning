$p='C:\Users\david\AppData\Local\Temp\r46_upload.ps1'
$e=$null
[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $p),[ref]$e)|Out-Null
'FIRST3=' + ((Get-Content -Encoding Byte -TotalCount 3 $p) -join ',')
'PARSE_ERRORS=' + $e.Count
'REMOVE_ITEM_HITS=' + @(Select-String -Path $p -Pattern 'Remove-Item').Count
'SCRIPT_LINES=' + (Get-Content $p).Count
