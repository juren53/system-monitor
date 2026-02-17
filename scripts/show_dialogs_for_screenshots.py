#!/usr/bin/env python3
"""Show each dialog one at a time for manual screenshot capture"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication, QMessageBox
from sysmon import RealTimeProcessDialog, RealTimeDiskDialog, RealTimeNetworkDialog

def show_dialog_with_prompt(dialog_name, dialog_class):
    """Show a dialog and wait for user to take screenshot"""
    print(f"\n{'='*70}")
    print(f"Showing {dialog_name} Dialog")
    print(f"{'='*70}")
    print("Please take a screenshot now...")
    print(f"Save as: images/dialog-{dialog_name.lower().replace(' ', '-')}-realtime.png")
    print()

    dialog = dialog_class()
    dialog.refresh_data()
    dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    print("\n" + "="*70)
    print("DIALOG SCREENSHOT HELPER")
    print("="*70)
    print("\nThis script will open each dialog one at a time.")
    print("Please take a screenshot of each dialog when it appears.")
    print("\nRecommended filenames:")
    print("  - CPU Dialog: images/dialog-cpu-realtime.png")
    print("  - Disk I/O Dialog: images/dialog-disk-realtime.png")
    print("  - Network Dialog: images/dialog-network-realtime.png")
    print("\nPress OK on each dialog after taking the screenshot.")
    print("="*70)

    input("\nPress Enter to start...")

    # Show CPU Dialog
    show_dialog_with_prompt("CPU", RealTimeProcessDialog)

    # Show Disk I/O Dialog
    show_dialog_with_prompt("Disk I/O", RealTimeDiskDialog)

    # Show Network Dialog
    show_dialog_with_prompt("Network", RealTimeNetworkDialog)

    print("\n" + "="*70)
    print("All dialogs shown. Screenshots complete!")
    print("="*70)
