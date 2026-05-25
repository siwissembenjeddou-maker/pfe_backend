Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class WindowHelper {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
}
"@

$found = $false

[WindowHelper]::EnumWindows({
        param($hwnd, $lParam)
        $sb = New-Object System.Text.StringBuilder 256
        [WindowHelper]::GetWindowText($hwnd, $sb, 256) | Out-Null
        $title = $sb.ToString()
        if ($title -like "*Pixel*" -or $title -like "*emulator*" -or $title -like "*Android*") {
            Write-Host "Found window: '$title' (handle: $hwnd)"
            # Move to position (100, 100), keep original size (use SWP_NOSIZE = 0x0001)
            [WindowHelper]::SetWindowPos($hwnd, [IntPtr]::Zero, 100, 100, 800, 1200, 0x0040) | Out-Null
            $script:found = $true
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null

if (-not $found) {
    Write-Host "No emulator window found. Make sure the emulator is running."
}
else {
    Write-Host "Done! The emulator window has been moved to position (100, 100)."
}
