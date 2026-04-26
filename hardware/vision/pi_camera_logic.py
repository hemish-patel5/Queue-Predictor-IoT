
import cv2
from ultralytics import YOLO
import json
import os
import paho.mqtt.client as mqtt
from datetime import datetime
 
# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = 'mqtt.thingsboard.cloud'
ACCESS_TOKEN = 'za6axxlrmmx1wsna0cz8'
 
# --- Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "../../hardware/drivers/vision_latest.json")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
 
# Load YOLO Model
print("[Vision] Loading YOLOv8 Nano...")
model = YOLO("yolov8n.pt").to('cpu')
 
def main():
    # --- MQTT Setup ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("[MQTT] Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"[MQTT] Failed to connect: {e}")
        return
 
    # --- Camera Setup ---
    # Index 1 for USB webcam on Pi
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
 
    if not cap.isOpened():
        print("[Vision] Error: Could not open camera.")
        return
 
    print("[Vision] Running. Sending 'people_in_frame' to ThingsBoard...")
    frame_count = 0
 
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
 
            # Run detection (class 0 is 'person')
            results = model(frame, classes=[0], verbose=False)
            count = len(results[0].boxes)
 
            # Draw UI for local display
            annotated_frame = results[0].plot()
            cv2.putText(
                annotated_frame,
                f"People Count: {count}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
 
            # Show window
            cv2.imshow("Queue Predictor - Live View", annotated_frame)
            print(f"Current Count: {count} | Frames: {frame_count}", end="\r")
 
            # Send Telemetry & Save JSON every 30 frames
            frame_count += 1
            if frame_count % 30 == 0:
                # Telemetry payload with ONLY people_in_frame
                payload = {
                    "people_in_frame": count
                }
                # 1. Send to ThingsBoard
                client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)
                # 2. Save locally as backup
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(payload, f, indent=2)
                print(f"\n[Telemetry Sent] people_in_frame: {count}")
 
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
 
    except KeyboardInterrupt:
        print("\n[Vision] Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()
        cap.release()
        cv2.destroyAllWindows()
        print("[Vision] Resources Released.")
 
if __name__ == "__main__":
    main()