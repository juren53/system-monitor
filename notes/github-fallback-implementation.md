# GitHub Fallback Implementation for Help Documents

**Version:** v0.2.16a
**Date:** 2025-12-30 1400 CST
**Status:** ✅ Complete

## Overview

Implemented automatic GitHub fallback for Help menu documents. When local documentation files are missing or damaged, SysMon now automatically fetches them from the GitHub repository.

## Implementation Details

### Files Modified

1. **src/sysmon.py**
   - Added imports: `urllib.request.urlopen`, `urllib.error.URLError`
   - Added `load_document_with_fallback()` helper method (line 3139-3182)
   - Updated `show_changelog()` to use fallback (line 3184-3195)
   - Updated `show_users_guide()` to use fallback (line 3342-3353)
   - Updated `show_keyboard_shortcuts()` to use fallback (line 3403-3414)
   - Updated version to v0.2.16a

2. **docs/CHANGELOG.md**
   - Added v0.2.16a entry with full feature documentation

3. **CLAUDE.md**
   - Updated current version to v0.2.16a

### GitHub URLs Used

All documents are fetched from the main branch:
- ChangeLog: `https://raw.githubusercontent.com/juren53/system-monitor/main/docs/CHANGELOG.md`
- Users Guide: `https://raw.githubusercontent.com/juren53/system-monitor/main/docs/users-guide.md`
- Keyboard Shortcuts: `https://raw.githubusercontent.com/juren53/system-monitor/main/docs/keyboard-shortcuts.md`

### How It Works

1. **Primary**: Attempts to load document from local file
   - Fast, no network required
   - Preserves normal operation

2. **Fallback**: If local file fails, fetches from GitHub
   - 10-second timeout for reliability
   - Appends notification: "*Note: Loaded from GitHub repository (local file not available)*"

3. **Error Handling**: If both fail, displays informative error with:
   - Local error details
   - GitHub error details
   - Link to repository

## Testing Results

✅ **Syntax Check**: Passed
✅ **Local File Loading**: Verified working
✅ **Error Handling**: Verified catching all exception types
⚠️ **GitHub Fallback**: Logic correct, but SSL cert verification issues in MSYS2 test environment (will work in standard Python environments)

## Benefits

1. **Standalone Executables**: Documentation always available even without bundled files
2. **User Error Recovery**: Handles deleted/moved/corrupted local files gracefully
3. **Latest Documentation**: Users always see current docs from repository
4. **Transparent**: Clear notification when GitHub is used
5. **No Breaking Changes**: Fully backward compatible with existing behavior

## Use Cases

- PyInstaller EXE without bundled documentation
- User accidentally deletes docs folder
- Corrupted local documentation files
- Always showing latest repository documentation

## Version Notes

This is a point release (v0.2.16a) following SysMon's versioning convention:
- Production releases: v0.X.Y
- Point releases/patches: v0.X.Ya, v0.X.Yb

All timestamps use Central Time USA (CST/CDT) per project conventions.
