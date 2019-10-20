import json
import logging

from ..util import dget
from ..schemas.entry import Entry
from ..schemas.feed import Feed


logger = logging.getLogger(__name__)


def process(push_client, payload):
	try:
		event = json.loads(payload)

		if event['table'] == 'entries':
			if event['action'] == 'INSERT':
				entry = event['entry']
				feed = event['feed']
				msg = f"*{feed['title']}*: [{entry['title']}]({entry['link']})"
				push_client.send(msg)

	except Exception as e:
		logger.exception(e)
