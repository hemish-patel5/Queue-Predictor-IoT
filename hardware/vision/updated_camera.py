#!/usr/bin/env python3
"""
Optimised People Counter for Raspberry Pi 4
- NCNN model format (fastest on ARM)
- Threaded camera capture
- 224x224 inference size
- Frame smoothing
"""
import cv2
import numpy as np
import json
import os
import time
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from collections import deque
from ultralytics import YOLO
load_dotenv()
# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN     = os.getenv('ACCESS_TOKEN')
# --- Path Setup ---
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
NCNN_MODEL  = os.path.join(SCRIPT_DIR, "yolov8n_ncnn_model")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "../../hardware/drivers/vision_latest.json")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
# --- Performance Settings ---
RESOLUTION_W    = 320
RESOLUTION_H    = 224
INFERENCE_SIZE  = 320
CONFIDENCE      = 0.45
TELEMETRY_EVERY = 5.0
HEADLESS        = True

# ─────────────────────────────────────────────
#  Threaded Camera
# ─────────────────────────────────────────────
class ThreadedCamera:
    def __init__(self, index=1):
        self.cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_H)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        if not self.cap.isOpened():
            print("[Camera] Index 1 failed, trying 0...")
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                raise RuntimeError("[Camera] No camera found.")
        self.frame   = None
        self.lock    = threading.Lock()
        self.running = True
        self.thread  = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print(f"[Camera] Started at {RESOLUTION_W}x{RESOLUTION_H}")
    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
    def read(self):
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
    # --- Load NCNN Model ---
    if not os.path.exists(NCNN_MODEL):
        print(f"[Vision] NCNN model not found at {NCNN_MODEL}")
        print("[Vision] Export with: python3 -c \"from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='ncnn', imgsz=224)\"")
        return
    print("[Vision] Loading NCNN model...")
    model = YOLO(NCNN_MODEL, task='detect')
    # Warmup
    print("[Vision] Warming up...")
    dummy = np.zeros((RESOLUTION_H, RESOLUTION_W, 3), dtype=np.uint8)
    model(dummy, verbose=False, imgsz=INFERENCE_SIZE)
    print("[Vision] Ready.")
    # --- MQTT ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("[MQTT] Connected to ThingsBoard!")
    except Exception as e:
        print(f"[MQTT] Failed to connect: {e}")
        return
    # --- Camera ---
    try:
        camera = ThreadedCamera(index=1)
    except RuntimeError as e:
        print(e)
        return
    # --- State ---
    last_telemetry = time.time()
    count_buffer   = deque(maxlen=5)
    inference_times = deque(maxlen=30)
    print("[Vision] Running... Press Ctrl+C to stop.")
    try:
        while True:
            # Get latest frame
            frame = camera.read()
            if frame is None:
                time.sleep(0.01)
                continue
            # --- YOLO Inference ---
            t0 = time.time()
            results = model(
                frame,
                classes=[0],
                verbose=False,
                conf=CONFIDENCE,
                imgsz=INFERENCE_SIZE
            )
            inference_time = time.time() - t0
            inference_times.append(inference_time)
            # Count and smooth
            count = len(results[0].boxes)
            count_buffer.append(count)
            current_count = round(sum(count_buffer) / len(count_buffer))
            # FPS based on actual inference time
            avg_inference = sum(inference_times) / len(inference_times)
            fps = 1.0 / avg_inference
            print(f"[Vision] People: {current_count} | FPS: {fps:.1f}", end="\r")
            # Optional display
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
            # Telemetry
            now = time.time()
            if now - last_telemetry >= TELEMETRY_EVERY:
                payload = {"people_in_frame": current_count}
                client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)
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