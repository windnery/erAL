import pytest
from world import World
from game_engine.commands._commands import REGISTER_COOLDOWN


class TestCommandCooldown:
    @pytest.fixture
    def world(self):
        w = World()
        # 确保进入正常游戏状态（非缓冲菜单、非调教模式）
        w.menu_active = False
        w.train_mode = False
        # 设置时间为上午 10:00，所有角色均已起床
        w.time_manager.hour = 10
        w.time_manager.minute = 0
        # 将玩家和舰娘置于同一地点
        w.player.location = {'region': 'home', 'node': 'living_room'}
        w.npc_manager.set_loc('Z23', 'home', 'living_room')
        w.npc_manager.set_loc('laffey', 'home', 'living_room')
        # 给一定的好感和亲密确保指令可用
        z23 = w.npc_manager.shipgirls['Z23']
        z23.favor = 1000
        z23.abl['intimacy_abl'] = 5
        laffey = w.npc_manager.shipgirls['laffey']
        laffey.favor = 1000
        laffey.abl['intimacy_abl'] = 5
        return w

    def test_registered_cooldowns_loaded(self):
        """验证配置的冷却时间已正确加载到注册表中"""
        assert REGISTER_COOLDOWN.get('poke_the_cheek') == 5
        assert REGISTER_COOLDOWN.get('rub_the_head') == 10
        assert REGISTER_COOLDOWN.get('hug') == 30
        assert REGISTER_COOLDOWN.get('nap') == 120

    def test_npc_command_cooldown_and_isolation(self, world):
        """测试目标NPC指令执行后进入冷却并在指令列表中被隐藏，同时不影响其他NPC"""
        z23 = world.npc_manager.shipgirls['Z23']
        laffey = world.npc_manager.shipgirls['laffey']

        # 初始状态：Z23 和 Laffey 都能看到 poke_the_cheek 指令
        z23_cmds_before = [c['key'] for c in world.command_manager.get_act_com('Z23')]
        laffey_cmds_before = [c['key'] for c in world.command_manager.get_act_com('laffey')]
        assert 'poke_the_cheek' in z23_cmds_before
        assert 'poke_the_cheek' in laffey_cmds_before

        # 对 Z23 执行 poke_the_cheek
        result = world.command_manager.do_cmd('poke_the_cheek', 'Z23')
        assert result != ''

        # 执行后：Z23 处于冷却中，指令列表中 poke_the_cheek 消失
        assert world.command_manager.is_cmd_cooling_down('poke_the_cheek', z23)
        z23_cmds_after = [c['key'] for c in world.command_manager.get_act_com('Z23')]
        assert 'poke_the_cheek' not in z23_cmds_after

        # 隔离性：Laffey 未进入冷却，依然可执行 poke_the_cheek
        # 保证 Laffey 仍在当前地点
        world.npc_manager.set_loc('laffey', 'home', 'living_room')
        assert not world.command_manager.is_cmd_cooling_down('poke_the_cheek', laffey)
        laffey_cmds_after = [c['key'] for c in world.command_manager.get_act_com('laffey')]
        assert 'poke_the_cheek' in laffey_cmds_after

        # 再次对 Z23 执行 poke_the_cheek 应被拦截
        repeat_result = world.command_manager.do_cmd('poke_the_cheek', 'Z23')
        assert repeat_result == ''

    def test_cooldown_expires_with_time(self, world):
        """测试随着游戏时间推进，冷却自然到期并重新出现"""
        z23 = world.npc_manager.shipgirls['Z23']
        # 执行 poke_the_cheek (CD = 5 分钟)
        world.command_manager.do_cmd('poke_the_cheek', 'Z23')
        assert world.command_manager.is_cmd_cooling_down('poke_the_cheek', z23)

        # 推进 4 分钟：仍在冷却中
        world.time_manager.advance_time(4)
        assert world.command_manager.is_cmd_cooling_down('poke_the_cheek', z23)
        assert 'poke_the_cheek' not in [c['key'] for c in world.command_manager.get_act_com('Z23')]

        # 再推进 2 分钟（总计 6 分钟）：冷却结束
        world.time_manager.advance_time(2)
        assert not world.command_manager.is_cmd_cooling_down('poke_the_cheek', z23)
        assert 'poke_the_cheek' in [c['key'] for c in world.command_manager.get_act_com('Z23')]

    def test_location_command_cooldown(self, world):
        """测试无目标/地点指令（如 nap）的冷却"""
        world.player.location = {'region': 'home', 'node': 'living_room'}
        loc_cmds_before = [c['key'] for c in world.command_manager._get_location_commands()]
        assert 'nap' in loc_cmds_before

        # 执行 nap
        world.command_manager.do_cmd('nap')

        # 执行后 nap 处于冷却中（CD = 120 分钟），地点指令中被隐藏
        assert world.command_manager.is_cmd_cooling_down('nap', world.player)
        loc_cmds_after = [c['key'] for c in world.command_manager._get_location_commands()]
        assert 'nap' not in loc_cmds_after

        # 再次执行被拦截
        assert world.command_manager.do_cmd('nap') == ''

    def test_cooldown_save_and_load(self, world, tmp_path):
        """测试存档与读档完整保留冷却状态"""
        world.save_manager.sav_dir = tmp_path
        z23 = world.npc_manager.shipgirls['Z23']

        # 执行 hug (CD = 30 分钟)
        world.command_manager.do_cmd('hug', 'Z23')
        assert world.command_manager.is_cmd_cooling_down('hug', z23)

        # 存档到槽位 1
        world.save_manager.save_game(1)

        # 创建新世界并读档
        new_world = World()
        new_world.save_manager.sav_dir = tmp_path
        err = new_world.save_manager.load_game(1)
        assert err is None

        # 读档后验证 Z23 仍在冷却中
        new_z23 = new_world.npc_manager.shipgirls['Z23']
        assert new_world.command_manager.is_cmd_cooling_down('hug', new_z23)
        assert 'hug' not in [c['key'] for c in new_world.command_manager.get_act_com('Z23')]

    def test_settle_day_cleans_expired_cooldowns(self, world):
        """测试日终结算跨天后，过期的冷却记录被自动清理"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.command_manager.do_cmd('poke_the_cheek', 'Z23')
        assert 'poke_the_cheek' in z23.cmd_cooldowns

        # 睡觉结算（推进数小时到第二天醒来）
        world.settle_day(sleep=True)

        # 冷却已过期并从字典中清理
        assert not world.command_manager.is_cmd_cooling_down('poke_the_cheek', z23)
        assert 'poke_the_cheek' not in z23.cmd_cooldowns
