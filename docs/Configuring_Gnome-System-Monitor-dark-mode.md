# Configuring GNOME System Monitor for Dark Mode on LMDE

## Problem

After setting LMDE (Linux Mint Debian Edition) to dark mode, GNOME System Monitor (v48.1) remained in light mode. The Cinnamon desktop's dark mode setting was not being inherited by the app.

## Root Cause

GNOME System Monitor is a GTK4/libadwaita application. While LMDE's Cinnamon desktop correctly sets the `org.gnome.desktop.interface color-scheme` to `prefer-dark` and the GTK theme to `Mint-Y-Dark`, libadwaita apps don't always respect these settings — they follow the Adwaita theme internally.

## What We Tried

### 1. Verified dconf settings (already correct)

```bash
gsettings get org.gnome.desktop.interface color-scheme
# 'prefer-dark'

gsettings get org.gnome.desktop.interface gtk-theme
# 'Mint-Y-Dark'
```

### 2. Created GTK4 settings file (did not fix it)

Created `~/.config/gtk-4.0/settings.ini`:

```ini
[Settings]
gtk-application-prefer-dark-theme=true
```

This alone was not enough for GNOME System Monitor to switch to dark mode.

### 3. Launched with GTK_THEME environment variable (worked)

```bash
GTK_THEME=Adwaita:dark gnome-system-monitor
```

This successfully forced the app into dark mode.

## Solution

Created a local `.desktop` file override that applies the `GTK_THEME` environment variable automatically when launching from the menu:

**File:** `~/.local/share/applications/org.gnome.SystemMonitor.desktop`

The key change is the `Exec` line:

```
Exec=env GTK_THEME=Adwaita:dark gnome-system-monitor
```

This local `.desktop` file takes priority over the system-wide one at `/usr/share/applications/org.gnome.SystemMonitor.desktop`, so GNOME System Monitor will always launch in dark mode.

## Notes

- This approach can be used for any stubborn GTK4/libadwaita app that ignores the system dark mode setting.
- The `~/.config/gtk-4.0/settings.ini` file was also created during troubleshooting and may help other GTK4 apps, so it was left in place.
