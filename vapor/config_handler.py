import configparser

from vapor.data_structures import CONFIG_DIR

CONFIG_PATH = CONFIG_DIR / 'config.ini'
"""The path to the config file."""


# TODO: make this into a class so that i don't have to read it multiple times
def write_config(key: str, value: str):
	"""Writes a value to the config file.

	Args:
		key (str): The key to write.
		value (str): The value to write.
	"""
	try:
		data = configparser.ConfigParser()
		data.read(CONFIG_PATH)

		if not data.has_section('vapor'):
			data.add_section('vapor')

		data.set('vapor', key, value)
		with CONFIG_PATH.open('w') as f:
			data.write(f)
	except Exception:
		pass


def read_config(key: str) -> str:
	"""Read a value from the config file if it exists.

	Args:
		key (str): The key to read.

	Returns:
		str: The API key if it exists. If not, an empty string.
	"""
	try:
		parser = configparser.ConfigParser()
		if CONFIG_PATH.exists():
			parser.read(CONFIG_PATH)
			if 'vapor' in parser.sections() and key in parser.options('vapor'):
				return parser.get('vapor', key)

		return ''
	except Exception:
		return ''
