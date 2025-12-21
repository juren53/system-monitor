# Git Attributes Configuration

This project uses `.gitattributes` to handle cross-platform line ending issues, following best practices from the HSTL Photo Metadata Project.

## File: `.gitattributes`

### Purpose
- Normalizes line endings across Windows, Linux, and macOS
- Prevents "CRLF will be replaced by LF" warnings
- Ensures consistent behavior across development environments
- Protects binary files from corruption

### Configuration Details

#### Text Files (Auto-Normalized)
```gitattributes
* text=auto
*.py text
*.md text
*.txt text
*.json text
*.yaml text
*.yml text
*.spec text
*.ini text
*.bat text
.gitignore text
.gitattributes text
```

**Behavior:**
- Stored in repository with LF (Unix-style) endings
- Automatically converted to CRLF on Windows checkout
- No conversions needed on Linux/macOS

#### LF-Only Files
```gitattributes
*.sh eol=lf
```

**Purpose:** Shell scripts always use LF endings, even on Windows

#### Binary Files (Protected)
```gitattributes
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pickle binary
*.exe binary
*.zip binary
*.dll binary
*.so binary
*.dylib binary
*.pyc binary
*.pyo binary
*.pyd binary
```

**Purpose:** Prevents Git from trying to normalize binary data

### Benefits

#### For Windows Developers
- Automatic CRLF conversion on checkout
- Consistent with Windows text editors
- No manual line ending management

#### For Linux/macOS Developers
- Files maintain LF endings (Unix standard)
- Consistent with command-line tools
- No unwanted CRLF characters

#### For Cross-Platform Collaboration
- Repository always has consistent LF endings
- Platform-appropriate line endings on checkout
- No more line ending conflicts

### Migration Process

When first adding `.gitattributes` to existing projects:

1. **New Files:** Automatically handled from creation
2. **Existing Files:** Normalized on first commit after adding `.gitattributes`
3. **Binary Files:** Protected from any text processing

### File-Specific Rules

#### Platform-Specific Config
```gitattributes
WindowsConfig/*.txt text eol=crlf
LinuxConfig/*.txt text eol=lf
```

This allows platform-specific configuration files to maintain appropriate line endings.

## Usage

### For Developers
1. Clone repository as normal
2. Git handles line endings automatically
3. No special configuration needed

### For New File Types
Add new file types to `.gitattributes`:
```gitattributes
*.ext text      # For new text file types
*.ext binary     # For new binary file types
```

## Implementation Details

This configuration follows Git's recommended practices:

- `* text=auto`: Let Git auto-detect text files
- Explicit file type declarations for clarity
- `eol=lf` for files requiring specific endings
- `binary` declarations for file protection

### References
- [Git Attributes Documentation](https://git-scm.com/docs/gitattributes)
- [HSTL Photo Metadata Project](https://github.com/juren53/HST-Metadata/tree/master/Photos/Version-2/Framework)
- [Cross-Platform Development Best Practices](https://thoughtbot.com/blog/dont-fall-for-the-git-core-autocrlf-trap)