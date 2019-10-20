import requests

class PushClient:
	
	def __init__(self, token):
		self.base_url = f"https://api.telegram.org/bot{token}/"
		self.session = requests.Session()
		self.session.header = {"content-type": "application/json"}

	def _request(self, method, payload):
		r = self.session.post(self.base_url + method, json=payload)
		try:
			r.raise_for_status()
		except requests.exceptions.HTTPError as e:
			try:
				data = r.json()
				raise ValueError(data['description']) from e
			except Exception:
				raise e

	def send(self, text):
		self._request('sendMessage', payload=dict(chat_id=582104136, text=text, parse_mode='Markdown'))
