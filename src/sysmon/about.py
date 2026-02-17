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

from pyqt_app_info import AppIdentity, gather_info

from sysmon.constants import (VERSION, RELEASE_DATE, FULL_VERSION,
                               BUILD_INFO, APPLICATION_START_TIME,
                               PYTHON_VERSION, PLATFORM_INFO, RELEASE_TIME)
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
        """Show about dialog using pyqt-app-info for environment details"""
        # Gather app info via pyqt-app-info
        identity = AppIdentity(
            name="SysMon",
            short_name="SysMon",
            version=VERSION,
            commit_date=f"{RELEASE_DATE} {RELEASE_TIME}",
            description="Real-time system monitoring with PyQtGraph",
            features=[
                "Real-time CPU, Disk I/O, Network monitoring",
                "Live RAM & Swap memory display",
                "Process drill-down analysis",
                "Window transparency, always-on-top, XDG compliance",
            ],
        )
        info = gather_info(identity, caller_file=__file__)

        # Calculate runtime
        uptime = datetime.datetime.now() - APPLICATION_START_TIME
        uptime_str = str(uptime).split('.')[0]

        # Helper to escape HTML
        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Build identity section HTML
        features_html = "".join(f"<li>{esc(f)}</li>" for f in info.identity.features)
        identity_html = f"""
        <h3>{esc(info.identity.name)}</h3>
        <p><b>Version:</b> {esc(info.identity.version)}</p>
        <p><b>Commit Date:</b> {esc(info.identity.commit_date)}</p>
        <p><b>Runtime:</b> {esc(uptime_str)}</p>
        <br>
        <p>{esc(info.identity.description)}</p>
        <br>
        <p><b>Features:</b></p>
        <ul>{features_html}</ul>
        """

        # Build technical details section HTML
        ex = info.execution
        tech_html = f"""
        <p style="font-size: 9pt; color: #666;">
        <b>Execution Mode:</b> {esc(ex.execution_mode)}<br><br>
        <b>Code Location:</b><br>{esc(ex.code_location)}<br><br>
        <b>Python Executable:</b><br>{esc(ex.python_executable)}<br><br>
        <b>Python Version:</b> {esc(ex.python_version)}<br><br>
        <b>OS:</b> {esc(ex.os_platform)}
        </p>
        """

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"About {info.identity.name}")
        dialog.setModal(True)
        dialog.resize(600, 500)

        layout = QVBoxLayout()

        # Identity label
        identity_label = QLabel()
        identity_label.setTextFormat(Qt.RichText)
        identity_label.setWordWrap(True)
        identity_label.setText(identity_html)
        layout.addWidget(identity_label)

        layout.addSpacing(10)

        # Technical details label (selectable for copying)
        tech_label = QLabel()
        tech_label.setTextFormat(Qt.RichText)
        tech_label.setWordWrap(True)
        tech_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        tech_label.setText(tech_html)
        layout.addWidget(tech_label)

        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
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
