from types import SimpleNamespace

from bot import Bot


class SpySender:
    def __init__(self):
        self.messages = []

    def send_message(self, **kwargs):
        self.messages.append(kwargs)


def make_update(chat_id, text=""):
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        message=SimpleNamespace(text=text),
    )


def make_context(args=None, sender=None):
    return SimpleNamespace(args=args or [], bot=sender or SpySender())


def test_isAdmin_true_for_owner_id():
    bot = Bot(OWNERID=42)
    assert bot.isAdmin(42) is True


def test_isAdmin_false_for_other_id():
    bot = Bot(OWNERID=42)
    assert bot.isAdmin(7) is False


def test_cb_start_sends_admin_message_for_owner():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(sender=sender)

    bot.cb_start(update, context)

    assert len(sender.messages) == 2
    assert "I am alive at" in sender.messages[0]["text"]
    assert "You are this bots admin!" == sender.messages[1]["text"]


def test_cb_start_sends_only_greeting_for_non_owner():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(sender=sender)

    bot.cb_start(update, context)

    assert len(sender.messages) == 1
    assert "I am alive at" in sender.messages[0]["text"]


def test_cb_mqtt_rejects_non_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(args=["topic", "payload"], sender=sender)

    result = bot.cb_mqtt(update, context)

    assert result is False
    assert sender.messages[0]["text"] == "ERROR: You are not this bots admin!"


def test_cb_mqtt_requires_topic_and_payload():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["only-topic"], sender=sender)

    result = bot.cb_mqtt(update, context)

    assert result is False
    assert "Usage:" in sender.messages[0]["text"]


def test_cb_mqtt_prefixes_topic_with_telegram_for_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["lights/kitchen", "on"], sender=sender)

    bot.cb_mqtt(update, context)

    assert sender.messages[0]["text"] == "Send to topic (telegram/lights/kitchen): on"
    assert sender.messages[1]["text"] == "FEATURE NOT YET IMPLEMENTED!"


def test_cb_mqtt_keeps_existing_telegram_prefix():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["telegram/lights/kitchen", "on", "now"], sender=sender)

    bot.cb_mqtt(update, context)

    assert sender.messages[0]["text"] == "Send to topic (telegram/lights/kitchen): on now"


def test_cb_unknown_echoes_unrecognized_message():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42, text="/whoami")
    context = make_context(sender=sender)

    bot.cb_unknown(update, context)

    assert sender.messages[0]["text"] == "Sorry, I didn't understand that: /whoami"


def test_sendMsgToOwner_uses_owner_id_and_html_parse_mode():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    bot.updater = SimpleNamespace(bot=sender)

    bot.sendMsgToOwner("<b>hello</b>")

    assert sender.messages[0]["chat_id"] == 42
    assert sender.messages[0]["text"] == "<b>hello</b>"
    assert sender.messages[0]["parse_mode"] is not None
