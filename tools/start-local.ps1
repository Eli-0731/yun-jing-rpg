param([int]$Port = 4310)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$nodeDirectory = 'D:\DevTools\node-v22.23.3-win-x64'
if (Test-Path -LiteralPath $nodeDirectory) { $env:PATH = $nodeDirectory + ';' + $env:PATH }
$env:YUNJING_MODE = 'local'
$env:HOST = '127.0.0.1'
$env:PORT = [string]$Port
$env:YUNJING_DATA_DIR = Join-Path $projectRoot '.data/postgres'
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot '.data') | Out-Null
$keyPath = Join-Path $projectRoot '.data/service.key'
if (-not (Test-Path -LiteralPath $keyPath)) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    [IO.File]::WriteAllText($keyPath, [Convert]::ToBase64String($bytes))
    $rng.Dispose()
}
$env:YUNJING_INTERNAL_KEY = [IO.File]::ReadAllText($keyPath).Trim()
if (-not (Test-Path -LiteralPath 'node_modules')) { & npm.cmd ci; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
& npm.cmd run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Local inspector: http://127.0.0.1:$Port"
& node dist/services/api/src/main.js
exit $LASTEXITCODE
