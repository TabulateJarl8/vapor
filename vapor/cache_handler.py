import json
from datetime import datetime
from typing import Self

from vapor.data_structures import CONFIG_DIR, AntiCheatData, AntiCheatStatus, Game

CACHE_PATH = CONFIG_DIR / 'cache.json'
"""The path to the cache file."""

CACHE_INVALIDATION_DAYS = 7
"""The number of days until a cached game is invalid."""

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
"""Cache timestamp format."""


class Cache:
	def __init__(self):
		self._games_data: dict[str, Game] = {}
		self._anti_cheat_data: dict[str, AntiCheatData] = {}

	def _serialize_game_data(self) -> dict:
		"""Serialize the game data into a valid JSON dict.

		Returns:
			dict: Valid JSON dict.
		"""
		return {
			app_id: {
				'name': game.name,
				'rating': game.rating,
				'playtime': game.playtime,
				'timestamp': datetime.now().strftime(TIMESTAMP_FORMAT),
			}
			for app_id, game in self._games_data.items()
		}

	def _serialize_anti_cheat_data(self) -> dict:
		"""Serialize the anticheat data into a valid JSON dict.

		Returns:
			dict: Valid JSON dict.
		"""
		return {
			'data': {
				app_id: ac_data.status.value
				for app_id, ac_data in self._anti_cheat_data.items()
			},
			'timestamp': datetime.now().strftime(TIMESTAMP_FORMAT)
		}

	@property
	def has_game_cache(self) -> bool:
		"""Whether or not there is game cache loaded."""
		return bool(self._games_data)

	@property
	def has_anticheat_cache(self) -> bool:
		"""Whether or not there is anticheat cache loaded."""
		return bool(self._anti_cheat_data)

	def get_game_data(self, app_id: str) -> Game | None:
		"""Get game data from app ID.

		Args:
			app_id (str): The game's app ID.

		Returns:
			Game | None: The game data if exists. If not, None.
		"""
		return self._games_data.get(app_id, None)

	def get_anticheat_data(self, app_id: str) -> AntiCheatData | None:
		"""Get anticheat data from app ID.

		Args:
			app_id (str): The game's app ID.

		Returns:
			AntiCheatData | None: The game anticheat data if exists. If not, None.
		"""
		return self._anti_cheat_data.get(app_id, None)

	def write_cache_file(self) -> Self:
		"""Serialize data and write the cache file to the disk.

		Returns:
			Self: self.
		"""
		serialized_data = {
			'game_cache': self._serialize_game_data(),
			'anticheat_cache': self._serialize_anti_cheat_data(),
		}

		CACHE_PATH.write_text(json.dumps(serialized_data))
		return self

	def load_cache(self, prune=True) -> Self:
		"""Load and deserialize the cache.

		Args:
			prune (bool, optional): Whether or not to prune old cache entries. Defaults to True.

		Returns:
			Self: self.
		"""
		if prune:
			self.prune_cache()

		try:
			data = json.loads(CACHE_PATH.read_text())
		except Exception:
			return self

		if 'game_cache' in data:
			self._games_data = {
				app_id: Game(
					game_cache['name'],
					rating=game_cache['rating'],
					playtime=game_cache['playtime'],
					app_id=app_id,
				)
				for app_id, game_cache in data['game_cache'].items()
			}

		if 'anticheat_cache' in data:
			self._anti_cheat_data = {
				app_id: AntiCheatData(app_id=app_id, status=AntiCheatStatus(status))
				for app_id, status in data['anticheat_cache']['data'].items()
			}

		return self

	def update_cache(
		self,
		game_list: list[Game] | None = None,
		anti_cheat_list: list[AntiCheatData] | None = None,
	) -> Self:
		"""Update the cache file with new game and anticheat data.

		Args:
			game_list (list[Game] | None, optional): List of new game data. Defaults to None.
			anti_cheat_list (list[AntiCheatData] | None, optional): List of new anticheat data. Defaults to None.

		Returns:
			Self: self.
		"""
		self.load_cache()

		if game_list:
			for game in game_list:
				self._games_data[game.app_id] = game

		if anti_cheat_list:
			for ac in anti_cheat_list:
				self._anti_cheat_data[ac.app_id] = ac

		self.write_cache_file()
		return self

	def prune_cache(self) -> Self:
		"""Remove the old entries from the cache file.

		Returns:
			Self: self.
		"""
		try:
			data = json.loads(CACHE_PATH.read_text())
		except Exception:
			return self

		if 'game_cache' in data:
			for app_id, val in data['game_cache'].items():
				try:
					parsed_date = datetime.strptime(val['timestamp'], TIMESTAMP_FORMAT)
					if (datetime.now() - parsed_date).days > CACHE_INVALIDATION_DAYS:
						# cache is too old, delete game
						del data[app_id]

				except ValueError:
					# invalid datetime format
					del data[app_id]

		if 'anticheat_cache' in data:
			try:
				parsed_date = datetime.strptime(
					data['anticheat_cache']['timestamp'], TIMESTAMP_FORMAT
				)
				if (datetime.now() - parsed_date).days > CACHE_INVALIDATION_DAYS:
					# cache is too old, delete game
					del data['anticheat_cache']

			except ValueError:
				# invalid datetime format
				del data['anticheat_cache']

		CACHE_PATH.write_text(json.dumps(data))

		return self
