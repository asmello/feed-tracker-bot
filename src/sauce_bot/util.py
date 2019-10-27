def dget(d, path, adapter=None, safe=False):
	for part in path.split('.'):
		if part not in d:
			if not safe:
				return None
			raise ValueError(f"missing key {part} in path {path}")
		d = d[part]
	if callable(adapter):
		try:
			return adapter(d)
		except Exception as e:
			if not safe:
				return None
			raise
	return d
