import asyncio
from importlib import metadata
import logging
from pathlib import Path
import re
import socket
import threading

from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters


class Bot():

    def __init__(self, OWNERID):
        self.OWNERID = OWNERID
        self.started = False
        self.hostname = socket.gethostname()
        self.application = None
        self._mqtt_publisher = None
        self._thread = None
        self._loop = None
        self._ready = threading.Event()
        self._startup_error = None
        logging.info("Telegram OWNERID: " + str(OWNERID))

    def isAdmin(self, ID):
        logging.debug("requested: {} ({})".format(type(ID), ID))
        logging.debug("trusted:   {} ({})".format(type(self.OWNERID), self.OWNERID))
        return ID == self.OWNERID

    async def _ensure_admin(self, update, context):
        if self.isAdmin(update.effective_chat.id):
            return True

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="ERROR: You are not this bots admin!")
        return False

    def _get_dependency_versions(self):
        requirements_path = Path(__file__).resolve().with_name('requirements.txt')
        if not requirements_path.exists():
            return None

        dependencies = []
        for raw_line in requirements_path.read_text(encoding='utf-8').splitlines():
            requirement = raw_line.split('#', 1)[0].strip()
            if not requirement:
                continue

            match = re.match(r'^([A-Za-z0-9_.-]+)', requirement)
            if match is None:
                continue

            package_name = match.group(1)
            try:
                dependencies.append((package_name, metadata.version(package_name)))
            except metadata.PackageNotFoundError:
                dependencies.append((package_name, None))

        return dependencies

    async def cb_start(self, update, context):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="I am alive at {}! And you are, {}!?".format(self.hostname,
                                                                                          str(update.effective_chat.id)))
        if self.isAdmin(update.effective_chat.id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You are this bots admin!")

    async def cb_help(self, update, context):
        if not await self._ensure_admin(update, context):
            return False

        lines = [
            "Available commands:",
            "/start - Check bot status and your chat id.",
            "/mqtt <topic> <payload> - Publish payload to an MQTT topic.",
            "/help - Show this help message.",
            "/version - Show installed versions for dependencies in requirements.txt.",
        ]
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(lines))

    async def cb_version(self, update, context):
        if not await self._ensure_admin(update, context):
            return False

        dependencies = self._get_dependency_versions()
        if dependencies is None:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='ERROR: requirements.txt not found.')
            return False

        if len(dependencies) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='No dependencies found in requirements.txt.')
            return False

        lines = ['Installed dependency versions (requirements.txt):']
        for package_name, version in dependencies:
            lines.append('- {}: {}'.format(package_name, version if version is not None else 'NOT INSTALLED'))

        await context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(lines))

    async def cb_mqtt(self, update, context):
        if not await self._ensure_admin(update, context):
            return False

        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="*Usage:* _/mqtt <topic> <payload>_",
                                           parse_mode=ParseMode.MARKDOWN)
            return False

        topic = context.args[0] if context.args[0].split('/')[0] == 'telegram' \
            else 'telegram/{}'.format(context.args[0])
        payload = ' '.join(context.args[1:])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Send to topic ({}): {}".format(topic, payload))

        if self._mqtt_publisher is None:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="ERROR: MQTT publisher is not configured.")
            return False

        try:
            self._mqtt_publisher(topic, payload)
        except Exception as e:
            logging.exception('Failed to publish MQTT message: %s', e)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="ERROR: MQTT publish failed: {}".format(str(e)))
            return False

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="MQTT message published.")

    def set_mqtt_publisher(self, publisher):
        self._mqtt_publisher = publisher

    async def cb_unknown(self, update, context):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Sorry, I didn't understand that: " + update.message.text)

    def init(self, TOKEN):
        self.application = ApplicationBuilder().token(TOKEN).build()

        self.application.add_handler(CommandHandler('start', self.cb_start))
        self.application.add_handler(CommandHandler('help', self.cb_help))
        self.application.add_handler(CommandHandler('version', self.cb_version))
        self.application.add_handler(CommandHandler('mqtt', self.cb_mqtt))
        self.application.add_handler(MessageHandler(filters.ALL, self.cb_unknown))

        logging.info("Telegram initialized.")

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def _startup():
            await self.application.initialize()
            await self.application.start()
            if self.application.updater is None:
                raise RuntimeError('Application updater is unavailable.')
            await self.application.updater.start_polling()

        try:
            self._loop.run_until_complete(_startup())
            self.started = True
            self._ready.set()
            self._loop.run_forever()
        except Exception as e:
            self._startup_error = e
            self._ready.set()
            logging.exception('Telegram polling crashed: %s', e)
        finally:
            self.started = False
            self._loop.close()

    def start(self):
        self._startup_error = None
        self._ready.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=10)

        if self._startup_error is not None:
            raise self._startup_error

    def stop(self):
        if self.application is None or self._loop is None or not self._loop.is_running():
            return

        async def _shutdown():
            if self.application.updater is not None:
                await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

        future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
        future.result(timeout=10)

        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=10)

        self.started = False
        logging.info("Fin!")

    def idle(self):
        logging.info("Idle ...")
        if not self.started:
            logging.warning("Idling, but Bot is not started.")
            return

        if self._thread is not None:
            self._thread.join()

    def sendMsgToOwner(self, msg):
        if self.application is None or self._loop is None or not self._loop.is_running():
            logging.warning('sendMsgToOwner called before Telegram bot was started.')
            return

        future = asyncio.run_coroutine_threadsafe(
            self.application.bot.send_message(chat_id=self.OWNERID, text=msg, parse_mode=ParseMode.HTML),
            self._loop,
        )
        future.result(timeout=10)
