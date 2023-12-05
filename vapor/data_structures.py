from typing import NamedTuple


class ProtonDBRating(NamedTuple):
	"""A ProtonDB rating with a weight and a color."""

	weight: int
	"""The weight of the rating. 0 is lowest, 5 is highest."""
	color: str
	"""The rating's color."""


class Response(NamedTuple):
	"""A response from an aiohttp request."""

	data: str
	"""The response body."""
	status: int
	"""The reponse status code."""


class Game(NamedTuple):
	"""A Steam game with ProtonDB info."""

	name: str
	"""The name of the game."""
	rating: str
	"""The ProtonDB rating."""
	playtime: int
	"""The game's playtime."""


class SteamUserData(NamedTuple):
	"""The data for a steam user."""

	game_ratings: list[Game]
	"""The user's game ratings from ProtonDB."""
	user_average: str
	"""The user's average ProtonDB rating."""


RATING_DICT: dict[str, ProtonDBRating] = {
	'borked': ProtonDBRating(weight=0, color='red'),
	'pending': ProtonDBRating(weight=1, color='blue'),
	'bronze': ProtonDBRating(weight=2, color='#CD7F32'),
	'silver': ProtonDBRating(weight=3, color='#A6A6A6'),
	'gold': ProtonDBRating(weight=4, color='#CFB53B'),
	'platinum': ProtonDBRating(weight=5, color='#B4C7DC'),
}
