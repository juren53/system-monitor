"""
SysMon Constants
Centralized version info, build info, and application defaults.
"""

import sys
import platform
import datetime

# Version Information
VERSION = "0.5.9b"
RELEASE_DATE = "2026-03-05"
RELEASE_TIME = "0830 CST"
FULL_VERSION = f"v{VERSION} {RELEASE_DATE} {RELEASE_TIME}"

# Build Information
BUILD_DATE = "2026-03-05"
BUILD_TIME = "0830 CST"
BUILD_INFO = f"{BUILD_DATE} {BUILD_TIME}"

# Runtime Information
APPLICATION_START_TIME = datetime.datetime.now()
PYTHON_VERSION = sys.version.split()[0]
PLATFORM_INFO = platform.platform()
