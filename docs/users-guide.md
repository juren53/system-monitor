# SysMon Users Guide

**Version:** v0.2.8 (Production Release)  
**Updated:** 2025-12-23  

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Quick Start](#2-quick-start)
- [3. Main Interface](#3-main-interface)
- [4. Using the Graphs](#4-using-the-graphs)
- [5. Memory Display](#5-memory-display)
- [6. Drill-Down Analysis](#6-drill-down-analysis)
- [7. Configuration Menu](#7-configuration-menu)
- [8. Menu System Reference](#8-menu-system-reference)
- [9. Keyboard Shortcuts](#9-keyboard-shortcuts)
- [10. Troubleshooting](#10-troubleshooting)

---

## 1. Introduction

SysMon is a real-time system monitoring application that provides live visualization of CPU usage, disk I/O, and network activity. Built with PyQtGraph for high-performance graphics and professional system insights.

### What SysMon Monitors

- **CPU Usage**: Real-time processor utilization with percentage display
- **Disk I/O**: Read/write rates in megabytes per second
- **Network Activity**: Live data transfer rates for system interfaces
- **Memory Usage**: Current RAM and swap utilization with GB formatting
- **Process Analysis**: Top resource-consuming processes by category

### Key Benefits

- **High Performance**: 75-150x faster than matplotlib-based alternatives
- **Real-time Updates**: Smooth, responsive data visualization
- **Lightweight**: Minimal system resource footprint
- **Professional**: Clean interface with essential features
- **Cross-Platform**: Works on Windows, Linux, and macOS

---

## 2. Quick Start

### Installation

```bash
# Install required dependencies
pip install PyQt5 pyqtgraph psutil

# Run SysMon
python3 src/sysmon.py
```

### First Launch

When you first launch SysMon, you'll see:

1. **Main Window**: Real-time graphs for CPU, Disk I/O, and Network
2. **Memory Display**: Current RAM and Swap usage at the top
3. **Menu Bar**: File, Edit, View, Config, and Help menus
4. **Live Updates**: Data refreshes every 200ms by default

The application immediately starts monitoring and displays real-time system activity.

---

## 3. Main Interface

### Graph Areas

The main window displays three real-time graphs:

#### CPU Graph
- **Purpose**: Shows processor utilization percentage over time
- **Display**: Green line chart from 0-100%
- **Time Range**: Default 20 seconds of history

#### Disk I/O Graph
- **Purpose**: Shows disk read and write rates
- **Display**: Red line (read) and cyan line (write) in MB/s
- **Legend**: Identifies read vs write operations

#### Network Graph
- **Purpose**: Shows network send and receive rates
- **Display**: Pink line (sent) and blue line (received) in MB/s
- **Legend**: Identifies sent vs receive traffic

### Memory Display

Located at the top of the application:

- **RAM Usage**: Total GB, Available GB, Usage Percentage (blue text)
- **Swap Usage**: Total GB, Available GB, Usage Percentage (orange text)
- **Format**: Clean display (e.g., "15.6GB | 3.1GB | 79%")

---

## 4. Using the Graphs

### Reading Real-Time Data

All graphs update in real-time with smooth scrolling:

- **Time Axis**: Shows relative time (-20s to 0s)
- **Value Axis**: Scales automatically based on data range
- **Smooth Scrolling**: Data slides smoothly as time progresses

### Graph Controls

#### Double-Click for Analysis
- **Action**: Double-click any graph to show top 10 processes
- **Progress**: Analysis shows progress bar with cancellation option
- **Results**: Displays processes sorted by resource usage

#### Zoom and Navigation
- **Time Window**: Adjust how much history is displayed (5-120 seconds)
- **Grid**: Background grid for easier reading
- **Smoothness**: Anti-aliased rendering for clarity

### Data Accuracy

- **Update Interval**: 200ms (default) - balance of responsiveness and performance
- **Data Source**: psutil library for accurate system metrics
- **Calibration**: Automatic scaling based on observed data ranges

---

## 5. Memory Display

### Understanding Memory Metrics

#### RAM (Random Access Memory)
- **Total**: Installed physical memory
- **Available**: Currently unused memory
- **Usage**: Percentage of memory in use

#### Swap Memory
- **Purpose**: Virtual memory expansion when RAM is full
- **Usage**: Indicates system memory pressure
- **Performance**: High swap usage may indicate need for more RAM

### Memory Color Coding

- **Blue Text**: RAM information (physical memory)
- **Orange Text**: Swap information (virtual memory)
- **Real-time**: Updates automatically with system changes

---

## 6. Drill-Down Analysis

### Triggering Analysis

Double-click any graph to see detailed process analysis:

- **CPU Graph**: Top CPU consumers by percentage
- **Disk Graph**: Top disk I/O processes by megabytes transferred
- **Network Graph**: Top network-active processes by connection count

### Understanding Results

#### CPU Consumers Dialog
```
PID      Name                            CPU %
====================================================
1234     chrome                          45.3%
5678     firefox                         22.1%
9012     systemd                          8.7%
```

#### Disk I/O Dialog
```
PID      Name                            MB
====================================================
1234     chrome                        156.78
5678     firefox                        234.12
9012     systemd                        12.45
```

#### Network-Active Dialog
```
PID      Name                            Connections
====================================================
1234     chrome                                   23
5678     firefox                                   18
9012     systemd                                    0
```

### Performance Features

- **Async Processing**: Analysis runs in background without blocking UI
- **Progress Indication**: Real-time progress bar with percentage
- **Cancellation**: Cancel button to stop long-running analysis
- **Fast Results**: Complete analysis in <0.5 seconds typical

---

## 7. Configuration Menu

### Time Window Settings

**Config → Update Interval**
- **Range**: 50ms to 5000ms
- **Default**: 200ms (balanced responsiveness vs performance)
- **Impact**: Higher values = smoother graphs, lower = more responsive

**Config → Time Window**
- **Range**: 5 seconds to 300 seconds
- **Default**: 20 seconds of history
- **Effect**: Adjusts how much historical data is displayed

### Visual Settings

**Config → Window Transparency**
- **Range**: 10% to 100% opacity
- **Purpose**: See-through mode for desktop integration
- **Default**: 100% (fully opaque)

**Config → Always On Top**
- **Purpose**: Keep SysMon visible above other windows
- **Use Case**: Monitoring while working in other applications

### Data Management

**Config → Reset Settings**
- **Action**: Reset all preferences to defaults
- **Scope**: Time window, update interval, transparency, etc.

---

## 8. Menu System Reference

### File Menu

| Menu Item | Purpose | Description |
|------------|----------|-------------|
| Exit | Close Application | Exits SysMon and cleans up resources |

### Edit Menu

| Menu Item | Purpose | Description |
|------------|----------|-------------|
| Copy Graph Data | Export Data | Copies current graph data to clipboard |

### View Menu

| Menu Item | Purpose | Description |
|------------|----------|-------------|
| Show CPU | Focus Graph | Shows CPU graph in focus/center |
| Show Disk I/O | Focus Graph | Shows disk graph in focus/center |
| Show Network | Focus Graph | Shows network graph in focus/center |

### Config Menu

All configuration options are detailed in [Configuration Menu](#7-configuration-menu).

### Help Menu

| Menu Item | Purpose | Description |
|------------|----------|-------------|
| Users Guide | Documentation | Opens this comprehensive user guide |
| ChangeLog | Version History | Shows development history and changes |
| About | Application Info | Displays version, build info, and system details |

---

## 9. Keyboard Shortcuts

### System Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| Ctrl+S | Save Settings | Save current configuration |
| Ctrl+C | Copy Data | Copy graph data to clipboard |
| F11 | Toggle Fullscreen | Switch between normal/fullscreen mode |
| Esc | Close Dialog | Close active dialog window |

### Navigation Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| Alt+F | File Menu | Open File menu |
| Alt+E | Edit Menu | Open Edit menu |
| Alt+V | View Menu | Open View menu |
| Alt+C | Config Menu | Open Configuration menu |
| Alt+H | Help Menu | Open Help menu |

---

## 10. Troubleshooting

### Common Issues

#### Application Won't Start

**Problem**: SysMon fails to launch
**Solutions**:
1. Check Python version: Requires Python 3.7+
2. Install dependencies: `pip install PyQt5 pyqtgraph psutil`
3. Run from correct directory: `python3 src/sysmon.py`

#### Graphs Not Updating

**Problem**: Graphs appear frozen or don't update
**Solutions**:
1. Check system load: Very high CPU usage can cause update delays
2. Restart SysMon: Close and reopen the application
3. Check update interval: Default 200ms may need adjustment

#### Memory Display Inaccurate

**Problem**: Memory values seem incorrect
**Solutions**:
1. System delay: Values update every 200ms by default
2. Permissions: psutil may need elevated access on some systems
3. System compatibility: Different OS versions report data differently

#### Drill-Down Analysis Fails

**Problem**: Double-clicking graphs doesn't show results
**Solutions**:
1. Wait for analysis: Progress bar shows completion status
2. Check permissions: Some processes require elevated access
3. System load: Very high activity may slow analysis

### Performance Tips

#### For Better Performance

1. **Adjust Update Interval**: Increase from 200ms if system is slow
2. **Reduce Time Window**: Smaller time windows use less memory
3. **Close Other Apps**: SysMon needs CPU cycles for monitoring
4. **Check Background Processes**: Other monitoring tools can conflict

#### For Better Accuracy

1. **Run as Administrator**: Some systems require elevated access for process data
2. **Update Dependencies**: Keep psutil and PyQt5 current
3. **Check System Time**: Accurate time calculations depend on system clock

### Getting Help

#### Documentation Resources

- **This Guide**: Comprehensive user documentation you're reading now
- **ChangeLog**: Detailed version history in `docs/CHANGELOG.md`
- **About Dialog**: Version and system information from Help menu

#### Support Information

- **Source Code**: Available in project repository
- **Issue Reports**: Include system details and error messages
- **Feature Requests**: Submit via project issue tracker

---

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+, Linux, macOS 10.14+
- **Python**: Version 3.7 or higher
- **Memory**: 512MB RAM minimum, 2GB+ recommended
- **Display**: 1024x768 resolution minimum

### Recommended Requirements

- **Python**: Version 3.9+ for best compatibility
- **Memory**: 4GB+ RAM for smooth performance
- **Display**: 1280x720 or higher resolution
- **Graphics**: Hardware acceleration support

---

**Thank you for using SysMon!**

*This guide is maintained with each release. Check the Help menu for the latest version.*
*For technical details and development history, see `docs/CHANGELOG.md`.*
*SysMon is developed with focus on performance, accuracy, and user experience.*