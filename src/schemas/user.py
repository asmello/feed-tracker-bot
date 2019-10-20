import telegram

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from . import Base


class User(Base):
	__tablename__ = 'users'

	db_id = Column(Integer, primary_key=True)
	is_bot = Column(Boolean)
	first_name = Column(String)
	last_name = Column(String)
	username = Column(String, unique=True)
	language_code = Column(String)

	def __repr__(self):
		return f"<User(username='{self.username}', is_bot='{self.is_bot}')>"

	@classmethod
	def from_telegram(cls, user: telegram.User):
		return cls(
			db_id=user.id,
			is_bot=user.is_bot,
			first_name=user.first_name,
			last_name=user.last_name,
			username=user.username,
			language_code=user.language_code
		)

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
