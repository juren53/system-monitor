#!/usr/bin/env python3
"""
SysMon - PyQtGraph-based System Monitor v0.2.9
Release: 2025-12-23 1052 CST

Real-time CPU, Disk I/O, and Network monitoring with smooth performance
Professional system monitoring with XDG compliance and advanced features
"""

import sys
import json
import os
import atexit
import platform
import datetime
import threading
import time
from collections import deque

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit,
                              QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                              QInputDialog, QColorDialog, QCheckBox, QSpinBox,
                              QGroupBox, QFormLayout, QDialogButtonBox, QComboBox)
from PyQt5.QtCore import QTimer, Qt, QSize, QSharedMemory, QSystemSemaphore, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence, QIcon, QPalette, QFont, QColor
from PyQt5.QtGui import QGuiApplication
import pyqtgraph as pg
import psutil

def filter_stderr_gdkpixbuf():
    """Filter out harmless GdkPixbuf critical warnings on Linux"""
    import threading
    import sys
    import os
    
    def stderr_filter_thread():
        """Background thread to filter stderr output"""
        import subprocess
        import select
        
        # Create pipe for stderr
        r, w = os.pipe()
        
        # Redirect stderr to our pipe
        old_stderr = sys.stderr.fileno()
        os.dup2(w, old_stderr)
        os.close(w)
        
        while True:
            try:
                # Wait for data on stderr
                ready, _, _ = select.select([r], [], [], 0.1)
                if ready:
                    data = os.read(r, 8192).decode('utf-8', errors='ignore')
                    if data:
                        lines = data.split('\n')
                        for line in lines:
                            # Filter out GdkPixbuf critical warnings
                            if ('GdkPixbuf-CRITICAL' in line and 
                                ('gdk_pixbuf_get_' in line or 
                                 'GDK_IS_PIXBUF' in line)):
                                # Skip these harmless warnings
                                continue
                            elif line.strip():
                                # Print other error messages
                                print(line, file=sys.stderr, flush=True)
            except (OSError, KeyboardInterrupt):
                break
            except Exception:
                break
    
    # Start filter thread only on Linux systems
    if platform.system() == "Linux":
        try:
            filter_thread = threading.Thread(target=stderr_filter_thread, daemon=True)
            filter_thread.start()
        except Exception:
            # If filtering fails, continue without it
            pass

# Apply stderr filtering at startup
filter_stderr_gdkpixbuf()

# Version Information
VERSION = "0.2.9"
RELEASE_DATE = "2025-12-23"
RELEASE_TIME = "1930 CST"
FULL_VERSION = f"v{VERSION} {RELEASE_DATE} {RELEASE_TIME}"

# Build Information
BUILD_DATE = "2025-12-23"
BUILD_TIME = "1930 CST"
BUILD_INFO = f"{BUILD_DATE} {BUILD_TIME}"

# Runtime Information
APPLICATION_START_TIME = datetime.datetime.now()
PYTHON_VERSION = sys.version.split()[0]
PLATFORM_INFO = platform.platform()

# Single instance management
shared_memory = None
system_semaphore = None

def check_single_instance():
    """Check if SysMon is already running using Qt native mechanisms"""
    global shared_memory, system_semaphore
    
    # Use version-specific keys to allow different versions to coexist
    instance_key = f"sysmon-v{VERSION}-instance"
    semaphore_key = f"sysmon-v{VERSION}-semaphore"
    
    # Create system semaphore for thread safety
    if system_semaphore is None:
        system_semaphore = QSystemSemaphore(semaphore_key, 1)
    
    system_semaphore.acquire()  # Raise semaphore to prevent race conditions
    
    # On Linux/Unix, clean up shared memory from abnormal terminations
    if sys.platform != 'win32':
        cleanup_shared_mem = QSharedMemory(instance_key)
        if cleanup_shared_mem.attach():
            cleanup_shared_mem.detach()
    
    # Try to create shared memory
    if shared_memory is None:
        shared_memory = QSharedMemory(instance_key)
    
    if shared_memory.attach():
        # Shared memory exists - application is already running
        system_semaphore.release()
        return False
    else:
        # Create shared memory for this instance
        if not shared_memory.create(1):
            # Failed to create - another instance started simultaneously
            system_semaphore.release()
            return False
        
        # Successfully created shared memory
        system_semaphore.release()
        return True

def cleanup_single_instance():
    """Clean up single instance resources"""
    global shared_memory, system_semaphore
    
    try:
        if shared_memory:
            if shared_memory.isAttached():
                shared_memory.detach()
    except Exception:
        pass  # Ignore cleanup errors
    
    try:
        if system_semaphore:
            system_semaphore.release()
    except Exception:
        pass  # Ignore cleanup errors

def show_instance_already_running(app):
    """Show message box when another instance is detected"""
    # Validate app parameter
    if app is None:
        print("Error: Invalid QApplication instance")
        return
    
    # Process pending events to ensure app is properly initialized
    app.processEvents()
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle('SysMon Already Running')
    msg_box.setText('SysMon is already running on this system.\n\n'
                   'Only one instance of SysMon can run at same time.\n\n'
                   'If you believe this is an error, please check your running processes.')
    msg_box.setStandardButtons(QMessageBox.Ok)
    
    # Show dialog and process events manually since main event loop isn't running
    msg_box.show()
    
    # Process events until dialog is closed
    while msg_box.isVisible():
        app.processEvents()
        time.sleep(0.01)  # Small delay to prevent CPU spinning

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

class ProcessWorker(QObject):
    """Worker for async process analysis"""
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, metric_type):
        super().__init__()
        self.metric_type = metric_type
        self._cancelled = False
        
    def cancel(self):
        """Cancel the operation"""
        self._cancelled = True
        
    def run(self):
        """Run process analysis"""
        try:
            processes = []
            total_checked = 0
            max_processes = 200  # Limit scan to prevent excessive scanning
            
            # Use non-blocking approach for CPU
            if self.metric_type == 'cpu':
                # First pass: get basic CPU info without interval
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    if self._cancelled:
                        return
                    total_checked += 1
                    if total_checked > max_processes:
                        break
                        
                    try:
                        info = proc.info
                        # Use cached cpu_percent if available, otherwise use current value
                        cpu_value = info.get('cpu_percent', 0.0)
                        if cpu_value is None:
                            cpu_value = 0.0
                            
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu_percent': cpu_value
                        })
                        
                        if total_checked % 50 == 0:
                            self.progress.emit(int((total_checked / min(max_processes, len(list(psutil.process_iter())))) * 100))
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            else:
                # For disk/network, collect more efficiently
                for proc in psutil.process_iter(['pid', 'name']):
                    if self._cancelled:
                        return
                    total_checked += 1
                    if total_checked > max_processes:
                        break
                        
                    try:
                        info = proc.info
                        
                        if self.metric_type == 'disk':
                            try:
                                io = proc.io_counters()
                                value = (io.read_bytes + io.write_bytes) / (1024**2)
                                key = 'disk_mb'
                                    
                                processes.append({
                                    'pid': info['pid'],
                                    'name': info['name'],
                                    key: value
                                })
                            except (psutil.AccessDenied, AttributeError):
                                continue
                        elif self.metric_type == 'network':
                            try:
                                connections = proc.connections()
                                value = len(connections)  # Count network connections
                                key = 'net_connections'
                                    
                                processes.append({
                                    'pid': info['pid'],
                                    'name': info['name'],
                                    key: value
                                })
                            except (psutil.AccessDenied, AttributeError):
                                continue
                                
                        if total_checked % 50 == 0:
                            self.progress.emit(int((total_checked / min(max_processes, len(list(psutil.process_iter())))) * 100))
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            # Sort and get top 10
            if self.metric_type == 'cpu':
                sort_key = 'cpu_percent'
            elif self.metric_type == 'disk':
                sort_key = 'disk_mb'
            else:  # network
                sort_key = 'net_connections'
            top_procs = sorted(processes, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
            
            self.finished.emit(top_procs)
            
        except Exception as e:
            self.error.emit(f"Error analyzing processes: {str(e)}")


class ProcessInfoDialog(QDialog):
    """Dialog showing top processes for a metric"""
    def __init__(self, title, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(550, 400)  # Increased width for better alignment
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        # Apply monospace font for proper alignment
        font = QFont("Monospace", 11)
        font.setFixedPitch(True)
        text_edit.setFont(font)
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
        self.max_points = int((self.time_window * 1000) / self.update_interval)
        
        # Data storage
        self.cpu_data = deque(maxlen=self.max_points)
        self.disk_read_data = deque(maxlen=self.max_points)
        self.disk_write_data = deque(maxlen=self.max_points)
        self.net_sent_data = deque(maxlen=self.max_points)
        self.net_recv_data = deque(maxlen=self.max_points)
        self.time_data = deque(maxlen=self.max_points)
        
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
    
    def set_window_icon(self):
        """Set window icon with proper error handling"""
        import os
        
        # Icon search paths (same as set_application_icon but for instance level)
        icon_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'icons', 'ICON_SysMon.png'),
            os.path.join(os.path.dirname(__file__), '..', 'icons', 'ICON_SysMon.ico'),
            os.path.join(os.getcwd(), 'icons', 'ICON_SysMon.png'),
            os.path.join(os.getcwd(), 'icons', 'ICON_SysMon.ico'),
            'icons/ICON_SysMon.png',
            'icons/ICON_SysMon.ico'
        ]
        
        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        return
            except Exception:
                continue
        # If no icon found, continue silently (application icon should be set already)
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Memory info panel
        memory_layout = QHBoxLayout()
        
        self.ram_label = QLabel("Ram: --/--/--")
        self.ram_label.setStyleSheet("QLabel { font-weight: bold; color: #2196F3; }")
        memory_layout.addWidget(self.ram_label)
        
        memory_layout.addStretch()
        
        self.swap_label = QLabel("Swap: --/--/--")
        self.swap_label.setStyleSheet("QLabel { font-weight: bold; color: #FF9800; }")
        memory_layout.addWidget(self.swap_label)
        
        main_layout.addLayout(memory_layout)
        
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
                font-size: 12px;
                font-style: italic;
                padding: 2px;
            }
        """)
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_layout.addWidget(self.version_label)
        
        main_layout.addLayout(version_layout)
        
        # Apply system theme to plots
        self.apply_system_theme_to_plots()
        
        # Load saved graph colors preferences
        self.load_graph_colors_preferences()
        
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
        graph_colors_action.setShortcut('Ctrl+G')  # Add keyboard shortcut
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
        
        users_guide_action = QAction('&Users Guide', self)
        users_guide_action.setStatusTip('Open comprehensive user documentation')
        users_guide_action.triggered.connect(self.show_users_guide)
        help_menu.addAction(users_guide_action)
        
        help_menu.addSeparator()
        
        navigation_action = QAction('&Keyboard Shortcuts', self)
        navigation_action.setStatusTip('View available keyboard shortcuts and navigation')
        navigation_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(navigation_action)
        
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
        
        # Memory information
        memory = psutil.virtual_memory()
        self.ram_total = memory.total / (1024**2)  # Convert to MB
        self.ram_available = memory.available / (1024**2)  # Convert to MB
        self.ram_percent = memory.percent
        
        # Swap information
        swap = psutil.swap_memory()
        self.swap_total = swap.total / (1024**2)  # Convert to MB
        self.swap_available = swap.free / (1024**2)  # Convert to MB
        self.swap_percent = swap.percent
        
        # Time axis
        if len(self.time_data) == 0:
            self.time_data.append(0)
        else:
            self.time_data.append(self.time_data[-1] + elapsed)
        
        self.prev_time = current_time
        
        # Update memory display labels
        self.ram_label.setText(f"Ram: {self.ram_total/1024:.1f}GB | {self.ram_available/1024:.1f}GB | {self.ram_percent:.0f}%")
        self.swap_label.setText(f"Swap: {self.swap_total/1024:.1f}GB | {self.swap_available/1024:.1f}GB | {self.swap_percent:.0f}%")
        
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
        
    def show_top_processes(self, metric_type):
        """Show top processes for the specified metric with async processing"""
        # Create progress dialog
        from PyQt5.QtWidgets import QProgressDialog, QApplication
        progress = QProgressDialog("Analyzing processes...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Process Analysis")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Create worker and thread
        self.process_worker = ProcessWorker(metric_type)
        self.process_thread = QThread()
        
        # Move worker to thread
        self.process_worker.moveToThread(self.process_thread)
        
        # Connect signals
        self.process_worker.finished.connect(self.process_thread.quit)
        self.process_worker.finished.connect(self.process_worker.deleteLater)
        self.process_worker.error.connect(self.process_thread.quit)
        self.process_worker.error.connect(self.process_worker.deleteLater)
        self.process_worker.progress.connect(progress.setValue)
        self.process_thread.started.connect(self.process_worker.run)
        
        # Handle completion
        self.process_worker.finished.connect(lambda top_procs: self.on_process_analysis_complete(top_procs, metric_type, progress))
        self.process_worker.error.connect(lambda error: self.on_process_analysis_error(error, progress))
        
        # Handle cancellation
        progress.canceled.connect(self.cancel_process_analysis)
        
        # Start analysis
        self.process_thread.start()
        
        # Keep the event loop responsive
        QApplication.processEvents()
    
    def cancel_process_analysis(self):
        """Cancel the ongoing process analysis"""
        if hasattr(self, 'process_worker') and self.process_worker:
            self.process_worker.cancel()
        if hasattr(self, 'process_thread') and self.process_thread:
            self.process_thread.quit()
            self.process_thread.wait()
    
    def on_process_analysis_complete(self, top_procs, metric_type, progress):
        """Handle completion of process analysis"""
        progress.close()
        
        if not top_procs:
            QMessageBox.information(self, "No Data", "No process data available.")
            return
        
        # Format output
        if metric_type == 'cpu':
            title = "Top 10 CPU Consumers"
            header = f"{'PID':<8} {'Name':<30} {'CPU %':>12}\n" + "="*52 + "\n"
            lines = [f"{p['pid']:<8} {p['name'][:30]:<30} {p['cpu_percent']:>11.1f}%" 
                    for p in top_procs]
        else:
            if metric_type == 'disk':
                title = "Top 10 Disk I/O Processes"
                sort_key = 'disk_mb'
                header = f"{'PID':<8} {'Name':<30} {'MB':>12}\n" + "="*52 + "\n"
                lines = [f"{p['pid']:<8} {p['name'][:30]:<30} {p[sort_key]:>11.2f}" 
                        for p in top_procs]
            else:  # network
                title = "Top 10 Network-Active Processes"
                sort_key = 'net_connections'
                header = f"{'PID':<8} {'Name':<30} {'Connections':>12}\n" + "="*52 + "\n"
                lines = [f"{p['pid']:<8} {p['name'][:30]:<30} {p[sort_key]:>12}" 
                        for p in top_procs]
        
        output = header + "\n".join(lines)
        
        dialog = ProcessInfoDialog(title, output, self)
        dialog.exec_()
        
        # Clean up thread
        if hasattr(self, 'process_thread') and self.process_thread:
            self.process_thread.deleteLater()
    
    def on_process_analysis_error(self, error, progress):
        """Handle process analysis error"""
        progress.close()
        QMessageBox.critical(self, "Error", error)
        
        # Clean up thread
        if hasattr(self, 'process_thread') and self.process_thread:
            self.process_thread.deleteLater()
    
    # Keyboard Navigation Methods
    def keyPressEvent(self, event):
        """Handle keyboard events for window positioning"""
        if event.key() == Qt.Key_Left:
            self.position_window_left()
        elif event.key() == Qt.Key_Right:
            self.position_window_right()
        else:
            super().keyPressEvent(event)
    
    def position_window_left(self):
        """Move window to left side while maintaining current window size"""
        try:
            # Get current window dimensions (preserve user's preferred size)
            current_width = self.width()
            current_height = self.height()
            
            # Get the screen where the window is currently located
            screen = self.screen()
            if not screen:
                # Fallback to primary screen if the window is not on any screen
                screen = QGuiApplication.primaryScreen()
            
            # Get available geometry (excluding taskbars, docks, etc.)
            available = screen.availableGeometry()
            
            # Calculate left position (preserve current window size)
            x_pos = available.x()
            # Ensure y position keeps window fully visible on screen
            y_pos = max(available.y(), 
                          min(self.y(), 
                              available.y() + available.height() - current_height))
            
            # Move window without resizing (preserve user's preferred dimensions)
            self.move(x_pos, y_pos)
            
        except Exception as e:
            print(f"Error moving window to left: {e}")
    
    def position_window_right(self):
        """Move window to right side while maintaining current window size"""
        try:
            # Get current window dimensions (preserve user's preferred size)
            current_width = self.width()
            current_height = self.height()
            
            # Get the screen where the window is currently located
            screen = self.screen()
            if not screen:
                # Fallback to primary screen if the window is not on any screen
                screen = QGuiApplication.primaryScreen()
            
            # Get available geometry (excluding taskbars, docks, etc.)
            available = screen.availableGeometry()
            
            # Calculate right position (preserve current window size)
            x_pos = available.x() + available.width() - current_width
            # Ensure y position keeps window fully visible on screen
            y_pos = max(available.y(), 
                          min(self.y(), 
                              available.y() + available.height() - current_height))
            
            # Move window without resizing (preserve user's preferred dimensions)
            self.move(x_pos, y_pos)
            
        except Exception as e:
            print(f"Error moving window to right: {e}")

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
        """Enhanced graph colors customization with background/grid support"""
        from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
        from PyQt5.QtGui import QColor
        
        # Current default colors (preserve existing professional scheme)
        default_colors = {
            'cpu': '#00ff00',      # Bright green
            'disk_read': '#ff6b6b',  # Red
            'disk_write': '#4ecdc4', # Cyan
            'net_sent': '#ff9ff3',   # Pink
            'net_recv': '#00bcd4',   # Blue
            'background': None,          # Let theme decide
            'grid': None                # Let theme decide
        }
        
        # Get current colors from plots
        current_colors = {
            'cpu': self.cpu_curve.opts['pen'].color().name() if self.cpu_curve else default_colors['cpu'],
            'disk_read': self.disk_read_curve.opts['pen'].color().name() if self.disk_read_curve else default_colors['disk_read'],
            'disk_write': self.disk_write_curve.opts['pen'].color().name() if self.disk_write_curve else default_colors['disk_write'],
            'net_sent': self.net_sent_curve.opts['pen'].color().name() if self.net_sent_curve else default_colors['net_sent'],
            'net_recv': self.net_recv_curve.opts['pen'].color().name() if self.net_recv_curve else default_colors['net_recv'],
        }
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Graph Colors")
        dialog.setModal(True)  # CRITICAL: Ensure dialog appears on top and blocks main window
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Graph selector
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Select Element:")
        self.graph_selector = QComboBox()
        
        graph_elements = [
            "CPU Usage Curve",
            "Disk Read Curve", 
            "Disk Write Curve",
            "Network Send Curve",
            "Network Receive Curve",
            "Background Color",
            "Grid Color"
        ]
        self.graph_selector.addItems(graph_elements)
        
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.graph_selector)
        layout.addLayout(selector_layout)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_label = QLabel("Choose Color:")
        self.color_display = QLabel("Current: None")
        self.color_display.setStyleSheet("border: 1px solid #ccc; padding: 5px; min-width: 100px;")
        
        select_button = QPushButton("Select Color")
        select_button.clicked.connect(self.select_graph_color)
        
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(select_button)
        layout.addLayout(color_layout)
        
        # Preview area
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(preview_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_button = QPushButton("Apply to Selected")
        apply_button.clicked.connect(self.apply_graph_color)
        apply_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; border: none; font-weight: bold;")
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_graph_colors)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(reset_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Update display initially
        self.update_graph_color_display()
        
        # Show dialog
        dialog.exec_()
    
    def select_graph_color(self):
        """Open color picker for selected graph element"""
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        
        # Map display names to internal keys
        element_map = {
            "CPU Usage Curve": "cpu",
            "Disk Read Curve": "disk_read",
            "Disk Write Curve": "disk_write",
            "Network Send Curve": "net_sent",
            "Network Receive Curve": "net_recv",
            "Background Color": "background",
            "Grid Color": "grid"
        }
        
        current_colors = self.get_current_graph_colors()
        selected_element = self.graph_selector.currentText()
        color_key = element_map.get(selected_element)
        current_color = current_colors.get(color_key, '#ffffff') if color_key else '#ffffff'
        
        # Open color dialog with current color
        color = QColorDialog.getColor(QColor(current_color), self, "Select Color")
        if color.isValid():
            # Update display
            self.color_display.setText(f"Current: {color.name()}")
            self.color_display.setStyleSheet(f"background-color: {color.name()}; color: white; padding: 5px; min-width: 100px; font-weight: bold;")
    
    def apply_graph_color(self):
        """Apply selected color to chosen graph element"""
        selected_element = self.graph_selector.currentText()
        color_text = self.color_display.text().replace("Current: ", "")
        
        if color_text and color_text != "None":
            from PyQt5.QtGui import QColor
            color = QColor(color_text)
            if color.isValid():
                self.apply_color_to_element(selected_element, color)
                
                # Save to preferences
                self.save_graph_colors_preference(selected_element, color.name())
    
    def apply_color_to_element(self, element, color):
        """Apply color to specific graph element"""
        color_pen = pg.mkPen(color=color, width=2)
        
        if element == "CPU Usage Curve":
            self.cpu_curve.setPen(color_pen)
        elif element == "Disk Read Curve":
            self.disk_read_curve.setPen(color_pen)
        elif element == "Disk Write Curve":
            self.disk_write_curve.setPen(color_pen)
        elif element == "Network Send Curve":
            self.net_sent_curve.setPen(color_pen)
        elif element == "Network Receive Curve":
            self.net_recv_curve.setPen(color_pen)
        elif element == "Background Color":
            self.cpu_plot.setBackground(color)
            self.disk_plot.setBackground(color)
            self.net_plot.setBackground(color)
        elif element == "Grid Color":
            # Apply to all plots
            for plot in [self.cpu_plot, self.disk_plot, self.net_plot]:
                plot.showGrid(x=True, y=True, alpha=0.3)
    
    def reset_graph_colors(self):
        """Reset all graph colors to defaults"""
        default_colors = {
            'cpu': '#00ff00',      # Bright green
            'disk_read': '#ff6b6b',  # Red
            'disk_write': '#4ecdc4', # Cyan
            'net_sent': '#ff9ff3',   # Pink
            'net_recv': '#00bcd4',   # Blue
        }
        
        # Apply defaults
        self.apply_color_to_element("CPU Usage Curve", QColor(default_colors['cpu']))
        self.apply_color_to_element("Disk Read Curve", QColor(default_colors['disk_read']))
        self.apply_color_to_element("Disk Write Curve", QColor(default_colors['disk_write']))
        self.apply_color_to_element("Network Send Curve", QColor(default_colors['net_sent']))
        self.apply_color_to_element("Network Receive Curve", QColor(default_colors['net_recv']))
        
        # Reset background and grid to theme defaults
        self.apply_system_theme_to_plots()
    
    def get_current_graph_colors(self):
        """Get current colors from all plot elements"""
        try:
            colors = {}
            
            # Get colors from CPU plot
            if hasattr(self, 'cpu_curve') and self.cpu_curve:
                colors['cpu'] = self.cpu_curve.opts['pen'].color().name()
            
            # Get colors from Disk plot
            if hasattr(self, 'disk_read_curve') and self.disk_read_curve:
                colors['disk_read'] = self.disk_read_curve.opts['pen'].color().name()
            if hasattr(self, 'disk_write_curve') and self.disk_write_curve:
                colors['disk_write'] = self.disk_write_curve.opts['pen'].color().name()
            
            # Get colors from Network plot
            if hasattr(self, 'net_sent_curve') and self.net_sent_curve:
                colors['net_sent'] = self.net_sent_curve.opts['pen'].color().name()
            if hasattr(self, 'net_recv_curve') and self.net_recv_curve:
                colors['net_recv'] = self.net_recv_curve.opts['pen'].color().name()
            
            return colors
        except:
            return {}
    
    def save_graph_colors_preference(self, element, color):
        """Save graph color preference to config"""
        try:
            # Load existing preferences
            preferences = {}
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    preferences = json.load(f)
            
            # Ensure graph_colors section exists
            if 'graph_colors' not in preferences:
                preferences['graph_colors'] = {}
            
            # Save the color preference
            if element and color:
                preferences['graph_colors'][element] = color
            
            # Write back to file
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=4)
            
        except Exception as e:
            print(f"Failed to save graph color preference: {e}")
    
    def load_graph_colors_preferences(self):
        """Load saved graph colors and apply them"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    preferences = json.load(f)
                
                # Apply saved graph colors
                if 'graph_colors' in preferences:
                    saved_colors = preferences['graph_colors']
                    
                    # Apply each saved color
                    for element, color_hex in saved_colors.items():
                        if color_hex:  # Skip None values
                            from PyQt5.QtGui import QColor
                            color = QColor(color_hex)
                            if color.isValid():
                                self.apply_color_to_element(element, color)
                    
                    print("✅ Loaded saved graph colors preferences")
                
        except Exception as e:
            print(f"Failed to load graph colors preferences: {e}")
            # Apply default colors on error
            self.reset_graph_colors()
    
    def update_graph_color_display(self):
        """Update the color display when selection changes"""
        selected_element = self.graph_selector.currentText()
        current_colors = self.get_current_graph_colors()
        current_color = current_colors.get(selected_element, 'None')
        
        if current_color == 'None':
            self.color_display.setText("Current: None (Theme Default)")
            self.color_display.setStyleSheet("border: 1px solid #ccc; padding: 5px; min-width: 100px; background: #f5f5f5;")
        else:
            self.color_display.setText(f"Current: {current_color}")
            from PyQt5.QtGui import QColor
            color = QColor(current_color)
            if color.isValid():
                self.color_display.setStyleSheet(f"background-color: {current_color}; color: white; padding: 5px; min-width: 100px; font-weight: bold;")
    
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
        """Show enhanced about dialog with version and timestamp info"""
        # Calculate runtime information
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = datetime.datetime.now() - APPLICATION_START_TIME
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("About SysMon")
        dialog.setModal(True)
        dialog.resize(800, 500)  # Wider, more compact size - better for small screens
        
        layout = QVBoxLayout()
        
        about_text = f"""
        <div style='font-family: Arial, sans-serif; margin: 15px;'>
            <div style='text-align: center; margin-bottom: 20px;'>
                <h2 style='margin: 0; color: #2196F3;'>SysMon - PyQtGraph Edition</h2>
                <p style='margin: 5px 0; color: #666; font-size: 14px;'>Real-time system monitoring with PyQtGraph</p>
            </div>
            
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <b style='color: #333;'>Version & Runtime:</b><br>
                <span style='color: #555;'>
                {FULL_VERSION} • Built: {BUILD_INFO} • Released: {RELEASE_DATE}<br>
                Runtime: {uptime_str} • Python {PYTHON_VERSION}
                </span>
            </div>
            
            <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <b style='color: #333;'>System:</b><br>
                <span style='color: #555;'>{PLATFORM_INFO}</span>
            </div>
            
            <div style='background-color: #fff3e0; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <b style='color: #333;'>Core Features:</b><br>
                <span style='color: #555; font-size: 0.9em;'>
                • Real-time CPU, Disk I/O, Network monitoring with smooth graphs<br>
                • Live RAM & Swap memory display with GB formatting<br>
                • Process drill-down analysis and resource tracking<br>
                • Window transparency, always-on-top, XDG compliance
                </span>
            </div>
            
            <div style='background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <b style='color: #333;'>Libraries:</b><br>
                <span style='color: #555; font-size: 0.9em;'>
                PyQt5 GUI Framework • PyQtGraph Plotting • psutil System Info
                </span>
            </div>
            
            <div style='text-align: center; margin-top: 10px; color: #666; font-size: 0.9em;'>
                <b>Author:</b> System Monitor Project
            </div>
        </div>
        """
        
        # Create text area with HTML content
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setHtml(about_text)
        text_area.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        layout.addWidget(text_area)
        
        # Add close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Center dialog on screen
        dialog.setGeometry(
            dialog.x() + (dialog.width() // 2),
            dialog.y() + (dialog.height() // 2),
            dialog.width(),
            dialog.height()
        )
        
        # Show dialog
        dialog.exec_()
    
    def show_users_guide(self):
        """Show comprehensive users guide dialog with theme-aware styling"""
        # Try to read the users guide file
        users_guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'users-guide.md')
        
        try:
            with open(users_guide_path, 'r', encoding='utf-8', errors='replace') as f:
                users_guide_content = f.read()
        except Exception as e:
            users_guide_content = f"""# SysMon Users Guide

Unable to load users guide file.

Error: {str(e)}

Please check the docs/users-guide.md file in the SysMon repository."""
        
        # Get theme-appropriate colors
        theme_colors = self.get_dialog_theme_colors()
        
        # Create dialog similar to changelog but wider for better readability
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon Users Guide")
        dialog.setModal(True)
        dialog.resize(1000, 750)  # Larger size for comprehensive guide
        
        layout = QVBoxLayout()
        
        # Create text area with users guide content using theme-aware styling
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
                background-color: {theme_colors['background']};
                color: {theme_colors['text']};
                border: 1px solid #dee2e6;
                padding: 12px;
                selection-background-color: {theme_colors['selection_bg']};
                selection-color: {theme_colors['selection_text']};
            }}
        """)
        text_area.setPlainText(users_guide_content)
        layout.addWidget(text_area)
        
        # Add close button with theme-aware styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Center dialog on screen
        dialog.setGeometry(
            dialog.x() + (dialog.width() // 2),
            dialog.y() + (dialog.height() // 2),
            dialog.width(),
            dialog.height()
        )
        
        # Show dialog
        dialog.exec_()
    
    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts and navigation help dialog"""
        # Get theme-appropriate colors
        theme_colors = self.get_dialog_theme_colors()
        
        shortcuts_content = """
# SysMon Keyboard Shortcuts & Navigation

## Window Positioning Navigation
**← Left Arrow**  : Move window to left side of current screen (preserves window size)
**→ Right Arrow** : Move window to right side of current screen (preserves window size)

## Existing Keyboard Shortcuts

### File Menu
**Ctrl+S**        : Save current graph data
**Ctrl+E**        : Export graph as image
**Ctrl+Q**        : Exit application

### Edit Menu  
**Ctrl+C**        : Copy graph data to clipboard
**Ctrl+Del**      : Clear all data and reset graphs

### View Menu
**F11**           : Toggle fullscreen mode
**Esc**           : Close active dialog

### Navigation Tips
- **Arrow Keys** work instantly - no need to drag window manually
- **Multi-Monitor** support: Arrow keys work on the screen where window is located
- **Size Preserving**: Window maintains current width and height during movement
- **Smart Positioning**: Window keeps your preferred dimensions while snapping to edges
- **Taskbar Aware**: Automatic detection avoids system UI elements

### Advanced Usage
- **Press Arrow Again**: Move between positions (left ↔ right) while maintaining size
- **Size Memory**: Window remembers your preferred dimensions for quick positioning
- **Combine with Features**: Use with "Always On Top" for persistent monitoring
- **Multi-Screen**: Move window between monitors using standard window dragging
- **Custom Sizing**: Resize window once, then use arrows to position quickly

### Theme Support
- **Automatic**: Keyboard shortcuts work in both light and dark themes
- **Consistent**: Same shortcuts across all operating systems
- **Responsive**: No delay in window positioning

---

For detailed feature documentation, see Help → Users Guide
        """
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon Keyboard Shortcuts")
        dialog.setModal(True)
        dialog.resize(700, 600)
        
        layout = QVBoxLayout()
        
        # Create text area with shortcuts content using theme-aware styling
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                background-color: {theme_colors['background']};
                color: {theme_colors['text']};
                border: 1px solid #dee2e6;
                padding: 12px;
                selection-background-color: {theme_colors['selection_bg']};
                selection-color: {theme_colors['selection_text']};
            }}
        """)
        text_area.setPlainText(shortcuts_content)
        layout.addWidget(text_area)
        
        # Add close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Center dialog on screen
        dialog.setGeometry(
            dialog.x() + (dialog.width() // 2),
            dialog.y() + (dialog.height() // 2),
            dialog.width(),
            dialog.height()
        )
        
        # Show dialog
        dialog.exec_()
    
def set_application_icon(app):
    """Set application icon with proper error handling"""
    import os
    
    # Possible icon paths to search (in order of preference)
    icon_paths = [
        # Relative to source file
        os.path.join(os.path.dirname(__file__), '..', 'icons', 'ICON_SysMon.png'),
        os.path.join(os.path.dirname(__file__), '..', 'icons', 'ICON_SysMon.ico'),
        # Current working directory paths
        os.path.join(os.getcwd(), 'icons', 'ICON_SysMon.png'),
        os.path.join(os.getcwd(), 'icons', 'ICON_SysMon.ico'),
        os.path.join(os.getcwd(), 'assets', 'icons', 'ICON_sysmon.png'),
        os.path.join(os.getcwd(), 'assets', 'icons', 'ICON_sysmon.ico'),
        # Fallback paths
        'icons/ICON_SysMon.png',
        'icons/ICON_SysMon.ico',
        'assets/icons/ICON_sysmon.png',
        'assets/icons/ICON_sysmon.ico'
    ]
    
    for icon_path in icon_paths:
        try:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    app.setWindowIcon(icon)
                    print(f"✓ Application icon set: {icon_path}")
                    return True
                else:
                    print(f"⚠ Icon file exists but failed to load: {icon_path}")
            else:
                continue
        except Exception as e:
            print(f"⚠ Icon loading failed for {icon_path}: {e}")
            continue
    
    print("⚠ No valid application icon found, using system default")
    return False

def main():
    app = QApplication(sys.argv)
    
    # Check for existing instance before creating any windows
    if not check_single_instance():
        show_instance_already_running(app)
        return 1  # Exit with error code
    
    # Set application icon
    set_application_icon(app)
    
    # Create and show main window
    monitor = SystemMonitor()
    monitor.show()
    
    # Register cleanup for single instance resources
    atexit.register(cleanup_single_instance)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
