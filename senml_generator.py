from kpn_senml import *

import time
import paho.mqtt.client as mqtt
import csv
import openaq
from datetime import datetime
from dateutil import parser

# MQTT broker settings

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_BASE_TOPIC = "iot"
MQTT_BROKER_LOGIN = "guest"
MQTT_BROKER_PWD = "guest"

# Set up MQTT broker

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

client = mqtt.Client()
client.username_pw_set(MQTT_BROKER_LOGIN, MQTT_BROKER_PWD)
client.on_connect = on_connect

# Experiment when OpenAQ API

def load_aq_sensors_definitions():
    sensors_definitions = []
    with open('open_aq_locations.csv') as locationsAndParameters:
        csvReader = csv.reader(locationsAndParameters)
        for row in csvReader:
            sensor = {
                'id': row[0],
                'name': row[1],
                'lat': float(row[2]),
                'lon': float(row[3]),
                'rawParameters': row[4]
            }
            sensors_definitions.append(sensor)
    return sensors_definitions

sensors_definitions = load_aq_sensors_definitions()
print("Loaded sensors definitions : {}".format(sensors_definitions))

api = openaq.OpenAQ()
#resp = api.cities(df=True, limit=10000)
#print (resp.query("country == 'FR'"))

def create_senml_pack(sensor_dict):
    sensor_bn = sensor_dict['id'] + ":" + sensor_dict['name']
    pack = SenmlPack(sensor_bn)
    latitude = SenmlRecord(SenmlNames.KPN_SENML_LATTITUDE, unit=SenmlUnits.SENML_UNIT_DEGREES_LATITUDE, value = sensor_dict['lat'])
    longitude = SenmlRecord(SenmlNames.KPN_SENML_LONGITUDE, unit=SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE, value = sensor_dict['lon'])
    pack.add(latitude)
    pack.add(longitude)
    for parameter in sensor_dict['rawParameters'].split(";"):
        print("Retrieving latest value for location {} and parameter {}".format(sensor_dict['id'], parameter))
        status, response = api.latest(location=sensor_dict['id'], parameter=parameter, df=False)
        print("Received raw data : {}".format(response))
        measure = response['results'][0]['measurements'][0]
        last_updated = measure['lastUpdated']
        last_updated_time = parser.isoparse(last_updated)
        value = measure['value']
        unit = measure['unit']
        print("Got new measure {} {} at {}".format(value, unit, last_updated))
        record = SenmlRecord(parameter, unit=unit, value=value, time = datetime.timestamp(last_updated_time))
        pack.add(record)
    return pack

def publist_mqtt_message(sensor_id, senml_message):
    # cf https://www.rabbitmq.com/mqtt.html#implementation for naming rules related to RabbitMQ
    mqtt_topic = MQTT_BROKER_BASE_TOPIC + "/" + sensor_id
    mqtt_message_info = client.publish(mqtt_topic, senml_message)
    print("Published message {} to topic {}".format(senml_message, mqtt_topic))

while True:
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    for sensor in sensors_definitions:
        pack = create_senml_pack(sensor)
        publist_mqtt_message(sensor['id'] + ":" + sensor['name'], pack.to_json())
    client.disconnect() 
    # measures are updated once per hour
    time.sleep(60 * 60)
