"""
PyQtGraph-based System Monitor
Demonstrates real-time CPU, Disk I/O, and Network monitoring with smooth performance
"""

import sys
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import psutil
import time

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
        self.resize(1000, 700)
        
        # Configuration
        self.time_window = 20  # seconds
        self.update_interval = 200  # ms
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
        self.setup_timer()
        
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
        
        # Setup plots
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

def main():
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()