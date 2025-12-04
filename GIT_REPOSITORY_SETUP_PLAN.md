# SysMon Git Repository Setup Plan

## Overview

This document outlines a comprehensive plan to establish a git repository locally for the SysMon project, enabling proper version control, collaboration capabilities, and professional project management.

## Current Project Analysis

### Project Structure
```
/home/juren/Projects/system-monitor/
├── Core Application Files
│   ├── sysmon.py                    # Main application (v0.0.9c, recently refactored)
│   ├── sysmon                       # Executable version
│   └── (archived - see archive/ directory)
├── Supporting Assets
│   ├── ICON_sysmon.ico, ICON_sysmon.png  # Application icons
│   ├── SysMon.png                     # Documentation screenshot
│   ├── CHANGELOG.md                   # Version history
│   └── Analysis_of_SysMon_code.txt    # Code analysis
├── Development & Testing
│   ├── test_routines/                 # Test scripts
│   ├── synology/syno-monitor.py       # Synology-specific version
│   ├── animated-graph.py, smooth.py    # Development utilities
│   └── generate_sysstat_graphs.sh     # Graph generation script
└── Documentation
    ├── changes                        # Change notes
    └── smooth time series data...      # Documentation file
```

### Current State
- **Version**: v0.0.9c (2025-12-04)
- **Recent Major Changes**: Comprehensive constants implementation (22 constants)
- **Platform Support**: Linux/Windows with Qt5 backend
- **Features**: Real-time monitoring, interactive controls, theme inheritance

---

## Phase 1: Repository Initialization

### 1.1 Initialize Git Repository
```bash
cd /home/juren/Projects/system-monitor
git init
```

### 1.2 Create Comprehensive .gitignore
```gitignore
# Python cache files
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE and Editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# User configuration files
.sysmon_config.json
*.log

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Test outputs
test_results/
.coverage
htmlcov/
.pytest_cache/

# Distribution
dist/
build/
*.egg
```

### 1.3 Configure Git User
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## Phase 2: Initial Commit Strategy

### 2.1 Initial Commit Structure
- Add all existing files to git
- Create comprehensive baseline commit
- Document current state thoroughly

### 2.2 Initial Commit Message
```
Initial commit: SysMon v0.0.9c with comprehensive refactoring

Core Features:
- Complete system monitoring application with CPU, Disk I/O, Network graphs
- Interactive controls: +/- for time window, double-click for process details
- Real-time data visualization with smooth scrolling and scaling
- Cross-platform compatibility (Linux/Windows) with Qt5 backend

Recent Improvements (v0.0.9c):
- Comprehensive constants implementation (22 constants)
- Eliminated all magic numbers for improved maintainability
- Organized constants into logical groups: Data Storage, Timing, Display & UI, Unit Conversion, Process & Popup
- Enhanced code readability and documentation

Technical Features:
- Desktop theme inheritance (light/dark auto-detection)
- Window geometry persistence with JSON configuration
- GdkPixbuf warning suppression for clean output
- Process drill-down popups with top 10 resource consumers
- Visual scale change indicators with flash effects

Documentation:
- Comprehensive CHANGELOG.md with detailed version history
- Code analysis documentation
- Multiple version archives for reference

Assets:
- Application icons (PNG/ICO formats)
- Documentation screenshots
- Test routines and development utilities
```

---

## Phase 3: Branch Strategy

### 3.1 Branch Structure
```
main (or master)     # Stable production code
├── develop           # Development and feature work
├── feature/constants  # Example feature branch
├── feature/ui-improvements
└── hotfix/bug-fixes
```

### 3.2 Branch Implementation
```bash
# Create main branch
git checkout -b main

# Create develop branch
git checkout -b develop

# Set up tracking
git push -u origin main
git push -u origin develop
```

### 3.3 Branch Protection Rules
- `main`: Only merge via pull request, require review
- `develop`: Direct commits allowed, feature branches merge here
- Feature branches: Created from `develop`, merge back to `develop`

---

## Phase 4: Repository Organization

### 4.1 Recommended Directory Structure
```
sysmon/
├── src/                    # Main application files
│   ├── sysmon.py          # Primary application
│   └── sysmon             # Executable
├── assets/                # Static assets
│   ├── icons/
│   │   ├── ICON_sysmon.ico
│   │   └── ICON_sysmon.png
│   └── images/
│       └── SysMon.png
├── docs/                  # Documentation
│   ├── CHANGELOG.md
│   ├── README.md
│   ├── Analysis_of_SysMon_code.txt
│   └── changes
├── tests/                 # Test routines
│   ├── test_geometry.py
│   ├── test_stderr_filter.py
│   └── test_routines/
├── scripts/               # Utility scripts
│   ├── generate_sysstat_graphs.sh
│   ├── animated-graph.py
│   └── smooth.py
├── platforms/             # Platform-specific versions
│   └── synology/
│       └── syno-monitor.py
├── archive/               # Version archives and development versions
│   ├── sysmon-07.py
│   ├── sysmon-08-L.py
│   ├── sysmon-09-L.py
│   ├── sysmon-4.py
│   └── sysmon-5.py
├── .gitignore
├── LICENSE
└── README.md
```

### 4.2 Migration Strategy
1. **Phase 1**: Create new directory structure
2. **Phase 2**: Move files to appropriate directories
3. **Phase 3**: Update any path references in code
4. **Phase 4**: Commit reorganization

---

## Phase 5: Git Configuration

### 5.1 Local Configuration
```bash
# Set default branch name
git config init.defaultBranch main

# Configure line endings (important after CRLF fixes)
git config core.autocrlf input  # Linux
# git config core.autocrlf true   # Windows

# Configure push strategy
git config push.default simple

# Set up useful aliases
git config alias.st status
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
```

### 5.2 Repository Metadata
- Create `README.md` with project overview
- Add `LICENSE` file (MIT recommended for open source)
- Consider `CONTRIBUTING.md` for future collaboration
- Add `.gitattributes` for line ending management

---

## Phase 6: Commit History Organization

### 6.1 Retroactive Commit Structure (Optional)
```
Initial commit: Complete v0.0.9c application
├── feat: Add basic system monitoring functionality
├── feat: Implement interactive controls (+/- keys)
├── feat: Add process drill-down popups
├── feat: Implement desktop theme inheritance
├── feat: Add window geometry persistence
├── feat: Add GdkPixbuf warning suppression
├── refactor: Implement comprehensive constants system
├── fix: Resolve Linux compatibility issues
└── docs: Update CHANGELOG and documentation
```

### 6.2 Tag Management
```bash
# Create tags for releases
git tag -a v0.0.9c -m "Release v0.0.9c: Constants refactoring"
git tag -a v0.0.9b -m "Release v0.0.9b: X-axis behavior fixes"
git tag -a v0.0.9a -m "Release v0.0.9a: Interactive controls"

# Push tags
git push --tags
```

### 6.3 Semantic Versioning Strategy
- **Major**: Breaking changes (2.0.0)
- **Minor**: New features (0.10.0)
- **Patch**: Bug fixes (0.0.10)

---

## Phase 7: Remote Repository Setup

### 7.1 Platform Selection

#### GitHub (Recommended)
- **Pros**: Largest community, excellent integration, good free tier
- **Cons**: Private repository limits
- **Setup**: Create via web interface, add remote origin

#### GitLab
- **Pros**: More features, unlimited private repos, CI/CD included
- **Cons**: Smaller community
- **Setup**: Self-hosted or gitlab.com

#### Bitbucket
- **Pros**: Good for small teams, free private repos
- **Cons**: Less popular, fewer integrations

### 7.2 Repository Creation
```bash
# After creating repository on platform
git remote add origin https://github.com/username/sysmon.git
git push -u origin main
git push -u origin develop
```

### 7.3 Repository Configuration
- Set repository description and topics
- Add README.md as repository homepage
- Configure default branch to `main`
- Set up branch protection rules
- Enable issues and pull requests

---

## Phase 8: Documentation Enhancement

### 8.1 README.md Structure
```markdown
# SysMon - Real-time System Monitor

## Description
Comprehensive system monitoring application with real-time graphs for CPU, Disk I/O, and Network activity.

## Features
- Real-time monitoring with smooth scrolling graphs
- Interactive controls (time window adjustment, process drill-down)
- Cross-platform compatibility (Linux/Windows)
- Desktop theme inheritance
- Process resource analysis
- Window geometry persistence

## Screenshots
![SysMon in action](assets/images/SysMon.png)

## Installation
### Requirements
- Python 3.7+
- matplotlib
- psutil
- PyQt5

### Install Dependencies
```bash
pip install matplotlib psutil PyQt5
```

### Run Application
```bash
python3 sysmon.py
```

## Usage
### Command Line Options
- `-s, --smooth-window`: Smoothing window size (1-20, default: 5)
- `-t, --time-window`: Time window in seconds (5-120, default: 20)

### Interactive Controls
- `+` or `=`: Increase time window by 5 seconds
- `-`: Decrease time window by 5 seconds
- Double-click on graph: Show top 10 processes for that metric

## Configuration
Configuration saved to: `~/.sysmon_config.json`

## Version History
See [CHANGELOG.md](docs/CHANGELOG.md) for detailed version history.

## License
[License Name] - see [LICENSE](LICENSE) file for details.
```

### 8.2 Additional Documentation
- **API Documentation**: If exposing any APIs
- **Development Setup**: Guide for new developers
- **Troubleshooting**: Common issues and solutions
- **Architecture Overview**: System design documentation

---

## Phase 9: Workflow Establishment

### 9.1 Commit Message Convention
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(ui): Add dark mode theme support
fix(graph): Resolve memory leak in animation loop
docs(readme): Update installation instructions
refactor(constants): Replace magic numbers with named constants
```

### 9.2 Development Workflow
1. Create feature branch from `develop`
2. Make changes with atomic commits
3. Test thoroughly
4. Create pull request to `develop`
5. Code review (if collaborating)
6. Merge to `develop`
7. Periodically merge `develop` to `main` for releases

### 9.3 Release Process
1. Update version numbers
2. Update CHANGELOG.md
3. Create release tag
4. Merge `develop` to `main`
5. Push tags and create GitHub release

---

## Phase 10: Maintenance Strategy

### 10.1 Regular Maintenance
- **Daily**: Commit changes with proper messages
- **Weekly**: Update CHANGELOG, review issues
- **Monthly**: Review and merge `develop` to `main`
- **Quarterly**: Review and update dependencies

### 10.2 Backup and Security
- **Repository Backup**: Regular git bundle backups
- **Remote Backup**: Multiple remote locations
- **Access Control**: Manage collaborator permissions
- **Secrets Management**: Never commit sensitive information

### 10.3 Quality Assurance
- **Code Review**: Review all changes before merge
- **Testing**: Comprehensive testing before releases
- **Documentation**: Keep docs current with code changes
- **Performance**: Monitor application performance

---

## Implementation Timeline

### Week 1: Foundation (High Priority)
- [ ] Initialize git repository
- [ ] Create .gitignore
- [ ] Initial commit with current state
- [ ] Create basic README.md
- [ ] Set up remote repository

### Week 2: Organization (Medium Priority)
- [ ] Implement branch strategy
- [ ] Reorganize directory structure
- [ ] Create comprehensive documentation
- [ ] Set up commit message conventions

### Week 3: Workflow (Medium Priority)
- [ ] Establish development workflow
- [ ] Create release process
- [ ] Set up tagging strategy
- [ ] Configure repository settings

### Ongoing: Maintenance (Low Priority)
- [ ] Regular commits and updates
- [ ] CI/CD pipeline setup
- [ ] Advanced documentation
- [ ] Community engagement

---

## Success Metrics

### Technical Metrics
- [ ] All code under version control
- [ ] Proper commit history with meaningful messages
- [ ] Working branch strategy
- [ ] Comprehensive documentation

### Process Metrics
- [ ] Consistent commit frequency
- [ ] Proper release tagging
- [ ] Updated CHANGELOG with each change
- [ ] Responsive issue management

### Quality Metrics
- [ ] Code review process established
- [ ] Testing coverage maintained
- [ ] Documentation accuracy
- [ ] Repository accessibility

---

## Conclusion

This comprehensive plan establishes professional version control for SysMon, enabling:
- **Better Change Tracking**: Every modification documented and attributed
- **Collaboration Ready**: Multiple developers can work together
- **Release Management**: Proper versioning and release process
- **Quality Assurance**: Code review and testing workflows
- **Professional Presentation**: Well-documented, organized project

The implementation should be approached systematically, starting with basic repository setup and progressively adding more sophisticated workflows and processes as needed.