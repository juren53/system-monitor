#!/usr/bin/python3
#---------------------sysmon.py v0.05--------------------------
# This code is a simple system monitor that displays CPU utilization, network I/O (upload and download speeds), 
# and disk I/O (read and write speeds) in real-time using psutil for system metrics, matplotlib for 
# visualization, and numpy for numerical operations.
# 
# Created Fri 08 Mar 2024 06:26:41 PM CST by JAU - 
# Modified Sat 09 Mar 2024 16:45:10 PM CST by JAU - added ver/date label & press Q to quit feature
# Modified Sun 10 Mar 2024 13:02:01 PM CDT by JAU  - added labels to across top of screen 
#   and removed tool bar at bottom of the screen
# Modified Mon 11 Mar 2024 05:51:01 AM CDT by JAU - added grid lines and decreased plot line width
# Modified Mon 18 Mar 2024 03:30:00 PM CDT - increased line width for better graph readability
# Modified Sun 17 Mar 2024 07:51:01 AM CDT by JAU - added Y axis ticks and labels to right sides of plots
# Modified Mon 18 Mar 2024 10:00:00 AM CDT - added statistical smoothing functionality (moving average and exponential)
# Modified Mon 18 Mar 2025 17:22:00 PM CDT - improved smoothing and thicker lines
#----------------------------------------------------------------
import psutil
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

import socket
import platform
import requests
import subprocess
import json


# Define the version number and release date
version_number = "0.0.5"
release_date = "2025-03-05 17:00"

hostname = socket.gethostname()
#ip_address = socket.gethostbyname(socket.gethostname())
# Try to get external IP address with error handling
try:
    response = requests.get('https://httpbin.org/ip', timeout=5)
    response.raise_for_status()  # Raise an exception for 4XX/5XX responses
    external_ip_address = response.json()['origin']
except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
    # Handle any network errors, timeouts, or invalid JSON responses
    external_ip_address = "N/A"
    print(f"Could not retrieve external IP address: {e}")

os_info = platform.system() + " " + platform.release()

output = subprocess.check_output(["hostname", "-I"]).decode()
ip_address = output.strip().split(" ")[0]

import matplotlib.pylab as pylab
params = {'legend.fontsize': 'x-small',
          'figure.figsize': (10, 5),
         'axes.labelsize': 'x-small',
         'axes.titlesize':'x-small',
         'lines.linewidth': 1.5,
         'xtick.labelsize':'x-small',
         'ytick.labelsize':'x-small'}
pylab.rcParams.update(params)
pylab.rcParams['toolbar'] = 'None'

# Smoothing functions
def moving_average(data, window_size):
    """
    Calculate the moving average of the input data.
    
    A moving average smooths data by averaging the last 'window_size' data points.
    This reduces noise and highlights trends in the data.
    
    Parameters:
    - data: numpy array of data points
    - window_size: number of data points to include in the average
    
    Returns:
    - smoothed data with the same shape as the input
    """
    if window_size < 2:  # No smoothing for window size less than 2
        return data
        
    result = np.copy(data)
    for i in range(len(data)):
        # Take the average of up to window_size previous points
        start_idx = max(0, i - window_size + 1)
        result[i] = np.mean(data[start_idx:i+1])
    return result

def exponential_smoothing(data, alpha):
    """
    Apply exponential smoothing to the input data.
    
    Exponential smoothing gives more weight to recent observations and
    progressively less weight to older observations. The parameter alpha 
    (between 0 and 1) controls the rate of weight decay.
    
    Alpha closer to 1 gives more weight to recent data (less smoothing).
    Alpha closer to 0 gives more weight to older data (more smoothing).
    
    Parameters:
    - data: numpy array of data points
    - alpha: smoothing factor (0 < alpha <= 1)
    
    Returns:
    - smoothed data with the same shape as the input
    """
    if alpha >= 1.0:  # No smoothing
        return data
        
    result = np.zeros_like(data)
    result[0] = data[0]  # First value remains the same
    
    for i in range(1, len(data)):
        # New smoothed value = alpha * current_value + (1-alpha) * previous_smoothed_value
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    
    return result


def get_cpu_usage():
    return psutil.cpu_percent(interval=.1)

def get_network_io():
    net_io_counters = psutil.net_io_counters()
    return net_io_counters.bytes_sent, net_io_counters.bytes_recv

def get_disk_io():
    disk_io_counters = psutil.disk_io_counters()
    return disk_io_counters.read_bytes, disk_io_counters.write_bytes

def on_key_press(event):
    global quit_program, smoothing_mode, window_size, alpha
    
    if event.key == 'q':
        quit_program = True
    elif event.key == 'm':
        # Toggle through smoothing modes: raw -> moving average -> exponential -> raw
        smoothing_mode = (smoothing_mode + 1) % 3
    elif event.key == '[' and smoothing_mode == 1:  # Decrease window size for moving average
        window_size = max(2, window_size - 1)
    elif event.key == ']' and smoothing_mode == 1:  # Increase window size for moving average
        window_size = min(50, window_size + 1)
    elif event.key == '-' and smoothing_mode == 2:  # Decrease alpha for exponential smoothing
        alpha = max(0.1, alpha - 0.1)
    elif event.key == '=' and smoothing_mode == 2:  # Increase alpha for exponential smoothing
        alpha = min(1.0, alpha + 0.1)


def main():
    print("System Monitor")
    print("=" * 20)

    # Initialize smoothing variables
    global smoothing_mode, window_size, alpha, quit_program
    smoothing_mode = 2  # 0: raw data, 1: moving average, 2: exponential smoothing
    window_size = 5     # Default window size for moving average
    alpha = 0.3         # Default alpha for exponential smoothing
    quit_program = False

    plt.ion()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 5))


    #fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 5), toolbar=False)
    fig.canvas.set_window_title('System Monitor')
    fig.canvas.mpl_connect('key_press_event', on_key_press)

    # Add grid lines
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)

    # Show Y-axis ticks and labels on the right side
    ax1.tick_params(axis='y', which='both', right=True, labelright=True)
    ax2.tick_params(axis='y', which='both', right=True, labelright=True)
    ax3.tick_params(axis='y', which='both', right=True, labelright=True)

    # Add a label in the upper left corner of the figure
    fig.text(0.01, 0.95, f'{hostname}     {os_info}',
             verticalalignment='top', horizontalalignment='left',
             transform=fig.transFigure, fontsize=8)

  
    # Add a label in the upper right corner of the figure
    fig.text(0.95, 0.95, f'{ip_address}    {external_ip_address}',
             verticalalignment='top', horizontalalignment='right',
             transform=fig.transFigure, fontsize=8)


    
    # Add version number and release date to the lower right corner of the figure
    fig.text(0.95, 0.01, f'Version: {version_number} | Date: {release_date}',
             verticalalignment='bottom', horizontalalignment='right',
             transform=fig.transFigure, fontsize=6)
    
    # Add text for smoothing controls
    controls_text = "Controls: [M]ode toggle | Window size: [ ] decrease, [ ] increase | Alpha: [-] decrease, [=] increase | [Q]uit"
    fig.text(0.50, 0.01, controls_text,
             verticalalignment='bottom', horizontalalignment='center',
             transform=fig.transFigure, fontsize=6)
    
    # Add text for smoothing mode and parameters
    smoothing_info_text = fig.text(0.05, 0.01, "Smoothing: Raw Data",
                           verticalalignment='bottom', horizontalalignment='left',
                           transform=fig.transFigure, fontsize=6)


    cpu_y = np.zeros(100)
    net_sent_y = np.zeros(100)
    net_recv_y = np.zeros(100)
    disk_read_y = np.zeros(100)
    disk_write_y = np.zeros(100)
    x = np.linspace(0, 99, 100)

    cpu_line, = ax1.plot(x, cpu_y)
    net_sent_line, = ax2.plot(x, net_sent_y)
    net_recv_line, = ax2.plot(x, net_recv_y)
    disk_read_line, = ax3.plot(x, disk_read_y)
    disk_write_line, = ax3.plot(x, disk_write_y)

    ax1.set_title('CPU Utilization')
    ax1.set_ylim(0, 100)
    #ax1.set_xlabel('Time')
    ax1.set_ylabel('CPU Usage (%)')

    ax2.set_title('Network I/O')
    #ax2.set_xlabel('Time')
    ax2.set_ylabel('Bytes/s')
    ax2.legend(['Upload', 'Download'], loc='upper left')
    net_io_text = ax2.text(0.5, 0.95, '', transform=ax2.transAxes, ha='center', va='top')

    ax3.set_title('Disk I/O')
    #ax3.set_xlabel('Time')
    ax3.set_ylabel('Bytes/s')
    ax3.legend(['Read', 'Write'], loc='upper left')
    disk_io_text = ax3.text(0.5, 0.95, '', transform=ax3.transAxes, ha='center', va='top')

    prev_net_sent = prev_net_recv = 0
    prev_disk_read = prev_disk_write = 0

    net_sent_history = []
    net_recv_history = []
    disk_read_history = []
    disk_write_history = []

    while True:
        if quit_program:
            plt.close(fig)
            break
            
        # Update raw data
        cpu_y = np.roll(cpu_y, -1)
        cpu_y[-1] = get_cpu_usage()
        
        # Apply smoothing if needed
        if smoothing_mode == 0:  # Raw data
            cpu_display = cpu_y
            smoothing_text = "Smoothing: Raw Data"
        elif smoothing_mode == 1:  # Moving average
            cpu_display = moving_average(cpu_y, window_size)
            smoothing_text = f"Smoothing: Moving Average (window = {window_size})"
        elif smoothing_mode == 2:  # Exponential smoothing
            cpu_display = exponential_smoothing(cpu_y, alpha)
            smoothing_text = f"Smoothing: Exponential (alpha = {alpha:.1f})"
        
        # Update smoothing info text
        smoothing_info_text.set_text(smoothing_text)
        
        # Update display
        cpu_line.set_ydata(cpu_display)

        net_sent, net_recv = get_network_io()
        net_sent_diff = net_sent - prev_net_sent
        net_recv_diff = net_recv - prev_net_recv
        prev_net_sent = net_sent
        prev_net_recv = net_recv

        net_sent_y = np.roll(net_sent_y, -1)
        net_sent_y[-1] = net_sent_diff
        net_sent_y = np.roll(net_sent_y, -1)
        net_sent_y[-1] = net_sent_diff
        net_sent_history.append(net_sent_diff)
        net_sent_history = net_sent_history[-20:]

        net_recv_y = np.roll(net_recv_y, -1)
        net_recv_y[-1] = net_recv_diff
        net_recv_history.append(net_recv_diff)
        net_recv_history = net_recv_history[-20:]

        # Apply smoothing if needed
        if smoothing_mode == 0:  # Raw data
            net_sent_display = net_sent_y
            net_recv_display = net_recv_y
        elif smoothing_mode == 1:  # Moving average
            net_sent_display = moving_average(net_sent_y, window_size)
            net_recv_display = moving_average(net_recv_y, window_size)
        elif smoothing_mode == 2:  # Exponential smoothing
            net_sent_display = exponential_smoothing(net_sent_y, alpha)
            net_recv_display = exponential_smoothing(net_recv_y, alpha)

        # Update display
        net_sent_line.set_ydata(net_sent_display)
        net_recv_line.set_ydata(net_recv_display)
        
        # Get current disk I/O information
        disk_read, disk_write = get_disk_io()
        disk_read_diff = disk_read - prev_disk_read
        disk_write_diff = disk_write - prev_disk_write
        prev_disk_read = disk_read
        prev_disk_write = disk_write

        disk_read_y = np.roll(disk_read_y, -1)
        disk_read_y[-1] = disk_read_diff
        disk_read_line.set_ydata(disk_read_y)
        disk_read_history.append(disk_read_diff)
        disk_read_history = disk_read_history[-20:]

        disk_write_y = np.roll(disk_write_y, -1)
        disk_write_y[-1] = disk_write_diff
        disk_write_line.set_ydata(disk_write_y)
        disk_write_history.append(disk_write_diff)
        disk_write_history = disk_write_history[-20:]

        # Adjust Y-axis limits dynamically based on the last 20 seconds of data
        ax2.set_ylim(0, max(max(net_sent_history), max(net_recv_history)) * 1.1)
        ax3.set_ylim(0, max(max(disk_read_history), max(disk_write_history)) * 1.1)

        from matplotlib.font_manager import FontProperties
        # Assuming net_io_text is your text object
        #font = FontProperties(family='sans serif', size=8, weight='bold')
        font = FontProperties(family='sans serif', size=8)
        net_io_text.set_fontproperties(font)
        disk_io_text.set_fontproperties(font)

        # Print current Network I/O numbers
        net_io_text.set_text(f"Upload: {net_sent_diff:.2f} B/s, Download: {net_recv_diff:.2f} B/s")

        # Print current Disk I/O numbers
        disk_io_text.set_text(f"Read: {disk_read_diff:.2f} B/s, Write: {disk_write_diff:.2f} B/s")

        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(1)

if __name__ == "__main__":
    main()
