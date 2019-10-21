import telegram

from .schemas import User


def admin(func):

	def authenticate(update: telegram.Update, context: telegram.ext.CallbackContext):
		session = context.bot.db_session
		user = session.query(User).get(update.effective_user.id)
		if user and user.is_admin:
			return func(update, context)

	return authenticate
