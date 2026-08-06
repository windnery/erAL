import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world import World

SAVE_VERSION = 1
SLOT_COUNT = 3


class SaveManager:
    """世界状态存档管理：存 delta（仅运行时字段），静态数据读档时从 data/ 重建"""

    def __init__(self, world: 'World', sav_dir: Path | None = None):
        self.world = world
        self.sav_dir = sav_dir or Path('sav')

    def serialize_world(self) -> dict:
        world = self.world
        player = world.player
        sg_state = {}
        for sg in world.npc_manager.get_all_npcs():
            sg_state[sg.id] = {
                'location': sg.location,
                'base': sg.base,
                'favor': sg.favor,
                'trust': sg.trust,
                'abl': sg.abl,
                'exp': sg.exp,
                'juel': sg.juel,
                'palam': sg.palam,
                'cflag': sg.cflag,
            }
        return {
            'version': SAVE_VERSION,
            'meta': {
                'day': world.time_manager.day,
                'hour': world.time_manager.hour,
                'minute': world.time_manager.minute,
                'player_name': player.name,
            },
            'data': {
                'time': {
                    'day': world.time_manager.day,
                    'hour': world.time_manager.hour,
                    'minute': world.time_manager.minute,
                },
                'player': {
                    'location': player.location,
                    'base': player.base,
                    'money': player.money,
                    'wake_time': player.wake_time,
                    'abl': player.abl,
                    'exp': player.exp,
                    'juel': player.juel,
                    'palam': player.palam,
                    'talent': player.talent,
                },
                'shipgirls': sg_state,
                'work': {
                    'works': world.work_manager.works,
                    'works_done': world.work_manager.works_done,
                },
                'menu_active': world.menu_active,
                'secretary_ship_id': (
                    world.npc_manager.secretary_ship.id
                    if world.npc_manager.secretary_ship else None
                ),
            },
        }

    def deserialize_world(self, data: dict) -> str | None:
        """把存档数据还原到 world。成功返回 None，失败返回错误信息"""
        try:
            d = data['data']
            tm = d['time']
            self.world.time_manager.day = tm['day']
            self.world.time_manager.hour = tm['hour']
            self.world.time_manager.minute = tm['minute']

            p = d['player']
            self.world.player.location = p['location']
            self.world.player.base = p['base']
            self.world.player.money = p['money']
            self.world.player.wake_time = p['wake_time']
            self.world.player.abl = p['abl']
            self.world.player.exp = p['exp']
            self.world.player.juel = p['juel']
            self.world.player.palam = p['palam']
            self.world.player.talent = p['talent']

            from game_engine.models.shipgirl import ShipGirl
            for sg_id, st in d['shipgirls'].items():
                sg = ShipGirl(**self.world.npc_manager.shipgirls_db[sg_id])
                sg.location = st['location']
                sg.base = st['base']
                sg.favor = st['favor']
                sg.trust = st['trust']
                sg.abl = st['abl']
                sg.exp = st['exp']
                sg.juel = st['juel']
                sg.palam = st['palam']
                sg.cflag = st['cflag']
                sg.update_palam_level()
                self.world.npc_manager.shipgirls[sg_id] = sg

            self.world.work_manager.works = d['work']['works']
            self.world.work_manager.works_done = d['work']['works_done']
            self.world.menu_active = d['menu_active']

            sec_id = d['secretary_ship_id']
            self.world.npc_manager.secretary_ship = (
                self.world.npc_manager.shipgirls[sec_id] if sec_id else None
            )
            self.world.player.update_palam_level()
            return None
        except (KeyError, TypeError, ValueError) as e:
            return f'存档数据损坏：{e}'

    def _slot_path(self, slot: int) -> Path:
        return self.sav_dir / f'slot_{slot}.json'

    def save_game(self, slot: int) -> dict:
        """保存到槽位，返回 meta（供前端提示）"""
        path = self._slot_path(slot)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.serialize_world()
        data['meta']['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data['meta']

    def load_game(self, slot: int) -> str | None:
        """从槽位读档并还原 world。成功返回 None，失败返回错误信息"""
        path = self._slot_path(slot)
        if not path.exists():
            return '该槽位没有存档'
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return f'存档读取失败：{e}'
        return self.deserialize_world(data)

    def get_save_list(self) -> list[dict]:
        """返回 3 个槽位信息：{slot, has_save, day, hour, minute, player_name}"""
        result = []
        for slot in range(1, SLOT_COUNT + 1):
            entry = {'slot': slot, 'has_save': False}
            path = self._slot_path(slot)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        meta = json.load(f).get('meta', {})
                    entry.update({
                        'has_save': True,
                        'day': meta.get('day'),
                        'hour': meta.get('hour'),
                        'minute': meta.get('minute'),
                        'player_name': meta.get('player_name', ''),
                    })
                except (json.JSONDecodeError, OSError):
                    entry['has_save'] = False
            result.append(entry)
        return result
