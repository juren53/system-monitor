"""
SysMon Window Mixin
Window positioning, geometry persistence, keyboard/mouse events, transparency, and always-on-top.
"""

import os
import json

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication


class WindowMixin:
    """Window management methods for SystemMonitor."""

    # Keyboard Navigation Methods
    def keyPressEvent(self, event):
        """Handle keyboard events for window positioning"""
        if event.key() == Qt.Key_Left:
            self.position_window_left()
        elif event.key() == Qt.Key_Right:
            self.position_window_right()
        elif event.key() == Qt.Key_M:
            self.minimize_window()
        elif event.key() == Qt.Key_Down:
            self.minimize_window()
        elif event.key() == Qt.Key_T:
            self.toggle_transparency()
        elif event.key() == Qt.Key_Q:
            self.close()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.increase_smoothing()
        elif event.key() == Qt.Key_Minus:
            self.decrease_smoothing()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Left-click to minimize window"""
        if event.button() == Qt.LeftButton:
            self.minimize_window()
        else:
            super().mousePressEvent(event)

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

    def minimize_window(self):
        """Minimize the application window to taskbar"""
        try:
            self.showMinimized()
        except Exception as e:
            print(f"Error minimizing window: {e}")

    def toggle_transparency(self):
        """Toggle window transparency between opaque and 50% transparent"""
        try:
            if self._transparency_toggled:
                # Return to opaque (100%)
                self.set_window_transparency(1.0)
                self._transparency_toggled = False
            else:
                # Set to 50% transparent
                self.set_window_transparency(0.5)
                self._transparency_toggled = True
        except Exception as e:
            print(f"Error toggling transparency: {e}")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

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
                    # Set flag before loading any preferences to block signal handling
                    self._loading_preferences = True
                    self.update_interval = prefs.get('update_interval', 200)
                    self.time_window = prefs.get('time_window', 30)
                    self.transparency = prefs.get('transparency', 1.0)
                    self.always_on_top = prefs.get('always_on_top', False)
                    self.invert_axis = prefs.get('invert_axis', False)
                    self.smoothing_window = prefs.get('smoothing_window', 1)
                    self.theme_mode = prefs.get('theme_mode', 'auto')
                    self.auto_check_updates = prefs.get('auto_check_updates', False)
                    self.last_update_check = prefs.get('last_update_check', 0)
                    self.update_check_interval_days = prefs.get('update_check_interval_days', 7)
                    self.skipped_update_versions = prefs.get('skipped_update_versions', [])

                    # Apply loaded preferences
                    if hasattr(self, 'timer'):
                        self.timer.setInterval(self.update_interval)
                    self.max_points = int((self.time_window * 1000) / self.update_interval)
                    self.set_window_transparency(self.transparency)
                    self.set_always_on_top(self.always_on_top)
                    self.always_on_top_action.setChecked(self.always_on_top)

                    # Apply saved axis inversion state to all graphs
                    if self.invert_axis:
                        self.cpu_plot.getPlotItem().getViewBox().invertX(True)
                        self.memory_plot.getPlotItem().getViewBox().invertX(True)
                        self.disk_plot.getPlotItem().getViewBox().invertX(True)
                        self.net_plot.getPlotItem().getViewBox().invertX(True)

                    # Clear the flag after all preferences are applied
                    self._loading_preferences = False

        except Exception as e:
            self._loading_preferences = False  # Ensure flag is reset even on error
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

    def set_window_transparency(self, transparency):
        """Set window transparency (0.0 to 1.0)"""
        self.transparency = max(0.1, min(1.0, transparency))  # Clamp between 0.1 and 1.0
        self.setWindowOpacity(self.transparency)

    def change_transparency(self):
        """Change window transparency through slider dialog"""
        from PyQt5.QtWidgets import QSlider

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
