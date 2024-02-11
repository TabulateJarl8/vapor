from unittest.mock import Mock, patch

import pytest
from rich.text import Text
from textual.color import Color
from textual.coordinate import Coordinate
from textual.widgets import Button, DataTable
from textual.widgets._data_table import CellDoesNotExist
from textual.widgets._toast import Toast

from tests.test_config import InMemoryPath
from vapor.api_interface import InvalidIDError, PrivateAccountError, UnauthorizedError
from vapor.config_handler import Config
from vapor.data_structures import (
	RATING_DICT,
	AntiCheatData,
	AntiCheatStatus,
	Game,
	SteamUserData,
)
from vapor.main import PrivateAccountScreen, SettingsScreen, SteamApp

STEAM_USER_DATA = SteamUserData(
	game_ratings=[
		Game('Cool Game', 'gold', 5, '123'),
		Game('No Anticheat Game', 'gold', 5, '456'),
	],
	user_average='gold',
)
STEAM_ID_URL = 'https://steamcommunity.com/id/tabulatejarl8/'
STEAM_PROFILE_URL = 'https://steamcommunity.com/profiles/76561198872425795'


@pytest.fixture
def config():
	cfg = Config()
	cfg._config_path = InMemoryPath()  # type: ignore
	return cfg


class MockCache:
	def get_anticheat_data(self, id):
		if id == '123':
			return AntiCheatData('123', AntiCheatStatus.DENIED)
		return None


@pytest.mark.asyncio
async def test_first_startup(config):
	app = SteamApp(config)
	async with app.run_test() as _:
		assert app.query_one('#api-key').value == ''  # type: ignore
		assert app.query_one('#user-id').value == ''  # type: ignore
		assert app.query_one(DataTable).get_cell_at(Coordinate(0, 0)) == ''


@pytest.mark.asyncio
async def test_invalid_input_data(config):
	app = SteamApp(config)

	async with app.run_test() as pilot:
		assert await pilot.click('#api-key')
		await pilot.press('q')

		# test that the input is highlighted red
		assert app.query_one('#api-key').styles.border_bottom == (
			'tall',
			Color(185, 60, 91),
		)

		# we need to type something and delete it, else the input will just be
		# focused and not errored
		assert await pilot.click('#user-id')
		await pilot.press('q', 'backspace')

		# test that the input is highlighted red
		assert app.query_one('#user-id').styles.border_bottom == (
			'tall',
			Color(185, 60, 91),
		)


@pytest.mark.asyncio
async def test_valid_input_data(config):
	app = SteamApp(config)

	async with app.run_test() as pilot:
		assert await pilot.click('#api-key')
		# type A 32 times to simulate a valid api key
		await pilot.press(*['A'] * 32)

		# test that the input is highlighted green
		assert app.query_one('#api-key').styles.border_bottom == (
			'tall',
			Color(78, 191, 113),
		)

		# any username will work
		assert await pilot.click('#user-id')
		await pilot.press('q')

		# test that the input is highlighted green
		assert app.query_one('#user-id').styles.border_bottom == (
			'tall',
			Color(78, 191, 113),
		)


def test_create_app():
	"""This is to cover the default class instantiation with the default Config"""
	with patch('vapor.config_handler.Config.read_config', return_value=True):
		SteamApp()


@pytest.mark.asyncio
async def test_table_population_username(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=MockCache()), patch(
		'vapor.main.get_steam_user_data', return_value=STEAM_USER_DATA
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			# submit the query
			assert await pilot.click('#submit-button')

			# check that the user average rating was created correctly
			assert app.query_one('#user-rating').renderable == Text.assemble(  # type: ignore
				'User Average Rating: ',
				(
					'Gold',
					RATING_DICT['gold'][1],
				),
			)

			# check the the appropriate game was added to the table
			table = app.query_one(DataTable)
			assert table.get_cell_at(Coordinate(0, 0)) == 'Cool Game'
			assert table.get_cell_at(Coordinate(0, 1)) == Text(
				'Gold', RATING_DICT['gold'][1]
			)
			assert table.get_cell_at(Coordinate(0, 2)) == Text('Denied', 'red')

			# check that no anticheat data was added for the second game
			assert table.get_cell_at(Coordinate(1, 2)) == Text('')

			# check that one two rows were added to the table
			with pytest.raises(CellDoesNotExist):
				table.get_cell_at(Coordinate(2, 0))


@pytest.mark.asyncio
async def test_parse_steam_url_id(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=MockCache()), patch(
		'vapor.main.get_steam_user_data', return_value=STEAM_USER_DATA
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			# test /id/ URL
			assert await pilot.click('#user-id')
			await pilot.press(*list(STEAM_ID_URL))

			# submit the query
			assert await pilot.click('#submit-button')

			# check that username was parsed correctly
			assert app.query_one('#user-id').value == 'tabulatejarl8'  # type: ignore


@pytest.mark.asyncio
async def test_parse_steam_url_profiles(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=MockCache()), patch(
		'vapor.main.get_steam_user_data', return_value=STEAM_USER_DATA
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			assert await pilot.click('#user-id')

			# type in the /profiles/ URL
			await pilot.press(*list(STEAM_PROFILE_URL))

			# submit the query
			assert await pilot.click('#submit-button')

			# check that username was parsed correctly
			assert app.query_one('#user-id').value == '76561198872425795'  # type: ignore


@pytest.mark.asyncio
async def test_no_cache_user_query(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=None), patch(
		'vapor.main.get_steam_user_data', return_value=STEAM_USER_DATA
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			# submit the query
			assert await pilot.click('#submit-button')

			# check that no anticheat data is present since we dont have cache
			assert app.query_one(DataTable).get_cell_at(Coordinate(0, 2)) == Text('')


@pytest.mark.asyncio
async def test_user_id_preservation(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=None), patch(
		'vapor.main.get_steam_user_data', return_value=STEAM_USER_DATA
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			# make sure theres no username by default
			assert app.config.get_value('user-id') == ''

			# set the preserve user id config option
			app.config.set_value('preserve-user-id', 'true')

			# type in 'username' as the username
			assert await pilot.click('#user-id')
			await pilot.press(*list('username'))

			# submit the query
			assert await pilot.click('#submit-button')

			# check if the username is in the config
			assert app.config.get_value('user-id') == 'username'


@pytest.mark.asyncio
async def test_invalid_id_error(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=None), patch(
		'vapor.main.get_steam_user_data', side_effect=Mock(side_effect=InvalidIDError)
	):
		app = SteamApp(config)

		async with app.run_test(notifications=True) as pilot:
			# submit the query
			assert await pilot.click('#submit-button')

			# check that notification was posted and that we can query the Toast
			assert app.query_one(Toast)._notification.message == 'Invalid Steam User ID'


@pytest.mark.asyncio
async def test_unauthorized_error(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=None), patch(
		'vapor.main.get_steam_user_data',
		side_effect=Mock(side_effect=UnauthorizedError),
	):
		app = SteamApp(config)

		async with app.run_test(notifications=True) as pilot:
			# submit the query
			assert await pilot.click('#submit-button')

			# check that notification was posted and that we can query the Toast
			assert app.query_one(Toast)._notification.message == 'Invalid Steam API Key'


@pytest.mark.asyncio
async def test_private_account_screen(config):
	with patch('vapor.main.get_anti_cheat_data', return_value=None), patch(
		'vapor.main.get_steam_user_data',
		side_effect=Mock(side_effect=PrivateAccountError),
	):
		app = SteamApp(config)

		async with app.run_test() as pilot:
			# submit the query
			assert await pilot.click('#submit-button')

			# check that the private account screen is shown to the user
			assert isinstance(app.screen, PrivateAccountScreen)

			# close the screen
			assert await pilot.click(Button)

			# check that the screen was closed
			assert not isinstance(app.screen_stack[-1], PrivateAccountScreen)


@pytest.mark.asyncio
async def test_settings_screen(config):
	app = SteamApp(config)

	# check that theres no default value
	assert app.config.get_value('preserve-user-id') == ''

	async with app.run_test() as pilot:
		# open the settings screen
		await pilot.press('ctrl+s')

		# check that the settings screen is shown to the user
		assert isinstance(app.screen, SettingsScreen)

		# # check that the default value was set
		# assert app.config.get_value('preserve-user-id') == 'false'

		# # switch on the preserve user id setting
		# assert await pilot.click(Switch)

		# # check that config value was set
		# assert app.config.get_value('preserve-user-id') == 'true'

		# # switch off the preserve user id setting
		# assert await pilot.click(Switch)

		# # check that config value was set
		# assert app.config.get_value('preserve-user-id') == 'false'
