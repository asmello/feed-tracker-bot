import telegram
from telegram.ext import CommandHandler

from . import start
from . import add_feed
from . import bot_restart


def register_commands(dispatcher: telegram.ext.Dispatcher):
	dispatcher.add_handler(start.get_handler())
	dispatcher.add_handler(add_feed.get_handler())
	dispatcher.add_handler(bot_restart.get_handler())
