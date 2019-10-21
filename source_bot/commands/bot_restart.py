import os
import sys
import time
import signal
import telegram
import logging

from threading import Thread
from telegram.ext import CommandHandler

from ..auth import admin


def get_handler():
	return CommandHandler('bot_restart', bot_restart)


def restart():
	logging.info("Will restart now!")
	os.kill(os.getpid(), signal.SIGINT)  # urge updater to stop
	time.sleep(5)  # give us some time to deliver final messages
	os.execl(sys.executable, sys.executable, *sys.argv)


@admin
def bot_restart(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Restarting myself...")
	Thread(target=restart).start()
