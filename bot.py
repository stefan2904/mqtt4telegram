import logging

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

logging.basicConfig(format='%(asctime)s -TELEGRAM - %(levelname)s - %(message)s', level=logging.INFO)

logging.info("Init ...")


class Bot():

    def __init__(self, OWNERID):
        self.OWNERID = OWNERID
        self.started = False

    def isAdmin(self, ID):
        return ID == self.OWNERID

    def cb_start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="I am alive! And you are " + str(update.effective_chat.id))
        if self.isAdmin(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text="You are this bots admin!")

    def cb_unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Sorry, I didn't understand that: " + update.message.text)

    def init(self, TOKEN):
        logging.info("Init Bot ...")
        self.updater = Updater(token=TOKEN, use_context=True)
        dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', lambda update, context: self.cb_start(update, context))
        dispatcher.add_handler(start_handler)

        unknown_handler = MessageHandler(Filters.all, lambda update, context: self.cb_unknown(update, context))
        dispatcher.add_handler(unknown_handler)

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
