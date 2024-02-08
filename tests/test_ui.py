import pytest
from textual.color import Color
from textual.coordinate import Coordinate
from textual.widgets import DataTable

from tests.test_config import InMemoryPath
from vapor.config_handler import Config
from vapor.main import SteamApp


@pytest.fixture
def config():
	cfg = Config()
	cfg._config_path = InMemoryPath()
	return cfg


@pytest.mark.asyncio
async def test_first_startup(config):
	app = SteamApp()
	app.config = config
	async with app.run_test() as _:
		assert app.query_one('#api-key').value == ''
		assert app.query_one('#user-id').value == ''
		assert app.query_one(DataTable).get_cell_at(Coordinate(0, 0)) == ''


@pytest.mark.asyncio
async def test_invalid_input_data(config):
	app = SteamApp()
	config.read_config()
	app.config = config

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
	app = SteamApp()
	config.read_config()
	app.config = config

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


@pytest.mark.asyncio
async def test_(config):
	app = SteamApp()
	config.read_config()
	app.config = config
