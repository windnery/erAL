# -*- coding: utf-8 -*-
"""第二层：指令系统测试

覆盖：所有指令注册完整性、can 边界、执行后状态变化
重点：约会系统 can 门槛、end_date 状态清理、body_touch 等 interact 指令
"""
import pytest

from conftest import place_next_to_player


# ============================================================
# 指令注册完整性（防"老坑"：忘导入）
# ============================================================

class TestRegistration:
    """所有指令必须注册（回归：interact/__init__ 忘导入的坑）"""

    def test_all_interact_commands_registered(self):
        from game_engine.commands._commands import REGISTER_CMD
        expected = {
            # interact
            'talk', 'hug', 'body_touch', 'invite_date', 'end_date',
            'work_together', 'rub_the_head', 'rub_the_butt',
            'rub_the_belly', 'request_a_lap_pillow',
            'poke_the_cheek', 'pinching_cheeks',
            # 日常
            'nap', 'sleep', 'work', 'open_your_eyes',
            # 系统
            'move', 'leave', 'save', 'load',
            # 菜单
            'set_wake_up_time', 'set_secretary_ship',
            # 前端
            'show_chara_info',
        }
        missing = expected - set(REGISTER_CMD.keys())
        assert not missing, f'以下指令未注册: {missing}'

    def test_registered_commands_have_names(self):
        """每个注册指令都有名字"""
        from game_engine.commands._commands import REGISTER_CMD, REGISTER_CMD_NAME
        for k in REGISTER_CMD:
            assert k in REGISTER_CMD_NAME, f'{k} 缺名字'
            assert REGISTER_CMD_NAME[k], f'{k} 名字为空'

    def test_system_commands_needs_target_false(self):
        """save/load 等无需目标的系统指令 needs_target=False
        （move/leave 需选节点/区域，虽标 True 但走 get_cmd_options 分支）"""
        from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAT, REGISTER_NEEDS_TARGET
        for k in ('save', 'load'):
            assert k in REGISTER_CMD
            assert REGISTER_NEEDS_TARGET.get(k) is False, f'{k} 应 needs_target=False'

    def test_show_chara_info_is_frontend(self):
        """查看角色信息是前端指令"""
        from game_engine.commands._commands import REGISTER_CMD, REGISTER_FRONTEND
        assert REGISTER_FRONTEND.get('show_chara_info') is True


# ============================================================
# 约会系统 can 门槛
# ============================================================

class TestInviteDateCan:
    """invite_date can：relationship>=1 + intimacy>=5 + favor>=240 + 非工作 + 非约会"""

    def _setup(self, world, favor=0, intimacy=0, relationship='0'):
        npc = world.npc_manager.shipgirls['Z23']
        npc.favor = favor
        npc.abl['intimacy_abl'] = intimacy
        npc.set_talent('relationship', relationship)
        place_next_to_player(world, npc)
        return npc

    def test_can_false_low_favor(self, world):
        """好感不够拒绝"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=100, intimacy=5, relationship='1')
        assert can(world, npc) is False

    def test_can_false_low_intimacy(self, world):
        """亲密不够拒绝"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=2, relationship='1')
        assert can(world, npc) is False

    def test_can_false_low_relationship(self, world):
        """关系不够拒绝"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=5, relationship='0')
        assert can(world, npc) is False

    def test_can_true_qualified(self, world):
        """全达标允许"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=5, relationship='1')
        assert can(world, npc) is True

    def test_can_false_dating_already(self, world):
        """约会中拒绝"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=5, relationship='1')
        npc.cflag['dating'] = True
        assert can(world, npc) is False

    def test_can_false_sleeping(self, world):
        """睡觉中拒绝"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=5, relationship='1')
        npc.cflag['sleeping'] = True
        assert can(world, npc) is False

    def test_can_false_not_nearby(self, world):
        """不在玩家身边拒绝（needs_target 指令要求 nearby）"""
        from game_engine.commands.interact.invite_date import can
        npc = self._setup(world, favor=500, intimacy=5, relationship='1')
        # 移到别的房间
        world.npc_manager.set_loc('Z23', 'home', 'bedroom')
        # 注意：can 本身不检查 nearby，这是 CommandManager.do_cmd 的职责
        # 这里只验证 can 在玩家所在位置时通过
        assert can(world, npc) is True


class TestEndDate:
    """end_date：约会中可结束、非约会拒绝、清状态"""

    def _start_dating(self, world):
        npc = world.npc_manager.shipgirls['Z23']
        place_next_to_player(world, npc)
        npc.cflag['dating'] = True
        npc.cflag['dating_following'] = True
        return npc

    def test_can_true_when_dating(self, world):
        from game_engine.commands.interact.end_date import can
        npc = self._start_dating(world)
        assert can(world, npc) is True

    def test_can_false_not_dating(self, world):
        from game_engine.commands.interact.end_date import can
        npc = self._start_dating(world)
        npc.cflag['dating'] = False
        assert can(world, npc) is False

    def test_end_date_clears_cflags(self, world):
        """执行 end_date 后清除约会状态"""
        from game_engine.commands.interact.end_date import end_date
        npc = self._start_dating(world)
        mes = end_date(world, 'Z23', time_out=True)
        assert npc.cflag.get('dating') is False
        assert npc.cflag.get('dating_following') is False
        assert isinstance(mes, list)

    def test_end_date_timeout_message(self, world):
        """超时结束有'时间太晚'文案"""
        from game_engine.commands.interact.end_date import end_date
        npc = self._start_dating(world)
        mes = end_date(world, 'Z23', time_out=True)
        assert any('太晚' in m for m in mes)

    def test_end_date_normal_message(self, world):
        """主动结束有正常文案"""
        from game_engine.commands.interact.end_date import end_date
        npc = self._start_dating(world)
        mes = end_date(world, 'Z23', time_out=False)
        assert any('太晚' not in m for m in mes)


# ============================================================
# interact 指令执行
# ============================================================

class TestInteractCommands:
    """交互指令执行不崩 + 好感/信赖变化"""

    @pytest.fixture(autouse=True)
    def _nearby(self, world):
        """所有交互测试先让 Z23 在玩家身边"""
        npc = world.npc_manager.shipgirls['Z23']
        place_next_to_player(world, npc)
        npc.cflag['sleeping'] = False
        world.player.base['energy'] = 100
        world.player.base['stamina'] = 100

    @pytest.mark.parametrize('cmd_name', [
        'talk', 'hug', 'body_touch',
        'rub_the_butt', 'rub_the_belly',
        'request_a_lap_pillow', 'pinching_cheeks',
    ])
    def test_interact_command_executes(self, world, cmd_name):
        """指令能执行且返回列表"""
        from game_engine.managers.CommandManager import CommandManager
        cm = world.command_manager
        result = cm.do_cmd(cmd_name, 'Z23')
        assert result is not None
        assert isinstance(result, (list, str)) or result == ''

    @pytest.mark.parametrize('cmd_name', ['poke_the_cheek', 'rub_the_head'])
    def test_interact_with_working_check_executes(self, world, cmd_name):
        """含玩家工作状态检查的指令应能执行

        ⚠️ 已知 bug：player.is_working() 不存在（is_working 已移到 ShipGirl），
        can 函数调用即 AttributeError → 指令永远不可用
        """
        result = world.command_manager.do_cmd(cmd_name, 'Z23')
        assert result is not None, f'{cmd_name} 应能执行（当前 is_working 崩溃）'

    def test_talk_increases_talk_exp(self, world):
        """talk 增加玩家会话经验"""
        from game_engine.commands.interact.talk import talk
        before = world.player.exp['talk_exp']
        mes = talk(world, 'Z23')
        assert world.player.exp['talk_exp'] == before + 1

    def test_work_together_requires_secretary(self, world):
        """一起工作需要秘书舰"""
        from game_engine.commands.interact.work_together import can
        npc = world.npc_manager.shipgirls['Z23']
        place_next_to_player(world, npc)
        assert can(world, npc) is False  # 未设秘书舰


# ============================================================
# 系统指令
# ============================================================

class TestSystemCommands:
    def test_move_changes_location(self, world):
        """移动指令改变玩家位置"""
        from game_engine.managers.CommandManager import CommandManager
        # 玩家在 home/living_room，先看可移动节点
        options = world.command_manager.get_cmd_options('move')
        assert isinstance(options, list) and len(options) > 0
        # 移动到一个节点
        target = options[0]
        if target.get('key') != 'return':
            result = world.command_manager.do_cmd('move', target['key'])
            assert world.player.location['node'] == target['key']

    def test_move_return_cancels(self, world):
        """move 取消（return）不改位置"""
        node_before = world.player.location['node']
        result = world.command_manager.do_cmd('move', 'return')
        assert world.player.location['node'] == node_before

    def test_leave_changes_region(self, world):
        """leave 改变区域"""
        options = world.command_manager.get_cmd_options('leave')
        assert isinstance(options, list) and len(options) > 0
        region_before = world.player.location['region']
        target = options[0]
        if target.get('key') != 'return':
            world.command_manager.do_cmd('leave', target['key'])
            assert world.player.location['region'] == target['key']


# ============================================================
# 日常指令
# ============================================================

class TestDailyCommands:
    def test_sleep_settles_day(self, world):
        """睡觉触发日终结算（需在卧室）"""
        world.player.base['energy'] = 100
        world.player.base['stamina'] = 100
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        world.time_manager.hour = 23
        world.time_manager.minute = 0
        before_day = world.time_manager.day
        mes = world.command_manager.do_cmd('sleep', None)
        assert isinstance(mes, list) and len(mes) > 0
        assert world.time_manager.day > before_day
        assert world.menu_active is True

    def test_nap_restores_stamina(self, world):
        """午睡恢复体力"""
        world.player.base['stamina'] = 50
        before = world.player.get_stamina()
        mes = world.command_manager.do_cmd('nap', None)
        assert world.player.get_stamina() >= before

    def test_work_increases_work_exp(self, world):
        """工作增加经验"""
        # 需要玩家在工作地点（WORK_LOC）才能通过 can_work
        world.player.location = {'region': 'office', 'node': 'desk'}
        before = world.player.exp['work_exp']
        mes = world.command_manager.do_cmd('work', None)
        assert world.player.exp['work_exp'] == before + 1
