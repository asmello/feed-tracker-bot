import os
import inspect


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


def print_welcome():
	art = r"""
	 _____                           ______       _   
	/  ___|                          | ___ \     | |  
	\ `--.  ___  _   _ _ __ ___ ___  | |_/ / ___ | |_ 
	 `--. \/ _ \| | | | '__/ __/ _ \ | ___ \/ _ \| __|
	/\__/ / (_) | |_| | | | (_|  __/ | |_/ / (_) | |_ 
	\____/ \___/ \__,_|_|  \___\___| \____/ \___/ \__|

	==================================================

	"""
	print(inspect.cleandoc(art))
