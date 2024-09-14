"""Tests related to vapor's API interface."""

import json
from unittest.mock import patch

import pytest

from vapor.api_interface import (
	Response,
	_extract_game_is_native,
	check_game_is_native,
	parse_anti_cheat_data,
	parse_steam_user_games,
)
from vapor.data_structures import AntiCheatStatus, Game
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
		]
	}
}

STEAM_GAME_PLATFORM_DATA = {
	'123': {
		'success': True,
		'data': {'platforms': {'windows': True, 'mac': False, 'linux': False}},
	}
}


class MockCache:
	"""Mock Cache object with a set Game data."""

	def __init__(self, has_game: bool):
		"""Construct a new MockCache object."""
		self.has_game_cache = has_game

	def get_game_data(self, app_id):  # noqa: ARG002
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

	def update_cache(self, game_list):
		"""Update cache with dummy function. Does nothing.

		Args:
			game_list (None): unused argument.
		"""


@pytest.mark.asyncio
async def test_parse_steam_game_data():
	"""Test that Steam data is correctly parsed."""
	assert await _extract_game_is_native(STEAM_GAME_DATA, '123456')
	assert not await _extract_game_is_native(STEAM_GAME_DATA, '789012')
	assert not await _extract_game_is_native(STEAM_GAME_DATA, '123')


@pytest.mark.asyncio
async def test_parse_anti_cheat_data():
	"""Test that anti-cheat data is parsed correctly."""
	result = await parse_anti_cheat_data(ANTI_CHEAT_DATA)
	assert len(result) == 2
	assert result[0].app_id == '123456'
	assert result[0].status == AntiCheatStatus.DENIED
	assert result[1].status == AntiCheatStatus.SUPPORTED


@pytest.mark.asyncio
async def test_parse_steam_user_games():
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
async def test_parse_steam_user_priv_acct():
	"""Test that Steam private accounts are handled correctly."""
	cache = MockCache(has_game=True)
	with pytest.raises(PrivateAccountError):
		await parse_steam_user_games({'response': {}}, cache)  # type: ignore


@pytest.mark.asyncio
async def test_check_game_is_native():
	"""Test that native games are correctly detected."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 200),
	):
		assert not await check_game_is_native('123')
