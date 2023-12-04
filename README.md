# Vapor: Steam Proton Compatibility Checker

Vapor is a Python package which offers a Terminal User Interface (TUI) program for checking ProtonDB compatibility ratings of games in a Steam user's library. The tool seamlessly integrates Steam and ProtonDB APIs to provide insightful compatibility information.

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
paru -S python-vapor
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

## Requirements
This package is built on top of textual and aiohttp, and uses poetry to manage dependencies. To install dependencies locally, just run `poetry install` in the repository's directory.

## Contributing
Contributions are welcomed! For bug fixes, improvements, or feature requests, feel free to open an issue or pull request.