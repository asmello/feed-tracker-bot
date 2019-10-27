from sqlalchemy import create_engine
from telegram import Bot
from telegram.utils.request import Request

import os
import json
import logging

from sauce_bot.schemas import Base, User


LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", 'INFO'))
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

DATABASE_URL = os.environ["DATABASE_URL"]
logger.info("Connecting to database %s...", DATABASE_URL)
DB_ENGINE = create_engine(DATABASE_URL, echo=LOG_LEVEL <= logging.DEBUG)
ADMIN_USERS = [int(x) for x in os.environ["ADMIN_USERS"].split(',')]

BOT = Bot(token=os.environ["TELEGRAM_TOKEN"])
logger.info("Setup complete.")


def initialize_db():
	Base.metadata.create_all(DB_ENGINE)

	logger.info("Registering admins: %s", ADMIN_USERS)

	# Register admin users so they have superpowers right away
	conn = DB_ENGINE.connect()
	conn.execute(User.__table__.insert(), [dict(db_id=user_id, is_admin=True) for user_id in ADMIN_USERS])
	conn.close()


def handler(event, context):
	payload = json.loads(event['body'])
	logger.debug("Received payload %s", payload)

	if 'action' not in payload:
		logger.info("Received payload %s", payload)
		return {
			"isBase64Encoded": False,
			"statusCode": 400,
			"headers": {
				'Content-Type': 'application/json'
			},
			"body": json.dumps({
				"message": "No action specified.",
				"input": event['body']
			})
		}

	if payload['action'] == 'INIT':
		initialize_db()
	elif payload['action'] == 'RECREATE':
		Base.metadata.drop_all(DB_ENGINE)
		initialize_db()
	elif payload['action'] == 'SETUP_WEBHOOK':
		if 'url' not in payload:
			return {
				"isBase64Encoded": False,
				"statusCode": 400,
				"headers": {
					'Content-Type': 'application/json'
				},
				"body": json.dumps({
					"message": "No URL specified.",
					"input": event['body']
				})
			}
		BOT.set_webhook(payload['url'])
	else:
		return {
			"isBase64Encoded": False,
			"statusCode": 400,
			"headers": {
				'Content-Type': 'application/json'
			},
			"body": json.dumps({
				"message": "Invalid action specified."
			})
		}

	return {
		"isBase64Encoded": False,
		"statusCode": 200,
		"headers": {
			'Content-Type': 'application/json'
		},
		"body": json.dumps({
			"message": "OK"
		})
	}
