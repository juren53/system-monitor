#!/bin/bash
#
# SysMon Desktop Launcher
# Ensures proper environment and paths for desktop integration
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add script directory to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Change to script directory to ensure relative paths work
cd "$SCRIPT_DIR"

# Launch the application
exec python3 "$SCRIPT_DIR/src/sysmon.py" "$@"