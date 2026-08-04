from game_engine.commands._commands import register_cmd
from data.time.time_data import leave_time_data, move_time_data


@register_cmd('leave', '离开当前区域', '系统')
def leave(manager, option: str):
    '''离开当前区域'''
    if option == 'return':
        # 取消离开
        return
    player = manager.player
    map_manager = manager.map_manager
    current_region = player.location['region']
    minutes = leave_time_data[current_region][option]
    # 先更新玩家位置到目的区域，再推进时间（事件基于目的地生成）
    player.location['region'] = option
    player.location['node'] = map_manager.regions[option]['entry_node']

    # 推进时间并获取NPC变动消息
    npc_events = manager.advance_time_with_events(minutes)

    region_name = map_manager.regions[option]['name']
    node_name = map_manager.maps[option][player.location['node']]['name']
    mes = [f"离开了{region_name}……",
           f"来到了{region_name}的{node_name}"]
    mes += npc_events
    return mes

@register_cmd('move', '移动', '系统')
def move(manager, option: str):
    '''移动'''
    if option == 'return':
        # 取消移动
        return
    
    player = manager.player
    minutes = move_time_data[player.location['node']][option]
    # 先更新玩家位置到目的地，再推进时间（事件基于目的地生成）
    player.location['node'] = option

    # 推进时间并获取NPC变动消息
    npc_events = manager.advance_time_with_events(minutes)

    return npc_events if npc_events else []