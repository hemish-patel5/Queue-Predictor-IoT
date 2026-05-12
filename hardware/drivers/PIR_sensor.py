import os
import time
import json
import ssl
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from pir_fsm import EventSequencer

load_dotenv()

# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# --- PIR Sensor Configuration (two sensors: entry then exit) ---
# Assumption: PIR_ENTRY_PIN is closest to the door (detects entrants first),
# PIR_EXIT_PIN is further inside and fires on people leaving the room.
# Adjust pins as needed in your hardware setup or via environment variables.
PIR_ENTRY_PIN = int(os.getenv('PIR_ENTRY_PIN', '24'))
PIR_EXIT_PIN = int(os.getenv('PIR_EXIT_PIN', '25'))

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_ENTRY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PIR_EXIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        # Use plaintext MQTT (port 1883) like other drivers (camera, sound)
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        return

    print("Starting PIR Motion Monitoring (2 sensors) ...")

    # Counters
    people_count = 0
    entry_count = 0
    exit_count = 0
    motion_count = 0
    last_event = None

    # Sequencer and timings
    SEQUENCE_WINDOW = float(os.getenv('PIR_SEQUENCE_WINDOW_SECONDS', '1.0'))
    REFRACTORY = float(os.getenv('PIR_REFRACTORY_SECONDS', '0.6'))
    PUBLISH_INTERVAL = float(os.getenv('PIR_PUBLISH_INTERVAL_SECONDS', '0.5'))

    sequencer = EventSequencer(sequence_window=SEQUENCE_WINDOW, refractory=REFRACTORY)

    last_publish = 0

    # Handlers for rising-edge callbacks
    def handle_event(sensor_label):
        nonlocal entry_count, exit_count, motion_count, last_event, last_publish
        ts = time.time()
        res = sequencer.add_event(sensor_label, ts)
        if res is None:
            return

        motion_count += 1
        if res == 'entry':
            entry_count += 1
            last_event = 'entry'
            print(f"[PIR] Entry detected. entry_count={entry_count}")
        elif res == 'exit':
            exit_count += 1
            last_event = 'exit'
            print(f"[PIR] Exit detected. exit_count={exit_count}")
        else:
            last_event = 'motion'

        # Publish per-event telemetry (no device-side people_count)
        event_payload = {
            'event_type': res,
            'ts': int(ts * 1000),
        }
        try:
            client.publish('v1/devices/me/telemetry', json.dumps(event_payload), 1)
        except Exception as e:
            print(f"MQTT publish error (event): {e}")

        # Publish cumulative counters so backend can compute authoritative people_count
        agg = {
            'motion_count': motion_count,
            'entry_count': entry_count,
            'exit_count': exit_count,
            'last_event': last_event,
        }
        try:
            client.publish('v1/devices/me/telemetry', json.dumps(agg), 1)
        except Exception as e:
            print(f"MQTT publish error (agg): {e}")

    # Setup GPIO callbacks
    DEBOUNCE_MS = int(max(50, float(os.getenv('PIR_GPIO_BOUNCE_MS', '200'))))
    try:
        GPIO.add_event_detect(PIR_ENTRY_PIN, GPIO.RISING, callback=lambda ch: handle_event('A'), bouncetime=DEBOUNCE_MS)
        GPIO.add_event_detect(PIR_EXIT_PIN, GPIO.RISING, callback=lambda ch: handle_event('B'), bouncetime=DEBOUNCE_MS)
    except Exception as e:
        print(f"GPIO add_event_detect failed: {e}")

    try:
        # Main loop: idle, callbacks handle events
        while True:
            time.sleep(1)
    finally:
        client.loop_stop()
        client.disconnect()
        GPIO.remove_event_detect(PIR_ENTRY_PIN)
        GPIO.remove_event_detect(PIR_EXIT_PIN)
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        GPIO.cleanup()