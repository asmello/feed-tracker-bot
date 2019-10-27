from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from .entry import Entry
from .feed import Feed
from .user import User
from .chat import Chat
from .user_feed import UserFeed
