from kpn_senml import *

import time
import paho.mqtt.client as mqtt
import csv

# MQTT broker settings

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_BASE_TOPIC = "iot"

# Set up MQTT broker

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

client = mqtt.Client()
client.on_connect = on_connect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Load sensors definitions from CSV

sensors = []
with open('sensors.csv') as sensorsDataFile:
    csvReader = csv.reader(sensorsDataFile)
    for row in csvReader:
        sensor = {
            'id': row[0],
            'lat': float(row[1]),
            'lon': float(row[2])
        }
        sensors.append(sensor)

print("Loaded sensors definitions :")
print(sensors)

def create_senml_pack(sensor_dict):
    sensor_bn = sensor_dict['id']
    pack = SenmlPack(sensor_bn)
    temp = SenmlRecord(SenmlNames.KPN_SENML_TEMPERATURE, unit=SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, value=23.5)
    humidity = SenmlRecord(SenmlNames.KPN_SENML_HUMIDITY, unit=SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY, value=73.5)
    latitude = SenmlRecord(SenmlNames.KPN_SENML_LATTITUDE, unit=SenmlUnits.SENML_UNIT_DEGREES_LATITUDE, value = sensor_dict['lat'])
    longitude = SenmlRecord(SenmlNames.KPN_SENML_LONGITUDE, unit=SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE, value = sensor_dict['lon'])
    pack.add(temp)
    pack.add(humidity)
    pack.add(latitude)
    pack.add(longitude)
    return pack

# cf https://www.rabbitmq.com/mqtt.html#implementation for naming rules related to RabbitMQ
for sensor_dict in sensors:
    mqtt_topic = MQTT_BROKER_BASE_TOPIC + "/" + sensor_dict['id']
    pack = create_senml_pack(sensor_dict)
    pack_as_json = pack.to_json()
    mqtt_message_info = client.publish(mqtt_topic, pack_as_json)
    print("Publishing {} to topic {}".format(pack_as_json, mqtt_topic))

# while True:
#     temp.value = temp.value + 1.1
#     door_pos.value = not door_pos.value
#     str_val.value = "test"
#     print(pack.to_json())
#     time.sleep(1)