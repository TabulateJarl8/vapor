from enum import Enum
from typing import Dict, List, NamedTuple

from platformdirs import user_config_path

CONFIG_DIR = user_config_path(appname='vapor', appauthor='tabulate', ensure_exists=True)
"""The config directory used to write files such as config and cache."""

PRIVATE_ACCOUNT_HELP_MESSAGE = """
Your Steam account is currently private. See README for more details.

Please change your Steam profile privacy settings:

1. From Steam, click the user dropdown and select "View my profile"
1. Click the "Edit Profile" button
2. Click the "Privacy Settings" tab
3. Set "Game details" to Public
4. Uncheck the Always keep my total playtime private option
""".strip()

_ANTI_CHEAT_COLORS: Dict[str, str] = {
	'Denied': 'red',
	'Broken': 'dark_orange3',
	'Planned': 'purple',
	'Running': 'blue',
	'Supported': 'green',
	'': '',
}


class AntiCheatStatus(Enum):
	"""Anti-Cheat status for a Steam game."""

	DENIED = 'Denied'
	BROKEN = 'Broken'
	PLANNED = 'Planned'
	RUNNING = 'Running'
	SUPPORTED = 'Supported'
	BLANK = ''


class AntiCheatData(NamedTuple):
	"""Game data from AreWeAntiCheatYet."""

	app_id: str
	"""The Steam app id of the game."""
	status: AntiCheatStatus
	"""The status of running the Anti-Cheat on Linux."""

	@property
	def color(self) -> str:
		"""The color of the Anti-Cheat status."""
		return _ANTI_CHEAT_COLORS[self.status.value]


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

	game_ratings: List[Game]
	"""The user's game ratings from ProtonDB."""
	user_average: str
	"""The user's average ProtonDB rating."""


RATING_DICT: Dict[str, ProtonDBRating] = {
	'borked': ProtonDBRating(weight=0, color='red'),
	'pending': ProtonDBRating(weight=1, color='blue'),
	'bronze': ProtonDBRating(weight=2, color='#CD7F32'),
	'silver': ProtonDBRating(weight=3, color='#A6A6A6'),
	'gold': ProtonDBRating(weight=4, color='#CFB53B'),
	'platinum': ProtonDBRating(weight=5, color='#B4C7DC'),
	'native': ProtonDBRating(weight=6, color='green'),
}
