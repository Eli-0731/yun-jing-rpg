$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$keyPath = Join-Path $projectRoot '.data/service.key'
$gameExecutable = Join-Path $projectRoot 'artifacts/windows/YunJing.exe'
if (-not (Test-Path -LiteralPath $keyPath)) { throw 'Run tools/start-local.ps1 first.' }
if (-not (Test-Path -LiteralPath $gameExecutable)) { throw 'Build Windows through tools/unity.ps1 -Target Windows first.' }
$env:YUNJING_INTERNAL_KEY = [IO.File]::ReadAllText($keyPath).Trim()
$server = Start-Process -FilePath $gameExecutable -ArgumentList @('-batchmode','-nographics','--server','-logFile',('"' + (Join-Path $projectRoot 'artifacts/room.log') + '"')) -WindowStyle Hidden -PassThru
Write-Host "Loopback room server PID $($server.Id). Close it with Stop-Process -Id $($server.Id)."
