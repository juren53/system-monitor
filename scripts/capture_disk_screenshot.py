#!/usr/bin/env python3
"""Capture Disk I/O dialog screenshot"""

import sys
import os
import subprocess
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def main():
    from sysmon import RealTimeDiskDialog

    app = QApplication(sys.argv)

    print("Opening Disk I/O dialog...")
    dialog = RealTimeDiskDialog()
    dialog.refresh_data()
    dialog.show()

    def capture():
        time.sleep(0.5)
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "Disk I/O" in line:
                    window_id = line.split()[0]
                    print(f"Found window: {window_id}")
                    subprocess.run(['import', '-window', window_id, 'images/dialog-disk-realtime.png'])
                    print("✓ Screenshot saved: images/dialog-disk-realtime.png")
                    break
        except Exception as e:
            print(f"Error: {e}")

        dialog.close()
        QApplication.quit()

    QTimer.singleShot(2500, capture)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
