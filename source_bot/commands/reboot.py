import os
import sys
import telegram
import logging

from threading import Thread
from telegram.ext import CommandHandler

from ..auth import admin


def get_handler(updater):

	def rebooter():
		logging.info("Will reboot now!")
		os.execl(sys.executable, sys.executable, *sys.argv)

	@admin
	def reboot(update: telegram.Update, context: telegram.ext.CallbackContext):
		update.message.reply_text("Rebooting...")
		Thread(target=rebooter).start()

	return CommandHandler('reboot', reboot)
