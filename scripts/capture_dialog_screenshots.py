#!/usr/bin/env python3
"""Capture screenshots of all three real-time dialogs"""

import sys
import os
import subprocess
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def capture_screenshot(window_title, output_file):
    """Capture screenshot of a specific window by title"""
    time.sleep(1)  # Wait for window to be fully drawn

    # Use wmctrl to find window ID
    try:
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if window_title in line:
                window_id = line.split()[0]
                print(f"Found window: {window_id} - {window_title}")

                # Use import to capture the window
                subprocess.run(['import', '-window', window_id, output_file])
                print(f"✓ Screenshot saved: {output_file}")
                return True
    except Exception as e:
        print(f"Error capturing screenshot: {e}")

    return False

def capture_cpu_dialog():
    """Capture CPU dialog screenshot"""
    print("\n" + "="*70)
    print("Capturing CPU Dialog Screenshot")
    print("="*70)

    from sysmon import RealTimeProcessDialog

    dialog = RealTimeProcessDialog()
    dialog.setWindowTitle("Real-Time Top 10 CPU Processes")  # Ensure consistent title

    # Trigger data collection
    dialog.refresh_data()

    # Show the dialog (non-modal)
    dialog.show()

    # Wait for data to populate
    QTimer.singleShot(2500, lambda: capture_and_close('cpu', dialog))

def capture_and_close(dialog_type, dialog):
    """Capture screenshot and close dialog"""
    output_file = f"images/dialog-cpu-realtime.png"

    if dialog_type == 'cpu':
        output_file = "images/dialog-cpu-realtime.png"
        window_title = "Real-Time Top 10 CPU Processes"
    elif dialog_type == 'disk':
        output_file = "images/dialog-disk-realtime.png"
        window_title = "Real-Time Top 10 Disk I/O Processes"
    elif dialog_type == 'network':
        output_file = "images/dialog-network-realtime.png"
        window_title = "Real-Time Top 10 Network Processes"

    # Capture screenshot
    success = capture_screenshot(window_title, output_file)

    # Close dialog
    dialog.close()

    if success:
        # Move to next dialog
        if dialog_type == 'cpu':
            QTimer.singleShot(500, capture_disk_dialog)
        elif dialog_type == 'disk':
            QTimer.singleShot(500, capture_network_dialog)
        elif dialog_type == 'network':
            QTimer.singleShot(500, QApplication.quit)
    else:
        print("⚠ Screenshot capture failed")
        QTimer.singleShot(500, QApplication.quit)

def capture_disk_dialog():
    """Capture Disk I/O dialog screenshot"""
    print("\n" + "="*70)
    print("Capturing Disk I/O Dialog Screenshot")
    print("="*70)

    from sysmon import RealTimeDiskDialog

    dialog = RealTimeDiskDialog()
    dialog.setWindowTitle("Real-Time Top 10 Disk I/O Processes")

    # Trigger data collection
    dialog.refresh_data()

    # Show the dialog
    dialog.show()

    # Wait for data to populate
    QTimer.singleShot(2500, lambda: capture_and_close('disk', dialog))

def capture_network_dialog():
    """Capture Network dialog screenshot"""
    print("\n" + "="*70)
    print("Capturing Network Dialog Screenshot")
    print("="*70)

    from sysmon import RealTimeNetworkDialog

    dialog = RealTimeNetworkDialog()
    dialog.setWindowTitle("Real-Time Top 10 Network Processes")

    # Trigger data collection
    dialog.refresh_data()

    # Show the dialog
    dialog.show()

    # Wait for data to populate
    QTimer.singleShot(2500, lambda: capture_and_close('network', dialog))

if __name__ == '__main__':
    # Check if wmctrl is available
    try:
        subprocess.run(['wmctrl', '-h'], capture_output=True)
    except FileNotFoundError:
        print("Error: wmctrl not found. Please install: sudo apt install wmctrl")
        sys.exit(1)

    app = QApplication(sys.argv)

    print("\n" + "="*70)
    print("DIALOG SCREENSHOT CAPTURE")
    print("Automatically capturing screenshots of all three dialogs")
    print("="*70)

    # Start with CPU dialog
    QTimer.singleShot(500, capture_cpu_dialog)

    sys.exit(app.exec_())
