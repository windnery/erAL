# -*- coding: utf-8 -*-
"""
erAL 核心系统测试 —— 示例：约会系统 + 日终结算 + 数值管线

设计要点：
1. 直接构造 World（不启动 GUI、不跑游戏循环），纯 Python 环境测试
2. 直接改 npc.favor / abl / talent 等初始值，绕过"游戏内慢慢培养"的成本
3. 用 pytest fixture 保证每个测试都是干净的新世界

运行：python -m pytest tests/ -v
"""
import sys
from pathlib import Path

import pytest

# 确保项目根目录在导入路径上
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from world import World


@pytest.fixture
def world():
    """每个测试一个全新的世界实例"""
    w = World()
    return w


# ---------- 约会系统 ----------

def _make_datable(w, npc_id='Z23'):
    """把舰娘拉到可约会的门槛（favor>=240, intimacy>=5, relationship>=1）"""
    npc = w.npc_manager.shipgirls[npc_id]
    npc.favor = 500
    npc.abl['intimacy_abl'] = 6
    npc.set_talent('relationship', '1')
    # 放到玩家身边
    w.npc_manager.set_loc(npc_id, w.player.location['region'], w.player.location['node'])
    return npc


class TestInviteDate:
    """约会邀请"""

    def test_invite_date_registered(self, world):
        """约会指令已注册"""
        from game_engine.commands._commands import REGISTER_CMD
        assert 'invite_date' in REGISTER_CMD

    def test_can_false_when_low_favor(self, world):
        """好感不够时不能邀请"""
        npc = world.npc_manager.shipgirls['Z23']
        npc.favor = 100  # 低于240
        npc.abl['intimacy_abl'] = 5
        npc.set_talent('relationship', '1')
        world.npc_manager.set_loc('Z23', world.player.location['region'], world.player.location['node'])
        from game_engine.commands.interact.invite_date import can
        assert can(world, npc) is False

    def test_can_true_when_qualified(self, world):
        """达标后可以邀请"""
        npc = _make_datable(world)
        from game_engine.commands.interact.invite_date import can
        assert can(world, npc) is True

    def test_invite_success_sets_dating_cflag(self, world):
        """成功邀请后进入约会状态"""
        npc = _make_datable(world)
        # 拉高数值保证成功（able 需要分数>=24）
        npc.favor = 900
        npc.abl['intimacy_abl'] = 8
        npc.abl['obedience_abl'] = 5
        npc.abl['servant_abl'] = 5
        world.player.abl['talk_abl'] = 6
        npc.set_talent('relationship', '2')
        npc.set_talent('lover', '1')

        from game_engine.commands.interact.invite_date import invite_date
        mes = invite_date(world, 'Z23')
        assert npc.cflag.get('dating') is True
        assert npc.cflag.get('dating_following') is True
        assert any('成功' in m for m in mes), f"未显示成功，消息: {mes}"

    def test_end_date_clears_cflag(self, world):
        """结束约会清除状态"""
        npc = _make_datable(world)
        npc.cflag['dating'] = True
        npc.cflag['dating_following'] = True

        from game_engine.commands.interact.end_date import end_date
        end_date(world, 'Z23', time_out=True)
        assert npc.cflag.get('dating') is False
        assert npc.cflag.get('dating_following') is False


class TestSettleDay:
    """日终结算"""

    def test_energy_exhaustion_no_crash(self, world):
        """气力耗尽不崩溃（回归测试：曾经删除耗尽结算逻辑）"""
        world.player.set_energy(0)
        mes = world.settle_day(exhaustion=True)
        assert isinstance(mes, list)

    def test_sleep_recovers_stamina(self, world):
        """睡觉恢复体力（把时间推进到晚上再睡）"""
        # 先推进时间到 23:00，确保 sleep 有足够时长
        world.time_manager.hour = 23
        world.time_manager.minute = 0
        world.player.wake_time = {'hour': 7, 'minute': 0}
        world.player.set_stamina(100)
        before = world.player.get_stamina()
        world.settle_day(sleep=True)
        assert world.player.get_stamina() > before


class TestCommandRegistration:
    """指令注册完整性（回归测试：防止老坑-指令未导入）"""

    def test_all_interact_commands_registered(self, world):
        from game_engine.commands._commands import REGISTER_CMD
        expected = {'talk', 'hug', 'body_touch', 'invite_date', 'end_date',
                    'work_together', 'rub_the_head', 'rub_the_butt',
                    'rub_the_belly', 'request_a_lap_pillow',
                    'poke_the_cheek', 'pinching_cheeks'}
        missing = expected - set(REGISTER_CMD.keys())
        assert not missing, f"以下指令未注册: {missing}"


class TestIsFollowing:
    """跟随状态（回归测试：键名不匹配 bug）"""

    def test_following_three_keys(self, world):
        npc = world.npc_manager.shipgirls['Z23']
        assert npc.is_following() is False
        npc.cflag['secretary_ship_following'] = True
        assert npc.is_following() is True
        npc.cflag['secretary_ship_following'] = False
        npc.cflag['dating_following'] = True
        assert npc.is_following() is True


if __name__ == '__main__':
    import pytest as pt
    pt.main([__file__, '-v'])
