from synology_dsm import SynologyDSM

api = SynologyDSM("<IP>", "<port>", "<username>", "<password>")

# Get system info
api.information.update()
print(f"Model: {api.information.model}")
print(f"Temperature: {api.information.temperature}°C")

# Get utilization
api.utilisation.update()
print(f"CPU Load: {api.utilisation.cpu_total_load}%")
print(f"Memory Use: {api.utilisation.memory_real_usage}%")


