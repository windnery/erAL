from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd

if TYPE_CHECKING:
    from world import World


@register_cmd('save', '存档', '系统', needs_target=False)
def save(world: World, option=None):
    """存档：option 为槽位 key（'1'/'2'/'3'）"""
    if option is None:
        return ['请选择存档槽位']
    slot = int(option)
    meta = world.save_manager.save_game(slot)
    return [f'已保存到槽位{slot}（第{meta["day"]}天 {meta["hour"]}:{str(meta["minute"]).zfill(2)}）']


@register_cmd('load', '读档', '系统', needs_target=False)
def load(world: World, option=None):
    """读档：option 为槽位 key（'1'/'2'/'3'）"""
    if option is None:
        return ['请选择存档槽位']
    slot = int(option)
    err = world.save_manager.load_game(slot)
    if err:
        return [err]
    return [f'读取了槽位{slot}的存档']
