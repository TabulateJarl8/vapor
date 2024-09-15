"""Tests realted to vapor's data structures."""

from vapor.data_structures import _ANTI_CHEAT_COLORS, AntiCheatData, AntiCheatStatus


def test_anti_cheat_data_color_resolution() -> None:
	"""Test that anticheat colors are correct."""
	assert (
		AntiCheatData('', AntiCheatStatus.BROKEN).color == _ANTI_CHEAT_COLORS['Broken']
	)

	assert (
		AntiCheatData('', AntiCheatStatus.PLANNED).color
		== _ANTI_CHEAT_COLORS['Planned']
	)

	assert (
		AntiCheatData('', AntiCheatStatus.RUNNING).color
		== _ANTI_CHEAT_COLORS['Running']
	)
