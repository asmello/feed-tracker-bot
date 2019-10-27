import telegram

from . import start
from . import add_feed
from . import remove_feed


def register_commands(dispatcher: telegram.ext.Dispatcher):

	def add_all(handlers):
		for handler in handlers:
			dispatcher.add_handler(handler)

	add_all(start.get_handlers())
	add_all(add_feed.get_handlers())
	add_all(remove_feed.get_handlers())


