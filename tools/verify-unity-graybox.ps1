param(
    [string]$EditorPath = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root 'apps/game'
# Use the pinned editor version; look in -EditorPath, $env:UNITY_EDITOR, the shared D:\DevTools install, then the Unity Hub default.
$version = ((Get-Content -LiteralPath (Join-Path $project 'ProjectSettings/ProjectVersion.txt') | Select-String '^m_EditorVersion:\s*(\S+)').Matches[0].Groups[1].Value)
$candidates = @($EditorPath, $env:UNITY_EDITOR,
    "D:\DevTools\Unity\$version\Editor\Unity.exe",
    (Join-Path $env:ProgramFiles "Unity\Hub\Editor\$version\Editor\Unity.exe")) | Where-Object { $_ }
$EditorPath = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $EditorPath) { throw "Unity $version not found. Tried: $($candidates -join '; ')" }
Write-Output "Unity $version at $EditorPath"
$artifacts = Join-Path $root 'artifacts'
New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
$log = Join-Path $artifacts ('unity-graybox-' + [guid]::NewGuid().ToString('N') + '.log')
$arguments = @('-batchmode', '-nographics', '-quit', '-projectPath', ('"' + $project + '"'),
    '-executeMethod', 'YunJing.Editor.QingxiHuntStandaloneBuilder.Verify', '-logFile', ('"' + $log + '"'))
$process = Start-Process -FilePath $EditorPath -ArgumentList $arguments -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(900000)) {
    Stop-Process -Id $process.Id
    throw "Unity validation timed out. Log: $log"
}
$process.Refresh()
if ($process.ExitCode -ne 0 -or -not (Select-String -LiteralPath $log -SimpleMatch 'GRAYBOX_VERIFY_PASS:' -Quiet)) {
    throw "Unity graybox validation failed (exit $($process.ExitCode)). Log: $log"
}
Write-Output "Unity graybox generation and reload checks passed. Log: $log"

