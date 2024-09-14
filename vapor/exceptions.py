"""Vapor's custom exceptions."""


class InvalidIDError(Exception):
	"""If an invalid Steam ID is used, this error will be raised."""


class UnauthorizedError(Exception):
	"""If an invalid Steam API key is used, this error will be raised."""


class PrivateAccountError(Exception):
	"""If an account is set to private."""


class ConfigFileNotReadError(Exception):
	"""If a config value is set without the config being read."""


class ConfigWriteError(Exception):
	"""If there was an error while writing the config."""


class ConfigReadError(Exception):
	"""If there was an error while reading the config."""
