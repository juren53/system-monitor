# SysMon - Real-time System Monitor

## Description
Comprehensive system monitoring application with real-time graphs for CPU, Disk I/O, and Network activity.

## Features
- Real-time monitoring with smooth scrolling graphs
- Interactive controls (time window adjustment, process drill-down)
- Cross-platform compatibility (Linux/Windows)
- Desktop theme inheritance
- Process resource analysis
- Window geometry persistence

## Installation
### Requirements
- Python 3.7+
- matplotlib
- psutil
- PyQt5

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
- `+` or `=`: Increase time window by 5 seconds
- `-`: Decrease time window by 5 seconds
- Double-click on graph: Show top 10 processes for that metric

## Configuration
Configuration saved to: `~/.sysmon_config.json`

## Version History
See [CHANGELOG.md](docs/CHANGELOG.md) for detailed version history.

## License
[License Name] - see [LICENSE](LICENSE) file for details.