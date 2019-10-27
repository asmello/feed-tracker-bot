import os
import logging


LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", 'INFO'))
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)


def request_handler(event, context):
	logger.info("Received event %s for context %s", event, context)
	return {
		"principalId": 'anyone',
		"policyDocument": {
			"Version": "2012-10-17",
			"Statement": [
				{
					"Action": "execute-api:Invoke",
					"Effect": "Allow",
					"Resource": event['methodArn']
				}
			]
		}
	}
