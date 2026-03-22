import os

from mqtt import Mqtt

BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT_RAW = os.getenv('MQTTPORT')
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')
TOPIC = os.getenv('MQTTTOPIC', 'failcloud/#')

missing = [
    name for name, value in {
        'MQTTHOST': BROKERHOST,
        'MQTTPORT': BROKERPORT_RAW,
        'MQTTUSERNAME': USERNAME,
        'MQTTPASSWORD': PASSWORD,
    }.items() if not value
]
if missing:
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

BROKERPORT = int(BROKERPORT_RAW)
CLIENT_ID = os.getenv('MQTTCLIENTID', f'mqtt4telegram.{USERNAME}.sub.{os.getpid()}')


def on_message(topic, payload):
    print(f"[Message] {topic}: {payload}")


mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD, topics=[TOPIC], client_id=CLIENT_ID)
mqtt.setCallback(on_message)
mqtt.waitForConnection()

print(f"Listening on {TOPIC} as {CLIENT_ID}. Press Ctrl+C to stop.")

try:
    mqtt.loop_forever()
except KeyboardInterrupt:
    mqtt.disconnect()
