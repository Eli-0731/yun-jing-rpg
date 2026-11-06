# Launch demo (free record 44 s), send real key presses to its window on a schedule, log send times.
param([string]$Exe, [string]$Out, [string]$Log)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class K {
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
$p = Start-Process -FilePath $Exe -ArgumentList @("-screen-width","1280","-screen-height","720","-screen-fullscreen","0","-qxOut",$Out,"-qxFree","44") -PassThru
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($p.MainWindowHandle -eq 0 -and $sw.Elapsed.TotalSeconds -lt 20) { Start-Sleep -Milliseconds 100; $p.Refresh() }
$h = $p.MainWindowHandle
$lines = @()
function Focus { [K]::keybd_event(0x12,0,0,[UIntPtr]::Zero); [K]::keybd_event(0x12,0,2,[UIntPtr]::Zero); [void][K]::ShowWindow($h,5); [void][K]::SetForegroundWindow($h) }
function Tap([byte]$vk, [string]$name) {
  Focus
  $ext = if ($vk -in 0x25..0x28) { 1 } else { 0 }
  [K]::keybd_event($vk,0,$ext,[UIntPtr]::Zero); Start-Sleep -Milliseconds 80; [K]::keybd_event($vk,0,($ext -bor 2),[UIntPtr]::Zero)
  $script:lines += ("{0:0.00}s tap {1} fg={2}" -f $sw.Elapsed.TotalSeconds, $name, ([K]::GetForegroundWindow() -eq $h))
}
function Hold([byte]$vk, [string]$name, [double]$sec) {
  Focus
  $script:lines += ("{0:0.00}s hold {1} {2}s start fg={3}" -f $sw.Elapsed.TotalSeconds, $name, $sec, ([K]::GetForegroundWindow() -eq $h))
  $end = $sw.Elapsed.TotalSeconds + $sec
  while ($sw.Elapsed.TotalSeconds -lt $end) { [K]::keybd_event($vk,0,1,[UIntPtr]::Zero); Start-Sleep -Milliseconds 30 }
  [K]::keybd_event($vk,0,3,[UIntPtr]::Zero)
  $script:lines += ("{0:0.00}s hold {1} end" -f $sw.Elapsed.TotalSeconds, $name)
}
function At([double]$t) { while ($sw.Elapsed.TotalSeconds -lt $t) { Start-Sleep -Milliseconds 20 } }
$lines += ("{0:0.00}s window ready" -f $sw.Elapsed.TotalSeconds)
At 4;  Tap 0x47 "G (open gate)"
At 13; Tap 0x32 "2 (weir camera)"
At 14; Hold 0x28 "Down (lower planks)" 4.6
At 22; Tap 0x31 "1 (overview camera)"
At 25; Tap 0x47 "G (close gate)"
At 32; Tap 0x32 "2 (weir camera)"
At 33; Hold 0x26 "Up (raise planks)" 4.6
At 39; Tap 0x33 "3 (intake camera)"
$p.WaitForExit(60000) | Out-Null
$lines += ("{0:0.00}s demo exited code={1}" -f $sw.Elapsed.TotalSeconds, $p.ExitCode)
$lines | Set-Content -Encoding utf8 $Log
$lines
