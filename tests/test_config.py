from io import BytesIO

import pytest

from vapor.config_handler import Config
from vapor.exceptions import ConfigFileNotReadError, ConfigReadError, ConfigWriteError


class InMemoryPath(BytesIO):
	def __init__(self):
		super().__init__()
		self.write(b'')

		self.exists_bool = True

	def open(self, _):
		self.seek(0)
		return self

	def exists(self):
		return self.exists_bool

	def write(self, string):
		if isinstance(string, str):
			string = string.encode()
		super().write(string)

	def __exit__(self, *_):
		pass


@pytest.fixture
def config():
	cfg = Config()
	cfg._config_path = InMemoryPath()
	return cfg


def test_set_value(config):
	config.read_config()
	config.set_value('test_key', 'test_value')
	assert config.get_value('test_key') == 'test_value'


def test_set_value_no_read(config):
	with pytest.raises(ConfigFileNotReadError):
		config.set_value('test', 'test2')


def test_get_value_no_read(config):
	assert config.get_value('non_existent_key') == ''


def test_get_value_empty(config):
	config.read_config()
	assert config.get_value('non_existent_key') == ''


def test_write_config(config):
	config.read_config()
	config.set_value('test_key', 'test_value')
	config.write_config()
	assert config._config_path.getvalue() != b''


def test_write_config_no_read(config):
	with pytest.raises(ConfigFileNotReadError):
		config.write_config()


def test_read_config_os_error(config):
	config._config_path = ''
	with pytest.raises(ConfigReadError):
		config.read_config()


def test_read_config_non_existent_file(config):
	config._config_path.exists_bool = False
	with pytest.raises(ConfigReadError):
		config.read_config()


def test_write_config_non_existent_file(config):
	config.read_config()
	config._config_path = ''
	with pytest.raises(ConfigWriteError):
		config.write_config()
