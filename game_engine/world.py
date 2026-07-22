from .manager.map_manager import MapManager

class World:
    '''世界类'''
    def __init__(self) -> None:
        self.map_manager = MapManager() # 地图管理器