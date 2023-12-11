from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Center
from textual.validation import Regex
from textual.widgets import Button, DataTable, Header, Input, Label

from vapor import argument_handler
from vapor.api_interface import (
	get_anti_cheat_data,
	get_item_from_appid,
	get_steam_user_data,
)
from vapor.config_handler import read_steam_api_key, write_steam_api_key
from vapor.data_structures import RATING_DICT, AntiCheatData, AntiCheatStatus
from vapor.exceptions import InvalidIDError, UnauthorizedError


class SteamApp(App):
	CSS_PATH = 'main.tcss'
	TITLE = 'Steam Profile Proton Compatibility Checker'

	def compose(self) -> ComposeResult:
		yield Header()
		yield Center(
			Input(
				value=read_steam_api_key(),
				placeholder='Steam API Key',
				id='api-key',
				validators=Regex(r'[A-Z0-9]{32}'),
			),
			Input(placeholder='User ID', id='user-id', validators=Regex(r'.+')),
			id='input-container',
		)
		yield Center(Button('Check Profile', variant='primary'))
		yield Center(
			Label(
				Text.assemble('User Average Rating: ', ('N/A', 'magenta')),
				id='user-rating',
			)
		)
		yield DataTable(zebra_stripes=True)

	def on_mount(self) -> None:
		# add nothing to table so that it shows up
		table = self.query_one(DataTable)
		table.add_columns('Title', 'Compatibility', 'Anti-Cheat Compatibility')

		for _ in range(12):
			table.add_row('', '')

	@work(exclusive=True)
	@on(Button.Pressed)
	@on(Input.Submitted)
	async def populate_table(self) -> None:
		try:
			# disable all Input widgets
			for item in self.query(Input):
				item.disabled = True
				item.blur()
				item.refresh()

			# disable all Button widgets
			for item in self.query(Button):
				item.disabled = True
				item.blur()
				item.refresh()

			# set the DataTable as loading
			table = self.query_one(DataTable)
			table.set_loading(loading=True)

			# get user's API key and ID
			api_key: Input = self.query_one('#api-key')  # type: ignore
			id: Input = self.query_one('#user-id')  # type: ignore

			write_steam_api_key(api_key.value)

			# fetch anti-cheat data
			ac_data = await get_anti_cheat_data()

			# Fetch user data
			user_data = await get_steam_user_data(api_key.value, id.value)
			table.clear()

			# Add games and ratings to the DataTable
			for game in user_data.game_ratings:
				if ac_data:
					game_ac: AntiCheatData | None = get_item_from_appid(
						ac_data, game.app_id
					)
					if not game_ac:
						game_ac = AntiCheatData('', AntiCheatStatus.BLANK)
				else:
					game_ac = AntiCheatData('', AntiCheatStatus.BLANK)

				table.add_row(
					game.name,
					Text(
						game.rating.capitalize(),
						style=RATING_DICT[game.rating][1],
					),
					Text(
						game_ac.status.value,
						style=game_ac.color,
					),
				)

			# Add the user's average rating to the screen
			rating_label: Label = self.query_one('#user-rating')  # type: ignore
			rating_label.update(
				Text.assemble(
					'User Average Rating: ',
					(
						user_data.user_average.capitalize(),
						RATING_DICT[user_data.user_average][1],
					),
				)
			)
		except InvalidIDError:
			self.notify('Invalid Steam User ID', title='Error', severity='error')
		except UnauthorizedError:
			self.notify('Invalid Steam API Key', title='Error', severity='error')
		finally:
			# re-enable Input widgets
			for item in self.query(Input):
				item.disabled = False

			# re-enable Button widgets
			for item in self.query(Button):
				item.disabled = False

			# set table as not loading
			table = self.query_one(DataTable)
			table.set_loading(loading=False)


if __name__ == '__main__':
	argument_handler.parse_args()
	app = SteamApp()
	app.run()
