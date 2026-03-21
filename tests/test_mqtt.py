from types import SimpleNamespace

import mqtt as mqtt_module


class FakeClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.logger_enabled = False
        self.username_password = None
        self.connect_args = None
        self.tls_enabled = False
        self.subscriptions = []
        self.published = []
        self.disconnected = False
        self.loop_forever_called = False
        self.loop_start_called = False
        self.loop_stop_called = False
        self.loop_called = False

        self.on_connect = None
        self.on_message = None

    def enable_logger(self):
        self.logger_enabled = True

    def tls_set(self):
        self.tls_enabled = True

    def username_pw_set(self, username, password):
        self.username_password = (username, password)

    def connect(self, host, port, keepalive):
        self.connect_args = (host, port, keepalive)

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos, retain))

    def disconnect(self):
        self.disconnected = True

    def loop_forever(self):
        self.loop_forever_called = True

    def loop_start(self):
        self.loop_start_called = True

    def loop_stop(self):
        self.loop_stop_called = True

    def loop(self):
        self.loop_called = True


def make_mqtt(monkeypatch, topics=None):
    created = {}

    def factory(client_id):
        created["client"] = FakeClient(client_id)
        return created["client"]

    monkeypatch.setattr(mqtt_module.mqtt, "Client", factory)
    wrapper = mqtt_module.Mqtt("broker.local", 1883, "alice", "secret", topics=topics or ["failcloud/#"])
    return wrapper, created["client"]


def test_init_configures_client(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)

    assert client.client_id == "mqtt4telegram.alice"
    assert client.logger_enabled is True
    assert client.tls_enabled is True
    assert client.username_password == ("alice", "secret")
    assert client.connect_args == ("broker.local", 1883, 60)
    assert callable(client.on_connect)
    assert callable(client.on_message)
    assert wrapper.connected is False


def test_on_connect_subscribes_topics_and_marks_connected(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch, topics=["a/#", "b/#"])
    seen = []
    wrapper.setCallback(lambda topic, payload: seen.append((topic, payload)))

    wrapper.on_connect(client, None, None, 0)

    assert client.subscriptions == ["a/#", "b/#"]
    assert wrapper.connected is True
    assert seen[0] == ("MQTT Status", "Connected to Broker at broker.local as alice!")


def test_on_connect_with_rc5_reports_unauthenticated(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)
    seen = []
    wrapper.setCallback(lambda topic, payload: seen.append((topic, payload)))

    wrapper.on_connect(client, None, None, 5)

    assert wrapper.connected is False
    assert seen[-1] == ("MQTT Status", "Unauthenticated")


def test_on_message_forwards_non_retain_messages(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)
    seen = []
    wrapper.setCallback(lambda topic, payload: seen.append((topic, payload)))

    msg = SimpleNamespace(topic="failcloud/x", payload=b"hello", retain=False)
    wrapper.on_message(client, None, msg)

    assert seen == [("failcloud/x", "hello")]


def test_on_message_ignores_retain_when_callback_set(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)
    seen = []
    wrapper.setCallback(lambda topic, payload: seen.append((topic, payload)))

    msg = SimpleNamespace(topic="failcloud/x", payload=b"hello", retain=True)
    wrapper.on_message(client, None, msg)

    assert seen == []


def test_publish_delegates_to_client(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)

    wrapper.publish("topic/a", "payload", retain=True)

    assert client.published == [("topic/a", "payload", 0, True)]


def test_loop_methods_and_disconnect_delegate_to_client(monkeypatch):
    wrapper, client = make_mqtt(monkeypatch)

    wrapper.loop_forever()
    wrapper.loop_start()
    wrapper.loop_stop()
    wrapper.loop()
    wrapper.disconnect()

    assert client.loop_forever_called is True
    assert client.loop_start_called is True
    assert client.loop_stop_called is True
    assert client.loop_called is True
    assert client.disconnected is True
