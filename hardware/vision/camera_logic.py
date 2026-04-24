import time
import json
import random
from datetime import datetime

OUTPUT_FILE = "hardware/vision_latest.json"

_sim_people = 5.0

def read_simulated():
    global _sim_people
    _sim_people += random.uniform(-1, 1)
    _sim_people = max(0.0, min(30.0, _sim_people))
    return round(_sim_people)

def main():
    print("[Vision] Simulation running...\n")
    try:
        while True:
            count = read_simulated()
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "people_in_frame": count,
                "note": "simulated — no camera in use",
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Vision] Stopped.")

if __name__ == "__main__":
    main()