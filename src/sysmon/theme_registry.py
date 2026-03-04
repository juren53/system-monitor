#!/usr/bin/env python3
"""
Theme Manager

Centralized theme registry and management system for PyQt6/PySide6 applications.
Provides an extensible architecture for defining, validating, registering,
and persisting UI and content themes.

v2.0.0
Created: 2026-01-30
Updated: 2026-03-04
"""

import re
import json
import threading
import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# Qt framework abstraction – supports both PyQt6 and PySide6
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import QSettings
    _QT_FRAMEWORK = "PyQt6"
except ImportError:
    try:
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import QSettings
        _QT_FRAMEWORK = "PySide6"
    except ImportError:
        # Qt not available – core data structures still usable without Qt
        QPalette = None
        QColor = None
        QSettings = None
        _QT_FRAMEWORK = None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ThemeCategory(Enum):
    """Valid categories for themes."""
    BUILT_IN = "Built-in"
    POPULAR = "Popular"
    CUSTOM = "Custom"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ThemeColors:
    """Data class for content (document/web) theme colors."""

    heading_color: str = field(
        default="#58a6ff", metadata={"label": "Headings"}
    )
    body_text_color: str = field(
        default="#c9d1d9", metadata={"label": "Body Text"}
    )
    background_color: str = field(
        default="#0d1117", metadata={"label": "Background"}
    )
    link_color: str = field(
        default="#58a6ff", metadata={"label": "Links"}
    )
    blockquote_color: str = field(
        default="#8b949e", metadata={"label": "Blockquotes"}
    )
    code_bg_color: str = field(
        default="#161b22", metadata={"label": "Code Blocks"}
    )
    border_color: str = field(
        default="#30363d", metadata={"label": "Borders"}
    )


@dataclass
class UIPalette:
    """Data class for UI theme palette colors."""

    window_color: str = "#2d2d2d"
    window_text_color: str = "#bbbbbb"
    base_color: str = "#1e1e1e"
    alternate_base_color: str = "#2d2d2d"
    text_color: str = "#bbbbbb"
    button_color: str = "#2d2d2d"
    button_text_color: str = "#bbbbbb"
    highlight_color: str = "#ffd700"
    highlighted_text_color: str = "#000000"
    secondary_highlight_color: str = "#ff8c00"


@dataclass
class Theme:
    """Complete theme definition including UI and content components."""

    name: str
    display_name: str
    content_colors: ThemeColors
    ui_palette: UIPalette
    description: str = ""
    is_built_in: bool = True
    category: ThemeCategory = ThemeCategory.CUSTOM


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ThemeRegistry:
    """Centralized theme registry with validation and discovery."""

    def __init__(self):
        self._themes: Dict[str, Theme] = {}
        self._initialize_builtin_themes()

    def _initialize_builtin_themes(self) -> None:
        """Initialize built-in themes."""

        # Dark Theme
        self.register_theme(
            Theme(
                name="dark",
                display_name="Dark",
                content_colors=ThemeColors(
                    heading_color="#58a6ff",
                    body_text_color="#c9d1d9",
                    background_color="#0d1117",
                    link_color="#58a6ff",
                    blockquote_color="#8b949e",
                    code_bg_color="#161b22",
                    border_color="#30363d",
                ),
                ui_palette=UIPalette(
                    window_color="#2d2d2d",
                    window_text_color="#bbbbbb",
                    base_color="#1e1e1e",
                    alternate_base_color="#2d2d2d",
                    text_color="#bbbbbb",
                    button_color="#2d2d2d",
                    button_text_color="#bbbbbb",
                    highlight_color="#ffd700",
                    highlighted_text_color="#000000",
                    secondary_highlight_color="#ff8c00",
                ),
                description="Dark theme with GitHub-inspired colors",
                category=ThemeCategory.BUILT_IN,
            )
        )

        # Light Theme
        self.register_theme(
            Theme(
                name="light",
                display_name="Light",
                content_colors=ThemeColors(
                    heading_color="#0366d8",
                    body_text_color="#24292e",
                    background_color="#ffffff",
                    link_color="#0366d8",
                    blockquote_color="#6a737d",
                    code_bg_color="#f6f8fa",
                    border_color="#e1e4e8",
                ),
                ui_palette=UIPalette(
                    window_color="#f0f0f0",
                    window_text_color="#000000",
                    base_color="#ffffff",
                    alternate_base_color="#f5f5f5",
                    text_color="#000000",
                    button_color="#f0f0f0",
                    button_text_color="#000000",
                    highlight_color="#0366d8",
                    highlighted_text_color="#ffffff",
                    secondary_highlight_color="#f66a0a",
                ),
                description="Light theme with GitHub-inspired colors",
                category=ThemeCategory.BUILT_IN,
            )
        )

        # Solarized Light Theme
        self.register_theme(
            Theme(
                name="solarized_light",
                display_name="Solarized Light",
                content_colors=ThemeColors(
                    heading_color="#586e75",
                    body_text_color="#657b83",
                    background_color="#fdf6e3",
                    link_color="#268bd2",
                    blockquote_color="#93a1a1",
                    code_bg_color="#eee8d5",
                    border_color="#93a1a1",
                ),
                ui_palette=UIPalette(
                    window_color="#fdf6e3",
                    window_text_color="#657b83",
                    base_color="#ffffff",
                    alternate_base_color="#f5f5dc",
                    text_color="#657b83",
                    button_color="#eee8d5",
                    button_text_color="#657b83",
                    highlight_color="#268bd2",
                    highlighted_text_color="#ffffff",
                    secondary_highlight_color="#cb4b16",
                ),
                description="Solarized light theme for comfortable reading",
                category=ThemeCategory.POPULAR,
            )
        )

        # Solarized Dark Theme
        self.register_theme(
            Theme(
                name="solarized_dark",
                display_name="Solarized Dark",
                content_colors=ThemeColors(
                    heading_color="#93a1a1",
                    body_text_color="#839496",
                    background_color="#002b36",
                    link_color="#268bd2",
                    blockquote_color="#586e75",
                    code_bg_color="#073642",
                    border_color="#586e75",
                ),
                ui_palette=UIPalette(
                    window_color="#073642",
                    window_text_color="#839496",
                    base_color="#002b36",
                    alternate_base_color="#073642",
                    text_color="#839496",
                    button_color="#073642",
                    button_text_color="#839496",
                    highlight_color="#268bd2",
                    highlighted_text_color="#fdf6e3",
                    secondary_highlight_color="#cb4b16",
                ),
                description="Solarized dark theme for comfortable reading",
                category=ThemeCategory.POPULAR,
            )
        )

        # Dracula Theme
        self.register_theme(
            Theme(
                name="dracula",
                display_name="Dracula",
                content_colors=ThemeColors(
                    heading_color="#f8f8f2",
                    body_text_color="#e2e2e2",
                    background_color="#282a36",
                    link_color="#8be9fd",
                    blockquote_color="#6272a4",
                    code_bg_color="#44475a",
                    border_color="#6272a4",
                ),
                ui_palette=UIPalette(
                    window_color="#282a36",
                    window_text_color="#f8f8f2",
                    base_color="#1e1f29",
                    alternate_base_color="#44475a",
                    text_color="#f8f8f2",
                    button_color="#44475a",
                    button_text_color="#f8f8f2",
                    highlight_color="#8be9fd",
                    highlighted_text_color="#282a36",
                    secondary_highlight_color="#ffb86c",
                ),
                description="Popular Dracula theme with vibrant colors",
                category=ThemeCategory.POPULAR,
            )
        )

        # GitHub Theme
        self.register_theme(
            Theme(
                name="github",
                display_name="GitHub",
                content_colors=ThemeColors(
                    heading_color="#24292f",
                    body_text_color="#24292f",
                    background_color="#ffffff",
                    link_color="#0969da",
                    blockquote_color="#57606a",
                    code_bg_color="#f6f8fa",
                    border_color="#d0d7de",
                ),
                ui_palette=UIPalette(
                    window_color="#ffffff",
                    window_text_color="#24292f",
                    base_color="#f6f8fa",
                    alternate_base_color="#ffffff",
                    text_color="#24292f",
                    button_color="#f6f8fa",
                    button_text_color="#24292f",
                    highlight_color="#0969da",
                    highlighted_text_color="#ffffff",
                    secondary_highlight_color="#e36209",
                ),
                description="Official GitHub theme colors",
                category=ThemeCategory.POPULAR,
            )
        )

    def register_theme(self, theme: Theme) -> bool:
        """Register a new theme. Returns True on success, False on validation failure."""
        if not self._validate_theme(theme):
            return False
        self._themes[theme.name] = theme
        return True

    def _validate_theme(self, theme: Theme) -> bool:
        """Validate theme definition using dataclasses.fields() for safe iteration."""

        def validate_color(color: str) -> bool:
            return bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))

        for f in dataclasses.fields(theme.content_colors):
            if not validate_color(getattr(theme.content_colors, f.name)):
                return False

        for f in dataclasses.fields(theme.ui_palette):
            if not validate_color(getattr(theme.ui_palette, f.name)):
                return False

        return True

    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self._themes.get(name)

    def get_all_themes(self) -> Dict[str, Theme]:
        """Get all registered themes."""
        return self._themes.copy()

    def get_theme_names(self) -> List[str]:
        """Get list of theme names."""
        return list(self._themes.keys())

    def get_themes_by_category(self, category: ThemeCategory) -> List[Theme]:
        """Get themes filtered by category."""
        return [t for t in self._themes.values() if t.category == category]

    def remove_theme(self, name: str) -> bool:
        """Remove a theme (only non-built-in themes can be removed)."""
        theme = self._themes.get(name)
        if theme and not theme.is_built_in:
            del self._themes[name]
            return True
        return False

    # ------------------------------------------------------------------
    # Persistence / export / import
    # ------------------------------------------------------------------

    def export_theme(self, name: str) -> Optional[dict]:
        """Export a theme as a plain dict suitable for JSON serialization."""
        theme = self._themes.get(name)
        if not theme:
            return None
        return {
            "name": theme.name,
            "display_name": theme.display_name,
            "description": theme.description,
            "is_built_in": theme.is_built_in,
            "category": theme.category.value,
            "content_colors": dataclasses.asdict(theme.content_colors),
            "ui_palette": dataclasses.asdict(theme.ui_palette),
        }

    def import_theme(self, data: dict) -> bool:
        """Import a theme from a plain dict. Returns True on success."""
        try:
            content_colors = ThemeColors(**data["content_colors"])
            ui_palette = UIPalette(**data["ui_palette"])
            category_value = data.get("category", ThemeCategory.CUSTOM.value)
            # Accept both enum value strings ("Custom") and enum names ("CUSTOM")
            try:
                category = ThemeCategory(category_value)
            except ValueError:
                category = ThemeCategory[category_value]
            theme = Theme(
                name=data["name"],
                display_name=data["display_name"],
                content_colors=content_colors,
                ui_palette=ui_palette,
                description=data.get("description", ""),
                is_built_in=data.get("is_built_in", False),
                category=category,
            )
            return self.register_theme(theme)
        except (KeyError, TypeError, ValueError):
            return False

    def save_custom_themes(self, path: Path) -> None:
        """Persist all non-built-in themes to a JSON file."""
        custom = [
            self.export_theme(name)
            for name, theme in self._themes.items()
            if not theme.is_built_in
        ]
        path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

    def load_custom_themes(self, path: Path) -> int:
        """Load custom themes from a JSON file. Returns number of themes loaded."""
        if not path.exists():
            return 0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0
        count = 0
        for theme_data in data:
            if self.import_theme(theme_data):
                count += 1
        return count


# ---------------------------------------------------------------------------
# Thread-safe singleton
# ---------------------------------------------------------------------------

_theme_registry: Optional[ThemeRegistry] = None
_theme_registry_lock = threading.Lock()


def get_theme_registry() -> ThemeRegistry:
    """Get the global theme registry instance (thread-safe double-checked locking)."""
    global _theme_registry
    if _theme_registry is None:
        with _theme_registry_lock:
            if _theme_registry is None:
                _theme_registry = ThemeRegistry()
    return _theme_registry


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_default_theme_colors() -> Dict[str, dict]:
    """Return a dict of {theme_name: content_colors_dict} for all themes."""
    registry = get_theme_registry()
    return {
        name: dataclasses.asdict(theme.content_colors)
        for name, theme in registry.get_all_themes().items()
    }


def get_fusion_palette(theme_name: str) -> "QPalette":
    """Get a Qt Fusion QPalette for the named theme."""
    if QPalette is None or QColor is None:
        raise RuntimeError("A Qt framework (PyQt6 or PySide6) is required for get_fusion_palette()")

    registry = get_theme_registry()
    theme = registry.get_theme(theme_name) or registry.get_theme("dark")

    palette = QPalette()
    ui = theme.ui_palette

    palette.setColor(QPalette.ColorRole.Window, QColor(ui.window_color))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(ui.window_text_color))
    palette.setColor(QPalette.ColorRole.Base, QColor(ui.base_color))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ui.alternate_base_color))
    palette.setColor(QPalette.ColorRole.Text, QColor(ui.text_color))
    palette.setColor(QPalette.ColorRole.Button, QColor(ui.button_color))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(ui.button_text_color))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ui.highlight_color))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(ui.highlighted_text_color))

    return palette


def get_search_css(theme_name: str) -> str:
    """Get CSS for search highlighting based on theme palette colors."""
    registry = get_theme_registry()
    theme = registry.get_theme(theme_name) or registry.get_theme("dark")

    highlight_color = theme.ui_palette.highlight_color
    highlighted_text_color = theme.ui_palette.highlighted_text_color
    secondary_highlight_color = theme.ui_palette.secondary_highlight_color

    return f"""
        QTextBrowser {{
            selection-background-color: {highlight_color} !important;
            selection-color: {highlighted_text_color} !important;
            font-weight: bold !important;
            border-radius: 2px !important;
        }}
        .search-current {{
            background-color: {highlight_color} !important;
            color: {highlighted_text_color} !important;
            font-weight: bold !important;
        }}
        .search-other {{
            background-color: {secondary_highlight_color} !important;
            color: #000000 !important;
        }}
    """


def detect_system_theme() -> str:
    """
    Detect the OS dark/light preference.

    Returns 'dark' or 'light'. Falls back to 'light' when Qt is unavailable
    or the platform doesn't support colour-scheme detection.
    """
    try:
        if _QT_FRAMEWORK == "PyQt6":
            from PyQt6.QtGui import QGuiApplication
            from PyQt6.QtCore import Qt
            app = QGuiApplication.instance()
            if app is not None:
                scheme = app.styleHints().colorScheme()
                if scheme == Qt.ColorScheme.Dark:
                    return "dark"
                return "light"
        elif _QT_FRAMEWORK == "PySide6":
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtCore import Qt
            app = QGuiApplication.instance()
            if app is not None:
                scheme = app.styleHints().colorScheme()
                if scheme == Qt.ColorScheme.Dark:
                    return "dark"
                return "light"
    except Exception:
        pass
    return "light"
