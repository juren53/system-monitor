"""
SysMon Disk I/O Dialogs
DiskIOWorker and RealTimeDiskDialog.
"""

import time

import psutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QSpinBox, QTableWidget,
                              QTableWidgetItem, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QGuiApplication


class DiskIOWorker(QObject):
    """Worker for disk I/O rate calculation"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, prev_io_counters=None, prev_timestamp=None):
        super().__init__()
        self.prev_io_counters = prev_io_counters or {}
        self.prev_timestamp = prev_timestamp
        self._cancelled = False

    def cancel(self):
        """Cancel the operation"""
        self._cancelled = True

    def run(self):
        """Collect disk I/O data with rate calculations"""
        try:
            current_timestamp = time.time()
            current_io_counters = {}
            processes = []

            # Calculate time delta
            if self.prev_timestamp:
                time_delta = current_timestamp - self.prev_timestamp
            else:
                time_delta = 1.0  # Default to 1 second for first run

            # Collect all processes
            for proc in psutil.process_iter(['pid', 'name']):
                if self._cancelled:
                    return

                try:
                    pid = proc.info['pid']
                    name = proc.info['name']

                    # Get I/O counters
                    io = proc.io_counters()
                    current_io_counters[pid] = io

                    # Calculate rates if we have previous data
                    if pid in self.prev_io_counters:
                        prev_io = self.prev_io_counters[pid]
                        read_rate = (io.read_bytes - prev_io.read_bytes) / time_delta / (1024**2)
                        write_rate = (io.write_bytes - prev_io.write_bytes) / time_delta / (1024**2)
                    else:
                        read_rate = 0.0
                        write_rate = 0.0

                    # Total I/O in MB
                    total_io = (io.read_bytes + io.write_bytes) / (1024**2)

                    # Only include processes with some I/O activity
                    if total_io > 0.01 or read_rate > 0.01 or write_rate > 0.01:
                        # Collect command line only (for performance)
                        try:
                            cmdline_list = proc.cmdline()
                            cmdline = ' '.join(cmdline_list) if cmdline_list else name
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            cmdline = name

                        processes.append({
                            'pid': pid,
                            'name': name,
                            'cmdline': cmdline,
                            'read_rate': max(0, read_rate),  # Ensure non-negative
                            'write_rate': max(0, write_rate),
                            'total_io': total_io
                        })

                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue

            # Sort by total I/O rate (read + write) and get top 10
            processes.sort(key=lambda x: x['read_rate'] + x['write_rate'], reverse=True)
            top_processes = processes[:10]

            # Return results
            self.finished.emit({
                'processes': top_processes,
                'io_counters': current_io_counters,
                'timestamp': current_timestamp
            })

        except Exception as e:
            self.error.emit(f"Error analyzing disk I/O: {str(e)}")


class RealTimeDiskDialog(QDialog):
    """Real-time dynamic disk I/O processes dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Top 10 Disk I/O Processes")
        self.resize(850, 400)

        # Update interval in milliseconds (default 3 seconds)
        self.update_interval = 3000

        # Timer for real-time updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)

        # Background threading
        self.process_thread = None
        self.process_worker = None

        # State tracking for rate calculation
        self.prev_io_counters = {}  # {pid: io_counters}
        self.prev_timestamp = None

        # Setup UI
        self.setup_ui()

        # Position dialog intelligently
        self.position_dialog_intelligently()

        # Start real-time updates
        self.start_real_time_updates()

    def setup_ui(self):
        """Setup the dialog UI components"""
        layout = QVBoxLayout()

        # Status indicator and controls
        control_layout = QHBoxLayout()

        # Status label
        self.status_label = QLabel(f"🟢 Auto-updating every {self.update_interval / 1000:.0f} seconds")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #4CAF50; }")
        control_layout.addWidget(self.status_label)

        control_layout.addStretch()

        # Update interval controls
        interval_label = QLabel("Update every:")
        control_layout.addWidget(interval_label)

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(60)
        self.interval_spinbox.setValue(int(self.update_interval / 1000))
        self.interval_spinbox.setSuffix(" sec")
        self.interval_spinbox.valueChanged.connect(self.change_update_interval)
        control_layout.addWidget(self.interval_spinbox)

        # Pause/Resume button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self.refresh_data)
        control_layout.addWidget(refresh_btn)

        layout.addLayout(control_layout)

        # Filter text box
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Type to filter processes by name or PID...")
        self.filter_box.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_box)

        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(lambda: self.filter_box.clear())
        filter_layout.addWidget(clear_filter_btn)

        layout.addLayout(filter_layout)

        # Table widget for process data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["PID", "Process Name", "Read MB/s", "Write MB/s", "Total MB"])

        # Left-justify header labels
        header = self.table_widget.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Set column widths
        self.table_widget.setColumnWidth(0, 80)   # PID
        self.table_widget.setColumnWidth(1, 400)  # Process Name / Command Line
        self.table_widget.setColumnWidth(2, 100)  # Read MB/s
        self.table_widget.setColumnWidth(3, 100)  # Write MB/s
        self.table_widget.setColumnWidth(4, 100)  # Total MB

        # Make table rows non-editable
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Enable sorting by clicking column headers
        self.table_widget.setSortingEnabled(True)

        layout.addWidget(self.table_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def position_dialog_intelligently(self):
        """Position dialog to avoid covering main window"""
        main_window = self.parent()

        # Dialog dimensions
        dialog_width = 650
        dialog_height = 400

        if main_window:
            try:
                # Get main window geometry safely
                main_rect = main_window.frameGeometry()
                screen = QGuiApplication.screenAt(main_rect.center())
                if not screen:
                    screen = QGuiApplication.primaryScreen()

                if screen:
                    available = screen.availableGeometry()

                    # Try to position to the right of main window
                    right_x = main_rect.right() + 20  # 20px gap
                    if right_x + dialog_width <= available.right():
                        x_pos = right_x
                        y_pos = main_rect.top()
                    else:
                        # Fall back to below main window
                        x_pos = main_rect.left()
                        y_pos = main_rect.bottom() + 20
                        # Ensure dialog fits on screen vertically
                        if y_pos + dialog_height > available.bottom():
                            y_pos = available.bottom() - dialog_height - 20

                    self.move(x_pos, y_pos)
                    return
            except:
                pass

        # Fallback to screen center
        if QGuiApplication.primaryScreen():
            screen_rect = QGuiApplication.primaryScreen().availableGeometry()
            x_pos = screen_rect.left() + (screen_rect.width() - dialog_width) // 2
            y_pos = screen_rect.top() + (screen_rect.height() - dialog_height) // 2
            self.move(x_pos, y_pos)

        self.resize(dialog_width, dialog_height)

    def start_real_time_updates(self):
        """Start real-time data updates"""
        self.update_timer.start(self.update_interval)
        self.is_paused = False

    def toggle_pause(self):
        """Toggle between pause and resume"""
        if self.is_paused:
            # Resume updates
            self.update_timer.start(self.update_interval)
            self.is_paused = False
            self.pause_btn.setText("Pause")
            self.status_label.setText(f"🟢 Auto-updating every {self.update_interval / 1000:.0f} seconds")
            self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #4CAF50; }")
        else:
            # Pause updates
            self.update_timer.stop()
            self.is_paused = True
            self.pause_btn.setText("Resume")
            self.status_label.setText("🟡 Updates paused")
            self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #FF9800; }")

    def change_update_interval(self, value):
        """Change the update interval based on spinbox value"""
        self.update_interval = value * 1000  # Convert seconds to milliseconds

        # Update status label
        if not self.is_paused:
            self.status_label.setText(f"🟢 Auto-updating every {value} seconds")

        # Restart timer with new interval if not paused
        if not self.is_paused:
            self.update_timer.stop()
            self.update_timer.start(self.update_interval)

    def refresh_data(self):
        """Refresh process data in background thread"""
        # Clean up previous thread if exists
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.quit()
            self.process_thread.wait()

        # Start new thread for data collection
        self.process_thread = QThread()
        self.process_worker = DiskIOWorker(self.prev_io_counters, self.prev_timestamp)
        self.process_worker.moveToThread(self.process_thread)

        # Connect signals
        self.process_worker.finished.connect(self.update_table)
        self.process_thread.started.connect(self.process_worker.run)

        self.process_thread.start()

    def update_table(self, result):
        """Update table with new process data"""
        processes = result['processes']
        self.prev_io_counters = result['io_counters']
        self.prev_timestamp = result['timestamp']

        if not processes:
            return

        # Clear existing data
        self.table_widget.setRowCount(0)

        # Add new data
        self.table_widget.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            # PID
            pid_item = QTableWidgetItem(str(proc['pid']))
            pid_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 0, pid_item)

            # Process Name / Command Line
            cmdline = proc.get('cmdline', proc['name'])
            cmdline_display = cmdline[:70] + '...' if len(cmdline) > 70 else cmdline
            name_item = QTableWidgetItem(cmdline_display)
            name_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 1, name_item)

            # Read MB/s
            read_rate = proc.get('read_rate', 0.0)
            read_item = QTableWidgetItem(f"{read_rate:.2f}")
            read_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 2, read_item)

            # Write MB/s
            write_rate = proc.get('write_rate', 0.0)
            write_item = QTableWidgetItem(f"{write_rate:.2f}")
            write_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 3, write_item)

            # Total MB
            total_io = proc.get('total_io', 0.0)
            total_item = QTableWidgetItem(f"{total_io:.1f}")
            total_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 4, total_item)

    def apply_filter(self):
        """Filter table rows based on search text"""
        filter_text = self.filter_box.text().lower()

        for row in range(self.table_widget.rowCount()):
            # Get PID and process name from the row
            pid_item = self.table_widget.item(row, 0)
            name_item = self.table_widget.item(row, 1)

            if pid_item and name_item:
                pid_text = pid_item.text().lower()
                name_text = name_item.text().lower()

                # Show row if filter text matches PID or name
                if filter_text in pid_text or filter_text in name_text:
                    self.table_widget.setRowHidden(row, False)
                else:
                    self.table_widget.setRowHidden(row, True)
            else:
                # Show row if items don't exist (shouldn't happen, but be safe)
                self.table_widget.setRowHidden(row, False)

    def closeEvent(self, a0):
        """Clean up resources when dialog is closed"""
        # Stop timer
        if self.update_timer:
            self.update_timer.stop()

        # Clean up thread
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.quit()
            self.process_thread.wait()

        # Accept the close event
        a0.accept()
