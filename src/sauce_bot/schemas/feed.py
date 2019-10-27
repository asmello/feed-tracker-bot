from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from . import Base


class Feed(Base):
	__tablename__ = 'feeds'

	db_id = Column(Integer, primary_key=True)
	href = Column(String, unique=True)
	title = Column(String)
	link = Column(String)
	subtitle = Column(String)
	language = Column(String)
	ttl = Column(Integer)
	updated_at = Column(DateTime)
	notified_at = Column(DateTime)

	entries = relationship('Entry', back_populates='feed', cascade="all, delete, delete-orphan")

	def __repr__(self):
		return f"<Feed(title='{self.title}', link='{self.link}')>"

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
