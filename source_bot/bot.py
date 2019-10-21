import logging
import telegram.bot
from telegram.ext import messagequeue as mq

from sqlalchemy.orm import sessionmaker

class Bot(telegram.bot.Bot):

	def __init__(self, *args, mqueue=None, db_engine=None, **kwargs):
		logging.info("Creating bot...")

		super().__init__(*args, **kwargs)
		self._is_messages_queued_default = True
		self._msg_queue = mqueue or mq.MessageQueue()
		self.db_engine = db_engine

		Session = sessionmaker()
		Session.configure(bind=db_engine)
		self._Session = Session

	def __del__(self):
		try:
			self._msg_queue.stop()
		except:
			pass

	@mq.queuedmessage
	def send_message(self, *args, **kwargs):
		return super().send_message(*args, **kwargs)

	@property
	def db_session(self):
		return self._Session()

	def get_feed_urls(self):
		return self.urls
