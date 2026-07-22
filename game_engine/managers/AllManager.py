from game_engine.managers.CommandManager import CommandManager
from game_engine.managers.MapManager import MapManager
from game_engine.managers.TimeManager import TimeManager


class AllManager:
    def __init__(self):
        self.map_manager = MapManager()
        self.time_manager = TimeManager()
        self.command_manager = CommandManager(self)
        
    def get_state(self):
        '''一次性返回前端需要的全部状态'''
        return {
            'location': self.map_manager.get_current_loc(),
            'commands': self.command_manager.get_commands(),
            'time': self.time_manager.get_state()
        }