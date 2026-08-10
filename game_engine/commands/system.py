from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from data.time.time_data import leave_time_data, move_time_data

if TYPE_CHECKING:
    from world import World


@register_cmd('leave', '离开当前区域', '系统')
def leave(world: World, option: str):
    """离开当前区域"""
    if option == 'return':
        # 取消离开
        return None
    player = world.player
    map_manager = world.map_manager
    current_region = player.location['region']
    minutes = leave_time_data[current_region][option]
    # 先更新玩家位置到目的区域，再推进时间（事件基于目的地生成）
    player.location['region'] = option
    player.location['node'] = map_manager.regions[option]['entry_node']

    # 推进时间并获取NPC变动消息
    npc_events = world.advance_time_with_events(minutes)

    region_name = map_manager.regions[option]['name']
    node_name = map_manager.maps[option][player.location['node']]['name']
    mes = [f"离开了{region_name}……",
           f"来到了{region_name}的{node_name}"]
    mes += npc_events
    return mes


@register_cmd('move', '移动', '系统')
def move(world: World, option: str):
    """移动"""
    if option == 'return':
        # 取消移动
        return

    player = world.player
    minutes = move_time_data[player.location['node']][option]
    # 先更新玩家位置到目的地，再推进时间（事件基于目的地生成）
    player.location['node'] = option

    # 推进时间并获取NPC变动消息
    npc_events = world.advance_time_with_events(minutes)

    return npc_events if npc_events else []


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
