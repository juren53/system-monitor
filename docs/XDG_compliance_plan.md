# XDG Compliance Plan for SysMon

## Overview
This document outlines the plan to make SysMon compliant with the XDG Base Directory Specification, which defines standard locations for user data files, configuration files, cache files, and state files on Linux systems.

## Current State Analysis

### Current File Storage
- **Configuration**: `~/.sysmon_config.json` (non-XDG compliant)
- **Cache**: None currently stored
- **Data**: None currently stored  
- **State**: None currently stored

### Current Dependencies
- matplotlib
- psutil
- PyQt5
- numpy
- argparse
- json
- os
- time
- atexit

## XDG Base Directory Specification Requirements

### Standard Directories
- **Configuration**: `$XDG_CONFIG_HOME` (default: `~/.config`)
- **Data**: `$XDG_DATA_HOME` (default: `~/.local/share`)
- **Cache**: `$XDG_CACHE_HOME` (default: `~/.cache`)
- **State**: `$XDG_STATE_HOME` (default: `~/.local/state`)

### File Type Classifications
- **Configuration files**: User preferences, settings, window geometry
- **Data files**: Application data that should persist between restarts
- **Cache files**: Non-essential data that can be safely deleted
- **State files**: Application state that should persist but isn't important enough for data directory

## Implementation Options

### Option A: Use External Library (Recommended)
**Library**: `platformdirs` or `xdg-base-dirs`

**Pros**:
- Well-tested and maintained
- Handles edge cases and cross-platform compatibility
- Follows best practices
- Minimal code changes required

**Cons**:
- Adds external dependency
- Slightly larger installation footprint

### Option B: Implement XDG Logic Directly

**Pros**:
- No additional dependencies
- Full control over implementation
- Smaller installation size

**Cons**:
- More maintenance overhead
- Need to handle edge cases manually
- Potential for implementation bugs

## Proposed Directory Structure

```
$XDG_CONFIG_HOME/sysmon/
├── config.json          # Main configuration (window geometry, settings)
└── preferences.json     # User preferences (if expanded in future)

$XDG_CACHE_HOME/sysmon/
└── (future cache files - e.g., graph data snapshots, temporary calculations)

$XDG_STATE_HOME/sysmon/
└── (future state files - e.g., last session state, undo history)
```

## Migration Strategy

### Phase 1: Detection and Migration
1. **Check for legacy configuration**: Look for `~/.sysmon_config.json`
2. **Create XDG directories**: Ensure target directories exist with proper permissions (0700)
3. **Migrate existing config**: Copy content from old location to new XDG-compliant location
4. **Notify user**: Inform about migration (optional, based on preference)
5. **Backup old file**: Rename old file to `~/.sysmon_config.json.bak` before removal

### Phase 2: Backward Compatibility
- Continue checking old location for a transition period
- Provide warning if old file is found but new location exists
- Eventually remove backward compatibility after sufficient transition time

## Implementation Steps

### Step 1: Add XDG Directory Detection
```python
def get_xdg_config_dir():
    """Get XDG config directory, fallback to ~/.config if not set"""
    return os.environ.get('XDG_CONFIG_HOME', 
                         os.path.join(os.path.expanduser('~'), '.config'))

def get_xdg_cache_dir():
    """Get XDG cache directory, fallback to ~/.cache if not set"""
    return os.environ.get('XDG_CACHE_HOME', 
                         os.path.join(os.path.expanduser('~'), '.cache'))

def get_xdg_state_dir():
    """Get XDG state directory, fallback to ~/.local/state if not set"""
    return os.environ.get('XDG_STATE_HOME', 
                         os.path.join(os.path.expanduser('~'), '.local/state'))
```

### Step 2: Update Configuration File Handling
- Modify `RealtimeMonitor.__init__()` to use XDG-compliant path
- Update `config_file` attribute to point to new location
- Ensure directory exists before attempting to read/write

### Step 3: Update Geometry Save/Load Methods
- Modify `load_window_geometry()` to handle new path
- Modify `save_window_geometry()` to handle new path
- Add error handling for directory creation

### Step 4: Add Migration Logic
```python
def migrate_legacy_config():
    """Migrate configuration from ~/.sysmon_config.json to XDG location"""
    legacy_path = os.path.join(os.path.expanduser('~'), '.sysmon_config.json')
    new_path = get_xdg_config_path()
    
    if os.path.exists(legacy_path) and not os.path.exists(new_path):
        try:
            # Ensure target directory exists
            os.makedirs(os.path.dirname(new_path), mode=0o700, exist_ok=True)
            
            # Copy configuration
            import shutil
            shutil.copy2(legacy_path, new_path)
            
            # Backup old file
            shutil.move(legacy_path, legacy_path + '.bak')
            
            print(f"Migrated configuration to: {new_path}")
            return True
        except Exception as e:
            print(f"Failed to migrate configuration: {e}")
            return False
    return False
```

### Step 5: Update Documentation
- Update README.md with new configuration location
- Add XDG compliance note to features
- Document migration process for users

## File Classification Decisions

### Current Files
- **Window geometry configuration**: `$XDG_CONFIG_HOME/sysmon/config.json`
  - Rationale: User preference that should persist between sessions

### Potential Future Files
- **Graph data cache**: `$XDG_CACHE_HOME/sysmon/graph_cache/`
  - Rationale: Temporary performance optimization data
- **Process history**: `$XDG_STATE_HOME/sysmon/process_history.json`
  - Rationale: Session state that's not important enough for data directory
- **User themes/customizations**: `$XDG_CONFIG_HOME/sysmon/themes/`
  - Rationale: User configuration

## Cross-Platform Considerations

### Windows Support
- Use `platformdirs` library for automatic Windows path handling
- Fallback to `%APPDATA%` for config, `%LOCALAPPDATA%` for cache

### macOS Support  
- Use `platformdirs` library for automatic macOS path handling
- Fallback to `~/Library/Application Support/` for config, `~/Library/Caches/` for cache

## Testing Strategy

### Unit Tests
- Test XDG directory detection with and without environment variables
- Test migration logic with various scenarios
- Test configuration save/load with new paths

### Integration Tests
- Test full application lifecycle with XDG paths
- Test migration from legacy to new paths
- Test cross-platform path handling

## Rollout Plan

### Version 0.2.0 (XDG Compliance Release)
1. Implement XDG directory detection
2. Add migration logic
3. Update configuration handling
4. Update documentation
5. Add backward compatibility

### Version 0.3.0 (Cleanup)
1. Remove backward compatibility for legacy paths
2. Add additional XDG-compliant features (cache, state)
3. Optimize directory usage

## Benefits of XDG Compliance

1. **Standardization**: Follows Linux desktop standards
2. **User Experience**: Predictable file locations for users
3. **Backup Friendly**: Easier for users to backup configurations
4. **Clean Home Directory**: Reduces dotfile clutter in user home
5. **System Integration**: Better integration with system tools and backup solutions

## Risks and Mitigations

### Risk: Breaking existing installations
**Mitigation**: Automatic migration and backward compatibility

### Risk: Permission issues
**Mitigation**: Proper directory creation with 0700 permissions

### Risk: Cross-platform compatibility
**Mitigation**: Use `platformdirs` library or platform-specific fallbacks

## Decision Points

1. **Library vs Direct Implementation**: Choose between `platformdirs` vs custom implementation
2. **Migration Strategy**: Automatic vs user-confirmed migration
3. **Backward Compatibility Duration**: How long to support legacy paths
4. **Additional Features**: Whether to implement cache and state directories immediately

## Timeline Estimate

- **Week 1**: Implementation of XDG detection and config handling
- **Week 2**: Migration logic and testing
- **Week 3**: Documentation updates and cross-platform testing
- **Week 4**: Release preparation and final testing

Total estimated effort: 3-4 weeks for full implementation and testing.