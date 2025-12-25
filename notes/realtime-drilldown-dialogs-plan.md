# Plan: Real-Time Dynamic Drill-Down Dialogs for SysMon

## Problem Statement
Current drill-down dialogs are limited:
- **CPU**: Has RealTimeProcessDialog (good - live updates every 1 second)
- **Disk I/O**: Uses static ProcessInfoDialog (poor - one-time snapshot only)
- **Network**: Uses static ProcessInfoDialog (poor - one-time snapshot only)

Users need real-time dynamic information in all drill-down dialogs to monitor current system activity, not just historical snapshots.

## Solution Overview
Implement real-time dynamic dialogs for all three metrics using embedded Qt dialogs with psutil, following the established RealTimeProcessDialog pattern. Implement sequentially: CPU enhancement first, then Disk I/O, then Network.

**Architecture Decision**: Embedded Qt dialogs (not standalone apps)
**Data Source**: Custom psutil-based implementation (not system utilities)
**Implementation Order**: CPU → Disk I/O → Network

## Implementation Approach

### Phase 1: CPU Drill-Down Enhancement (Extend Existing)
**Goal**: Enhance RealTimeProcessDialog with additional columns and sorting

**Current State**:
- RealTimeProcessDialog already exists (lines 369-586)
- Shows: PID, Process Name, CPU %
- Updates every 1 second
- Color-coded CPU percentages
- Pause/resume capability

**Enhancements**:
1. Add Memory % column
2. Add sortable columns (click header to sort)
3. Add filtering capability (text search box)
4. Add column for command line arguments (optional, toggleable)

**Minimal Changes**:
- Extend ProcessWorker to include memory_percent in CPU mode
- Add 4th column to table widget
- Implement header click sorting
- Add search/filter text box

**Files Modified**:
- `src/sysmon.py`: Enhance RealTimeProcessDialog class

---

### Phase 2: Disk I/O Drill-Down (New Implementation)
**Goal**: Create RealTimeDiskDialog showing read/write rates per process

**Metrics to Display**:
- PID
- Process Name
- Read Rate (MB/s) - instantaneous
- Write Rate (MB/s) - instantaneous
- Total I/O (MB) - cumulative since process start

**Technical Approach**:

1. **Create RealTimeDiskDialog class** (similar to RealTimeProcessDialog)
   - QTableWidget with 5 columns
   - 1-second update timer
   - Pause/resume button
   - Color coding based on I/O rates (high red, medium yellow, low green)

2. **Extend ProcessWorker for disk rates**
   - Current implementation only shows cumulative totals
   - Need to calculate deltas between updates:
     ```python
     # Store previous io_counters per process
     self.prev_io_counters = {}

     # On each update:
     current_io = proc.io_counters()
     if pid in self.prev_io_counters:
         prev_io = self.prev_io_counters[pid]
         read_rate = (current_io.read_bytes - prev_io.read_bytes) / time_delta / (1024**2)
         write_rate = (current_io.write_bytes - prev_io.write_bytes) / time_delta / (1024**2)
     self.prev_io_counters[pid] = current_io
     ```

3. **Data Dictionary**:
   ```python
   {
     'pid': int,
     'name': str,
     'read_rate': float,    # MB/s
     'write_rate': float,   # MB/s
     'total_io': float      # MB cumulative
   }
   ```

4. **Replace double-click handler**:
   ```python
   # Line 754-755, change from:
   lambda evt: self.show_top_processes('disk') if evt.double() else None
   # To:
   lambda evt: self.show_realtime_disk() if evt.double() else None
   ```

5. **Color Coding Logic**:
   - Red: Combined I/O rate > 10 MB/s
   - Yellow: Combined I/O rate 1-10 MB/s
   - Green: Combined I/O rate < 1 MB/s

**Files Modified**:
- `src/sysmon.py`: Add RealTimeDiskDialog class (after RealTimeProcessDialog)
- `src/sysmon.py`: Extend ProcessWorker to support disk rate calculations
- `src/sysmon.py`: Add show_realtime_disk() method
- `src/sysmon.py`: Update disk plot double-click handler

**Challenges**:
- Need to maintain state between worker runs (previous I/O counters)
- Consider making ProcessWorker persistent per dialog instead of recreating
- Handle processes that start/stop between updates

---

### Phase 3: Network Drill-Down (New Implementation)
**Goal**: Create RealTimeNetworkDialog showing connections and bandwidth per process

**Metrics to Display**:
- PID
- Process Name
- Connections (count)
- Send Rate (KB/s) - instantaneous
- Receive Rate (KB/s) - instantaneous
- Total Sent/Received (MB) - cumulative

**Technical Approach**:

1. **Create RealTimeNetworkDialog class**
   - QTableWidget with 6 columns
   - 1-second update timer
   - Pause/resume button
   - Color coding based on bandwidth rates

2. **Extend ProcessWorker for network rates**
   - **Challenge**: psutil does NOT provide per-process network I/O on most platforms
   - Only system-wide network I/O is available via `psutil.net_io_counters()`
   - Per-process network I/O requires platform-specific approaches:
     - **Linux**: Parse `/proc/[pid]/net/dev` (not exposed by psutil)
     - **Windows**: Use Windows Performance Counters (complex)
     - **macOS**: Limited support

3. **Fallback Strategy** (Cross-Platform):
   - **Display connection count** (already implemented, works cross-platform)
   - **Display protocol types** (TCP, UDP)
   - **Display remote addresses** (top 3 connections per process)
   - **Show connection states** (ESTABLISHED, LISTEN, etc.)
   - **Estimate activity** based on connection changes over time

4. **Enhanced Data Dictionary** (without bandwidth):
   ```python
   {
     'pid': int,
     'name': str,
     'connections': int,
     'tcp_connections': int,
     'udp_connections': int,
     'top_remotes': list,        # Top 3 remote IPs/ports
     'established_count': int,
     'listen_count': int
   }
   ```

5. **Alternative: Linux-Specific Bandwidth** (Phase 3b - Optional):
   - If on Linux, attempt to read `/proc/[pid]/net/dev`
   - Gracefully fall back to connection-only view on other platforms
   - Add platform detection and conditional logic

6. **Replace double-click handler**:
   ```python
   # Line 767-768, change from:
   lambda evt: self.show_top_processes('network') if evt.double() else None
   # To:
   lambda evt: self.show_realtime_network() if evt.double() else None
   ```

7. **Color Coding Logic**:
   - Red: > 50 connections
   - Yellow: 10-50 connections
   - Green: < 10 connections

**Files Modified**:
- `src/sysmon.py`: Add RealTimeNetworkDialog class
- `src/sysmon.py`: Extend ProcessWorker for enhanced network metrics
- `src/sysmon.py`: Add show_realtime_network() method
- `src/sysmon.py`: Update network plot double-click handler

**Challenges**:
- Per-process bandwidth not available cross-platform
- May need to settle for enhanced connection information instead of true bandwidth
- Consider Linux-specific implementation in future enhancement

---

## Architecture Design

### ProcessWorker Modifications

**Current Structure**:
```python
class ProcessWorker(QObject):
    def __init__(self, metric_type):  # 'cpu', 'disk', 'network'
        self.metric_type = metric_type

    def run(self):
        # Collect data based on metric_type
        # Return top 10 processes
```

**Enhanced Structure**:
```python
class ProcessWorker(QObject):
    def __init__(self, metric_type, calculate_rates=False, prev_state=None):
        self.metric_type = metric_type
        self.calculate_rates = calculate_rates  # For disk/network rate calculations
        self.prev_state = prev_state or {}      # Previous counters for delta calculation
        self.current_time = time.time()

    def run(self):
        if self.metric_type == 'cpu':
            return self._collect_cpu_data()
        elif self.metric_type == 'disk' and self.calculate_rates:
            return self._collect_disk_rates()
        elif self.metric_type == 'network':
            return self._collect_network_data()
        # ... existing logic ...

    def _collect_disk_rates(self):
        current_data = {}
        time_delta = time.time() - self.current_time

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                io = proc.io_counters()

                if pid in self.prev_state:
                    prev = self.prev_state[pid]
                    read_rate = (io.read_bytes - prev.read_bytes) / time_delta / (1024**2)
                    write_rate = (io.write_bytes - prev.write_bytes) / time_delta / (1024**2)
                else:
                    read_rate = write_rate = 0.0

                current_data[pid] = {
                    'pid': pid,
                    'name': proc.info['name'],
                    'read_rate': read_rate,
                    'write_rate': write_rate,
                    'io_counters': io  # Store for next iteration
                }
            except:
                pass

        return current_data
```

### Dialog Base Class Pattern

**Option 1: Create RealTimeDialogBase** (Recommended)
```python
class RealTimeDialogBase(QDialog):
    """Base class for real-time process monitoring dialogs"""

    def __init__(self, parent, metric_type, columns):
        self.metric_type = metric_type
        self.columns = columns
        self.prev_state = {}  # For rate calculations

        self.setup_ui()
        self.position_dialog_intelligently()
        self.start_real_time_updates()

    def setup_ui(self):
        # Common UI elements: table, pause button, status label
        # Subclasses customize columns

    def refresh_data(self):
        # Create ProcessWorker with prev_state
        # Update prev_state on completion

    def update_table(self, data):
        # Populate table with data
        # Apply color coding (subclass-specific)
```

**Option 2: Generalize RealTimeProcessDialog** (Simpler)
- Rename to RealTimeMonitorDialog
- Add metric_type parameter
- Dynamically configure columns based on metric_type
- Single dialog class handles all three types

---

## Implementation Sequence

### Phase 1: CPU Enhancement (1-2 hours)
1. Add memory_percent to ProcessWorker CPU data collection
2. Add 4th column to RealTimeProcessDialog table
3. Implement column sorting (QTableWidget.setSortingEnabled)
4. Add filter text box and filtering logic
5. Test and verify

### Phase 2: Disk I/O Dialog (3-4 hours)
1. Create RealTimeDiskDialog class (copy/modify from CPU dialog)
2. Implement ProcessWorker._collect_disk_rates() method
3. Add prev_state management to maintain I/O counter deltas
4. Update show_realtime_disk() method
5. Change disk plot double-click handler
6. Implement disk-specific color coding
7. Test with real disk I/O activity

### Phase 3: Network Dialog (3-4 hours)
1. Create RealTimeNetworkDialog class
2. Implement ProcessWorker._collect_network_data() with enhanced metrics
3. Add show_realtime_network() method
4. Change network plot double-click handler
5. Implement network-specific color coding
6. Test with various network activities
7. Document cross-platform limitations (no per-process bandwidth)

### Optional Phase 3b: Linux Network Bandwidth (2-3 hours)
1. Detect Linux platform
2. Implement /proc/[pid]/net/dev parsing
3. Calculate send/receive rates
4. Add bandwidth columns conditionally
5. Test on Linux systems

---

## Critical Files to Modify

**Main File**: `/home/juren/Projects/system-monitor/src/sysmon.py`

**Sections to Modify**:
1. **Lines 235-342**: ProcessWorker class
   - Add calculate_rates parameter
   - Add prev_state handling
   - Implement _collect_disk_rates() method
   - Enhance _collect_network_data() method

2. **Lines 369-586**: RealTimeProcessDialog class (CPU)
   - Add memory column
   - Add sorting capability
   - Add filtering

3. **After line 586**: Add RealTimeDiskDialog class (~200 lines)

4. **After RealTimeDiskDialog**: Add RealTimeNetworkDialog class (~200 lines)

5. **Lines 2216-2220**: show_realtime_processes() method
   - Enhance for CPU improvements

6. **New method after line 2220**: show_realtime_disk() (~20 lines)

7. **New method**: show_realtime_network() (~20 lines)

8. **Line 754-755**: Disk plot double-click handler (change to show_realtime_disk)

9. **Line 767-768**: Network plot double-click handler (change to show_realtime_network)

**Estimated Code Addition**: ~500-600 lines
**Estimated Code Modification**: ~100-150 lines
**Total Impact**: ~700 lines (manageable, keeps codebase reasonable)

---

## Technical Challenges and Solutions

### Challenge 1: Maintaining State Between Updates
**Problem**: Need previous I/O counters to calculate rates
**Solution**: Store prev_state in dialog, pass to each ProcessWorker instance

### Challenge 2: Processes Starting/Stopping
**Problem**: Process may not exist in prev_state (newly started)
**Solution**: Gracefully handle missing prev_state entries, show 0 rate for first update

### Challenge 3: Per-Process Network Bandwidth
**Problem**: Not available cross-platform via psutil
**Solution**:
- Primary: Enhanced connection information (counts, protocols, states)
- Optional: Linux-specific implementation for true bandwidth

### Challenge 4: Performance with Many Processes
**Problem**: Scanning 200 processes every second
**Solution**:
- Keep 200 process limit
- Use cached values where possible
- Consider increasing update interval to 2 seconds for disk/network if needed

### Challenge 5: Thread Management
**Problem**: Creating new thread every refresh is inefficient
**Solution**: Consider persistent worker threads in future optimization

---

## User Experience Flow

### Current Flow (Disk/Network):
```
User double-clicks Disk graph
    → Progress dialog appears
    → Background scan completes
    → Static dialog shows snapshot
    → Data is already stale
```

### New Flow (All Graphs):
```
User double-clicks any graph
    → Real-time dialog appears immediately
    → Live updates every 1 second
    → Color-coded for quick identification
    → Sortable columns
    → Pause/resume control
    → Always showing current state
```

---

## Testing Strategy

### Phase 1 (CPU):
- Verify memory column displays correctly
- Test sorting by each column
- Test filtering with various search terms
- Verify color coding still works

### Phase 2 (Disk):
- Generate disk I/O activity (large file copy, compile, etc.)
- Verify read/write rates update in real-time
- Check rate calculations are accurate
- Test color coding thresholds
- Verify processes appear/disappear correctly

### Phase 3 (Network):
- Generate network activity (downloads, streaming, etc.)
- Verify connection counts update
- Check protocol breakdown
- Test remote address display
- Verify color coding

---

## Success Criteria

1. ✅ All three drill-down dialogs show real-time data
2. ✅ Disk I/O shows read/write rates (MB/s)
3. ✅ Network shows connection count and enhanced metrics
4. ✅ All dialogs have pause/resume capability
5. ✅ Color coding provides quick visual feedback
6. ✅ Dialogs position intelligently
7. ✅ Codebase remains manageable (~700 line addition)
8. ✅ Cross-platform compatibility maintained

---

## Future Enhancements (Not in Scope)

1. Export drill-down data to CSV
2. Historical graphs within drill-down dialogs
3. Process kill/suspend capability from dialogs
4. Alert thresholds with notifications
5. Per-process network bandwidth on all platforms
6. Thread pooling for worker management
7. Configurable update intervals per dialog

---

## Notes

- Keep existing static dialogs as fallback (don't delete ProcessInfoDialog yet)
- Consider adding preference to choose between static and real-time
- Document platform-specific limitations in help system
- Add tooltips explaining metrics in dialogs
