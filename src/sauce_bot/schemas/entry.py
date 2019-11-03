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

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
