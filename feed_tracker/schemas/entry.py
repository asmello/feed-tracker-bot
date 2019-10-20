from . import Base

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.event import listen
from sqlalchemy.schema import DDL


class Entry(Base):
	__tablename__ = 'entries'

	db_id = Column(Integer, primary_key=True)
	id = Column(String, unique=True)
	title = Column(String)
	link = Column(String)
	subtitle = Column(String)
	language = Column(String)
	published_at = Column(DateTime)
	summary = Column(String)
	feed_id = Column(Integer, ForeignKey('feeds.db_id'))

	feed = relationship('Feed', back_populates='entries', single_parent=True)

	def __repr__(self):
		return f"<Entry(id='{self.id}', title='{self.title}', link='{self.link}')>"

listen(Entry.__table__, 'after_create', DDL(
	'''
	CREATE OR REPLACE FUNCTION notify_entry_event() RETURNS TRIGGER AS $$
		DECLARE
			record RECORD;
			parent RECORD;
			payload JSON;
		BEGIN
			IF (TG_OP = 'DELETE') THEN
				record = OLD;
			ELSE
				record = NEW;
			END IF;

			SELECT * INTO STRICT parent FROM feeds WHERE db_id = record.feed_id;

			payload = json_build_object(
				'table', TG_TABLE_NAME,
				'action', TG_OP,
				'entry', row_to_json(record),
				'feed', row_to_json(parent)
			);

			PERFORM pg_notify('events', payload::text);

			RETURN NULL;
		END;
	$$ LANGUAGE plpgsql;

	CREATE TRIGGER notify_entry_event_trigger
	AFTER INSERT OR UPDATE OR DELETE ON entries
		FOR EACH ROW EXECUTE PROCEDURE notify_entry_event();
	'''
))
