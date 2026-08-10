import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent


def load_maps():
	"""加载地图"""
	all_maps: dict[str, dict[str, dict[str, Any]]] = {}
	folder = DATA_DIR / 'maps'

	for json_file in folder.glob('*.json'):
		# 跳过_regions.json
		if json_file.name.startswith('_'):
			continue
		region_id = json_file.stem

		with open(json_file, 'r', encoding='utf-8') as f:
			region_data = json.load(f)
			all_maps[region_id] = region_data

	return all_maps

def load_regions():
	"""加载区域注册表"""
	with open(DATA_DIR / 'maps/_regions.json', 'r', encoding='utf-8') as f:
		regions = json.load(f)
	return regions

def load_leave_time():
	"""加载离开时间"""
	with open(DATA_DIR / 'time/leave_time.json', 'r', encoding='utf-8') as f:
		leave_time = json.load(f)
	return leave_time

def load_move_time():
	"""加载移动时间"""
	with open(DATA_DIR / 'time/move_time.json', 'r', encoding='utf-8') as f:
		move_time = json.load(f)
	return move_time

def load_command_time():
	"""加载日常指令时间"""
	with open(DATA_DIR / 'time/command_time.json', 'r', encoding='utf-8') as f:
		command_time = json.load(f)
	return command_time

def load_attr_defs():
	"""加载属性定义表"""
	with open(DATA_DIR / 'attr_defs.json', 'r', encoding='utf-8') as f:
		attr_defs = json.load(f)
	return attr_defs

def load_player():
	"""加载玩家数据"""
	with open(DATA_DIR / 'characters/_player.json', 'r', encoding='utf-8') as f:
		player_data = json.load(f)
	return player_data

def load_shipgirls():
	"""加载舰娘数据"""
	shipgirls: dict[str, dict[str, Any]] = {}
	folder = DATA_DIR / 'characters'

	for json_file in folder.glob('*.json'):
		# 跳过_player.json
		if json_file.name.startswith('_'):
			continue

		with open(json_file, 'r', encoding='utf-8') as f:
			shipgirl_data = json.load(f)
			shipgirl_id = shipgirl_data['id']
			shipgirls[shipgirl_id] = shipgirl_data

	return shipgirls

def load_skins():
	"""加载皮肤数据"""
	skins: dict[str, dict[str, dict[str, Any]]] = {}
	folder = DATA_DIR / 'skins'

	for json_file in folder.glob('*.json'):
		skin_id = json_file.stem
		with open(json_file, 'r', encoding='utf-8') as f:
			skin_data = json.load(f)
			skins[skin_id] = skin_data

	return skins

def load_items():
	"""加载道具数据"""
	with open(DATA_DIR / 'items.json', 'r', encoding='utf-8') as f:
		items = json.load(f)
	return items


