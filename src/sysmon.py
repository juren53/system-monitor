"""
SysMon - PyQtGraph-based System Monitor v0.2.0
Release: 2025-12-21

Real-time CPU, Disk I/O, and Network monitoring with smooth performance
Professional system monitoring with XDG compliance and advanced features
"""

import sys
import json
import os
import atexit
import platform
from collections import deque

# Version Information
VERSION = "0.2.2"
RELEASE_DATE = "2025-12-21"
FULL_VERSION = f"v{VERSION} ({RELEASE_DATE})"
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit,
                             QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                             QInputDialog, QColorDialog, QCheckBox, QSpinBox,
                             QGroupBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QKeySequence, QIcon, QPalette
import pyqtgraph as pg
import psutil
import time

def get_xdg_config_dir():
    """Get XDG-compliant configuration directory"""
    if platform.system() == "Windows":
        # Windows: Use AppData instead of XDG
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'sysmon')
    else:
        # Linux/macOS: Use XDG standard
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            return os.path.join(xdg_config, 'sysmon')
        else:
            return os.path.join(os.path.expanduser('~'), '.config', 'sysmon')

def ensure_config_directory(config_dir):
    """Ensure configuration directory exists"""
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

def migrate_old_config(old_config_file, new_config_dir):
    """Migrate old config file to new XDG location"""
    if os.path.exists(old_config_file) and not os.path.exists(os.path.join(new_config_dir, 'config.json')):
        try:
            # Read old config
            with open(old_config_file, 'r') as f:
                old_data = json.load(f)
            
            # Write to new location
            with open(os.path.join(new_config_dir, 'config.json'), 'w') as f:
                json.dump(old_data, f, indent=2)
            
            # Remove old file
            os.remove(old_config_file)
            return True
        except Exception as e:
            print(f"Config migration failed: {e}")
            return False
    return False

def get_config_file_path(config_dir):
    """Get main config file path"""
    return os.path.join(config_dir, 'config.json')

def get_preferences_file_path(config_dir):
    """Get preferences file path"""
    return os.path.join(config_dir, 'preferences.json')

class ProcessInfoDialog(QDialog):
    """Dialog showing top processes for a metric"""
    def __init__(self, title, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(processes)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SysMon - PyQtGraph Edition")
        
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
        self.max_points = int((self.time_window * 1000) / self.update_interval)
        
        # Data storage
        self.cpu_data = deque(maxlen=self.max_points)
        self.disk_read_data = deque(maxlen=self.max_points)
        self.disk_write_data = deque(maxlen=self.max_points)
        self.net_sent_data = deque(maxlen=self.max_points)
        self.net_recv_data = deque(maxlen=self.max_points)
        self.time_data = deque(maxlen=self.max_points)
        
        # Previous values for rate calculation
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_net_io = psutil.net_io_counters()
        self.prev_time = time.time()
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_timer()
        
        # Load preferences after timer is created
        self.load_window_geometry()
        
        # Add periodic save timer as backup
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_window_geometry)
        self.save_timer.start(30000)  # Save every 30 seconds
        
    def setup_pyqtgraph_theme(self):
        """Configure PyQtGraph to match system theme"""
        # Get system palette
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        bg_brightness = sum([bg_color.red(), bg_color.green(), bg_color.blue()]) / 3
        is_dark_theme = bg_brightness < 128
        
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
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.time_label = QLabel(f"Time Window: {self.time_window}s")
        control_layout.addWidget(self.time_label)
        
        decrease_btn = QPushButton("-")
        decrease_btn.clicked.connect(self.decrease_time_window)
        control_layout.addWidget(decrease_btn)
        
        increase_btn = QPushButton("+")
        increase_btn.clicked.connect(self.increase_time_window)
        control_layout.addWidget(increase_btn)
        
        control_layout.addStretch()
        
        info_label = QLabel("Double-click graphs for process details")
        control_layout.addWidget(info_label)
        
        main_layout.addLayout(control_layout)
        
        # Setup plots with system theme
        self.setup_pyqtgraph_theme()
        pg.setConfigOptions(antialias=True)
        
        # CPU Plot
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setLabel('left', 'Usage', units='%')
        self.cpu_plot.setLabel('bottom', 'Time', units='s')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color='#00ff00', width=2))
        self.cpu_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_top_processes('cpu') if evt.double() else None)
        main_layout.addWidget(self.cpu_plot)
        
        # Disk I/O Plot
        self.disk_plot = pg.PlotWidget(title="Disk I/O (MB/s)")
        self.disk_plot.setLabel('left', 'Rate', units='MB/s')
        self.disk_plot.setLabel('bottom', 'Time', units='s')
        self.disk_plot.showGrid(x=True, y=True, alpha=0.3)
        self.disk_read_curve = self.disk_plot.plot(pen=pg.mkPen(color='#ff6b6b', width=2), name='Read')
        self.disk_write_curve = self.disk_plot.plot(pen=pg.mkPen(color='#4ecdc4', width=2), name='Write')
        self.disk_plot.addLegend()
        self.disk_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_top_processes('disk') if evt.double() else None)
        main_layout.addWidget(self.disk_plot)
        
        # Network Plot
        self.net_plot = pg.PlotWidget(title="Network Traffic (MB/s)")
        self.net_plot.setLabel('left', 'Rate', units='MB/s')
        self.net_plot.setLabel('bottom', 'Time', units='s')
        self.net_plot.showGrid(x=True, y=True, alpha=0.3)
        self.net_sent_curve = self.net_plot.plot(pen=pg.mkPen(color='#ff9ff3', width=2), name='Sent')
        self.net_recv_curve = self.net_plot.plot(pen=pg.mkPen(color='#54a0ff', width=2), name='Received')
        self.net_plot.addLegend()
        self.net_plot.scene().sigMouseClicked.connect(
            lambda evt: self.show_top_processes('network') if evt.double() else None)
        main_layout.addWidget(self.net_plot)
        
        # Version label in lower right corner
        version_layout = QHBoxLayout()
        version_layout.addStretch()
        
        # Create version label with release info
        version_text = f"SysMon {VERSION}\nReleased: {RELEASE_DATE}"
        self.version_label = QLabel(version_text)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 9px;
                font-style: italic;
                padding: 2px;
            }
        """)
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_layout.addWidget(self.version_label)
        
        main_layout.addLayout(version_layout)
        
        # Apply system theme to plots
        self.apply_system_theme_to_plots()
        
    def apply_system_theme_to_plots(self):
        """Apply system theme colors to plots"""
        # Get system palette
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        bg_brightness = sum([bg_color.red(), bg_color.green(), bg_color.blue()]) / 3
        is_dark_theme = bg_brightness < 128
        
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
        self.cpu_curve.setPen(pg.mkPen(color=cpu_color, width=2))
        self.cpu_plot.getAxis('left').setPen(axis_color)
        self.cpu_plot.getAxis('bottom').setPen(axis_color)
        self.cpu_plot.getAxis('left').setTextPen(text_color)
        self.cpu_plot.getAxis('bottom').setTextPen(text_color)
        
        # Apply colors to Disk plot
        self.disk_read_curve.setPen(pg.mkPen(color=disk_read_color, width=2))
        self.disk_write_curve.setPen(pg.mkPen(color=disk_write_color, width=2))
        self.disk_plot.getAxis('left').setPen(axis_color)
        self.disk_plot.getAxis('bottom').setPen(axis_color)
        self.disk_plot.getAxis('left').setTextPen(text_color)
        self.disk_plot.getAxis('bottom').setTextPen(text_color)
        
        # Apply colors to Network plot
        self.net_sent_curve.setPen(pg.mkPen(color=net_sent_color, width=2))
        self.net_recv_curve.setPen(pg.mkPen(color=net_recv_color, width=2))
        self.net_plot.getAxis('left').setPen(axis_color)
        self.net_plot.getAxis('bottom').setPen(axis_color)
        self.net_plot.getAxis('left').setTextPen(text_color)
        self.net_plot.getAxis('bottom').setTextPen(text_color)
        
    def setup_menu_bar(self):
        """Setup the application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        save_data_action = QAction('&Save Data...', self)
        save_data_action.setShortcut('Ctrl+S')
        save_data_action.setStatusTip('Save monitoring data to file')
        save_data_action.triggered.connect(self.save_data)
        file_menu.addAction(save_data_action)
        
        export_graph_action = QAction('&Export Graph...', self)
        export_graph_action.setShortcut('Ctrl+E')
        export_graph_action.setStatusTip('Export graph as image')
        export_graph_action.triggered.connect(self.export_graph)
        file_menu.addAction(export_graph_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu('&Edit')
        
        copy_graph_action = QAction('&Copy Graph to Clipboard', self)
        copy_graph_action.setShortcut('Ctrl+C')
        copy_graph_action.setStatusTip('Copy current graph to clipboard')
        copy_graph_action.triggered.connect(self.copy_graph)
        edit_menu.addAction(copy_graph_action)
        
        clear_data_action = QAction('&Clear All Data', self)
        clear_data_action.setShortcut('Ctrl+Del')
        clear_data_action.setStatusTip('Clear all monitoring data')
        clear_data_action.triggered.connect(self.clear_data)
        edit_menu.addAction(clear_data_action)
        
        edit_menu.addSeparator()
        
        reset_settings_action = QAction('&Reset Settings', self)
        reset_settings_action.setStatusTip('Reset all settings to defaults')
        reset_settings_action.triggered.connect(self.reset_settings)
        edit_menu.addAction(reset_settings_action)
        
        # View Menu
        view_menu = menubar.addMenu('&View')
        
        self.show_cpu_action = QAction('Show &CPU', self, checkable=True)
        self.show_cpu_action.setChecked(True)
        self.show_cpu_action.triggered.connect(self.toggle_cpu_plot)
        view_menu.addAction(self.show_cpu_action)
        
        self.show_disk_action = QAction('Show &Disk I/O', self, checkable=True)
        self.show_disk_action.setChecked(True)
        self.show_disk_action.triggered.connect(self.toggle_disk_plot)
        view_menu.addAction(self.show_disk_action)
        
        self.show_network_action = QAction('Show &Network', self, checkable=True)
        self.show_network_action.setChecked(True)
        self.show_network_action.triggered.connect(self.toggle_network_plot)
        view_menu.addAction(self.show_network_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction('&Full Screen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.setStatusTip('Toggle full screen mode')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Config Menu
        config_menu = menubar.addMenu('&Config')
        
        update_interval_action = QAction('&Update Interval...', self)
        update_interval_action.setStatusTip('Change data update interval')
        update_interval_action.triggered.connect(self.change_update_interval)
        config_menu.addAction(update_interval_action)
        
        time_window_action = QAction('&Time Window Settings...', self)
        time_window_action.setStatusTip('Configure time window settings')
        time_window_action.triggered.connect(self.change_time_window_settings)
        config_menu.addAction(time_window_action)
        
        graph_colors_action = QAction('&Graph Colors...', self)
        graph_colors_action.setStatusTip('Customize graph colors')
        graph_colors_action.triggered.connect(self.customize_graph_colors)
        config_menu.addAction(graph_colors_action)
        
        config_menu.addSeparator()
        
        transparency_action = QAction('&Transparency...', self)
        transparency_action.setStatusTip('Set window transparency for see-through mode')
        transparency_action.triggered.connect(self.change_transparency)
        config_menu.addAction(transparency_action)
        
        self.always_on_top_action = QAction('&Always On Top', self, checkable=True)
        self.always_on_top_action.setStatusTip('Keep window always on top of other windows')
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        config_menu.addAction(self.always_on_top_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        changelog_action = QAction('&ChangeLog', self)
        changelog_action.setStatusTip('View SysMon development history and changes')
        changelog_action.triggered.connect(self.show_changelog)
        help_menu.addAction(changelog_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('&About', self)
        about_action.setStatusTip('About SysMon')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_timer(self):
        """Setup update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(self.update_interval)
        
    def update_data(self):
        """Update all monitoring data"""
        current_time = time.time()
        elapsed = current_time - self.prev_time
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_data.append(cpu_percent)
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io and self.prev_disk_io:
            read_rate = (disk_io.read_bytes - self.prev_disk_io.read_bytes) / elapsed / (1024**2)
            write_rate = (disk_io.write_bytes - self.prev_disk_io.write_bytes) / elapsed / (1024**2)
            self.disk_read_data.append(max(0, read_rate))
            self.disk_write_data.append(max(0, write_rate))
            self.prev_disk_io = disk_io
        
        # Network I/O
        net_io = psutil.net_io_counters()
        if net_io and self.prev_net_io:
            sent_rate = (net_io.bytes_sent - self.prev_net_io.bytes_sent) / elapsed / (1024**2)
            recv_rate = (net_io.bytes_recv - self.prev_net_io.bytes_recv) / elapsed / (1024**2)
            self.net_sent_data.append(max(0, sent_rate))
            self.net_recv_data.append(max(0, recv_rate))
            self.prev_net_io = net_io
        
        # Time axis
        if len(self.time_data) == 0:
            self.time_data.append(0)
        else:
            self.time_data.append(self.time_data[-1] + elapsed)
        
        self.prev_time = current_time
        
        # Update plots
        self.update_plots()
        
    def update_plots(self):
        """Update all plot curves"""
        if len(self.time_data) == 0:
            return
            
        # Normalize time axis to show last N seconds
        time_array = [t - self.time_data[-1] for t in self.time_data]
        
        # Update CPU
        self.cpu_curve.setData(time_array, list(self.cpu_data))
        
        # Update Disk I/O
        self.disk_read_curve.setData(time_array, list(self.disk_read_data))
        self.disk_write_curve.setData(time_array, list(self.disk_write_data))
        
        # Update Network
        self.net_sent_curve.setData(time_array, list(self.net_sent_data))
        self.net_recv_curve.setData(time_array, list(self.net_recv_data))
        
    def increase_time_window(self):
        """Increase time window by 5 seconds"""
        self.time_window = min(120, self.time_window + 5)
        self.update_time_window()
        
    def decrease_time_window(self):
        """Decrease time window by 5 seconds"""
        self.time_window = max(5, self.time_window - 5)
        self.update_time_window()
        
    def update_time_window(self):
        """Update time window and adjust data buffers"""
        self.max_points = int((self.time_window * 1000) / self.update_interval)
        
        # Update all deques with new maxlen
        for data_list in [self.cpu_data, self.disk_read_data, self.disk_write_data,
                         self.net_sent_data, self.net_recv_data, self.time_data]:
            if len(data_list) > self.max_points:
                # Trim from the left
                for _ in range(len(data_list) - self.max_points):
                    data_list.popleft()
        
        # Update x-axis range
        self.cpu_plot.setXRange(-self.time_window, 0)
        self.disk_plot.setXRange(-self.time_window, 0)
        self.net_plot.setXRange(-self.time_window, 0)
        
        self.time_label.setText(f"Time Window: {self.time_window}s")
        
    def show_top_processes(self, metric_type):
        """Show top processes for the specified metric"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    
                    if metric_type == 'cpu':
                        value = proc.cpu_percent(interval=0.1)
                        key = 'cpu_percent'
                    elif metric_type == 'disk':
                        io = proc.io_counters()
                        value = (io.read_bytes + io.write_bytes) / (1024**2)
                        key = 'disk_mb'
                    elif metric_type == 'network':
                        io = proc.io_counters()
                        value = (io.read_bytes + io.write_bytes) / (1024**2)
                        key = 'net_mb'
                    else:
                        continue
                    
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        key: value
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort and get top 10
            sort_key = 'cpu_percent' if metric_type == 'cpu' else f'{metric_type}_mb'
            top_procs = sorted(processes, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
            
            # Format output
            if metric_type == 'cpu':
                title = "Top 10 CPU Consumers"
                header = f"{'PID':<8} {'Name':<30} {'CPU %':>10}\n" + "="*50 + "\n"
                lines = [f"{p['pid']:<8} {p['name'][:30]:<30} {p['cpu_percent']:>9.1f}%" 
                        for p in top_procs]
            else:
                title = f"Top 10 {metric_type.title()} I/O Processes"
                header = f"{'PID':<8} {'Name':<30} {'MB':>10}\n" + "="*50 + "\n"
                lines = [f"{p['pid']:<8} {p['name'][:30]:<30} {p[sort_key]:>9.2f}" 
                        for p in top_procs]
            
            output = header + "\n".join(lines)
            
            dialog = ProcessInfoDialog(title, output, self)
            dialog.exec_()
            
        except Exception as e:
            print(f"Error getting process info: {e}")
    
    # Window Geometry Methods
    def closeEvent(self, event):
        """Handle window close event to save geometry"""
        try:
            self.save_window_geometry()
            print("Window geometry saved successfully")
        except Exception as e:
            print(f"Failed to save window geometry: {e}")
        event.accept()
    
    def load_window_geometry(self):
        """Load saved window geometry and preferences"""
        try:
            # Load main config (window geometry, etc.)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    geometry = config.get('window_geometry', {})
                    if geometry:
                        # Convert back to QByteArray format
                        geometry_data = geometry.get('geometry', '')
                        state_data = geometry.get('state', '')
                        
                        if geometry_data:
                            from PyQt5.QtCore import QByteArray
                            geo_bytes = QByteArray(geometry_data.encode('latin1'))
                            state_bytes = QByteArray(state_data.encode('latin1'))
                            
                            self.restoreGeometry(geo_bytes)
                            self.restoreState(state_bytes)
                        else:
                            # Backwards compatibility: handle old x,y,window_size format
                            x = config.get('x')
                            y = config.get('y') 
                            window_size = config.get('window_size')
                            if x is not None and y is not None and window_size:
                                self.move(x, y)
                                self.resize(window_size[0], window_size[1])
            
            # Load user preferences
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    self.update_interval = prefs.get('update_interval', 200)
                    self.time_window = prefs.get('time_window', 30)
                    self.transparency = prefs.get('transparency', 1.0)
                    self.always_on_top = prefs.get('always_on_top', False)
                    
                    # Apply loaded preferences
                    if hasattr(self, 'timer'):
                        self.timer.setInterval(self.update_interval)
                    self.max_points = int((self.time_window * 1000) / self.update_interval)
                    self.set_window_transparency(self.transparency)
                    self.set_always_on_top(self.always_on_top)
                    self.always_on_top_action.setChecked(self.always_on_top)
                    
        except Exception as e:
            print(f"Failed to load configuration: {e}")
    
    def save_window_geometry(self):
        """Save window geometry and preferences"""
        try:
            # Use Qt's proper geometry serialization
            geometry_data = {
                'geometry': self.saveGeometry().data().decode('latin1'),
                'state': self.saveState().data().decode('latin1')
            }
            
            config = {
                'window_geometry': geometry_data
            }
            
            # Load existing config and merge if it exists
            existing_config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        existing_config = json.load(f)
                except:
                    existing_config = {}
            
            # Merge new settings with existing ones
            existing_config.update(config)
            
            # Save main config (window geometry, etc.)
            with open(self.config_file, 'w') as f:
                json.dump(existing_config, f, indent=2)
                # print(f"Saved configuration to: {self.config_file}")  # Debug output
        except Exception as e:
            print(f"Failed to save configuration: {e}")  # Debug output
    
    def save_preferences(self):
        """Save user preferences to separate preferences file"""
        try:
            preferences = {
                'update_interval': self.update_interval,
                'time_window': self.time_window,
                'transparency': self.transparency,
                'always_on_top': self.always_on_top
            }
            
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
                
            print(f"Saved preferences to: {self.preferences_file}")
        except Exception as e:
            print(f"Failed to save preferences: {e}")
    
    # File Menu Methods
    def save_data(self):
        """Save monitoring data to CSV file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Data", "", "CSV Files (*.csv);;All Files (*)")
            
            if file_path:
                import csv
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Time', 'CPU %', 'Disk Read (MB/s)', 'Disk Write (MB/s)', 
                                   'Network Sent (MB/s)', 'Network Received (MB/s)'])
                    
                    for i, time_val in enumerate(self.time_data):
                        writer.writerow([
                            time_val,
                            self.cpu_data[i] if i < len(self.cpu_data) else '',
                            self.disk_read_data[i] if i < len(self.disk_read_data) else '',
                            self.disk_write_data[i] if i < len(self.disk_write_data) else '',
                            self.net_sent_data[i] if i < len(self.net_sent_data) else '',
                            self.net_recv_data[i] if i < len(self.net_recv_data) else ''
                        ])
                
                QMessageBox.information(self, "Success", f"Data saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
    
    def export_graph(self):
        """Export current graph view as image"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Graph", "", "PNG Files (*.png);;All Files (*)")
            
            if file_path:
                # Get screen capture of the main window
                import os
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                screenshot = screen.grabWindow(self.winId())
                screenshot.save(file_path, 'png')
                
                QMessageBox.information(self, "Success", f"Graph exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export graph: {str(e)}")
    
    # Edit Menu Methods
    def copy_graph(self):
        """Copy current graph to clipboard"""
        try:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())
            QApplication.clipboard().setImage(screenshot.toImage())
            QMessageBox.information(self, "Success", "Graph copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy graph: {str(e)}")
    
    def clear_data(self):
        """Clear all monitoring data"""
        reply = QMessageBox.question(self, 'Clear Data', 
                                   'Are you sure you want to clear all monitoring data?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.cpu_data.clear()
            self.disk_read_data.clear()
            self.disk_write_data.clear()
            self.net_sent_data.clear()
            self.net_recv_data.clear()
            self.time_data.clear()
            self.update_plots()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, 'Reset Settings', 
                                   'Are you sure you want to reset all settings to defaults?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.time_window = 20
            self.update_interval = 200
            self.transparency = 1.0
            self.always_on_top = False
            self.max_points = int((self.time_window * 1000) / self.update_interval)
            self.timer.setInterval(self.update_interval)
            self.update_time_window()
            self.set_window_transparency(self.transparency)
            self.set_always_on_top(self.always_on_top)
            self.always_on_top_action.setChecked(self.always_on_top)
            
            # Remove config file to reset window geometry
            try:
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
                if os.path.exists(self.preferences_file):
                    os.remove(self.preferences_file)
            except:
                pass
            
            QMessageBox.information(self, "Success", "Settings reset to defaults\n\nConfig file removed - window will reset to default size and position on next restart.")
    
    # View Menu Methods
    def toggle_cpu_plot(self):
        """Toggle CPU plot visibility"""
        self.cpu_plot.setVisible(self.show_cpu_action.isChecked())
    
    def toggle_disk_plot(self):
        """Toggle Disk I/O plot visibility"""
        self.disk_plot.setVisible(self.show_disk_action.isChecked())
    
    def toggle_network_plot(self):
        """Toggle Network plot visibility"""
        self.net_plot.setVisible(self.show_network_action.isChecked())
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    # Config Menu Methods
    def change_update_interval(self):
        """Change data update interval"""
        interval, ok = QInputDialog.getInt(
            self, 'Update Interval', 'Update interval (milliseconds):', 
            self.update_interval, 50, 5000, 50)
        
        if ok:
            self.update_interval = interval
            self.timer.setInterval(interval)
            self.max_points = int((self.time_window * 1000) / self.update_interval)
            self.update_time_window()
            self.save_preferences()
    
    def change_time_window_settings(self):
        """Configure time window settings"""
        time_window, ok = QInputDialog.getInt(
            self, 'Time Window', 'Time window (seconds):', 
            self.time_window, 5, 300, 5)
        
        if ok:
            self.time_window = time_window
            self.update_time_window()
            self.save_preferences()
    
    def customize_graph_colors(self):
        """Customize graph colors"""
        color = QColorDialog.getColor()
        if color.isValid():
            # For simplicity, change CPU curve color
            self.cpu_curve.setPen(pg.mkPen(color=color, width=2))
    
    def set_window_transparency(self, transparency):
        """Set window transparency (0.0 to 1.0)"""
        self.transparency = max(0.1, min(1.0, transparency))  # Clamp between 0.1 and 1.0
        self.setWindowOpacity(self.transparency)
    
    def change_transparency(self):
        """Change window transparency through slider dialog"""
        from PyQt5.QtWidgets import QSlider, QVBoxLayout, QHBoxLayout, QLabel, QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Window Transparency")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Explanation label
        info_label = QLabel("Set window transparency for see-through mode:\n")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Current value label
        value_label = QLabel(f"Current: {int(self.transparency * 100)}%")
        layout.addWidget(value_label)
        
        # Transparency slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(10)  # 10% minimum for visibility
        slider.setMaximum(100)  # 100% = fully opaque
        slider.setValue(int(self.transparency * 100))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(10)
        layout.addWidget(slider)
        
        # Percentage labels
        percent_layout = QHBoxLayout()
        percent_layout.addWidget(QLabel("10%"))
        percent_layout.addStretch()
        percent_layout.addWidget(QLabel("50%"))
        percent_layout.addStretch()
        percent_layout.addWidget(QLabel("100%"))
        layout.addLayout(percent_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Reset")
        
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connect signals
        def update_value(value):
            value_label.setText(f"Current: {value}%")
            # Preview transparency in real-time
            self.set_window_transparency(value / 100.0)
        
        def reset_transparency():
            slider.setValue(100)
        
        def accept_changes():
            self.transparency = slider.value() / 100.0
            self.save_preferences()
            dialog.accept()
        
        def reject_changes():
            # Restore original transparency
            self.set_window_transparency(self.transparency)
            dialog.reject()
        
        slider.valueChanged.connect(update_value)
        ok_button.clicked.connect(accept_changes)
        cancel_button.clicked.connect(reject_changes)
        reset_button.clicked.connect(reset_transparency)
        
        # Store original transparency in case of cancel
        original_transparency = self.transparency
        
        # Show dialog
        dialog.exec_()
        
        # If dialog was rejected, restore original
        if dialog.result() == QDialog.Rejected:
            self.set_window_transparency(original_transparency)
    
    def set_always_on_top(self, always_on_top):
        """Set window always on top state"""
        self.always_on_top = always_on_top
        
        # Set window flags based on always on top state
        flags = self.windowFlags()
        if always_on_top:
            # Add WindowStaysOnTopHint flag
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            # Remove WindowStaysOnTopHint flag
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        
        # Show the window again to apply the new flags
        self.show()
    
    def toggle_always_on_top(self):
        """Toggle always on top state"""
        self.always_on_top = not self.always_on_top
        self.set_always_on_top(self.always_on_top)
        self.save_preferences()
    
    # Help Menu Methods
    def show_changelog(self):
        """Show changelog dialog"""
        # Try to read the changelog file
        changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'CHANGELOG.md')
        
        try:
            with open(changelog_path, 'r', encoding='utf-8', errors='replace') as f:
                changelog_content = f.read()
        except Exception as e:
            changelog_content = f"""# ChangeLog

Unable to load CHANGELOG.md file.

Error: {str(e)}

Please check the docs/CHANGELOG.md file in the SysMon repository."""
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon ChangeLog")
        dialog.setModal(True)
        dialog.resize(900, 700)
        
        layout = QVBoxLayout()
        
        # Create text area with changelog content
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setPlainText(changelog_content)
        text_area.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                padding: 12px;
                selection-background-color: #0078d7;
                selection-color: white;
            }
        """)
        layout.addWidget(text_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Show dialog
        dialog.exec_()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <b>SysMon - PyQtGraph Edition</b><br><br>
        Real-time system monitoring with PyQtGraph<br><br>
        <b>Features:</b><br>
        • CPU, Disk I/O, and Network monitoring<br>
        • Real-time graphs with smooth performance<br>
        • Process drill-down information<br>
        • Window transparency and always-on-top<br>
        • XDG-compliant configuration<br>
        • Professional menu system<br>
        • Automatic system theme detection<br>
        • Customizable time windows and colors<br><br>
        <b>Version:</b> {FULL_VERSION} (Production Release)<br>
        <b>Release Date:</b> {RELEASE_DATE}<br>
        <b>Author:</b> System Monitor Project<br><br>
        <b>Libraries:</b><br>
        • PyQt5 - GUI Framework<br>
        • PyQtGraph - High-performance plotting<br>
        • psutil - System information<br>
        • Platform detection - Cross-platform support<br>
        """
        
        QMessageBox.about(self, "About SysMon", about_text)

def main():
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
