from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from data.time.time_data import leave_time_data

if TYPE_CHECKING:
    from world import World



@register_cmd('leave', '离开当前区域', '系统', needs_target=False)
def leave(world: World, option: str):
    """离开当前区域（三段式复合流水线）"""
    if option == 'return':
        # 取消离开
        return None
    return world.movement_manager.start_leave(option)


@register_cmd('move', '移动', '系统', needs_target=False)
def move(world: World, option: str):
    """移动（区域内；通过 MovementManager 逐点步进状态机处理）"""
    if option == 'return':
        # 取消移动
        return None
    return world.movement_manager.start_local_move(option)


@register_cmd('items', '道具', '系统', needs_target=False, frontend=True)
def items(world: World, option: str):
    """道具"""
    return []


@register_cmd('juus', '☆啾信☆', '系统', needs_target=False, frontend=True)
def juus(world: World, option: str):
    """打开啾信"""
    return []


@register_cmd('save', '存档', '系统', needs_target=False)
def save(world: World, option=None):
    """存档：option 为槽位 key（'1'~'10'）"""
    if option is None:
        return ['请选择存档槽位']
    slot = int(option)
    meta = world.save_manager.save_game(slot)
    time_info = f" [{meta['saved_at']}]" if meta.get('saved_at') else ""
    return [f'已保存到槽位{slot}（第{meta["day"]}天 {meta["hour"]}:{str(meta["minute"]).zfill(2)}{time_info}）']


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
