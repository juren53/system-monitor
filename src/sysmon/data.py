"""
SysMon Data Mixin
Timer setup, data collection, plot updates, and smoothing.
"""

import time
import psutil
from PyQt5.QtCore import QTimer


class DataMixin:
    """Data collection and plot update methods for SystemMonitor."""

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

        self.ram_percent_data.append(self.ram_percent)
        self.swap_percent_data.append(self.swap_percent)

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

        # Apply smoothing to all data series
        cpu_smoothed = self.apply_smoothing(self.cpu_data)
        disk_read_smoothed = self.apply_smoothing(self.disk_read_data)
        disk_write_smoothed = self.apply_smoothing(self.disk_write_data)
        net_sent_smoothed = self.apply_smoothing(self.net_sent_data)
        net_recv_smoothed = self.apply_smoothing(self.net_recv_data)

        # Update CPU
        self.cpu_curve.setData(time_array, cpu_smoothed)

        # Update Disk I/O
        self.disk_read_curve.setData(time_array, disk_read_smoothed)
        self.disk_write_curve.setData(time_array, disk_write_smoothed)

        # Update Memory
        ram_smoothed = self.apply_smoothing(self.ram_percent_data)
        swap_smoothed = self.apply_smoothing(self.swap_percent_data)
        self.mem_ram_curve.setData(time_array, ram_smoothed)
        self.mem_swap_curve.setData(time_array, swap_smoothed)

        # Update Network
        self.net_sent_curve.setData(time_array, net_sent_smoothed)
        self.net_recv_curve.setData(time_array, net_recv_smoothed)

    def apply_smoothing(self, data):
        """Apply moving average smoothing to data

        Args:
            data: List or deque of numeric values

        Returns:
            List of smoothed values (same length as input)
        """
        if self.smoothing_window <= 1 or len(data) < 2:
            return list(data)

        smoothed = []
        window = min(self.smoothing_window, len(data))

        for i in range(len(data)):
            # Calculate average of current point and previous points
            start_idx = max(0, i - window + 1)
            window_data = list(data)[start_idx:i+1]
            avg = sum(window_data) / len(window_data)
            smoothed.append(avg)

        return smoothed
