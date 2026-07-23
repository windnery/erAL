from game_engine.commands._commands import register_cmd
from data.time.time_data import leave_time_data, move_time_data


@register_cmd('leave')
def leave(manager, option: str):
    '''离开当前区域'''
    if option == 'return':
        # 取消离开
        return
    player = manager.player
    map_manager = manager.map_manager
    current_region = player.location['region']
    # 推进时间并获取NPC变动消息
    npc_events = manager.advance_time_with_events(leave_time_data[current_region][option])
    player.location['region'] = option
    # 离开后默认进入该区域的默认节点
    player.location['node'] = map_manager.regions[option]['entry_node']

    region_name = map_manager.regions[option]['name']
    node_name = map_manager.maps[option][player.location['node']]['name']
    mes = [f"离开了{region_name}……",
           f"来到了{region_name}的{node_name}"]
    mes += npc_events
    return mes

@register_cmd('move')
def move(manager, option: str):
    '''移动'''
    if option == 'return':
        # 取消移动
        return
    
    # 推进时间并获取NPC变动消息
    npc_events = manager.advance_time_with_events(move_time_data[manager.player.location['node']][option])
    player = manager.player
    player.location['node'] = option

    return npc_events if npc_events else []