import os
import sys
import telegram
import logging

from threading import Thread
from telegram.ext import CommandHandler

from ..auth import admin


def get_handler():
	return CommandHandler('restart', restart)


def do_restart():
	logging.info("Will restart now!")
	os.execl(sys.executable, sys.executable, *sys.argv)


@admin
def restart(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Restarting...")
	Thread(target=restart).start()
