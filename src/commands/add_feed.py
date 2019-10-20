import logging
import telegram
import feedparser

from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, Filters

from ..schemas import Feed
from ..util import dget

PENDING_URL = 1


def get_handler():
	return ConversationHandler(
		entry_points=[CommandHandler('add_feed', enter)],
		states={
			PENDING_URL: [MessageHandler(Filters.all, enter_url)]
		},
		fallbacks=[CommandHandler('cancel', cancel)]
	)


def enter(update: telegram.Update, context: telegram.ext.CallbackContext):
	args = context.args

	if len(args) == 0:
		update.message.reply_text("What is the URL for the new feed?")
		return PENDING_URL

	for url in args:
		feed, error = _add(url, context.bot.db_session)
		if feed:
			msg = f"Added *{feed.title}* as a new feed."
		else:
			msg = f"Oh no! Could not add `{url}`. Reason: {error}."
		update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)

	return ConversationHandler.END


def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Canceling the new feed entry.")
	return ConversationHandler.END


def enter_url(update: telegram.Update, context: telegram.ext.CallbackContext):
	urls = list(update.message.parse_entities(types='url').values())
	
	if not urls:
		update.message.reply_text("No URL detected. Canceled.")
		return ConversationHandler.END

	for url in urls:
		feed, error = _add(url, context.bot.db_session)
		if feed:
			msg = f"Added *{feed.title}* as a new feed."
		else:
			msg = f"Oh no! Could not add `{url}`. Reason: {error}."
		update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)

	return ConversationHandler.END


def _add(url, db_session):
	logging.debug("Fetching feed data for URL: %s", url)
	data = feedparser.parse(url)

	logging.debug("Got feed data: %s", data)

	if data['bozo']:
		logging.info("Failed to parse feed from URL: %s.", url)
		return None, data['bozo_exception'].getMessage()

	feed = Feed(
		title=dget(data, 'feed.title'),
		link=dget(data, 'feed.link'), 
		subtitle=dget(data, 'feed.subtitle'),
		language=dget(data, 'feed.language'),
		ttl=dget(data, 'feed.ttl', int),
		href=dget(data, 'href')
	)

	db_session.add(feed)
	db_session.commit()
	return feed, 'success'
