import pytest

from vapor.api_interface import (
	parse_anti_cheat_data,
	parse_steam_game_platform_info,
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


class MockCache:
	def __init__(self, has_game: bool):
		self.has_game_cache = has_game

	def get_game_data(self, app_id):  # noqa: ARG002
		return Game(
			name='Euro Truck Simulator 2',
			rating='native',
			playtime=12933,
			app_id='227300',
		)

	def update_cache(self, game_list):
		pass


@pytest.mark.asyncio
async def test_parse_steam_game_data():
	assert await parse_steam_game_platform_info(STEAM_GAME_DATA, '123456')
	assert not await parse_steam_game_platform_info(STEAM_GAME_DATA, '789012')
	assert not await parse_steam_game_platform_info(STEAM_GAME_DATA, '123')


@pytest.mark.asyncio
async def test_parse_anti_cheat_data():
	result = await parse_anti_cheat_data(ANTI_CHEAT_DATA)
	assert len(result) == 2
	assert result[0].app_id == '123456'
	assert result[0].status == AntiCheatStatus.DENIED
	assert result[1].status == AntiCheatStatus.SUPPORTED


@pytest.mark.asyncio
async def test_parse_steam_user_games():
	# mock function that returns gold as every games rating # noqa: ERA001
	async def _get_game_rating_func(*_):
		return 'gold'

	cache = MockCache(has_game=True)
	result = await parse_steam_user_games(
		STEAM_USER_GAMES_DATA, cache, _get_game_rating_func
	)
	assert len(result.game_ratings) == 2
	assert result.user_average == 'gold'


@pytest.mark.asyncio
async def test_parse_steam_user_priv_acct():
	# mock function that returns gold as every games rating # noqa: ERA001
	async def _get_game_rating_func(*_):
		return 'gold'

	cache = MockCache(has_game=True)
	with pytest.raises(PrivateAccountError):
		await parse_steam_user_games({'response': {}}, cache, _get_game_rating_func)
