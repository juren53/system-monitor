"""
SysMon Configuration
XDG-compliant config paths, config file load/save, and migration utilities.
"""

import os
import json
import platform


def get_xdg_config_dir():
    """Get XDG-compliant configuration directory"""
    if platform.system() == "Windows":
        # Windows: Use AppData instead of XDG
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'sysmon')
    else:
        # Linux/macOS: Use XDG standard
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            return os.path.join(xdg_config, 'sysmon')
        else:
            return os.path.join(os.path.expanduser('~'), '.config', 'sysmon')


def ensure_config_directory(config_dir):
    """Ensure configuration directory exists"""
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)


def migrate_old_config(old_config_file, new_config_dir):
    """Migrate old config file to new XDG location"""
    if os.path.exists(old_config_file) and not os.path.exists(os.path.join(new_config_dir, 'config.json')):
        try:
            # Read old config
            with open(old_config_file, 'r') as f:
                old_data = json.load(f)

            # Write to new location
            with open(os.path.join(new_config_dir, 'config.json'), 'w') as f:
                json.dump(old_data, f, indent=2)

            # Remove old file
            os.remove(old_config_file)
            return True
        except Exception as e:
            print(f"Config migration failed: {e}")
            return False
    return False


def get_config_file_path(config_dir):
    """Get main config file path"""
    return os.path.join(config_dir, 'config.json')


def get_preferences_file_path(config_dir):
    """Get preferences file path"""
    return os.path.join(config_dir, 'preferences.json')
