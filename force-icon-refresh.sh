#!/bin/bash
#
# Force Icon Cache Refresh Script for SysMon
# Aggressively clears all possible icon caches
#

echo "🔄 FORCING ICON CACHE REFRESH..."

# Clear all known icon cache locations
echo "Clearing GTK caches..."
rm -rf ~/.cache/gtk-3.0/ 2>/dev/null || true
rm -rf ~/.cache/icons/ 2>/dev/null || true

echo "Clearing Qt caches..."
rm -rf ~/.cache/qt-* 2>/dev/null || true

echo "Clearing XDG caches..."
rm -rf ~/.cache/menus 2>/dev/null || true
rm -rf ~/.cache/desktop-menu 2>/dev/null || true

# Clear any theme caches
echo "Clearing theme caches..."
rm -rf ~/.themes/*/icon-cache 2>/dev/null || true
rm -rf ~/.local/share/icons/*/ 2>/dev/null || true

# Force update desktop database
echo "Updating desktop database..."
update-desktop-database ~/.local/share/applications/

# Force update GTK icon cache
echo "Updating GTK icon cache..."
gtk-update-icon-cache -f ~/.local/share/icons/ 2>/dev/null || true
gtk-update-icon-cache -f /usr/share/icons/ 2>/dev/null || true

# Force update XDG icon resources
echo "Updating XDG resources..."
xdg-icon-resource forceupdate 2>/dev/null || true

# Touch desktop file to trigger refresh
echo "Triggering desktop refresh..."
touch ~/.local/share/applications/sysmon.desktop

# Final update
echo "Final desktop database update..."
update-desktop-database ~/.local/share/applications/

echo "✅ ICON CACHE REFRESH COMPLETE!"
echo ""
echo "🔄 RESTART YOUR DESKTOP ENVIRONMENT TO SEE CHANGES:"
echo "   - Log out and log back in (most reliable)"
echo "   - Or restart your desktop session"
echo "   - Or reboot the system"