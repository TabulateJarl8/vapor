import configparser

from vapor.data_structures import CONFIG_DIR

CONFIG_PATH = CONFIG_DIR / 'config.ini'
"""The path to the config file."""


def write_steam_api_key(api_key: str):
	"""Writes the Steam API key to the config file.

	Args:
		api_key (str): The Steam API key.
	"""
	try:
		data = configparser.ConfigParser()
		data.add_section('vapor')
		data.set('vapor', 'steam-api-key', api_key)
		with CONFIG_PATH.open('w') as f:
			data.write(f)
	except Exception:
		pass


def read_steam_api_key() -> str:
	"""Read the Steam API key from the config file if it exists.

	Returns:
		str: The API key if it exists. If not, an empty string.
	"""
	try:
		parser = configparser.ConfigParser()
		if CONFIG_PATH.exists():
			parser.read(CONFIG_PATH)
			if 'vapor' in parser.sections() and 'steam-api-key' in parser.options(
				'vapor'
			):
				return parser.get('vapor', 'steam-api-key')

		return ''
	except Exception:
		return ''
