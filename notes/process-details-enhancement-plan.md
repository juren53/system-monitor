# Process Details Enhancement Plan

## Current State

### What We Show Now
- **Process Name Column**: Truncated to 20-25 characters
- **Example**: `chrome.exe` instead of `chrome.exe --type=renderer --origin-trial-disabled`
- **Data Source**: `psutil.process_iter(['pid', 'name'])` - only collects `name` field

### What's Available from psutil

psutil provides extensive process information:

```python
proc = psutil.Process(pid)

# Basic info
proc.name()              # 'chrome.exe'
proc.exe()               # 'C:\\Program Files\\Google\\Chrome\\chrome.exe'
proc.cmdline()           # ['chrome.exe', '--type=renderer', '--origin-trial-disabled', ...]
proc.cwd()               # 'C:\\Users\\jimur'
proc.username()          # 'DESKTOP\\jimur'
proc.create_time()       # 1234567890.123

# Status/metrics
proc.status()            # 'running', 'sleeping', etc.
proc.num_threads()       # 12
proc.cpu_percent()       # Already collected
proc.memory_percent()    # Already collected
proc.memory_info()       # rss, vms, etc.

# Network/Disk
proc.connections()       # Network connections (already used)
proc.io_counters()       # Disk I/O (already used)
```

### Examples from 'glances'
```
NordVPN.exe --auto-start
chrome.exe --type=renderer --origin-trial-dis
python.exe C:\Users\jimur\AppData\Local\Packa
firefox.exe -contentproc -isForBrowser -prefs
```

---

## Enhancement Options

### Option 1: Show Full Command Line in Process Name Column ⭐ RECOMMENDED

**Implementation:**
- Replace `proc.info['name']` with `' '.join(proc.cmdline())` or smart truncation
- Widen the Process Name column (e.g., 400-500px instead of 200-240px)
- Enable horizontal scrolling on the table
- Show first 60-80 chars with ellipsis for very long cmdlines

**Pros:**
✅ Immediate visibility - no extra clicks
✅ Similar to 'glances' and other monitoring tools
✅ Simple implementation
✅ Users can see arguments at a glance
✅ Can still sort/filter by full command line

**Cons:**
❌ Takes more horizontal space
❌ Very long command lines still need truncation
❌ Dialog may need to be wider (or scrollable)

**Code Changes:**
- Modify ProcessWorker to collect cmdline: `process_iter(['pid', 'name', 'cmdline'])`
- Update display logic to use cmdline instead of name
- Increase column width and enable horizontal scroll

**Example Display:**
```
PID    Process Name / Command Line                              CPU %   Memory %
1234   chrome.exe --type=renderer --origin-trial-disabled...    15.2%   2.3%
5678   python.exe C:\Users\jimur\AppData\Local\Packages\...     8.5%    1.8%
```

---

### Option 2: Tooltip on Hover

**Implementation:**
- Keep truncated names in the table
- Add tooltips showing full command line + additional details
- Hover over any cell in a row to see tooltip

**Pros:**
✅ Clean, compact table layout
✅ Full details available without taking space
✅ Can show even more info (exe path, user, status, etc.)
✅ No horizontal scrolling needed

**Cons:**
❌ Requires hovering - not immediately visible
❌ Can't copy full command line easily
❌ Less discoverable for users

**Code Changes:**
- Add `setToolTip()` to each table row/cell
- Format tooltip with full process details

**Example Tooltip:**
```
PID: 1234
Name: chrome.exe
Command: chrome.exe --type=renderer --origin-trial-disabled --autoplay-policy=user-gesture-required
Path: C:\Program Files\Google\Chrome\Application\chrome.exe
User: DESKTOP\jimur
Status: running
Threads: 12
```

---

### Option 3: Details Button/Column

**Implementation:**
- Add a "Details" button or icon in each row
- Click to open a popup dialog with all process information
- Alternative: Double-click row to show details

**Pros:**
✅ Clean table layout
✅ Can show comprehensive information
✅ Users choose when to see details
✅ Can include real-time updates for selected process

**Cons:**
❌ Extra click required
❌ More UI complexity
❌ Takes time to view details for multiple processes

**Code Changes:**
- Add Details column with QPushButton or make rows double-clickable
- Create ProcessDetailsDialog showing all available info
- Connect click handler to show dialog

---

### Option 4: Expandable Rows

**Implementation:**
- Single-click row to expand/collapse additional details
- Show command line and other info in expanded section
- Similar to accordion UI pattern

**Pros:**
✅ Compact when collapsed
✅ Details visible without separate dialog
✅ Can show multiple expanded rows simultaneously

**Cons:**
❌ Complex UI implementation in Qt
❌ Scrolling behavior can be awkward
❌ Table height constantly changing

**Code Changes:**
- Custom table item delegate
- Row height management
- Expand/collapse logic

---

### Option 5: Multi-Column Approach

**Implementation:**
- Split into separate columns: "Name", "Arguments", "Path"
- Name: just the executable (chrome.exe)
- Arguments: command-line args (--type=renderer...)
- Path: working directory or exe path

**Pros:**
✅ Organized information
✅ Can sort by different aspects
✅ Clear separation of concerns

**Cons:**
❌ Takes significant horizontal space
❌ Many columns can be overwhelming
❌ Arguments column still needs truncation

**Code Changes:**
- Increase column count by 1-2
- Modify ProcessWorker to collect cmdline, exe, or cwd
- Adjust column widths and layout

---

### Option 6: Smart Truncation with Ellipsis

**Implementation:**
- Show full command line but with intelligent truncation
- Keep important parts visible (executable name + key args)
- Click/hover to see full text in tooltip

**Pros:**
✅ Balance between visibility and space
✅ Shows most important information
✅ Full details available on demand

**Cons:**
❌ Complex truncation logic
❌ May hide important arguments
❌ Users need to remember hover/click

**Code Changes:**
- Smart truncation algorithm (keep start and key parts)
- Tooltip for full command line
- Possibly add "..." indicator

---

## Recommendations

### Primary Recommendation: **Option 1 + Option 2 Hybrid**

**Why:**
1. **Show More Upfront**: Display first 60-80 characters of full command line
2. **Tooltip for Complete Details**: Hover shows everything (full cmdline, path, user, status)
3. **Wider Column**: Increase Process Name column to 350-400px
4. **Enable Horizontal Scroll**: Let table scroll if needed
5. **Best of Both Worlds**: Immediate visibility + comprehensive details on demand

**Implementation Steps:**
1. Modify ProcessWorker to collect `cmdline` from psutil
2. Format cmdline as string (join args with spaces)
3. Display first 70 chars in table with "..." if truncated
4. Add rich tooltip with all available process details
5. Widen Process Name column and enable horizontal scrolling
6. Test with various process types (browsers, Python scripts, system processes)

**Example Implementation:**
```python
# In ProcessWorker
cmdline = proc.cmdline()
cmdline_str = ' '.join(cmdline) if cmdline else proc.name()

processes.append({
    'pid': proc.info['pid'],
    'name': proc.info['name'],
    'cmdline': cmdline_str,
    'exe': proc.exe(),
    'username': proc.username(),
    'status': proc.status(),
    'num_threads': proc.num_threads()
})

# In dialog display
cmdline_display = proc['cmdline'][:70] + '...' if len(proc['cmdline']) > 70 else proc['cmdline']
name_item = QTableWidgetItem(cmdline_display)

# Tooltip with full details
tooltip = f"""PID: {proc['pid']}
Command: {proc['cmdline']}
Executable: {proc['exe']}
User: {proc['username']}
Status: {proc['status']}
Threads: {proc['num_threads']}"""
name_item.setToolTip(tooltip)
```

---

## Alternative Recommendation: **Option 1 Only (Simplest)**

If you prefer the simplest approach:
- Just show full command line (up to 100 chars)
- Widen Process Name column to 500px
- Enable horizontal scrolling
- No tooltips needed

**Pros:**
✅ Minimal code changes
✅ Exactly like 'glances'
✅ No hidden information

**Cons:**
❌ Wide table
❌ May need scrolling

---

## Questions for User

1. **Primary Display**: Do you want to see full command line in the table, or just extended name with tooltip?

2. **Column Width**: Are you comfortable with a wider table (500-600px wide) or prefer scrolling?

3. **Additional Info**: Besides command line, what other process details interest you?
   - Executable path
   - Username/owner
   - Status (running/sleeping)
   - Number of threads
   - Working directory
   - Parent process

4. **All Three Dialogs**: Should this enhancement apply to all three dialogs (CPU, Disk, Network)?

5. **Table Behavior**: Prefer horizontal scrolling or fixed-width with tooltips?

---

## Implementation Complexity

| Option | Complexity | Lines of Code | Testing Effort |
|--------|------------|---------------|----------------|
| Option 1 | Low | ~30 lines | Low |
| Option 2 | Low | ~20 lines | Low |
| Option 1+2 Hybrid | Medium | ~50 lines | Medium |
| Option 3 | Medium | ~100 lines | Medium |
| Option 4 | High | ~200 lines | High |
| Option 5 | Medium | ~60 lines | Low |
| Option 6 | Medium | ~40 lines | Medium |

---

## Next Steps

Please review these options and let me know:
1. Which approach you prefer (or combination)
2. Whether you want additional process details beyond command line
3. Any specific UI preferences (column width, scrolling, tooltips)

I can implement any of these options or create a custom combination based on your feedback.
