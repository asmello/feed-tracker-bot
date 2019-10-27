import logging
import telegram

from datetime import datetime
from sqlalchemy.orm import sessionmaker

from sauce_bot.schemas import Feed, UserFeed


LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", 'INFO'))
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

DATABASE_URL = os.environ["DATABASE_URL"]
logger.info("Connecting to database %s...", DATABASE_URL)
DB_ENGINE = create_engine(DATABASE_URL, echo=LOG_LEVEL <= logging.DEBUG)

DB_Session = sessionmaker()
DB_Session.configure(bind=DB_ENGINE)
logger.info("Setup complete.")


def handler(event, context):
	logger.debug("Processing database event with payload: %s", event)

	if event['table'] == 'entries':
		if event['action'] == 'INSERT':
			entry = event['entry']
			feed = event['feed']
			feeds = Feed.__table__
			db_session = DB_Session()

			# Record metadata for last time notifications were issued
			db_session.execute(feeds.update().where(feeds.c.db_id == feed['db_id']), {"notified_at": datetime.now()})
			db_session.commit()

			if not feed['notified_at']:
				logger.info(
					"Ignoring notification for new entry=%s in feed=%s (first update)", entry['db_id'], feed['db_id']
				)
				return  # this is the first time entries were added for this feed, don't send notifications

			logger.info("Sending out notifications for new entry=%s in feed=%s", entry['db_id'], feed['db_id'])
			text = f"*{feed['title']}*: [{entry['title']}]({entry['link']})"

			for user_feed in db_session.query(UserFeed).filter_by(feed_id=feed['db_id']):
				BOT.send_message(chat_id=user_feed.user_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
