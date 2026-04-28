#!/usr/bin/env python3
"""
Maximum Performance People Counter for Raspberry Pi 4
- Threaded frame capture (never waits for camera)
- YOLOv8 Nano with CPU optimisations
- Non-blocking MQTT publishing
"""
 
import cv2
from ultralytics import YOLO
import json
import os
import time
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
 
load_dotenv()
 
# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
 
# --- Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "../../hardware/drivers/vision_latest.json")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
 
# --- Performance Settings ---
RESOLUTION_W     = 320    # Frame width
RESOLUTION_H     = 240    # Frame height
YOLO_IMGSZ       = 320    # YOLO internal inference size
CONFIDENCE       = 0.45   # Detection confidence threshold
TELEMETRY_EVERY  = 5.0    # Send telemetry every N seconds
HEADLESS         = True   # Set False to show display (slower)
 
 
# ─────────────────────────────────────────────
#  Threaded Camera — always has the latest frame
# ─────────────────────────────────────────────
class ThreadedCamera:
    def __init__(self, index=1):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_H)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
 
        if not self.cap.isOpened():
            print(f"[Camera] Index {index} failed, trying 0...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("[Camera] No camera found.")
 
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
 
        # Start background capture thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print(f"[Camera] Started at {RESOLUTION_W}x{RESOLUTION_H}")
 
    def _capture_loop(self):
        """Continuously grab frames in background."""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
 
    def read(self):
        """Get the latest frame."""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
 
    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()
 
 
# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def main():
    # --- Load YOLO ---
    print("[Vision] Loading YOLOv8 Nano...")
    model = YOLO("yolov8n.pt")
 
    # Warm up the model so first inference is not slow
    import numpy as np
    dummy = np.zeros((RESOLUTION_H, RESOLUTION_W, 3), dtype=np.uint8)
    model(dummy, verbose=False, imgsz=YOLO_IMGSZ)
    print("[Vision] Model warmed up.")
 
    # --- MQTT Setup ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("[MQTT] Connected to ThingsBoard!")
    except Exception as e:
        print(f"[MQTT] Failed to connect: {e}")
        return
 
    # --- Camera Setup ---
    try:
        camera = ThreadedCamera(index=1)
    except RuntimeError as e:
        print(e)
        return
 
    # --- Timing ---
    last_telemetry = time.time()
    current_count = 0
    frame_times = []
 
    print("[Vision] Running... Press Ctrl+C to stop.")
 
    try:
        while True:
            loop_start = time.time()
 
            # Get latest frame from thread
            frame = camera.read()
            if frame is None:
                time.sleep(0.01)
                continue
 
            # --- YOLO Inference ---
            results = model(
                frame,
                classes=[0],       # People only
                verbose=False,
                conf=CONFIDENCE,
                imgsz=YOLO_IMGSZ
            )
            current_count = len(results[0].boxes)
 
            # --- FPS Calculation ---
            frame_time = time.time() - loop_start
            frame_times.append(frame_time)
            if len(frame_times) > 30:
                frame_times.pop(0)
            fps = 1.0 / (sum(frame_times) / len(frame_times))
 
            print(f"[Vision] People: {current_count} | FPS: {fps:.1f}", end="\r")
 
            # --- Optional Display ---
            if not HEADLESS:
                annotated = results[0].plot()
                cv2.putText(
                    annotated,
                    f"People: {current_count} | FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )
                cv2.imshow("Queue Predictor", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
 
            # --- Send Telemetry every N seconds ---
            now = time.time()
            if now - last_telemetry >= TELEMETRY_EVERY:
                payload = {"people_in_frame": current_count}
 
                # Publish to ThingsBoard
                client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)
 
                # Save locally
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(payload, f, indent=2)
 
                print(f"\n[Telemetry] Sent people_in_frame: {current_count} | FPS: {fps:.1f}")
                last_telemetry = now
 
    except KeyboardInterrupt:
        print("\n[Vision] Stopping...")
    finally:
        camera.stop()
        client.loop_stop()
        client.disconnect()
        if not HEADLESS:
            cv2.destroyAllWindows()
        print("[Vision] Done.")
 
 
if __name__ == "__main__":
    main()