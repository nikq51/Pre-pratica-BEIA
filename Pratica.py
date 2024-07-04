import paho.mqtt.client as mqtt
import random
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from influxdb_client import InfluxDBClient
import asyncio

# Configurare client InfluxDB
bucket = "Nicu"
org = "Nicu"
token = "NYCXeTVlUEgGnu9ACtfmyd2Wnpg46Zm9_uhCat3NGpcVMwH71R5C5YEcT1y3-3l9bsRSuXF0rXU21o_Fq6Ht7g=="
url = "http://localhost:8086"

influx_client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# MQTT Configuration
MQTT_ip = "mqtt.beia-telemetrie.ro"
MQTT_port = 1883
MQTT_topic = "/training/device/nicu-busuioc/"
reconnect = True

client = mqtt.Client()

# MQTT Callbacks
def on_disconnect(client, userdata, rc):
    global reconnect
    if reconnect:
        print("Disconnected, attempting to reconnect...")
        while True:
            try:
                client.reconnect()
                print("Reconnected")
                break
            except:
                print("Reconnect failed, retrying in 5 seconds...")
                time.sleep(5)

client.on_disconnect = on_disconnect
client.connect(MQTT_ip, MQTT_port, 60)

# Function to generate random sensor data
def generate_sensor_data():
    humidity = round(random.uniform(0, 100), 2)
    temperature = round(random.uniform(0, 40), 2)
    return {
        "temperature": temperature,
        "humidity": humidity
    }

# Function to publish data to MQTT
def publish_data(client, topic, data):
    payload = json.dumps(data)
    client.publish(topic, payload)

# Function to send data to both MQTT and InfluxDB
def send_data():
    data = generate_sensor_data()
    publish_data(client, MQTT_topic, data)
    print(f"Published to MQTT: {data}")

    point = influxdb_client.Point("measurement")\
        .tag("building", "Trade Center")\
        .field("temperature", data["temperature"])\
        .field("humidity", data["humidity"])
    write_api.write(bucket=bucket, org=org, record=point)
    print(f"Written to InfluxDB: {point}")

# Main loop to publish data periodically
try:
    while True:
        send_data()
        time.sleep(5)  # Sleep for 5 seconds
except KeyboardInterrupt:
    print("Finished")
    reconnect = False
    client.disconnect()
    influx_client.close()

# Funcție de callback pentru comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! What information would you like to know?")

# Funcție de callback pentru comanda /temperature
async def temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temperature, _ = generate_sensor_data()
    await update.message.reply_text(f'Temperatura actuală este: {temperature}°C')

# Funcție de callback pentru comanda /humidity
async def humidity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, humidity = generate_sensor_data()
    await update.message.reply_text(f'Umiditatea actuală este: {humidity}%')

# Configurare bot Telegram
telegram_token = "7482201156:AAG52lN9WC6xJ0IOY0rt7w5OpYIxhFWwUDU"
application = Application.builder().token(telegram_token).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("temperature", temperature))
application.add_handler(CommandHandler("humidity", humidity))

# Pornire bot
application.run_polling()
