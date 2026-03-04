"""
SysMon Theme Mixin
Theme detection, application, and PyQtGraph theme configuration.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
import pyqtgraph as pg

from sysmon.theme_registry import get_theme_registry, ThemeCategory

_DARK_THEMES = {'dark', 'solarized_dark', 'dracula'}


class ThemeMixin:
    """Theme management methods for SystemMonitor."""

    def setup_pyqtgraph_theme(self):
        """Configure PyQtGraph to match system theme"""
        # Use the is_dark_theme method which respects manual theme selection
        is_dark_theme = self.is_dark_theme()

        # Apply theme to PyQtGraph global config
        if is_dark_theme:
            pg.setConfigOptions(
                background=(20, 20, 20),  # Dark background
                foreground=(200, 200, 200),  # Light text
                antialias=True,
                enableExperimental=True
            )
        else:
            pg.setConfigOptions(
                background=(240, 240, 240),  # Light background
                foreground=(40, 40, 40),  # Dark text
                antialias=True,
                enableExperimental=True
            )

    def get_dialog_theme_colors(self):
        """Get theme-appropriate colors for dialogs"""
        # Get system palette
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        bg_brightness = sum([bg_color.red(), bg_color.green(), bg_color.blue()]) / 3
        is_dark_theme = bg_brightness < 128

        if is_dark_theme:
            return {
                'background': '#1e1e1e',
                'text': '#c8c8c8',
                'selection_bg': '#0078d7',
                'selection_text': 'white'
            }
        else:
            return {
                'background': '#f8f9fa',
                'text': '#212529',
                'selection_bg': '#0078d7',
                'selection_text': 'white'
            }

    def is_dark_theme(self):
        """Check if application is using a dark theme"""
        return self.current_theme in _DARK_THEMES

    def _palette_from_theme(self, theme_name):
        """Build a PyQt5 QPalette from a ThemeManager UIPalette."""
        registry = get_theme_registry()
        theme = registry.get_theme(theme_name) or registry.get_theme('dark')
        ui = theme.ui_palette

        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor(ui.window_color))
        palette.setColor(QPalette.WindowText,      QColor(ui.window_text_color))
        palette.setColor(QPalette.Base,            QColor(ui.base_color))
        palette.setColor(QPalette.AlternateBase,   QColor(ui.alternate_base_color))
        palette.setColor(QPalette.Text,            QColor(ui.text_color))
        palette.setColor(QPalette.Button,          QColor(ui.button_color))
        palette.setColor(QPalette.ButtonText,      QColor(ui.button_text_color))
        palette.setColor(QPalette.Highlight,       QColor(ui.highlight_color))
        palette.setColor(QPalette.HighlightedText, QColor(ui.highlighted_text_color))

        # Tooltip colors derived from base/text
        palette.setColor(QPalette.ToolTipBase, QColor(ui.base_color))
        palette.setColor(QPalette.ToolTipText, QColor(ui.text_color))

        # Disabled: window text at ~50% opacity
        disabled_text = QColor(ui.window_text_color)
        disabled_text.setAlpha(128)
        palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
        palette.setColor(QPalette.Disabled, QPalette.Text,       disabled_text)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

        return palette

    def apply_application_theme(self):
        """Apply theme palette to entire application (not just graphs)"""
        palette = self._palette_from_theme(self.current_theme)

        # Apply palette to the application
        QApplication.instance().setPalette(palette)

        # Apply explicit menu bar stylesheet — Qt's native Windows style overrides
        # the palette for QMenuBar/QMenu, making text washed out in dark mode.
        if self.is_dark_theme():
            self.menuBar().setStyleSheet("""
                QMenuBar {
                    background-color: #353535;
                    color: #e0e0e0;
                }
                QMenuBar::item:selected {
                    background-color: #2a82da;
                    color: #ffffff;
                }
                QMenuBar::item:pressed {
                    background-color: #1a6bbf;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #353535;
                    color: #e0e0e0;
                    border: 1px solid #555555;
                }
                QMenu::item:selected {
                    background-color: #2a82da;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #555555;
                }
            """)
        else:
            self.menuBar().setStyleSheet("")  # Restore native light rendering

        # Also apply to PyQtGraph theme and plots (if they exist)
        self.setup_pyqtgraph_theme()
        if hasattr(self, 'cpu_plot'):
            self.apply_system_theme_to_plots()

        # Re-style hover labels to match new theme
        if hasattr(self, '_cpu_hover_label'):
            style = self._hover_label_style()
            for lbl in (self._cpu_hover_label, self._mem_hover_label,
                        self._disk_hover_label, self._net_hover_label):
                lbl.setStyleSheet(style)

    def apply_system_theme_to_plots(self):
        """Apply system theme colors to plots"""
        # Use the is_dark_theme method which respects manual theme selection
        is_dark_theme = self.is_dark_theme()

        # Set theme colors
        if is_dark_theme:
            text_color = '#c8c8c8'
            grid_color = '#404040'
            axis_color = '#808080'

            # Dark theme colors for better contrast
            cpu_color = '#4CAF50'
            disk_read_color = '#FF9800'
            disk_write_color = '#2196F3'
            net_sent_color = '#E91E63'
            net_recv_color = '#00BCD4'
            mem_ram_color = '#2196F3'
            mem_swap_color = '#FF9800'

            # Set plot backgrounds
            self.cpu_plot.setBackground((20, 20, 20))
            self.memory_plot.setBackground((20, 20, 20))
            self.disk_plot.setBackground((20, 20, 20))
            self.net_plot.setBackground((20, 20, 20))
        else:
            text_color = '#282828'
            grid_color = '#d0d0d0'
            axis_color = '#808080'

            # Light theme colors
            cpu_color = '#00ff00'
            disk_read_color = '#ff6b6b'
            disk_write_color = '#4ecdc4'
            net_sent_color = '#ff9ff3'
            net_recv_color = '#54a0ff'
            mem_ram_color = '#1565C0'
            mem_swap_color = '#E65100'

            # Set plot backgrounds
            self.cpu_plot.setBackground((240, 240, 240))
            self.memory_plot.setBackground((240, 240, 240))
            self.disk_plot.setBackground((240, 240, 240))
            self.net_plot.setBackground((240, 240, 240))

        # Apply colors to CPU plot
        self.cpu_curve.setPen(pg.mkPen(color=cpu_color, width=self.line_thickness))
        self.cpu_plot.getAxis('left').setPen(axis_color)
        self.cpu_plot.getAxis('bottom').setPen(axis_color)
        self.cpu_plot.getAxis('left').setTextPen(text_color)
        self.cpu_plot.getAxis('bottom').setTextPen(text_color)

        # Apply colors to Memory plot
        self.mem_ram_curve.setPen(pg.mkPen(color=mem_ram_color, width=self.line_thickness))
        self.mem_swap_curve.setPen(pg.mkPen(color=mem_swap_color, width=self.line_thickness))
        self.memory_plot.getAxis('left').setPen(axis_color)
        self.memory_plot.getAxis('bottom').setPen(axis_color)
        self.memory_plot.getAxis('left').setTextPen(text_color)
        self.memory_plot.getAxis('bottom').setTextPen(text_color)

        # Apply colors to Disk plot
        self.disk_read_curve.setPen(pg.mkPen(color=disk_read_color, width=self.line_thickness))
        self.disk_write_curve.setPen(pg.mkPen(color=disk_write_color, width=self.line_thickness))
        self.disk_plot.getAxis('left').setPen(axis_color)
        self.disk_plot.getAxis('bottom').setPen(axis_color)
        self.disk_plot.getAxis('left').setTextPen(text_color)
        self.disk_plot.getAxis('bottom').setTextPen(text_color)

        # Apply colors to Network plot
        self.net_sent_curve.setPen(pg.mkPen(color=net_sent_color, width=self.line_thickness))
        self.net_recv_curve.setPen(pg.mkPen(color=net_recv_color, width=self.line_thickness))
        self.net_plot.getAxis('left').setPen(axis_color)
        self.net_plot.getAxis('bottom').setPen(axis_color)
        self.net_plot.getAxis('left').setTextPen(text_color)
        self.net_plot.getAxis('bottom').setTextPen(text_color)

    def switch_theme(self, name):
        """Switch to a named theme and apply immediately."""
        if name == self.current_theme:
            return
        self.current_theme = name
        self.apply_application_theme()
        self.update_theme_menu_states()
        self.save_preferences()

    def update_theme_menu_states(self):
        """Update checkmarks in the Theme submenu to reflect current theme."""
        for theme_name, action in self.theme_actions.items():
            action.setChecked(theme_name == self.current_theme)
