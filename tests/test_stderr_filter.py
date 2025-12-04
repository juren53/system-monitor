#!/usr/bin/env python3
"""Test script to verify that only GdkPixbuf-CRITICAL warnings are filtered."""

import os
import sys
import threading

# Copy the filter function from sysmon-07.py
def _filter_stderr():
    """Filter stderr to suppress ONLY GdkPixbuf-CRITICAL warnings."""
    if sys.stderr.isatty():
        read_fd, write_fd = os.pipe()
        stderr_fd = sys.stderr.fileno()
        stderr_copy = os.dup(stderr_fd)
        os.dup2(write_fd, stderr_fd)
        os.close(write_fd)
        
        def filter_thread():
            with os.fdopen(read_fd, 'rb') as pipe:
                with os.fdopen(stderr_copy, 'wb') as original_stderr:
                    for line in pipe:
                        # Only filter GdkPixbuf-CRITICAL - allow ALL other errors/warnings
                        if b'GdkPixbuf-CRITICAL' not in line:
                            original_stderr.write(line)
                            original_stderr.flush()
        
        thread = threading.Thread(target=filter_thread, daemon=True)
        thread.start()

# Activate the filter
_filter_stderr()

# Small delay to ensure filter thread is ready
import time
time.sleep(0.1)

# Test various stderr messages
print("Testing stderr filtering...\n", file=sys.stderr)

# This should appear (normal error)
print("ERROR: This is a normal error message", file=sys.stderr)

# This should appear (Python warning)
print("Warning: This is a warning message", file=sys.stderr)

# This should NOT appear (GdkPixbuf warning)
print("(python3:12345): GdkPixbuf-CRITICAL **: 00:00:00.000: gdk_pixbuf_get_width: assertion 'GDK_IS_PIXBUF (pixbuf)' failed", file=sys.stderr)

# This should appear (another normal message)
print("INFO: This is an info message", file=sys.stderr)

# This should appear (exception-like message)
print("Traceback (most recent call last):", file=sys.stderr)
print("  File 'test.py', line 10, in main", file=sys.stderr)
print("ValueError: Something went wrong", file=sys.stderr)

# This should NOT appear (another GdkPixbuf warning)
print("GdkPixbuf-CRITICAL: Another pixbuf error", file=sys.stderr)

# This should appear (normal message)
print("\nAll done! If filtering works, you should NOT see GdkPixbuf lines above.", file=sys.stderr)

# Wait a moment for filter to process
time.sleep(0.2)
