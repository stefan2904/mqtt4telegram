import logging

import paho.mqtt.client as mqtt


class Mqtt():
    def __init__(self, host, port, username, password):
        self.host = host
        self.username = username
        self.client = mqtt.Client(client_id='mqtt4telegram.' + username + '@' + host)
        self.client.enable_logger()

        self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)

        self.callback = lambda topic, payload: None
        self.connected = False

        self.client.tls_set()
        self.client.username_pw_set(username, password)
        self.client.connect(host, port, 60)

        logging.info("MQTT initialized.")

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result code " + str(rc))
        self.callback('MQTT Status', 'Connected to Broker at {} as {}!'.format(self.host, self.username))
        if rc == 5:
            logging.error("Unauthenticated")
            self.callback('MQTT Status', 'Unauthenticated')
            return

        client.subscribe('failcloud/#')
        # self.client.subscribe('$SYS/#')
        self.connected = True

    def on_message(self, client, userdata, msg):
        if self.callback is not None:
            self.callback(msg.topic, str(msg.payload, 'utf-8'))
        else:
            logging.info(msg.topic + ": " + str(msg.payload, 'utf-8'))

    def loop_forever(self):
        self.client.loop_forever()

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

    def loop(self):
        self.client.loop()

    def waitForConnection(self):
        while not self.connected:
            self.loop()

    def publish(self, topic, payload):
        self.client.publish(topic, payload, 0)
        logging.info('> Published: {}: {}'.format(topic, payload))

    def setCallback(self, cb):
        self.callback = cb

    def disconnect(self):
        self.client.disconnect()
