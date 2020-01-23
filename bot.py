import logging
import socket

from telegram import ParseMode
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater


class Bot():

    def __init__(self, OWNERID):
        self.OWNERID = OWNERID
        self.started = False
        logging.info("Telegram OWNERID: " + str(OWNERID))

    def isAdmin(self, ID):
        logging.debug("requested: {} ({})".format(type(ID), ID))
        logging.debug("trusted:   {} ({})".format(type(self.OWNERID), self.OWNERID))
        return ID == self.OWNERID

    def cb_start(self, update, context):
        hostname = socket.gethostname()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="I am alive at {}! And you are, {}!?".format(hostname,
                                                                                   str(update.effective_chat.id)))
        if self.isAdmin(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text="You are this bots admin!")

    def cb_mqtt(self, update, context):
        if not self.isAdmin(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text="ERROR: You are not this bots admin!")
            return False

        if len(context.args) < 2:
            context.bot.send_message(chat_id=update.effective_chat.id, text="*Usage:* _/mqtt <topic> <payload>_",
                                     parse_mode=ParseMode.MARKDOWN)
            return False

        topic = context.args[0] if context.args[0].split('/')[0] == 'telegram' \
            else 'telegram/{}'.format(context.args[0])
        payload = ' '.join(context.args[1:])
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Send to topic ({}): {}".format(topic, payload))

        context.bot.send_message(chat_id=update.effective_chat.id, text="FEATURE NOT YET IMPLEMENTED!")

    def cb_unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Sorry, I didn't understand that: " + update.message.text)

    def init(self, TOKEN):
        self.updater = Updater(token=TOKEN, use_context=True)
        dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', lambda update, context: self.cb_start(update, context))
        dispatcher.add_handler(start_handler)

        mqtt_handler = CommandHandler('mqtt', lambda update, context: self.cb_mqtt(update, context))
        dispatcher.add_handler(mqtt_handler)

        unknown_handler = MessageHandler(Filters.all, lambda update, context: self.cb_unknown(update, context))
        dispatcher.add_handler(unknown_handler)

        logging.info("Telegram initialized.")

    def start(self):
        self.updater.start_polling()
        self.started = True

    def stop(self):
        self.updater.stop()
        self.started = False
        logging.info("Fin!")

    def idle(self):
        logging.info("Idle ...")
        if not self.started:
            logging.warn("Idling, but Bot is not started.")
        self.updater.idle()

    def sendMsgToOwner(self, msg):
        self.updater.bot.send_message(chat_id=self.OWNERID, text=msg, parse_mode=ParseMode.MARKDOWN)
