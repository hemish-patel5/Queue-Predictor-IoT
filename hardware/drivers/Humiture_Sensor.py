#!/usr/bin/env python3
import os
import time
import json
import RPi.GPIO as GPIO
import requests
from dotenv import load_dotenv

load_dotenv()

# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
TELEMETRY_URL = f"https://{THINGSBOARD_HOST}/api/v1/{ACCESS_TOKEN}/telemetry"

# --- DHT11 Configuration ---
DHTPIN = 22
GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100
STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def send_telemetry(payload):
    try:
        response = requests.post(TELEMETRY_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"[ThingsBoard] Sent: {payload}")
        else:
            print(f"[ThingsBoard] Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ThingsBoard] Failed to send: {e}")

def read_dht11_dat():
    GPIO.setup(DHTPIN, GPIO.OUT)
    GPIO.output(DHTPIN, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(DHTPIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

    unchanged_count = 0
    last = -1
    data = []
    timeout = time.time() + 2

    while True:
        if time.time() > timeout:
            return False
        current = GPIO.input(DHTPIN)
        data.append(current)
        if last != current:
            unchanged_count = 0
            last = current
        else:
            unchanged_count += 1
            if unchanged_count > MAX_UNCHANGE_COUNT:
                break

    state = STATE_INIT_PULL_DOWN
    lengths = []
    current_length = 0

    for current in data:
        current_length += 1

        if state == STATE_INIT_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_INIT_PULL_UP
            else:
                continue
        if state == STATE_INIT_PULL_UP:
            if current == GPIO.HIGH:
                state = STATE_DATA_FIRST_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_DATA_PULL_UP
            else:
                continue
        if state == STATE_DATA_PULL_UP:
            if current == GPIO.HIGH:
                current_length = 0
                state = STATE_DATA_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_PULL_DOWN:
            if current == GPIO.LOW:
                lengths.append(current_length)
                state = STATE_DATA_PULL_UP
            else:
                continue

    if len(lengths) != 40:
        return False

    shortest_pull_up = min(lengths)
    longest_pull_up = max(lengths)
    halfway = (longest_pull_up + shortest_pull_up) / 2

    bits = []
    the_bytes = []
    byte = 0

    for length in lengths:
        bit = 0
        if length > halfway:
            bit = 1
        bits.append(bit)

    for i in range(0, len(bits)):
        byte = byte << 1
        if (bits[i]):
            byte = byte | 1
        else:
            byte = byte | 0
        if ((i + 1) % 8 == 0):
            the_bytes.append(byte)
            byte = 0

    checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
    if the_bytes[4] != checksum:
        return False

    return the_bytes[0], the_bytes[2]

def main():
    print("Raspberry Pi DHT11 Temperature & Humidity Monitor")
    print(f"Sending to: {TELEMETRY_URL}\n")

    # Send startup status
    send_telemetry({"Humiture_Status": True})

    while True:
        try:
            time.sleep(3)
            result = None
            for i in range(10):
                result = read_dht11_dat()
                if result:
                    break
                time.sleep(2)
            if result:
                humidity, temperature = result
                print(f"Humidity: {humidity}%,  Temperature: {temperature} C")

                payload = {
                    "temperature": temperature,
                    "humidity": humidity,
                    "Humiture_Status": True
                }
                send_telemetry(payload)
            else:
                print("Sensor read failed")

        except Exception as e:
            print(f"Error reading sensor: {e}")

        time.sleep(1)

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        destroy()