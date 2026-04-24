# !/usr/bin/env python3
import time
import json
import random
from datetime import datetime

OUTPUT_FILE = "hardware/humiture_latest.json"

_sim_temp = 22.0
_sim_humidity = 55.0

def read_simulated():
    global _sim_temp, _sim_humidity
    _sim_temp += random.uniform(-0.3, 0.3)
    _sim_humidity += random.uniform(-1.0, 1.0)
    _sim_temp = max(10.0, min(40.0, _sim_temp))
    _sim_humidity = max(20.0, min(90.0, _sim_humidity))
    return round(_sim_temp), round(_sim_humidity)

def comfort_label(temp, humidity):
    if 20 <= temp <= 24 and 40 <= humidity <= 60:
        return "comfortable"
    elif temp > 27 or humidity > 70:
        return "hot/humid"
    elif temp < 18:
        return "cool"
    return "acceptable"

def main():
    print("Humiture Sensor Simulation running...\n")
    try:
        while True:
            temperature, humidity = read_simulated()
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "temperature_c": temperature,
                "humidity_pct": humidity,
                "comfort": comfort_label(temperature, humidity),
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nHumiture Sensor Stopped.")

if __name__ == "__main__":
    main()