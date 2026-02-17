# SysMon Refactoring Plan

**Author:** pi (AI coding assistant)  
**Date:** Sun 08 Feb 2026 07:50:00 AM CST  
**Status:** Proposal — awaiting review  

---

## Problem Statement

SysMon is a well-functioning, feature-rich system monitor that has grown organically from a simple PyQt5 project into a 4,153-line monolithic file (`src/sysmon.py`). The application runs great, but the single-file architecture creates challenges for:

- **Navigability** — finding a specific feature in 4,000+ lines
- **Maintainability** — changes in one area risk side-effects elsewhere
- **Collaboration** — harder for multiple contributors (human or AI) to work on different features
- **Testing** — difficult to unit test individual components in isolation

The goal is to **improve the architecture without breaking what works**. No rewrites, no new abstractions — just clean separation of concerns.

---

## Current Architecture

### File Size

| Component | Lines | % of Total |
|---|---|---|
| **SystemMonitor (main class)** | **2,586** | **62%** |
| RealTimeProcessDialog | 285 | 7% |
| RealTimeDiskDialog | 298 | 7% |
| RealTimeNetworkDialog | 299 | 7% |
| DiskIOWorker | 89 | 2% |
| NetworkWorker | 73 | 2% |
| ProcessWorker | 134 | 3% |
| Standalone functions + boilerplate | ~389 | 10% |
| **Total** | **4,153** | |

### The Core Problem

The `SystemMonitor` class has **70+ methods** spanning unrelated responsibilities:

- Theme detection and application
- Menu bar construction (168 lines alone)
- Data collection and smoothing
- Graph setup and updating
- Window positioning and geometry persistence
- Keyboard/mouse event handling
- Settings dialogs (colors, thickness, transparency, themes)
- About/changelog/help dialogs with Markdown rendering
- GitHub update checking
- Configuration load/save/migration

These are all tangled into a single 2,586-line class.

---

## Proposed Target Architecture

```
src/
├── sysmon.py                  (~150 lines)  Entry point, main(), wires everything together
├── sysmon/
│   ├── __init__.py
│   ├── constants.py           (~50 lines)   VERSION, defaults, build info, unit constants
│   ├── config.py              (~120 lines)  XDG paths, load/save geometry & preferences, migration
│   ├── theme.py               (~180 lines)  is_dark_theme, apply_application_theme, apply_system_theme_to_plots
│   ├── data.py                (~100 lines)  update_data, apply_smoothing, clear_data, save_data, export
│   ├── plots.py               (~80 lines)   Graph widget setup, update_plots, toggle_*_plot
│   ├── menu.py                (~180 lines)  setup_menu_bar — all menu construction
│   ├── keyboard.py            (~60 lines)   keyPressEvent, mousePressEvent, shortcut handling
│   ├── window.py              (~120 lines)  position_left/right, minimize, fullscreen, always_on_top, transparency
│   ├── updates.py             (~150 lines)  check_for_updates, update dialogs, auto-check logic
│   ├── markdown_render.py     (~160 lines)  render_markdown_to_html, load_document_with_fallback
│   ├── platform.py            (~90 lines)   filter_stderr, single_instance management, set_application_icon
│   ├── monitor.py             (~100 lines)  SystemMonitor class — slim __init__ that wires mixins together
│   └── dialogs/
│       ├── __init__.py
│       ├── process.py         (~420 lines)  ProcessWorker + RealTimeProcessDialog + ProcessInfoDialog
│       ├── disk.py            (~390 lines)  DiskIOWorker + RealTimeDiskDialog
│       ├── network.py         (~370 lines)  NetworkWorker + RealTimeNetworkDialog
│       ├── about.py           (~110 lines)  show_about, show_changelog, show_users_guide
│       ├── settings.py        (~300 lines)  change_theme, graph colors, line thickness, transparency dialog
│       └── config_viewer.py   (~90 lines)   ConfigFileViewerDialog
```

**Result:** No single file exceeds ~420 lines. The entry point (`sysmon.py`) drops from 4,153 to ~150 lines.

---

## Technical Approach: Mixin Classes

The cleanest way to decompose a large `QMainWindow` subclass without rewriting its internals is the **mixin pattern**. Each group of related methods becomes a mixin class in its own file. They all share `self` because they're combined into a single class via multiple inheritance.

### Example

```python
# src/sysmon/theme.py
class ThemeMixin:
    """Theme detection and application methods for SystemMonitor."""
    
    def setup_pyqtgraph_theme(self):
        ...  # existing code, unchanged
    
    def is_dark_theme(self):
        ...  # existing code, unchanged
    
    def apply_application_theme(self):
        ...  # existing code, unchanged
    
    def apply_system_theme_to_plots(self):
        ...  # existing code, unchanged
```

```python
# src/sysmon/monitor.py
from sysmon.theme import ThemeMixin
from sysmon.menu import MenuMixin
from sysmon.data import DataMixin
from sysmon.plots import PlotsMixin
from sysmon.window import WindowMixin
from sysmon.keyboard import KeyboardMixin
from sysmon.updates import UpdatesMixin
from sysmon.markdown_render import MarkdownMixin

class SystemMonitor(
    ThemeMixin,
    MenuMixin,
    DataMixin,
    PlotsMixin,
    WindowMixin,
    KeyboardMixin,
    UpdatesMixin,
    MarkdownMixin,
    QMainWindow
):
    def __init__(self):
        super().__init__()
        # ~50 lines of initialization and wiring
        ...
```

### Why Mixins?

- **Zero behavior changes** — methods stay exactly the same, they just live in different files
- **`self` still works** — all mixins share the same instance
- **No new abstractions** — no dependency injection, no event buses, no service layers
- **Easy to test** — can instantiate individual mixins or mock others
- **Incremental** — can move one group of methods at a time, testing after each step
- **Reversible** — if something goes wrong, just move the methods back

---

## Phased Implementation Plan

### Phase 1 — Low Risk, High Impact

**Estimated effort:** 1-2 sessions  
**Risk:** Minimal — these are already self-contained pieces

| Step | What | From | To | Lines Moved |
|------|------|------|----|-------------|
| 1.1 | Version, defaults, build info | top of sysmon.py | `sysmon/constants.py` | ~50 |
| 1.2 | XDG paths, config load/save, migration | standalone functions + SystemMonitor methods | `sysmon/config.py` | ~120 |
| 1.3 | ProcessWorker + ProcessInfoDialog + RealTimeProcessDialog | sysmon.py classes | `sysmon/dialogs/process.py` | ~420 |
| 1.4 | DiskIOWorker + RealTimeDiskDialog | sysmon.py classes | `sysmon/dialogs/disk.py` | ~390 |
| 1.5 | NetworkWorker + RealTimeNetworkDialog | sysmon.py classes | `sysmon/dialogs/network.py` | ~370 |
| 1.6 | ConfigFileViewerDialog | sysmon.py class | `sysmon/dialogs/config_viewer.py` | ~90 |
| 1.7 | filter_stderr, single_instance, set_application_icon | standalone functions | `sysmon/platform.py` | ~90 |

**Phase 1 result:** `sysmon.py` drops from ~4,153 to ~2,623 lines (~37% reduction). All the easy wins.

### Phase 2 — Mixin Extraction

**Estimated effort:** 2-3 sessions  
**Risk:** Low-medium — methods reference `self` attributes, need to verify all cross-references

| Step | What | Methods Moved | To | Lines Moved |
|------|------|---------------|-----|-------------|
| 2.1 | Theme management | `setup_pyqtgraph_theme`, `is_dark_theme`, `apply_application_theme`, `apply_system_theme_to_plots`, `get_dialog_theme_colors` | `sysmon/theme.py` | ~180 |
| 2.2 | Update checking | `check_for_updates`, `show_update_available_dialog`, `skip_update_version`, `toggle_auto_check_updates`, `check_updates_on_startup`, `show_startup_update_notification` | `sysmon/updates.py` | ~150 |
| 2.3 | Markdown rendering | `render_markdown_to_html`, `load_document_with_fallback` | `sysmon/markdown_render.py` | ~160 |
| 2.4 | Menu construction | `setup_menu_bar` | `sysmon/menu.py` | ~180 |

**Phase 2 result:** `sysmon.py` drops to ~1,953 lines (~53% total reduction).

### Phase 3 — Complete Decomposition

**Estimated effort:** 2-3 sessions  
**Risk:** Medium — these methods are more tightly coupled to `__init__` state

| Step | What | Methods Moved | To | Lines Moved |
|------|------|---------------|-----|-------------|
| 3.1 | Data collection & smoothing | `update_data`, `apply_smoothing`, `clear_data`, `save_data`, `export_graph`, `copy_graph` | `sysmon/data.py` | ~100 |
| 3.2 | Plot setup & updates | `setup_ui` (graph portion), `update_plots`, `toggle_*_plot` | `sysmon/plots.py` | ~80 |
| 3.3 | Window management | `position_window_left/right`, `minimize_window`, `toggle_fullscreen`, `set_always_on_top`, `toggle_always_on_top`, `set_window_transparency`, `toggle_transparency` | `sysmon/window.py` | ~120 |
| 3.4 | Keyboard/mouse | `keyPressEvent`, `mousePressEvent` | `sysmon/keyboard.py` | ~60 |
| 3.5 | Settings dialogs | `change_theme`, `customize_graph_colors`, `select_graph_color`, `apply_graph_color`, `apply_color_to_element`, `reset_graph_colors`, `customize_line_thickness`, related helpers, `change_transparency` | `sysmon/dialogs/settings.py` | ~300 |
| 3.6 | Help/About dialogs | `show_about`, `show_changelog`, `show_users_guide`, `show_keyboard_shortcuts`, `show_issue_tracker`, `show_changelog_github` | `sysmon/dialogs/about.py` | ~110 |
| 3.7 | Final cleanup | Slim `__init__`, create `monitor.py` with mixin composition | `sysmon/monitor.py` | ~100 |

**Phase 3 result:** Full decomposition complete. No file exceeds ~420 lines.

---

## Validation Strategy

After each step:

1. **Run the app** — `python3 src/sysmon.py` — verify all three graphs render and update
2. **Test keyboard controls** — `+`/`-` for time window, shortcuts
3. **Test double-click drill-down** — all three graph types
4. **Test menus** — File, Edit, View, Config, Help all functional
5. **Test window persistence** — close and reopen, verify position/size restored
6. **Test theme switching** — Config → Theme → cycle through Auto/Light/Dark
7. **Run existing tests** — `python3 tests/test_geometry.py`, `python3 tests/test_stderr_filter.py`

### Regression Checklist

- [ ] App launches without errors
- [ ] CPU, Disk I/O, Network graphs all display and update
- [ ] Double-click opens real-time process/disk/network dialogs
- [ ] Keyboard shortcuts work (+, -, Ctrl+Q, F11, etc.)
- [ ] Menu bar fully functional (all items)
- [ ] Window geometry saves/loads correctly
- [ ] Theme detection works (auto/light/dark)
- [ ] Graph colors and line thickness customization works
- [ ] Transparency slider works
- [ ] Always-on-top toggle works
- [ ] About dialog displays correctly with Markdown
- [ ] Changelog renders correctly
- [ ] Update checker works (Help → Check for Updates)
- [ ] Config file viewer shows correct paths
- [ ] Single-instance detection works
- [ ] No GdkPixbuf warnings in stderr (Linux)

---

## What This Plan Does NOT Do

- ❌ **No logic changes** — all behavior stays identical
- ❌ **No new dependencies** — same packages, same imports
- ❌ **No new design patterns** — no DI, no event buses, no service locators
- ❌ **No API changes** — external interfaces (CLI args, config files, keyboard shortcuts) unchanged
- ❌ **No class hierarchy changes** — still one `QMainWindow` subclass, just composed from mixins
- ❌ **No renaming** — method and variable names stay the same

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Circular imports between modules | Medium | Careful import ordering; use TYPE_CHECKING for type hints |
| Mixin method resolution order (MRO) issues | Low | QMainWindow always last in inheritance; mixins don't override each other |
| `self` attribute not initialized when mixin method called | Low | Keep all `__init__` setup in `SystemMonitor.__init__`; mixins don't define `__init__` |
| Test imports break | Low | Keep `src/sysmon.py` as the public entry point with re-exports |
| Git blame history lost | Certain | Use `git mv` where possible; add commit messages referencing refactoring plan |

---

## Success Criteria

- `src/sysmon.py` entry point is ≤ 150 lines
- No module exceeds ~420 lines
- All items on the regression checklist pass
- Application behavior is **identical** before and after
- Existing tests continue to pass

---

## Notes

- The `icon_loader.py` module already follows this pattern — it was extracted successfully and lives independently in `src/`
- The Synology platform variant (`platforms/synology/syno-monitor.py`) is unaffected by this refactoring
- The `github_version_checker.py` script is already a separate module — good precedent
- This plan was developed by analyzing the full 4,153-line `sysmon.py` structure, method dependencies, and class relationships
