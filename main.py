#!/usr/bin/env python3

import re
import yaml
import logging
import argparse
import telegram

from sqlalchemy import create_engine
from telegram.ext import Updater, CommandHandler
from telegram.utils.request import Request

from source_bot.bot import Bot
from source_bot.commands import register_commands
from source_bot.schemas import initialize_db, recreate_db
from source_bot.functions import db_monitor, process_urls, hello_world
from source_bot.util import dget, validate_config, get_config, print_welcome


def main(args):
	print_welcome()

	with open(args.config, 'r') as f:
		config = yaml.safe_load(f)
	validate_config(config)

	if get_config(args, config, 'verbose'):
		logging.basicConfig(level=logging.INFO)
		verbose_level = 1
	elif get_config(args, config, 'debug'):
		logging.basicConfig(level=logging.DEBUG)
		verbose_level = 2
	else:
		logging.basicConfig(level=logging.WARN)
		verbose_level = 0

	db_url = get_config(args, config, 'database.url')
	logging.info("Connecting to database %s...", db_url)

	engine = create_engine(db_url, echo=verbose_level > 1)

	if args.initialize:
		initialize_db(engine, config)
	elif args.recreate:
		recreate_db(engine, config)

	bot = Bot(token=get_config(args, config, 'token'), db_engine=engine, request=Request(con_pool_size=8))

	updater = Updater(bot=bot, use_context=True)
	job_queue = updater.job_queue
	dispatcher = updater.dispatcher

	register_commands(dispatcher)

	dispatcher.run_async(db_monitor, bot)

	hello_world_job = job_queue.run_once(hello_world, when=1)
	fetch_feeds_job = job_queue.run_repeating(process_urls, interval=60, first=5)

	logging.info("Starting event loop...")
	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Feed tracking services.")
	parser.add_argument(
		'-c', '--config', metavar='CONFIG_FILE', help="Path to YAML configuration file.", default='config.yml'
	)

	verbose_options = parser.add_mutually_exclusive_group()
	verbose_options.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode (console outputs).")
	verbose_options.add_argument(
		'-vv', '--debug', action='store_true', help="Enable debug mode (detailed console outputs)."
	)

	start_actions = parser.add_mutually_exclusive_group()
	start_actions.add_argument('--initialize', action='store_true', help="Initialize the database upon start.")
	start_actions.add_argument(
		'--recreate', action='store_true',
		help="Delete all data in the database, and initialize it again upon start."
	)

	main(parser.parse_args())
