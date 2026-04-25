import cv2
import json
import time
from datetime import datetime
from ultralytics import YOLO
from picamera2 import Picamera2

OUTPUT_FILE = "hardware/pi_vision_latest.json"

model = YOLO("yolov8n.pt")

def count_people(frame):
    results = model(frame, classes=[0], verbose=False)
    return len(results[0].boxes)

def main():
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    ))
    cam.start()
    time.sleep(2)  # warm up camera

    print("[Vision] YOLO nano running on Pi Camera...\n")
    try:
        while True:
            frame = cam.capture_array()

            count = count_people(frame)
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "people_in_frame": count,
                "note": "YOLOv8 nano — anonymous detection",
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
                json.dump(payload, f, indent=2)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n[Vision] Stopped.")
    finally:
        cam.stop()

if __name__ == "__main__":
    main()