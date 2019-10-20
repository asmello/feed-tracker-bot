from . import Base

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Feed(Base):
	__tablename__ = 'feeds'

	db_id = Column(Integer, primary_key=True)
	href = Column(String, unique=True)
	title = Column(String)
	link = Column(String)
	subtitle = Column(String)
	language = Column(String)
	ttl = Column(Integer)

	entries = relationship('Entry', back_populates='feed', cascade="all, delete, delete-orphan")

	def __repr__(self):
		return f"<Feed(title='{self.title}', link='{self.link}')>"
