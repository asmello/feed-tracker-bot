import os
import logging
import feedparser

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import sessionmaker

from sauce_bot.schemas import Feed, Entry


LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", 'INFO'))
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

DATABASE_URL = os.environ["DATABASE_URL"]
logger.info("Connecting to database %s...", DATABASE_URL)
DB_ENGINE = create_engine(DATABASE_URL, echo=LOG_LEVEL <= loggin.DEBUG)

DB_Session = sessionmaker()
DB_Session.configure(bind=DB_ENGINE)


def handler(event, context):
	logger.info("Processing feeds...")

	db_session = DB_Session()

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
