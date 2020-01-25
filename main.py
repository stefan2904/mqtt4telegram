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
        retval = ''
        for k, v in payload.items():
            retval += '\n' + k + ': ' + str(v)
        return retval
    except ValueError as e:
        logging.debug('could not decode JSON: ' + str(e))
        if type(payload) == bytes:
            return payload.decode('utf-8')
        return payload


def mqtt2telegram(topic, payload):
    topic = topic.replace('_', ' ')
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
