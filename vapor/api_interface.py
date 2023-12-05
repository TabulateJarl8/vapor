import json

import aiohttp

from vapor.data_structures import RATING_DICT, Game, Response, SteamUserData
from vapor.exceptions import InvalidIDError, UnauthorizedError


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


async def get_game_average_rating(id: str) -> str:
	"""Get the average game rating from ProtonDB.

	Args:
		id (str): The game ID.

	Returns:
		str: A text rating from ProtonDB. gold, bronze, silver, etc.
	"""
	async with aiohttp.ClientSession() as session:
		data = await get(
			session, f'https://www.protondb.com/api/v1/reports/summaries/{id}.json'
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
				rating=await get_game_average_rating(game['appid']),
				playtime=game['playtime_forever'],
			)
			for game in games
		]

		game_ratings.sort(key=lambda x: x.playtime)
		game_ratings.reverse()

		# compute user average
		game_rating_nums = [RATING_DICT[game.rating][0] for game in game_ratings]
		user_average = round(sum(game_rating_nums) / len(game_rating_nums))
		user_average_text = [
			key for key, value in RATING_DICT.items() if value[0] == user_average
		][0]

		return SteamUserData(game_ratings=game_ratings, user_average=user_average_text)
