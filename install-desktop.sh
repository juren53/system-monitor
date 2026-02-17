#!/bin/bash
#
# SysMon Desktop Integration Installer
# Sets up desktop file and icons for user-level installation
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$PROJECT_DIR/sysmon.desktop"
LAUNCHER_SCRIPT="$PROJECT_DIR/sysmon.sh"
ICON_FILE="$PROJECT_DIR/icons/ICON_SysMon.png"

# Installation paths
USER_APPS_DIR="$HOME/.local/share/applications"
USER_ICONS_DIR="$HOME/.local/share/icons/hicolor"
USER_AUTOSTART_DIR="$HOME/.config/autostart"

# Logging function
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if project directory is valid
check_project_structure() {
    log "Checking project structure..."
    
    if [[ ! -f "$DESKTOP_FILE" ]]; then
        error "Desktop file not found: $DESKTOP_FILE"
    fi
    
    if [[ ! -f "$LAUNCHER_SCRIPT" ]]; then
        error "Launcher script not found: $LAUNCHER_SCRIPT"
    fi
    
    if [[ ! -f "$ICON_FILE" ]]; then
        error "Icon file not found: $ICON_FILE"
    fi
    
    # Check if launcher script is executable
    if [[ ! -x "$LAUNCHER_SCRIPT" ]]; then
        warn "Making launcher script executable..."
        chmod +x "$LAUNCHER_SCRIPT"
    fi
}

# Create necessary directories
create_directories() {
    log "Creating user directories..."
    
    mkdir -p "$USER_APPS_DIR"
    mkdir -p "$USER_ICONS_DIR"/{16x16,32x32,48x48,64x64,128x128,256x256,512x512}/apps
    mkdir -p "$USER_AUTOSTART_DIR"
}

# Install desktop file
install_desktop_file() {
    log "Installing desktop file..."
    
    # Create a temporary version with correct absolute paths
    TEMP_DESKTOP="/tmp/sysmon-$(date +%s).desktop"
    
    sed "s|/home/juren/Projects/system-monitor|$PROJECT_DIR|g" "$DESKTOP_FILE" > "$TEMP_DESKTOP"
    
    # Validate the desktop file
    if command -v desktop-file-validate >/dev/null 2>&1; then
        if ! desktop-file-validate "$TEMP_DESKTOP"; then
            error "Desktop file validation failed"
        fi
    fi
    
    # Install to user applications directory
    cp "$TEMP_DESKTOP" "$USER_APPS_DIR/sysmon.desktop"
    rm "$TEMP_DESKTOP"
    
    # Set proper permissions
    chmod 644 "$USER_APPS_DIR/sysmon.desktop"
    
    log "Desktop file installed to: $USER_APPS_DIR/sysmon.desktop"
}

# Install icons
install_icons() {
    log "Installing icons..."
    
    # Icon sizes to install
    SIZES=(16 32 48 64 128 256 512)
    
    for size in "${SIZES[@]}"; do
        ICON_DIR="$USER_ICONS_DIR/${size}x${size}/apps"
        TARGET_ICON="$ICON_DIR/sysmon.png"
        
        # Copy the icon (using the same file for all sizes)
        cp "$ICON_FILE" "$TARGET_ICON"
        chmod 644 "$TARGET_ICON"
        
        log "Installed ${size}x${size} icon: $TARGET_ICON"
    done
}

# Update icon cache
update_icon_cache() {
    log "Updating icon cache..."
    
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$USER_ICONS_DIR" 2>/dev/null || true
        log "Icon cache updated"
    else
        warn "gtk-update-icon-cache not found, skipping cache update"
    fi
}

# Create autostart entry (optional)
create_autostart() {
    if [[ "$1" == "--autostart" ]]; then
        log "Creating autostart entry..."
        
        cat > "$USER_AUTOSTART_DIR/sysmon.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SysMon
Comment=Real-time system monitoring with PyQtGraph
Exec=$LAUNCHER_SCRIPT
Icon=$ICON_FILE
Terminal=false
StartupNotify=true
Categories=System;Monitor;
EOF
        
        chmod 644 "$USER_AUTOSTART_DIR/sysmon.desktop"
        log "Autostart entry created: $USER_AUTOSTART_DIR/sysmon.desktop"
    fi
}

# Test installation
test_installation() {
    log "Testing installation..."
    
    # Test desktop file
    if command -v gtk-launch >/dev/null 2>&1; then
        if gtk-launch sysmon >/dev/null 2>&1 & then
            log "Desktop file test: SUCCESS"
            sleep 1
        else
            warn "Desktop file test: FAILED (but installation may still work)"
        fi
    fi
    
    # Check icon visibility
    if [[ -f "$USER_ICONS_DIR/256x256/apps/sysmon.png" ]]; then
        log "Icon installation: SUCCESS"
    else
        error "Icon installation: FAILED"
    fi
}

# Show usage information
show_usage() {
    cat << EOF

${BLUE}SysMon Desktop Integration - Installation Complete!${NC}

Desktop File: $USER_APPS_DIR/sysmon.desktop
Icons: $USER_ICONS_DIR/*x*/apps/sysmon.png

${GREEN}To launch SysMon:${NC}
• From application menu (System category)
• From terminal: gtk-launch sysmon
• From desktop file: $USER_APPS_DIR/sysmon.desktop

${GREEN}Quick Actions:${NC}
Right-click the SysMon menu entry to see quick actions:
• Show CPU Focus
• Show Network Focus  
• Minimal Mode
• Settings

${GREEN}To uninstall:${NC}
Run: $PROJECT_DIR/install-desktop.sh --uninstall

EOF
}

# Main installation function
main() {
    echo -e "${BLUE}SysMon Desktop Integration Installer${NC}"
    echo "============================================"
    
    check_project_structure
    create_directories
    install_desktop_file
    install_icons
    update_icon_cache
    create_autostart "$1"
    test_installation
    show_usage
}

# Uninstall function
uninstall() {
    log "Uninstalling SysMon desktop integration..."
    
    # Remove desktop file
    if [[ -f "$USER_APPS_DIR/sysmon.desktop" ]]; then
        rm "$USER_APPS_DIR/sysmon.desktop"
        log "Removed desktop file: $USER_APPS_DIR/sysmon.desktop"
    fi
    
    # Remove icons
    SIZES=(16 32 48 64 128 256 512)
    for size in "${SIZES[@]}"; do
        ICON_PATH="$USER_ICONS_DIR/${size}x${size}/apps/sysmon.png"
        if [[ -f "$ICON_PATH" ]]; then
            rm "$ICON_PATH"
            log "Removed ${size}x${size} icon: $ICON_PATH"
        fi
    done
    
    # Remove autostart entry
    if [[ -f "$USER_AUTOSTART_DIR/sysmon.desktop" ]]; then
        rm "$USER_AUTOSTART_DIR/sysmon.desktop"
        log "Removed autostart entry: $USER_AUTOSTART_DIR/sysmon.desktop"
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$USER_ICONS_DIR" 2>/dev/null || true
        log "Updated icon cache"
    fi
    
    log "Uninstallation complete!"
}

# Check command line arguments
case "${1:-}" in
    --uninstall)
        uninstall
        exit 0
        ;;
    --help|-h)
        echo "Usage: $0 [--autostart] [--uninstall] [--help]"
        echo "  --autostart    Create autostart entry"
        echo "  --uninstall    Remove desktop integration"
        echo "  --help         Show this help"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        if [[ "$1" == "--autostart" ]]; then
            main "$1"
        else
            error "Unknown option: $1. Use --help for usage information."
        fi
        ;;
esac