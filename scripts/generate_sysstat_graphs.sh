#!/bin/bash
# Generate graphical reports from sysstat data

# Get today's day number for the log file
DAY=$(date +%d)
LOGFILE="/var/log/sysstat/sa${DAY}"
OUTPUT_DIR="${1:-./sysstat_graphs}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Generating graphs from $LOGFILE..."

# CPU utilization
echo "- CPU utilization graph..."
sadf -g "$LOGFILE" -- -u > "$OUTPUT_DIR/cpu_usage.svg"

# Memory utilization
echo "- Memory utilization graph..."
sadf -g "$LOGFILE" -- -r > "$OUTPUT_DIR/memory_usage.svg"

# Network statistics
echo "- Network statistics graph..."
sadf -g "$LOGFILE" -- -n DEV > "$OUTPUT_DIR/network_usage.svg"

# I/O transfer rates
echo "- I/O transfer rates graph..."
sadf -g "$LOGFILE" -- -b > "$OUTPUT_DIR/io_transfer.svg"

# Disk statistics
echo "- Disk statistics graph..."
sadf -g "$LOGFILE" -- -d > "$OUTPUT_DIR/disk_stats.svg"

# Load average
echo "- Load average graph..."
sadf -g "$LOGFILE" -- -q > "$OUTPUT_DIR/load_average.svg"

echo ""
echo "Graphs generated in: $OUTPUT_DIR"
echo "Open any .svg file in a web browser to view the graphs."
echo ""
echo "Available graphs:"
ls -lh "$OUTPUT_DIR"/*.svg
