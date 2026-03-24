import asyncio
from types import SimpleNamespace

import bot as bot_module
from bot import Bot
from telegram.constants import ParseMode


class SpySender:
    def __init__(self):
        self.messages = []

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)


class DummyFuture:
    def result(self, timeout=None):
        return None


def make_update(chat_id, text="", message_thread_id=None):
    message = SimpleNamespace(text=text, message_thread_id=message_thread_id)
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        effective_message=message,
        message=message,
    )


def make_context(args=None, sender=None):
    return SimpleNamespace(args=args or [], bot=sender or SpySender())


def run(coro):
    return asyncio.run(coro)


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

    run(bot.cb_start(update, context))

    assert len(sender.messages) == 2
    assert "I am alive at" in sender.messages[0]["text"]
    assert "You are this bots admin!" == sender.messages[1]["text"]


def test_cb_start_sends_only_greeting_for_non_owner():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(sender=sender)

    run(bot.cb_start(update, context))

    assert len(sender.messages) == 1
    assert "I am alive at" in sender.messages[0]["text"]


def test_cb_help_rejects_non_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(sender=sender)

    result = run(bot.cb_help(update, context))

    assert result is False
    assert sender.messages[0]["text"] == "ERROR: You are not this bots admin!"


def test_cb_help_lists_available_commands_for_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(sender=sender)

    run(bot.cb_help(update, context))

    message = sender.messages[0]["text"]
    assert "Available commands:" in message
    assert "/start" in message
    assert "/mqtt" in message
    assert "/help" in message
    assert "/version" in message
    assert "message_thread_id" in message
    assert "core.telegram.org/bots/api#sendmessage" in message


def test_cb_version_rejects_non_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(sender=sender)

    result = run(bot.cb_version(update, context))

    assert result is False
    assert sender.messages[0]["text"] == "ERROR: You are not this bots admin!"


def test_cb_version_lists_dependency_versions_for_admin(monkeypatch):
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(sender=sender)

    monkeypatch.setattr(bot, "_get_dependency_versions", lambda: [("pytest", "8.4.0"), ("requests", None)])

    run(bot.cb_version(update, context))

    message = sender.messages[0]["text"]
    assert "Installed dependency versions (requirements.txt):" in message
    assert "- pytest: 8.4.0" in message
    assert "- requests: NOT INSTALLED" in message


def test_cb_mqtt_rejects_non_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(7)
    context = make_context(args=["topic", "payload"], sender=sender)

    result = run(bot.cb_mqtt(update, context))

    assert result is False
    assert sender.messages[0]["text"] == "ERROR: You are not this bots admin!"


def test_cb_mqtt_requires_topic_and_payload():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["only-topic"], sender=sender)

    result = run(bot.cb_mqtt(update, context))

    assert result is False
    assert "Usage:" in sender.messages[0]["text"]
    assert sender.messages[0]["parse_mode"] == ParseMode.MARKDOWN


def test_cb_mqtt_prefixes_topic_with_telegram_for_admin():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["lights/kitchen", "on"], sender=sender)

    published = []
    bot.set_mqtt_publisher(lambda topic, payload: published.append((topic, payload)))

    run(bot.cb_mqtt(update, context))

    assert sender.messages[0]["text"] == "Send to topic (telegram/lights/kitchen): on"
    assert sender.messages[1]["text"] == "MQTT message published."
    assert published == [("telegram/lights/kitchen", "on")]


def test_cb_mqtt_replies_to_same_message_thread_when_available():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42, message_thread_id=99)
    context = make_context(args=["lights/kitchen", "on"], sender=sender)

    published = []
    bot.set_mqtt_publisher(lambda topic, payload: published.append((topic, payload)))

    run(bot.cb_mqtt(update, context))

    assert sender.messages[0]["message_thread_id"] == 99
    assert sender.messages[1]["message_thread_id"] == 99
    assert published == [("telegram/lights/kitchen", "on")]


def test_cb_mqtt_keeps_existing_telegram_prefix():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["telegram/lights/kitchen", "on", "now"], sender=sender)

    published = []
    bot.set_mqtt_publisher(lambda topic, payload: published.append((topic, payload)))

    run(bot.cb_mqtt(update, context))

    assert sender.messages[0]["text"] == "Send to topic (telegram/lights/kitchen): on now"
    assert published == [("telegram/lights/kitchen", "on now")]


def test_cb_mqtt_fails_when_publisher_is_missing():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42)
    context = make_context(args=["lights/kitchen", "on"], sender=sender)

    result = run(bot.cb_mqtt(update, context))

    assert result is False
    assert sender.messages[1]["text"] == "ERROR: MQTT publisher is not configured."


def test_cb_unknown_echoes_unrecognized_message():
    bot = Bot(OWNERID=42)
    sender = SpySender()
    update = make_update(42, text="/whoami")
    context = make_context(sender=sender)

    run(bot.cb_unknown(update, context))

    assert sender.messages[0]["text"] == "Sorry, I didn't understand that: /whoami"


def test_sendMsgToOwner_uses_owner_id_and_html_parse_mode(monkeypatch):
    bot = Bot(OWNERID=42)
    sender = SpySender()
    bot.application = SimpleNamespace(bot=sender)
    bot._loop = object()

    def fake_run_coroutine_threadsafe(coro, loop):
        run(coro)
        return DummyFuture()

    monkeypatch.setattr(bot_module.asyncio, "run_coroutine_threadsafe", fake_run_coroutine_threadsafe)

    class RunningLoop:
        def is_running(self):
            return True

    bot._loop = RunningLoop()

    bot.sendMsgToOwner("<b>hello</b>")

    assert sender.messages[0]["chat_id"] == 42
    assert sender.messages[0]["text"] == "<b>hello</b>"
    assert sender.messages[0]["parse_mode"] == ParseMode.HTML


def test_sendMsgToOwner_uses_remembered_owner_thread_id(monkeypatch):
    bot = Bot(OWNERID=42)
    sender = SpySender()
    bot.application = SimpleNamespace(bot=sender)

    def fake_run_coroutine_threadsafe(coro, loop):
        run(coro)
        return DummyFuture()

    monkeypatch.setattr(bot_module.asyncio, "run_coroutine_threadsafe", fake_run_coroutine_threadsafe)

    class RunningLoop:
        def is_running(self):
            return True

    bot._loop = RunningLoop()
    bot._remember_owner_thread(make_update(42, message_thread_id=123))

    bot.sendMsgToOwner("<b>hello</b>")

    assert sender.messages[0]["message_thread_id"] == 123
