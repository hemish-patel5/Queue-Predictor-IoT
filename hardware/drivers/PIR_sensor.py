import os
import time
import json
import ssl
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# --- Beam Break Configuration ---
BEAM_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(BEAM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    try:
        client.connect(THINGSBOARD_HOST, 8883, 60)
        client.loop_start()
        print("Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        return

    print("Starting Beam Break Monitoring...")

    count = 0
    beam_broken = False

    while True:
        try:
            current_state = GPIO.input(BEAM_PIN)

            # Detect new break event
            if current_state == 1 and not beam_broken:
                beam_broken = True
                count += 1
                print(f"Beam broken! Total count: {count}")

            elif current_state == 0:
                beam_broken = False

            payload = {
                "beam_broken": bool(current_state),
                "break_count": count,
            }

            client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(0.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        GPIO.cleanup()