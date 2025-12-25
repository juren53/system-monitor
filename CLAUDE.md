# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SysMon is a cross-platform real-time system monitor built with PyQt5 and PyQtGraph. It displays CPU, Disk I/O, and Network activity with high-performance scrolling graphs (75-150x faster than matplotlib). Current version: v0.2.9.

## Development Commands

### Running the Application
```bash
# With virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 src/sysmon.py

# Direct run (if dependencies installed globally)
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
bash run-sysmon.sh

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
- Update version in: README.md, src/sysmon.py (VERSION, RELEASE_DATE, RELEASE_TIME, BUILD_DATE, BUILD_TIME), About dialog

## Architecture

### Single-File Application
The entire application is contained in `src/sysmon.py` (2333 lines). This is intentional - do not split into modules without explicit approval.

### Key Classes

**SystemMonitor (line 587)** - Main application window
- Manages UI, graphs, timers, and configuration
- Uses PyQtGraph for real-time plotting (3 graphs: CPU, Disk I/O, Network)
- Handles XDG-compliant config storage in `~/.config/sysmon/`
- Window geometry persistence with 30-second auto-save
- Menu system with transparency, always-on-top, time window controls

**ProcessWorker (line 235)** - Async process analysis
- QObject-based worker for non-blocking process scanning
- Handles CPU, disk, and network metric collection via psutil
- Limits to 200 processes to prevent excessive scanning
- Emits progress signals for UI updates

**RealTimeProcessDialog (line 369)** - Live top processes viewer
- Updates every second with current top 10 CPU processes
- Uses QTableWidget for formatted display
- Cancellable background worker thread

**ProcessInfoDialog (line 345)** - Static process snapshot
- Shows top 10 processes for a specific metric at time of double-click
- Monospace font for alignment

### Data Flow

1. **QTimer** (200ms interval) triggers `update_plot()` in src/sysmon.py:1015
2. **update_plot()** collects system metrics via psutil:
   - CPU: `psutil.cpu_percent()`
   - Disk I/O: `psutil.disk_io_counters()` - calculates MB/s from deltas
   - Network: `psutil.net_io_counters()` - calculates KB/s from deltas
   - Memory: `psutil.virtual_memory()`, `psutil.swap_memory()`
3. Data stored in `deque` collections (maxlen based on time_window)
4. PyQtGraph plots updated with `setData()` for smooth scrolling
5. Configuration auto-saved every 30 seconds

### Configuration System

**XDG-compliant storage** (src/sysmon.py:165-233):
- Linux: `~/.config/sysmon/`
- Windows: `%APPDATA%/sysmon/`
- macOS: `~/Library/Application Support/sysmon/`

**Config files**:
- `config.json` - window geometry
- `preferences.json` - time window, transparency, always-on-top settings

**Migration**: Automatically migrates from old `~/.sysmon_config.json` format

### Theme System

Auto-detects system theme (light/dark) via QPalette brightness analysis (src/sysmon.py:657-679). Configures PyQtGraph backgrounds and foregrounds accordingly.

### Platform-Specific Code

**Linux stderr filtering** (src/sysmon.py:33-85):
- Background thread filters harmless GdkPixbuf warnings
- Uses pipe redirection and select() for non-blocking read

**Icon handling**:
- Multi-resolution icons in `icons/` directory
- Window icon, tray icon (if implemented), and desktop file icon
- PyInstaller bundles icons via SysMon.spec

### Process Analysis

Double-click on any graph triggers async process analysis:
- CPU graph → top CPU consumers
- Disk graph → top disk I/O (read+write MB)
- Network graph → top network connections count

Worker thread prevents UI freezing during process iteration.

## Dependencies

Core (from requirements.txt):
- PyQt5 >= 5.15.0 (GUI framework)
- pyqtgraph >= 0.14.0 (real-time plotting - replaced matplotlib)
- psutil >= 5.8.0 (system metrics)
- numpy >= 1.25.0 (array operations for PyQtGraph)

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
└── run-sysmon.sh     # Desktop integration script (Linux)
```

## Common Issues

**Icon not showing**: Check `icons/ICON_SysMon-t.png` exists and run `force-icon-refresh.sh` on Linux.

**GdkPixbuf warnings on Linux**: Normal - stderr filter suppresses harmless Qt/GTK warnings.

**Process analysis slow**: Limited to 200 processes max. CPU analysis uses cached values to avoid blocking.

**Window geometry not saving**: Check `~/.config/sysmon/config.json` permissions. Auto-save runs every 30 seconds.

## Development Notes

- **No matplotlib**: Project migrated from matplotlib to PyQtGraph for performance (v0.2.x series)
- **Single instance**: Uses QSharedMemory to prevent multiple instances
- **Memory layout**: Uses `deque` with `maxlen` for automatic old-data removal
- **Real-time updates**: 200ms timer provides 5 updates/second for smooth graphs
