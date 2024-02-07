from configparser import ConfigParser
from typing import Optional

from vapor.data_structures import CONFIG_DIR
from vapor.exceptions import ConfigFileNotReadError, ConfigReadError, ConfigWriteError

CONFIG_PATH = CONFIG_DIR / 'config.ini'
"""The path to the config file."""


class Config:
	def __init__(self):
		self._config_path = CONFIG_PATH
		self._config_data: Optional[ConfigParser] = None

	def set_value(self, key: str, value: str):
		"""Sets a value in the config file.

		This does not write to the actual config file, just updates it in memory.

		Args:
			key (str): The key to write.
			value (str): The value to write.

		Raises:
			ConfigFileNotReadError: If a config value is set without the config being read.
		"""
		if self._config_data is None:
			raise ConfigFileNotReadError

		if not self._config_data.has_section('vapor'):
			self._config_data.add_section('vapor')

		self._config_data.set('vapor', key, value)


	def write_config(self):	
		"""Writes the config to a file.
		
		Raises:
			ConfigFileNotReadError: If the config file was never read.
			ConfigWriteError: If an error was encountered while writing the file.
		"""
		if self._config_data is not None:
			try:
				with self._config_path.open('w') as f:
					self._config_data.write(f)
			except Exception as e:
				raise ConfigWriteError from e
		else:
			raise ConfigFileNotReadError


	def read_value(self, key: str) -> str:
		"""Read a value from the config file if it exists.

		Args:
			key (str): The key to read.

		Returns:
			str: The config value if exists. If not, an empty string.

		Raises:
			ConfigFileNotReadError: If the config file was never read.
		"""
		if self._config_data is None:
			return ''

		if 'vapor' in self._config_data.sections() and key in self._config_data.options('vapor'):
			return self._config_data.get('vapor', key)

		return ''

	def read_config(self):
		"""Read the config from the file location.

		Raises:
			ConfigReadError: If an error was encoutnered while reading the file.
		"""
		try:
			self._config_data = ConfigParser()
			if self._config_path.exists():
				self._config_data.read(self._config_path)
		except Exception as e:
			raise ConfigReadError from e
