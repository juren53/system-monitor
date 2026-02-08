"""
SysMon Network Dialogs
NetworkWorker and RealTimeNetworkDialog.
"""

import psutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QSpinBox, QTableWidget,
                              QTableWidgetItem, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QGuiApplication


class NetworkWorker(QObject):
    """Worker for network connection analysis"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._cancelled = False

    def cancel(self):
        """Cancel the operation"""
        self._cancelled = True

    def run(self):
        """Collect network connection data with enhanced metrics"""
        try:
            processes = []

            # Collect all processes with network connections
            for proc in psutil.process_iter(['pid', 'name']):
                if self._cancelled:
                    return

                try:
                    pid = proc.info['pid']
                    name = proc.info['name']

                    # Get network connections
                    connections = proc.connections(kind='inet')

                    if len(connections) > 0:
                        # Count by protocol
                        tcp_count = sum(1 for conn in connections if conn.type == 1)  # SOCK_STREAM
                        udp_count = sum(1 for conn in connections if conn.type == 2)  # SOCK_DGRAM

                        # Count by state (only TCP has states)
                        established_count = sum(1 for conn in connections
                                               if hasattr(conn, 'status') and conn.status == 'ESTABLISHED')
                        listen_count = sum(1 for conn in connections
                                          if hasattr(conn, 'status') and conn.status == 'LISTEN')

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
                            'connections': len(connections),
                            'tcp_connections': tcp_count,
                            'udp_connections': udp_count,
                            'established_count': established_count,
                            'listen_count': listen_count
                        })

                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue

            # Sort by total connections and get top 10
            processes.sort(key=lambda x: x['connections'], reverse=True)
            top_processes = processes[:10]

            # Return results
            self.finished.emit(top_processes)

        except Exception as e:
            self.error.emit(f"Error analyzing network connections: {str(e)}")


class RealTimeNetworkDialog(QDialog):
    """Real-time dynamic network connections dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Top 10 Network Processes")
        self.resize(950, 400)

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
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "PID", "Process Name", "Total Conns", "TCP", "UDP", "ESTABLISHED"
        ])

        # Left-justify header labels
        header = self.table_widget.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Set column widths
        self.table_widget.setColumnWidth(0, 80)   # PID
        self.table_widget.setColumnWidth(1, 400)  # Process Name / Command Line
        self.table_widget.setColumnWidth(2, 100)  # Total Connections
        self.table_widget.setColumnWidth(3, 80)   # TCP
        self.table_widget.setColumnWidth(4, 80)   # UDP
        self.table_widget.setColumnWidth(5, 120)  # ESTABLISHED

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
        dialog_width = 750
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
        self.process_worker = NetworkWorker()
        self.process_worker.moveToThread(self.process_thread)

        # Connect signals
        self.process_worker.finished.connect(self.update_table)
        self.process_thread.started.connect(self.process_worker.run)

        self.process_thread.start()

    def update_table(self, processes):
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

            # Total Connections
            total_conns = proc.get('connections', 0)
            total_item = QTableWidgetItem(str(total_conns))
            total_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 2, total_item)

            # TCP Connections
            tcp_conns = proc.get('tcp_connections', 0)
            tcp_item = QTableWidgetItem(str(tcp_conns))
            tcp_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 3, tcp_item)

            # UDP Connections
            udp_conns = proc.get('udp_connections', 0)
            udp_item = QTableWidgetItem(str(udp_conns))
            udp_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 4, udp_item)

            # ESTABLISHED Connections
            established = proc.get('established_count', 0)
            est_item = QTableWidgetItem(str(established))
            est_item.setFont(QFont("Arial", 10))
            self.table_widget.setItem(row, 5, est_item)

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
