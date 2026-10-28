param(
    [ValidateSet('Generate','WorldPreview','Walkthrough','WalkthroughWindows','UnifiedWorld','UnifiedWorldWindows','NoviceVillage','NoviceVillageWindows','Windows','Android','LinuxServer')] [string]$Target = 'Generate',
    [string]$EditorPath = 'D:\DevTools\Unity\6000.0.82f1\Editor\Unity.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $projectRoot 'apps/game'
if (-not (Test-Path -LiteralPath $EditorPath)) { throw "Unity not found: $EditorPath" }
if ($Target -eq 'WalkthroughWindows' -or $Target -eq 'UnifiedWorldWindows' -or $Target -eq 'NoviceVillageWindows') {
    # Input backend changes made by scene generation take effect after an Editor restart.
    $prepass = if ($Target -eq 'WalkthroughWindows') { 'Walkthrough' } elseif ($Target -eq 'NoviceVillageWindows') { 'NoviceVillage' } else { 'UnifiedWorld' }
    & $PSCommandPath -Target $prepass -EditorPath $EditorPath
}
$methods = @{ Generate='Generate'; WorldPreview='Generate'; Walkthrough='Generate'; WalkthroughWindows='BuildWindows'; UnifiedWorld='Generate'; UnifiedWorldWindows='BuildWindows'; NoviceVillage='Generate'; NoviceVillageWindows='BuildWindows'; Windows='BuildWindows'; Android='BuildAndroid'; LinuxServer='BuildLinuxServer' }
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'artifacts') | Out-Null
$log = Join-Path $projectRoot "artifacts/unity-$Target.log"
$builder = if ($Target -eq 'WorldPreview') { 'QingxiWorldBuilder' } elseif ($Target -like 'Walkthrough*') { 'QingxiWalkthroughBuilder' } elseif ($Target -like 'UnifiedWorld*') { 'QingxiUnifiedWorldBuilder' } elseif ($Target -like 'NoviceVillage*') { 'QingxiNoviceVillageBuilder' } else { 'ProjectBuilder' }
$method = 'YunJing.Editor.' + $builder + '.' + $methods[$Target]
$arguments = @('-batchmode','-nographics','-quit','-projectPath','.', '-executeMethod',$method,'-logFile',('"' + $log + '"'))
$process = Start-Process -FilePath $EditorPath -WorkingDirectory $gamePath -ArgumentList $arguments -WindowStyle Hidden -PassThru
# Wait for the Editor itself; helper processes may outlive a completed batch run.
$process.WaitForExit()
$process.Refresh()
if ($process.ExitCode -ne 0) { Get-Content -LiteralPath $log -Tail 35; throw "Unity failed ($($process.ExitCode)). Log: $log" }
Write-Host "Unity $Target completed. Log: $log"
