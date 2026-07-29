from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import REGISTER_CMD

if TYPE_CHECKING:
    from world import World


class CommandManager:
    def __init__(self, world: World):
        self.world = world

    def get_Act_COM(self):
        '''获取交互指令'''
        act_com = self._get_location_commands()  # 当前地点特定指令
        act_com += self._get_npc_commands()  # 当前地点NPC特定指令
        return act_com

    def get_EX_COM(self):
        '''获取通用指令(系统指令)'''
        ex_com = self._get_common_commands()
        return ex_com
    
    def get_cmd_options(self, command: str):
        # 根据指令名 返回这个指令所需的选项列表
        if command == 'move':
            return self.world.map_manager.get_available_nodes(self.world.player.location['region'], self.world.player.location['node'])
        elif command == 'leave':
            return self.world.map_manager.get_available_regions(self.world.player.location['region'])
        # TODO: 其他指令在这里补充
        else:
            return []

    def do_cmd(self, command: str, option: str | None = None):
        # 执行指令 option是用户选择的选项
        func = REGISTER_CMD.get(command)
        mes = func(self.world, option) if func else ''
        return mes  # 返回最新状态


    def _get_common_commands(self):
        # 获取通用指令列表
        return [
            {'key': 'leave', 'name': '离开当前区域'},
            {'key': 'move', 'name': '移动'},
            {'key': 'show_chara_info', 'name': '查看角色信息'},
            {'key': 'save', 'name': '存档'},
            {'key': 'load', 'name': '读档'}
        ]

    def _get_location_commands(self):
        # 获取当前地点特定的指令列表
        region = self.world.player.location['region']
        node = self.world.player.location['node']
        actions = self.world.map_manager.maps[region][node].get('actions', {})
        return [{'key': k, 'name': v} for k, v in actions.items()]

    def _get_npc_commands(self):
        # 获取当前地点NPC特定的指令列表
        # 只有当前位置有NPC时才返回（前端再根据是否选中决定是否显示）
        if not self.world.npc_manager.get_npcs_at(self.world.player.location['region'], self.world.player.location['node']):
            return []
        commands = [
            {'key': 'talk', 'name': '会话', 'needs_target': True},
            {'key': 'rub_the_head', 'name': '摸头', 'needs_target': True},
            {'key': 'body_touch', 'name': '身体接触', 'needs_target': True},
            
        ]
        # TODO: 加入NPC特定的指令
        return commands
