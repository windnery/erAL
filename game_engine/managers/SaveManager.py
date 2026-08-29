import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world import World

SAVE_VERSION = 3
SLOT_COUNT = 10
MAX_SLOTS = 10


class SaveManager:
    """世界状态存档管理：存 delta（仅运行时字段），静态数据读档时从 data/ 重建"""

    MAX_SLOTS = 10

    def __init__(self, world: 'World', sav_dir: Path | None = None):
        self.world = world
        self.sav_dir = Path(sav_dir) if sav_dir else Path('sav')

    def serialize_world(self) -> dict:
        world = self.world
        player = world.player
        train = world.train_manager.train
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
                'talent': sg.talent,
                'mark': sg.mark,
                'talk_fatigue': sg.talk_fatigue,
                'is_talk_fatigue': sg.is_talk_fatigue,
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
                    'cflag': player.cflag,
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
                # v2 新增：皮肤系统
                'skins': {
                    'unlocked_skins': sorted(world.skin_manager.unlocked_skins),
                    'locked_skins': sorted(world.skin_manager.locked_skins),
                    'today_shop_skins': list(world.skin_manager.today_shop_skins),
                    'ships_wear_skin': dict(world.skin_manager.ships_wear_skin),
                },
                # v2 新增：道具系统
                'items': dict(world.item_manager.items),
                # v3 新增：事件系统
                'events': world.event_manager.get_state(),
                'train': None if train is None else {
                    'location': train.location,
                    'actors': list(train.actors),
                    'targets': list(train.targets),
                    'participants': list(train.participants),
                    'initiative': dict(train.initiative),
                    'leader': train.leader,
                },
            },
        }

    def deserialize_world(self, data: dict) -> str | None:
        """把存档数据还原到 world。成功返回 None，失败返回错误信息"""
        try:
            version = data.get('version', 1)
            d = data['data']
            if version > SAVE_VERSION:
                return f'存档版本过新（{version} > {SAVE_VERSION}），请更新游戏'

            tm = d['time']
            self.world.time_manager.day = tm['day']
            self.world.time_manager.hour = tm['hour']
            self.world.time_manager.minute = tm['minute']

            p = d['player']
            self.world.player.location = p['location']
            player_base = p['base']
            # 旧存档没有精力字段时，按玩家最大精力初始化。
            player_base.setdefault('max_vitality', self.world.player.base.get('max_vitality', 2000))
            player_base.setdefault('vitality', player_base['max_vitality'])
            self.world.player.base = player_base
            self.world.player.money = p['money']
            self.world.player.wake_time = p['wake_time']
            self.world.player.abl = p['abl']
            self.world.player.exp = p['exp']
            self.world.player.juel = p['juel']
            self.world.player.palam = p['palam']
            self.world.player.talent = p['talent']
            self.world.player.cflag = p.get('cflag', self.world.player.cflag)

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
                sg.talent = st['talent']
                # 刻印（旧存档无该字段时保持默认0）
                sg.mark = st.get('mark', sg.mark)
                sg.talk_fatigue = st.get('talk_fatigue', 0)
                sg.is_talk_fatigue = st.get('is_talk_fatigue', False)
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

            skins = d.get('skins')
            if skins is not None:
                skin_mgr = self.world.skin_manager
                skin_mgr.unlocked_skins = set(skins.get('unlocked_skins', []))
                skin_mgr.locked_skins = set(skins.get('locked_skins', []))
                skin_mgr.ships_wear_skin = dict(skins.get('ships_wear_skin', {}))
                if 'today_shop_skins' in skins:
                    skin_mgr.today_shop_skins = list(skins.get('today_shop_skins', []))
                else:
                    skin_mgr.refresh_daily_shop()

            items = d.get('items')
            if items is not None:
                self.world.item_manager.items = dict(items)

            events = d.get('events')
            self.world.event_manager.load_state(events)

            train_state = d.get('train')
            if train_state is None:
                self.world.train_manager.train = None
                self.world.train_mode = False
            else:
                from game_engine.managers.TrainManager import Train

                train = Train(train_state['location'], self.world.player)
                train.actors = list(train_state['actors'])
                train.targets = list(train_state['targets'])
                train.participants = list(train_state['participants'])
                train.initiative = dict(train_state['initiative'])
                train.leader = train_state['leader']
                self.world.train_manager.train = train
                self.world.train_mode = True

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
        temp_path = path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
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
        error = self.deserialize_world(data)
        if error is not None:
            return error
        return None

    def get_save_list(self) -> list[dict]:
        """返回 10 个槽位信息：{slot, has_save, day, hour, minute, player_name, saved_at}"""
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
                        'saved_at': meta.get('saved_at', ''),
                    })
                except (json.JSONDecodeError, OSError):
                    entry['has_save'] = False
            result.append(entry)
        return result
