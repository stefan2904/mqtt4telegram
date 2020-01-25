import asyncio
import logging
import os
import time

import aiohttp
from connect_box import ConnectBox
from connect_box.exceptions import ConnectBoxConnectionError

from mqtt import Mqtt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ROUTERPASSWORD = os.getenv('ROUTERPASSWORD')

BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT = int(os.getenv('MQTTPORT'))
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')

mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD, topics=[])
mqtt.waitForConnection()

mqtt.publish('failcloud/connectbot', 'Hello from experiment.mqtt4connectbox python script!')

# via https://github.com/fabaff/python-connect-box/blob/master/example.py

buffer = {}


def aliasify(dev):
    if dev.mac == '8C:45:00:69:E9:17':
        dev.hostname = 'IKEA TRADFRI'
    elif dev.mac == 'A0:28:ED:86:36:46':
        dev.hostname = 'think7plus'
    return dev


def createBuffer(devices):
    b = {}
    for dev in devices:
        b[dev.mac] = aliasify(dev)
    return b


formatDevice = lambda d: '{} ({})'.format(d.hostname, d.ip)
formatDeviceLong = lambda d: '{} ({}): {}'.format(d.hostname, d.ip, d.mac)


def sendToBroker(suffix, msg):
    mqtt.publish('failcloud/connectbot/{}'.format(suffix), msg)


def diffBuffers(oldbuffer, newbuffer):
    new = newbuffer.keys()
    old = oldbuffer.keys()
    added = new - old
    gone = old - new

    if added:
        sendToBroker('connected', '\n'.join(map(lambda mac: formatDevice(newbuffer[mac]), added)))
        print('connected: \n', '\n '.join(map(lambda mac: formatDeviceLong(newbuffer[mac]), added)))
    if gone:
        sendToBroker('disconnected', '\n'.join(map(lambda mac: formatDevice(oldbuffer[mac]), gone)))
        print('disconnected: \n ', '\n '.join(map(lambda mac: formatDeviceLong(oldbuffer[mac]), gone)))
    return (added, gone)


def report(devices):
    global buffer
    newbuffer = createBuffer(devices)
    diffBuffers(buffer, newbuffer)
    buffer = newbuffer


async def main():
    while True:
        async with aiohttp.ClientSession() as session:
            client = ConnectBox(session, ROUTERPASSWORD)

            # Print details about the connected devices
            await client.async_get_devices()
            # pprint(client.devices)
            report(client.devices)

            await client.async_close_session()


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except ConnectBoxConnectionError as e:
    logging.warn('Disconnected from Connectbox (' + str(e) + ', lets wait 10s and then reconnect.')
    time.sleep(10)
