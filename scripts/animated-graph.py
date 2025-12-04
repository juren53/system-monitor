import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import argparse

# Function to generate random data
def generate_data():
    x = np.linspace(0, 10, 100)
    y = np.random.rand(100)
    return x, y

# Function to update plot with new data
def update(frame):
    x, y = generate_data()
    line.set_data(x, y)
    return line,

# Initialize plot
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-')

# Set plot limits
ax.set_xlim(0, 10)
ax.set_ylim(0, 1)

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description='Display animated random data plot',
    epilog='Press Q to quit the animation window')
parser.add_argument('-f', '--frequency', type=int, default=100,
                    help='Update frequency in milliseconds (default: 100)')
args = parser.parse_args()

# Create animation
ani = FuncAnimation(fig, update, frames=range(100), blit=True, interval=args.frequency)

# Show plot
plt.show()

