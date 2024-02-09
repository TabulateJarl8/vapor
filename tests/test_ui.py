from unittest.mock import patch

import pytest
from rich.text import Text
from textual.color import Color
from textual.coordinate import Coordinate
from textual.widgets import DataTable
from textual.widgets._data_table import CellDoesNotExist

from tests.test_config import InMemoryPath
from vapor.config_handler import Config
from vapor.data_structures import (
	RATING_DICT,
	AntiCheatData,
	AntiCheatStatus,
	Game,
	SteamUserData,
)
from vapor.main import SteamApp

STEAM_USER_DATA = SteamUserData(
	game_ratings=[Game('Cool Game', 'gold', 5, '123')], user_average='gold'
)


@pytest.fixture
def config():
	cfg = Config()
	cfg._config_path = InMemoryPath()
	return cfg


class MockCache:
	def get_anticheat_data(self, _):
		return AntiCheatData('789012', AntiCheatStatus.DENIED)


@pytest.mark.asyncio
async def test_first_startup(config):
	app = SteamApp(config)
	async with app.run_test() as _:
		assert app.query_one('#api-key').value == ''
		assert app.query_one('#user-id').value == ''
		assert app.query_one(DataTable).get_cell_at(Coordinate(0, 0)) == ''


@pytest.mark.asyncio
async def test_invalid_input_data(config):
	app = SteamApp(config)

	async with app.run_test() as pilot:
		await pilot.click('#api-key')
		await pilot.press('q')

		# test that the input is highlighted red
		assert app.query_one('#api-key').styles.border_bottom == (
			'tall',
			Color(185, 60, 91),
		)

		# we need to type something and delete it, else the input will just be
		# focused and not errored
		await pilot.click('#user-id')
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
		await pilot.click('#api-key')
		# type A 32 times to simulate a valid api key
		await pilot.press(*['A'] * 32)

		# test that the input is highlighted green
		assert app.query_one('#api-key').styles.border_bottom == (
			'tall',
			Color(78, 191, 113),
		)

		# any username will work
		await pilot.click('#user-id')
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
			# type A 32 times to simulate a valid api key
			await pilot.click('#api-key')
			await pilot.press(*['A'] * 32)

			# any username will work
			await pilot.click('#user-id')
			await pilot.press('q')

			# submit the query
			await pilot.click('#submit-button')

			# check that the user average rating was created correctly
			assert app.query_one('#user-rating').renderable == Text.assemble(
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

			# check that one one row was added to the table
			with pytest.raises(CellDoesNotExist):
				table.get_cell_at(Coordinate(1, 0))
