import feedparser
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime

from ..schemas.feed import Feed
from ..schemas.entry import Entry
from ..util import dget


def process(Session, urls):
	session = Session()

	for url in urls:

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
