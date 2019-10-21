import os
import sys
import telegram
import logging

from threading import Thread
from telegram.ext import CommandHandler

from ..auth import admin


def reboot():
	logging.info("Will reboot now!")
	os.execl(sys.executable, sys.executable, *sys.argv)


def get_handler():

	@admin
	def _reboot(update: telegram.Update, context: telegram.ext.CallbackContext):
		update.message.reply_text("Rebooting...")
		Thread(target=reboot).start()

	return CommandHandler('reboot', _reboot)
