import time
import json
import random
from datetime import datetime

OUTPUT_FILE = "hardware/co2_latest.json"

_sim_co2 = 800.0

def read_simulated():
    global _sim_co2
    _sim_co2 += random.uniform(-20, 20)
    _sim_co2 = max(400.0, min(2000.0, _sim_co2))
    return round(_sim_co2)

def air_quality_label(ppm):
    if ppm < 600:
        return "fresh"
    elif ppm < 1000:
        return "good"
    elif ppm < 1500:
        return "moderate"
    return "poor"

def main():
    print("CO2 Sensor Simulation running...\n")
    try:
        while True:
            ppm = read_simulated()
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "co2_ppm": ppm,
                "air_quality": air_quality_label(ppm),
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCO2 Sensor Stopped.")

if __name__ == "__main__":
    main()