import os
import json
import logging

from sqlalchemy import create_engine
from telegram import Update
from telegram.ext import Dispatcher
from telegram.utils.request import Request

from sauce_bot.bot import Bot
from sauce_bot.commands import register_commands


LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", 'INFO'))
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

DATABASE_URL = os.environ["DATABASE_URL"]
logger.info("Connecting to database %s...", DATABASE_URL)
DB_ENGINE = create_engine(DATABASE_URL, echo=LOG_LEVEL <= logging.DEBUG)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
BOT = Bot(token=TELEGRAM_TOKEN, db_engine=DB_ENGINE, request=Request(con_pool_size=8))
DISPATCHER = Dispatcher(BOT, None, workers=0, use_context=True)
register_commands(DISPATCHER)


def handler(event, context):
	payload = json.loads(event['body'])
	logger.info("Got payload %s", payload)
	DISPATCHER.process_update(Update.de_json(payload, BOT))
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
