# GitHub Version Checker Module Documentation

## Overview

The `GitHub Version Checker` is a standalone Python module that enables applications to check for new releases on GitHub repositories. It's designed to be lightweight, reusable, and easy to integrate into any Python application.

## Features

- **Standalone Operation**: Works independently of any specific application
- **Async Support**: Both synchronous and asynchronous version checking
- **Semantic Versioning**: Robust version comparison including pre-release versions (a, b, rc)
- **Flexible Repository Support**: Accepts various GitHub URL formats
- **Minimal Dependencies**: Only requires standard library (urllib, json, re, threading)
- **Robust Error Handling**: Comprehensive error handling for network issues
- **Configurable Timeouts**: Prevents hanging on network requests

## Installation

Simply copy `github_version_checker.py` into your project directory:

```bash
cp github_version_checker.py /path/to/your/project/
```

## Quick Start

### Basic Usage

```python
from github_version_checker import GitHubVersionChecker

# Create checker instance
checker = GitHubVersionChecker(
    repo_url="owner/repository",  # or full GitHub URL
    current_version="1.0.0",
    timeout=10
)

# Synchronous check
result = checker.get_latest_version()
if result.has_update:
    print(f"Update available: {result.current_version} → {result.latest_version}")
    print(f"Download: {result.download_url}")
else:
    print("You have the latest version")

# Asynchronous check with callback
def on_update_check(result):
    if result.has_update:
        print(f"Update found! {result.latest_version}")

checker.check_for_updates(on_update_check)
```

### Integration Example for GUI Applications

```python
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from github_version_checker import GitHubVersionChecker, VersionCheckResult

class UpdateCheckThread(QThread):
    result_ready = pyqtSignal(VersionCheckResult)
    
    def __init__(self, checker):
        super().__init__()
        self.checker = checker
    
    def run(self):
        result = self.checker.get_latest_version()
        self.result_ready.emit(result)

# Usage in your application
def check_for_updates():
    checker = GitHubVersionChecker("myorg/myapp", "1.0.0")
    
    thread = UpdateCheckThread(checker)
    thread.result_ready.connect(lambda result: show_update_dialog(result))
    thread.start()

def show_update_dialog(result):
    if result.has_update:
        QMessageBox.information(None, "Update Available", 
            f"New version {result.latest_version} is available!\n"
            f"Current version: {result.current_version}\n"
            f"Download: {result.download_url}")
```

## API Reference

### GitHubVersionChecker Class

#### Constructor

```python
GitHubVersionChecker(repo_url, current_version, timeout=10)
```

**Parameters:**
- `repo_url` (str): GitHub repository in formats:
  - `"owner/repository"`
  - `"github.com/owner/repository"`
  - `"https://github.com/owner/repository"`
  - `"git@github.com:owner/repository.git"`
- `current_version` (str): Current application version
- `timeout` (int): Network request timeout in seconds (default: 10)

#### Methods

##### get_latest_version() → VersionCheckResult

Performs a synchronous version check. Blocks until the request completes.

**Returns:** `VersionCheckResult` object with check results

##### check_for_updates(callback: Callable[[VersionCheckResult], None])

Performs an asynchronous version check with callback.

**Parameters:**
- `callback`: Function to call when check completes

##### compare_versions(version1: str, version2: str) → int

Compares two version strings using semantic versioning.

**Parameters:**
- `version1`: First version string
- `version2`: Second version string

**Returns:**
- `-1`: version1 < version2
- `0`: version1 == version2
- `1`: version1 > version2

### VersionCheckResult Class

Data class containing version check results.

#### Attributes

- `has_update` (bool): True if newer version is available
- `current_version` (str): The current version string
- `latest_version` (str): The latest version from GitHub
- `download_url` (str): URL to the GitHub release page
- `release_notes` (str): Full release notes/description
- `published_date` (str): ISO 8601 publication date
- `error_message` (str): Error message if check failed
- `is_newer` (bool): True if current version is older than latest

## Repository URL Formats

The module accepts various GitHub URL formats:

```python
# All these are valid:
checker = GitHubVersionChecker("owner/repository", "1.0.0")
checker = GitHubVersionChecker("github.com/owner/repository", "1.0.0")
checker = GitHubVersionChecker("https://github.com/owner/repository", "1.0.0")
checker = GitHubVersionChecker("git@github.com:owner/repository.git", "1.0.0")
```

## Version Comparison Logic

The module supports semantic versioning with pre-release handling:

### Supported Version Formats
- `1.0.0` - Standard semantic version
- `1.0.0a` - Alpha release (equivalent to 1.0.0-alpha)
- `1.0.0b` - Beta release (equivalent to 1.0.0-beta)
- `1.0.0rc` - Release candidate
- `v1.0.0` - With 'v' prefix (automatically stripped)

### Version Comparison Rules
1. **Numeric Comparison**: Compare major.minor.patch numerically
2. **Pre-release Handling**: Pre-releases are considered older than final releases
3. **Alpha < Beta < RC < Final**: Pre-release type ranking
4. **Missing Parts**: Versions with missing parts are padded with zeros (`1.0` → `1.0.0`)

## Error Handling

The module provides comprehensive error handling:

### Network Errors
- `URLError`: General network connectivity issues
- `HTTPError`: HTTP status errors (404, 500, etc.)
- Timeout errors when requests exceed the specified timeout

### Data Errors
- `JSONDecodeError`: Invalid JSON response from GitHub API
- Invalid repository URL formats
- Malformed version strings

### Error Recovery
- Graceful degradation when GitHub API is unavailable
- Detailed error messages in `VersionCheckResult.error_message`
- No exceptions thrown in normal operation

## Best Practices

### 1. Use Asynchronous Checks for GUI Applications

```python
# Good: Non-blocking for GUI
checker.check_for_updates(callback)

# Avoid: Blocking in GUI thread
result = checker.get_latest_version()  # This will freeze UI
```

### 2. Implement User Preferences

```python
# Store user preferences for update checking
class AppSettings:
    def __init__(self):
        self.auto_check_updates = True
        self.last_check_time = None
        self.skipped_versions = []

def should_check_for_updates(settings, current_time):
    if not settings.auto_check_updates:
        return False
    if settings.last_check_time is None:
        return True
    # Check at most once per day
    return (current_time - settings.last_check_time) > 86400
```

### 3. Handle Skip Version Logic

```python
def check_with_skip_logic(checker, skipped_versions):
    result = checker.get_latest_version()
    
    if result.has_update and result.latest_version not in skipped_versions:
        show_update_notification(result)
        return True
    return False
```

### 4. Cache Results

```python
import time

class CachedVersionChecker:
    def __init__(self, repo_url, current_version, cache_duration=3600):
        self.checker = GitHubVersionChecker(repo_url, current_version)
        self.cache_duration = cache_duration
        self.last_check = 0
        self.cached_result = None
    
    def get_latest_version(self):
        current_time = time.time()
        
        if (current_time - self.last_check) < self.cache_duration and self.cached_result:
            return self.cached_result
        
        result = self.checker.get_latest_version()
        self.cached_result = result
        self.last_check = current_time
        
        return result
```

## Integration Examples

### Command Line Application

```python
#!/usr/bin/env python3
import argparse
from github_version_checker import GitHubVersionChecker

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    
    checker = GitHubVersionChecker(args.repo, args.version)
    result = checker.get_latest_version()
    
    if result.has_update:
        print(f"Update available: {result.current_version} → {result.latest_version}")
        print(f"Download: {result.download_url}")
    else:
        print("Up to date")

if __name__ == "__main__":
    main()
```

### Web Application Integration

```python
from flask import Flask, jsonify
from github_version_checker import GitHubVersionChecker

app = Flask(__name__)

@app.route('/check-updates/<repo>/<version>')
def check_updates(repo, version):
    try:
        checker = GitHubVersionChecker(repo, version)
        result = checker.get_latest_version()
        
        return jsonify({
            'has_update': result.has_update,
            'current_version': result.current_version,
            'latest_version': result.latest_version,
            'download_url': result.download_url,
            'error': result.error_message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Testing

The module includes comprehensive test functionality:

```python
# Run the built-in test suite
python3 github_version_checker.py

# Test with different repositories
python3 test_cli_integration.py --repo "microsoft/vscode" --version "1.85.0"
```

## Security Considerations

- **No Automatic Downloads**: The module only checks for updates and provides download links
- **HTTPS Only**: All requests use secure HTTPS connections
- **Rate Limiting Aware**: Respects GitHub API rate limits
- **No Authentication Required**: Uses public GitHub API endpoints
- **Input Validation**: Validates repository URLs and version strings

## Limitations

- **GitHub Only**: Works only with GitHub-hosted repositories
- **Public Repositories**: Requires public repositories (private repos need authentication)
- **API Rate Limits**: Subject to GitHub API rate limiting (60 requests/hour for unauthenticated)
- **Release-based**: Only checks for GitHub releases, not git tags or commits

## Troubleshooting

### Common Issues

1. **404 Not Found Error**
   - Repository URL is incorrect
   - Repository has no releases (only tags/commits)
   - Repository is private

2. **Network Timeout**
   - Increase timeout parameter: `GitHubVersionChecker(repo, version, timeout=30)`
   - Check internet connectivity
   - Verify firewall settings

3. **Invalid Version Comparison**
   - Ensure version strings follow semantic versioning
   - Check for unexpected characters in version strings

### Debug Mode

Enable debug output by checking error messages:

```python
result = checker.get_latest_version()
if result.error_message:
    print(f"Debug: {result.error_message}")
    # Log the full error for troubleshooting
```

## License

This module is part of the SysMon project and follows the same license terms.

## Contributing

When contributing to this module:
1. Maintain backward compatibility
2. Add comprehensive tests for new features
3. Update documentation
4. Follow the existing code style and patterns