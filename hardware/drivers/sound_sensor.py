import time
import json
import random
from datetime import datetime

OUTPUT_FILE = "hardware/sound_latest.json"

_sim_noise = 20.0

def read_simulated():
    global _sim_noise
    _sim_noise += random.uniform(-5, 5)
    _sim_noise = max(0.0, min(100.0, _sim_noise))
    return round(_sim_noise)

def noise_label(level):
    if level < 30:
        return "quiet"
    elif level < 60:
        return "moderate"
    return "loud"

def main():
    print("Sound Simulation running...\n")
    try:
        while True:
            level = read_simulated()
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "noise_level_pct": level,
                "noise_level": noise_label(level),
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSound Stopped.")

if __name__ == "__main__":
    main()