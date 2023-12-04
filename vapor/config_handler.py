import configparser
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / 'vapor_config.ini'


def write_steam_api_key(api_key: str):
	try:
		data = configparser.ConfigParser()
		data.add_section('vapor')
		data.set('vapor', 'steam-api-key', api_key)
		with CONFIG_PATH.open('w') as f:
			data.write(f)
	except Exception:
		pass


def read_steam_api_key() -> str:
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
