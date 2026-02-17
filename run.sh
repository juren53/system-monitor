#!/bin/bash
# run.sh - Set up venv and run SysMon

VENV_DIR=".venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "Error: Failed to create venv. Install python3-venv:"
        echo "  pkexec apt install python3-venv"
        exit 1
    fi
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies if needed (check for pyqtgraph as indicator)
if ! python3 -c "import pyqtgraph" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run SysMon with any passed arguments
python3 src/sysmon.py "$@"
