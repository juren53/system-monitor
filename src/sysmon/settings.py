"""
SysMon Settings Mixin
Configuration dialogs, graph customization, preferences, data export, and view toggles.
"""

import os
import json

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QMessageBox, QFileDialog,
                              QInputDialog, QColorDialog, QComboBox,
                              QGroupBox, QRadioButton, QDialogButtonBox,
                              QSpinBox, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import pyqtgraph as pg

from sysmon.dialogs import ConfigFileViewerDialog


class SettingsMixin:
    """Settings, preferences, and graph customization methods for SystemMonitor."""

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
                         self.net_sent_data, self.net_recv_data, self.time_data,
                         self.ram_percent_data, self.swap_percent_data]:
            if len(data_list) > self.max_points:
                # Trim from the left
                for _ in range(len(data_list) - self.max_points):
                    data_list.popleft()

        # Update x-axis range
        self.cpu_plot.setXRange(-self.time_window, 0)
        self.memory_plot.setXRange(-self.time_window, 0)
        self.disk_plot.setXRange(-self.time_window, 0)
        self.net_plot.setXRange(-self.time_window, 0)

    def increase_smoothing(self):
        """Increase smoothing window by 1 point"""
        if self.smoothing_window < self.max_smoothing:
            self.smoothing_window += 1
            self.show_smoothing_status()
            self.save_preferences()
        else:
            # Already at maximum - show feedback
            self.show_smoothing_limit_status("maximum")

    def decrease_smoothing(self):
        """Decrease smoothing window by 1 point"""
        if self.smoothing_window > self.min_smoothing:
            self.smoothing_window -= 1
            self.show_smoothing_status()
            self.save_preferences()
        else:
            # Already at minimum - show feedback
            self.show_smoothing_limit_status("minimum")

    def show_smoothing_status(self):
        """Display current smoothing level as status message"""
        if self.smoothing_window == 1:
            status_msg = "Smoothing: OFF (Raw data)"
        else:
            # Calculate approximate time window for smoothing
            time_span = (self.smoothing_window * self.update_interval) / 1000
            status_msg = f"Smoothing: {self.smoothing_window}-point ({time_span:.2f}s window)"

        # Display in window title briefly
        original_title = self.windowTitle()
        self.setWindowTitle(f"SysMon - {status_msg}")

        # Reset title after 2 seconds
        QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))

    def show_smoothing_limit_status(self, limit_type):
        """Display feedback when user tries to exceed smoothing limits"""
        if limit_type == "minimum":
            status_msg = f"Smoothing: Already at MINIMUM ({self.min_smoothing}-point)"
        else:  # maximum
            time_span = (self.max_smoothing * self.update_interval) / 1000
            status_msg = f"Smoothing: Already at MAXIMUM ({self.max_smoothing}-point / {time_span:.2f}s)"

        # Display in window title briefly
        original_title = self.windowTitle()
        self.setWindowTitle(f"SysMon - {status_msg}")

        # Reset title after 2 seconds
        QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))

    def on_axis_changed(self):
        """Handle axis inversion changes from any graph's context menu"""
        # Skip signal handling during preference loading to prevent overwriting saved settings
        if self._loading_preferences:
            return

        # Get the state from whichever graph triggered the signal
        sender = self.sender()  # Get the ViewBox that triggered the signal
        state = sender.getState()
        new_invert_state = state.get('xInverted', False)

        # Only update if state actually changed to avoid recursion
        if new_invert_state != self.invert_axis:
            self.invert_axis = new_invert_state
            # Apply the same state to all four graphs
            self.cpu_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
            self.memory_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
            self.disk_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
            self.net_plot.getPlotItem().getViewBox().invertX(self.invert_axis)
            # Save the preference
            self.save_preferences()

    def save_preferences(self):
        """Save user preferences to separate preferences file"""
        try:
            preferences = {
                'update_interval': self.update_interval,
                'time_window': self.time_window,
                'transparency': self.transparency,
                'always_on_top': self.always_on_top,
                'invert_axis': self.invert_axis,
                'smoothing_window': self.smoothing_window,
                'theme_mode': self.theme_mode,
                'auto_check_updates': self.auto_check_updates,
                'last_update_check': self.last_update_check,
                'update_check_interval_days': self.update_check_interval_days,
                'skipped_update_versions': self.skipped_update_versions
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
                    writer.writerow(['Time', 'CPU %', 'Memory RAM %', 'Memory Swap %',
                                   'Disk Read (MB/s)', 'Disk Write (MB/s)',
                                   'Network Sent (MB/s)', 'Network Received (MB/s)'])

                    for i, time_val in enumerate(self.time_data):
                        writer.writerow([
                            time_val,
                            self.cpu_data[i] if i < len(self.cpu_data) else '',
                            self.ram_percent_data[i] if i < len(self.ram_percent_data) else '',
                            self.swap_percent_data[i] if i < len(self.swap_percent_data) else '',
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
            self.ram_percent_data.clear()
            self.swap_percent_data.clear()
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
            self.smoothing_window = 1
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

    def toggle_memory_plot(self):
        """Toggle Memory plot visibility"""
        self.memory_plot.setVisible(self.show_memory_action.isChecked())

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

    def view_config_files(self):
        """Display configuration files in read-only dialog"""
        dialog = ConfigFileViewerDialog(self.config_file, self.preferences_file, self)
        dialog.exec_()

    def change_time_window_settings(self):
        """Configure time window settings"""
        time_window, ok = QInputDialog.getInt(
            self, 'Time Window', 'Time window (seconds):',
            self.time_window, 5, 300, 5)

        if ok:
            self.time_window = time_window
            self.update_time_window()
            self.save_preferences()

    def change_smoothing_level(self):
        """Configure smoothing level via dialog"""
        level, ok = QInputDialog.getInt(
            self, 'Smoothing Level',
            'Smoothing window (data points):\n1 = No smoothing (raw data)\nHigher = More smoothing',
            self.smoothing_window, 1, 20, 1)

        if ok:
            self.smoothing_window = level
            self.show_smoothing_status()
            self.save_preferences()

    def change_theme(self):
        """Configure theme mode (Auto/Light/Dark)"""
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Theme Selection")
        dialog.setModal(True)
        dialog.resize(400, 250)

        layout = QVBoxLayout()

        # Description
        desc_label = QLabel(
            "Select the theme mode for SysMon:\n\n"
            "• Auto: Automatically detect system theme\n"
            "• Light: Force light theme\n"
            "• Dark: Force dark theme"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Radio buttons group
        group_box = QGroupBox("Theme Mode")
        group_layout = QVBoxLayout()

        self.theme_auto_radio = QRadioButton("Auto (System Detection)")
        self.theme_light_radio = QRadioButton("Light")
        self.theme_dark_radio = QRadioButton("Dark")

        # Set current selection
        if self.theme_mode == 'auto':
            self.theme_auto_radio.setChecked(True)
        elif self.theme_mode == 'light':
            self.theme_light_radio.setChecked(True)
        elif self.theme_mode == 'dark':
            self.theme_dark_radio.setChecked(True)

        group_layout.addWidget(self.theme_auto_radio)
        group_layout.addWidget(self.theme_light_radio)
        group_layout.addWidget(self.theme_dark_radio)
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Show dialog and apply if accepted
        if dialog.exec_() == QDialog.Accepted:
            # Determine selected theme
            old_theme = self.theme_mode
            if self.theme_auto_radio.isChecked():
                self.theme_mode = 'auto'
            elif self.theme_light_radio.isChecked():
                self.theme_mode = 'light'
            elif self.theme_dark_radio.isChecked():
                self.theme_mode = 'dark'

            # Apply theme if changed
            if old_theme != self.theme_mode:
                self.apply_application_theme()
                self.save_preferences()
                QMessageBox.information(
                    self,
                    "Theme Changed",
                    f"Theme set to: {self.theme_mode.capitalize()}\n\nThe new theme has been applied."
                )

    def customize_graph_colors(self):
        """Enhanced graph colors customization with background/grid support"""
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
            "Memory RAM Curve",
            "Memory Swap Curve",
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
        # Map display names to internal keys
        element_map = {
            "CPU Usage Curve": "cpu",
            "Memory RAM Curve": "mem_ram",
            "Memory Swap Curve": "mem_swap",
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
            color = QColor(color_text)
            if color.isValid():
                self.apply_color_to_element(selected_element, color)

                # Save to preferences
                self.save_graph_colors_preference(selected_element, color.name())

    def apply_color_to_element(self, element, color):
        """Apply color to specific graph element"""
        color_pen = pg.mkPen(color=color, width=self.line_thickness)

        if element == "CPU Usage Curve":
            self.cpu_curve.setPen(color_pen)
        elif element == "Memory RAM Curve":
            self.mem_ram_curve.setPen(color_pen)
        elif element == "Memory Swap Curve":
            self.mem_swap_curve.setPen(color_pen)
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
            self.memory_plot.setBackground(color)
            self.disk_plot.setBackground(color)
            self.net_plot.setBackground(color)
        elif element == "Grid Color":
            # Apply to all plots
            for plot in [self.cpu_plot, self.memory_plot, self.disk_plot, self.net_plot]:
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

    def customize_line_thickness(self):
        """Open dialog to adjust graph line thickness"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Line Thickness")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Description
        desc_label = QLabel("Adjust the thickness of graph lines (1-10 pixels):")
        layout.addWidget(desc_label)

        # Spinbox for thickness
        thickness_layout = QHBoxLayout()
        thickness_label = QLabel("Thickness:")
        thickness_layout.addWidget(thickness_label)

        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(1, 10)
        self.thickness_spinbox.setValue(self.line_thickness)
        self.thickness_spinbox.setSuffix(" px")
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addStretch()
        layout.addLayout(thickness_layout)

        # Preview frame
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        preview_frame.setMinimumHeight(60)
        preview_layout = QVBoxLayout(preview_frame)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.update_thickness_preview()
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_frame)

        # Connect spinbox to preview update
        self.thickness_spinbox.valueChanged.connect(self.update_thickness_preview)

        # Buttons
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(lambda: self.apply_line_thickness_from_dialog(dialog))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_thickness_preview(self):
        """Update the preview label to show sample line thickness"""
        thickness = self.thickness_spinbox.value()
        # Create a visual representation using Unicode block characters
        line_char = "━" * 20  # Heavy horizontal line
        self.preview_label.setText(f"<span style='font-size: {8 + thickness}pt;'>{line_char}</span>")
        self.preview_label.setToolTip(f"Preview: {thickness}px thickness")

    def apply_line_thickness_from_dialog(self, dialog):
        """Apply the selected line thickness and close dialog"""
        self.line_thickness = self.thickness_spinbox.value()
        self.apply_line_thickness()
        self.save_line_thickness_preference()
        dialog.accept()

    def apply_line_thickness(self):
        """Apply current line thickness to all graph curves"""
        # Get current colors from each curve
        cpu_color = self.cpu_curve.opts['pen'].color()
        mem_ram_color = self.mem_ram_curve.opts['pen'].color()
        mem_swap_color = self.mem_swap_curve.opts['pen'].color()
        disk_read_color = self.disk_read_curve.opts['pen'].color()
        disk_write_color = self.disk_write_curve.opts['pen'].color()
        net_sent_color = self.net_sent_curve.opts['pen'].color()
        net_recv_color = self.net_recv_curve.opts['pen'].color()

        # Rebuild pens with new thickness
        self.cpu_curve.setPen(pg.mkPen(color=cpu_color, width=self.line_thickness))
        self.mem_ram_curve.setPen(pg.mkPen(color=mem_ram_color, width=self.line_thickness))
        self.mem_swap_curve.setPen(pg.mkPen(color=mem_swap_color, width=self.line_thickness))
        self.disk_read_curve.setPen(pg.mkPen(color=disk_read_color, width=self.line_thickness))
        self.disk_write_curve.setPen(pg.mkPen(color=disk_write_color, width=self.line_thickness))
        self.net_sent_curve.setPen(pg.mkPen(color=net_sent_color, width=self.line_thickness))
        self.net_recv_curve.setPen(pg.mkPen(color=net_recv_color, width=self.line_thickness))

    def save_line_thickness_preference(self):
        """Save line thickness preference to config file"""
        try:
            # Load existing preferences
            preferences = {}
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    preferences = json.load(f)

            # Save line thickness
            preferences['line_thickness'] = self.line_thickness

            # Write back to file
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=4)

        except Exception as e:
            print(f"Failed to save line thickness preference: {e}")

    def load_line_thickness_preference(self):
        """Load saved line thickness preference and apply it"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    preferences = json.load(f)

                if 'line_thickness' in preferences:
                    self.line_thickness = preferences['line_thickness']
                    # Clamp to valid range
                    self.line_thickness = max(1, min(10, self.line_thickness))
                    self.apply_line_thickness()
                    print(f"✅ Loaded line thickness preference: {self.line_thickness}px")

        except Exception as e:
            print(f"Failed to load line thickness preference: {e}")

    def get_current_graph_colors(self):
        """Get current colors from all plot elements"""
        try:
            colors = {}

            # Get colors from CPU plot
            if hasattr(self, 'cpu_curve') and self.cpu_curve:
                colors['cpu'] = self.cpu_curve.opts['pen'].color().name()

            # Get colors from Memory plot
            if hasattr(self, 'mem_ram_curve') and self.mem_ram_curve:
                colors['mem_ram'] = self.mem_ram_curve.opts['pen'].color().name()
            if hasattr(self, 'mem_swap_curve') and self.mem_swap_curve:
                colors['mem_swap'] = self.mem_swap_curve.opts['pen'].color().name()

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
            color = QColor(current_color)
            if color.isValid():
                self.color_display.setStyleSheet(f"background-color: {current_color}; color: white; padding: 5px; min-width: 100px; font-weight: bold;")
