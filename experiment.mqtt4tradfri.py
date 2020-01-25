import json
import logging
import os
import threading
import time

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from mqtt import Mqtt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT = int(os.getenv('MQTTPORT'))
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')

TRADFRIIP = os.getenv('TRADFRIIP')
TRADFRIidentity = os.getenv('TRADFRIidentity')
TRADFRIkey = os.getenv('TRADFRIkey')


def mqttCallback(topic, payload):
    logging.info('< Received: {}: {}'.format(topic, payload))


api_factory = APIFactory(host=TRADFRIIP, psk_id=TRADFRIidentity, psk=TRADFRIkey)
api = api_factory.request

gateway = Gateway()

devices_command = gateway.get_devices()
devices_commands = api(devices_command)
devices = api(devices_commands)

devices = [dev for dev in devices if dev.has_light_control]

logging.info("Setup MQTT ...")

mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD)
mqtt.setCallback(mqttCallback)
mqtt.waitForConnection()

mqtt.publish('failcloud/test', 'Hello from python script!')


def report(light):
    rep = {}
    rep['name'] = light.device.name
    rep['id'] = light.device.id
    # rep['path'] = light.device.path
    rep['state'] = "on" if light.state else "off"
    rep['dimmer'] = light.dimmer
    rep['color'] = light.hex_color
    mqtt.publish('failcloud/tradfri', json.dumps(rep))


def observe(api, device):
    def callback(updated_device):
        light = updated_device.light_control.lights[0]
        report(light)

    def err_callback(err):
        print(err)

    def worker():
        api(device.observe(callback, err_callback, duration=60 * 5))

    threading.Thread(target=worker, daemon=True).start()

    print('Now observing ' + device.name)


def observeLight(dev):
    if dev.has_light_control:
        observe(api, dev)


while True:
    for dev in devices:
        observeLight(dev)

    print('sleeping ...')
    time.sleep(60 * 5)

#  mqtt.loop_forever()
print('fin')
