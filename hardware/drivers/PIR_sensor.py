import time
import json
import random
from datetime import datetime

OUTPUT_FILE = "hardware/pir_latest.json"

_occupancy = 0
_entries = 0
_exits = 0

def simulate_step():
    global _occupancy, _entries, _exits
    roll = random.random()
    if roll < 0.3 and _occupancy < 30:
        _occupancy += 1
        _entries += 1
    elif roll < 0.5 and _occupancy > 0:
        _occupancy -= 1
        _exits += 1

def main():
    print("PIR Sensor Simulation running...\n")
    try:
        while True:
            simulate_step()
            estimated_wait_min = round(_occupancy * 1.5)
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "occupancy": _occupancy,
                "total_entries": _entries,
                "total_exits": _exits,
                "estimated_wait_min": estimated_wait_min,
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPIR Sensor Stopped.")

if __name__ == "__main__":
    main()