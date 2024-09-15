"""Tests related to vapor's config handler."""

from io import BytesIO

import pytest
from typing_extensions import Self

from vapor.config_handler import Config
from vapor.exceptions import ConfigFileNotReadError, ConfigReadError, ConfigWriteError


class InMemoryPath(BytesIO):
	"""An in memory "file" with a virtual path."""

	def __init__(self) -> None:
		"""Construct a virtual in-memory file."""
		super().__init__()
		self.write(b'')

		self.exists_bool = True

	def open(self, _) -> Self:
		"""Seek to 0 to mimic file opening."""
		self.seek(0)
		return self

	def exists(self) -> bool:
		"""Return whether or not the file has been set to exist by the user."""
		return self.exists_bool

	def write(self, string) -> int:
		"""Write a string to the virtual file."""
		if isinstance(string, str):
			string = string.encode()
		super().write(string)

		return 0

	def __exit__(self, *_) -> None:
		"""Define dummy method for use in with blocks."""


@pytest.fixture
def config() -> Config:
	"""Pytest fixture of Config that uses InMemoryPath."""
	cfg = Config()
	cfg._config_path = InMemoryPath()  # type: ignore
	return cfg


def test_set_value(config: Config) -> None:
	"""Test setting a value in the config."""
	config.read_config()
	config.set_value('test_key', 'test_value')
	assert config.get_value('test_key') == 'test_value'


def test_set_value_no_read(config: Config) -> None:
	"""Test that setting a value without reading throws an error."""
	with pytest.raises(ConfigFileNotReadError):
		config.set_value('test', 'test2')


def test_get_value_no_read(config: Config) -> None:
	"""Test getting a value without returns an empty string."""
	assert not config.get_value('non_existent_key')


def test_get_value_empty(config: Config) -> None:
	"""Test that getting a nonexistant value behaves correctly."""
	config.read_config()
	assert not config.get_value('non_existent_key')


def test_write_config(config) -> None:
	"""Test that writing the config works correctly."""
	config.read_config()
	config.set_value('test_key', 'test_value')
	config.write_config()
	assert config._config_path.getvalue() != b''


def test_write_config_no_read(config: Config) -> None:
	"""Test writing config without reading throws an error."""
	with pytest.raises(ConfigFileNotReadError):
		config.write_config()


def test_read_config_os_error(config) -> None:
	"""Test reading with an invalid path throws an error."""
	config._config_path = ''
	with pytest.raises(ConfigReadError):
		config.read_config()


def test_read_config_non_existent_file(config) -> None:
	"""Test reading when file doesn't exist behaves correctly."""
	config._config_path.exists_bool = False
	assert config.read_config()._config_data._sections == {}


def test_write_config_non_existent_file(config) -> None:
	"""Test that writing to a nonexistant path throws an error."""
	config.read_config()
	config._config_path = ''
	with pytest.raises(ConfigWriteError):
		config.write_config()
