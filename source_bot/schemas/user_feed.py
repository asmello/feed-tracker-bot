from sqlalchemy import Column, Integer, ForeignKey

from . import Base


class UserFeed(Base):
	__tablename__ = 'user_feeds'

	user_id = Column('user_id', ForeignKey('users.db_id'), primary_key=True)
	feed_id = Column('feed_id', ForeignKey('feeds.db_id'), primary_key=True)

	def __repr__(self):
		return f"<UserFeed(user_id='{self.user_id}', feed_id='{self.feed_id}')>"

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
