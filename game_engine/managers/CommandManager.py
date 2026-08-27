from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAN, REGISTER_CMD_NAME, REGISTER_CAT, \
    REGISTER_NEEDS_TARGET, REGISTER_FRONTEND, REGISTER_MODE

if TYPE_CHECKING:
    from world import World


LOGGER = logging.getLogger('eral.command')


class CommandManager:
    def __init__(self, world: World):
        self.world = world

    def get_act_com(self, selected_npc_id: str | None = None):
        """获取交互指令"""
        act_com = self._get_location_commands()
        act_com += self._get_npc_commands(selected_npc_id)
        return act_com

    def get_ex_com(self):
        """获取通用指令(系统指令)"""
        ex_com = self._get_system_commands()
        return ex_com

    def get_menu_com(self):
        """获取缓冲菜单指令"""
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
            # 全部舰娘
            current_sec_id = self.world.npc_manager.secretary_ship.id if self.world.npc_manager.secretary_ship else None
            options = []
            for sg in self.world.npc_manager.get_all_npcs():
                avatar_path = ''
                if hasattr(self.world, 'skin_manager') and self.world.skin_manager:
                    avatar_path = self.world.skin_manager.get_ship_skin_paths(sg.id).get('avatar', '')
                if not avatar_path:
                    avatar_path = f"assets/avatars/{sg.name}/{sg.id}_default.webp"
                options.append({
                    'key': sg.id,
                    'name': sg.name,
                    'id': sg.id,
                    'ship_type': str(sg.talent.get('ship_type', '0')),
                    'alignment': str(sg.talent.get('alignment', '0')),
                    'avatar': avatar_path,
                    'is_current': sg.id == current_sec_id,
                    'value': {'shipgirl_id': sg.id}
                })
            return options
        elif command in ('save', 'load'):
            slots = self.world.save_manager.get_save_list()
            options = []
            for s in slots:
                if s['has_save']:
                    time_info = f" [{s['saved_at']}]" if s.get('saved_at') else ""
                    name = (f'槽位{s["slot"]}：第{s["day"]}天 '
                            f'{str(s["hour"]).zfill(2)}:{str(s["minute"]).zfill(2)} {s["player_name"]}{time_info}')
                else:
                    name = f'槽位{s["slot"]}：空'
                options.append({
                    'key': str(s['slot']),
                    'name': name,
                    'has_save': s['has_save']
                })
            return options
        else:
            return []

    def do_cmd(self, command: str, option: str | None = None):
        # 执行指令
        func = REGISTER_CMD.get(command)
        if not func:
            return ''

        # 调教指令：单参数约定 func(world)，目标从会话解析
        if REGISTER_MODE.get(command):
            can = REGISTER_CAN.get(command)
            if can and not can(self.world):
                return ''
            result = func(self.world)
            LOGGER.info(
                'command.executed',
                extra={
                    'category': REGISTER_CAT.get(command, ''),
                    'command': command,
                    'target_id': None,
                    'train_mode': True,
                },
            )
            return result

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

        result = func(self.world, option)
        LOGGER.info(
            'command.executed',
            extra={
                'category': REGISTER_CAT.get(command, ''),
                'command': command,
                'target_id': option if is_target_command else None,
                'train_mode': False,
            },
        )
        return result

    def _get_system_commands(self):
        # 系统类指令：从注册表反查 cat='系统' 的指令
        sys_com = [{'key': k, 'name': REGISTER_CMD_NAME[k], 'cat': REGISTER_CAT[k],
                    'frontend': REGISTER_FRONTEND.get(k, False)}
                   for k in REGISTER_CMD if REGISTER_CAT.get(k) == '系统']
        return sys_com

    def _get_location_commands(self):
        """Return commands that depend on the current location, not an NPC."""
        commands = []
        for key in REGISTER_CMD:
            if REGISTER_CAT.get(key) in ('系统', '菜单'):
                continue
            if REGISTER_MODE.get(key):
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
            if REGISTER_MODE.get(key):
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
                'frontend': REGISTER_FRONTEND.get(key, False),
            })
        return commands
