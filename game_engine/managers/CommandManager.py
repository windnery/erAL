from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAN, REGISTER_CMD_NAME, REGISTER_CAT, REGISTER_NEEDS_TARGET

if TYPE_CHECKING:
    from world import World


class CommandManager:
    def __init__(self, world: World):
        self.world = world

    def get_Act_COM(self, selected_npc_id: str | None = None):
        '''获取交互指令'''
        act_com = self._get_location_commands()
        act_com += self._get_npc_commands(selected_npc_id)
        return act_com

    def get_EX_COM(self):
        '''获取通用指令(系统指令)'''
        ex_com = self._get_system_commands()
        return ex_com

    def get_MENU_COM(self):
        '''获取缓冲菜单指令'''
        return [{'key': k, 'name': REGISTER_CMD_NAME[k], 'cat': '菜单'}
                for k in REGISTER_CMD if REGISTER_CAT.get(k) == '菜单']

    def get_cmd_options(self, command: str):
        # 根据指令名 返回这个指令所需的选项列表
        if command == 'move':
            return self.world.map_manager.get_available_nodes(self.world.player.location['region'],
                                                              self.world.player.location['node'])
        elif command == 'leave':
            return self.world.map_manager.get_available_regions(self.world.player.location['region'])
        elif command == 'set_wake_up_time':
            # 预设起床时间档位
            return [{'key': '6', 'name': '6:00', 'value': {'hour': 6, 'minute': 0}},
                    {'key': '7', 'name': '7:00', 'value': {'hour': 7, 'minute': 0}},
                    {'key': '8', 'name': '8:00', 'value': {'hour': 8, 'minute': 0}},
                    {'key': '9', 'name': '9:00', 'value': {'hour': 9, 'minute': 0}}]
        elif command == 'set_secretary_ship':
            # 全部舰娘（不限附近）
            return [{'key': sg.id, 'name': sg.name, 'value': {'shipgirl_id': sg.id}}
                    for sg in self.world.npc_manager.get_all_npcs()]
        # TODO: 其他指令在这里补充
        else:
            return []

    def do_cmd(self, command: str, option: str | None = None):
        # Execute a command and re-check its availability.
        func = REGISTER_CMD.get(command)
        if not func:
            return ''

        can = REGISTER_CAN.get(command)
        is_target_command = REGISTER_NEEDS_TARGET.get(command, True)
        is_system_command = REGISTER_CAT.get(command) == '系统'

        if can and not is_system_command:
            if is_target_command:
                if option is None:
                    return ''
                try:
                    npc = self.world.npc_manager.get_npc_by_id(option)
                except KeyError:
                    return ''
                nearby_npcs = self.world.npc_manager.get_npcs_at(
                    self.world.player.location['region'],
                    self.world.player.location['node'])
                if npc not in nearby_npcs or not can(self.world, npc):
                    return ''
            elif not can(self.world):
                return ''

        return func(self.world, option)
    def _get_system_commands(self):
        # 系统类指令：从注册表反查 cat='系统' 的指令
        sys_com = [{'key': k, 'name': REGISTER_CMD_NAME[k], 'cat': REGISTER_CAT[k]}
                   for k in REGISTER_CMD if REGISTER_CAT.get(k) == '系统']
        # save/load 未走注册表，先硬编码补上（保持原功能）
        sys_com += [{'key': 'save', 'name': '存档', 'cat': '系统'},
                    {'key': 'load', 'name': '读档', 'cat': '系统'}]
        return sys_com

    def _get_location_commands(self):
        """Return commands that depend on the current location, not an NPC."""
        commands = []
        for key in REGISTER_CMD:
            if REGISTER_CAT.get(key) in ('系统', '菜单'):
                continue
            if REGISTER_NEEDS_TARGET.get(key, True):
                continue

            can = REGISTER_CAN.get(key)
            if can and not can(self.world):
                continue
            commands.append({
                'key': key,
                'name': REGISTER_CMD_NAME[key],
                'needs_target': False,
                'cat': REGISTER_CAT[key],
            })
        return commands
    def _get_npc_commands(self, selected_npc_id: str | None = None):
        # Only generate NPC commands for the selected NPC.
        if selected_npc_id is None:
            return []

        npcs = self.world.npc_manager.get_npcs_at(
            self.world.player.location['region'],
            self.world.player.location['node'])
        npc = next((npc for npc in npcs if npc.id == selected_npc_id), None)
        if npc is None:
            return []

        commands = []
        for key in REGISTER_CMD:
            if REGISTER_CAT.get(key) == '系统':
                continue
            if not REGISTER_NEEDS_TARGET.get(key, True):
                continue

            can = REGISTER_CAN.get(key)
            if can and not can(self.world, npc):
                continue
            commands.append({
                'key': key,
                'name': REGISTER_CMD_NAME[key],
                'needs_target': True,
                'npc_id': npc.id,
                'cat': REGISTER_CAT[key],
            })
        return commands