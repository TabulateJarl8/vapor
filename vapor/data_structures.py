from typing import NamedTuple

from platformdirs import user_config_path

CONFIG_DIR = user_config_path(appname='vapor', appauthor='tabulate', ensure_exists=True)
"""The config directory used to write files such as config and cache."""


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
	app_id: str
	"""The game's App ID."""


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
	'native': ProtonDBRating(weight=6, color='green'),
}
