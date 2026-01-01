# Plan: GitHub Version Checking for SysMon

### Overview
Add automatic version checking functionality that queries the GitHub repository for new releases and notifies users when updates are available.

### Current State Analysis
- **Existing GitHub Integration**: SysMon already uses `urllib` for fetching documentation from GitHub and `webbrowser` for opening GitHub URLs
- **Threading Pattern**: Uses `QThread + QObject` workers with signal/slot connections for background tasks
- **Version Management**: Version stored in constants (`VERSION = "0.2.18d"`)
- **Error Handling**: Robust fallback patterns for network requests

### Implementation Strategy

#### 1. **GitHub Version Worker Class**
Create `GitHubVersionWorker(QObject)` following existing patterns:
- Query GitHub Releases API: `https://api.github.com/repos/juren53/system-monitor/releases/latest`
- Compare versions using semantic version parsing
- Emit signals: `version_available(latest_version, download_url)` or `error(message)`
- 10-second timeout to prevent hanging

#### 2. **Menu Integration**
Add to Help menu (after existing GitHub actions):
- **Check for Updates** - Manual version check with keyboard shortcut
- **Auto-check on startup** - Configurable preference

#### 3. **Update Notification Dialog**
Create update notification dialog following existing `QDialog` patterns:
- Show current version vs. latest version
- Direct download link to GitHub releases
- Skip this version option
- Remind me later option
- Theme-aware styling

#### 4. **Version Comparison Logic**
- Strip 'v' prefix and compare semantic versions
- Handle pre-release suffixes (a, b, rc)
- Ignore build metadata for comparison
- Only notify if newer version available

#### 5. **Configuration Integration**
Add to preferences.json:
- `auto_check_updates`: boolean (default: false)
- `last_update_check`: timestamp
- `skip_update_versions`: array of versions to ignore
- `update_check_interval_days`: integer (default: 7)

#### 6. **Network Error Handling**
Follow existing fallback patterns:
- Graceful degradation on network failures
- User-friendly error messages
- Retry mechanism for transient failures
- Offline mode detection

### Technical Implementation Details

#### **Key Code Locations**
- **Worker Class**: After `ProcessNetworkWorker` (~line 1525)
- **Menu Setup**: In `init_menu()` Help section (~line 2240)
- **Preferences**: Extend `save_preferences()` and `load_preferences()`
- **Dialog**: After existing dialog classes (~line 1100)

#### **Dependencies**
No new dependencies required - uses existing:
- `urllib.request.urlopen` for API calls
- `webbrowser` for opening release pages
- Existing threading infrastructure

#### **GitHub API Response**
```json
{
  "tag_name": "v0.2.19",
  "name": "SysMon v0.2.19",
  "published_at": "2025-01-15T10:30:00Z",
  "html_url": "https://github.com/juren53/system-monitor/releases/tag/v0.2.19"
}
```

### User Experience Flow

#### **Manual Check**
1. User clicks Help → Check for Updates
2. Progress indicator shows "Checking for updates..."
3. If update available: Show notification dialog
4. If current: Show "You have the latest version" message
5. If offline: Show "Unable to check - check internet connection"

#### **Startup Check (if enabled)**
1. Background check on application launch
2. Only notify if update found AND version not skipped
3. Silent if no update or offline

#### **Update Dialog Options**
- **Download Now** → Open GitHub releases page
- **Skip This Version** → Don't notify for this version again
- **Remind Me Later** → Check again in configured interval
- **Disable Auto-check** → Turn off startup checks

### Configuration Options
Add to Config menu:
- **Auto-check for Updates** (toggle)
- **Update Check Interval** (1, 3, 7, 14, 30 days)

### Integration with Existing Features

#### **Threading**
Reuse existing worker thread management pattern:
```python
self.version_worker_thread = QThread()
self.version_worker = GitHubVersionWorker(self.VERSION)
self.version_worker.moveToThread(self.version_worker_thread)
self.version_worker.version_available.connect(self.on_update_available)
```

#### **Theme Support**
Follow existing theme detection for dialog styling
- Dark/light mode aware update notifications
- Consistent button styling with other dialogs

#### **Error Handling**
Use existing message box patterns:
```python
QMessageBox.warning(self, 'Update Check Failed', message)
```

### Security Considerations
- No automatic downloads - only links to official GitHub releases
- Verify GitHub API responses before parsing
- No execution of downloaded files
- User-controlled update process

### Testing Strategy
- Mock GitHub API responses for testing
- Test network failure scenarios
- Verify version comparison logic
- Test preference persistence
- Validate UI responsiveness during checks

### Implementation Phases

#### Phase 1: Core Worker and API Integration
- Create GitHubVersionWorker class
- Implement version comparison logic
- Add basic error handling
- Test GitHub API connectivity

#### Phase 1.5: Standalone Test and Module Development ✅ COMPLETED
- ✅ Created standalone test script outside sysmon.py to test GitHub API connectivity
- ✅ Developed the version checking capability as a separate module (`github_version_checker.py`)
- ✅ Tested module with multiple repositories to validate reusability
- ✅ Defined clean API interface for integration with other programs
- ✅ Validated module independence and portability
- ✅ Created comprehensive test suite for the module
- ✅ Documented module usage patterns and integration guide

#### Phase 1.5 Deliverables
- `github_version_checker.py` - Standalone module with full functionality
- `test_cli_integration.py` - CLI integration test and demo
- `test_pyqt_integration.py` - PyQt5 GUI integration example
- `github_version_checker_documentation.md` - Comprehensive API documentation
- Module successfully tested with SysMon, VSCode, and other repositories

#### Phase 2: UI Integration ✅ COMPLETED
- Add menu items
- Create update notification dialog
- Implement user preferences for auto-checking
- Integrate with existing theme system

#### Phase 3: Polish and Refinement
- Add skip version functionality
- Implement remind me later logic
- Add configuration options
- Test edge cases and error conditions

#### Phase 4: Testing and Documentation
- Comprehensive testing
- Update user documentation
- Add changelog entry
- Verify cross-platform compatibility

### Phase 1.5: Standalone Test and Module Development Details

#### Module Design Goals
- **Independence**: Module should work without SysMon dependencies
- **Reusability**: Easy integration with other PyQt5/PySide applications
- **Minimal Dependencies**: Only requires standard libraries + urllib
- **Clean API**: Simple interface for checking versions and getting results
- **Configurable**: Flexible GitHub repository and branch configuration

#### Proposed Module Structure
```python
# github_version_checker.py
class GitHubVersionChecker:
    def __init__(self, repo_url, current_version, timeout=10):
        pass
    
    def check_for_updates(self, callback=None):
        """Check for updates, return immediately if callback provided"""
        pass
    
    def get_latest_version(self):
        """Blocking version check with timeout"""
        pass
    
    def compare_versions(self, version1, version2):
        """Semantic version comparison"""
        pass
```

#### Standalone Test Script Features
- Test GitHub API connectivity with SysMon repository
- Test version comparison logic with various version formats
- Simulate network failures and timeout scenarios
- Test different repository configurations
- Validate threading and callback mechanisms
- Performance testing for response times

#### Module Interface Testing
- Test with simple PyQt5 application
- Test with command-line script
- Test with different GitHub repositories
- Validate error handling in various scenarios

### Success Criteria
- Successfully detects new GitHub releases
- Non-blocking background checks
- Intuitive user notification system
- Robust error handling for network issues
- Seamless integration with existing UI/UX
- Persistent user preferences
- Cross-platform compatibility
- **Standalone module works independently of SysMon**
- **Module can be easily integrated with other applications**
- **Comprehensive test coverage for all module functionality**