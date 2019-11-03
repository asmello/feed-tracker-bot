import pickle
import logging
import telegram
import requests
import feedparser
import sqlalchemy

from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.dialects import postgresql as pg
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, Filters

from aws_xray_sdk.core import xray_recorder, patch

from ..schemas import Feed, UserFeed
from ..util import dget

patch(['requests'])

PENDING_URL = 1
PAGE_SIZE = 4

logger = logging.getLogger()


def get_handlers():
	return [
		ConversationHandler(
			entry_points=[CommandHandler('addfeed', enter)],
			states={
				PENDING_URL: [MessageHandler(Filters.all, pending_url)]
			},
			fallbacks=[CommandHandler('cancel', cancel)]
		)
	]


@xray_recorder.capture("enter_handler")
def enter(update: telegram.Update, context: telegram.ext.CallbackContext):
	args = context.args

	if len(args) == 0:
		update.message.reply_text("What is the URL for the new feed?")
		return PENDING_URL
	if len(args) > 1:
		update.message.reply_text("Please specify one URL at a time.")
		return ConversationHandler.END

	_process(args[0], update, context)
	return ConversationHandler.END


@xray_recorder.capture("cancel_handler")
def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
	update.message.reply_text("Canceling the new feed entry.")
	return ConversationHandler.END


@xray_recorder.capture("pending_url_handler")
def pending_url(update: telegram.Update, context: telegram.ext.CallbackContext):
	urls = list(update.message.parse_entities(types='url').values())
	
	if not urls:
		update.message.reply_text("No URL detected. Canceled.")
		return ConversationHandler.END
	if len(urls) > 1:
		update.message.reply_text("Please specify one URL at a time.")
		return ConversationHandler.END

	return _process(urls[0], update, context)


@xray_recorder.capture("process_subfunction")
def _process(url, update, context):
	feed_links, error = _extract_feed_links(url)

	if error:
		msg = f"NOT adding `{url}`. Reason: {error}."
		update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)

	elif len(feed_links) == 1:
		feed_url = requests.compat.urljoin(url, feed_links[0])
		feed, error = _add(feed_url, context.bot.db_session, update.effective_user)
		if feed and not error:
			if feed.get('subtitle'):
				msg = f"Added *{feed.title}* _({feed.subtitle})_ to your feeds."
			else:
				msg = f"Added *{feed.title}* to your feeds."
			update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)
		elif feed:
			msg = f"NOT adding *{feed.title}*. Reason: {error}."
			update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)
		else:
			msg = f"Oh no! Could not add feed. Reason: {error}."
			update.message.reply_text(msg)
	else:
		# TODO: store feed links in database so they can be reliably referenced in the future
		buttons = [
			[
				InlineKeyboardButton(
					feed_link.get('title', feed_link['href']), callback_data=f"addfeed:select:{feed_link['href']}"
				)
			] for feed_link in feed_links
		]
		if len(feed_links) > PAGE_SIZE:
			buttons += [[InlineKeyboardButton("More...", callback_data=f"addfeed:forward:{PAGE_SIZE}")]]
		reply_markup = InlineKeyboardMarkup(buttons)
		update.message.reply_text("Which feed would you like to add?", reply_markup=reply_markup)

	return ConversationHandler.END


@xray_recorder.capture("extract_feed_links_subfunction")
def _extract_feed_links(url):
	logger.info("Fetching URL: %s", url)
	headers = {
		# Simple scraper blocker counter-measure
		'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
					  "(KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
	}
	try:
		response = requests.get(url, headers=headers)
	except requests.exceptions.MissingSchema:
		url = "https://" + url
		response = requests.get(url, headers=headers)
	if response.status_code != requests.codes.ok:
		logger.debug("Server response: %s", response.text)
		return None, f"server responded with {response.status_code}"

	doc_type = response.headers['content-type'].split(';')[0]
	if doc_type == 'text/html':
		# Parse page to search for RSS or Atom feeds
		soup = BeautifulSoup(response.text, features='lxml')
		atom_links = soup.find_all('link', attrs={'rel': 'alternate', 'type': 'application/atom+xml'})
		rss_links = soup.find_all('link', attrs={'rel': 'alternate', 'type': 'application/rss+xml'})
		links = atom_links + rss_links
		# TODO: add feeds to database every time they are found
		if not links:
			return None, "no feeds found"
		elif len(links) == 1:
			return (links[0]['href'],), None
		return links, None
	elif doc_type == 'application/atom+xml' or doc_type == 'application/rss+xml':
		return (url,), None
	else:
		xray_recorder.put_annotation("content-type", response.headers['content-type'])
		return None, "unrecognized content"


@xray_recorder.capture("add_subfunction")
def _add(url, db_session, user):
	feed = (
		db_session.query(Feed)
		.filter_by(href=url)
		.join(UserFeed)
		.filter_by(user_id=user.id)
		.first()
	)
	if feed:
		return feed, "already added"

	logger.debug("Fetching feed data for URL: %s", url)
	data = feedparser.parse(url)

	logger.debug("Got feed data: %s", data)

	if data['bozo']:
		logger.info("Failed to parse feed from URL: %s.", url)
		return None, data['bozo_exception'].getMessage()

	insert_stmt = pg.insert(Feed.__table__)
	result = db_session.execute(
		insert_stmt.on_conflict_do_update(
			index_elements=['href'],
			set_=dict(
				title=insert_stmt.excluded.title,
				language=insert_stmt.excluded.language,
				link=insert_stmt.excluded.link,
				subtitle=insert_stmt.excluded.subtitle,
				ttl=insert_stmt.excluded.ttl,
				updated_at=insert_stmt.excluded.updated_at
			)
		).returning(Feed.__table__.c.db_id),
		dict(
			title=dget(data, 'feed.title'),
			link=dget(data, 'feed.link'), 
			subtitle=dget(data, 'feed.subtitle'),
			language=dget(data, 'feed.language'),
			ttl=dget(data, 'feed.ttl', int),
			href=dget(data, 'href'),
			updated_at=datetime.now()
		)
	)

	db_session.commit()

	try:
		user_feed = UserFeed(user_id=user.id, feed_id=result.first()[0])
		db_session.add(user_feed)
		db_session.commit()
	except sqlalchemy.exc.IntegrityError:
		return None, "user not registered (run /start first)"

	return data.feed, None
