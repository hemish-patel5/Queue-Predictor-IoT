#!/usr/bin/env python3
import os
import time
import json
import PCF8591 as ADC
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

GPIO.setmode(GPIO.BCM)

def setup():
    ADC.setup(0x48)

def noise_label(value):
    if value < 50:
        return "loud"
    elif value < 150:
        return "moderate"
    return "quiet"

def main():
    setup()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        return

    print("Starting Sound Sensor Monitoring...")

    count = 0
    while True:
        try:
            voice_value = ADC.read(0)

            if voice_value < 50:
                count += 1

            payload = {
                "sound_value": voice_value,
                "noise_level": noise_label(voice_value),
                "trigger_count": count,
            }

            print(f"Sound Value: {voice_value} | Level: {noise_label(voice_value)} | Triggers: {count}")
            client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(0.2)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        GPIO.cleanup()