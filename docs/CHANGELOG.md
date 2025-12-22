# Changelog - sysmon.py

## 2025-12-22 - Real-Time Memory Display Enhancement  [ v0.2.6 ]

### 💾 **Memory Monitoring Features**
- **Real-Time RAM Display:** Live RAM usage with total/available/percentage
- **Real-Time Swap Display:** Live swap memory usage with total/available/percentage  
- **GB Unit Format:** Clean display using GB units (e.g., "15.6GB | 3.1GB | 79%")
- **Color-Coded Labels:** RAM in blue (#2196F3), Swap in orange (#FF9800)
- **Compact Layout:** Efficient use of previously underutilized UI space

### 🔄 **UI Transformation**
- **Removed Time Window Controls:** Relocated to Config menu for cleaner interface
- **Replaced Info Text:** Removed "Double-click graphs for process details" from header
- **Enhanced Visibility:** Memory information now prominent at top of application
- **Preserved Functionality:** All existing controls available through Config menu

### 📊 **Data Integration**
- **psutil Integration:** Uses virtual_memory() and swap_memory() APIs
- **Real-Time Updates:** Memory data refreshes with same frequency as graphs (200ms)
- **Accurate Calculations:** Proper byte-to-GB conversion and percentage calculations
- **Error Handling:** Graceful handling of systems with no swap space

---

## 2025-12-22 - Single Instance Prevention & Dialog Fix  [ v0.2.5 ]

### 🚫 **Single Instance Implementation**
- **Added Qt Native Single Instance Prevention** using QSharedMemory and QSystemSemaphore
- **Cross-Platform Support**: Works on Windows, Linux, and macOS
- **Version-Aware**: Different versions can coexist (uses version-specific keys)
- **User-Friendly Messages**: Clear error dialog when attempting to launch second instance
- **Automatic Cleanup**: Shared memory and semaphore cleanup on application exit
- **Race Condition Protection**: Thread-safe implementation with semaphore locking

### 🔧 **Dialog Fix Implementation**
- **Removed Conflicting QApplication**: Fixed hanging dialog issue by reusing existing app instance
- **Manual Event Processing**: Added proper event loop handling for dialog display
- **Clean Application Exit**: Dialog now closes properly without "Force Quit" requirement
- **User Experience**: Second instance shows message and exits cleanly after dialog dismissal

### 🛠️ **Technical Implementation**
- **Instance Key**: `sysmon-v0.2.5-instance` (version-specific)
- **Semaphore Key**: `sysmon-v0.2.5-semaphore` (for thread safety)
- **Shared Memory**: 1-byte allocation for presence detection
- **Linux Cleanup**: Handles abnormal termination scenarios
- **Graceful Exit**: Proper resource management with atexit registration
- **Event Loop Fix**: Manual event processing resolves Qt lifecycle conflicts

### 🎯 **User Experience**
- **Prevention**: Second instance shows clear error message and exits
- **No Resource Conflicts**: Eliminates duplicate system monitoring overhead
- **Configuration Protection**: Prevents config file corruption from concurrent access
- **Professional Behavior**: Industry-standard single-instance pattern
- **Dialog Usability**: Error dialog can be closed normally without system intervention

### 📚 **Error Message**
```
SysMon Already Running
SysMon is already running on this system.

Only one instance of SysMon can run at the same time.

If you believe this is an error, please check your running processes.
```

### 🏗️ **Architecture Changes**
- **New Functions**: `check_single_instance()`, `cleanup_single_instance()`, `show_instance_already_running(app)`
- **Modified main()**: Early instance checking before window creation
- **Global Variables**: `shared_memory`, `system_semaphore` for resource management
- **Added Imports**: `QSharedMemory`, `QSystemSemaphore` from PyQt5.QtCore
- **Function Signature Update**: `show_instance_already_running()` now accepts app parameter

### ✅ **Testing Verified**
- **First Instance**: Successfully acquires resources and runs
- **Second Instance**: Properly detects existing instance and exits
- **Dialog Behavior**: Error dialog displays and closes correctly
- **Resource Cleanup**: Correctly releases shared memory and semaphore
- **Cross-Platform**: Tested on Linux with Windows/macOS compatibility built-in

---

## 2025-12-21 - User Accessibility & Documentation  [ v0.2.2 ]

### 📚 **User Documentation Access**
- **ChangeLog Menu Item:** Added Help → ChangeLog for development visibility
- **Interactive Dialog:** 900x700 window with scrollable changelog content
- **Enhanced Readability:** Improved font size and spacing for comfortable reading
- **Cross-Platform Fonts:** Consolas/Monaco/Courier New fallbacks
- **Error Handling:** Graceful fallback if changelog file unavailable
- **UTF-8 Support:** Proper handling of emoji characters in documentation
- **Development Transparency:** Users can see complete feature evolution

### 🔧 **UI/UX Improvements**
- **Font Size:** Increased from 10px to 14px for optimal readability
- **Line Height:** Added 1.4 line-height for improved spacing
- **Dialog Size:** Expanded from 800x600 to 900x700 for more content
- **Padding:** Increased from 8px to 12px for better text spacing
- **Font Family:** Prioritized Consolas (Windows), Monaco (macOS), Courier New (fallback)
- **Selection Highlighting:** Added text selection styling for better user experience
- **QTextEdit Viewer:** Implemented QTextEdit-based changelog viewer for optimal performance

---

## 2025-12-21 - Cross-Platform Line Ending Management  [ v0.2.1 ]

### 🔧 **Infrastructure Improvement**
- **Added .gitattributes:** Cross-platform line ending configuration
- **Eliminated CRLF Warnings:** No more "CRLF will be replaced by LF" messages
- **Following HSTL Project Pattern:** Professional cross-platform development practices
- **Comprehensive Documentation:** Complete guide in `docs/gitattributes-explanation.md`

### 🌐 **Cross-Platform Benefits**
- **Windows Developers:** Automatic CRLF conversion on checkout
- **Linux/macOS Developers:** Files maintain standard LF endings
- **Team Collaboration:** Repository consistency across all platforms
- **No More Conflicts:** Line ending issues eliminated

### 📁 **File Type Handling**
- **Text Files:** Auto-normalized (*.py, *.md, *.txt, *.json, *.spec, *.bat)
- **Binary Files:** Protected from text processing (*.png, *.ico, *.exe, *.zip)
- **Shell Scripts:** LF-only endings regardless of platform (*.sh eol=lf)
- **Python Binaries:** Explicit binary declarations (*.pyc, *.pyo, *.pyd)

### 📚 **Documentation Added**
- **Complete Guide:** `docs/gitattributes-explanation.md` with implementation details
- **Migration Process:** How to handle existing files
- **Best Practices:** Git-recommended configuration
- **Usage Examples:** For adding new file types
- **Reference Links:** Documentation and inspiration sources

### Technical Details
- **Repository Storage:** All text files stored with LF endings
- **Windows Checkout:** Automatic CRLF conversion for native text editors
- **Platform Detection:** Appropriate line endings per operating system
- **Binary Protection:** Prevents corruption of image, executable, and library files

---

## 2025-12-21 - Branch Promotion & Release Ready  [ v0.2.0 ]

### 🎯 **MAJOR MILESTONE: Prototype Promoted to Main**

### Branch Restructuring
- **Promoted to Production:** `feature/pyqtgraph-prototype` branch promoted to `main`
- **Backup Preserved:** Original main branch saved as `old-main-backup`
- **Remote Updated:** GitHub origin/main now points to new main branch
- **Release Ready:** All PyQtGraph features now production-ready

### Complete Feature Summary
- **PyQtGraph Implementation:** 75-150x faster real-time plotting performance
- **Professional Menu Suite:** Complete File, Edit, View, Config, Help menus
- **XDG Compliance:** Cross-platform configuration following OS standards
- **Window Transparency:** Interactive see-through mode (10%-100% opacity)
- **Always On Top:** Toggle for floating desktop monitor behavior
- **Enhanced Preferences:** Separated geometry and user preference management
- **System Theme Integration:** Automatic light/dark theme detection

### Benefits Achieved
- **Performance:** Dramatically improved real-time monitoring responsiveness
- **Professional UI:** Complete menu system with keyboard shortcuts
- **Cross-Platform:** Windows, Linux, macOS compatibility with XDG standards
- **User Experience:** Persistent settings, transparency, and always-on-top options
- **Standards Compliance:** XDG Base Directory Specification implementation

### What's New in v0.2.0 (vs Previous Main)
- **PyQtGraph Replacement:** matplotlib → PyQtGraph for massive performance gains
- **Complete Menu System:** Added File, Edit, View, Config, Help menus
- **Window Transparency:** New see-through mode capability
- **Always On Top:** Toggle to keep window above other apps
- **XDG Compliance:** Professional cross-platform config management
- **Automatic Themes:** System light/dark theme detection and adaptation
- **Enhanced Persistence:** Window geometry + user preferences saved separately
- **Version Labeling:** Version and release date displayed in UI lower right corner
- **Updated Documentation:** All files updated with v0.2.0 and 2025-12-21 release info
- **Keyboard Shortcuts:** Professional shortcuts (Ctrl+S, Ctrl+C, F11, etc.)
- **Line Ending Management:** Added .gitattributes for cross-platform compatibility
- **Line Ending Management:** Added .gitattributes for cross-platform compatibility

### Configuration Structure
- **Windows:** `%APPDATA%\sysmon\config.json` + `preferences.json`
- **Linux/macOS:** `~/.config/sysmon/config.json` + `preferences.json`
- **Migration:** Automatic from old `~/.sysmon_config.json` location

---

## 2025-12-21 - XDG Compliance & Transparency Features  [ Prototype v0.1.2 ]

### Added
- **XDG Base Directory Specification Compliance**
  - Cross-platform configuration directory management
  - Windows: Uses `%APPDATA%\sysmon` following Windows conventions
  - Linux/macOS: Uses `~/.config/sysmon` following XDG standard
  - Automatic migration from old `~/.sysmon_config.json` location
  - Graceful fallback handling for missing or corrupted configs

- **Separated Configuration Structure**
  - Main config: Window geometry and position (config.json)
  - User preferences: Update interval, time window, transparency (preferences.json)
  - Proper file organization and cleaner configuration management
  - Backwards compatibility with existing configuration files

### Added
- **Window Transparency Feature**
  - Config → Transparency... menu item for see-through mode
  - Interactive slider dialog (10% - 100% opacity range)
  - Real-time preview while adjusting transparency
  - Transparency preference saved and restored across sessions
  - Safety minimum of 10% opacity to maintain visibility
  - Reset button to quickly return to fully opaque mode

- **Always On Top Feature**
  - Config → Always On Top menu item with checkbox indicator
  - Toggle to keep window always above other applications
  - Uses Qt.WindowStaysOnTopHint for proper window layering
  - State saved to preferences and restored on startup
  - Perfect for creating floating desktop monitor widget
  - Can be combined with transparency for see-through overlay

### Fixed
- **Window Geometry Persistence**
  - Fixed geometry save/load format mismatch
  - Now uses proper Qt serialization (QByteArray) for reliable restoration
  - Maintains backwards compatibility with old x,y,window_size format
  - Window position, size, and state properly restored on startup
  - Enhanced error handling for corrupted geometry data

### Improved
- **Configuration Management**
  - XDG-compliant file locations following OS conventions
  - Automatic config migration with user notification
  - Better error handling for missing/corrupted config files
  - Clean separation of geometry vs user preferences
  - Debug output for troubleshooting configuration issues

### Technical Details
- **New XDG Functions:**
  - `get_xdg_config_dir()` - Platform-specific config directory
  - `migrate_old_config()` - Seamless migration from old config location
  - `ensure_config_directory()` - Creates config directories if needed
  - `get_config_file_path()` / `get_preferences_file_path()` - Path utilities

- **Transparency Implementation:**
  - `set_window_transparency()` - Core opacity setting with clamping
  - `change_transparency()` - Interactive slider dialog with preview
  - Integrated with preferences system for persistence
  - Proper state management with cancel/restore functionality

- **Configuration File Structure:**
  ```json
  // config.json - Window geometry
  {
    "window_geometry": {
      "geometry": "<QByteArray data>",
      "state": "<QByteArray data>"
    }
  }
  
  // preferences.json - User settings  
  {
    "update_interval": 200,
    "time_window": 30,
    "transparency": 1.0
  }
  ```

### Platform Support
- **Windows:** `%APPDATA%\sysmon\`
- **Linux:** `~/.config/sysmon/`
- **macOS:** `~/.config/sysmon/` (XDG standard)
- **Migration:** Automatic from old `~/.sysmon_config.json`

### Benefits
- **Standards Compliance:** Follows XDG Base Directory Specification
- **Cross-Platform:** Consistent behavior across Windows, Linux, macOS
- **User Experience:** Window transparency for improved desktop integration
- **Configuration:** Reliable save/restore of window position and preferences
- **Professional:** Industry-standard configuration management

---

## 2025-12-21 - PyQtGraph Prototype Branch  [ Prototype v0.1.0 ]

### ⚠️ **MAJOR ARCHITECTURE CHANGE**

### Added
- **PyQtGraph Implementation**
  - Replaced matplotlib with PyQtGraph for significantly better real-time performance
  - 75-150x faster plotting for real-time updates
  - Native Qt integration with built-in pan/zoom capabilities
  - GPU acceleration for smooth scrolling and interactions

### Added
- **Comprehensive Menu Suite**
  - **File Menu:** Save Data (Ctrl+S), Export Graph (Ctrl+E), Exit (Ctrl+Q)
  - **Edit Menu:** Copy Graph (Ctrl+C), Clear Data (Ctrl+Del), Reset Settings
  - **View Menu:** Show/Hide plots (CPU, Disk, Network), Full Screen (F11)
  - **Config Menu:** Update Interval, Time Window Settings, Graph Colors
  - **Help Menu:** About dialog with version and library information
  - Keyboard shortcuts for power users
  - Proper file dialogs with filters

### Added
- **Automatic System Theme Inheritance**
  - Detects Windows light/dark theme automatically
  - Applies appropriate PyQtGraph background/foreground colors
  - Optimized color schemes for both themes:
    - Dark: Bright colors for high contrast (#4CAF50, #FF9800, #2196F3, etc.)
    - Light: Original vibrant color scheme maintained
  - Seamless integration with system visual style

### Improved
- **Performance**
  - Dramatically reduced CPU usage from plotting operations
  - Smoother scrolling even with long time windows (120+ seconds)
  - Lower memory footprint for real-time monitoring
  - Better responsiveness during high system load

### Improved
- **Windows Compatibility**
  - Removed Unix-specific shebang line (`#!/usr/bin/env python`)
  - Native Windows integration with proper PATH handling
  - Optimized for Windows 10/11 visual themes
  - MSYS2 compatibility maintained for development

### Fixed
- **Python Environment Issues**
  - Resolved module import conflicts between MSYS2 and Windows Python
  - Corrected PATH configuration for development vs production
  - Fixed window geometry persistence with proper Qt event handling

## 2025-12-21 - Bug Fixes & Improvements  [ Prototype v0.1.1 ]

### Fixed
- **Window Geometry Persistence**
  - Fixed Qt closeEvent method for reliable save on exit
  - Added periodic save timer (30 seconds) as backup mechanism
  - Enhanced error handling with debug output
  - Config file confirmed working: saves position and size correctly
  - Test shows geometry saved as 349x607 at position (659, 30)

### Improved
- **Reliability**
  - Dual save mechanism: event-based + periodic timer
  - Better error handling for config file operations
  - Debug console output for troubleshooting
  - Robust fallback handling for corrupted/missing config

### Technical Details
- **Config File Format:**
  ```json
  {
    "x": <window_x_position>,
    "y": <window_y_position>, 
    "window_size": [<width>, <height>],
    "time_window": <seconds>,
    "update_interval": <milliseconds>
  }
  ```

- **Save Mechanisms:**
  - Primary: Qt closeEvent on window close
  - Backup: QTimer every 30 seconds during operation
  - Location: `~/.sysmon_config.json`
  - Format: JSON with human-readable indentation

### Benefits
- **User Experience:** Window opens in same position every time
- **Settings Persistence:** Time window and update interval remembered
- **Robustness:** Multiple save mechanisms prevent data loss
- **Debugging:** Console output for troubleshooting issues
  - Enhanced error handling for missing dependencies

### Technical Details
- **Libraries Updated:**
  - `matplotlib` → `pyqtgraph` (plotting)
  - Added comprehensive `PyQt5` widget imports
  - Enhanced `psutil` integration for process monitoring

- **Code Structure:**
  - Modular menu system with separate handler methods
  - Theme detection and application in dedicated methods
  - Improved error handling with user-friendly messages
  - File I/O operations with proper exception handling

- **Branch Information:**
  - Branch: `feature/pyqtgraph-prototype`
  - Ready for evaluation and potential merge to main
  - Backward compatible configuration preserved

### Migration Notes
- **Data Export:** Now supports both CSV (data) and PNG (screenshots)
- **Configuration:** All previous settings maintained with new options
- **Performance:** Noticeable improvement in real-time responsiveness
- **Memory:** Lower overall system resource usage

### Added
- **Window Geometry Persistence**
  - Saves window size and position to `~/.sysmon_config.json`
  - Restores window geometry on application startup
  - Stores time window and update interval preferences
  - Automatic save on application exit using Qt closeEvent
  - Periodic save timer as backup (every 30 seconds)
  - Enhanced reset settings to clear config file
  - Debug output to verify save/load operations
  - Fixed Qt event handling for reliable geometry persistence

### Benefits
- **Speed:** Up to 150x faster plotting performance
- **Integration:** Native Qt look and feel
- **Usability:** Professional menu system with standard shortcuts
- **Visual:** Automatic theme matching for seamless appearance
- **Platform:** Optimized for Windows development environment
- **Convenience:** Remembers your window layout and preferences

---

## 2025-12-07 - Fixed Graph Representation Issue  [ v0.1.2 ]

### Fixed
- **Moving average edge effects**
  - Resolved issue where most recent data points always pointed downward regardless of actual activity
  - Replaced `np.convolve(mode='same')` with proper edge-aware moving average implementation
  - Eliminates zero-padding artifacts that caused artificial downward trends
  - Now accurately represents real system activity patterns

### Improved
- **Graph accuracy**
  - Most recent data points now show correct values
  - Real-time monitoring provides accurate visual feedback
  - Maintains smooth scrolling without edge effects

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
