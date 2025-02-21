"""Tests related to vapor's API interface."""

import json
from unittest.mock import patch

import pytest

from vapor.api_interface import (
	_parse_steam_user_games,  # pyright: ignore[reportPrivateUsage]
	check_game_is_native,
	get_anti_cheat_data,
	get_game_average_rating,
	get_steam_user_data,
	resolve_vanity_name,
)
from vapor.cache_handler import Cache
from vapor.data_structures import AntiCheatStatus, Game, Response
from vapor.exceptions import InvalidIDError, PrivateAccountError, UnauthorizedError

# Test data fixtures
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

	def __init__(self, has_game: bool = False, has_anticheat: bool = False) -> None:
		"""Construct a new MockCache object."""
		self.has_game_cache: bool = has_game
		self.has_anticheat_cache: bool = has_anticheat

	def get_game_data(self, app_id: None) -> Game:  # pyright: ignore[reportUnusedParameter]
		"""Return a set Game data for testing."""
		return Game(
			name='Euro Truck Simulator 2',
			rating='native',
			playtime=12933,
			app_id='227300',
		)

	def update_cache(self, game_list: None) -> None:  # pyright: ignore[reportUnusedParameter]
		"""Update cache with dummy function. Does nothing."""


class MockResponse:
	"""Mock API response."""

	def __init__(self, status: int, data: str) -> None:
		"""Construct a new MockResponse."""
		self.status: int = status
		self.data: str = data


# Game Rating Tests
@pytest.mark.asyncio
async def test_get_game_rating_no_cache() -> None:
	"""Test getting game rating without cache."""
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


@pytest.mark.asyncio
async def test_get_game_rating_with_cache() -> None:
	"""Test getting game rating with cache."""
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


@pytest.mark.asyncio
async def test_get_game_rating_native() -> None:
	"""Test getting rating for native game."""
	with patch('vapor.api_interface.check_game_is_native', return_value=True):
		assert await get_game_average_rating('227300', Cache()) == 'native'


@pytest.mark.asyncio
async def test_get_game_rating_request_failure() -> None:
	"""Test handling of failed rating request."""
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


# Vanity Name Resolution Tests
@pytest.mark.asyncio
async def test_resolve_vanity_name_forbidden() -> None:
	"""Test handling of forbidden vanity name resolution."""
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


@pytest.mark.asyncio
async def test_resolve_vanity_name_invalid() -> None:
	"""Test handling of invalid vanity name."""
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


@pytest.mark.asyncio
async def test_resolve_vanity_name_valid() -> None:
	"""Test successful vanity name resolution."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=MockResponse(
			status=200,
			data=json.dumps(STEAM_VANITY_URL_DATA),
		),
	):
		assert await resolve_vanity_name('', '') == '76561198872425795'


# Steam User Data Tests
@pytest.mark.asyncio
async def test_get_steam_user_data_unauthorized() -> None:
	"""Test handling of unauthorized Steam user data request."""
	with (
		patch(
			'vapor.api_interface.resolve_vanity_name',
			side_effect=UnauthorizedError(),
		),
		pytest.raises(UnauthorizedError),
	):
		await get_steam_user_data('', '')


@pytest.mark.asyncio
async def test_get_steam_user_data_valid() -> None:
	"""Test successful Steam user data retrieval."""
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


@pytest.mark.asyncio
async def test_get_steam_user_data_invalid_id() -> None:
	"""Test handling of invalid Steam ID."""
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
		pytest.raises(InvalidIDError),
	):
		await get_steam_user_data('', 'n/a')


@pytest.mark.asyncio
async def test_get_steam_user_data_unauthorized_valid_id() -> None:
	"""Test handling of unauthorized request with valid Steam ID."""
	with (
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(
				status=401,
				data='{}',
			),
		),
		pytest.raises(UnauthorizedError),
	):
		await get_steam_user_data('', '76561198872425795')


# Anti-Cheat Data Tests
@pytest.mark.asyncio
async def test_get_anti_cheat_data_valid() -> None:
	"""Test successful anti-cheat data retrieval."""
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=200, data=json.dumps(ANTI_CHEAT_DATA)),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		cache = await get_anti_cheat_data()
		assert cache is not None
		game_data = cache._anti_cheat_data  # pyright: ignore[reportPrivateUsage]
		assert len(game_data) == 2
		assert '123456' in game_data
		assert game_data['123456'].status == AntiCheatStatus.DENIED
		assert '789012' in game_data
		assert game_data['789012'].status == AntiCheatStatus.SUPPORTED


@pytest.mark.asyncio
async def test_get_anti_cheat_data_cached() -> None:
	"""Test anti-cheat data retrieval with existing cache."""
	with patch(
		'vapor.cache_handler.Cache.load_cache',
		return_value=MockCache(has_anticheat=True),
	):
		cache = await get_anti_cheat_data()
		assert cache is not None


@pytest.mark.asyncio
async def test_get_anti_cheat_data_invalid_response() -> None:
	"""Test handling of invalid anti-cheat data response."""
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=400, data=json.dumps(ANTI_CHEAT_DATA)),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		assert await get_anti_cheat_data() is None


@pytest.mark.asyncio
async def test_get_anti_cheat_data_invalid_data() -> None:
	"""Test handling of invalid anti-cheat data format."""
	with (
		patch(
			'vapor.api_interface.async_get',
			return_value=MockResponse(status=200, data='n/a'),
		),
		patch('vapor.cache_handler.Cache.load_cache', return_value=Cache()),
	):
		assert await get_anti_cheat_data() is None


# Steam User Games Parsing Tests
@pytest.mark.asyncio
async def test_parse_steam_user_games_valid() -> None:
	"""Test successful parsing of Steam user games."""
	with patch(
		'vapor.api_interface.get_game_average_rating',
		return_value='gold',
	):
		cache = MockCache(has_game=True)
		result = await _parse_steam_user_games(STEAM_USER_GAMES_DATA, cache)  # pyright: ignore[reportArgumentType]
		assert len(result.game_ratings) == 2
		assert result.user_average == 'gold'


@pytest.mark.asyncio
async def test_parse_steam_user_games_private() -> None:
	"""Test handling of private Steam account."""
	cache = MockCache(has_game=True)
	with pytest.raises(PrivateAccountError):
		await _parse_steam_user_games({'response': {}}, cache)  # pyright: ignore[reportArgumentType]


# Native Game Check Tests
@pytest.mark.asyncio
async def test_check_game_is_native_success() -> None:
	"""Test successful native game check."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 200),
	):
		assert not await check_game_is_native('123')
		assert await check_game_is_native('456')


@pytest.mark.asyncio
async def test_check_game_is_native_invalid() -> None:
	"""Test handling of invalid game ID for native check."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 200),
	):
		assert not await check_game_is_native('invalid')


@pytest.mark.asyncio
async def test_check_game_is_native_error() -> None:
	"""Test handling of API error during native check."""
	with patch(
		'vapor.api_interface.async_get',
		return_value=Response(json.dumps(STEAM_GAME_PLATFORM_DATA), 401),
	):
		assert not await check_game_is_native('456')
