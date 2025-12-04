#!/usr/bin/env python3
# sysmon-07.py  2025-11-22 
# CPU, Disk IO and Net IO scrolling graph
# w drill down popups and Visual Scale Change Indicators

'''
Tue 03 Dec 2025 09:20:00 PM CST Fixed X-axis behavior - X-axis now remains fixed at 0 to time window parameter instead of scrolling, data scrolls left smoothly with full window coverage

Wed 26 Nov 2025 01:01:08 AM CST Suppressed GdkPixbuf warnings - Filters out harmless GTK/Qt interaction warnings at OS level

Tue 26 Nov 2025 10:02:04 AM CST Fixed window geometry persistence - Now properly remembers window position and size on Linux

Tue 26 Nov 2025 08:02:16 AM CST Added desktop theme inheritance - Automatically matches your system's light/dark theme

Mon 24 Nov 2025 06:02:26 AM CST Fixed window geometry persistence - Now properly remembers window position and size on Linux

'''

import os
import sys
import subprocess
import threading

# Suppress GdkPixbuf warnings by filtering stderr at OS level
def _filter_stderr():
    """Filter stderr to suppress ONLY GdkPixbuf-CRITICAL warnings.
    
    All other stderr messages (Python exceptions, tracebacks, warnings, etc.)
    are passed through unchanged to the console.
    """
    if sys.stderr.isatty():
        # Create a pipe
        read_fd, write_fd = os.pipe()
        
        # Save original stderr
        stderr_fd = sys.stderr.fileno()
        stderr_copy = os.dup(stderr_fd)
        
        # Redirect stderr to pipe
        os.dup2(write_fd, stderr_fd)
        os.close(write_fd)
        
        # Thread to read from pipe and filter output
        def filter_thread():
            with os.fdopen(read_fd, 'rb') as pipe:
                with os.fdopen(stderr_copy, 'wb') as original_stderr:
                    for line in pipe:
                        # Only filter GdkPixbuf-CRITICAL - allow ALL other errors/warnings
                        if b'GdkPixbuf-CRITICAL' not in line:
                            original_stderr.write(line)
                            original_stderr.flush()
        
        thread = threading.Thread(target=filter_thread, daemon=True)
        thread.start()

_filter_stderr()

import matplotlib
matplotlib.use('Qt5Agg')  # Force Qt5 backend
from matplotlib.backends import qt_compat as _qt_compat
from matplotlib.backends.qt_compat import QtWidgets, QtGui
import psutil
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from datetime import datetime
import json
import os
import numpy as np
import argparse
from matplotlib.ticker import FuncFormatter
import time
import atexit

# ============================================================================
# SYSTEM MONITOR CONSTANTS
# ============================================================================

# Data Storage Constants
DATA_BUFFER_SIZE = 200          # Maximum seconds of data to store in deques
DEFAULT_TIME_WINDOW = 20        # Default time window in seconds for X-axis
DEFAULT_SMOOTH_WINDOW = 5       # Default smoothing window size for moving average

# Timing Constants
ANIMATION_INTERVAL = 50         # Animation update interval in milliseconds
PROCESS_SAMPLE_DELAY = 0.2      # Delay for process sampling in seconds
TIME_WINDOW_STEP = 5            # Time window adjustment step in seconds
MIN_TIME_WINDOW = 5             # Minimum allowed time window in seconds
MAX_TIME_WINDOW = 120           # Maximum allowed time window in seconds

# Display & UI Constants
CPU_MAX_PERCENT = 100           # Maximum CPU percentage for Y-axis scaling
DEFAULT_WINDOW_X = 100          # Default window X position
DEFAULT_WINDOW_Y = 100          # Default window Y position
FLASH_DURATION = 10             # Flash effect duration in frames (~500ms)

# Unit Conversion Constants
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024
BITS_PER_KB = 1000
BITS_PER_MB = 1000 * 1000
BITS_PER_GB = 1000 * 1000 * 1000

# Process & Popup Constants
TOP_PROCESSES_COUNT = 10        # Number of top processes to display
MAX_SMOOTH_WINDOW = 20         # Maximum allowed smoothing window size
POPUP_FIG_WIDTH_CPU = 5.5       # Popup figure width for CPU processes
POPUP_FIG_WIDTH_DISK = 6.0      # Popup figure width for Disk processes
POPUP_FIG_WIDTH_NET = 5.0       # Popup figure width for Network processes
POPUP_FIG_HEIGHT = 3.5          # Popup figure height for all process types
POPUP_WINDOW_X = 50             # Popup window X position
POPUP_WINDOW_Y = 50             # Popup window Y position

def get_system_metrics():
    # Get current metrics
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    disk_io = psutil.disk_io_counters()
    net_io = psutil.net_io_counters()
    
    return {
        'CPU_Usage': cpu_percent,
        'Memory_Usage': memory_percent,
        'Disk_Read': disk_io.read_bytes,
        'Disk_Write': disk_io.write_bytes,
        'Network_Upload': net_io.bytes_sent,
        'Network_Download': net_io.bytes_recv
    }

def _apply_qt_desktop_theme():
    """Apply Qt desktop palette to Matplotlib rcParams (dark/light aware), and set app icon early."""
    # Ensure there is a QApplication (use empty argv so Qt doesn't eat CLI args)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    # Set application icon BEFORE any windows/figures are created
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for candidate in ('ICON_sysmon.png', 'ICON_sysmon.ico'):
            icon_path = os.path.join(script_dir, candidate)
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                if not icon.isNull():
                    app.setWindowIcon(icon)
                    break
    except Exception:
        pass

    pal = app.palette()

    def qhex(role):
        c = pal.color(role)
        return f"#{c.red():02x}{c.green():02x}{c.blue():02x}"

    # Basic palette-derived colors
    fig_bg = qhex(QtGui.QPalette.Window)
    axes_bg = qhex(QtGui.QPalette.Base)
    text_fg = qhex(QtGui.QPalette.WindowText)
    axes_edge = qhex(QtGui.QPalette.Mid)
    grid_col = qhex(QtGui.QPalette.Mid)
    tick_col = text_fg

    # Apply to Matplotlib
    plt.rcParams.update({
        'figure.facecolor': fig_bg,
        'axes.facecolor': axes_bg,
        'axes.edgecolor': axes_edge,
        'axes.labelcolor': text_fg,
        'xtick.color': tick_col,
        'ytick.color': tick_col,
        'grid.color': grid_col,
        'grid.alpha': 0.3,
        'text.color': text_fg,
        'figure.edgecolor': fig_bg,
        'savefig.facecolor': fig_bg,
        'savefig.edgecolor': fig_bg,
        'legend.edgecolor': axes_edge,
        'legend.facecolor': axes_bg,
    })

class RealtimeMonitor:
    def __init__(self, max_points=DEFAULT_TIME_WINDOW, smooth_window=DEFAULT_SMOOTH_WINDOW):
        self.max_points = max_points  # Time window in seconds for X-axis
        self.smooth_window = smooth_window  # Window size for moving average
        self.time_window_step = TIME_WINDOW_STEP  # Seconds to adjust when using +/- keys
        self.min_time_window = MIN_TIME_WINDOW  # Minimum time window
        self.max_time_window = MAX_TIME_WINDOW  # Maximum time window
        # Store unlimited data points - max_points now controls display window
        self.metrics_data = {
            'CPU_Usage': deque(maxlen=DATA_BUFFER_SIZE),  # Store up to DATA_BUFFER_SIZE seconds of data
            'Disk_Read': deque(maxlen=DATA_BUFFER_SIZE),
            'Disk_Write': deque(maxlen=DATA_BUFFER_SIZE),
            'Network_Upload': deque(maxlen=DATA_BUFFER_SIZE),
            'Network_Download': deque(maxlen=DATA_BUFFER_SIZE)
        }
        self.times = deque(maxlen=DATA_BUFFER_SIZE)
        self.start_time = datetime.now()
        self.last_disk_read = None
        self.last_disk_write = None
        self.last_net_upload = None
        self.last_net_download = None
        self.last_timestamp = None
        self.last_sample_time = None
        self.config_file = os.path.join(os.path.expanduser('~'), '.sysmon_config.json')
        
        # Track scale changes for visual indicators
        self.last_disk_scale_magnitude = 0  # Track order of magnitude (KB, MB, GB)
        self.last_net_scale_magnitude = 0   # Track order of magnitude (Kbps, Mbps, Gbps)
        self.disk_flash_counter = 0
        self.net_flash_counter = 0
        # Apply desktop theme before creating any figures
        _apply_qt_desktop_theme()

        # Create figure and subplots - 3 subplots total
        self.fig, self.axes = plt.subplots(3, 1, figsize=(12, 8))
        self.fig.canvas.manager.set_window_title('SysMon')
        
        # Set custom window icon using QPixmap for proper loading
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'ICON_sysmon.png')
            if not os.path.exists(icon_path):
                icon_path = os.path.join(script_dir, 'ICON_sysmon.ico')
            if os.path.exists(icon_path):
                pixmap = QtGui.QPixmap(icon_path)
                if not pixmap.isNull():
                    icon = QtGui.QIcon(pixmap)
                    self.fig.canvas.manager.window.setWindowIcon(icon)
        except Exception:
            pass
        
        self.fig.suptitle('SysMon', fontsize=16, fontweight='bold')
        
        # Record the default axes facecolor to restore after flashes
        self.default_axes_facecolor = self.axes[0].get_facecolor()
        
        # Setup each subplot
        self.lines = []
        
        # Setup CPU subplot
        cpu_line, = self.axes[0].plot([], [], color='#FF6B6B', linewidth=2, label='CPU')
        self.lines.append(cpu_line)
        self.axes[0].set_ylabel('CPU Usage (%)', fontsize=9, fontweight='bold')
        self.axes[0].grid(True, alpha=0.3, linestyle='--')
        self.axes[0].set_xlim(0, self.max_points)
        self.axes[0].set_ylim(0, CPU_MAX_PERCENT)
        self.axes[0].tick_params(axis='y', labelsize=8)
        self.axes[0].tick_params(axis='x', labelsize=8)
        
        # Setup disk I/O subplot with two lines (read and write)
        disk_read_line, = self.axes[1].plot([], [], color='#45B7D1', linewidth=2, label='Read')
        disk_write_line, = self.axes[1].plot([], [], color='#9B59B6', linewidth=2, label='Write')
        self.lines.append(disk_read_line)
        self.lines.append(disk_write_line)
        self.axes[1].set_ylabel('Disk I/O', fontsize=9, fontweight='bold')
        self.axes[1].grid(True, alpha=0.3, linestyle='--')
        self.axes[1].set_xlim(0, self.max_points)
        self.axes[1].set_ylim(0, CPU_MAX_PERCENT)
        self.axes[1].autoscale(axis='y')
        self.axes[1].yaxis.set_major_formatter(FuncFormatter(self.format_bytes))
        self.axes[1].tick_params(axis='y', labelsize=8)
        self.axes[1].tick_params(axis='x', labelsize=8)
        self.axes[1].legend(loc='upper left', fontsize=8)
        
        # Setup network subplot with two lines (upload and download)
        upload_line, = self.axes[2].plot([], [], color='#96CEB4', linewidth=2, label='Upload')
        download_line, = self.axes[2].plot([], [], color='#FFA07A', linewidth=2, label='Download')
        self.lines.append(upload_line)
        self.lines.append(download_line)
        self.axes[2].set_ylabel('Network', fontsize=9, fontweight='bold')
        self.axes[2].grid(True, alpha=0.3, linestyle='--')
        self.axes[2].set_xlim(0, self.max_points)
        self.axes[2].set_ylim(0, CPU_MAX_PERCENT)
        self.axes[2].autoscale(axis='y')
        self.axes[2].yaxis.set_major_formatter(FuncFormatter(self.format_bits))
        self.axes[2].tick_params(axis='y', labelsize=8)
        self.axes[2].tick_params(axis='x', labelsize=8)
        self.axes[2].legend(loc='upper left', fontsize=8)
        
        self.axes[-1].set_xlabel('Time (seconds)', fontsize=9, fontweight='bold')
        self.fig.tight_layout(pad=2.0)
        
        # Add version text in lower left corner
        self.fig.text(0.01, 0.01, 'v0.0.9c 2025-12-04 10:45', fontsize=8, 
                     ha='left', va='bottom', transform=self.fig.transFigure)
        
        # Enable auto-adjust on resize
        self.fig.set_tight_layout(True)
        
        # Load and apply saved window geometry
        self.load_window_geometry()
        
        # Register atexit handler to save geometry on exit
        atexit.register(self.save_window_geometry)
        
        # Connect click events (double-click) for drill-down popups
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Connect keyboard events for time window adjustment
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
    
    def load_window_geometry(self):
        """Load window size and position from config file (Qt5 backend)"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                if 'window_size' in config:
                    manager = self.fig.canvas.manager
                    window = manager.window
                    width, height = config['window_size']
                    x = config.get('x', DEFAULT_WINDOW_X)
                    y = config.get('y', DEFAULT_WINDOW_Y)
                    window.setGeometry(x, y, width, height)
        except Exception as e:
            # Silently ignore errors and use default geometry
            pass
    
    def save_window_geometry(self):
        """Save window size and position to config file (Qt5 backend)"""
        try:
            manager = self.fig.canvas.manager
            window = manager.window
            geometry = window.geometry()
            
            config = {
                'x': geometry.x(),
                'y': geometry.y(),
                'window_size': [geometry.width(), geometry.height()]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            # Silently ignore errors
            pass
    
    def format_bytes(self, value, pos):
        """Format bytes per second in human-readable format"""
        if value == 0:
            return '0'
        elif value < BYTES_PER_KB:
            return f'{int(value)}B/s'
        elif value < BYTES_PER_MB:
            return f'{int(value/BYTES_PER_KB)}KB/s'
        elif value < BYTES_PER_GB:
            return f'{int(value/BYTES_PER_MB)}MB/s'
        else:
            return f'{int(value/BYTES_PER_GB)}GB/s'
    
    def format_bits(self, value, pos):
        """Format bits per second in human-readable format"""
        if value == 0:
            return '0'
        elif value < BITS_PER_KB:
            return f'{int(value)}bps'
        elif value < BITS_PER_MB:
            return f'{int(value/BITS_PER_KB)}Kbps'
        elif value < BITS_PER_GB:
            return f'{int(value/BITS_PER_MB)}Mbps'
        else:
            return f'{int(value/BITS_PER_GB)}Gbps'
    
    def get_top_cpu_processes(self):
        """Get top 10 processes by CPU usage (samples over ~200 ms)"""
        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    p.cpu_percent(None)  # prime
                    procs.append(p)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(PROCESS_SAMPLE_DELAY)
            rows = []
            for p in procs:
                try:
                    rows.append({'pid': p.pid, 'name': p.name(), 'cpu_percent': p.cpu_percent(None)})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(rows, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:TOP_PROCESSES_COUNT]
        except Exception:
            return []
    
    def get_top_disk_processes(self):
        """Get top 10 processes by Disk I/O rate (bytes/s over ~200 ms)"""
        try:
            first = {}
            procs = []
            t0 = time.time()
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    io1 = p.io_counters()
                    first[p.pid] = (io1.read_bytes, io1.write_bytes, p.name())
                    procs.append(p)
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass
            time.sleep(PROCESS_SAMPLE_DELAY)
            dt = max(time.time() - t0, 0.001)
            rows = []
            for p in procs:
                try:
                    io2 = p.io_counters()
                    r1, w1, name = first.get(p.pid, (0, 0, p.name()))
                    r_rate = max(io2.read_bytes - r1, 0) / dt
                    w_rate = max(io2.write_bytes - w1, 0) / dt
                    rows.append({'pid': p.pid, 'name': name, 'read_bps': r_rate, 'write_bps': w_rate, 'total': r_rate + w_rate})
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass
            return sorted(rows, key=lambda x: x['total'], reverse=True)[:TOP_PROCESSES_COUNT]
        except Exception:
            return []
    
    def get_top_network_processes(self):
        """Get top 10 processes by Network activity (connection count proxy)"""
        try:
            rows = []
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    conns = p.net_connections()
                    rows.append({'pid': p.pid, 'name': p.name(), 'connections': len(conns)})
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass
            return sorted(rows, key=lambda x: x['connections'], reverse=True)[:TOP_PROCESSES_COUNT]
        except Exception:
            return []
    
    def show_process_details(self, metric_type):
        """Show a popup window with top 10 processes for the given metric (Matplotlib table)"""
        # Collect rows per metric type
        if metric_type == 'CPU Usage':
            rows = self.get_top_cpu_processes()
            col_labels = ['PID', 'Process', 'CPU %']
            cell_data = [[r['pid'], r['name'][:30], f"{r['cpu_percent']:.1f}"] for r in rows]
            fig_width = POPUP_FIG_WIDTH_CPU
        elif metric_type == 'Disk I/O':
            rows = self.get_top_disk_processes()
            col_labels = ['PID', 'Process', 'Read', 'Write']
            cell_data = [[r['pid'], r['name'][:25], f"{int(r['read_bps']/BYTES_PER_KB)}K", f"{int(r['write_bps']/BYTES_PER_KB)}K"] for r in rows]
            fig_width = POPUP_FIG_WIDTH_DISK
        else:  # Network
            rows = self.get_top_network_processes()
            col_labels = ['PID', 'Process', 'Conns']
            cell_data = [[r['pid'], r['name'][:30], r['connections']] for r in rows]
            fig_width = POPUP_FIG_WIDTH_NET
        
        fig, ax = plt.subplots(figsize=(fig_width, POPUP_FIG_HEIGHT))
        fig.canvas.manager.set_window_title(f'Top 10 - {metric_type}')
        ax.axis('tight')
        ax.axis('off')
        ax.set_title(f'Top 10 - {metric_type}', fontsize=10, fontweight='bold', pad=5)
        
        table = ax.table(cellText=cell_data, colLabels=col_labels, loc='center', cellLoc='left')
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1, 1.1)
        
        # Style header row
        for i, key in enumerate(col_labels):
            table[(0, i)].set_facecolor('#E0E0E0')
            table[(0, i)].set_text_props(weight='bold')
        
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        # Position window in upper left corner
        try:
            mngr = fig.canvas.manager
            mngr.window.setGeometry(POPUP_WINDOW_X, POPUP_WINDOW_Y, int(fig_width*100), 350)
        except Exception:
            pass  # Backend might not support positioning
        
        plt.show(block=False)
    
    def on_click(self, event):
        """Handle click events on the plot"""
        # Double-click anywhere on a graph to show process details (non-blocking Matplotlib popup)
        if event.dblclick and event.inaxes is not None:
            if event.inaxes == self.axes[0]:
                self.show_process_details('CPU Usage')
            elif event.inaxes == self.axes[1]:
                self.show_process_details('Disk I/O')
            elif event.inaxes == self.axes[2]:
                self.show_process_details('Network')
    
    def on_key_press(self, event):
        """Handle keyboard events for X-axis zoom control"""
        if event.key in ['+', '=']:  # Zoom out (show more time)
            new_window = self.max_points + self.time_window_step
            if new_window <= self.max_time_window:
                self.max_points = new_window
                print(f"Time window: {self.max_points} seconds")
        elif event.key == '-':  # Zoom in (show less time)
            new_window = self.max_points - self.time_window_step
            if new_window >= self.min_time_window:
                self.max_points = new_window
                print(f"Time window: {self.max_points} seconds")
    
    def get_magnitude_level(self, value, divisor):
        """Get the order of magnitude level (0=base, 1=K, 2=M, 3=G)"""
        if value < divisor:
            return 0
        elif value < divisor * divisor:
            return 1
        elif value < divisor * divisor * divisor:
            return 2
        else:
            return 3
    
    def moving_average(self, data, window_size):
        """Calculate moving average for smoothing using same-length output"""
        if len(data) < window_size:
            return np.array(data)  # Not enough data to smooth
        # Use mode='same' to keep same length, then trim edges to avoid edge effects
        # This prevents data from disappearing during startup
        smoothed = np.convolve(data, np.ones(window_size) / window_size, mode='same')
        return smoothed
    
    def filter_data_by_time_window(self, time_data, value_data, current_time):
        """Filter data to only include points within the current time window."""
        if len(time_data) == 0 or len(value_data) == 0:
            return []
        
        # Calculate the time threshold
        time_threshold = current_time - self.max_points
        
        # Find indices within the time window
        filtered_values = []
        for i, t in enumerate(time_data):
            if i < len(value_data) and t >= time_threshold:
                filtered_values.append(value_data[i])
        
        return filtered_values
    
    def animate(self, frame):
        current_time = datetime.now()
        elapsed_time = (current_time - self.start_time).total_seconds()
        
        # Sample new data only once per second
        should_sample = (self.last_sample_time is None or 
                        (current_time - self.last_sample_time).total_seconds() >= 1.0)
        
        if should_sample:
            # Get current metrics
            metrics = get_system_metrics()
            
            # Calculate disk I/O rates in bytes per second
            if self.last_disk_read is not None and self.last_timestamp is not None:
                time_delta = (current_time - self.last_timestamp).total_seconds()
                if time_delta > 0:
                    disk_read_rate = (metrics['Disk_Read'] - self.last_disk_read) / time_delta
                    disk_write_rate = (metrics['Disk_Write'] - self.last_disk_write) / time_delta
                    upload_rate = ((metrics['Network_Upload'] - self.last_net_upload) * 8) / time_delta  # Convert bytes to bits
                    download_rate = ((metrics['Network_Download'] - self.last_net_download) * 8) / time_delta
                else:
                    disk_read_rate = 0
                    disk_write_rate = 0
                    upload_rate = 0
                    download_rate = 0
            else:
                disk_read_rate = 0
                disk_write_rate = 0
                upload_rate = 0
                download_rate = 0
            
            # Update last values for next calculation
            self.last_disk_read = metrics['Disk_Read']
            self.last_disk_write = metrics['Disk_Write']
            self.last_net_upload = metrics['Network_Upload']
            self.last_net_download = metrics['Network_Download']
            self.last_timestamp = current_time
            self.last_sample_time = current_time
            
            # Update data
            self.times.append(elapsed_time)
            self.metrics_data['CPU_Usage'].append(metrics['CPU_Usage'])
            self.metrics_data['Disk_Read'].append(disk_read_rate)
            self.metrics_data['Disk_Write'].append(disk_write_rate)
            self.metrics_data['Network_Upload'].append(upload_rate)
            self.metrics_data['Network_Download'].append(download_rate)
        
        # Update plots - convert absolute time to relative time within window
        time_array = list(self.times)
        
        if len(time_array) == 0:
            return self.lines
        
        # Update CPU plot with smoothing
        cpu_data = list(self.metrics_data['CPU_Usage'])
        if len(cpu_data) > 0:
            # Apply smoothing first
            cpu_smooth = self.moving_average(cpu_data, self.smooth_window)
            # Get corresponding time values - align to rightmost data points
            # When data < smooth_window, no smoothing occurs and lengths match
            # When data >= smooth_window, smoothing reduces length by (window_size - 1)
            num_points = len(cpu_smooth)
            time_for_smooth = time_array[-num_points:] if num_points <= len(time_array) else time_array
            
            # Calculate relative time positions
            current_time_val = elapsed_time
            
            # When elapsed time < time window, show all data from 0
            # When elapsed time >= time window, scroll to show only most recent max_points seconds
            if current_time_val <= self.max_points:
                # Early phase: show all data starting from 0
                relative_times = time_for_smooth
                visible_cpu = cpu_smooth
            else:
                # Scrolling phase: filter to visible window
                time_offset = current_time_val - self.max_points
                visible_data = [(t - time_offset, v) for t, v in zip(time_for_smooth, cpu_smooth) if t >= time_offset]
                if visible_data:
                    relative_times, visible_cpu = zip(*visible_data)
                else:
                    relative_times, visible_cpu = [], []
            
            if len(relative_times) > 0:
                self.lines[0].set_data(relative_times, visible_cpu)
        
        # Fixed X-axis: always 0 to max_points
        self.axes[0].set_xlim(0, self.max_points)
        
        # Update disk I/O plot (both read and write) with smoothing
        disk_read_data = list(self.metrics_data['Disk_Read'])
        disk_write_data = list(self.metrics_data['Disk_Write'])
        if len(disk_read_data) > 0:
            # Apply smoothing first
            disk_read_smooth = self.moving_average(disk_read_data, self.smooth_window)
            disk_write_smooth = self.moving_average(disk_write_data, self.smooth_window)
            # Get corresponding time values - align to rightmost data points
            num_points = len(disk_read_smooth)
            time_for_smooth = time_array[-num_points:] if num_points <= len(time_array) else time_array
            
            # Calculate relative time positions
            current_time_val = elapsed_time
            
            # When elapsed time < time window, show all data from 0
            # When elapsed time >= time window, scroll to show only most recent max_points seconds
            if current_time_val <= self.max_points:
                # Early phase: show all data starting from 0
                relative_times_disk = time_for_smooth
                visible_read = disk_read_smooth
                visible_write = disk_write_smooth
            else:
                # Scrolling phase: filter to visible window
                time_offset = current_time_val - self.max_points
                visible_data_read = [(t - time_offset, v) for t, v in zip(time_for_smooth, disk_read_smooth) if t >= time_offset]
                visible_data_write = [(t - time_offset, v) for t, v in zip(time_for_smooth, disk_write_smooth) if t >= time_offset]
                if visible_data_read:
                    relative_times_disk, visible_read = zip(*visible_data_read)
                    _, visible_write = zip(*visible_data_write)
                else:
                    relative_times_disk, visible_read, visible_write = [], [], []
            
            if len(relative_times_disk) > 0:
                self.lines[1].set_data(relative_times_disk, visible_read)
                self.lines[2].set_data(relative_times_disk, visible_write)
                
                # Fixed X-axis: always 0 to max_points
                self.axes[1].set_xlim(0, self.max_points)
                
                # Auto-scale y-axis based on visible data
                all_disk_visible = list(visible_read) + list(visible_write)
                if len(all_disk_visible) > 0:
                    max_val = max(all_disk_visible) if max(all_disk_visible) > 0 else 10
                    self.axes[1].set_ylim(0, max_val * 1.1)
                    
                    # Detect scale magnitude change for Disk I/O
                    current_magnitude = self.get_magnitude_level(max_val, BYTES_PER_KB)  # Bytes: KB=1, MB=2, GB=3
                    if current_magnitude != self.last_disk_scale_magnitude and self.last_disk_scale_magnitude > 0:
                        self.disk_flash_counter = FLASH_DURATION  # Flash for FLASH_DURATION frames (~500ms)
                    self.last_disk_scale_magnitude = current_magnitude
                    
                    # Apply flash effect
                    if self.disk_flash_counter > 0:
                        self.axes[1].set_facecolor('#FFEBEE' if self.disk_flash_counter % 4 < 2 else 'white')
                        self.disk_flash_counter -= 1
                    else:
                        self.axes[1].set_facecolor(self.default_axes_facecolor)
        
        # Update network plot (both upload and download) with smoothing
        upload_data = list(self.metrics_data['Network_Upload'])
        download_data = list(self.metrics_data['Network_Download'])
        if len(upload_data) > 0:
            # Apply smoothing first
            upload_smooth = self.moving_average(upload_data, self.smooth_window)
            download_smooth = self.moving_average(download_data, self.smooth_window)
            # Get corresponding time values - align to rightmost data points
            num_points = len(upload_smooth)
            time_for_smooth = time_array[-num_points:] if num_points <= len(time_array) else time_array
            
            # Calculate relative time positions
            current_time_val = elapsed_time
            
            # When elapsed time < time window, show all data from 0
            # When elapsed time >= time window, scroll to show only most recent max_points seconds
            if current_time_val <= self.max_points:
                # Early phase: show all data starting from 0
                relative_times_net = time_for_smooth
                visible_upload = upload_smooth
                visible_download = download_smooth
            else:
                # Scrolling phase: filter to visible window
                time_offset = current_time_val - self.max_points
                visible_data_upload = [(t - time_offset, v) for t, v in zip(time_for_smooth, upload_smooth) if t >= time_offset]
                visible_data_download = [(t - time_offset, v) for t, v in zip(time_for_smooth, download_smooth) if t >= time_offset]
                if visible_data_upload:
                    relative_times_net, visible_upload = zip(*visible_data_upload)
                    _, visible_download = zip(*visible_data_download)
                else:
                    relative_times_net, visible_upload, visible_download = [], [], []
            
            if len(relative_times_net) > 0:
                self.lines[3].set_data(relative_times_net, visible_upload)
                self.lines[4].set_data(relative_times_net, visible_download)
                
                # Fixed X-axis: always 0 to max_points
                self.axes[2].set_xlim(0, self.max_points)
                
                # Auto-scale y-axis based on visible data
                all_network_visible = list(visible_upload) + list(visible_download)
                if len(all_network_visible) > 0:
                    max_val = max(all_network_visible) if max(all_network_visible) > 0 else 10
                    self.axes[2].set_ylim(0, max_val * 1.1)
                    
                    # Detect scale magnitude change for Network
                    current_magnitude = self.get_magnitude_level(max_val, BITS_PER_KB)  # Bits: Kbps=1, Mbps=2, Gbps=3
                    if current_magnitude != self.last_net_scale_magnitude and self.last_net_scale_magnitude > 0:
                        self.net_flash_counter = FLASH_DURATION  # Flash for FLASH_DURATION frames (~500ms)
                    self.last_net_scale_magnitude = current_magnitude
                    
                    # Apply flash effect
                    if self.net_flash_counter > 0:
                        self.axes[2].set_facecolor('#E3F2FD' if self.net_flash_counter % 4 < 2 else 'white')
                        self.net_flash_counter -= 1
                    else:
                        self.axes[2].set_facecolor(self.default_axes_facecolor)
        
        # Refresh layout to handle any window resizing
        self.fig.canvas.draw_idle()
        
        return self.lines
    
    def start(self):
        # Animation updates every ANIMATION_INTERVAL ms for smooth scrolling, but data samples every 1 second
        anim = animation.FuncAnimation(
            self.fig, self.animate, interval=ANIMATION_INTERVAL, blit=False, cache_frame_data=False
        )
        
        # Save window geometry when closing
        self.fig.canvas.mpl_connect('close_event', lambda event: self.save_window_geometry())
        
        plt.show()
        return anim

def main():
    parser = argparse.ArgumentParser(
        prog='SysMon',
        description='Real-time system monitoring with live graphs for CPU, Disk I/O, and Network activity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python sysmon.py                    # Run with default settings (20s window)
  python sysmon.py -t 30              # Start with 30 second time window
  python sysmon.py -s 10 -t 60        # 60s window with heavy smoothing
  
  Interactive controls:
    + or = : Increase time window by 5 seconds
    -      : Decrease time window by 5 seconds
''')
    
    parser.add_argument(
        '-s', '--smooth-window',
        type=int,
        default=DEFAULT_SMOOTH_WINDOW,
        metavar='N',
        help=f'smoothing window size (default: {DEFAULT_SMOOTH_WINDOW}). Higher values = smoother graphs but less responsive. Range: 1-20'
    )
    
    parser.add_argument(
        '-t', '--time-window',
        type=int,
        default=DEFAULT_TIME_WINDOW,
        metavar='N',
        help=f'time window in seconds to display (default: {DEFAULT_TIME_WINDOW}). Use +/- keys to adjust while running'
    )
    
    args = parser.parse_args()
    
    # Validate smooth_window range
    if args.smooth_window < 1 or args.smooth_window > MAX_SMOOTH_WINDOW:
        parser.error(f"smooth-window must be between 1 and {MAX_SMOOTH_WINDOW}")
    
    print("Starting real-time system monitoring...")
    print(f"Smoothing window: {args.smooth_window}")
    print(f"Time window: {args.time_window} seconds (use +/- keys to adjust)")
    print("Close the window to stop monitoring.\n")
    
    monitor = RealtimeMonitor(max_points=args.time_window, smooth_window=args.smooth_window)
    monitor.start()

if __name__ == "__main__":
    main()
