import json
from typing import Any, Dict, List, Optional

import aiohttp

from vapor.cache_handler import Cache
from vapor.data_structures import (
	RATING_DICT,
	AntiCheatData,
	AntiCheatStatus,
	Game,
	Response,
	SteamUserData,
)
from vapor.exceptions import InvalidIDError, PrivateAccountError, UnauthorizedError


async def async_get(url: str, **session_kwargs: Any) -> Response:
	"""Async get request for fetching web content.

	Args:
		url (str): The URL to fetch data from.
		**session_kwargs (Any): arguments to pass to aiohttp.ClientSession

	Returns:
		Response: A Response object containing the body and status code.
	"""
	async with aiohttp.ClientSession(**session_kwargs) as session, session.get(
		url
	) as response:
		return Response(data=await response.text(), status=response.status)


async def check_game_is_native(app_id: str) -> bool:
	"""Check if a given Steam game has native Linux support.

	Args:
		app_id (int): The App ID of the game.

	Returns:
		bool: Whether or not the game has native Linux support.
	"""
	data = await async_get(
		f'https://store.steampowered.com/api/appdetails?appids={app_id}&filters=platforms',
	)
	if data.status != 200:
		return False

	json_data = json.loads(data.data)

	return await parse_steam_game_platform_info(json_data, app_id)


async def parse_steam_game_platform_info(data: Dict, app_id: str) -> bool:
	"""Parse data from the Steam API and return whether or not the game is
	native to Linux.

	Args:
		data (Dict): the data from the Steam API.
		app_id (str): The App ID of the game

	Returns:
		bool: Whether or not the game has native Linux support.
	"""
	if str(app_id) not in data:
		return False

	json_data = data[str(app_id)]
	return json_data.get('success', False) and json_data['data']['platforms'].get(
		'linux', False
	)


async def get_anti_cheat_data() -> Optional[Cache]:
	"""Get's the anti-cheat data from cache. If expired, it will fetch new
	data and write that to cache.

	Returns:
		Optional[Cache]: The cache containing anti-cheat data.
	"""
	cache = Cache().load_cache()
	if cache.has_anticheat_cache:
		return cache

	data = await async_get(
		'https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json',
	)

	if data.status != 200:
		return None

	try:
		anti_cheat_data = json.loads(data.data)
	except json.JSONDecodeError:
		return None

	deserialized_data = await parse_anti_cheat_data(anti_cheat_data)

	cache.update_cache(anti_cheat_list=deserialized_data)

	return cache


async def parse_anti_cheat_data(data: List[Dict]) -> List[AntiCheatData]:
	"""Parse data from AreWeAntiCheatYet and return a list of
	AntiCheatData instances.

	Args:
		data (List[Dict]): The data from AreWeAntiCheatYet

	Returns:
		List[AntiCheatData]: the anticheat statuses of each game in the given data
	"""
	return [
		AntiCheatData(
			app_id=game['storeIds']['steam'],
			status=AntiCheatStatus(game['status']),
		)
		for game in data
		if 'steam' in game['storeIds']
	]


async def get_game_average_rating(app_id: str, cache: Cache) -> str:
	"""Get the average game rating from ProtonDB.

	Args:
		id (str): The game ID.
		cache (Cache): The game cache.

	Returns:
		str: A text rating from ProtonDB. gold, bronze, silver, etc.
	"""
	if cache.has_game_cache:
		game = cache.get_game_data(app_id)
		if game is not None:
			return game.rating

	if await check_game_is_native(app_id):
		return 'native'

	data = await async_get(
		f'https://www.protondb.com/api/v1/reports/summaries/{app_id}.json'
	)
	if data.status != 200:
		return 'pending'

	json_data = json.loads(data.data)

	return json_data.get('tier', 'pending')


async def resolve_vanity_name(api_key: str, name: str) -> str:
	"""Resolve a Steam vanity name into a Steam user ID.

	Args:
		api_key (str): The Steam API key.
		name (str): The user's vanity name.

	Raises:
		UnauthorizedError: If an invalid Steam API key is provided.
		InvalidIDError: If an invalid Steam vanity URL is provided.

	Returns:
		str: The Steam ID of the user.
	"""
	data = await async_get(
		f'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={api_key}&vanityurl={name}',
	)

	if data.status == 403:
		raise UnauthorizedError

	user_data = json.loads(data.data)
	if 'response' not in user_data or user_data['response']['success'] != 1:
		raise InvalidIDError

	return user_data['response']['steamid']


async def get_steam_user_data(api_key: str, id: str) -> SteamUserData:
	"""Fetch a steam user's games and get their ratings from ProtonDB.

	Args:
		api_key (str): Steam API key.
		id (str): The user's Steam ID or vanity name.

	Raises:
		InvalidIDError: If an invalid Steam ID is provided.
		UnauthorizedError: If an invalid Steam API key is provided.

	Returns:
		SteamUserData: The Steam user's data.
	"""
	# check if ID is a Steam ID or vanity URL
	if len(id) != 17 or not id.startswith('76561198'):
		try:
			id = await resolve_vanity_name(api_key, id)
		except UnauthorizedError as e:
			raise UnauthorizedError from e
		except InvalidIDError:
			pass

	cache = Cache().load_cache()

	data = await async_get(
		f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={id}&format=json&include_appinfo=1&include_played_free_games=1',
	)
	if data.status == 400:
		raise InvalidIDError
	if data.status == 401:
		raise UnauthorizedError

	data = json.loads(data.data)

	return await parse_steam_user_games(data, cache)


async def parse_steam_user_games(
	data: Dict,
	cache: Cache,
) -> SteamUserData:
	"""Parse user data from the Steam API and return information on their games.

	Args:
		data (Dict): user data from the Steam API
		cache (Cache): the loaded Cache file

	Returns:
		SteamUserData: the user's Steam games and ProtonDB ratings
	"""

	data = data['response']

	if 'games' not in data:
		raise PrivateAccountError

	games = data['games']
	game_ratings = [
		Game(
			name=game['name'],
			rating=await get_game_average_rating(str(game['appid']), cache),
			playtime=game['playtime_forever'],
			app_id=str(game['appid']),
		)
		for game in games
	]

	game_ratings.sort(key=lambda x: x.playtime)
	game_ratings.reverse()

	# remove all of the games that we used that were already cached
	# this ensures that the timestamps of those games don't get updated
	game_ratings_copy = game_ratings.copy()
	for game in game_ratings_copy:
		if cache.get_game_data(game.app_id) is not None:
			game_ratings_copy.remove(game)

	# update the game cache
	cache.update_cache(game_list=game_ratings)

	# compute user average
	game_rating_nums = [RATING_DICT[game.rating][0] for game in game_ratings]
	user_average = round(sum(game_rating_nums) / len(game_rating_nums))
	user_average_text = [
		key for key, value in RATING_DICT.items() if value[0] == user_average
	][0]

	return SteamUserData(game_ratings=game_ratings, user_average=user_average_text)
