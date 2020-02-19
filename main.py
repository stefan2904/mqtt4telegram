import json
import logging
import os

from bot import Bot
from mqtt import Mqtt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

OWNERID = int(os.getenv('TELEGRAMOWNERID'))
TOKEN = os.getenv('TELEGRAMTOKEN')

bot = Bot(OWNERID)
bot.init(TOKEN)
bot.start()


# bot.idle()

def tryDecode(payload):
    try:
        payload = json.loads(payload)
        retval = json.dumps(payload, indent=2, sort_keys=True)
    except ValueError as e:
        logging.debug('could not decode JSON: ' + str(e))
        if type(payload) == bytes:
            return payload.decode('utf-8')
        return payload


def filter_todoist(topic, payload):
    # topic = 'failcloud/todoist/item:completed'
    topics = topic.split('/')
    action = topics[2].split(':')
    return '{}: {}'.format(action[2], payload['item']['content'])


def getFilter(topic):
    topics = topic.split('/')
    if topics[1] == 'todoist':
        return filter_todoist
    else:
        return None


def mqtt2telegram(topic, payload):
    topic = topic.replace('_', ' ')
    filter = getFilter(topic)
    if filter is not None:
        payload = filter(topic, payload)
    else:
        payload = tryDecode(payload)
    msg = """<b>mqtt2telegram:</b> <i>{}</i>
{}
            """.format(topic, payload)
    logging.info(msg)
    bot.sendMsgToOwner(msg)


BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT = int(os.getenv('MQTTPORT'))
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')

mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD)
mqtt.setCallback(mqtt2telegram)

mqtt2telegram('Status', 'Bot (re-)initialized!')

mqtt.loop_forever()

mqtt2telegram('Status', 'Bot shutdown ...')
