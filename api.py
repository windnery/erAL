import inspect

from game_engine.commands.commands import REGISTER_CMD
from game_engine.world import World

class Api:
    def __init__(self):
        self.world = World()
        # 万能上下文 传参用
        self.ctx = {
            'map_manager': self.world.map_manager
        }

    def get_current_loc(self):
        # 获取当前位置信息
        loc_info = self.world.map_manager.get_current_loc()
        return loc_info

    def get_commands(self):
        # 获取当前位置显示的命令
        cmd_info = self.world.map_manager.get_current_loc_cmd()
        return cmd_info

    def get_cmd_options(self, command: str):
        # 根据指令名 返回这个指令所需的选项列表
        if command == 'move':
            return self.world.map_manager.get_available_nodes()
        elif command == 'leave':
            return self.world.map_manager.get_available_regions()
        # TODO: 其他指令在这里补充
        else: return []

    def do_cmd(self, command: str, option: str|None = None):
        # 执行指令 option是用户选择的选项
        if command == 'move':
            REGISTER_CMD[command](self.world.map_manager, option)
        elif command == 'leave':
            REGISTER_CMD[command](self.world.map_manager, option)

