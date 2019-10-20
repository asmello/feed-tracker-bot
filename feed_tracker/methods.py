import json
import select
import logging
import telegram
import psycopg2
import feedparser

from sqlalchemy.dialects import postgresql as pg 
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .schemas import Feed, Entry
from .util import dget

logger = logging.getLogger(__name__)


def process_db_updates(bot, payload):
	event = json.loads(payload)

	if event['table'] == 'entries':
		if event['action'] == 'INSERT':
			entry = event['entry']
			feed = event['feed']
			text = f"*{feed['title']}*: [{entry['title']}]({entry['link']})"
			bot.send_message(chat_id=582104136, text=text, parse_mode='Markdown')


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
						logger.exception(e)
	finally:
		conn.close()


def process_urls(context: telegram.ext.CallbackContext):

	session = context.bot.get_session()

	for url in context.bot.get_feed_urls():

		data = feedparser.parse(url)

		feed = session.query(Feed).filter_by(href=data.href).first()
		if feed:
			feed.title = dget(data, 'feed.title')
			feed.link = dget(data, 'feed.link')
			feed.subtitle = dget(data, 'feed.subtitle')
			feed.ttl = dget(data, 'feed.ttl', int)
		else:
			feed = Feed(
				title=dget(data, 'feed.title'),
				link=dget(data, 'feed.link'), 
				subtitle=dget(data, 'feed.subtitle'),
				language=dget(data, 'feed.language'),
				ttl=dget(data, 'feed.ttl', int),
				href=dget(data, 'href')
			)
			session.add(feed)
			session.flush()

		insert_stmt = pg.insert(Entry.__table__)

		session.execute(
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

		session.commit()
