"""
SysMon Process Dialogs
ProcessWorker, ProcessInfoDialog, and RealTimeProcessDialog.
"""

import time

import psutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QTextEdit, QSpinBox, QTableWidget,
                              QTableWidgetItem, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QGuiApplication


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

            # Use two-pass approach for accurate CPU measurements
            if self.metric_type == 'cpu':
                # First pass: collect ALL processes and initialize cpu_percent()
                # NOTE: We must collect all processes, not just first 200, to avoid missing
                # high-PID processes like Python, Chrome, etc.
                procs_list = []
                for proc in psutil.process_iter(['pid', 'name']):
                    if self._cancelled:
                        return
                    total_checked += 1

                    try:
                        # Initialize cpu_percent (first call returns 0.0)
                        proc.cpu_percent()
                        procs_list.append(proc)

                        if total_checked % 100 == 0:
                            self.progress.emit(min(50, int((total_checked / 500) * 50)))  # 0-50% for first pass

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Wait 0.5 seconds for CPU measurement
                time.sleep(0.5)

                # Second pass: get actual CPU and memory percentages
                for idx, proc in enumerate(procs_list):
                    if self._cancelled:
                        return

                    try:
                        cpu_value = proc.cpu_percent()  # Second call returns actual percentage
                        memory_value = proc.memory_percent()

                        # Collect command line only (for performance)
                        try:
                            cmdline_list = proc.cmdline()
                            cmdline = ' '.join(cmdline_list) if cmdline_list else proc.info['name']
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            cmdline = proc.info['name']

                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'cpu_percent': cpu_value,
                            'memory_percent': memory_value
                        })

                        if idx % 50 == 0:
                            self.progress.emit(50 + int((idx / len(procs_list)) * 50))  # 50-100% for second pass

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            else:
                # For disk/network, collect ALL processes (same as CPU)
                for proc in psutil.process_iter(['pid', 'name']):
                    if self._cancelled:
                        return
                    total_checked += 1

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

                        if total_checked % 100 == 0:
                            self.progress.emit(min(100, int((total_checked / 500) * 100)))

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


class RealTimeProcessDialog(QDialog):
    """Real-time dynamic top processes dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Top 10 CPU Processes")
        self.resize(750, 400)

        # Update interval in milliseconds (default 3 seconds)
        self.update_interval = 3000

        # Timer for real-time updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)

        # Background threading
        self.process_thread = None
        self.process_worker = None

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
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["PID", "Process Name", "CPU %", "Memory %"])

        # Left-justify header labels
        header = self.table_widget.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Set column widths
        self.table_widget.setColumnWidth(0, 80)   # PID
        self.table_widget.setColumnWidth(1, 400)  # Process Name / Command Line
        self.table_widget.setColumnWidth(2, 100)  # CPU %
        self.table_widget.setColumnWidth(3, 100)  # Memory %

        # Make table rows non-editable
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Enable sorting by clicking column headers
        self.table_widget.setSortingEnabled(True)

        # Sort by CPU descending - data will be pre-sorted

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
        dialog_width = 550
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
        self.process_worker = ProcessWorker('cpu')
        self.process_worker.moveToThread(self.process_thread)

        # Connect signals
        self.process_worker.finished.connect(self.update_table)
        self.process_thread.started.connect(self.process_worker.run)

        self.process_thread.start()

    def update_table(self, processes, metric_type=None):
        """Update table with new process data"""
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

            # CPU %
            cpu_percent = proc['cpu_percent']
            cpu_item = QTableWidgetItem(f"{cpu_percent:.1f}%")
            cpu_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 2, cpu_item)

            # Memory %
            memory_percent = proc.get('memory_percent', 0.0)
            memory_item = QTableWidgetItem(f"{memory_percent:.1f}%")
            memory_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 3, memory_item)

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
