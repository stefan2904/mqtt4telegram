import logging
import os

from bot import Bot

logging.basicConfig(format='%(asctime)s - ROOT - %(levelname)s - %(message)s', level=logging.INFO)

OWNERID = 24314476
TOKEN = os.getenv('TELEGRAMTOKEN')

bot = Bot(OWNERID)
bot.init(TOKEN)
bot.start()
bot.idle()
