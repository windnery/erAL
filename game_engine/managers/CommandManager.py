from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import REGISTER_CMD

if TYPE_CHECKING:
    from game_engine.managers.AllManager import AllManager


class CommandManager:
    def __init__(self, manager: AllManager):
        self.manager = manager

    def get_commands(self):
        # 获取当前可用的指令列表
        commands = self._get_common_commands()  # 通用指令
        commands += self._get_location_commands()  # 当前地点特定指令
        commands += self._get_npc_commands()  # 当前地点NPC特定指令
        return commands
    
    def get_cmd_options(self, command: str):
        # 根据指令名 返回这个指令所需的选项列表
        if command == 'move':
            return self.manager.map_manager.get_available_nodes()
        elif command == 'leave':
            return self.manager.map_manager.get_available_regions()
        # TODO: 其他指令在这里补充
        else:
            return []

    def do_cmd(self, command: str, option: str | None = None):
        # 执行指令 option是用户选择的选项
        func = REGISTER_CMD.get(command)
        if func:
            func(self.manager, option)
        # TODO: 执行完指令后统一处理副作用
        return self.manager.get_state()  # 返回最新状态


    def _get_common_commands(self):
        # 获取通用指令列表
        return [
            {'key': 'leave', 'name': '离开当前区域'},
            {'key': 'move', 'name': '移动到其他地点'},
            {'key': 'show_chara_info', 'name': '查看角色信息'},
            {'key': 'save', 'name': '存档'},
            {'key': 'load', 'name': '读档'}
        ]

    def _get_location_commands(self):
        # 获取当前地点特定的指令列表
        region = self.manager.map_manager.region
        node = self.manager.map_manager.node
        actions = self.manager.map_manager.maps[region][node].get('actions', {})
        return [{'key': k, 'name': v} for k, v in actions.items()]

    def _get_npc_commands(self):
        # 获取当前地点NPC特定的指令列表
        # TODO
        return []
