# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SysMon is a cross-platform real-time system monitor built with PyQt5 and PyQtGraph. It displays CPU, Disk I/O, and Network activity with high-performance scrolling graphs (75-150x faster than matplotlib). Current version: v0.4.3.

## Development Commands

### Running the Application
```bash
# Recommended: use run.sh (auto-creates venv, installs deps, launches app)
./run.sh
./run.sh -s 5 -t 20  # with command-line options

# Manual setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 src/sysmon.py

# Command-line options
python3 src/sysmon.py -s 5 -t 20  # smoothing window 5, time window 20s
```

### Testing
```bash
# Run specific test
python3 tests/test_geometry.py
python3 tests/test_stderr_filter.py
```

### Building Executables
```bash
# Windows build (PyInstaller)
pyinstaller SysMon.spec

# The spec file includes icon bundling and no-console mode
```

### Installing Desktop Entry (Linux)
```bash
# Install desktop file
bash install-desktop.sh

# Force icon refresh
bash force-icon-refresh.sh
```

## Critical Project Rules

### Timezone Convention
**ALL timestamps MUST use Central Time USA (CST/CDT), NEVER UTC.**

This applies to:
- Changelog entries in source code headers
- Version labels in UI (see VERSION, RELEASE_DATE, RELEASE_TIME in src/sysmon.py:88-96)
- Documentation timestamps
- Git commit messages

Format examples:
- Full timestamp: `Tue 03 Dec 2025 09:20:00 PM CST`
- Version label: `v0.0.9b 2025-12-03`
- Release time: `1930 CST`

### Version Numbering
- Production releases: `v0.X.Y` (e.g., v0.2.9)
- Point releases/patches: `v0.X.Ya`, `v0.X.Yb` (e.g., v0.2.9a)
- Update version in: README.md, src/sysmon.py (VERSION, RELEASE_DATE, RELEASE_TIME, BUILD_DATE, BUILD_TIME), About dialog, CLAUDE.md

## Architecture

### Modular Package Architecture
The application entry point is `src/sysmon.py` (~266 lines) which composes `SystemMonitor` from mixin modules in `src/sysmon/`. Refactored from a single-file monolith in v0.4.0.

### Key Classes

**SystemMonitor (line 1398)** - Main application window
- Manages UI, graphs, timers, and configuration
- Uses PyQtGraph for real-time plotting (3 graphs: CPU, Disk I/O, Network)
- Handles XDG-compliant config storage in `~/.config/sysmon/`
- Window geometry persistence with 30-second auto-save
- Menu system with transparency, always-on-top, time window controls

**ProcessWorker (line 238)** - Async process analysis
- QObject-based worker for non-blocking process scanning
- Handles CPU, disk, and network metric collection via psutil
- Two-pass CPU measurement (0.5s delay) for accurate percentages
- Scans ALL processes (not limited to 200) to avoid missing high-PID processes
- Emits progress signals for UI updates

**RealTimeProcessDialog (line 388)** - Live CPU process viewer
- Updates every 3 seconds (adjustable 1-60s) with current top 10 CPU processes
- Uses QTableWidget with sortable columns
- Filter by process name or PID
- Pause/Resume controls for snapshot analysis
- Cancellable background worker thread

**RealTimeDiskDialog (line 667)** - Live disk I/O viewer
- Shows Read MB/s, Write MB/s, and Total MB for top 10 processes
- Delta-based rate calculation for accurate MB/s metrics
- Same real-time controls as CPU dialog

**RealTimeNetworkDialog** - Live network connections viewer
- Shows connection counts (Total, TCP, UDP, ESTABLISHED) per process
- Protocol and state breakdown
- Same real-time controls as CPU/Disk dialogs

**ProcessInfoDialog (line 364)** - Static process snapshot (legacy)
- Shows top 10 processes for a specific metric at time of middle-click
- Monospace font for alignment

### Data Flow

1. **QTimer** (200ms interval) triggers `update_data()` in src/sysmon.py:2031
2. **update_data()** collects system metrics via psutil:
   - CPU: `psutil.cpu_percent()`
   - Disk I/O: `psutil.disk_io_counters()` - calculates MB/s from deltas
   - Network: `psutil.net_io_counters()` - calculates KB/s from deltas
   - Memory: `psutil.virtual_memory()`, `psutil.swap_memory()`
3. Data stored in `deque` collections (maxlen based on time_window)
4. PyQtGraph plots updated with `setData()` for smooth scrolling
5. Configuration auto-saved every 30 seconds

### Configuration System

**XDG-compliant storage** (src/sysmon.py:192-236):
- Linux/macOS: `~/.config/sysmon/` (XDG standard)
- Windows: `%APPDATA%/sysmon/`

**Config files**:
- `config.json` - window geometry and position
- `preferences.json` - time window, transparency, always-on-top, axis inversion, graph colors

**Migration**: Automatically migrates from old `~/.sysmon_config.json` format

### Theme System

Auto-detects system theme (light/dark) via QPalette brightness analysis (src/sysmon.py:1470, 1637). Configures PyQtGraph backgrounds and foregrounds accordingly. Theme methods:
- `setup_pyqtgraph_theme()` - Initialize graph theme colors
- `is_dark_theme()` - Detect system theme
- `apply_system_theme_to_plots()` - Apply theme to all graphs

### Platform-Specific Code

**Linux stderr filtering** (src/sysmon.py:36-88):
- Background thread filters harmless GdkPixbuf warnings
- Uses pipe redirection and select() for non-blocking read
- Only enabled on Linux systems

**Icon handling**:
- Multi-resolution icons in `icons/` directory
- Window icon, tray icon (if implemented), and desktop file icon
- PyInstaller bundles icons via SysMon.spec

### Mouse Actions

- **Left-click** anywhere on the window to minimize to taskbar
- **Middle-click** (scroll wheel click) on any graph opens real-time process monitor dialogs

### Process Analysis

Middle-click on any graph opens real-time process monitor dialogs:
- **CPU graph** → RealTimeProcessDialog showing top CPU consumers with live updates
- **Disk graph** → RealTimeDiskDialog showing read/write MB/s rates
- **Network graph** → RealTimeNetworkDialog showing connection counts

All dialogs feature:
- Live updates every 3 seconds (adjustable 1-60s)
- Sortable columns (click headers)
- Process filtering by name or PID
- Pause/Resume controls
- Background worker threads to prevent UI freezing

### Key Features

**Real-time drill-down dialogs** (v0.2.15):
- Live-updating top 10 process lists with sortable columns
- Adjustable update intervals (1-60 seconds, default 3s)
- Process filtering by name or PID
- Pause/Resume controls for snapshot analysis

**Keyboard-controlled graph smoothing** (v0.2.18):
- +/- keys adjust moving average filter (1-20 points)
- Real-time smoothing of all graphs with visual feedback
- Reduces noise on busy systems, clarifies trends
- Persistent preference saved across sessions

**Live memory display**:
- RAM and Swap usage displayed in real-time
- Updates with each graph refresh

**Persistent graph preferences**:
- Axis inversion direction (left-to-right or right-to-left)
- Custom graph colors
- Saved to preferences.json

## Dependencies

Core (from requirements.txt):
- PyQt5 >= 5.15.0 (GUI framework)
- pyqtgraph >= 0.14.0 (real-time plotting - replaced matplotlib)
- psutil >= 5.8.0 (system metrics)
- numpy >= 1.25.0 (array operations for PyQtGraph)
- markdown >= 3.4.0 (documentation rendering)
- pygments >= 2.15.0 (syntax highlighting for markdown)
- pyqt-app-info (app identity & environment detection for About dialog — core only, no `[qt]` extra)

## Directory Structure

```
system-monitor/
├── src/              # Main application (single file: sysmon.py)
├── icons/            # Application icons (various sizes/formats)
├── tests/            # Test scripts (geometry, stderr filtering)
├── scripts/          # Utility scripts (graph experiments, system stats)
├── platforms/        # Platform-specific versions (e.g., Synology NAS)
├── archive/          # Old version files (not in git)
├── docs/             # CHANGELOG, analysis documents
├── notes/            # Development notes
├── SysMon.spec       # PyInstaller build specification
├── requirements.txt  # Python dependencies
└── run.sh            # Cross-platform venv launcher (auto-setup & run)
```

## Common Issues

**Icon not showing**: Check `icons/ICON_SysMon-t.png` exists and run `force-icon-refresh.sh` on Linux.

**GdkPixbuf warnings on Linux**: Normal - stderr filter suppresses harmless Qt/GTK warnings.

**Process analysis slow**: Scans ALL processes (not limited). CPU analysis uses two-pass measurement with 0.5s delay for accuracy.

**Window geometry not saving**: Check `~/.config/sysmon/config.json` permissions. Auto-save runs every 30 seconds.

## Development Notes

- **No matplotlib**: Project migrated from matplotlib to PyQtGraph for performance (v0.2.x series)
- **Single instance**: Uses QSharedMemory + QSystemSemaphore to prevent multiple instances (src/sysmon.py:110-190). Version-specific instance keys allow different versions to coexist.
- **Memory layout**: Uses `deque` with `maxlen` for automatic old-data removal
- **Real-time updates**: 200ms timer provides 5 updates/second for smooth graphs
- **Thread safety**: Process analysis uses QThread + QObject workers with signal/slot connections
- **Markdown support**: Built-in help system renders markdown with syntax highlighting
