# Changelog - sysmon.py

## 2025-12-05 - Enhanced Visual Scale Change Indicators & UI Improvements  [ v0.1.1 ]

### Added
- **Directional color-coded flash indicators**
  - Red flash (`#FFEBEE`) when Y-axis scale increases (KB→MB→GB, Kbps→Mbps→Gbps)
  - Blue flash (`#E3F2FD`) when Y-axis scale decreases (GB→MB→KB, Gbps→Mbps→Kbps)
  - Applies to both Disk I/O and Network graphs
  - Maintains existing flash duration (~500ms) and alternating pattern

### Improved
- **Visual feedback for scale changes**
  - More intuitive indication of load direction
  - Red indicates increasing activity/scale
  - Blue indicates decreasing activity/scale
  - Helps users quickly identify traffic patterns

- **UI title sizing**
  - Reduced main title font size from 16 to 12 points
  - Added `TITLE_FONT_SIZE` constant for maintainability
  - Creates more space for monitoring graphs while maintaining visual hierarchy
  - Bold font weight preserved for title prominence

### Technical Details
- Added `disk_flash_direction` and `net_flash_direction` instance variables
- Enhanced magnitude detection logic to track direction of change
- Updated flash color logic with conditional color selection
- Direction tracking resets after flash completes
- Added `TITLE_FONT_SIZE = 12` constant in Display & UI Constants section
- Backward compatible with existing flash behavior

## 2025-12-04 - Code Refactoring & Constants Implementation  [ v0.0.9c ]

### Added
- **Comprehensive constants system**
  - Added centralized constants section with 22 well-documented constants
  - Organized into logical groups: Data Storage, Timing, Display & UI, Unit Conversion, Process & Popup
  - All magic numbers replaced with descriptive constant names

### Improved
- **Code maintainability**
  - All hardcoded values now centralized for easy modification
  - Constants use descriptive names following Python conventions (UPPER_CASE)
  - Each constant includes clear documentation explaining its purpose
  - Ready for future user-configurable settings

- **Code readability**
  - Magic numbers like `200`, `1024`, `1000` replaced with `DATA_BUFFER_SIZE`, `BYTES_PER_KB`, `BITS_PER_KB`
  - Animation timing uses `ANIMATION_INTERVAL` instead of hardcoded `50ms`
  - Process sampling delay uses `PROCESS_SAMPLE_DELAY` instead of `0.2s`
  - UI dimensions use descriptive constants like `POPUP_FIG_WIDTH_CPU`

### Technical Details
- **Constants added (22 total):**
  - **Data Storage:** `DATA_BUFFER_SIZE`, `DEFAULT_TIME_WINDOW`, `DEFAULT_SMOOTH_WINDOW`
  - **Timing:** `ANIMATION_INTERVAL`, `PROCESS_SAMPLE_DELAY`, `TIME_WINDOW_STEP`, `MIN_TIME_WINDOW`, `MAX_TIME_WINDOW`
  - **Display & UI:** `CPU_MAX_PERCENT`, `DEFAULT_WINDOW_X/Y`, `FLASH_DURATION`
  - **Unit Conversion:** `BYTES_PER_KB/MB/GB`, `BITS_PER_KB/MB/GB`
  - **Process & Popup:** `TOP_PROCESSES_COUNT`, `MAX_SMOOTH_WINDOW`, `POPUP_FIG_*`, `POPUP_WINDOW_X/Y`

- **Updated components:**
  - Argument parser defaults now use constants
  - Validation ranges use `MAX_SMOOTH_WINDOW` constant
  - Help messages dynamically display constant values
  - All deque maxlen values use `DATA_BUFFER_SIZE`
  - Unit conversion functions use `BYTES_PER_*` and `BITS_PER_*`
  - Popup windows use dimension constants
  - Flash effects use `FLASH_DURATION`

### Benefits
- **Easier maintenance:** Change values in one location affects entire application
- **Better testing:** Constants can be easily modified for testing different configurations
- **Future configuration ready:** Constants can be exposed as user settings
- **Improved documentation:** Each constant explains its purpose and units
- **Consistent behavior:** Same values used consistently throughout codebase

## 2025-12-03 - X-axix behavior  [ v0.0.9b ]

## Fixed 
- **X-axis behavior 
  - X-axis now remains fixed at 0 to time window parameter instead of scrolling 
  - data scrolls left smoothly with full window coverage

## 2025-11-29 - Interactive Time Window Control

### Added
- **Interactive X-axis zoom control**
  - Press `+` or `=` to increase time window by 5 seconds (zoom out)
  - Press `-` to decrease time window by 5 seconds (zoom in)
  - Time window adjustable from 5 to 120 seconds
  - Default time window changed from 60 to 20 seconds
  - New command-line argument: `-t` or `--time-window` to set initial window
  - Real-time feedback printed to console when adjusting
  - Data buffer stores up to 200 seconds for smooth zooming

### Fixed
- **Y-axis dynamic scaling**
  - Y-axis now scales based only on data within the visible X-axis time window
  - Previously used all buffered data (up to 200 seconds)
  - Now responds immediately when zooming in/out with +/- keys
  - Provides more accurate scaling for the current view

## 2025-11-26 - Linux Compatibility & Theme Updates

### Fixed
- **Window geometry persistence on Linux**
  - Original code used Qt-specific methods that didn't work on Linux
  - Forced Qt5Agg backend for consistent behavior across systems
  - Removed conflicting Tk backend code
  - Window position and size now properly saved to `~/.sysmon_config.json`
  - Window restores to previous position/size on next launch
  - Used `atexit` handler to ensure geometry is saved even on abrupt close

### Added
- **Desktop theme inheritance**
  - Automatically detects system Qt theme (light/dark)
  - Applies theme colors to:
    - Figure and axes backgrounds
    - Text colors (labels, ticks, titles)
    - Grid lines and axes edges
    - Legend styling
  - Flash effect backgrounds now respect theme colors instead of hard-coded white
  - Application adapts to user's desktop environment appearance

- **Custom application icon**
  - Added support for `ICON_sysmon.png` and `ICON_sysmon.ico`
  - Icon set at Qt application level before window creation
  - Appears in taskbar and window title bar
  - Prefers PNG format for better Linux compatibility

- **GdkPixbuf warning suppression**
  - Implemented OS-level stderr filtering
  - Filters out harmless GdkPixbuf-CRITICAL warnings from GTK/Qt interaction
  - Uses pipe and background thread to intercept C library messages
  - Preserves all other error messages and Python exceptions

### Technical Details
- Added imports: `atexit`, `threading`, `QtWidgets`, `QtGui`
- New function: `_apply_qt_desktop_theme()` - Detects and applies Qt palette
- New function: `_filter_stderr()` - OS-level stderr filtering
- Backend forced to Qt5Agg at import time
- Icon loading handles both PNG and ICO formats with proper null checking
- Window geometry saved with x, y, width, height in JSON format

### Files Created
- `ICON_sysmon.png` - PNG version of application icon (converted from ICO)

### Configuration
- Config file location: `~/.sysmon_config.json`
- Config format:
  ```json
  {
    "x": <window_x_position>,
    "y": <window_y_position>,
    "window_size": [<width>, <height>]
  }
  ```

### Platform Notes
- Changes specifically tested and verified on Linux Mint Debian Edition (LMDE)
- Qt5 backend provides better Linux desktop integration than Tk
- All changes maintain backward compatibility with Windows (where originally developed)
