"""
SysMon Updates Mixin
GitHub version checking and update notification methods.
"""

import time
import threading
import webbrowser

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QTextEdit, QMessageBox)
from PyQt5.QtCore import QTimer, Qt

try:
    from github_version_checker import GitHubVersionChecker, VersionCheckResult
except ImportError:
    GitHubVersionChecker = None
    VersionCheckResult = None

from .constants import VERSION


class UpdatesMixin:
    """Update checking methods for SystemMonitor."""

    def check_for_updates(self):
        """Check for newer SysMon releases on GitHub"""
        if not GitHubVersionChecker:
            QMessageBox.warning(
                self,
                'Update Check Unavailable',
                'GitHub version checker module is not available.\n\n'
                'Please ensure the github_version_checker.py file is present.'
            )
            return

        # Show progress indicator
        QMessageBox.information(
            self,
            'Checking for Updates',
            'Checking for SysMon updates on GitHub...\n\nThis may take a few seconds.'
        )

        # Create version checker for SysMon repository
        checker = GitHubVersionChecker(
            repo_url="juren53/system-monitor",
            current_version=VERSION,
            timeout=15
        )

        # Perform check
        result = checker.get_latest_version()

        if result.error_message:
            QMessageBox.warning(
                self,
                'Update Check Failed',
                f'Unable to check for updates:\n\n{result.error_message}\n\n'
                'Please check your internet connection and try again.'
            )
            return

        # Update last check time
        self.last_update_check = time.time()
        self.save_preferences()

        if result.has_update:
            self.show_update_available_dialog(result)
        else:
            QMessageBox.information(
                self,
                'Up to Date',
                f'You have the latest version of SysMon!\n\n'
                f'Current Version: {result.current_version}\n'
                f'Latest Version: {result.latest_version}\n\n'
                'SysMon is up to date.'
            )

    def show_update_available_dialog(self, result):
        """Show dialog when update is available"""
        # Check if this version was skipped
        if result.latest_version in self.skipped_update_versions:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon Update Available")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("🆕 SysMon Update Available!")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3; margin: 10px;")
        layout.addWidget(title_label)

        # Version info
        info_text = f"""
        <div style='padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin: 5px;'>
            <b>Current Version:</b> {result.current_version}<br>
            <b>Latest Version:</b> {result.latest_version}<br>
            <b>Release Date:</b> {result.published_date[:10] if result.published_date else 'N/A'}
        </div>
        """

        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)

        # Release notes preview
        if result.release_notes:
            notes_text = result.release_notes[:300]
            if len(result.release_notes) > 300:
                notes_text += "..."

            notes_label = QLabel("Release Notes:")
            notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(notes_label)

            notes_browser = QTextEdit()
            notes_browser.setPlainText(notes_text)
            notes_browser.setReadOnly(True)
            notes_browser.setMaximumHeight(150)
            layout.addWidget(notes_browser)

        # Buttons
        button_layout = QHBoxLayout()

        download_button = QPushButton("Download Update")
        download_button.setStyleSheet("""
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
        """)
        download_button.clicked.connect(lambda: webbrowser.open(result.download_url))
        button_layout.addWidget(download_button)

        skip_button = QPushButton("Skip This Version")
        skip_button.clicked.connect(lambda: self.skip_update_version(result.latest_version, dialog))
        button_layout.addWidget(skip_button)

        later_button = QPushButton("Remind Me Later")
        later_button.clicked.connect(dialog.accept)
        button_layout.addWidget(later_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        # Show dialog
        dialog.exec_()

    def skip_update_version(self, version, dialog):
        """Skip the specified version"""
        if version not in self.skipped_update_versions:
            self.skipped_update_versions.append(version)
            self.save_preferences()

        dialog.accept()

        QMessageBox.information(
            self,
            'Update Skipped',
            f'Version {version} has been skipped.\n\n'
            'You will not be notified about this version again.\n'
            'You can enable notifications again in preferences.'
        )

    def toggle_auto_check_updates(self):
        """Toggle automatic update checking"""
        self.auto_check_updates = self.auto_check_updates_action.isChecked()
        self.save_preferences()

        if self.auto_check_updates:
            QMessageBox.information(
                self,
                'Auto-check Enabled',
                'SysMon will automatically check for updates on startup.\n\n'
                f'Checks will be performed every {self.update_check_interval_days} days.'
            )
        else:
            QMessageBox.information(
                self,
                'Auto-check Disabled',
                'SysMon will not automatically check for updates.\n\n'
                'You can still check manually from the Help menu.'
            )

    def check_updates_on_startup(self):
        """Check for updates on startup if enabled"""
        if not self.auto_check_updates or not GitHubVersionChecker:
            return

        current_time = time.time()
        days_since_last_check = (current_time - self.last_update_check) / (24 * 60 * 60)

        if days_since_last_check >= self.update_check_interval_days:
            # Perform check in background to not block startup
            def background_check():
                try:
                    checker = GitHubVersionChecker(
                        repo_url="juren53/system-monitor",
                        current_version=VERSION,
                        timeout=10
                    )
                    result = checker.get_latest_version()

                    if result.has_update and not result.error_message:
                        if result.latest_version not in self.skipped_update_versions:
                            # Show notification in main thread
                            QTimer.singleShot(1000, lambda: self.show_startup_update_notification(result))

                    # Update last check time
                    self.last_update_check = time.time()
                    self.save_preferences()

                except Exception as e:
                    print(f"Startup update check failed: {e}")

            # Run in background thread
            thread = threading.Thread(target=background_check, daemon=True)
            thread.start()

    def show_startup_update_notification(self, result):
        """Show update notification on startup"""
        reply = QMessageBox.question(
            self,
            'SysMon Update Available',
            f'A new version of SysMon is available!\n\n'
            f'Current: {result.current_version}\n'
            f'Latest: {result.latest_version}\n\n'
            'Would you like to download the update now?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            webbrowser.open(result.download_url)
