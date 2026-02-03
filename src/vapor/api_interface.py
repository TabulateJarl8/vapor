"""Steam and ProtonDB API helper functions."""

from __future__ import annotations

import json
from typing import cast

import aiohttp

from vapor.cache_handler import Cache
from vapor.data_structures import (
	HTTP_BAD_REQUEST,
	HTTP_FORBIDDEN,
	HTTP_SUCCESS,
	HTTP_UNAUTHORIZED,
	RATING_DICT,
	STEAM_USER_ID_LENGTH,
	AntiCheatAPIResponse,
	AntiCheatData,
	AntiCheatStatus,
	Game,
	ProtonDBAPIResponse,
	Response,
	SteamAPINameResolutionResponse,
	SteamAPIPlatformsResponse,
	SteamAPIUserDataResponse,
	SteamUserData,
)
from vapor.exceptions import InvalidIDError, PrivateAccountError, UnauthorizedError


async def async_get(url: str) -> Response:
	"""Async get request for fetching web content.

	Args:
		url (str): The URL to fetch data from.

	Returns:
		Response: A Response object containing the body and status code.
	"""
	async with aiohttp.ClientSession() as session, session.get(url) as response:
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
	if data.status != HTTP_SUCCESS:
		return False

	json_data = cast(dict[str, SteamAPIPlatformsResponse], json.loads(data.data))

	# extract whether or not a game is Linux native
	if str(app_id) not in json_data:
		return False

	game_data = json_data[str(app_id)]
	return game_data.get('success', False) and game_data['data']['platforms'].get(
		'linux',
		False,
	)


async def get_anti_cheat_data() -> Cache | None:
	"""Get the anti-cheat data from cache.

	If expired, this function will fetch new data and write that to cache.

	Returns:
		Cache | None: The cache containing anti-cheat data.
	"""
	cache = Cache().load_cache()
	if cache.has_anticheat_cache:
		return cache

	data = await async_get(
		'https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json',
	)

	if data.status != HTTP_SUCCESS:
		return None

	try:
		anti_cheat_data = cast(list[AntiCheatAPIResponse], json.loads(data.data))
	except json.JSONDecodeError:
		return None

	# parse the data from AreWeAntiCheatYet
	deserialized_data = [
		AntiCheatData(
			app_id=game['storeIds']['steam'],
			status=AntiCheatStatus(game['status']),
		)
		for game in anti_cheat_data
		if 'steam' in game['storeIds']
	]

	cache.update_cache(anti_cheat_list=deserialized_data)

	return cache


async def get_game_average_rating(app_id: str, cache: Cache) -> str:
	"""Get the average game rating from ProtonDB.

	Args:
		app_id (str): The game ID.
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
		f'https://www.protondb.com/api/v1/reports/summaries/{app_id}.json',
	)
	if data.status != HTTP_SUCCESS:
		return 'pending'

	json_data = cast(ProtonDBAPIResponse, json.loads(data.data))

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

	if data.status == HTTP_FORBIDDEN:
		raise UnauthorizedError

	user_data = cast(SteamAPINameResolutionResponse, json.loads(data.data))
	if 'response' not in user_data or user_data['response']['success'] != 1:
		raise InvalidIDError

	return user_data['response']['steamid']


async def get_steam_user_data(api_key: str, user_id: str) -> SteamUserData:
	"""Fetch a steam user's games and get their ratings from ProtonDB.

	Args:
		api_key (str): Steam API key.
		user_id (str): The user's Steam ID or vanity name.

	Raises:
		InvalidIDError: If an invalid Steam ID is provided.
		UnauthorizedError: If an invalid Steam API key is provided.

	Returns:
		SteamUserData: The Steam user's data.
	"""
	# check if ID is a Steam ID or vanity URL
	if len(user_id) != STEAM_USER_ID_LENGTH or not user_id.startswith('76561198'):
		try:
			user_id = await resolve_vanity_name(api_key, user_id)
		except UnauthorizedError as e:
			raise UnauthorizedError from e
		except InvalidIDError:
			pass

	cache = Cache().load_cache()

	data = await async_get(
		f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={user_id}&format=json&include_appinfo=1&include_played_free_games=1',
	)
	if data.status == HTTP_BAD_REQUEST:
		raise InvalidIDError
	if data.status == HTTP_UNAUTHORIZED:
		raise UnauthorizedError

	user_data = cast(SteamAPIUserDataResponse, json.loads(data.data))

	return await _parse_steam_user_games(user_data, cache)


async def _parse_steam_user_games(
	data: SteamAPIUserDataResponse,
	cache: Cache,
) -> SteamUserData:
	"""Parse user data from the Steam API and return information on their games.

	Args:
		data (SteamAPIUserDataResponse): user data from the Steam API
		cache (Cache): the loaded Cache file

	Returns:
		SteamUserData: the user's Steam games and ProtonDB ratings

	Raises:
		PrivateAccountError: if `games` is not present in `data['response']`
			(the user's account was found but is private)
	"""
	game_data = data['response']

	if 'games' not in game_data:
		raise PrivateAccountError

	games = game_data['games']
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
	games_to_remove: list[Game] = [
		game
		for game in game_ratings_copy
		if cache.get_game_data(game.app_id) is not None
	]

	# we do this in a seperate loop so that we're not mutating the
	# iterable during iteration
	for game in games_to_remove:
		game_ratings_copy.remove(game)

	# update the game cache
	cache.update_cache(game_list=game_ratings)

	# compute user average
	game_rating_nums = [RATING_DICT[game.rating][0] for game in game_ratings]
	user_average = round(sum(game_rating_nums) / len(game_rating_nums))
	user_average_text = next(
		key for key, value in RATING_DICT.items() if value[0] == user_average
	)

	return SteamUserData(game_ratings=game_ratings, user_average=user_average_text)
