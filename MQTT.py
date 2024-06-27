import paho.mqtt.client as mqtt
import random
import time
import json

# MQTT Configuration
MQTT_ip = "82.78.81.188"  # Server
MQTT_port = 1883
MQTT_topic = "/training/device/nicu-busuioc/data"  # Topic

# Function to generate pressure data
def generate_pressure_data():
    pressure = random.uniform(980, 1020)  # Range: 980 to 1020 hPa
    return round(pressure, 2)  # Round to two decimal places

# Publish function
def publish_data(client, topic, data):
    payload = json.dumps(data)
    client.publish(topic, payload)

# Client configuration
client = mqtt.Client()
client.connect(MQTT_ip, MQTT_port)

# Publishing the data
try:
    while True:
        pressure = generate_pressure_data()
        data = {
            "sensor_id": "sensor2",
            "pressure": pressure
        }
        print(f"Publishing data: {data}")
        publish_data(client, MQTT_topic, data)
        time.sleep(10)  # Sleep 10 seconds
except KeyboardInterrupt:
    print("Finished")
    client.disconnect()
