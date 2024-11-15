"""Vapor's global data structures."""

from enum import Enum
from typing import Dict, List, NamedTuple, TypedDict

from platformdirs import user_config_path
from typing_extensions import NotRequired

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

HTTP_SUCCESS = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
STEAM_USER_ID_LENGTH = 17


_ANTI_CHEAT_COLORS: Dict[str, str] = {
	'Denied': 'red',
	'Broken': 'dark_orange3',
	'Planned': 'purple',
	'Running': 'blue',
	'Supported': '#02b302',
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
	"""A Steam game with it's associated ProtonDB info."""

	name: str
	"""The name of the game."""
	rating: str
	"""The ProtonDB rating."""
	playtime: int
	"""The game's playtime."""
	app_id: str
	"""The game's App ID."""


class SteamUserData(NamedTuple):
	"""The data for a steam user.

	Includes a list of games and their respective ProtonDB ratings,
	as well as the user's average ProtonDB rating.
	"""

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
	'native': ProtonDBRating(weight=6, color='#02b302'),
}


class _Platforms(TypedDict):
	"""Available platforms a game can run on in Steam.

	Attributes:
		linux (bool): Linux
		mac (bool): MacOS
		windows (bool): Windows
	"""

	linux: bool
	mac: bool
	windows: bool


class _GamePlatformData(TypedDict):
	"""Contains different platforms a game is supported on.

	Attributes:
		platforms (_Platforms): The platforms the game is supported on
	"""

	platforms: _Platforms


class SteamAPIPlatformsResponse(TypedDict):
	"""Steam API response for which platforms a game is supported on.

	Attributes:
		success (bool): Whether or not the request was a success
		data (_GamePlatformData): Dictionary containing the platforms the game is on
	"""

	success: bool
	data: _GamePlatformData


class AntiCheatAPIResponse(TypedDict):
	"""AreWeAntiCheatYet anticheat data.

	Attributes:
		storeIds (Dict[str, str]): Distribution platforms the the game's ID on each
		status (AntiCheatStatus): Game's current anticheat status
	"""

	storeIds: Dict[str, str]
	status: AntiCheatStatus


class ProtonDBAPIResponse(TypedDict):
	"""ProtonDB response for a game's compatibility.

	Attributes:
		bestReportedTier (str): best tier of compatibility that has been reported
		confidence (str): confidence of the compatibility rating
		score (float):
		tier (str): game's current tier of compatibility
		total (int): total reports maybe?
		trendingTier (str): current trending tier of compatibility
	"""

	bestReportedTier: str
	confidence: str
	score: float
	tier: str
	total: int
	trendingTier: str


class _SteamAPINameResolutionResponseData(TypedDict):
	"""Subdictionary containing a Steam user's Steam ID.

	Attributes:
		steamid (str): Steam ID of a user
		success (int): Whether or not the server succeeded in finding the ID
	"""

	steamid: str
	success: int


class SteamAPINameResolutionResponse(TypedDict):
	"""Steam API response when resolving a vanity name to a user ID.

	Attributes:
		response (_SteamAPINameResolutionResponseData): Response containing user's ID
	"""

	response: _SteamAPINameResolutionResponseData


class _SteamAPIGameInfo(TypedDict):
	"""Steam API Response containing Game metadata.

	Attributes:
		appid (int): Game App ID
		name (str): Game name
		playtime_forever (int): Full playtime a user has in the game
		img_icon_url (str):
		has_community_visible_stats (bool):
		playtime_windows_forever (int): Playtime on Windows
		playtime_mac_forever (int): Playtime on MacOS
		playtime_linux_forever (int): Playtime on Linux
		playtime_deck_forever (int): Playtime on the Steam Deck
		rtime_last_played (int): Time the user last played the game
		content_descriptorids (List[int]):
		playtime_disconnected (int): Total playtime while not connected to the internet
	"""

	appid: int
	name: str
	playtime_forever: int
	img_icon_url: str
	has_community_visible_stats: bool
	playtime_windows_forever: int
	playtime_mac_forever: int
	playtime_linux_forever: int
	playtime_deck_forever: int
	rtime_last_played: int
	content_descriptorids: List[int]
	playtime_disconnected: int


class _SteamAPIUserGameList(TypedDict):
	"""Subdictionary in Steam Owned Games API response.

	Contains a total game count and the list of a user's owned games.

	Attributes:
		game_count (int): Total number of games a user owns
		games (List[_SteamAPIGameInfo]): List of games the user owns with metadata
	"""

	game_count: int
	games: List[_SteamAPIGameInfo]


class SteamAPIUserDataResponse(TypedDict):
	"""Defines spec for Steam API user data for owned games.

	Attributes:
		response (_SteamAPIUserGameList): The actual data of the response is stored in here
	"""

	response: _SteamAPIUserGameList


class SerializedGameData(TypedDict):
	"""Serialized game data for caching.

	Attributes:
		name (str): Name of the game
		rating (str): Game's ProtonDB rating
		timestamp (str): Last updated
	"""

	name: str
	rating: str
	timestamp: str


class SerializedAnticheatData(TypedDict):
	"""Serialized anticheat data for caching.

	Attributes:
		data (Dict[str, str]): Dictionary of app_id: anticheat_status
		timestamp (str): Last updated
	"""

	data: Dict[str, str]
	timestamp: str


class CacheFile(TypedDict):
	"""Fully aggregated cache file as JSON.

	Attributes:
		game_cache (NotRequired[Dict[str, SerializedGameData]]): Optional game cache
		anticheat_cache (NotRequired[SerializedAnticheatData]): Optional anticheat cache
	"""

	game_cache: NotRequired[Dict[str, SerializedGameData]]
	anticheat_cache: NotRequired[SerializedAnticheatData]
