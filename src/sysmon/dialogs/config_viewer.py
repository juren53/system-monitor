"""
SysMon Config Viewer Dialog
Read-only dialog for viewing SysMon configuration files.
"""

import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                              QTextEdit, QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ConfigFileViewerDialog(QDialog):
    """Dialog showing SysMon configuration files in read-only tabs"""
    def __init__(self, config_file, preferences_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SysMon Configuration Files")
        self.resize(700, 500)

        layout = QVBoxLayout()

        # Create tabbed interface for both config files
        tab_widget = QTabWidget()

        # Tab 1: config.json
        config_tab = QWidget()
        config_layout = QVBoxLayout()

        # Label showing full path
        config_path_label = QLabel(f"<b>File:</b> {config_file}")
        config_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        config_path_label.setWordWrap(True)
        config_layout.addWidget(config_path_label)

        # Text editor for config.json
        config_text_edit = QTextEdit()
        config_text_edit.setReadOnly(True)
        font = QFont("Monospace", 10)
        font.setFixedPitch(True)
        config_text_edit.setFont(font)

        # Load and display config.json
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_content = f.read()
                config_text_edit.setPlainText(config_content)
            else:
                config_text_edit.setPlainText(f"Configuration file not found:\n{config_file}")
        except Exception as e:
            config_text_edit.setPlainText(f"Error reading configuration file:\n{str(e)}")

        config_layout.addWidget(config_text_edit)
        config_tab.setLayout(config_layout)
        tab_widget.addTab(config_tab, "config.json")

        # Tab 2: preferences.json
        prefs_tab = QWidget()
        prefs_layout = QVBoxLayout()

        # Label showing full path
        prefs_path_label = QLabel(f"<b>File:</b> {preferences_file}")
        prefs_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        prefs_path_label.setWordWrap(True)
        prefs_layout.addWidget(prefs_path_label)

        # Text editor for preferences.json
        prefs_text_edit = QTextEdit()
        prefs_text_edit.setReadOnly(True)
        prefs_text_edit.setFont(font)

        # Load and display preferences.json
        try:
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r') as f:
                    prefs_content = f.read()
                prefs_text_edit.setPlainText(prefs_content)
            else:
                prefs_text_edit.setPlainText(f"Preferences file not found:\n{preferences_file}")
        except Exception as e:
            prefs_text_edit.setPlainText(f"Error reading preferences file:\n{str(e)}")

        prefs_layout.addWidget(prefs_text_edit)
        prefs_tab.setLayout(prefs_layout)
        tab_widget.addTab(prefs_tab, "preferences.json")

        layout.addWidget(tab_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
