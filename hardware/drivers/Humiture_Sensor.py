#!/usr/bin/env python3
import os
import time
import paho.mqtt.client as mqtt
import json
from dotenv import load_dotenv
import adafruit_dht
import board
 
load_dotenv()


# --- ThingsBoard Configuration ---
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# --- DHT11 Configuration ---
# board.D17 corresponds to GPIO 17
dht_device = adafruit_dht.DHT11(board.D17)
 
def main():
    # Setup MQTT Client (Added API version to fix your Deprecation Warning)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(ACCESS_TOKEN)
    try:
        client.connect(THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("Connected to ThingsBoard successfully!")
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        return
 
    print("Starting DHT11 Monitoring...")
    # print(dht_device.humidity, dht_device.temperature)
    while True:
        try:
            # The library handles the complex timing logic for you
            temperature = dht_device.temperature
            humidity = dht_device.humidity
 
            if humidity is not None and temperature is not None:
                print(f"Humidity: {humidity}%, Temperature: {temperature} C")
                # Prepare and send telemetry
                payload = {
                    "temperature": temperature,
                    "humidity": humidity
                }
                client.publish('v1/devices/me/telemetry', json.dumps(payload), 1)
        except RuntimeError as error:
            # DHT sensors are notorious for timeout errors, just keep going
            # print(error.args[0])
            pass
        except Exception as error:
            dht_device.exit()
            raise error
 
        time.sleep(2.0)
 
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")