import paho.mqtt.client as mqtt
import random
import requests
from bs4 import BeautifulSoup
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# InfluxDB Configuration
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
def main_loop():
    try:
        while True:
            send_data()
            time.sleep(5)  # Sleep for 5 seconds
    except KeyboardInterrupt:
        print("Finished")
        global reconnect
        reconnect = False
        client.disconnect()
        influx_client.close()

# Telegram Bot Configuration
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your bot. Send /help to see the list of available commands.")

async def help_command(update: Update, context: ContextTypes):
    help_text = "Available commands:\n"
    help_text += "/start - Start the bot\n"
    help_text += "/help - Show this help message\n"
    help_text += "/info - Get bot information\n"
    help_text += "/temperature - Get the current temperature"
    help_text += "/humidity - Get the current humidity"
    await update.message.reply_text(help_text)

async def info(update: Update, context: ContextTypes):
    bot_info = "Bot Name: {}\nUsername: @{}\nID: {}".format(
        context.bot.name, context.bot.username, context.bot.id)
    await update.message.reply_text(bot_info)

async def temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = generate_sensor_data()
    await update.message.reply_text(f'Temperatura actuală este: {data["temperature"]}°C')

async def humidity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = generate_sensor_data()
    await update.message.reply_text(f'Umiditatea actuală este: {data["humidity"]}%')

# Main function to run both the main loop and the Telegram bot
def main():
    # Start the main loop in a separate thread
    import threading
    threading.Thread(target=main_loop).start()

    # Set up the Telegram bot
    telegram_token = "7482201156:AAG52lN9WC6xJ0IOY0rt7w5OpYIxhFWwUDU"
    application = Application.builder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("temperature", temperature))
    application.add_handler(CommandHandler("humidity", humidity))

    # Run the Telegram bot
    application.run_polling()

if __name__ == "__main__":
    main()
