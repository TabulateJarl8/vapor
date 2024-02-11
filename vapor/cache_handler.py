import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from typing_extensions import Self

from vapor.data_structures import CONFIG_DIR, AntiCheatData, AntiCheatStatus, Game

CACHE_PATH = CONFIG_DIR / 'cache.json'
"""The path to the cache file."""

CACHE_INVALIDATION_DAYS = 7
"""The number of days until a cached game is invalid."""

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
"""Cache timestamp format."""


class Cache:
	def __init__(self):
		self.cache_path = CACHE_PATH
		self._games_data: Dict[str, Tuple[Game, str]] = {}
		self._anti_cheat_data: Dict[str, AntiCheatData] = {}
		self._anti_cheat_timestamp: str = ''

	def __repr__(self):
		return f'Cache({self.__dict__!r})'

	def _serialize_game_data(self) -> dict:
		"""Serialize the game data into a valid JSON dict.

		Returns:
			dict: Valid JSON dict.
		"""
		return {
			app_id: {
				'name': game[0].name,
				'rating': game[0].rating,
				'playtime': game[0].playtime,
				'timestamp': game[1],
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
			'timestamp': self._anti_cheat_timestamp,
		}

	@property
	def has_game_cache(self) -> bool:
		"""Whether or not there is game cache loaded."""
		return bool(self._games_data)

	@property
	def has_anticheat_cache(self) -> bool:
		"""Whether or not there is anticheat cache loaded."""
		return bool(self._anti_cheat_data)

	def get_game_data(self, app_id: str) -> Optional[Game]:
		"""Get game data from app ID.

		Args:
			app_id (str): The game's app ID.

		Returns:
			Optional[Game]: The game data if exists. If not, None.
		"""
		data = self._games_data.get(app_id, None)
		if data is not None:
			return data[0]

		return None

	def get_anticheat_data(self, app_id: str) -> Optional[AntiCheatData]:
		"""Get anticheat data from app ID.

		Args:
			app_id (str): The game's app ID.

		Returns:
			Optional[AntiCheatData]: The game anticheat data if exists. If not, None.
		"""
		data = self._anti_cheat_data.get(app_id, None)
		if data is not None:
			return data

		return None

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
			data = json.loads(self.cache_path.read_text())
		except Exception:
			return self

		if 'game_cache' in data:
			self._games_data = {
				app_id: (
					Game(
						game_cache['name'],
						rating=game_cache['rating'],
						playtime=game_cache['playtime'],
						app_id=app_id,
					),
					game_cache['timestamp'],
				)
				for app_id, game_cache in data['game_cache'].items()
			}

		if 'anticheat_cache' in data:
			self._anti_cheat_data = {
				app_id: AntiCheatData(app_id=app_id, status=AntiCheatStatus(status))
				for app_id, status in data['anticheat_cache']['data'].items()
			}
			self._anti_cheat_timestamp = data['anticheat_cache']['timestamp']

		return self

	def update_cache(
		self,
		game_list: Optional[List[Game]] = None,
		anti_cheat_list: Optional[List[AntiCheatData]] = None,
	) -> Self:
		"""Update the cache file with new game and anticheat data.

		Args:
			game_list (Optional[List[Game]], optional): List of new game data. Defaults to None.
			anti_cheat_list (Optional[List[AntiCheatData]], optional): List of new anticheat data. Defaults to None.

		Returns:
			Self: self.
		"""
		self.load_cache()

		if game_list:
			for game in game_list:
				if game.app_id not in self._games_data:
					timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
				else:
					timestamp = self._games_data[game.app_id][1]

				self._games_data[game.app_id] = (
					game,
					timestamp,
				)

		if anti_cheat_list:
			for ac in anti_cheat_list:
				self._anti_cheat_data[ac.app_id] = ac

			self._anti_cheat_timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

		serialized_data = {
			'game_cache': self._serialize_game_data(),
			'anticheat_cache': self._serialize_anti_cheat_data(),
		}

		self.cache_path.write_text(json.dumps(serialized_data))

		return self

	def prune_cache(self) -> Self:
		"""Remove the old entries from the cache file.

		Returns:
			Self: self.
		"""
		try:
			data = json.loads(self.cache_path.read_text())
		except Exception:
			return self

		if 'game_cache' in data:
			# cast this to a list to be able to modify while iterating
			for app_id, val in list(data['game_cache'].items()):
				try:
					parsed_date = datetime.strptime(val['timestamp'], TIMESTAMP_FORMAT)
					if (datetime.now() - parsed_date).days > CACHE_INVALIDATION_DAYS:
						# cache is too old, delete game
						del data['game_cache'][app_id]

				except ValueError:
					# invalid datetime format
					del data['game_cache'][app_id]

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

		self.cache_path.write_text(json.dumps(data))

		return self
