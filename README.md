# Vapor: Steam Proton Compatibility Checker

<p align="center">
	<a href="https://badge.fury.io/py/vapor-steam"><img alt="PyPI" src="https://img.shields.io/pypi/v/vapor-steam" /></a>
	<a href="https://aur.archlinux.org/packages/python-vapor-steam/"><img alt="AUR version" src="https://img.shields.io/aur/version/python-vapor-steam"></a>
	<a href="https://pepy.tech/project/vapor-steam"><img alt="Downloads" src="https://pepy.tech/badge/vapor-steam" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/vapor-steam.svg" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/graphs/commit-activity"><img alt="Maintenance" src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/issues/"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/TabulateJarl8/vapor.svg" /></a>
	<img alt="Coverage" src="https://img.shields.io/codecov/c/github/TabulateJarl8/vapor" />
	<a href="https://github.com/TabulateJarl8"><img alt="GitHub followers" src="https://img.shields.io/github/followers/TabulateJarl8?style=social" /></a>
	<br>
	<a href="https://ko-fi.com/L4L3L7IO2"><img alt="Kofi Badge" src="https://ko-fi.com/img/githubbutton_sm.svg" /></a>
</p>

Vapor is a Python package built on [Textual](https://github.com/textualize/textual/) which offers a simple Terminal User Interface for checking ProtonDB compatibility ratings of games in a Steam user's library. The tool seamlessly integrates Steam and ProtonDB APIs to provide insightful compatibility information.

![Vapor Showing Information](https://raw.githubusercontent.com/TabulateJarl8/vapor/master/img/info.png)

## Installation

Vapor is available as [vapor-steam](https://pypi.org/project/vapor-steam/) on PyPI.

[uv](https://docs.astral.sh/uv/):

```shell
# install permanently
uv tool install vapor-steam

# or, just try it out
uvx --from vapor-steam vapor
```

With pip or pipx:

```shell
# with pipx
pipx install vapor-steam

# with standard pip
pip3 install vapor-steam
```

Arch users can install the package from the AUR with your favorite AUR helper:

```shell
paru -S python-vapor-steam

```

Or manually with `makepkg`:

```shell
git clone https://aur.archlinux.org/python-vapor-steam.git && cd python-vapor-steam
makepkg -si
```

## Quick Start

1. **Obtain a Steam API Key**: Get your Steam API key by [filling out this form](https://steamcommunity.com/dev/apikey).
2. **Run the Program**: Run vapor with the `vapor` command. It can also be ran without installation, with `uv run python src/vapor/main.py`.

## Features

- **User Library Analysis**: Fetches and displays game compatibility ratings from ProtonDB for a specified Steam user.
- **User Average Compatibility**: Calculates and presents the average game compatibility for the user's library.
- **Automatic Steam ID Resolution**: Vapor automatically resolves the given Steam ID, so you can use either your vanity name or your 64-bit Steam ID.
- **Automatic Steam URL Detection**: Directly paste a Steam user profile URL, like `https://steamcommunity.com/id/<user>` or `https://steamcommunity.com/profiles/<user>` into the "User ID" box and it will be detected and parsed correctly.
- **AreWeAntiCheatYet Integration**: Integartion with Are We Anti-Cheat Yet? to show the anti-cheat compatibility status of your games.

## Requirements

This package is built on top of [Textual](https://github.com/Textualize/textual), and uses uv to manage dependencies. To install dependencies locally, just run `uv sync` in the repository's directory.

## Private Steam Account Error

This error occurs if your game details are set to private in your privacy settings. First, double check that you're using the correct Steam ID or vanity URL. This is different from your display name. To make sure, you can directly copy your profile URL into Vapor and your Steam ID will be extracted. Your profile URL will look like `https://steamcommunity.com/id/<vanity_name>` or `https://steamcommunity.com/profiles/<steam_id>`.

If you've double checked that your account information is correct, please complete the following steps to fix this issue:

1. From Steam, click the user dropdown and select "View my profile"
1. Click the "Edit Profile" button
1. Click the "Privacy Settings" tab
1. Set "Game details" to Public
1. Uncheck the Always keep my total playtime private option

## Contributing

Contributions are welcomed! For bug fixes, improvements, or feature requests, feel free to open an issue or pull request.

Developer dependencies can be installed with `uv sync --dev`
