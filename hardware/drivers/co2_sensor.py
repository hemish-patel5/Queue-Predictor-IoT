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

# --- Gas Sensor Configuration ---
DO = 17
GPIO.setmode(GPIO.BCM)

def setup():
    ADC.setup(0x48)
    GPIO.setup(DO, GPIO.IN)

def print_status(x):
    if x == 1:
        print('')
        print('   *********')
        print('   * Safe~ *')
        print('   *********')
        print('')
    if x == 0:
        print('')
        print('   ***************')
        print('   * Danger Gas! *')
        print('   ***************')
        print('')

def main():
    setup()

    # --- MQTT Setup ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        return

    print("Starting Gas Sensor Monitoring...")

    status = 1
    while True:
        try:
            gas_value = ADC.read(0)
            tmp = GPIO.input(DO)

            if tmp != status:
                print_status(tmp)
                status = tmp

            payload = {
                "gas_value": gas_value,
                "gas_safe": bool(tmp)
            }

            print(f"Gas Value: {gas_value} | Safe: {bool(tmp)}")
            client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(3)

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        destroy()