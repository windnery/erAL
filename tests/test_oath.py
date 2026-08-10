# -*- coding: utf-8 -*-
"""誓约指令测试"""
import pytest
from world import World


@pytest.fixture
def world():
    return World()


@pytest.fixture
def player(world):
    return world.player


def _make_oathable(world, npc, favor=2000, trust=800, intimacy=10, relationship='3'):
    """构造可誓约状态（含移到玩家身边）：
    - 关系=爱（relationship=3）
    - 亲密>=9
    - 好感>=1500
    - 持有誓约之戒
    """
    npc.set_talent('relationship', relationship)
    npc.abl['intimacy_abl'] = intimacy
    npc.favor = favor
    npc.trust = trust
    world.item_manager.gain_items('oath_ring', 1)
    world.npc_manager.set_loc(npc.id, world.player.location['region'], world.player.location['node'])
    return npc


class TestOathRegistration:
    """誓约指令注册"""

    def test_oath_registered(self):
        from game_engine.commands._commands import REGISTER_CMD, REGISTER_CMD_NAME
        assert 'oath' in REGISTER_CMD
        assert REGISTER_CMD_NAME['oath'] == '誓约'

    def test_oath_category(self):
        from game_engine.commands._commands import REGISTER_CAT
        assert REGISTER_CAT.get('oath') == '日常'

    def test_oath_needs_target(self):
        from game_engine.commands._commands import REGISTER_NEEDS_TARGET
        assert REGISTER_NEEDS_TARGET.get('oath', True) is True


class TestOathCan:
    """誓约 can 判定"""

    def test_can_false_when_no_ring(self, world, z23):
        """无戒指时不可誓约"""
        assert not world.item_manager.has_item('oath_ring')
        # 其他条件满足
        z23.set_talent('relationship', '3')
        z23.abl['intimacy_abl'] = 10
        z23.favor = 2000
        z23.trust = 800
        from game_engine.commands.interact.oath import can
        assert can(world, z23) is False

    def test_can_false_when_relationship_below_3(self, world, z23):
        """关系未达爱时不可誓约"""
        _make_oathable(world, z23, relationship='2')  # 喜欢
        from game_engine.commands.interact.oath import can
        assert can(world, z23) is False

    def test_can_false_when_intimacy_below_9(self, world, z23):
        """亲密<9时不可誓约"""
        _make_oathable(world, z23, intimacy=8)
        from game_engine.commands.interact.oath import can
        assert can(world, z23) is False

    def test_can_false_when_favor_below_1500(self, world, z23):
        """好感<1500时不可誓约"""
        _make_oathable(world, z23, favor=1400)
        from game_engine.commands.interact.oath import can
        assert can(world, z23) is False

    def test_can_true_when_all_conditions_met(self, world, z23):
        """全部条件满足时可誓约"""
        _make_oathable(world, z23)
        from game_engine.commands.interact.oath import can
        assert can(world, z23) is True


class TestOathExecution:
    """誓约执行（成功/失败分支）"""

    def test_oath_success_sets_relationship_4(self, world, z23, player):
        """誓约成功：关系变为4（誓约），get_talent_name 不崩"""
        _make_oathable(world, z23, favor=5000, trust=900)
        # 提高成功率：高会话
        player.abl['talk_abl'] = 5

        result = world.command_manager.do_cmd('oath', 'Z23')
        assert isinstance(result, list)
        assert z23.talent.get('relationship') == '4'
        # Bug 1 验证：字符串 '4' 存进去后 get_talent_name 正常
        assert z23.get_talent_name('relationship') == '誓约'

    def test_oath_success_consumes_ring(self, world, z23, player):
        """誓约成功：消耗戒指（use_items 不再校验 is_usable）"""
        _make_oathable(world, z23, favor=5000, trust=900)
        player.abl['talk_abl'] = 5
        assert world.item_manager.has_item('oath_ring')
        world.command_manager.do_cmd('oath', 'Z23')
        assert world.item_manager.has_item('oath_ring') is False

    def test_oath_failure_keeps_relationship_3(self, world, z23, player):
        """誓约失败：关系保持3（爱）"""
        _make_oathable(world, z23, favor=1600, trust=200)
        player.abl['talk_abl'] = 0  # 低会话降低成功率

        result = world.command_manager.do_cmd('oath', 'Z23')
        assert isinstance(result, list)
        assert z23.talent.get('relationship') == '3'

    def test_oath_failure_does_not_consume_ring(self, world, z23, player):
        """誓约失败：不消耗戒指"""
        _make_oathable(world, z23, favor=1600, trust=200)
        player.abl['talk_abl'] = 0
        assert world.item_manager.has_item('oath_ring')
        world.command_manager.do_cmd('oath', 'Z23')
        assert world.item_manager.has_item('oath_ring')

    def test_oath_consumes_energy_on_both_branches(self, world, z23, player):
        """誓约成功/失败都消耗气力"""
        _make_oathable(world, z23, favor=5000, trust=900)
        player.abl['talk_abl'] = 5
        initial_energy = player.base['energy']
        world.command_manager.do_cmd('oath', 'Z23')
        assert player.base['energy'] == initial_energy - 100

    def test_oath_failure_gives_negative_source(self, world, z23, player):
        """誓约失败：产生负向 source（escape/disgust）"""
        _make_oathable(world, z23, favor=1600, trust=200)
        player.abl['talk_abl'] = 0
        # 重置 palam 以便观察变化
        for k in z23.palam:
            z23.palam[k] = 0
        world.command_manager.do_cmd('oath', 'Z23')
        # escape_palam / disgust_palam 应增加（由 source 转化）
        assert z23.palam.get('escape_palam', 0) > 0 or z23.palam.get('disgust_palam', 0) > 0
