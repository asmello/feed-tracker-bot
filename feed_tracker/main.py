#!/usr/bin/env python3

import re
import yaml
import logging
import argparse
import telegram

from sqlalchemy import create_engine
from telegram.ext import Updater, CommandHandler

from .bot import Bot
from .schemas import initialize_db, recreate_db
from .methods import db_monitor, process_urls
from .util import dget, validate_config, get_config

logger = logging.getLogger(__name__)


def main(args):

	with open(args.config, 'r') as f:
		config = yaml.safe_load(f)
	validate_config(config)

	engine = create_engine(get_config(args, config, 'database.url'), echo=get_config(args, config, 'verbose'))

	if args.initialize:
		initialize_db(engine)
	elif args.recreate:
		recreate_db(engine)

	bot = Bot(token=get_config(args, config, 'auth.token'), db_engine=engine)
	bot.urls = config['feeds']

	updater = Updater(bot=bot, use_context=True)
	job_queue = updater.job_queue
	dispatcher = updater.dispatcher

	dispatcher.run_async(db_monitor, bot)

	fetch_feeds_job = job_queue.run_repeating(process_urls, interval=60, first=0)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Feed tracking services.")
	parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode (console outputs).")
	parser.add_argument(
		'-c', '--config', metavar='CONFIG_FILE', help="Path to YAML configuration file.", default='config.yml'
	)

	start_actions = parser.add_mutually_exclusive_group()
	start_actions.add_argument('--initialize', action='store_true', help="Initialize the database upon start.")
	start_actions.add_argument(
		'--recreate', action='store_true',
		help="Delete all data in the database, and initialize it again upon start."
	)

	main(parser.parse_args())
