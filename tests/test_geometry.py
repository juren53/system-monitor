#!/usr/bin/env python3
import matplotlib.pyplot as plt
import json

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 2, 3])

manager = fig.canvas.manager
print(f"Manager type: {type(manager)}")
print(f"Has window: {hasattr(manager, 'window')}")

if hasattr(manager, 'window'):
    window = manager.window
    print(f"Window type: {type(window)}")
    print(f"Window attributes: {dir(window)}")
    print(f"Has wm_geometry: {hasattr(window, 'wm_geometry')}")
    
    if hasattr(window, 'wm_geometry'):
        geom = window.wm_geometry()
        print(f"Current geometry: {geom}")

def save_on_close(event):
    print("\nClosing event triggered")
    try:
        manager = fig.canvas.manager
        if hasattr(manager, 'window'):
            window = manager.window
            if hasattr(window, 'wm_geometry'):
                geom_str = window.wm_geometry()
                print(f"Geometry on close: {geom_str}")
                
                import re
                match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geom_str)
                if match:
                    width, height, x, y = map(int, match.groups())
                    config = {
                        'x': x,
                        'y': y,
                        'window_size': [width, height]
                    }
                    print(f"Config to save: {config}")
                else:
                    print(f"Failed to parse geometry: {geom_str}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

fig.canvas.mpl_connect('close_event', save_on_close)

plt.show()
