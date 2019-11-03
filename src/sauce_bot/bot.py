import telegram.bot

from sqlalchemy.orm import sessionmaker

class Bot(telegram.bot.Bot):

	def __init__(self, *args, db_engine=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.db_engine = db_engine

		Session = sessionmaker()
		Session.configure(bind=db_engine)
		self._Session = Session


	@property
	def db_session(self):
		return self._Session()
