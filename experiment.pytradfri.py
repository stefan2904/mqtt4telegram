import os
import threading
import time

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

TRADFRIIP = os.getenv('TRADFRIIP')
TRADFRIidentity = os.getenv('TRADFRIidentity')
TRADFRIkey = os.getenv('TRADFRIkey')

api_factory = APIFactory(host=TRADFRIIP, psk_id=TRADFRIidentity, psk=TRADFRIkey)
api = api_factory.request

gateway = Gateway()

devices_command = gateway.get_devices()
devices_commands = api(devices_command)
devices = api(devices_commands)

devices = [dev for dev in devices if dev.has_light_control]


def printDevice(dev):
    print()
    print(dev.name)
    print('  model:     ' + dev.device_info.model_number)
    print('  id:        ' + str(dev.id))
    print('  light:     ' + str(dev.has_light_control))
    if dev.has_light_control:
        print('     Control: {}'.format(dev.light_control.raw))
        print('     lights:  {}'.format(dev.light_control.lights[0].supported_features))
        print('     state: {}'.format(dev.light_control.lights[0].state))
        print('     simmer: {}'.format(dev.light_control.lights[0].dimmer))
    print('  reachable: ' + str(dev.reachable))
    print('  last_seen: ' + str(dev.last_seen))


def report(light):
    rep = {}
    rep['name'] = light.device.name
    rep['state'] = "on" if light.state else "off"
    rep['dimmer'] = light.dimmer
    rep['hex_color'] = light.hex_color
    # f5faf6 = cold | f1e0b5 = normal | efd275 = warm
    # rep['xy_color'] = light.xy_color
    # rep['sb_xy_color'] = light.hsb_xy_color
    print(rep)


def observe(api, device):
    def callback(updated_device):
        light = updated_device.light_control.lights[0]
        print("Received message for: %s" % light)
        report(light)

    def err_callback(err):
        print(err)

    def worker():
        api(device.observe(callback, err_callback, duration=120))

    threading.Thread(target=worker, daemon=True).start()
    # print('Sleeping to start observation task')
    # time.sleep(1)
    print('Now observing ' + device.name)


def observeLight(dev):
    if dev.has_light_control:
        observe(api, dev)


for dev in devices:
    printDevice(dev)
    observeLight(dev)

print('sleeping ...')
time.sleep(120)
print('fin')
