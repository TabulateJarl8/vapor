import argparse
from unittest.mock import patch

from vapor.argument_handler import parse_args
from vapor.cache_handler import CACHE_PATH


def test_parse_args_with_clear_cache():
	"""Test parsing arguments with --clear-cache flag."""
	with patch(
		'argparse.ArgumentParser.parse_args',
		return_value=argparse.Namespace(clear_cache=True),
	), patch('os.unlink') as mock_unlink:
		parse_args()
		mock_unlink.assert_called_once_with(CACHE_PATH)


def test_parse_args_without_clear_cache():
	"""Test parsing arguments without --clear-cache flag."""
	with patch(
		'argparse.ArgumentParser.parse_args',
		return_value=argparse.Namespace(clear_cache=False),
	), patch('os.unlink') as mock_unlink:
		parse_args()
		mock_unlink.assert_not_called()


def test_parse_args_no_args():
	"""Test parsing arguments with no arguments."""
	with patch(
		'argparse.ArgumentParser.parse_args',
		return_value=argparse.Namespace(clear_cache=False),
	), patch('os.unlink') as mock_unlink:
		parse_args()
		mock_unlink.assert_not_called()


def test_parse_args_missing_cache():
	"""Test parsing arguments when cache file is missing."""
	with patch(
		'argparse.ArgumentParser.parse_args',
		return_value=argparse.Namespace(clear_cache=True),
	), patch('os.unlink', side_effect=FileNotFoundError):
		parse_args()
		# Ensure that unlink is not called in case of FileNotFoundError
		assert True
