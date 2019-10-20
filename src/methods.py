import json
import select
import logging
import telegram
import psycopg2
import feedparser

from datetime import datetime
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql as pg 
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .schemas import Feed, Entry, UserFeed
from .util import dget


def process_db_updates(bot, payload):
	event = json.loads(payload)

	if event['table'] == 'entries':
		if event['action'] == 'INSERT':
			entry = event['entry']
			feed = event['feed']
			feeds = Feed.__table__
			db_session = bot.db_session

			# Record metadata for last time notifications were issued
			db_session.execute(feeds.update().where(feeds.c.db_id == feed['db_id']), {"notified_at": datetime.now()})
			db_session.commit()

			if not feed['notified_at']:
				logging.info(
					"Ignoring notification for new entry=%s in feed=%s (first update)", entry['db_id'], feed['db_id']
				)
				return  # this is the first time entries were added for this feed, don't send notifications

			logging.info("Sending out notifications for new entry=%s in feed=%s", entry['db_id'], feed['db_id'])
			text = f"*{feed['title']}*: [{entry['title']}]({entry['link']})"

			for user_feed in db_session.query(UserFeed).filter_by(feed_id=feed['db_id']):
				bot.send_message(chat_id=user_feed.user_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def db_monitor(bot):
	conn = bot.db_engine.raw_connection()
	try:
		conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

		with conn.cursor() as cursor:
			cursor.execute("LISTEN events;")

		while True:
			if select.select([conn], [], [], 5) == ([],[],[]):
				pass
			else:
				conn.poll()
				while conn.notifies:
					notify = conn.notifies.pop(0)
					try:
						process_db_updates(bot, notify.payload)
					except Exception as e:
						logging.exception(e)
	finally:
		conn.close()


def process_urls(context: telegram.ext.CallbackContext):

	db_session = context.bot.db_session

	for feed in db_session.query(Feed).all():

		data = feedparser.parse(feed.href)

		insert_stmt = pg.insert(Entry.__table__)

		db_session.execute(
			insert_stmt.on_conflict_do_update(
				index_elements=['id'],
				set_=dict(
					title=insert_stmt.excluded.title,
					language=insert_stmt.excluded.language,
					link=insert_stmt.excluded.link,
					published_at=insert_stmt.excluded.published_at,
					summary=insert_stmt.excluded.summary,
					feed_id=insert_stmt.excluded.feed_id
				)
			),
			[dict(
				id=dget(entry, 'id'),
				title=dget(entry, 'title'),
				language=dget(entry, 'language'),
				link=dget(entry, 'link'),
				published_at=dget(entry, 'published_parsed', lambda x: datetime(*x[:6])),
				summary=dget(entry, 'summary'),
				feed_id=feed.db_id
			) for entry in data.entries]
		)

		db_session.commit()
