from telegram.ext import CommandHandler

from . import start
from . import add_feed

def register_commands(dispatcher):
	dispatcher.add_handler(start.get_handler())
	dispatcher.add_handler(add_feed.get_handler())
