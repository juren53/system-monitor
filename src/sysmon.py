#!/usr/bin/env python3
"""
SysMon - PyQtGraph-based System Monitor v0.5.1
Release: 2026-02-20 0556 CST

Real-time CPU, Disk I/O, and Network monitoring with smooth performance
Professional system monitoring with XDG compliance and advanced features
"""

import sys
import os
import atexit
import time
from collections import deque

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPalette
import pyqtgraph as pg
import psutil

# --- Modular imports ---
from sysmon.constants import (VERSION, RELEASE_DATE, RELEASE_TIME, FULL_VERSION,
                               BUILD_DATE, BUILD_TIME, BUILD_INFO,
                               APPLICATION_START_TIME, PYTHON_VERSION, PLATFORM_INFO)
from sysmon.config import (get_xdg_config_dir, ensure_config_directory,
                            migrate_old_config, get_config_file_path,
                            get_preferences_file_path)
from sysmon.platform import (filter_stderr_gdkpixbuf, check_single_instance,
                              cleanup_single_instance, show_instance_already_running,
                              set_application_icon)
from sysmon.theme import ThemeMixin
from sysmon.menu import MenuMixin
from sysmon.updates import UpdatesMixin
from sysmon.markdown_render import MarkdownMixin
from sysmon.data import DataMixin
from sysmon.window import WindowMixin
from sysmon.settings import SettingsMixin
from sysmon.about import AboutMixin

# Apply stderr filtering at startup
filter_stderr_gdkpixbuf()


class SystemMonitor(ThemeMixin, MenuMixin, UpdatesMixin, MarkdownMixin,
                    DataMixin, WindowMixin, SettingsMixin, AboutMixin,
                    QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SysMon - PyQtGraph Edition")

        # Set window icon (fallback for window-level icon)
        self.set_window_icon()

        # XDG-compliant configuration directory
        self.config_dir = get_xdg_config_dir()
        ensure_config_directory(self.config_dir)

        # Migrate old config if exists
        old_config_file = os.path.join(os.path.expanduser('~'), '.sysmon_config.json')
        migration_success = migrate_old_config(old_config_file, self.config_dir)
        if migration_success:
            print("Migrated configuration to XDG-compliant location")

        # Configuration file paths
        self.config_file = get_config_file_path(self.config_dir)
        self.preferences_file = get_preferences_file_path(self.config_dir)

        # Set default size if no saved geometry exists
        if not hasattr(self, '_initial_geometry_loaded'):
            self.resize(1000, 700)

        # Configuration defaults (will be overridden by loaded preferences)
        self.time_window = 20  # seconds
        self.update_interval = 200  # ms
        self.transparency = 1.0  # 1.0 = opaque, 0.0 = fully transparent
        self.always_on_top = False  # Window always on top setting
        self.invert_axis = False  # X-axis inversion for all graphs
        self._loading_preferences = False  # Flag to prevent signal handling during init
        self._transparency_toggled = False  # Flag to track transparency toggle state
        self.smoothing_window = 1  # Number of data points to average (1 = no smoothing)
        self.min_smoothing = 1     # Minimum smoothing (raw data)
        self.max_smoothing = 20    # Maximum smoothing (20-point moving average)
        self.theme_mode = 'auto'   # Theme mode: 'auto', 'light', or 'dark'
        self.line_thickness = 2    # Graph line thickness (1-10, default 2)

        # Update checking configuration
        self.auto_check_updates = False  # Auto-check for updates on startup
        self.last_update_check = 0  # Timestamp of last update check
        self.update_check_interval_days = 7  # Days between automatic checks
        self.skipped_update_versions = []  # Versions user chose to skip

        self.max_points = int((self.time_window * 1000) / self.update_interval)

        # Data storage
        self.cpu_data = deque(maxlen=self.max_points)
        self.disk_read_data = deque(maxlen=self.max_points)
        self.disk_write_data = deque(maxlen=self.max_points)
        self.net_sent_data = deque(maxlen=self.max_points)
        self.net_recv_data = deque(maxlen=self.max_points)
        self.time_data = deque(maxlen=self.max_points)
        self.ram_percent_data = deque(maxlen=self.max_points)
        self.swap_percent_data = deque(maxlen=self.max_points)

        # Memory data storage
        self.ram_total = 0
        self.ram_available = 0
        self.ram_percent = 0
        self.swap_total = 0
        self.swap_available = 0
        self.swap_percent = 0

        # Previous values for rate calculation
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_net_io = psutil.net_io_counters()
        self.prev_time = time.time()

        # Async process analysis attributes
        self.process_worker = None
        self.process_thread = None

        self.setup_ui()
        self.setup_hover_tracking()
        self.setup_menu_bar()
        self.setup_timer()

        # Load preferences after timer is created
        self.load_window_geometry()

        # Add periodic save timer as backup
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_window_geometry)
        self.save_timer.start(30000)  # Save every 30 seconds

        # Check for updates on startup if enabled
        self.check_updates_on_startup()

    def set_window_icon(self):
        """Set window icon via IconLoader"""
        from icon_loader import icons
        self.setWindowIcon(icons.app_icon())

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Setup plots with system theme
        self.apply_application_theme()
        pg.setConfigOptions(antialias=True)

        # CPU Plot
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setLabel('left', 'Usage', units='%')
        self.cpu_plot.setLabel('bottom', 'Time', units='s')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setXRange(-self.time_window, 0)
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color='#00ff00', width=self.line_thickness))
        self.cpu_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_realtime_processes('cpu') if evt.button() == Qt.MiddleButton else None)
        main_layout.addWidget(self.cpu_plot)

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

        # Disk I/O Plot
        self.disk_plot = pg.PlotWidget(title="Disk I/O (MB/s)")
        self.disk_plot.setLabel('left', 'Rate', units='MB/s')
        self.disk_plot.setLabel('bottom', 'Time', units='s')
        self.disk_plot.setXRange(-self.time_window, 0)
        self.disk_plot.showGrid(x=True, y=True, alpha=0.3)
        self.disk_read_curve = self.disk_plot.plot(pen=pg.mkPen(color='#ff6b6b', width=self.line_thickness), name='Read')
        self.disk_write_curve = self.disk_plot.plot(pen=pg.mkPen(color='#4ecdc4', width=self.line_thickness), name='Write')
        self.disk_plot.addLegend()
        self.disk_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_realtime_disk() if evt.button() == Qt.MiddleButton else None)
        main_layout.addWidget(self.disk_plot)

        # Network Plot
        self.net_plot = pg.PlotWidget(title="Network Traffic (MB/s)")
        self.net_plot.setLabel('left', 'Rate', units='MB/s')
        self.net_plot.setLabel('bottom', 'Time', units='s')
        self.net_plot.setXRange(-self.time_window, 0)
        self.net_plot.showGrid(x=True, y=True, alpha=0.3)
        self.net_sent_curve = self.net_plot.plot(pen=pg.mkPen(color='#ff9ff3', width=self.line_thickness), name='Sent')
        self.net_recv_curve = self.net_plot.plot(pen=pg.mkPen(color='#54a0ff', width=self.line_thickness), name='Received')
        self.net_plot.addLegend()
        self.net_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_realtime_network() if evt.button() == Qt.MiddleButton else None)
        main_layout.addWidget(self.net_plot)

        # Apply plot theme now that plots exist
        self.apply_system_theme_to_plots()

        # Connect to state change signals to auto-save when user inverts axes
        # All graphs share the same invert_axis setting
        self.cpu_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
        self.memory_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
        self.disk_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)
        self.net_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.on_axis_changed)

        # Version label in lower right corner
        version_layout = QHBoxLayout()
        version_layout.addStretch()

        # Create version label with release info
        version_text = f"SysMon {VERSION}\nReleased: {RELEASE_DATE}"
        self.version_label = QLabel(version_text)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 12px;
                font-style: italic;
                padding: 2px;
            }
        """)
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_layout.addWidget(self.version_label)

        main_layout.addLayout(version_layout)

        # Load saved graph colors preferences (theme already applied earlier)
        self.load_graph_colors_preferences()

        # Load saved line thickness preference
        self.load_line_thickness_preference()


def main():
    app = QApplication(sys.argv)

    # Check for existing instance before creating any windows
    if not check_single_instance():
        show_instance_already_running(app)
        return 1  # Exit with error code

    # Set application icon and desktop filename (Linux taskbar association)
    app.setDesktopFileName("sysmon")  # must match sysmon.desktop
    set_application_icon(app)

    # Create and show main window
    monitor = SystemMonitor()
    monitor.show()

    # Fix Windows taskbar icon (no-op on other platforms)
    from icon_loader import icons
    icons.set_taskbar_icon(monitor)

    # Register cleanup for single instance resources
    atexit.register(cleanup_single_instance)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
