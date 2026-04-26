import cv2
from ultralytics import YOLO
import json
from datetime import datetime

OUTPUT_FILE = "hardware/drivers/vision_latest.json"

model = YOLO("yolov8n.pt")

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("[Vision] Cannot open camera")
        return

    print("[Vision] Running — press Q to quit\n")

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            results = model(frame, classes=[0], verbose=False)
            count = len(results[0].boxes)

            # Draw bounding boxes
            annotated = results[0].plot()

            # Overlay count on screen
            cv2.putText(
                annotated,
                f"People: {count}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

            cv2.imshow("Queue Predictor — Live View", annotated)

            # Write to JSON every 30 frames
            frame_count += 1
            if frame_count % 30 == 0:
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "people_in_frame": count,
                    "note": "YOLOv8 nano — Logitech webcam",
                }
                print(json.dumps(payload))
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(payload, f, indent=2)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()