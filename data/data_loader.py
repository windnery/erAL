import json
from pathlib import Path
from typing import Any


def load_maps():
	'''加载地图'''
	all_maps: dict[str, dict[str, dict[str, Any]]] = {}
	folder = Path('data/maps')

	for json_file in folder.glob('*.json'):
		# 跳过_regions.json
		if json_file.name.startswith('_'):
			continue
		region_id = json_file.stem

		with open(json_file, 'r', encoding='utf-8') as f:
			region_data = json.load(f)
			all_maps[region_id] = region_data

	return all_maps