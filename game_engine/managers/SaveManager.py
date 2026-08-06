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
