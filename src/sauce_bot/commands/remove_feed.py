import logging
import telegram
import feedparser
import sqlalchemy

from datetime import datetime
from sqlalchemy.dialects import postgresql as pg
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
	ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
)

from aws_xray_sdk.core import xray_recorder, patch

from ..schemas import Feed, UserFeed
from ..util import dget

patch(['requests'])

PENDING_URL = 1
PAGE_SIZE = 4

logger = logging.getLogger()


def get_handlers():
	return (
		ConversationHandler(
			entry_points=[CommandHandler('rmfeed', enter)],
			states={},
			fallbacks=[CommandHandler('cancel', cancel)]
		),
		CallbackQueryHandler(remove, pattern='^rmfeed:remove'),
		CallbackQueryHandler(forward, pattern='^rmfeed:forward'),
		CallbackQueryHandler(back, pattern='^rmfeed:back'),
	)


@xray_recorder.capture("cancel_handler")
def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Alright, no feeds removed.")
	return ConversationHandler.END


@xray_recorder.capture("enter_handler")
def enter(update: telegram.Update, context: telegram.ext.CallbackContext):
	args = context.args

	if len(args) == 0:
		db_session = context.bot.db_session
		user = update.effective_user

		feeds = (
			db_session.query(Feed.db_id, Feed.title)
			.join(UserFeed)
			.filter_by(user_id=user.id)
			.order_by(Feed.db_id)
			.limit(PAGE_SIZE + 1)
			.all()
		)
		if not feeds:
			update.message.reply_text("No feeds to remove! Add one with /addfeed.")
			return ConversationHandler.END

		buttons = [
			[InlineKeyboardButton(feed_title, callback_data=f"rmfeed:remove:{feed_id}")]
			for feed_id, feed_title in feeds[:PAGE_SIZE]
		]
		if len(feeds) > PAGE_SIZE:
			buttons += [[InlineKeyboardButton("More...", callback_data=f"rmfeed:forward:{feeds[-1][0]}")]]

		reply_markup = InlineKeyboardMarkup(buttons)
		update.message.reply_text("Which feed would you like to remove?", reply_markup=reply_markup)

	return ConversationHandler.END


@xray_recorder.capture("forward_handler")
def forward(update: telegram.Update, context: telegram.ext.CallbackContext):
	query = update.callback_query
	chat = update.effective_chat
	user = update.effective_user
	db_session = context.bot.db_session
	feed_id = int(query.data.split(':')[-1])

	feeds = (
		db_session.query(Feed.db_id, Feed.title)
		.join(UserFeed)
		.filter(UserFeed.user_id == user.id, Feed.db_id >= feed_id)
		.order_by(Feed.db_id)
		.limit(PAGE_SIZE + 1)
		.all()
	)

	if not feeds:
		logger.error("Got empty results from rmfeed:forward for user=%s at cursor=%s", user.id, feed_id)
		query.answer("Error! No more results!")
		return

	buttons = [
		[InlineKeyboardButton(feed_title, callback_data=f"rmfeed:remove:{feed_id}")]
		for feed_id, feed_title in feeds[:PAGE_SIZE]
	]
	if len(feeds) > PAGE_SIZE:
		buttons += [[
			InlineKeyboardButton("Back...", callback_data=f"rmfeed:back:{feed_id}"),
			InlineKeyboardButton("Next...", callback_data=f"rmfeed:forward:{feeds[-1][0]}")
		]]
	else:
		buttons += [[InlineKeyboardButton("Back...", callback_data=f"rmfeed:back:{feed_id}")]]

	reply_markup = InlineKeyboardMarkup(buttons)
	query.edit_message_reply_markup(reply_markup)


@xray_recorder.capture("back_handler")
def back(update: telegram.Update, context: telegram.ext.CallbackContext):
	query = update.callback_query
	chat = update.effective_chat
	user = update.effective_user
	db_session = context.bot.db_session
	feed_id = int(query.data.split(':')[-1])

	feeds = (
		db_session.query(Feed.db_id, Feed.title)
		.join(UserFeed)
		.filter(UserFeed.user_id == user.id, Feed.db_id < feed_id)
		.order_by(Feed.db_id.desc())
		.limit(PAGE_SIZE + 1)
		.all()
	)

	if not feeds:
		logger.error("Got empty results from rmfeed:back for user=%s at cursor=%s", user.id, feed_id)
		query.answer("Error! No more results!")
		return

	buttons = [
		[InlineKeyboardButton(feed_title, callback_data=f"rmfeed:remove:{feed_id}")]
		for feed_id, feed_title in feeds[PAGE_SIZE-1::-1]
	]
	if len(feeds) > PAGE_SIZE:
		buttons += [[
			InlineKeyboardButton("Back...", callback_data=f"rmfeed:back:{feeds[0][0]}"),
			InlineKeyboardButton("Next...", callback_data=f"rmfeed:forward:{feed_id}")
		]]
	else:
		buttons += [[InlineKeyboardButton("More...", callback_data=f"rmfeed:forward:{feed_id}")]]

	reply_markup = InlineKeyboardMarkup(buttons)
	query.edit_message_reply_markup(reply_markup)


@xray_recorder.capture("remove_handler")
def remove(update: telegram.Update, context: telegram.ext.CallbackContext):
	query = update.callback_query
	chat = update.effective_chat
	user = update.effective_user
	feed_id = int(query.data.split(':')[-1])

	db_session = context.bot.db_session
	result = (
		db_session
		.query(UserFeed, Feed.title)
		.filter_by(feed_id=feed_id, user_id=user.id)
		.join(Feed)
		.first()
	)
	if result is None:
		query.answer("Error! Feed already removed.")
		return

	userfeed, feed_title = result
	db_session.delete(userfeed)
	db_session.commit()

	query.answer("Feed removed successfully!")
	context.bot.send_message(
		chat_id=chat.id, text=f"Removed feed *{feed_title}*.", parse_mode=telegram.ParseMode.MARKDOWN
	)
