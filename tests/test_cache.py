import json
import io
from pathlib import Path
import pytest
from datetime import datetime, timedelta

from vapor.cache_handler import Cache
from vapor.data_structures import AntiCheatData, AntiCheatStatus, Game

class BytesIOPath:
	def __init__(self, bytes_io):
		self.bytes_io = bytes_io

	def read_text(self):
		self.bytes_io.seek(0)
		return self.bytes_io.read().decode()

	def write_text(self, text):
		self.bytes_io.seek(0)
		self.bytes_io.truncate()
		self.bytes_io.write(text.encode())

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.bytes_io.close()

@pytest.fixture
def cache():
	return Cache()

@pytest.fixture
def cache_data():
	return {
		'game_cache': {
			'123456': {
				'name': 'Game 1',
				'rating': 'gold',
				'playtime': 100,
				'timestamp': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
			},
			'483': {
				'name': 'Game 2',
				'rating': 'platinum',
				'playtime': 100,
				'timestamp': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
			}
		},
		'anticheat_cache': {
			'data': {
				'789012': 'Denied'
			},
			'timestamp': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
		}
	}

@pytest.mark.asyncio
async def test_load_cache(cache, cache_data):
	with io.BytesIO(json.dumps(cache_data).encode()) as f:
		cache.cache_path = BytesIOPath(f)
		cache.load_cache(prune=False)
		
		assert cache.has_game_cache
		assert cache.has_anticheat_cache
		assert cache.get_game_data('123456') is not None
		assert cache.get_anticheat_data('789012') is not None

@pytest.mark.asyncio
async def test_update_cache(cache, cache_data):
	with io.BytesIO() as f:
		cache.cache_path = BytesIOPath(f)
		cache.update_cache(
			game_list=[
				Game(name='Game 2', rating='silver', playtime=200, app_id='654321')
			],
			anti_cheat_list=[
				AntiCheatData(app_id='987654', status=AntiCheatStatus.DENIED)
			]
		)

		f.seek(0)
		updated_data = json.loads(f.read())
		assert '654321' in updated_data['game_cache']
		assert '987654' in updated_data['anticheat_cache']['data']

@pytest.mark.asyncio
async def test_prune_cache(cache, cache_data):
	with io.BytesIO(json.dumps(cache_data).encode()) as f:
		cache.cache_path = BytesIOPath(f)
		cache.load_cache(prune=True)

		f.seek(0)
		pruned_data = json.loads(f.read())

		assert '123456' not in pruned_data['game_cache']
		assert '483' in pruned_data['game_cache']

		assert 'anticheat_cache' not in pruned_data
