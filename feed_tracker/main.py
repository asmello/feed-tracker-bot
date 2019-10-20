#!/usr/bin/env python3

import re
import argparse
import yaml
import select
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .schemas import initialize_db, recreate_db
from .feed_ingest.process import process as process_sources
from .feed_notify.process import process as process_updates
from .feed_notify.push_client import PushClient
from .util import dget, validate_config, get_config


def setup(args):
	with open(args.config, 'r') as f:
		config = yaml.safe_load(f)
	validate_config(config)

	engine = create_engine(get_config(args, config, 'database.url'), echo=get_config(args, config, 'verbose'))

	if args.initialize:
		initialize_db(engine)
	elif args.recreate:
		recreate_db(engine)

	Session = sessionmaker()
	Session.configure(bind=engine)

	return config, engine, Session


def main_ingest(args):
	config, _, Session = setup(args)
	
	process_sources(Session, config['feeds'])


def main_track(args):
	config, engine, Session = setup(args)

	push_client = PushClient(token=get_config(args, config, 'auth.token'))

	conn = engine.raw_connection()
	try:
		conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

		with conn.cursor() as cursor:
			cursor.execute("LISTEN events;")

		while True:
			if select.select([conn], [], [], 5) == ([],[],[]):
				pass
			else:
				conn.poll()
				while conn.notifies:
					notify = conn.notifies.pop(0)
					process_updates(push_client, notify.payload)
	finally:
		conn.close()


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

	subparsers = parser.add_subparsers(help="Sub-commands")

	parser_ingest = subparsers.add_parser("ingest", help="Actively ingest feed data into database.")
	parser_ingest.set_defaults(func=main_ingest)

	parser_track = subparsers.add_parser("track", help="Monitor new feed data and send out notifications.")
	parser_track.set_defaults(func=main_track)

	args = parser.parse_args()
	args.func(args)
