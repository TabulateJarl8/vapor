# Vapor: Steam Proton Compatibility Checker

<p align="center">
	<a href="https://badge.fury.io/py/vapor-steam"><img alt="PyPI" src="https://img.shields.io/pypi/v/vapor-steam" /></a>
	<a href="https://aur.archlinux.org/packages/python-vapor-steam/"><img alt="AUR version" src="https://img.shields.io/aur/version/python-vapor-steam"></a>
	<a href="https://pepy.tech/project/vapor-steam"><img alt="Downloads" src="https://pepy.tech/badge/vapor-steam" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/vapor-steam.svg" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/graphs/commit-activity"><img alt="Maintenance" src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" /></a>
	<a href="https://github.com/TabulateJarl8/vapor/issues/"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/TabulateJarl8/vapor.svg" /></a>
	<a href="https://github.com/TabulateJarl8"><img alt="GitHub followers" src="https://img.shields.io/github/followers/TabulateJarl8?style=social" /></a>
	<br>
	<a href="https://ko-fi.com/L4L3L7IO2"><img alt="Kofi Badge" src="https://ko-fi.com/img/githubbutton_sm.svg" /></a>
</p>

Vapor is a Python package built on [Textual](https://github.com/textualize/textual/) which offers a simple Terminal User Interface for checking ProtonDB compatibility ratings of games in a Steam user's library. The tool seamlessly integrates Steam and ProtonDB APIs to provide insightful compatibility information.

![Vapor Showing Information](https://raw.githubusercontent.com/TabulateJarl8/vapor/master/img/info.png)

## Installation
[pipx](https://pipx.pypa.io/stable/) is a great tool for installing Python packages in an isolated environment. If wanting to install via `pipx`, just run
```shell
pipx install vapor-steam
```
This project can also be installed with pip normally with
```shell
pip3 install vapor-steam
```

Arch user's can install the package from the AUR with your favorite AUR helper:
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
2. **Run the Program**: Run vapor with the `vapor` command. It can also be ran without installation, with `python3 vapor/main.py`.

## Features
 - **User Library Analysis**: Fetches and displays game compatibility ratings from ProtonDB for a specified Steam user.
 - **User Average Compatibility**: Calculates and presents the average game compatibility for the user's library.
 - **Automatic Steam ID Resolution**: Vapor automatically resolves the given Steam ID, so you can use either your vanity name or your 64-bit Steam ID.

## Requirements
This package is built on top of textual and aiohttp, and uses poetry to manage dependencies. To install dependencies locally, just run `poetry install` in the repository's directory.

## Contributing
Contributions are welcomed! For bug fixes, improvements, or feature requests, feel free to open an issue or pull request.
