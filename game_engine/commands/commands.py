from ..manager.map_manager import MapManager
REGISTER_CMD = {}
def register_cmd(name: str):
    '''装饰器：自动把指令注册到字典中'''
    def decorator(func):
        REGISTER_CMD[name] = func
        return func
    return decorator


#=================命令区=================
@register_cmd('leave')
def leave(map_manager: MapManager, option: str):
    '''离开当前区域'''
    if option == 'return':
        # 取消离开
        return
    map_manager.region = option
    # 离开后默认进入该区域的默认节点
    map_manager.node = map_manager.regions[option]['entry_node']

@register_cmd('move')
def move(map_manager: MapManager, option: str):
    '''移动'''
    if option == 'return':
        # 取消移动
        return
    map_manager.node = option