"""
SysMon About/Help Mixin
Help menu dialogs: about, changelog, users guide, keyboard shortcuts,
issue tracker, and real-time process/disk/network drill-down launchers.
"""

import os
import datetime
import webbrowser

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QTextEdit, QTextBrowser, QMessageBox,
                              QProgressDialog, QApplication)
from PyQt5.QtCore import Qt, QThread

from sysmon.constants import (VERSION, RELEASE_DATE, FULL_VERSION,
                               BUILD_INFO, APPLICATION_START_TIME,
                               PYTHON_VERSION, PLATFORM_INFO)
from sysmon.dialogs import (ProcessWorker, ProcessInfoDialog,
                             RealTimeProcessDialog, RealTimeDiskDialog,
                             RealTimeNetworkDialog)


class AboutMixin:
    """Help menu dialog methods for SystemMonitor."""

    def show_top_processes(self, metric_type):
        """Show top processes for the specified metric with async processing"""
        # Create progress dialog
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

    def show_changelog(self):
        """Show changelog dialog with rendered markdown"""
        changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'CHANGELOG.md')
        github_url = 'https://raw.githubusercontent.com/juren53/system-monitor/main/docs/CHANGELOG.md'

        markdown_content, source_info = self.load_document_with_fallback(
            changelog_path, github_url, 'ChangeLog'
        )

        # Append source info if loaded from GitHub
        if source_info:
            markdown_content += source_info

        # Convert markdown to HTML
        html_content = self.render_markdown_to_html(markdown_content)

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon ChangeLog")
        dialog.setModal(True)
        dialog.resize(900, 700)

        # Use QTextBrowser instead of QTextEdit for better HTML rendering
        text_browser = QTextBrowser()
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)  # Allow clicking links
        text_browser.setHtml(html_content)

        # Remove extra stylesheet since HTML has embedded CSS
        text_browser.setStyleSheet("QTextBrowser { border: none; }")

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(text_browser)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

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
        """Show users guide dialog with rendered markdown"""
        users_guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'users-guide.md')
        github_url = 'https://raw.githubusercontent.com/juren53/system-monitor/main/docs/users-guide.md'

        markdown_content, source_info = self.load_document_with_fallback(
            users_guide_path, github_url, 'Users Guide'
        )

        # Append source info if loaded from GitHub
        if source_info:
            markdown_content += source_info

        # Convert markdown to HTML
        html_content = self.render_markdown_to_html(markdown_content)

        # Create dialog (same as changelog but larger)
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon Users Guide")
        dialog.setModal(True)
        dialog.resize(1000, 750)

        text_browser = QTextBrowser()
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(html_content)
        text_browser.setStyleSheet("QTextBrowser { border: none; }")

        # Close button and layout (same as changelog)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)

        layout = QVBoxLayout()
        layout.addWidget(text_browser)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        dialog.exec_()

    def show_realtime_processes(self, metric_type):
        """Show real-time process monitoring dialog"""
        if metric_type == 'cpu':
            dialog = RealTimeProcessDialog(self)
            dialog.exec_()

    def show_realtime_disk(self):
        """Show real-time disk I/O monitoring dialog"""
        dialog = RealTimeDiskDialog(self)
        dialog.exec_()

    def show_realtime_network(self):
        """Show real-time network monitoring dialog"""
        dialog = RealTimeNetworkDialog(self)
        dialog.exec_()

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog with rendered markdown"""
        shortcuts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'keyboard-shortcuts.md')
        github_url = 'https://raw.githubusercontent.com/juren53/system-monitor/main/docs/keyboard-shortcuts.md'

        markdown_content, source_info = self.load_document_with_fallback(
            shortcuts_path, github_url, 'Keyboard Shortcuts'
        )

        # Append source info if loaded from GitHub
        if source_info:
            markdown_content += source_info

        # Convert markdown to HTML
        html_content = self.render_markdown_to_html(markdown_content)

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("SysMon Keyboard Shortcuts")
        dialog.setModal(True)
        dialog.resize(800, 650)

        text_browser = QTextBrowser()
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(html_content)
        text_browser.setStyleSheet("QTextBrowser { border: none; }")

        # Close button and layout
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)

        layout = QVBoxLayout()
        layout.addWidget(text_browser)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        dialog.exec_()

    def show_issue_tracker(self):
        """Open SysMon issue tracker in default web browser"""
        try:
            webbrowser.open('https://github.com/juren53/system-monitor/issues')
        except Exception as e:
            QMessageBox.warning(
                self,
                'Unable to Open Browser',
                f'Could not open issue tracker in browser.\n\n'
                f'Please visit:\nhttps://github.com/juren53/system-monitor/issues\n\n'
                f'Error: {str(e)}'
            )

    def show_changelog_github(self):
        """Open SysMon ChangeLog on GitHub in default web browser"""
        try:
            webbrowser.open('https://github.com/juren53/system-monitor/blob/main/docs/CHANGELOG.md')
        except Exception as e:
            QMessageBox.warning(
                self,
                'Unable to Open Browser',
                f'Could not open ChangeLog in browser.\n\n'
                f'Please visit:\nhttps://github.com/juren53/system-monitor/blob/main/docs/CHANGELOG.md\n\n'
                f'Error: {str(e)}'
            )
