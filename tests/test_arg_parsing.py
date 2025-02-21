"""Tests related to argument parsing."""

import argparse
from unittest.mock import MagicMock, patch

from vapor.argument_handler import parse_args


def test_parse_args_without_clear_cache() -> None:
	"""Test parsing arguments without --clear-cache flag."""
	with (
		patch(
			'argparse.ArgumentParser.parse_args',
			return_value=argparse.Namespace(clear_cache=False),
		),
		patch('pathlib.Path.unlink', MagicMock()) as mock_unlink,
	):
		parse_args()
		mock_unlink.assert_not_called()


@patch('pathlib.Path.unlink', **{'other.side_effect': FileNotFoundError})
def test_parse_args_missing_cache(mock_unlink) -> None:
	"""Test parsing arguments when cache file is missing."""
	with patch(
		'argparse.ArgumentParser.parse_args',
		return_value=argparse.Namespace(clear_cache=True),
	):
		parse_args()

		mock_unlink.assert_called_once_with(missing_ok=True)
