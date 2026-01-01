# Plan: Real-Time Graph Smoothing Adjustment

## Overview
Add keyboard-driven real-time smoothing to SysMon graphs using a moving average filter. Users press **'+'** to increase smoothing and **'-'** to decrease it, with visual feedback showing the current smoothing level.

## Current State Analysis

### Existing Code (sysmon.py)
- **No smoothing currently applied** - raw data from psutil is displayed directly
- Data collection: `update_data()` (line 2177) collects raw CPU%, disk I/O, network rates
- Data storage: `deque` collections hold raw values (cpu_data, disk_read_data, etc.)
- Plot update: `update_plots()` (line 2236) renders data without filtering
- Keyboard handler: `keyPressEvent()` (line 2375) handles T, M, Q, arrow keys

### Similar Existing Features
- **Time Window Adjustment**: `increase_time_window()` / `decrease_time_window()` methods exist (lines 2255-2263)
  - Adjust by 5 seconds, range 5-120s
  - NOT keyboard accessible (only via menu)
- **Transparency Toggle**: 'T' key toggles between 100% and 50% opacity
- **Position Keys**: Arrow keys, M key, Q key already implemented

## Implementation Plan

### 1. Add Smoothing Window Instance Variable
**Location**: `SystemMonitor.__init__()` (line 1528)

```python
# Add after line 1560 (after _transparency_toggled)
self.smoothing_window = 1  # Number of data points to average (1 = no smoothing)
self.min_smoothing = 1     # Minimum smoothing (raw data)
self.max_smoothing = 20    # Maximum smoothing (20-point moving average)
```

**Why**: Track the current smoothing level, defaults to 1 (no smoothing/raw data)

### 2. Create Moving Average Helper Method
**Location**: After `update_plots()` method (around line 2254)

```python
def apply_smoothing(self, data):
    """Apply moving average smoothing to data

    Args:
        data: List or deque of numeric values

    Returns:
        List of smoothed values (same length as input)
    """
    if self.smoothing_window <= 1 or len(data) < 2:
        return list(data)

    smoothed = []
    window = min(self.smoothing_window, len(data))

    for i in range(len(data)):
        # Calculate average of current point and previous points
        start_idx = max(0, i - window + 1)
        window_data = list(data)[start_idx:i+1]
        avg = sum(window_data) / len(window_data)
        smoothed.append(avg)

    return smoothed
```

**Why**: Implements simple moving average (SMA) - each point is average of itself + previous N points

**Algorithm**: For window size 5 at index i, average data[i-4:i+1]

### 3. Modify update_plots() to Apply Smoothing
**Location**: `update_plots()` method (line 2236)

**Current code** (line 2245):
```python
self.cpu_curve.setData(time_array, list(self.cpu_data))
```

**Replace with**:
```python
# Apply smoothing to all data series
cpu_smoothed = self.apply_smoothing(self.cpu_data)
disk_read_smoothed = self.apply_smoothing(self.disk_read_data)
disk_write_smoothed = self.apply_smoothing(self.disk_write_data)
net_sent_smoothed = self.apply_smoothing(self.net_sent_data)
net_recv_smoothed = self.apply_smoothing(self.net_recv_data)

# Update curves with smoothed data
self.cpu_curve.setData(time_array, cpu_smoothed)
self.disk_read_curve.setData(time_array, disk_read_smoothed)
self.disk_write_curve.setData(time_array, disk_write_smoothed)
self.net_sent_curve.setData(time_array, net_sent_smoothed)
self.net_recv_curve.setData(time_array, net_recv_smoothed)
```

**Why**: Applies smoothing to all 5 data series before rendering

### 4. Add Keyboard Shortcuts for Smoothing Adjustment
**Location**: `keyPressEvent()` method (line 2375)

**Add before the `else:` clause** (before line 2390):
```python
elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
    self.increase_smoothing()
elif event.key() == Qt.Key_Minus:
    self.decrease_smoothing()
```

**Why**:
- '+' key increases smoothing (also works with '=' for no-shift access)
- '-' key decreases smoothing
- Follows convention of +/- for increment/decrement

### 5. Create Smoothing Adjustment Methods
**Location**: After `update_time_window()` method (around line 2281)

```python
def increase_smoothing(self):
    """Increase smoothing window by 1 point"""
    if self.smoothing_window < self.max_smoothing:
        self.smoothing_window += 1
        self.show_smoothing_status()
        self.save_preferences()

def decrease_smoothing(self):
    """Decrease smoothing window by 1 point"""
    if self.smoothing_window > self.min_smoothing:
        self.smoothing_window -= 1
        self.show_smoothing_status()
        self.save_preferences()

def show_smoothing_status(self):
    """Display current smoothing level as status message"""
    if self.smoothing_window == 1:
        status_msg = "Smoothing: OFF (Raw data)"
    else:
        # Calculate approximate time window for smoothing
        time_span = (self.smoothing_window * self.update_interval) / 1000
        status_msg = f"Smoothing: {self.smoothing_window}-point ({time_span:.2f}s window)"

    # Display in window title briefly
    original_title = self.windowTitle()
    self.setWindowTitle(f"SysMon - {status_msg}")

    # Reset title after 2 seconds
    QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))
```

**Why**:
- Adjusts by 1 point at a time for fine control
- Range: 1 (no smoothing) to 20 (heavy smoothing)
- Shows visual feedback via window title
- Saves preference immediately

**User Feedback Details**:
- Example at window=5, interval=200ms: "Smoothing: 5-point (1.00s window)"
- Window title shows status for 2 seconds, then reverts

### 6. Persist Smoothing Preference
**Location**: Multiple locations for save/load

#### A. Update save_preferences() (line 2596)
**Add** to preferences dictionary:
```python
preferences = {
    'update_interval': self.update_interval,
    'time_window': self.time_window,
    'transparency': self.transparency,
    'always_on_top': self.always_on_top,
    'invert_axis': self.invert_axis,
    'smoothing_window': self.smoothing_window  # NEW
}
```

#### B. Update load_config() (line 2517)
**Add** after line 2520:
```python
self.smoothing_window = prefs.get('smoothing_window', 1)
```

#### C. Update reset_settings() (line 2688)
**Add** after line 2694:
```python
self.smoothing_window = 1  # Reset to no smoothing
```

**Why**: User's smoothing preference persists across sessions

### 7. Add Menu Option (Optional Enhancement)
**Location**: Config menu creation (around line 2117)

**Add** after Time Window Settings action:
```python
smoothing_action = QAction('&Smoothing Level...', self)
smoothing_action.setStatusTip('Configure graph smoothing level')
smoothing_action.triggered.connect(self.change_smoothing_level)
config_menu.addAction(smoothing_action)
```

**And add method** (around line 2765):
```python
def change_smoothing_level(self):
    """Configure smoothing level via dialog"""
    level, ok = QInputDialog.getInt(
        self, 'Smoothing Level',
        'Smoothing window (data points):\n1 = No smoothing (raw data)\nHigher = More smoothing',
        self.smoothing_window, 1, 20, 1)

    if ok:
        self.smoothing_window = level
        self.show_smoothing_status()
        self.save_preferences()
```

**Why**: Provides GUI alternative for users who prefer menus over keyboard

## Technical Details

### Moving Average Algorithm
- **Type**: Simple Moving Average (SMA)
- **Window**: User-adjustable 1-20 points
- **Edge handling**: Use available points at start (graceful degradation)
- **Performance**: O(n*w) where n=data points, w=window size (acceptable for typical n≈100-600)

### Smoothing Window Examples
| Window | Update Interval | Time Span | Effect |
|--------|----------------|-----------|--------|
| 1 | 200ms | N/A | No smoothing (raw data) |
| 3 | 200ms | 0.6s | Minimal smoothing (light noise reduction) |
| 5 | 200ms | 1.0s | Light smoothing (good for CPU spikes) |
| 10 | 200ms | 2.0s | Medium smoothing (steady trends) |
| 20 | 200ms | 4.0s | Heavy smoothing (very smooth, delayed response) |

### Performance Impact
- **Negligible**: 5 smoothing operations per update (5 data series)
- **Max cost**: 20-point window on 600-point dataset = ~6,000 additions per update
- **Update rate**: 200ms interval = plenty of time for computation

### User Experience Flow
1. User presses **'+'** key
2. `smoothing_window` increases from 1 → 2
3. Window title shows: "SysMon - Smoothing: 2-point (0.40s window)"
4. All graphs immediately display smoothed data
5. After 2 seconds, title reverts to "SysMon - PyQtGraph Edition"
6. Setting saved to preferences.json

## Testing Checklist
- [ ] Test smoothing=1 (no smoothing, raw data)
- [ ] Test smoothing=5 (moderate smoothing)
- [ ] Test smoothing=20 (maximum smoothing)
- [ ] Test '+' key increments up to max (20)
- [ ] Test '-' key decrements down to min (1)
- [ ] Test '+' at max does nothing (stays at 20)
- [ ] Test '-' at min does nothing (stays at 1)
- [ ] Verify status message displays correctly
- [ ] Verify preference saves and loads across restart
- [ ] Test with different update intervals (50ms, 200ms, 1000ms)
- [ ] Verify all 5 graphs smooth correctly (CPU, disk R/W, net S/R)

## Documentation Updates Required

### 1. docs/keyboard-shortcuts.md
Add to keyboard shortcuts list:
```markdown
### Graph Control
- **+** - Increase smoothing (reduce noise, lag increases)
- **-** - Decrease smoothing (more responsive, more noise)
```

### 2. docs/CHANGELOG.md
New entry for v0.2.18:
```markdown
## 2025-12-31 XXXX CST - Real-Time Graph Smoothing  [ v0.2.18 ]

### 📊 **NEW FEATURE: Keyboard-Controlled Graph Smoothing**
- **Shortcut Keys**: Press **'+'** to increase smoothing, **'-'** to decrease
- **Smoothing Range**: 1 (no smoothing) to 20 points (heavy smoothing)
- **Visual Feedback**: Window title shows current smoothing level for 2 seconds
- **Persistence**: Smoothing preference saved to preferences.json

### 📝 **Implementation Details**
- Added simple moving average (SMA) filter to all 5 data series
- Created `apply_smoothing()` method for filtering
- Added keyboard handlers for +/- keys in `keyPressEvent()`
- Added `increase_smoothing()` and `decrease_smoothing()` methods
- Status display via temporary window title change
- Optional menu item in Config menu

### 🎯 **Use Cases**
- Reduce noise on busy systems (CPU spikes, disk bursts)
- Smooth out network fluctuations for clearer trends
- Trade-off: More smoothing = clearer trends but slower response
- Quick adjustment without leaving main window
```

### 3. CLAUDE.md
Update "Key Features" section to mention smoothing:
```markdown
**Real-time drill-down dialogs** (v0.2.15):
- Live-updating top 10 process lists with sortable columns
- Adjustable update intervals (1-60 seconds, default 3s)
- Process filtering by name or PID
- Pause/Resume controls for snapshot analysis

**Keyboard-controlled smoothing** (v0.2.18):
- +/- keys adjust moving average filter (1-20 points)
- Real-time smoothing of all graphs
- Visual feedback via status display
```

## Code Changes Summary
- **Lines added**: ~80-100
- **Files modified**: 1 (sysmon.py only)
- **New methods**: 4 (apply_smoothing, increase_smoothing, decrease_smoothing, show_smoothing_status, optional: change_smoothing_level)
- **Modified methods**: 3 (keyPressEvent, update_plots, save_preferences, load_config, reset_settings)
- **New instance variables**: 3 (smoothing_window, min_smoothing, max_smoothing)

## Alternative Approaches Considered

### Option A: Exponential Moving Average (EMA)
- **Pro**: Less memory, better for real-time streams
- **Con**: More complex, harder for users to understand
- **Decision**: Use SMA for simplicity

### Option B: Adjust Time Window Instead
- **Pro**: Already implemented methods exist
- **Con**: Changes visible history, not true "smoothing"
- **Decision**: Keep time window separate, implement true data smoothing

### Option C: Gaussian Smoothing
- **Pro**: Better preservation of features
- **Con**: Requires scipy/numpy, adds dependency complexity
- **Decision**: Use SMA (no new dependencies)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation with high smoothing | Low | O(n*w) complexity acceptable for n≈600, w≤20 |
| User confusion about smoothing vs time window | Medium | Clear status messages showing time span |
| Smoothed data hides important spikes | Medium | Default to smoothing=1 (off), user must enable |
| Preference file corruption | Low | Default to smoothing=1 if load fails |

## Future Enhancements (Not in Scope)
- [ ] Per-graph smoothing (different smoothing for CPU vs Network)
- [ ] Smoothing algorithm selection (SMA vs EMA vs Gaussian)
- [ ] Visual indicator on graphs showing smoothing level
- [ ] Keyboard shortcut cheat sheet (press 'H' to show)
- [ ] Separate smoothing for each metric type

---

**Plan Status**: Ready for implementation
**Estimated Implementation Time**: 45-60 minutes
**Compatibility**: Linux, Windows, macOS (pure Python, no platform-specific code)
