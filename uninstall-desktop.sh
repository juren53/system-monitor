#!/bin/bash
#
# SysMon Desktop Integration Uninstaller
# Removes desktop file and icons for clean uninstallation
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
USER_APPS_DIR="$HOME/.local/share/applications"
USER_ICONS_DIR="$HOME/.local/share/icons/hicolor"
USER_AUTOSTART_DIR="$HOME/.config/autostart"

# Files to remove
DESKTOP_FILE="$USER_APPS_DIR/sysmon.desktop"
AUTOSTART_FILE="$USER_AUTOSTART_DIR/sysmon.desktop"

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

# Check if installation exists
check_installation() {
    log "Checking for existing SysMon desktop integration..."
    
    local found=false
    
    if [[ -f "$DESKTOP_FILE" ]]; then
        log "Found desktop file: $DESKTOP_FILE"
        found=true
    fi
    
    if [[ -f "$AUTOSTART_FILE" ]]; then
        log "Found autostart file: $AUTOSTART_FILE"
        found=true
    fi
    
    # Check for icons
    local icon_found=false
    for size in 16 32 48 64 128 256 512; do
        if [[ -f "$USER_ICONS_DIR/${size}x${size}/apps/sysmon.png" ]]; then
            if [[ "$icon_found" == false ]]; then
                log "Found SysMon icons"
                icon_found=true
            fi
        fi
    done
    
    if [[ "$found" == false && "$icon_found" == false ]]; then
        warn "No SysMon desktop integration found"
        echo "Nothing to uninstall."
        exit 0
    fi
}

# Remove desktop file
remove_desktop_file() {
    if [[ -f "$DESKTOP_FILE" ]]; then
        rm "$DESKTOP_FILE"
        log "Removed desktop file: $DESKTOP_FILE"
    else
        warn "Desktop file not found: $DESKTOP_FILE"
    fi
}

# Remove autostart file
remove_autostart_file() {
    if [[ -f "$AUTOSTART_FILE" ]]; then
        rm "$AUTOSTART_FILE"
        log "Removed autostart file: $AUTOSTART_FILE"
    else
        warn "Autostart file not found: $AUTOSTART_FILE"
    fi
}

# Remove icons
remove_icons() {
    log "Removing SysMon icons..."
    
    local removed_count=0
    local sizes=(16 32 48 64 128 256 512)
    
    for size in "${sizes[@]}"; do
        local icon_path="$USER_ICONS_DIR/${size}x${size}/apps/sysmon.png"
        if [[ -f "$icon_path" ]]; then
            rm "$icon_path"
            log "Removed ${size}x${size} icon"
            ((removed_count++))
        fi
    done
    
    if [[ $removed_count -eq 0 ]]; then
        warn "No SysMon icons found to remove"
    else
        log "Removed $removed_count icon files"
    fi
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

# Clean up empty directories (optional)
cleanup_directories() {
    log "Cleaning up empty directories..."
    
    # Remove empty icon directories
    for size in 16 32 48 64 128 256 512; do
        local icon_dir="$USER_ICONS_DIR/${size}x${size}/apps"
        if [[ -d "$icon_dir" ]] && [[ -z "$(ls -A "$icon_dir" 2>/dev/null)" ]]; then
            rmdir "$icon_dir" 2>/dev/null || true
            rmdir "$USER_ICONS_DIR/${size}x${size}" 2>/dev/null || true
        fi
    done
    
    # Remove empty apps and autostart directories if possible
    rmdir "$USER_APPS_DIR" 2>/dev/null || true
    rmdir "$USER_AUTOSTART_DIR" 2>/dev/null || true
}

# Show summary
show_summary() {
    cat << EOF

${BLUE}SysMon Desktop Integration - Uninstallation Complete!${NC}

The following has been removed:
• Desktop file from applications menu
• SysMon icons from system
• Autostart entry (if present)

${GREEN}To reinstall:${NC}
Run: /home/juren/Projects/system-monitor/install-desktop.sh

${YELLOW}Note:${NC}
Any running SysMon processes were not stopped.
You may need to manually close SysMon if it's currently running.

EOF
}

# Main uninstallation function
main() {
    echo -e "${BLUE}SysMon Desktop Integration Uninstaller${NC}"
    echo "=============================================="
    
    check_installation
    
    echo
    read -p "Do you want to continue with uninstallation? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Uninstallation cancelled."
        exit 0
    fi
    
    remove_desktop_file
    remove_autostart_file
    remove_icons
    update_icon_cache
    cleanup_directories
    show_summary
}

# Check command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo "  --help    Show this help"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1. Use --help for usage information."
        ;;
esac