import os
import sys

from mqtt import Mqtt

BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT = int(os.getenv('MQTTPORT'))
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')

mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD)
mqtt.waitForConnection()

mqtt.publish('failcloud/test/testPublish', 'hi hello')

