"""TUI program to check the ProtonDB compatibility of all the games of a Steam user.

Vapor is a Python package built on Textual which offers a simple Terminal User
Interface for checking ProtonDB compatibility ratings of games in a Steam
user's library. The tool seamlessly integrates Steam and ProtonDB APIs
to provide insightful compatibility information.
"""

from vapor import main as entrypoint
from vapor.argument_handler import parse_args


def main():
	"""Entrypoint for the program."""
	parse_args()

	app = entrypoint.SteamApp()
	app.run()


if __name__ == '__main__':
	main()
