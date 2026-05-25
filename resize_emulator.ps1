Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class WinResize {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
}
"@

[WinResize]::EnumWindows({
    param($hwnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 256
    [WinResize]::GetWindowText($hwnd, $sb, 256) | Out-Null
    $title = $sb.ToString()
    if ($title -like "*Pixel_4_XL:5554*" -and $title -notlike "*Extended*") {
        Write-Host "Resizing: $title"
        # Resize to 380x820 pixels at position (50, 30)
        [WinResize]::SetWindowPos($hwnd, [IntPtr]::Zero, 50, 30, 380, 820, 0x0040) | Out-Null
        Write-Host "Done! Emulator resized."
    }
    return $true
}, [IntPtr]::Zero) | Out-Null
