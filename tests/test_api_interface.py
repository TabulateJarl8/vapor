"""Tests related to vapor's API interface."""

import json
from unittest.mock import patch

import pytest

from vapor.api_interface import (
	_parse_steam_user_games,
	check_game_is_native,
	get_anti_cheat_data,
	get_game_average_rating,
	get_steam_user_data,
	resolve_vanity_name,
)
from vapor.cache_handler import Cache
from vapor.data_structures import AntiCheatStatus, Game, Response
from vapor.exceptions import InvalidIDError, PrivateAccountError, UnauthorizedError

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

STEAM_VANITY_URL_DATA = {'response': {'steamid': '76561198872425795', 'success': 1}}

STEAM_VANITY_URL_DATA_INVALID = {'response': {'message': 'No match', 'success': 42}}

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

PROTONDB_API_RESPONSE = {
	'bestReportedTier': 'platinum',
	'confidence': 'strong',
	'score': 0.88,
	'tier': 'platinum',
	'total': 302,
	'trendingTier': 'platinum',
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


@pytest.mark.asyncio
async def test_get_game_average_rating() -> None:
	"""Test that we can get the average game rating from ProtonDB."""
	# test with no cache
	with (
		patch('vapor.api_interface.check_game_is_native', return_value=False),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=200,
				data=json.dumps(PROTONDB_API_RESPONSE),
			),
		),
	):
		assert await get_game_average_rating('227300', Cache()) == 'platinum'

	# test with cache
	with (
		patch('vapor.api_interface.check_game_is_native', return_value=False),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=200,
				data=json.dumps(PROTONDB_API_RESPONSE),
			),
		),
	):
		assert (
			await get_game_average_rating('227300', MockCache(has_game=True))  # pyright: ignore[reportArgumentType]
			== 'native'
		)

	# test with native game
	with patch('vapor.api_interface.check_game_is_native', return_value=True):
		assert await get_game_average_rating('227300', Cache()) == 'native'

	# test with request failure
	with (
		patch('vapor.api_interface.check_game_is_native', return_value=False),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=400,
				data='{}',
			),
		),
	):
		assert await get_game_average_rating('227300', Cache()) == 'pending'


@pytest.mark.asyncio
async def test_resolve_vanity_name() -> None:
	# test forbidden
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=403,
				data='{}',
			),
		),
		pytest.raises(UnauthorizedError),
	):
		await resolve_vanity_name('', '')

	# test invalid id
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=200,
				data=json.dumps(STEAM_VANITY_URL_DATA_INVALID),
			),
		),
		pytest.raises(InvalidIDError),
	):
		await resolve_vanity_name('', '')

	# test valid id
	with patch(
		'vapor.api_interface.async_get',
		return_value=MockResponse(
			status=200,
			data=json.dumps(STEAM_VANITY_URL_DATA),
		),
	):
		assert await resolve_vanity_name('', '') == '76561198872425795'


@pytest.mark.asyncio
async def test_get_steam_user_data() -> None:
	"""Test that getting the steam user data works."""
	# test invalid ID unauthorized
	with (
		patch(
			'vapor.api_interface.resolve_vanity_name',
			side_effect=UnauthorizedError(),
		),
		pytest.raises(UnauthorizedError),
	):
		await get_steam_user_data('', '')

	# test valid response
	with (
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=200,
				data=json.dumps(STEAM_USER_GAMES_DATA),
			),
		),
	):
		await get_steam_user_data('', '76561198872425795')

	# test invalid ID
	with (
		patch(
			'vapor.api_interface.resolve_vanity_name',
			side_effect=InvalidIDError(),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=400,
				data='{}',
			),
		),
	):
		await get_steam_user_data('', '76561198872425795')


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
		result = await _parse_steam_user_games(STEAM_USER_GAMES_DATA, cache)  # type: ignore
		assert len(result.game_ratings) == 2
		assert result.user_average == 'gold'


@pytest.mark.asyncio
async def test_parse_steam_user_priv_acct() -> None:
	"""Test that Steam private accounts are handled correctly."""
	cache = MockCache(has_game=True)
	with pytest.raises(PrivateAccountError):
		await _parse_steam_user_games({'response': {}}, cache)  # type: ignore


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
