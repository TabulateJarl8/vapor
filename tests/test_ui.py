import pytest
from tests.test_config import InMemoryPath
from vapor.config_handler import Config
from vapor.main import SteamApp
from textual.widgets import DataTable, Button
from textual.coordinate import Coordinate

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
		assert app.query_one("#api-key").value == ''
		assert app.query_one("#user-id").value == ''
		assert app.query_one(DataTable).get_cell_at(Coordinate(0, 0)) == ''

@pytest.mark.asyncio
async def test_no_api_key(config):
	app = SteamApp()
	app.config = config
	async with app.run_test() as pilot:
		await pilot.click(Button)
		assert app.query_one('#api-key').styles.border == ''