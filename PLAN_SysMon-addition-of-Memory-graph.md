# Plan: Add Memory Graph to SysMon

## Context
SysMon currently shows RAM and Swap usage as text labels at the top of the UI. The goal is to replace those labels with a fourth scrolling graph — "Memory Usage (%)" — positioned immediately below the CPU graph. The graph will show two lines (RAM % and Swap %) on a fixed 0–100% Y-axis, matching the CPU graph style. The text labels are removed since the graph makes them redundant.

---

## Files to Modify

| File | Scope |
|---|---|
| `src/sysmon.py` | Add 2 deques; remove text label panel; add Memory plot |
| `src/sysmon/data.py` | Append to deques; remove label updates; update plots |
| `src/sysmon/theme.py` | Add memory plot colors and theming |
| `src/sysmon/settings.py` | 7 small changes across multiple methods |
| `src/sysmon/menu.py` | Add "Show Memory" toggle to View menu |
| `src/sysmon/window.py` | Apply axis inversion to memory plot on load |

---

## Step-by-Step Changes

### 1. `src/sysmon.py` — `__init__()`, lines 96–110

Add two time-series deques alongside the existing ones:
```python
self.ram_percent_data = deque(maxlen=self.max_points)
self.swap_percent_data = deque(maxlen=self.max_points)
```
The existing scalar variables (`ram_percent`, `swap_percent`, etc.) remain as intermediate values used during data collection.

---

### 2. `src/sysmon.py` — `setup_ui()`, lines 147–176

**Remove** the entire memory info panel (lines 147–160):
- `memory_layout`, `self.ram_label`, `self.swap_label`, `main_layout.addLayout(memory_layout)`

**Add Memory plot** after the CPU plot block (after line 176), before Disk I/O:
```python
# Memory Plot
self.memory_plot = pg.PlotWidget(title="Memory Usage (%)")
self.memory_plot.setLabel('left', 'Usage', units='%')
self.memory_plot.setLabel('bottom', 'Time', units='s')
self.memory_plot.setYRange(0, 100)
self.memory_plot.setXRange(-self.time_window, 0)
self.memory_plot.showGrid(x=True, y=True, alpha=0.3)
self.mem_ram_curve = self.memory_plot.plot(
    pen=pg.mkPen(color='#2196F3', width=self.line_thickness), name='RAM')
self.mem_swap_curve = self.memory_plot.plot(
    pen=pg.mkPen(color='#FF9800', width=self.line_thickness), name='Swap')
self.memory_plot.addLegend()
main_layout.addWidget(self.memory_plot)
```

**Add** `memory_plot` sigStateChanged connection (lines 209–211):
```python
self.memory_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
```

---

### 3. `src/sysmon/data.py` — `update_data()`

After `self.swap_percent = swap.percent` (line 57), append to deques:
```python
self.ram_percent_data.append(self.ram_percent)
self.swap_percent_data.append(self.swap_percent)
```

**Remove** lines 67–74 (the `ram_label.setText` and `swap_label.setText` calls).

**In `update_plots()`**, after the existing smoothing block, add:
```python
ram_smoothed = self.apply_smoothing(self.ram_percent_data)
swap_smoothed = self.apply_smoothing(self.swap_percent_data)
self.mem_ram_curve.setData(time_array, ram_smoothed)
self.mem_swap_curve.setData(time_array, swap_smoothed)
```

---

### 4. `src/sysmon/theme.py` — `apply_system_theme_to_plots()`

Add memory colors to both theme branches:
- **Dark:** `mem_ram_color = '#2196F3'`, `mem_swap_color = '#FF9800'`, background `(20, 20, 20)`
- **Light:** `mem_ram_color = '#1565C0'`, `mem_swap_color = '#E65100'`, background `(240, 240, 240)`
  (Slightly darker shades for light theme readability)

Add background and curve/axis theming for `memory_plot` following the exact same pattern as the three existing plots.

---

### 5. `src/sysmon/settings.py` — 7 locations

**a) `update_time_window()`** — add deques to the trim loop and X-axis update:
```python
# In the deque loop, add:
self.ram_percent_data, self.swap_percent_data
# X-axis:
self.memory_plot.setXRange(-self.time_window, 0)
```

**b) `on_axis_changed()`** — sync inversion to memory plot:
```python
self.memory_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
```

**c) `clear_data()`** — clear memory deques:
```python
self.ram_percent_data.clear()
self.swap_percent_data.clear()
```

**d) `save_data()` CSV** — add columns and data:
```python
# Header: add 'Memory RAM %', 'Memory Swap %'
# Data rows: add ram_percent_data[i], swap_percent_data[i]
```

**e) `customize_graph_colors()`** — add to `graph_elements` list:
```python
"Memory RAM Curve", "Memory Swap Curve"
```

**f) `select_graph_color()` element_map + `apply_color_to_element()`** — add:
```python
"Memory RAM Curve": "mem_ram"
"Memory Swap Curve": "mem_swap"
# apply_color_to_element: handle mem_ram → mem_ram_curve, mem_swap → mem_swap_curve
# Also add memory_plot to Background Color and Grid Color blocks
```

**g) `apply_line_thickness()`** — add:
```python
self.mem_ram_curve.setPen(pg.mkPen(color=mem_ram_color, width=self.line_thickness))
self.mem_swap_curve.setPen(pg.mkPen(color=mem_swap_color, width=self.line_thickness))
```

Add **`toggle_memory_plot()`** method alongside the existing toggles:
```python
def toggle_memory_plot(self):
    self.memory_plot.setVisible(self.show_memory_action.isChecked())
```

---

### 6. `src/sysmon/menu.py` — View menu (after line 77)

```python
self.show_memory_action = QAction('Show &Memory', self, checkable=True)
self.show_memory_action.setChecked(True)
self.show_memory_action.triggered.connect(self.toggle_memory_plot)
view_menu.addAction(self.show_memory_action)
```

---

### 7. `src/sysmon/window.py` — `load_window_geometry()`, lines 199–202

Add memory plot to the axis inversion restore block:
```python
self.memory_plot.getPlotItem().getViewBox().invertX(True)
```

---

## Verification

1. Run `./run.sh` — four graphs should appear stacked: CPU → Memory → Disk → Network
2. Memory graph shows two lines (RAM % blue, Swap % orange) with a legend
3. Text labels at top are gone
4. Y-axis fixed 0–100%, X-axis scrolls with time
5. `+`/`-` smoothing keys affect the memory curves
6. View menu → "Show Memory" hides/shows the graph
7. Config → Graph Colors → memory curves appear in the color picker
8. Right-click any graph → Invert X → all four graphs invert together
9. Save Data (CSV) includes RAM % and Swap % columns
10. Theme toggle (light/dark) applies correct colors to memory plot
