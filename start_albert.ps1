$lines = Get-Content "config.toml"

$arrays = @{}

foreach ($line in $lines) {
    if ($line -match '^\s*(to_play|to_advise|to_engine)\s*=\s*\[(.*)\]\s*$') {
        $key = $matches[1]
        $arrayContent = $matches[2]

        if ($arrayContent -eq '') {
            $arrays[$key] = @()
        } else {
            $arrays[$key] = $arrayContent -split ',' | ForEach-Object {
                $_.Trim().Trim('"')
            }
        }
    }
}

$combinedLength = $arrays['to_play'].Count + $arrays['to_advise'].Count + $arrays['to_engine'].Count
Write-Host "Combined length: $combinedLength"

for ($i = 1; $i -le $combinedLength; $i++) {
    Start-Process -FilePath "C:\Program Files (x86)\daide\albert\Albert.exe"
}
