"""
SysMon Platform Utilities
Stderr filtering, single-instance management, and application icon setup.
"""

import sys
import os
import platform
import threading
import time

from PyQt5.QtCore import QSharedMemory, QSystemSemaphore
from PyQt5.QtWidgets import QMessageBox

from .constants import VERSION


def filter_stderr_gdkpixbuf():
    """Filter out harmless GdkPixbuf critical warnings on Linux"""

    def stderr_filter_thread():
        """Background thread to filter stderr output"""
        import select

        # Create pipe for stderr
        r, w = os.pipe()

        # Redirect stderr to our pipe
        old_stderr = sys.stderr.fileno()
        os.dup2(w, old_stderr)
        os.close(w)

        while True:
            try:
                # Wait for data on stderr
                ready, _, _ = select.select([r], [], [], 0.1)
                if ready:
                    data = os.read(r, 8192).decode('utf-8', errors='ignore')
                    if data:
                        lines = data.split('\n')
                        for line in lines:
                            # Filter out GdkPixbuf critical warnings
                            if ('GdkPixbuf-CRITICAL' in line and
                                ('gdk_pixbuf_get_' in line or
                                 'GDK_IS_PIXBUF' in line)):
                                # Skip these harmless warnings
                                continue
                            elif line.strip():
                                # Print other error messages
                                print(line, file=sys.stderr, flush=True)
            except (OSError, KeyboardInterrupt):
                break
            except Exception:
                break

    # Start filter thread only on Linux systems
    if platform.system() == "Linux":
        try:
            filter_thread = threading.Thread(target=stderr_filter_thread, daemon=True)
            filter_thread.start()
        except Exception:
            # If filtering fails, continue without it
            pass


# Single instance management
shared_memory = None
system_semaphore = None


def check_single_instance():
    """Check if SysMon is already running using Qt native mechanisms"""
    global shared_memory, system_semaphore

    # Use version-specific keys to allow different versions to coexist
    instance_key = f"sysmon-v{VERSION}-instance"
    semaphore_key = f"sysmon-v{VERSION}-semaphore"

    # Create system semaphore for thread safety
    if system_semaphore is None:
        system_semaphore = QSystemSemaphore(semaphore_key, 1)

    system_semaphore.acquire()  # Raise semaphore to prevent race conditions

    # On Linux/Unix, clean up shared memory from abnormal terminations
    if sys.platform != 'win32':
        cleanup_shared_mem = QSharedMemory(instance_key)
        if cleanup_shared_mem.attach():
            cleanup_shared_mem.detach()

    # Try to create shared memory
    if shared_memory is None:
        shared_memory = QSharedMemory(instance_key)

    if shared_memory.attach():
        # Shared memory exists - application is already running
        system_semaphore.release()
        return False
    else:
        # Create shared memory for this instance
        if not shared_memory.create(1):
            # Failed to create - another instance started simultaneously
            system_semaphore.release()
            return False

        # Successfully created shared memory
        system_semaphore.release()
        return True


def cleanup_single_instance():
    """Clean up single instance resources"""
    global shared_memory, system_semaphore

    try:
        if shared_memory:
            if shared_memory.isAttached():
                shared_memory.detach()
    except Exception:
        pass  # Ignore cleanup errors

    try:
        if system_semaphore:
            system_semaphore.release()
    except Exception:
        pass  # Ignore cleanup errors


def show_instance_already_running(app):
    """Show message box when another instance is detected"""
    # Validate app parameter
    if app is None:
        print("Error: Invalid QApplication instance")
        return

    # Process pending events to ensure app is properly initialized
    app.processEvents()

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle('SysMon Already Running')
    msg_box.setText('SysMon is already running on this system.\n\n'
                   'Only one instance of SysMon can run at same time.\n\n'
                   'If you believe this is an error, please check your running processes.')
    msg_box.setStandardButtons(QMessageBox.Ok)

    # Show dialog and process events manually since main event loop isn't running
    msg_box.show()

    # Process events until dialog is closed
    while msg_box.isVisible():
        app.processEvents()
        time.sleep(0.01)  # Small delay to prevent CPU spinning


def set_application_icon(app):
    """Set application icon via IconLoader"""
    from icon_loader import icons
    app.setWindowIcon(icons.app_icon())
