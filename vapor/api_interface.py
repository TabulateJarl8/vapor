import json
from typing import Any, Iterable

import aiohttp

from vapor import cache_handler
from vapor.data_structures import (
	RATING_DICT,
	AntiCheatData,
	AntiCheatStatus,
	Game,
	Response,
	SteamUserData,
)
from vapor.exceptions import InvalidIDError, UnauthorizedError


def get_item_from_appid(iterable: Iterable, app_id: str) -> Any | None:
	"""Get an item from a list that has a certain app id.

	Args:
		iterable (Iterable): The iterable to search.
		app_id (str): The app id to search for.

	Returns:
		Any | None: The item if found. If not, None.
	"""
	return next((game for game in iterable if game.app_id == app_id), None)


async def get(session: aiohttp.ClientSession, url: str) -> Response:
	"""Async get request for fetching web content.

	Args:
		session (aiohttp.ClientSession): an aiohttp session.
		url (str): The URL to fetch data from.

	Returns:
		Response: A Response object containing the body and status code.
	"""
	async with session.get(url) as response:
		return Response(data=await response.text(), status=response.status)


async def check_game_is_native(app_id: str) -> bool:
	"""Check if a given Steam game has native Linux support.

	Args:
		app_id (int): The App ID of the game.

	Returns:
		bool: Whether or not the game has native Linux support.
	"""
	async with aiohttp.ClientSession() as session:
		data = await get(
			session,
			f'https://store.steampowered.com/api/appdetails?appids={app_id}&filters=platforms',
		)
		if data.status != 200:
			return False

		json_data = json.loads(data.data)[str(app_id)]

		if json_data.get('success', False):
			return json_data['data']['platforms'].get('linux', False)

		return False


async def get_anti_cheat_data() -> list[AntiCheatData] | None:
	"""Get's the anti-cheat data from cache. If expired, it will fetch new data and write that to cache.

	Returns:
		list[AntiCheatData] | None: The list of game anti-cheat data.
	"""
	cache = cache_handler.read_game_cache()
	if 'anticheat' in cache:
		return cache['anticheat']

	async with aiohttp.ClientSession() as session:
		data = await get(
			session,
			'https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json',
		)

		if data.status != 200:
			return None

		anti_cheat_data = json.loads(data.data)
		deserialized_data = [
			AntiCheatData(
				app_id=game['storeIds']['steam'],
				status=AntiCheatStatus(game['status']),
			)
			for game in anti_cheat_data
			if 'steam' in game['storeIds']
		]

		cache_handler.update_game_cache(anti_cheat_data=deserialized_data)

		return deserialized_data


async def get_game_average_rating(app_id: str, cache: dict[str, list[Any]]) -> str:
	"""Get the average game rating from ProtonDB.

	Args:
		id (str): The game ID.
		cache (dict[str, dict[str, str]]): The game cache. Can be an empty dict if no cache is wanted.

	Returns:
		str: A text rating from ProtonDB. gold, bronze, silver, etc.
	"""
	if 'games' in cache:
		game: Game | None = get_item_from_appid(cache['games'], app_id)
		if game is not None:
			return game.rating

	if await check_game_is_native(app_id):
		return 'native'

	async with aiohttp.ClientSession() as session:
		data = await get(
			session, f'https://www.protondb.com/api/v1/reports/summaries/{app_id}.json'
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
	async with aiohttp.ClientSession() as session:
		data = await get(
			session,
			f'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={api_key}&vanityurl={name}',
		)

		if data.status == 403:
			raise UnauthorizedError

		user_data = json.loads(data.data)
		if user_data['response']['success'] != 1:
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

	cache = cache_handler.read_game_cache()

	async with aiohttp.ClientSession() as session:
		data = await get(
			session,
			f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={id}&format=json&include_appinfo=1&include_played_free_games=1',
		)
		if data.status == 400:
			raise InvalidIDError
		if data.status == 401:
			raise UnauthorizedError

		games = json.loads(data.data)['response']['games']
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
			if game.app_id in cache:
				game_ratings_copy.remove(game)

		# update the game cache
		cache_handler.update_game_cache(game_ratings)

		# compute user average
		game_rating_nums = [RATING_DICT[game.rating][0] for game in game_ratings]
		user_average = round(sum(game_rating_nums) / len(game_rating_nums))
		user_average_text = [
			key for key, value in RATING_DICT.items() if value[0] == user_average
		][0]

		return SteamUserData(game_ratings=game_ratings, user_average=user_average_text)
