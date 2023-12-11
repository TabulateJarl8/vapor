import contextlib
import json
from datetime import datetime
from typing import Any

from vapor.data_structures import CONFIG_DIR, AntiCheatData, AntiCheatStatus, Game

CACHE_PATH = CONFIG_DIR / 'cache.json'
"""The path to the cache file."""

CACHE_INVALIDATION_DAYS = 7
"""The number of days until a cached game is invalid."""

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
"""Cache timestamp format."""


def update_game_cache(
	game_list: list[Game] | None = None,
	anti_cheat_data: list[AntiCheatData] | None = None,
):
	"""Update the cache file with a new list of games or anticheat.

	Args:
		game_list (list[Game] | None, optional): The list of games. Defaults to None.
		anti_cheat_data (list[AntiCheatData] | None, optional): The anti-cheat data to cache. Defaults to None.
	"""
	if game_list:
		serialized_games = {
			'games': {
				game.app_id: {
					'name': game.name,
					'rating': game.rating,
					'playtime': game.playtime,
					'timestamp': datetime.now().strftime(TIMESTAMP_FORMAT),
				}
				for game in game_list
			}
		}
	else:
		serialized_games = {}

	current_games = {}
	if CACHE_PATH.is_file():
		# try to read the current game cache into a dictionary
		with contextlib.suppress(Exception):
			current_games |= json.loads(CACHE_PATH.read_text())

	current_games |= serialized_games

	if anti_cheat_data:
		current_games['anticheat'] = {}
		current_games['anticheat']['data'] = {
			data.app_id: data.status.value for data in anti_cheat_data
		}
		current_games['anticheat']['timestamp'] = datetime.now().strftime(
			TIMESTAMP_FORMAT
		)

	CACHE_PATH.write_text(json.dumps(current_games))


def read_game_cache(invalidate_cache: bool = True) -> dict[str, list[Any]]:
	"""Read the game cache and optionally invalidate it.

	Args:
		invalidate_cache (bool, optional): Whether or not to invalidate the cache before reading it. Defaults to True.

	Returns:
		dict[str, dict[str, str]]: The dict of game cache.
	"""
	if invalidate_cache:
		invalidate_game_cache()

	try:
		data = json.loads(CACHE_PATH.read_text())
	except Exception:
		return {}

	game_data: dict[str, Any] = {}

	if 'games' in data:
		game_data['games'] = [
			Game(
				name=game['name'],
				rating=game['rating'],
				playtime=game['playtime'],
				app_id=app_id,
			)
			for app_id, game in data['games'].items()
		]

	if 'anticheat' in data:
		game_data['anticheat'] = [
			AntiCheatData(app_id=app_id, status=AntiCheatStatus(acstatus))
			for app_id, acstatus in data['anticheat']['data'].items()
		]

	return game_data


def invalidate_game_cache():
	"""Find cache entires that are older than 7 days and remove them."""
	try:
		cache = json.loads(CACHE_PATH.read_text())
	except Exception:
		CACHE_PATH.unlink(missing_ok=True)
		return

	if 'games' in cache:
		for app_id, data in cache['games'].items():
			try:
				parsed_date = datetime.strptime(data['timestamp'], TIMESTAMP_FORMAT)
				if (datetime.now() - parsed_date).days > 7:
					# cache is too old, delete game
					del cache[app_id]

			except ValueError:
				# invalid datetime format
				del cache[app_id]

	if 'anticheat' in cache:
		parsed_date = datetime.strptime(
			cache['anticheat']['timestamp'], TIMESTAMP_FORMAT
		)
		if (datetime.now() - parsed_date).days > 7:
			# cache is too old, delete data
			del cache['anticheat']

	CACHE_PATH.write_text(json.dumps(cache))
