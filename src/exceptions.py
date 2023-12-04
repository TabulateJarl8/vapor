class InvalidIDError(Exception):
	"""If an invalid Steam ID is used, this error will be raised."""


class UnauthorizedError(Exception):
	"""If an invalid Steam API key is used, this error will be raised."""
