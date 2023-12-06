from vapor import main as entrypoint
from vapor.argument_handler import parse_args


def main():
	parse_args()

	app = entrypoint.SteamApp()
	app.run()


if __name__ == '__main__':
	main()
