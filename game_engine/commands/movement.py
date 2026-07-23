from game_engine.commands._commands import register_cmd
from data.time.time_data import leave_time_data, move_time_data


@register_cmd('leave')
def leave(manager, option: str):
    '''离开当前区域'''
    if option == 'return':
        # 取消离开
        return
    map_manager = manager.map_manager
    # 推进时间
    manager.time_manager.advance_time(leave_time_data[map_manager.region][option])
    map_manager.region = option
    # 离开后默认进入该区域的默认节点
    map_manager.node = map_manager.regions[option]['entry_node']
    map_manager.region_name = map_manager.regions[option]['name']
    map_manager.node_name = map_manager.maps[option][map_manager.node]['name']

    return [f"你离开了{map_manager.region_name}……",
            f"来到了{map_manager.region_name}的{map_manager.node_name}"]

@register_cmd('move')
def move(manager, option: str):
    '''移动'''
    if option == 'return':
        # 取消移动
        return
    
    map_manager = manager.map_manager
    # 推进时间
    manager.time_manager.advance_time(move_time_data[map_manager.node][option])
    old_node = map_manager.node_name
    map_manager.node = option
    map_manager.node_name = map_manager.maps[map_manager.region][map_manager.node]['name']

    return []