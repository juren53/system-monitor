# install-windows.ps1
# Creates a Start Menu shortcut for SysMon and attempts to pin it to the Taskbar.
# Run from PowerShell: .\install-windows.ps1

$ExePath  = "$env:USERPROFILE\bin\SysMon.exe"
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$ShortcutPath = "$StartMenuDir\SysMon.lnk"

# --- Validate executable -------------------------------------------------------
if (-not (Test-Path $ExePath)) {
    Write-Error "SysMon.exe not found at $ExePath"
    exit 1
}

# --- Create Start Menu shortcut ------------------------------------------------
# Use the icon embedded in the exe so shortcut icon always matches the build.
$Shell    = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath       = $ExePath
$Shortcut.WorkingDirectory = Split-Path $ExePath
$Shortcut.Description      = "SysMon - Real-Time System Monitor"
$Shortcut.IconLocation     = "$ExePath,0"
$Shortcut.Save()

# Flush the Windows icon cache so the new icon appears immediately.
ie4uinit.exe -show

Write-Host "Start Menu shortcut created: $ShortcutPath" -ForegroundColor Green

# --- Pin to Taskbar (Windows 10/11) -------------------------------------------
# Windows 11 removed the old VerbsEx approach. The only reliable method is the
# "Pin to taskbar" verb via the shell, which still works on Windows 10 and some
# Windows 11 builds.
try {
    $ShellApp = New-Object -ComObject Shell.Application
    $Folder   = $ShellApp.Namespace((Split-Path $ShortcutPath))
    $Item     = $Folder.ParseName((Split-Path $ShortcutPath -Leaf))
    $Verbs    = $Item.Verbs()
    $PinVerb  = $Verbs | Where-Object { $_.Name -match "Pin to tas&kbar|Pin to Taskbar" }

    if ($PinVerb) {
        $PinVerb.DoIt()
        Write-Host "Pinned to Taskbar." -ForegroundColor Green
    } else {
        Write-Host "Automatic taskbar pinning not available on this Windows version." -ForegroundColor Yellow
        Write-Host "To pin manually: open Start Menu, find SysMon, right-click -> 'Pin to taskbar'" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Taskbar pinning skipped: $_" -ForegroundColor Yellow
    Write-Host "To pin manually: open Start Menu, find SysMon, right-click -> 'Pin to taskbar'" -ForegroundColor Yellow
}
