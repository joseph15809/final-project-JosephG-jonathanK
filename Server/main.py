import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import deque
import os
from dotenv import load_dotenv
import numpy as np
import requests
import time

load_dotenv()
url = "http://localhost:6543/api/temperature"
BROKER = "broker.hivemq.com"
PORT = 1883
BASE_TOPIC = os.getenv("BASE_TOPIC")
TOPIC = BASE_TOPIC + "/#"

last_sent_time = 0

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when the client connects to the broker."""
    if reason_code == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe(TOPIC)
        print(f"Subscribed to {TOPIC}")
    else:
        print(f"Failed to connect with result code {reason_code}")


def on_message(client, userdata, message):
    global last_sent_time
    now = time.time()

    try:
        payload = json.loads(message.payload.decode())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mac_address = payload.get("mac_address")
        temperature = payload.get("temperature")

        if not mac_address:
            print(f"[ERROR] MAC address is missing in the payload: {payload}")
            return

        if "temperature" in payload and now - last_sent_time >= 5:
                temperature_data = {
                "mac_address": mac_address,
                "value": temperature,
                "unit": "Celsius",
                "timestamp": timestamp
            }
        response = requests.post(url, json=temperature_data)

        if response.status_code == 200:
            print(f"[{timestamp}] Sent temperature: {payload['temperature']}°C")
        else:
            print(f"[ERROR] Failed to send data to server: {response.status_code}")

        last_sent_time = now

    except json.JSONDecodeError:
        print(f"[ERROR] Received non-JSON message on {message.topic}: {message.payload.decode()}")


def main():
    # Create MQTT client
    print("Creating MQTT client...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Set callback functions
    client.on_connect = on_connect
    client.on_message = on_message


    # Set the callback functions onConnect and onMessage
    print("Setting callback functions...")
    
    try:
        # Connect to broker
        print("Connecting to broker...")
        client.connect(BROKER, PORT, 60)
        
        # Start the MQTT loop
        print("Starting MQTT loop...")
        client.loop_forever()    

    except KeyboardInterrupt:
        print("\nDisconnecting from broker...")
        # make sure to stop the loop and disconnect from the broker
        client.disconnect()
        print("Exited successfully")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()