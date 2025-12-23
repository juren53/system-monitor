# SysMon - Real-time System Monitor

**Version:** v0.2.7 (Production Release)
**Release Date:** 2025-12-23

## Description
Comprehensive system monitoring application with real-time graphs for CPU, Disk I/O, and Network activity. Built with PyQtGraph for high-performance real-time visualization.

## Features
- **Real-time monitoring** with smooth scrolling graphs (75-150x faster than matplotlib)
- **Live memory display** showing RAM and Swap usage in real-time
- **Professional menu system** with File, Edit, View, Config, Help menus
- **Window transparency** for see-through mode (10%-100% opacity control)
- **Always On Top** toggle for floating desktop monitor
- **XDG compliance** for cross-platform configuration management
- **Cross-platform compatibility** (Windows, Linux, macOS)
- **Automatic system theme** detection (light/dark mode)
- **Process resource analysis** with drill-down capability
- **Window geometry persistence** with XDG-compliant configuration
- **Keyboard shortcuts** for power users (Ctrl+S, Ctrl+C, F11, etc.)

## Installation
### Requirements
- Python 3.7+
- PyQt5
- PyQtGraph
- psutil
- (matplotlib no longer required - replaced with PyQtGraph)

### Install Dependencies
```bash
pip install matplotlib psutil PyQt5
```

### Run Application
```bash
python3 src/sysmon.py
```

## Usage
### Command Line Options
- `-s, --smooth-window`: Smoothing window size (1-20, default: 5)
- `-t, --time-window`: Time window in seconds (5-120, default: 20)

### Interactive Controls
- Double-click on graph: Show top 10 processes for that metric
- Config menu: Time window settings, transparency, always-on-top

## Configuration
Configuration saved to: `~/.sysmon_config.json`

## Version History
See [CHANGELOG.md](docs/CHANGELOG.md) for detailed version history.

## License
[License Name] - see [LICENSE](LICENSE) file for details.