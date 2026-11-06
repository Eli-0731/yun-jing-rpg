# Qingxi waterworks B: drive the Unity player with real OS key presses, mouse clicks/drags/wheel and (attempted)
# touch injection, while the player records itself (-qxOut). Slot and button positions come from the player's
# ui_map.json (client pixels), so clicks land where the player actually draws them.
#   powershell -ExecutionPolicy Bypass -File drive_puzzle.ps1 -Exe <QingxiWaterworks.exe> -Out <dir> -Log <driver.log>
param([string]$Exe, [string]$Out, [string]$Log)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, int dx, int dy, int data, UIntPtr extra);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x; public int y; }
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int left; public int top; public int right; public int bottom; }
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [StructLayout(LayoutKind.Sequential)] public struct POINTER_INFO {
    public int pointerType; public uint pointerId; public uint frameId; public uint pointerFlags;
    public IntPtr sourceDevice; public IntPtr hwndTarget;
    public POINT ptPixelLocation; public POINT ptHimetricLocation; public POINT ptPixelLocationRaw; public POINT ptHimetricLocationRaw;
    public uint dwTime; public uint historyCount; public int InputData; public uint dwKeyStates; public ulong PerformanceCount; public int ButtonChangeType; }
  [StructLayout(LayoutKind.Sequential)] public struct POINTER_TOUCH_INFO {
    public POINTER_INFO pointerInfo; public uint touchFlags; public uint touchMask; public RECT rcContact; public RECT rcContactRaw; public uint orientation; public uint pressure; }
  [DllImport("user32.dll", SetLastError = true)] public static extern bool InitializeTouchInjection(uint maxCount, uint mode);
  [DllImport("user32.dll", SetLastError = true)] public static extern bool InjectTouchInput(uint count, POINTER_TOUCH_INFO[] contacts);
  public static bool Touch(int x, int y, uint flags) {
    var c = new POINTER_TOUCH_INFO();
    c.pointerInfo.pointerType = 2; c.pointerInfo.pointerId = 0; c.pointerInfo.pointerFlags = flags;
    c.pointerInfo.ptPixelLocation.x = x; c.pointerInfo.ptPixelLocation.y = y;
    c.touchMask = 7; c.orientation = 90; c.pressure = 32000;
    c.rcContact.left = x - 2; c.rcContact.right = x + 2; c.rcContact.top = y - 2; c.rcContact.bottom = y + 2;
    return InjectTouchInput(1, new[] { c });
  }
}
"@
$seconds = 600
$p = Start-Process -FilePath $Exe -ArgumentList @("-screen-width","1280","-screen-height","720","-screen-fullscreen","0","-qxOut",$Out,"-qxFree",$seconds) -PassThru
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($p.MainWindowHandle -eq 0 -and $sw.Elapsed.TotalSeconds -lt 30) { Start-Sleep -Milliseconds 100; $p.Refresh() }
$h = $p.MainWindowHandle
$script:lines = @()
function Note([string]$s) { $script:lines += ("{0,7:0.00}s {1}" -f $sw.Elapsed.TotalSeconds, $s) }
function Focus { if ([W]::GetForegroundWindow() -ne $h) { [W]::keybd_event(0x12,0,0,[UIntPtr]::Zero); [W]::keybd_event(0x12,0,2,[UIntPtr]::Zero); [void][W]::ShowWindow($h,5); [void][W]::SetForegroundWindow($h); Start-Sleep -Milliseconds 120 } }
function Wait([double]$s) { Start-Sleep -Milliseconds ([int]($s * 1000)) }
function Key([byte]$vk, [string]$name, [byte[]]$mods = @()) {
  Focus
  foreach ($m in $mods) { [W]::keybd_event($m,0,0,[UIntPtr]::Zero) }
  $ext = if ($vk -in 0x25..0x28 -or $vk -eq 0x2E) { 1 } else { 0 }
  [W]::keybd_event($vk,0,$ext,[UIntPtr]::Zero); Start-Sleep -Milliseconds 70; [W]::keybd_event($vk,0,($ext -bor 2),[UIntPtr]::Zero)
  [array]::Reverse($mods); foreach ($m in $mods) { [W]::keybd_event($m,0,2,[UIntPtr]::Zero) }
  Note ("key {0} fg={1}" -f $name, ([W]::GetForegroundWindow() -eq $h))
}
function Map { for ($i = 0; $i -lt 20; $i++) { try { return Get-Content -Raw (Join-Path $Out "ui_map.json") | ConvertFrom-Json } catch { Start-Sleep -Milliseconds 50 } } }
function ToScreen([int]$x, [int]$y) { $pt = New-Object W+POINT; $pt.x = $x; $pt.y = $y; [void][W]::ClientToScreen($h, [ref]$pt); return $pt }
function MoveTo([int]$x, [int]$y, [double]$sec = 0.35) {
  # glide the cursor so the recording shows where it goes
  $start = New-Object W+POINT; Add-Type -AssemblyName System.Windows.Forms
  $c = [System.Windows.Forms.Cursor]::Position; $n = [Math]::Max(1, [int]($sec * 60))
  for ($i = 1; $i -le $n; $i++) { [void][W]::SetCursorPos([int]($c.X + ($x - $c.X) * $i / $n), [int]($c.Y + ($y - $c.Y) * $i / $n)); Start-Sleep -Milliseconds 16 }
}
function ClickAt([int]$cx, [int]$cy, [string]$name, [bool]$right = $false) {
  Focus
  $pt = ToScreen $cx $cy
  MoveTo $pt.x $pt.y
  Start-Sleep -Milliseconds 120
  if ($right) { [W]::mouse_event(0x08,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 70; [W]::mouse_event(0x10,0,0,0,[UIntPtr]::Zero) }
  else { [W]::mouse_event(0x02,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 70; [W]::mouse_event(0x04,0,0,0,[UIntPtr]::Zero) }
  Note ("{0}click {1} client=({2},{3})" -f $(if ($right) { "right-" } else { "" }), $name, $cx, $cy)
}
function ClickSlot([string]$id, [bool]$right = $false) {
  $m = Map; $xy = $m.slots.$id
  # only click a slot the player actually shows inside the 3D view (left of the 440 px panel)
  if ($xy[0] -lt 10 -or $xy[0] -gt ($m.screen[0] - 450) -or $xy[1] -lt 10 -or $xy[1] -gt ($m.screen[1] - 10)) { Note ("slot " + $id + " OFFSCREEN at (" + $xy[0] + "," + $xy[1] + "), click skipped"); return }
  ClickAt $xy[0] $xy[1] ("slot " + $id) $right
}
function ClickButton([string]$id) { $m = Map; $xy = $m.buttons.$id; if ($null -eq $xy) { Note ("button " + $id + " NOT IN MAP"); return }; ClickAt $xy[0] $xy[1] ("button " + $id) }
function Drag([int]$x0, [int]$y0, [int]$x1, [int]$y1, [double]$sec) {
  Focus
  $a = ToScreen $x0 $y0; $b = ToScreen $x1 $y1
  MoveTo $a.x $a.y; [W]::mouse_event(0x02,0,0,0,[UIntPtr]::Zero)
  $n = [int]($sec * 60)
  for ($i = 1; $i -le $n; $i++) { [void][W]::SetCursorPos([int]($a.x + ($b.x - $a.x) * $i / $n), [int]($a.y + ($b.y - $a.y) * $i / $n)); Start-Sleep -Milliseconds 16 }
  [W]::mouse_event(0x04,0,0,0,[UIntPtr]::Zero)
  Note ("drag client ({0},{1}) -> ({2},{3}) {4}s" -f $x0, $y0, $x1, $y1, $sec)
}
function Wheel([int]$cx, [int]$cy, [int]$notches) {
  Focus
  $pt = ToScreen $cx $cy; MoveTo $pt.x $pt.y
  for ($i = 0; $i -lt [Math]::Abs($notches); $i++) { [W]::mouse_event(0x0800,0,0,[Math]::Sign($notches) * 120,[UIntPtr]::Zero); Start-Sleep -Milliseconds 180 }
  Note ("wheel {0} notches at ({1},{2})" -f $notches, $cx, $cy)
}
function Place([byte]$vk, [string]$name) { Key $vk $name; Wait 0.9 }

$VK = @{ UP=0x26; DOWN=0x28; LEFT=0x25; RIGHT=0x27; TAB=0x09; ENTER=0x0D; ESC=0x1B; DEL=0x2E; CTRL=0x11; SHIFT=0x10;
         G=0x47; Q=0x51; W=0x57; E=0x45; C=0x43; Z=0x5A; Y=0x59; F12=0x7B; MINUS=0xBD }
function D([int]$n) { return [byte](0x30 + $n) }

Note "window ready"
Wait 4
# ---------------- A. wrong joints, explained, then fixed (full clues)
Key $VK.C "C close-up on P2"; Wait 1.6
Key (D 5) "5 B03 bend into P2 (dead end)"; Wait 4.5
Key $VK.Z "Ctrl+Z undo" @($VK.CTRL); Wait 1.8
Key (D 9) "9 B04-V02 tee at P2 (both sides open)"; Wait 4.5
Key $VK.DEL "Del remove"; Wait 1.2
Key (D 4) "4 B05 gate at P2 (closed)"; Wait 3.5
Key $VK.UP "Up -> P3"; Wait 0.8
Key (D 5) "5 B03 bend at P3 (outlet misses every slot)"; Wait 4.5
Key (D 1) "1 B02 straight at P3"; Wait 1.5
Key $VK.UP "Up -> P4"; Wait 0.8
Key (D 2) "2 B07-V02 corner patch on P4 (wrong shape)"; Wait 4.5
Key (D 1) "1 B07 saddle patch on P4"; Wait 1.8
Key $VK.UP "Up -> P5"; Wait 0.8
Place (D 1) "1 B02 at P5"
Key $VK.UP "Up -> P6"; Wait 0.8
Place (D 1) "1 B02 at P6"
Key $VK.W "W restore_channel"; Wait 3.5
Key $VK.C "C overview"; Wait 2
ClickSlot "P2"; Wait 1.2
Key $VK.G "G open gate P2"; Wait 6
Key $VK.ENTER "Enter complete"; Wait 7
Key $VK.ENTER "Enter again (resend same request)"; Wait 6
Key $VK.ESC "Esc close card"; Wait 1.5
# ---------------- B. protect the nursery: refused for the direct line, then the western bypass
Key $VK.E "E protect_nursery on the direct line"; Wait 4.5
ClickButton "clear"; Wait 1.8
ClickSlot "P2"; Wait 0.8
Place (D 6) "6 B03-V04 left bend at P2"
Key $VK.LEFT "Left -> L1"; Wait 0.7
Place (D 1) "1 B02 at L1"
Key $VK.LEFT "Left -> L2"; Wait 0.7
Place (D 5) "5 B03 right bend at L2"
Key $VK.UP "Up -> L3"; Wait 0.7
Place (D 2) "2 B02-V03 at L3"
Key $VK.UP "Up -> L4"; Wait 0.7
Place (D 4) "4 B05 gate at L4"
Key $VK.UP "Up -> L5"; Wait 0.7
Place (D 7) "7 B03-V02 right bend at L5"
Key $VK.RIGHT "Right -> L6"; Wait 0.7
Place (D 1) "1 B02 at L6"
Key $VK.TAB "Tab -> L7"; Wait 0.7
Place (D 8) "8 B03-V03 left bend at L7"
ClickSlot "L4"; Wait 1.0
Key $VK.G "G open gate L4"; Wait 2.5
Key $VK.E "E protect_nursery"; Wait 4.5
Key $VK.ENTER "Enter complete"; Wait 7
Key $VK.ESC "Esc close card"; Wait 1.2
# ---------------- C. mouse camera: drag to orbit, wheel to zoom
Drag 420 470 600 400 1.4; Wait 1.2
Wheel 420 380 4; Wait 1.5
Wheel 420 380 -4; Wait 1.2
Drag 600 400 420 470 1.2; Wait 1.2
# ---------------- D. clear the silt first (mud to the drain, field held by a closed gate)
ClickButton "clear"; Wait 1.5
ClickSlot "P2"; Wait 0.8
Place (D 9) "9 B04-V02 tee at P2"
Key $VK.LEFT "Left -> L1"; Wait 0.7
Place (D 1) "1 B02 at L1"
Key $VK.LEFT "Left -> L2"; Wait 0.7
Place $VK.MINUS "- B02-V05 discharge ramp at L2"
ClickSlot "R1"; Wait 0.8
Place (D 4) "4 B05 gate at R1 (kept closed)"
Wait 1.5
Key $VK.Q "Q clear_silt"; Wait 4
Key $VK.ENTER "Enter complete"; Wait 7
Key $VK.ESC "Esc close card"; Wait 1.2
# ---------------- E. after desilting: rebuild the direct line, full water; mouse palette clicks
ClickButton "clear"; Wait 1.5
ClickSlot "P2"; Wait 0.8
ClickButton "place:B05"; Wait 0.9
Key $VK.UP "Up -> P3"; Wait 0.6
ClickButton "place:B02"; Wait 0.9
Key $VK.UP "Up -> P4"; Wait 0.6
ClickButton "patch:B07"; Wait 0.9
Key $VK.UP "Up -> P5"; Wait 0.6
Place (D 1) "1 B02 at P5"
Key $VK.UP "Up -> P6"; Wait 0.6
Place (D 1) "1 B02 at P6"
ClickSlot "P2"; Wait 0.8
ClickButton "gate"; Wait 1.5
ClickButton "choose:restore_channel"; Wait 5
ClickButton "complete"; Wait 7
ClickButton "closecard"; Wait 1.2
# ---------------- F. right-click remove, undo / redo
ClickSlot "P5" $true; Wait 4
Key $VK.Z "Ctrl+Z undo" @($VK.CTRL); Wait 2.5
Key $VK.Z "Ctrl+Shift+Z redo" @($VK.CTRL, $VK.SHIFT); Wait 2.5
Key $VK.Y "Ctrl+Y redo (nothing left)" @($VK.CTRL); Wait 2
Key $VK.Z "Ctrl+Z undo" @($VK.CTRL); Wait 2.5
# ---------------- G. no clues: preview is an estimate, completion reveals what was missed
ClickButton "obs:none"; Wait 3
ClickSlot "P2"; Wait 0.8
Place (D 4) "4 B05 at P2"
Key $VK.UP "Up -> P3"; Wait 0.6
Place (D 1) "1 B02 at P3"
Key $VK.UP "Up -> P4"; Wait 0.6
Key $VK.UP "Up -> P5"; Wait 0.6
Place (D 1) "1 B02 at P5"
Key $VK.UP "Up -> P6"; Wait 0.6
Place (D 1) "1 B02 at P6"
ClickSlot "P2"; Wait 0.8
Key $VK.G "G open gate"; Wait 1.5
Key $VK.W "W restore_channel"; Wait 5
Key $VK.ENTER "Enter complete"; Wait 8
Key $VK.ESC "Esc close card"; Wait 1.5
# ---------------- H. touch: tap a slot, one-finger drag (Windows touch injection; may be ignored without a digitizer)
$ok = [W]::InitializeTouchInjection(2, 1)
Note ("InitializeTouchInjection ok={0} err={1}" -f $ok, [Runtime.InteropServices.Marshal]::GetLastWin32Error())
if ($ok) {
  Focus
  $m = Map; $xy = $m.slots.L3; $pt = ToScreen $xy[0] $xy[1]
  $r1 = [W]::Touch($pt.x, $pt.y, 0x00010006); Start-Sleep -Milliseconds 60
  $r2 = [W]::Touch($pt.x, $pt.y, 0x00040000)
  Note ("touch tap L3 at screen ({0},{1}) down={2} up={3} err={4}" -f $pt.x, $pt.y, $r1, $r2, [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  Wait 1.5
  $a = ToScreen 420 480
  [void][W]::Touch($a.x, $a.y, 0x00010006)
  for ($i = 1; $i -le 40; $i++) { [void][W]::Touch($a.x + $i * 4, $a.y - $i, 0x00020006); Start-Sleep -Milliseconds 16 }
  $r3 = [W]::Touch($a.x + 160, $a.y - 40, 0x00040000)
  Note ("touch drag up={0} err={1}" -f $r3, [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  Wait 2
}
Key $VK.F12 "F12 end recording"
$p.WaitForExit(60000) | Out-Null
Note ("player exited code={0}" -f $p.ExitCode)
$script:lines | Set-Content -Encoding utf8 $Log
$script:lines
