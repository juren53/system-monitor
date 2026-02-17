#!/bin/bash
# SysMon System Package Installation Script
# For Ubuntu/Debian systems with externally-managed Python environments

echo "Installing SysMon dependencies using system package manager..."

# Update package list
echo "Updating package list..."
sudo apt update

# Install core Python packages
echo "Installing core dependencies..."
sudo apt install -y \
    python3-pyqt5 \
    python3-pyqtgraph \
    python3-psutil \
    python3-matplotlib \
    python3-numpy \
    python3-requests

# Install optional but recommended packages
echo "Installing optional dependencies..."
sudo apt install -y \
    python3-pil \
    python3-setuptools

# Install development tools (optional)
echo "Installing development tools..."
sudo apt install -y \
    python3-venv \
    python3-pip \
    python3-pytest

# Install system integration packages
echo "Installing system integration packages..."
sudo apt install -y \
    python3-xdg \
    python3-gi \
    gir1.2-gtk-3.0

echo "Installation complete!"
echo ""
echo "You can now run SysMon with:"
echo "  python3 src/sysmon.py"
echo ""
echo "For the legacy matplotlib version:"
echo "  python3 src/sysmon"