"""
SysMon Theme Mixin
Theme detection, application, and PyQtGraph theme configuration.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
import pyqtgraph as pg


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
        """Check if application is using dark theme"""
        # Check for manual theme override
        if self.theme_mode == 'dark':
            return True
        elif self.theme_mode == 'light':
            return False
        # else: theme_mode == 'auto', use system detection

        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        # Consider dark if background lightness < 128
        return bg_color.lightness() < 128

    def apply_application_theme(self):
        """Apply theme palette to entire application (not just graphs)"""
        is_dark = self.is_dark_theme()
        palette = QPalette()

        if is_dark:
            # Dark theme colors
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, QColor(200, 200, 200))
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ToolTipText, QColor(200, 200, 200))
            palette.setColor(QPalette.Text, QColor(200, 200, 200))
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, QColor(200, 200, 200))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            # Disabled colors
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        else:
            # Light theme colors
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            # Disabled colors
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))

        # Apply palette to the application
        QApplication.instance().setPalette(palette)

        # Also apply to PyQtGraph theme and plots (if they exist)
        self.setup_pyqtgraph_theme()
        if hasattr(self, 'cpu_plot'):
            self.apply_system_theme_to_plots()

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

            # Set plot backgrounds
            self.cpu_plot.setBackground((20, 20, 20))
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

            # Set plot backgrounds
            self.cpu_plot.setBackground((240, 240, 240))
            self.disk_plot.setBackground((240, 240, 240))
            self.net_plot.setBackground((240, 240, 240))

        # Apply colors to CPU plot
        self.cpu_curve.setPen(pg.mkPen(color=cpu_color, width=self.line_thickness))
        self.cpu_plot.getAxis('left').setPen(axis_color)
        self.cpu_plot.getAxis('bottom').setPen(axis_color)
        self.cpu_plot.getAxis('left').setTextPen(text_color)
        self.cpu_plot.getAxis('bottom').setTextPen(text_color)

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
