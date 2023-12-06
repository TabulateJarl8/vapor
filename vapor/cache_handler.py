import contextlib
import json
from datetime import datetime

from vapor.data_structures import CONFIG_DIR, Game

CACHE_PATH = CONFIG_DIR / 'cache.json'
"""The path to the cache file."""

CACHE_INVALIDATION_DAYS = 7
"""The number of days until a cached game is invalid."""

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
"""Cache timestamp format."""


def update_game_cache(game_list: list[Game]):
	"""Update the cache file with a new list of games.

	Args:
		game_list (list[Game]): The list of games.
	"""
	serialized_games = {
		game.app_id: {
			'rating': game.rating,
			'timestamp': datetime.now().strftime(TIMESTAMP_FORMAT),
		}
		for game in game_list
	}

	current_games = {}
	if CACHE_PATH.is_file():
		# try to read the current game cache into a dictionary
		with contextlib.suppress(Exception):
			current_games |= json.loads(CACHE_PATH.read_text())

	current_games |= serialized_games

	CACHE_PATH.write_text(json.dumps(current_games))


def read_game_cache(invalidate_cache: bool = True) -> dict[str, dict[str, str]]:
	"""Read the game cache and optionally invalidate it.

	Args:
		invalidate_cache (bool, optional): Whether or not to invalidate the cache before reading it. Defaults to True.

	Returns:
		dict[str, dict[str, str]]: The dict of game cache.
	"""
	if invalidate_cache:
		invalidate_game_cache()

	try:
		return json.loads(CACHE_PATH.read_text())
	except Exception:
		return {}


def invalidate_game_cache():
	"""Find cache entires that are older than 7 days and remove them."""
	cache = read_game_cache(invalidate_cache=False)

	for app_id, data in cache.items():
		try:
			parsed_date = datetime.strptime(data['timestamp'], TIMESTAMP_FORMAT)
			if (datetime.now() - parsed_date).days > 7:
				# cache is too old, delete game
				del cache[app_id]

		except ValueError:
			# invalid datetime format
			del cache[app_id]

	CACHE_PATH.write_text(json.dumps(cache))
