# GitHub Repository Cleanup Plan - Option 1
## Preserve Repository & Clean Files

**Objective:** Clean up existing GitHub repository while preserving repository URL, stars, issues, and settings. Implement proper Git workflow and directory structure.

**Strategy:** Download backup → Clean remote files → Initialize local git → Push clean version

---

## Phase 1: Backup Current Repository ⏱️ 5 minutes

### Step 1.1: Download ZIP Backup
1. Open browser and navigate to your GitHub repository
2. Click the green **"Code"** button above the file list
3. Click **"Download ZIP"** in the dropdown menu
4. Save as `sysmon-backup-YYYY-MM-DD.zip` in a safe location

### Step 1.2: Verify Backup
- Extract ZIP to verify all files are present
- Compare with local directory structure

---

## Phase 2: Clean Up GitHub Repository ⏱️ 15-20 minutes

### Step 2.1: Delete Legacy Files via Web Interface
**Files to delete (these will be moved to archive/ locally):**
- `sysmon-07.py`
- `sysmon-08-L.py` 
- `sysmon-09-L.py`
- `sysmon-4.py`
- `sysmon-5.py`

**Process for each file:**
1. Navigate to file on GitHub
2. Click the 3-dot menu (⋮) → "Delete file"
3. Commit message: `Remove legacy version files (will be archived locally)`
4. Click "Commit changes"

### Step 2.2: Delete Development Files (if not needed)
Consider deleting these from GitHub (they'll remain locally):
- `animated-graph.py`
- `smooth.py`
- `generate_sysstat_graphs.sh`

---

## Phase 3: Initialize Local Git Repository ⏱️ 10 minutes

### Step 3.1: Create Directory Structure
```bash
cd /home/juren/Projects/system-monitor
mkdir -p src assets/icons assets/images docs tests scripts platforms/synology archive
```

### Step 3.2: Move Files to New Structure
```bash
# Core application
mv sysmon.py src/
mv sysmon src/

# Assets
mv ICON_sysmon.ico ICON_sysmon.png assets/icons/
mv SysMon.png assets/images/

# Documentation
mv CHANGELOG.md docs/
mv Analysis_of_SysMon-v0.0.9b_code.txt docs/
mv changes docs/
mv "smooth time series data for output to a realtime graph.txt" docs/

# Tests
mv test_routines/* tests/
rmdir test_routines

# Scripts
mv animated-graph.py smooth.py generate_sysstat_graphs.sh scripts/

# Platform-specific
mv synology/* platforms/synology/
rmdir synology

# Archive
mv sysmon-07.py sysmon-08-L.py sysmon-09-L.py sysmon-4.py sysmon-5.py archive/
```

### Step 3.3: Initialize Git
```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 3.4: Create .gitignore
Create comprehensive .gitignore (from GIT_REPOSITORY_SETUP_PLAN.md)

### Step 3.5: Initial Commit
```bash
git add .
git commit -m "Initial commit: SysMon v0.0.9c with comprehensive refactoring"
```

---

## Phase 4: Connect to Remote & Push ⏱️ 10 minutes

### Step 4.1: Add Remote Origin
```bash
git remote add origin https://github.com/yourusername/your-repo.git
```

### Step 4.2: Push to GitHub
```bash
git branch -M main
git push -u origin main
```

---

## Phase 5: Final Setup ⏱️ 10 minutes

### Step 5.1: Create README.md
Add comprehensive README following GIT_REPOSITORY_SETUP_PLAN.md

### Step 5.2: Add LICENSE
Choose appropriate license (MIT recommended)

### Step 5.3: Final Push
```bash
git add README.md LICENSE
git commit -m "Add README and LICENSE"
git push origin main
```

---

## Pre-Execution Checklist

### Before you start:
- [ ] Have your GitHub username and repository name ready
- [ ] Confirm you have write access to the repository
- [ ] Decide on your preferred license
- [ ] Have your Git user.name and user.email ready

### Files you'll need to update after reorganization:
- Any import statements that reference moved files
- Documentation that references old file paths
- Scripts that reference old file locations

---

## Expected Final Directory Structure

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
│   ├── Analysis_of_SysMon-v0.0.9b_code.txt
│   └── changes/
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

---

## Estimated Total Time: 45-60 minutes

---

## Critical Success Factors

1. **Backup First**: Always download ZIP before making changes
2. **Verify Each Step**: Check that files are where you expect them
3. **Test After Reorganization**: Ensure sysmon.py still works from new location
4. **Update References**: Fix any hardcoded paths in documentation

---

## Advantages of This Approach

- ✅ Preserves repository URL, stars, issues
- ✅ Maintains any existing settings/integrations
- ✅ Clean backup via ZIP download
- ✅ Proper Git workflow going forward
- ✅ Implements planned directory structure
- ✅ Professional repository organization

---

## Notes

- Files deleted via GitHub interface remain in Git history (acceptable for this use case)
- The ZIP backup provides complete safety net
- Proper version control established from this point forward
- Follows best practices for Git repository management