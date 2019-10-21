import logging

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .entry import Entry
from .feed import Feed
from .user import User
from .chat import Chat
from .user_feed import UserFeed


def initialize_db(engine, config):
	Base.metadata.create_all(engine)

	admins = config['admins']
	logging.info("Registering admins: %s", admins)

	# Register admin users so they have superpowers right away
	conn = engine.connect()
	conn.execute(User.__table__.insert(), [dict(db_id=user_id, is_admin=True) for user_id in admins])
	conn.close()


def recreate_db(engine, config):
	Base.metadata.drop_all(engine)
	initialize_db(engine, config)
