from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Center, Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.validation import Regex
from textual.widgets import (
	Button,
	DataTable,
	Footer,
	Header,
	Input,
	Label,
	Markdown,
	Static,
	Switch,
)

from vapor import argument_handler
from vapor.api_interface import (
	get_anti_cheat_data,
	get_steam_user_data,
)
from vapor.config_handler import Config
from vapor.data_structures import (
	PRIVATE_ACCOUNT_HELP_MESSAGE,
	RATING_DICT,
	AntiCheatData,
	AntiCheatStatus,
)
from vapor.exceptions import InvalidIDError, PrivateAccountError, UnauthorizedError


class SettingsScreen(Screen):
	BINDINGS = [('escape', 'app.pop_screen', 'Close Settings')]

	def __init__(self, config):
		self.config: Config = config
		super().__init__()

	def compose(self) -> ComposeResult:
		with Container(id='content-container'):
			yield Markdown('# Settings', classes='heading')

			with VerticalScroll():  # noqa: SIM117
				with Horizontal():
					yield Static('Preserve Profile URL Input Value:', classes='label')
					yield Switch(
						value=self.config.get_value('preserve-user-id') == 'true',
						id='preserve-user-id',
					)

		yield Footer()

	def on_mount(self) -> None:
		if not self.config.get_value('preserve-user-id'):
			self.config.set_value('preserve-user-id', 'false')
			self.config.write_config()

	@on(Switch.Changed)
	def on_setting_changed(self, event: Switch.Changed):
		self.config.set_value(event.switch.id, str(event.value).lower())  # type: ignore
		self.config.write_config()


class PrivateAccountScreen(ModalScreen):
	def compose(self) -> ComposeResult:
		yield Center(
			Label(PRIVATE_ACCOUNT_HELP_MESSAGE, id='acct-info'),
			Button('Close', variant='error', id='close-acct-screen'),
			id='dialog',
		)

	def on_button_pressed(self) -> None:
		self.dismiss()


class SteamApp(App):
	CSS_PATH = 'main.tcss'
	TITLE = 'Steam Profile Proton Compatibility Checker'
	BINDINGS = [('ctrl+s', "push_screen('settings')", 'Settings')]

	def __init__(self, custom_config: Optional[Config] = None):
		if custom_config is None:
			custom_config = Config()

		self.config = custom_config.read_config()
		super().__init__()

	def compose(self) -> ComposeResult:
		self.show_account_help_dialog = False
		yield Header()
		yield Container(
			Center(
				Input(
					value=self.config.get_value('steam-api-key'),
					placeholder='Steam API Key',
					id='api-key',
					validators=Regex(r'[A-Z0-9]{32}'),
				),
				Input(
					placeholder='Profile URL or Steam ID',
					value=self.config.get_value('user-id')
					if self.config.get_value('preserve-user-id') == 'true'
					else '',
					id='user-id',
					validators=Regex(r'.+'),
				),
				id='input-container',
			),
			Center(Button('Check Profile', variant='primary', id='submit-button')),
			Center(
				Label(
					Text.assemble('User Average Rating: ', ('N/A', 'magenta')),
					id='user-rating',
				)
			),
			DataTable(zebra_stripes=True),
			id='body',
		)
		yield Footer()

	def on_mount(self) -> None:
		# add nothing to table so that it shows up
		table = self.query_one(DataTable)
		table.add_columns('Title', 'Compatibility', 'Anti-Cheat Compatibility')

		for _ in range(12):
			table.add_row('', '')

		self.install_screen(SettingsScreen(self.config), name='settings')

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

			self.config.set_value('steam-api-key', api_key.value)

			# parse id input to add URL compatibility
			parsed_url = urlparse(id.value)
			if parsed_url.netloc == 'steamcommunity.com' and (
				'/profiles/' in parsed_url.path or '/id/' in parsed_url.path
			):
				id.value = Path(parsed_url.path).name
				id.refresh()

			if self.config.get_value('preserve-user-id') == 'true':
				self.config.set_value('user-id', id.value)

			# fetch anti-cheat data
			cache = await get_anti_cheat_data()

			# Fetch user data
			user_data = await get_steam_user_data(api_key.value, id.value)
			table.clear()

			# Add games and ratings to the DataTable
			for game in user_data.game_ratings:
				if cache:
					game_ac = cache.get_anticheat_data(game.app_id)
					if not game_ac:
						game_ac = AntiCheatData('', AntiCheatStatus.BLANK)
				else:
					game_ac = AntiCheatData('', AntiCheatStatus.BLANK)

				table.add_row(
					game.name,
					Text(
						game.rating.capitalize(),
						style=RATING_DICT[game.rating][1],
						justify='center',
					),
					Text(game_ac.status.value, style=game_ac.color, justify='center'),
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
		except PrivateAccountError:
			self.show_account_help_dialog = True
		finally:
			self.config.write_config()

			# re-enable Input widgets
			for item in self.query(Input):
				item.disabled = False

			# re-enable Button widgets
			for item in self.query(Button):
				item.disabled = False

			# set table as not loading
			table = self.query_one(DataTable)
			table.set_loading(loading=False)

			if self.show_account_help_dialog:
				self.show_account_help_dialog = False
				self.push_screen(PrivateAccountScreen())


if __name__ == '__main__':
	argument_handler.parse_args()
	app = SteamApp()
	app.run()
