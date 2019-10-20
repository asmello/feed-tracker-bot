import logging
import telegram
import feedparser
import sqlalchemy

from datetime import datetime
from sqlalchemy.dialects import postgresql as pg 
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, Filters

from ..schemas import Feed, UserFeed
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

	_process(args, update, context)
	return ConversationHandler.END


def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Canceling the new feed entry.")
	return ConversationHandler.END


def enter_url(update: telegram.Update, context: telegram.ext.CallbackContext):
	urls = list(update.message.parse_entities(types='url').values())
	
	if not urls:
		update.message.reply_text("No URL detected. Canceled.")
		return ConversationHandler.END

	_process(urls, update, context)
	return ConversationHandler.END


def _process(urls, update, context):
	for url in urls:
		feed, error = _add(url, context.bot.db_session, update.effective_user)
		if feed:
			if feed.subtitle:
				msg = f"Added *{feed.title}* _({feed.subtitle})_ to your feeds."
			else:
				msg = f"Added *{feed.title}* to your feeds."
		else:
			msg = f"Oh no! Could not add feed. Reason: {error}."
		update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)


def _add(url, db_session, user):
	logging.debug("Fetching feed data for URL: %s", url)
	data = feedparser.parse(url)

	logging.debug("Got feed data: %s", data)

	if data['bozo']:
		logging.info("Failed to parse feed from URL: %s.", url)
		return None, data['bozo_exception'].getMessage()

	insert_stmt = pg.insert(Feed.__table__)
	result = db_session.execute(
		insert_stmt.on_conflict_do_update(
			index_elements=['href'],
			set_=dict(
				title=insert_stmt.excluded.title,
				language=insert_stmt.excluded.language,
				link=insert_stmt.excluded.link,
				subtitle=insert_stmt.excluded.subtitle,
				ttl=insert_stmt.excluded.ttl,
				updated_at=insert_stmt.excluded.updated_at
			)
		).returning(Feed.__table__.c.db_id),
		dict(
			title=dget(data, 'feed.title'),
			link=dget(data, 'feed.link'), 
			subtitle=dget(data, 'feed.subtitle'),
			language=dget(data, 'feed.language'),
			ttl=dget(data, 'feed.ttl', int),
			href=dget(data, 'href'),
			updated_at=datetime.now()
		)
	)

	db_session.commit()

	try:
		user_feed = UserFeed(user_id=user.id, feed_id=result.first()[0])
		db_session.add(user_feed)
		db_session.commit()
	except sqlalchemy.exc.IntegrityError:
		return None, "user not registered (run /start first)"

	return data.feed, 'success'
