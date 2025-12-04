import numpy as np
import matplotlib.pyplot as plt
# Example time series data
time_series_data = np.random.rand(10) # Replace this with your actual data
# Choose a window size
window_size = 10 # Adjust based on your data
# Calculate the moving average
window = np.ones(window_size)/window_size
smoothed_data = np.convolve(time_series_data, window, 'valid')
# Plot the original and smoothed data
plt.figure(figsize=(10, 6))
plt.plot(time_series_data, label='Original Data')
plt.plot(smoothed_data, label='Smoothed Data')
plt.legend()
plt.show()

