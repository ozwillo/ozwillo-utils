from kpn_senml import *

import time
import paho.mqtt.client as mqtt

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

# Create a SenML pack and records

sensor_bn = "urn:ngsi-ld:Sensor:0123-4567-8901-2345"
pack = SenmlPack(sensor_bn)
temp = SenmlRecord(SenmlNames.KPN_SENML_TEMPERATURE, unit=SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, value=23.5)
humidity = SenmlRecord(SenmlNames.KPN_SENML_HUMIDITY, unit=SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY, value=73.5)

pack.add(temp)
pack.add(humidity)

print(pack.to_json())

# Send SenML pack to MQTT broker

# cf https://www.rabbitmq.com/mqtt.html#implementation for naming rules related to RabbitMQ
mqtt_topic = MQTT_BROKER_BASE_TOPIC + "/" + sensor_bn
mqtt_message_info = client.publish(mqtt_topic, pack.to_json())
print("Published SenML message to " + mqtt_topic + ", published : " + str(mqtt_message_info.is_published()))

# while True:
#     temp.value = temp.value + 1.1
#     door_pos.value = not door_pos.value
#     str_val.value = "test"
#     print(pack.to_json())
#     time.sleep(1)