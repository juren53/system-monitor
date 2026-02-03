# Plan: Add Adjustable Graph Line Thickness

## Overview
Add user-adjustable graph line thickness to the Config menu, placed under Graph Colors. Currently, line width is hardcoded to `width=2` in all `pg.mkPen()` calls.

## Implementation

### 1. Add Menu Item (src/sysmon.py ~line 2213)
After the Graph Colors menu action, add a new "Line Thickness..." action:
```python
line_thickness_action = QAction('Line &Thickness...', self)
line_thickness_action.setStatusTip('Adjust graph line thickness')
line_thickness_action.triggered.connect(self.customize_line_thickness)
config_menu.addAction(line_thickness_action)
```

### 2. Add Instance Variable (src/sysmon.py ~line 1545)
Add `self.line_thickness = 2` as default in `__init__`, near other graph-related variables.

### 3. Create Dialog Function (~after line 3154)
Add `customize_line_thickness()` method:
- Create QDialog with QSpinBox (range 1-10, default 2)
- Preview label showing sample line
- Apply and Cancel buttons
- On Apply: update `self.line_thickness`, call `apply_line_thickness()`, save preference

### 4. Create Apply Function (~after customize_line_thickness)
Add `apply_line_thickness()` method:
- Get current colors from each curve
- Rebuild pens with new thickness: `pg.mkPen(color=current_color, width=self.line_thickness)`
- Apply to all 5 curves: cpu_curve, disk_read_curve, disk_write_curve, net_sent_curve, net_recv_curve

### 5. Update Existing Code to Use Variable
Replace hardcoded `width=2` with `self.line_thickness` in:
- Line 1701: cpu_curve creation
- Lines 1712-1713: disk_read/write_curve creation
- Lines 1725-1726: net_sent/recv_curve creation
- Lines 2082, 2089-2090, 2097-2098: apply_system_theme_to_plots()
- Line 3199: apply_color_to_element()

### 6. Save/Load Preference
- In `customize_line_thickness()`: save to preferences.json as `"line_thickness": N`
- Add `load_line_thickness_preference()` method
- Call it from `__init__` after graph setup (~line 1762)

## Files Modified
- `src/sysmon.py` - single file, all changes

## Key Line Locations
| Change | Location |
|--------|----------|
| Instance variable | ~1545 (near graph vars) |
| Menu item | ~2213 (after Graph Colors) |
| Initial curve creation | 1701, 1712-1713, 1725-1726 |
| Theme application | 2082, 2089-2090, 2097-2098 |
| Color application | 3199 |
| New dialog function | ~3154 (after customize_graph_colors) |
| Load preference call | ~1762 (after load_graph_colors_preferences) |

## Verification
1. Run `python src/sysmon.py`
2. Config menu should show "Line Thickness..." below "Graph Colors..."
3. Open dialog, adjust thickness (1-10), click Apply
4. All graph lines should update immediately
5. Close and reopen app - thickness should persist
6. Verify preferences.json contains `"line_thickness": N`
