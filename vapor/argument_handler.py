import argparse

from vapor import cache_handler


def parse_args():
	"""Parse arguments from stdin."""
	parser = argparse.ArgumentParser(
		prog='vapor',
		description='TUI program to check the ProtonDB compatibility of all the games of a Steam user',
	)
	parser.add_argument(
		'--clear-cache', action='store_true', help="Clear all of vapor's cache"
	)

	args = parser.parse_args()

	if args.clear_cache:
		cache_handler.CACHE_PATH.unlink()
