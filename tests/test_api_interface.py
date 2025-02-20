"""Tests related to vapor's API interface."""

import json
from unittest.mock import patch

import pytest

from vapor.api_interface import (
	check_game_is_native,
	get_anti_cheat_data,
	parse_steam_user_games,
)
from vapor.cache_handler import Cache
from vapor.data_structures import AntiCheatStatus, Game, Response
from vapor.exceptions import PrivateAccountError

STEAM_GAME_DATA = {
	'123456': {'success': True, 'data': {'platforms': {'linux': True}}},
	'789012': {'success': False},
}

ANTI_CHEAT_DATA = [
	{'storeIds': {'steam': '123456'}, 'status': 'Denied'},
	{'storeIds': {'steam': '789012'}, 'status': 'Supported'},
	{'storeIds': {'epic': 'something'}, 'status': 'Supported'},
]

STEAM_USER_GAMES_DATA = {
	'response': {
		'games': [
			{'appid': 123456, 'name': 'Test Game 1', 'playtime_forever': 100},
			{'appid': 789012, 'name': 'Test Game 2', 'playtime_forever': 200},
		],
	},
}

STEAM_GAME_PLATFORM_DATA = {
	'123': {
		'success': True,
		'data': {'platforms': {'windows': True, 'mac': False, 'linux': False}},
	},
	'456': {
		'success': True,
		'data': {'platforms': {'windows': False, 'mac': True, 'linux': True}},
	},
}


class MockCache:
	"""Mock Cache object with a set Game data."""

	def __init__(self, has_game: bool, has_anticheat: bool = False) -> None:
		"""Construct a new MockCache object."""
		self.has_game_cache = has_game
		self.has_anticheat_cache = has_anticheat

	def get_game_data(self, app_id: None) -> Game:
		"""Return a set Game data for testing.

		Args:
			app_id (None): unused argument.
		"""
		return Game(
			name='Euro Truck Simulator 2',
			rating='native',
			playtime=12933,
			app_id='227300',
		)

	def update_cache(self, game_list: None) -> None:
		"""Update cache with dummy function. Does nothing.

		Args:
			game_list (None): unused argument.
		"""


class MockResponse:
	"""Mock API response."""

	def __init__(self, status: int, data: str) -> None:
		"""Construct a new MockResponse."""
		self.status = status
		self.data = data


# def test_parse_steam_game_data() -> None:
# 	"""Test that Steam data is correctly parsed."""
# 	assert _extract_game_is_native(STEAM_GAME_DATA, '123456')
# 	assert not _extract_game_is_native(STEAM_GAME_DATA, '789012')
# 	assert not _extract_game_is_native(STEAM_GAME_DATA, '123')
#
#
@pytest.mark.asyncio
async def test_get_anti_cheat_data() -> None:
	"""Test that anti-cheat data is gotten correctly."""
	# test valid response
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=200, data=json.dumps(ANTI_CHEAT_DATA)),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		cache = await get_anti_cheat_data()
		assert cache is not None
		game_data = cache._anti_cheat_data
		assert len(game_data) == 2
		assert '123456' in game_data
		assert game_data['123456'].status == AntiCheatStatus.DENIED
		assert '789012' in game_data
		assert game_data['789012'].status == AntiCheatStatus.SUPPORTED

	# test existing cache
	with patch(
		'vapor.cache_handler.Cache.load_cache',
		return_value=MockCache(has_game=False, has_anticheat=True),
	):
		cache = await get_anti_cheat_data()
		assert cache is not None

	# test invalid response
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=400, data=json.dumps(ANTI_CHEAT_DATA)),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		assert await get_anti_cheat_data() is None

	# test invalid data
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=200, data='n/a'),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		assert await get_anti_cheat_data() is None


@pytest.mark.asyncio
async def test_parse_steam_user_games() -> None:
	"""Test that Steam games are parsed correctly."""
	with patch(
		'vapor.api_interface.get_game_average_rating',
		return_value='gold',
	):
		cache = MockCache(has_game=True)
		result = await parse_steam_user_games(STEAM_USER_GAMES_DATA, cache)  # type: ignore
		assert len(result.game_ratings) == 2
		assert result.user_average == 'gold'


@pytest.mark.asyncio
async def test_parse_steam_user_priv_acct() -> None:
	"""Test that Steam private accounts are handled correctly."""
	cache = MockCache(has_game=True)
	with pytest.raises(PrivateAccountError):
		await parse_steam_user_games({'response': {}}, cache)  # type: ignore


@pytest.mark.asyncio
async def test_check_game_is_native() -> None:
	"""Test that native games are correctly detected and errors are handled."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 200),
	):
		assert not await check_game_is_native('123')
		assert not await check_game_is_native('invalid')
		assert await check_game_is_native('456')

	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 401),
	):
		# this should say false even though 456 is native because it
		# should fail with a non-200 status code
		assert not await check_game_is_native('456')
