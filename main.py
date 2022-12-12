import json
import logging
import os

from bot import Bot
from mqtt import Mqtt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


if __name__ == '__main__':
    OWNERID = int(os.getenv('TELEGRAMOWNERID'))
    TOKEN = os.getenv('TELEGRAMTOKEN')

    bot = Bot(OWNERID)
    bot.init(TOKEN)
    bot.start()
    # bot.idle()


def tryDecode(topic, payload, json_as_list=True):
    try:
        payload = json.loads(payload)
        if not json_as_list:
            return json.dumps(payload, indent=2, sort_keys=True)
        else:
            if type(payload) is dict:
                # create flat key-value list based on dict (only works if depth<=1)
                lines = ['- <b>{}</b>: {}'.format(key, value) for key, value in payload.items()]
                return '\n'.join(lines)
            elif type(payload) is list:
                lines = ['- {}'.format(value) for value in payload]
                return '\n'.join(lines)

    except ValueError as e:
        logging.debug('could not decode JSON: ' + str(e))
        if type(payload) == bytes:
            return payload.decode('utf-8')
    return payload


def parser_todoist(topic, payload):
    # topic = 'failcloud/todoist/item:completed'
    topics = topic.split('/')
    logging.debug('topics: ' + str(topics))

    actions = topics[2].split(':')
    logging.debug('actions: ' + str(actions))

    action = actions[1] if len(actions) >= 2 else actions[0]
    payload = json.loads(payload)
    logging.debug('payload: ' + str(payload))

    return '{}: {}'.format(action, payload['item']['content'])


def getParser(topic):
    topics = topic.split('/')
    if len(topics) <= 1:
        return tryDecode

    if topics[1] == 'todoist':
        return parser_todoist
    else:
        return tryDecode


def mqtt2telegram(topic, payload):
    logging.debug('mqtt2telegram: ' + topic)
    topic = topic.replace('_', ' ')
    parser = getParser(topic)
    payload = parser(topic, payload)
    logging.debug('Sending to Telegram ...')
    msg = """<b>mqtt2telegram:</b> <i>{}</i>
{}
            """.format(topic, payload)
    logging.info(msg)
    bot.sendMsgToOwner(msg)


if __name__ == '__main__':
    BROKERHOST = os.getenv('MQTTHOST')
    BROKERPORT = int(os.getenv('MQTTPORT'))
    USERNAME = os.getenv('MQTTUSERNAME')
    PASSWORD = os.getenv('MQTTPASSWORD')

    mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD)
    mqtt.setCallback(mqtt2telegram)

    mqtt2telegram('Status', 'Bot (re-)initialized!')

    mqtt.loop_forever()

    mqtt2telegram('Status', 'Bot shutdown ...')
