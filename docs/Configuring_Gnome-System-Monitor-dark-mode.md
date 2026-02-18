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

## Additional .desktop Launch Options

The `.desktop` file `Exec` line can also pass environment variables and command-line arguments:

```
# Force HiDPI scaling
Exec=env GDK_SCALE=2 GTK_THEME=Adwaita:dark gnome-system-monitor

# Open directly to a specific tab
Exec=env GTK_THEME=Adwaita:dark gnome-system-monitor -p   # Processes tab
Exec=env GTK_THEME=Adwaita:dark gnome-system-monitor -s   # Resources tab
Exec=env GTK_THEME=Adwaita:dark gnome-system-monitor -f   # File Systems tab

# Force display backend
Exec=env GDK_BACKEND=x11 GTK_THEME=Adwaita:dark gnome-system-monitor
```

## gsettings Configuration

Most GNOME System Monitor settings are managed via `gsettings` under the `org.gnome.gnome-system-monitor` schema. These persist across sessions in the dconf database.

### General

| Setting | Description | Default |
|---|---|---|
| `current-tab` | Tab shown on launch (`processes`, `resources`, `disks`) | `'resources'` |
| `show-whose-processes` | Which processes to show (`user`, `active`, `all`) | `'user'` |
| `show-dependencies` | Show process tree (parent/child relationships) | `false` |
| `show-all-fs` | Show all filesystems including virtual ones | `false` |
| `maximized` | Launch maximized | `false` |
| `window-width` / `window-height` | Window dimensions | `620` / `720` |
| `kill-dialog` | Show confirmation dialog before killing a process | `true` |

### Graph & Update Settings

| Setting | Description | Default |
|---|---|---|
| `update-interval` | Process list refresh interval in ms | `3000` |
| `graph-update-interval` | Graph refresh interval in ms | `100` |
| `graph-data-points` | Number of data points shown in graphs | `60` |
| `disks-interval` | Disk usage refresh interval in ms | `5000` |
| `smooth-refresh` | Enable smooth process list updates | `true` |
| `cpu-smooth-graph` | Smooth CPU graph lines | `true` |
| `cpu-stacked-area-chart` | Stack CPU cores in area chart | `false` |
| `logarithmic-scale` | Use logarithmic scale for network graph | `false` |
| `solaris-mode` | Divide CPU usage by number of CPUs | `true` |

### Graph Colors

| Setting | Description | Default |
|---|---|---|
| `cpu-colors` | Per-core CPU graph colors | (array of hex colors) |
| `mem-color` | Memory usage graph color | `'#e01b24'` |
| `swap-color` | Swap usage graph color | `'#33d17a'` |
| `net-in-color` | Network receive graph color | `'#3584e4'` |
| `net-out-color` | Network send graph color | `'#e66100'` |
| `disk-read-color` | Disk read graph color | `'#3584e4'` |
| `disk-write-color` | Disk write graph color | `'#e66100'` |

### Display Units

| Setting | Description | Default |
|---|---|---|
| `network-in-bits` | Show current network speed in bits/s | `false` |
| `network-total-in-bits` | Show total network transfer in bits | `false` |
| `process-memory-in-iec` | Show process memory in IEC units (KiB/MiB) | `false` |
| `resources-memory-in-iec` | Show resource memory in IEC units | `false` |

### Example Commands

```bash
# List all current settings
gsettings list-recursively org.gnome.gnome-system-monitor

# Set default tab to Processes
gsettings set org.gnome.gnome-system-monitor current-tab 'processes'

# Show all processes (not just current user)
gsettings set org.gnome.gnome-system-monitor show-whose-processes 'all'

# Faster graph updates (50ms instead of 100ms)
gsettings set org.gnome.gnome-system-monitor graph-update-interval 50

# More graph history (120 data points instead of 60)
gsettings set org.gnome.gnome-system-monitor graph-data-points 120

# Change memory graph color to blue
gsettings set org.gnome.gnome-system-monitor mem-color '#3584e4'

# Show network speeds in bits per second
gsettings set org.gnome.gnome-system-monitor network-in-bits true

# Reset a setting to default
gsettings reset org.gnome.gnome-system-monitor graph-update-interval
```

## Notes

- This approach can be used for any stubborn GTK4/libadwaita app that ignores the system dark mode setting.
- The `~/.config/gtk-4.0/settings.ini` file was also created during troubleshooting and may help other GTK4 apps, so it was left in place.
- The gsettings configuration is stored in the dconf database at `/org/gnome/gnome-system-monitor/` and can also be browsed with the `dconf-editor` GUI tool.
