$ErrorActionPreference = "Stop"

$nativeSource = @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class DwmStreamDeckNative
{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maximumCount);
}
"@

try {
    Add-Type -TypeDefinition $nativeSource -ErrorAction Stop

    $foreground = [DwmStreamDeckNative]::GetForegroundWindow()
    if ($foreground -eq [IntPtr]::Zero) {
        Write-Output "not-foreground"
        exit 0
    }

    [uint32]$foregroundProcessId = 0
    [void][DwmStreamDeckNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundProcessId)
    $foregroundProcess = Get-Process -Id $foregroundProcessId -ErrorAction Stop
    $normalizedName = ($foregroundProcess.ProcessName -replace '[\s-]', '').ToLowerInvariant()
    $titleBuffer = New-Object System.Text.StringBuilder 512
    [void][DwmStreamDeckNative]::GetWindowText($foreground, $titleBuffer, $titleBuffer.Capacity)
    $windowTitle = $titleBuffer.ToString().Trim().ToLowerInvariant()

    $knownProcess = $normalizedName -in @('streamdeck', 'elgatostreamdeck')
    $knownTitle = $windowTitle -eq 'stream deck' -or $windowTitle.StartsWith('stream deck ')
    if (-not ($knownProcess -or $knownTitle)) {
        Write-Output "not-foreground"
        exit 0
    }

    $SW_FORCEMINIMIZE = 11
    $WM_SYSCOMMAND = 0x0112
    $SC_MINIMIZE = 0xF020

    [void][DwmStreamDeckNative]::ShowWindowAsync($foreground, $SW_FORCEMINIMIZE)
    Start-Sleep -Milliseconds 120

    if (-not [DwmStreamDeckNative]::IsIconic($foreground) -and
        [DwmStreamDeckNative]::GetForegroundWindow() -eq $foreground) {
        [void][DwmStreamDeckNative]::PostMessage(
            $foreground,
            $WM_SYSCOMMAND,
            [IntPtr]$SC_MINIMIZE,
            [IntPtr]::Zero
        )
        Start-Sleep -Milliseconds 100
    }

    if (-not [DwmStreamDeckNative]::IsIconic($foreground) -and
        [DwmStreamDeckNative]::GetForegroundWindow() -eq $foreground) {
        [void][DwmStreamDeckNative]::ShowWindow($foreground, $SW_FORCEMINIMIZE)
        Start-Sleep -Milliseconds 120
    }

    if ([DwmStreamDeckNative]::IsIconic($foreground) -or
        [DwmStreamDeckNative]::GetForegroundWindow() -ne $foreground) {
        Write-Output "released"
    }
    else {
        Write-Output "blocked"
    }
}
catch {
    Write-Output "blocked"
}
