# Plan: Persist Graph Axis Inversion Setting in SysMon

## Problem
The "Invert Axis" setting accessible via right-click context menu on CPU/Disk/Net graphs works at runtime but doesn't persist to the configuration file. Users have to re-apply the setting every time they restart SysMon.

## Solution Overview
Add a shared axis inversion state to the existing preferences.json configuration system. All three graphs (CPU, Disk, Net) will share the same inversion setting for visual consistency. Following the established pattern used for other settings like transparency and always_on_top.

## Implementation Steps

### 1. Add Instance Variable (sysmon.py ~line 617 in __init__)
Add a single variable to track axis inversion state shared across all graphs:
```python
self.invert_axis = False
```

### 2. Connect to ViewBox State Change Signals (sysmon.py ~line 767, after plot creation)
After creating the three plots (cpu_plot, disk_plot, net_plot), connect to their ViewBox signals to detect axis changes. All three connect to the same handler:
```python
# Connect to state change signals to auto-save when user inverts axes
# All graphs share the same invert_axis setting
self.cpu_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
self.disk_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
self.net_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
```

### 3. Add Signal Handler Method (new method in sysmon.py)
Create a handler that captures state changes, applies to all graphs, and saves preferences:
```python
def on_axis_changed(self):
    # Get the state from whichever graph triggered the signal
    sender = self.sender()  # Get the ViewBox that triggered the signal
    state = sender.getState()
    new_invert_state = state.get('xInverted', False)

    # Only update if state actually changed to avoid recursion
    if new_invert_state != self.invert_axis:
        self.invert_axis = new_invert_state
        # Apply the same state to all three graphs
        self.cpu_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
        self.disk_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
        self.net_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
        # Save the preference
        self.save_preferences()
```

### 4. Update save_preferences() Method (sysmon.py ~line 1389-1404)
Add the axis inversion setting to the preferences dictionary:
```python
preferences = {
    'update_interval': self.update_interval,
    'time_window': self.time_window,
    'transparency': self.transparency,
    'always_on_top': self.always_on_top,
    'invert_axis': self.invert_axis  # ADD
}
```

### 5. Update load_window_geometry() Method (sysmon.py ~line 1337-1355)
Load the saved axis inversion state on startup:
```python
# After loading existing preferences (transparency, always_on_top, etc.)
self.invert_axis = prefs.get('invert_axis', False)
```

### 6. Apply Saved Settings to Plots (sysmon.py in load_window_geometry, after loading prefs)
Apply the loaded axis inversion state to all three plots:
```python
# Apply saved axis inversion state to all graphs
if self.invert_axis:
    self.cpu_plot.getPlotItem().getViewBox().invertX(True)
    self.disk_plot.getPlotItem().getViewBox().invertX(True)
    self.net_plot.getPlotItem().getViewBox().invertX(True)
```

## Critical Files
- **Main file:** `/home/juren/Projects/system-monitor/src/sysmon.py`
  - Lines ~617: __init__ (add instance variable)
  - Lines ~767: Plot creation (connect signals)
  - Lines 1337-1355: load_window_geometry (load and apply settings)
  - Lines 1389-1404: save_preferences (save settings)
  - New method: on_axis_changed (signal handler)

## Notes
- All three graphs (CPU, Disk, Net) share the same axis inversion state for visual consistency
- When user inverts axis on any graph, all three graphs are automatically synchronized
- Uses existing preferences.json file alongside other settings
- Follows the established pattern used for transparency and always_on_top preferences
- PyQtGraph's context menu continues to work as before - we just capture the state changes and sync them
- The sigStateChanged signal fires whenever any ViewBox state changes, but we only care about xInverted
- Recursion is prevented by checking if the new state differs from current state before applying changes
