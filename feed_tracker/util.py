import os


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


def get_config(args, config, setting_path):
	arg_name = setting_path.replace('.', '_')
	if hasattr(args, arg_name) and getattr(args, arg_name):
		return getattr(args, arg_name)

	env_value = dget(os.environ, setting_path)
	if env_value:
		return env_value
	
	return dget(config, setting_path)


def validate_config(config):
	assert dget(config, 'database.url', type) is str, "Database URL must be supplied."
	assert dget(config, 'feeds', type) is list, "Feeds must be a list."
	assert len(dget(config, 'feeds')) > 0, "Feeds must be non-empty."
	assert type(dget(config, 'feeds')[0]) is str, "Feeds must be a list of strings."
