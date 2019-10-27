import logging
import telegram
from telegram.ext import CommandHandler

from sqlalchemy.dialects import postgresql as pg 

from ..schemas import User, Chat

logger = logging.getLogger()


def get_handlers():
	return [CommandHandler('start', start)]


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
	bot = context.bot
	session = bot.db_session
	chat = update.effective_chat
	user = update.effective_user

	# Do nothing if chat already exists
	if session.query(Chat).get(chat.id):
		return

	# Upsert user to database
	insert_stmt = pg.insert(User.__table__)
	session.execute(
		insert_stmt.on_conflict_do_update(
			index_elements=['db_id'],
			set_=dict(
				is_bot=insert_stmt.excluded.is_bot,
				first_name=insert_stmt.excluded.first_name,
				last_name=insert_stmt.excluded.last_name,
				username=insert_stmt.excluded.username,
				language_code=insert_stmt.excluded.language_code
			)
		),
		User.from_telegram(user).to_dict()
	)

	# Insert chat to database
	session.add(Chat.from_telegram(chat))
	session.commit()

	bot.send_message(chat_id=chat.id, text=f"Welcome, {user.full_name}!")
