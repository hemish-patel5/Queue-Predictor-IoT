import time
import json
from datetime import datetime

SENSOR_FILES = {
    "humiture": "hardware/humiture_latest.json",
    "co2":      "hardware/co2_latest.json",
    "sound":    "hardware/sound_latest.json",
    "pir":      "hardware/pir_latest.json",
    "vision":   "hardware/vision_latest.json",
}

OUTPUT_FILE = "backend/logic/fused_state.json"


def load(key):
    try:
        with open(SENSOR_FILES[key]) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def crowd_level(occupancy):
    if occupancy <= 3:
        return "empty"
    elif occupancy <= 8:
        return "light"
    elif occupancy <= 15:
        return "moderate"
    elif occupancy <= 25:
        return "busy"
    return "very_busy"


def main():
    print("[Fusion] Running...\n")
    try:
        while True:
            humiture = load("humiture")
            co2      = load("co2")
            sound    = load("sound")
            pir      = load("pir")
            vision   = load("vision")

            # Prefer vision count over PIR if available
            if vision:
                occupancy = vision.get("people_in_frame", 0)
                count_source = "vision"
            elif pir:
                occupancy = pir.get("occupancy", 0)
                count_source = "pir"
            else:
                occupancy = 0
                count_source = "none"

            state = {
                "timestamp":          datetime.utcnow().isoformat(),
                "occupancy":          occupancy,
                "count_source":       count_source,
                "estimated_wait_min": round(occupancy * 1.5),
                "crowd_level":        crowd_level(occupancy),
                "temperature_c":      humiture.get("temperature_c")  if humiture else None,
                "humidity_pct":       humiture.get("humidity_pct")   if humiture else None,
                "comfort":            humiture.get("comfort")         if humiture else None,
                "co2_ppm":            co2.get("co2_ppm")             if co2      else None,
                "air_quality":        co2.get("air_quality")         if co2      else None,
                "noise_level":        sound.get("noise_level")       if sound    else None,
                "sensor_health": {
                    "humiture": "ok" if humiture else "missing",
                    "co2":      "ok" if co2      else "missing",
                    "sound":    "ok" if sound    else "missing",
                    "pir":      "ok" if pir      else "missing",
                    "vision":   "ok" if vision   else "missing",
                }
            }

            print(json.dumps(state, indent=2))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(state, f, indent=2)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Fusion] Stopped.")


if __name__ == "__main__":
    main()