# python -m venv venv
# venv\Scripts\activate
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && pip install ultralytics opencv-python


import cv2
import json
import time
from datetime import datetime
from ultralytics import YOLO

OUTPUT_FILE = "hardware/vision_latest.json"

model = YOLO("yolov8n.pt")  # downloads automatically first run

def count_people(frame):
    results = model(frame, classes=[0], verbose=False)  # class 0 = person
    return len(results[0].boxes)

def main():
    cap = cv2.VideoCapture(0)  # 0 = laptop webcam
    if not cap.isOpened():
        print("Cannot open webcam")
        return

    print("YOLO nano running on webcam...\n")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame read failed, retrying...")
                continue

            count = count_people(frame)
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "people_in_frame": count,
                "note": "YOLOv8 nano — anonymous detection",
            }
            print(json.dumps(payload))
            with open(OUTPUT_FILE, "w") as f:
               json.dump(payload, f, indent=2)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nCamera Stopped.")
    finally:
        cap.release()

if __name__ == "__main__":
    main()