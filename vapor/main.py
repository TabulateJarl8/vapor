"""Main code and UI."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, cast
from urllib.parse import urlparse

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Center, Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.types import CSSPathType
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
from typing_extensions import override

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


class SettingsScreen(Screen[None]):
	"""Settings editor screen for modifying the config file."""

	BINDINGS: ClassVar[list[BindingType]] = [
		Binding('escape', 'app.pop_screen', 'Close Settings', show=True),
	]

	def __init__(self, config: Config) -> None:
		"""Construct the Settings screen."""
		self.config: Config = config
		super().__init__()

	@override
	def compose(self) -> ComposeResult:
		"""Compose the Settings screen with textual components."""
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
		"""On mount, check that all the needed config values have been set in config.

		This is useful for migration of older versions to newer versions when new
		configuration options have been added.
		"""
		if not self.config.get_value('preserve-user-id'):
			self.config.set_value('preserve-user-id', 'false')
			self.config.write_config()

	@on(Switch.Changed)
	def on_setting_changed(self, event: Switch.Changed) -> None:
		"""Whenever a setting has changed, update it in the config file."""
		if event.switch.id:
			self.config.set_value(event.switch.id, str(event.value).lower())  # type: ignore
			self.config.write_config()


class PrivateAccountScreen(ModalScreen[None]):
	"""Error screen for private account errors."""

	@override
	def compose(self) -> ComposeResult:
		"""Compose the error screen with textual components."""
		yield Center(
			Label(PRIVATE_ACCOUNT_HELP_MESSAGE, id='acct-info'),
			Button('Close', variant='error', id='close-acct-screen'),
			id='dialog',
		)

	def on_button_pressed(self) -> None:
		"""When the dismiss button is pressed, close the screen."""
		self.dismiss()


class SteamApp(App[None]):
	"""Main application class."""

	CSS_PATH: ClassVar[CSSPathType | None] = 'main.tcss'
	TITLE: str | None = 'Steam Profile Proton Compatibility Checker'
	BINDINGS: ClassVar[list[BindingType]] = [
		Binding('ctrl+s', "push_screen('settings')", 'Settings', show=True),
	]

	def __init__(self, custom_config: Config | None = None) -> None:
		"""Construct the application.

		This reads and instantiates the config.
		"""
		if custom_config is None:
			custom_config = Config()

		self.config: Config = custom_config.read_config()
		self.show_account_help_dialog: bool = False
		super().__init__()

	@override
	def compose(self) -> ComposeResult:
		"""Compose the application from textual components."""
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
				),
			),
			DataTable[str | Text](zebra_stripes=True),
			id='body',
		)
		yield Footer()

	def on_mount(self) -> None:
		"""On mount, we initialize the table columns."""
		# add nothing to table so that it shows up
		table: DataTable[str | Text] = self.query_one(DataTable)
		table.add_columns('Title', 'Compatibility', 'Anti-Cheat Compatibility')

		for _ in range(12):
			table.add_row('', '')

		self.install_screen(SettingsScreen(self.config), name='settings')  # pyright: ignore[reportUnknownMemberType]

	@work(exclusive=True)
	@on(Button.Pressed, '#submit-button')
	@on(Input.Submitted)
	async def populate_table(self) -> None:
		"""Populate datatable with game information when submit button is pressed."""
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
			table: DataTable[str | Text] = self.query_one(DataTable)
			table.set_loading(loading=True)

			# get user's API key and ID
			api_key: Input = cast(Input, self.query_one('#api-key'))
			user_id: Input = cast(Input, self.query_one('#user-id'))

			self.config.set_value('steam-api-key', api_key.value)

			# parse id input to add URL compatibility
			parsed_url = urlparse(user_id.value)
			if parsed_url.netloc == 'steamcommunity.com' and (
				'/profiles/' in parsed_url.path or '/id/' in parsed_url.path
			):
				user_id.value = Path(parsed_url.path).name
				user_id.refresh()

			if self.config.get_value('preserve-user-id') == 'true':
				self.config.set_value('user-id', user_id.value)

			# fetch anti-cheat data
			cache = await get_anti_cheat_data()

			# Fetch user data
			user_data = await get_steam_user_data(api_key.value, user_id.value)
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
			rating_label: Label = cast(Label, self.query_one('#user-rating'))
			rating_label.update(
				Text.assemble(
					'User Average Rating: ',
					(
						user_data.user_average.capitalize(),
						RATING_DICT[user_data.user_average][1],
					),
				),
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
