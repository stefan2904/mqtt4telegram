import logging

import paho.mqtt.client as mqtt


class Mqtt():
    def __init__(self, host, port, username, password):
        self.client = mqtt.Client(client_id='mqtt4telegram')
        self.client.enable_logger()

        self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)

        self.client.tls_set()
        self.client.username_pw_set(username, password)
        self.client.connect(host, port, 60)

        self.callback = None

        logging.info("MQTT initialized.")

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result code " + str(rc))
        if rc == 5:
            logging.error("Unauthenticated")
            return

        self.client.subscribe('failcloud/#')
        # self.client.subscribe('$SYS/#')

    def on_message(self, client, userdata, msg):
        if self.callback is not None:
            self.callback(msg.topic, str(msg.payload, 'utf-8'))
        else:
            logging.info(msg.topic + ": " + str(msg.payload, 'utf-8'))

    def loop_forever(self):
        self.client.loop_forever()

    def setCallback(self, cb):
        self.callback = cb
