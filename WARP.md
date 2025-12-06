# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SysMon is a real-time system monitoring application built with Python, PyQt5, and matplotlib. It provides live scrolling graphs for CPU usage, Disk I/O, and Network activity with interactive controls and drill-down capabilities. The application features desktop theme inheritance, window geometry persistence, and cross-platform support (Linux/Windows).

## Development Commands

### Running the Application
```bash
# Basic run
python3 src/sysmon.py

# With custom smoothing window (1-20, default: 5)
python3 src/sysmon.py -s 10

# With custom time window (5-120 seconds, default: 20)
python3 src/sysmon.py -t 30

# Combined options
python3 src/sysmon.py -s 8 -t 40
```

### Dependencies Installation
```bash
pip install matplotlib psutil PyQt5
```

### Running Tests
```bash
# Test window geometry persistence
python3 tests/test_geometry.py

# Test stderr filtering (GdkPixbuf warnings)
python3 tests/test_stderr_filter.py
```

## Architecture & Code Structure

### Core Application (`src/sysmon.py`)
The main application is a monolithic ~800+ line file organized into:

1. **Initialization & Theme Setup** (lines 1-117)
   - `_filter_stderr()`: Filters GdkPixbuf-CRITICAL warnings using OS-level pipe/thread mechanism
   - `_apply_qt_desktop_theme()`: Detects and applies Qt desktop palette (light/dark theme) to matplotlib
   - Constants section: 22 centralized constants for data storage, timing, display, and units

2. **RealtimeMonitor Class** (lines 184+)
   - **Data Management**: Uses `deque` with 200-second buffer; time window controls visible display (5-120s)
   - **Three subplots**: CPU (single line), Disk I/O (read/write), Network (upload/download)
   - **Scale indicators**: Flash effects with directional colors (red=increasing, blue=decreasing scale)
   - **Window persistence**: Saves/loads geometry to `~/.sysmon_config.json` using Qt5 backend

3. **Key Methods**
   - `get_system_metrics()`: Collects psutil data (CPU, memory, disk, network)
   - `get_top_*_processes()`: Samples processes over 200ms for drill-down popups
   - `on_click()`: Double-click handler for process drill-down
   - `on_key_press()`: Keyboard controls (+/- for time window adjustment)
   - `update()`: Animation callback that updates all graphs at 50ms intervals

### Data Flow
1. `animation.FuncAnimation()` calls `update()` every 50ms
2. `update()` collects metrics via psutil → calculates rates → applies smoothing
3. Data stored in deques (200s capacity) → visible window extracted → plotted
4. Y-axis auto-scales based on visible data only
5. Scale magnitude changes trigger flash indicators

### Interactive Features
- **Double-click any graph**: Shows top 10 processes for that metric in popup window
- **Keyboard controls**:
  - `+` or `=`: Increase time window by 5 seconds (zoom out)
  - `-`: Decrease time window by 5 seconds (zoom in)
- **Window geometry**: Position and size automatically saved on exit

### Platform-Specific Code
- **Linux**: Uses Qt5Agg backend, XDG config paths planned (currently using `~/.sysmon_config.json`)
- **Windows**: Cross-platform compatible (originally developed on Windows)
- **Synology**: Separate implementation in `platforms/synology/syno-monitor.py` (uses synology_dsm API)

## Key Constants

All magic numbers are centralized at the top of `src/sysmon.py`:
- `DATA_BUFFER_SIZE = 200`: Maximum seconds stored in memory
- `DEFAULT_TIME_WINDOW = 20`: Default visible time range
- `ANIMATION_INTERVAL = 50`: Update frequency in milliseconds
- `PROCESS_SAMPLE_DELAY = 0.2`: Delay between process samples for accurate CPU measurement
- Unit conversion: `BYTES_PER_KB/MB/GB`, `BITS_PER_KB/MB/GB`

## Project Conventions

### Timezone
**CRITICAL**: All timestamps MUST use Central Time USA (CST/CDT), never UTC.
- Changelog format: `Tue 03 Dec 2025 09:20:00 PM CST`
- Version label format: `v0.0.9b 2025-12-03`
- Always include timezone indicator (CST or CDT)

### Version Numbering
- Release format: `v0.0.X` (e.g., v0.0.9)
- Point release format: `v0.0.Xa`, `v0.0.Xb` (e.g., v0.0.9b, v0.1.1)
- Update version in both UI label (line ~289) and header comment (line 2)

### Code Organization
- Main application: `src/sysmon.py`
- Icons: `assets/icons/` (ICON_sysmon.png, ICON_sysmon.ico)
- Documentation: `docs/` (CHANGELOG.md, analysis files)
- Tests: `tests/` (test_geometry.py, test_stderr_filter.py)
- Utility scripts: `scripts/` (animated-graph.py, smooth.py)
- Legacy versions: `archive/` (sysmon-*.py historical versions)
- Platform variants: `platforms/synology/`

### Configuration
- User config: `~/.sysmon_config.json`
- Contains: window x/y position, width/height
- Auto-saved on application exit via `atexit` handler

## Backend & Dependencies
- **Backend**: Qt5Agg (forced in code for consistency)
- **Required packages**: matplotlib, psutil, PyQt5
- **Python version**: 3.7+
- **OS compatibility**: Linux (LMDE tested), Windows

## Notes for AI Agents

### When Modifying Code
1. **Constants first**: Always use existing constants; add new ones to the constants section if needed
2. **Timezone compliance**: Any timestamp additions must use Central Time
3. **Theme awareness**: UI colors should use Qt palette or respect theme; avoid hardcoded colors
4. **Version updates**: Update both header comment and UI version label together
5. **Changelog**: Document changes in `docs/CHANGELOG.md` with Central Time timestamp

### Common Tasks
- **Adjust buffer size**: Modify `DATA_BUFFER_SIZE` constant
- **Change update frequency**: Modify `ANIMATION_INTERVAL` (in milliseconds)
- **Modify smoothing**: Adjust `DEFAULT_SMOOTH_WINDOW` or `MAX_SMOOTH_WINDOW`
- **Change popup dimensions**: Modify `POPUP_FIG_WIDTH_*` and `POPUP_FIG_HEIGHT` constants

### Testing Approach
No formal test framework; use manual test scripts in `tests/` directory. Run the application and verify:
- Window geometry persists across sessions
- Keyboard controls work (+/- for zoom)
- Double-click drill-down shows process popups
- Theme matches desktop (test in light and dark modes)
- No GdkPixbuf warnings appear in stderr
