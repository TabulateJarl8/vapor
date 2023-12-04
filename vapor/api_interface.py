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
		json_data = json.loads(data.data)
		if data.status != 200 or 'tier' not in json_data:
			return 'unknown'

		return json_data['tier']


async def get_steam_user_data(api_key: str, id: str) -> SteamUserData:
	"""Fetch a steam user's games and get their ratings from ProtonDB.

	Args:
			api_key (str): Steam API key.
			id (str): The user's Steam ID.

	Raises:
			InvalidIDError: If an invalid Steam ID is provided.
			UnauthorizedError: If an invalid Steam API key is provided.

	Returns:
			SteamUserData: The Steam user's data.
	"""
	async with aiohttp.ClientSession() as session:
		data = await get(
			session,
			f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={id}&format=json&include_appinfo=1',
		)
		if 'Bad Request' in data.data:
			raise InvalidIDError
		if 'Unauthorized' in data.data:
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
