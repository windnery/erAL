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

def load_command_cooldown():
	"""加载日常指令冷却时间"""
	path = DATA_DIR / 'time/command_cooldown.json'
	if not path.exists():
		return {}
	with open(path, 'r', encoding='utf-8') as f:
		command_cooldown = json.load(f)
	return command_cooldown

def load_attr_defs():
	"""加载属性定义表"""
	with open(DATA_DIR / 'attr_defs.json', 'r', encoding='utf-8') as f:
		attr_defs = json.load(f)
	return attr_defs


# 属性 section 的合并策略：
# - talent: 角色 JSON 全权负责（不参与 default 合并）
# - favor/trust: 平铺结构 {name, default}，JSON 没写时用 default
# - base/abl/exp/juel/palam/cflag/mark: 嵌套结构 {key: {name, default}}，default 打底 + JSON 覆盖
# - base 额外过滤：只保留 attr_defs 定义的键
_FLAT_SECTIONS = ('favor', 'trust')
_NESTED_SECTIONS = ('base', 'abl', 'exp', 'juel', 'palam', 'cflag', 'mark')
_FILTER_SECTIONS = ('base',)  # 过滤掉 attr_defs 未定义的键


def _merge_section(spec_defs, chara_data, section: str):
	"""按 attr_defs 的 default 初始化，再用角色 JSON 的 section 覆盖"""
	if section == 'talent':
		# talent 无 default，完全由角色 JSON 定义
		return dict(chara_data.get(section, {}))
	if section in _FLAT_SECTIONS:
		# 平铺结构: {name, default}
		return chara_data.get(section, spec_defs['default'])
	# 嵌套结构: {key: {name, default}}
	result = {k: v['default'] for k, v in spec_defs.items()}
	json_data = chara_data.get(section, {})
	if section in _FILTER_SECTIONS:
		# 只保留 attr_defs 定义的键
		json_data = {k: v for k, v in json_data.items() if k in spec_defs}
	result.update(json_data)
	return result


def merge_character_attrs(attr_defs, chara_data: dict[str, Any]) -> dict[str, Any]:
	"""将角色 JSON 数据与 attr_defs 的 default 合并，返回补全后的角色数据

	- 数值 section（base/abl/exp/juel/palam/cflag/mark）: default 打底 + JSON 覆盖
	- favor/trust: JSON 覆盖，缺省用 default
	- talent: 纯 JSON，不合并
	- 顶层键（id/name/location/schedule 等）: 原样保留
	"""
	merged = dict(chara_data)
	for section in _NESTED_SECTIONS + _FLAT_SECTIONS + ('talent',):
		spec = attr_defs.get(section)
		if spec is not None:
			merged[section] = _merge_section(spec, chara_data, section)
	return merged


def load_player():
	"""加载玩家数据"""
	with open(DATA_DIR / 'characters/_player.json', 'r', encoding='utf-8') as f:
		player_data = json.load(f)
	return merge_character_attrs(load_attr_defs(), player_data)


def load_shipgirls():
	"""加载舰娘数据"""
	shipgirls: dict[str, dict[str, Any]] = {}
	folder = DATA_DIR / 'characters'
	attr_defs = load_attr_defs()

	for json_file in folder.glob('*.json'):
		# 跳过_player.json
		if json_file.name.startswith('_'):
			continue

		with open(json_file, 'r', encoding='utf-8') as f:
			shipgirl_data = json.load(f)
			shipgirl_id = shipgirl_data['id']
			shipgirls[shipgirl_id] = merge_character_attrs(attr_defs, shipgirl_data)

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


