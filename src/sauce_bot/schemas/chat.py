import telegram

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from . import Base

class Chat(Base):
	__tablename__ = 'chats'

	db_id = Column(Integer, primary_key=True)
	type = Column(String)
	title = Column(String)
	username = Column(String, unique=True)
	first_name = Column(String)
	last_name = Column(String)
	description = Column(String)
	invite_link = Column(String)

	def __repr__(self):
		return f"<Chat(username='{self.username}', title='{self.title}')>"

	@classmethod
	def from_telegram(cls, chat: telegram.Chat):
		return cls(
			db_id=chat.id,
			type=chat.type,
			title=chat.title,
			username=chat.username,
			first_name=chat.first_name,
			last_name=chat.last_name,
			description=chat.description,
			invite_link=chat.invite_link
		)

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
