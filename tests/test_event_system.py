from __future__ import annotations
import pytest

from game_engine.events._base import BaseEvent, EVENT_REGISTRY, register_event
from game_engine.events._enums import EventTrigger
from game_engine.events.date.date_end_kiss import DateEndKissEvent
from game_engine.events.date.date_end_disappointment_clear import DateEndDisappointmentClearEvent
from game_engine.events.date.date_end_confess import DateEndConfessEvent
from game_engine.events.date.date_end_normal import DateEndNormalEvent
from game_engine.commands._context import CommandContext
from world import World


@pytest.fixture
def world():
    w = World()
    # 退出初始缓冲菜单
    w.menu_active = False
    return w


class TestEventSystemCore:
    """测试事件系统核心调度与注册机制"""

    def test_event_registry_has_date_events(self):
        date_events = EVENT_REGISTRY[EventTrigger.DATE_END]
        event_ids = [e.event_id for e in date_events]
        assert "date_end_kiss" in event_ids
        assert "date_end_disappointment_clear" in event_ids
        assert "date_end_confess" in event_ids
        assert "date_end_normal" in event_ids

    def test_event_priority_and_exclusive(self, world):
        ctx = CommandContext(world)
        laffey = world.npc_manager.get_npc_by_id('laffey')
        
        # 注册两个临时测试事件
        @register_event
        class LowPriEvent(BaseEvent):
            event_id = "test_low"
            trigger = EventTrigger.MILESTONE
            priority = 10
            exclusive = True
            def can_trigger(self, w, c, target=None, **kw): return True
            def execute(self, w, c, target=None, **kw):
                c.say("LOW")
                return True

        @register_event
        class HighPriEvent(BaseEvent):
            event_id = "test_high"
            trigger = EventTrigger.MILESTONE
            priority = 50
            exclusive = True
            def can_trigger(self, w, c, target=None, **kw): return True
            def execute(self, w, c, target=None, **kw):
                c.say("HIGH")
                return True

        triggered = world.event_manager.trigger(EventTrigger.MILESTONE, ctx, target=laffey)
        assert len(triggered) == 1
        assert triggered[0].event_id == "test_high"
        assert "HIGH" in ctx.result()[0]
        assert world.event_manager.has_triggered("test_high", laffey.id)

    def test_once_event_does_not_repeat(self, world):
        ctx = CommandContext(world)
        laffey = world.npc_manager.get_npc_by_id('laffey')

        @register_event
        class OnceEvent(BaseEvent):
            event_id = "test_once"
            trigger = EventTrigger.DAY_START
            priority = 10
            exclusive = False
            once = True
            def can_trigger(self, w, c, target=None, **kw): return True
            def execute(self, w, c, target=None, **kw):
                c.say("ONCE")
                return True

        t1 = world.event_manager.trigger(EventTrigger.DAY_START, ctx, target=laffey)
        assert len(t1) == 1
        assert world.event_manager.has_triggered("test_once", laffey.id)

        # 第二次触发应被过滤
        ctx2 = CommandContext(world)
        t2 = world.event_manager.trigger(EventTrigger.DAY_START, ctx2, target=laffey)
        assert len(t2) == 0


class TestDateEndEvents:
    """测试约会结束各分支事件判定与执行效果"""

    def test_date_end_kiss_event(self, world):
        ctx = CommandContext(world)
        laffey = world.npc_manager.get_npc_by_id('laffey')
        laffey.set_talent('no_kiss_exp', 1)
        laffey.set_talent('relationship', '2')  # 喜欢
        laffey.abl['intimacy_abl'] = 10
        laffey.favor = 500
        laffey.base['emotion'] = 500
        laffey.cflag['kissed_date_end'] = False

        # 低分不触发初吻，兜底触发通常道别
        t_low = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx, target=laffey, score=100
        )
        assert len(t_low) == 1
        assert isinstance(t_low[0], DateEndNormalEvent)
        assert laffey.has_talent('no_kiss_exp')

        # 高分达标触发初吻
        ctx2 = CommandContext(world)
        t_high = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx2, target=laffey, score=250
        )
        assert len(t_high) == 1
        assert isinstance(t_high[0], DateEndKissEvent)
        assert not laffey.has_talent('no_kiss_exp')
        assert laffey.exp['kiss_exp'] >= 1
        assert laffey.exp['love_exp'] >= 10
        assert world.player.exp['kiss_exp'] >= 1

    def test_date_end_disappointment_clear_event(self, world):
        ctx = CommandContext(world)
        z23 = world.npc_manager.get_npc_by_id('Z23')
        z23.mark['disappointment_mark'] = 1
        # 非初吻，避免初吻抢占
        z23.talent['kiss_virgin'] = 0
        z23.exp['kiss_exp'] = 5

        t = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx, target=z23, score=200
        )
        assert len(t) == 1
        assert isinstance(t[0], DateEndDisappointmentClearEvent)
        assert z23.mark['disappointment_mark'] == 0

    def test_date_end_confess_event(self, world):
        ctx = CommandContext(world)
        javelin = world.npc_manager.get_npc_by_id('javelin')
        # 满足触发条件：初吻已完成（no_kiss_exp）、非恋人
        javelin.set_talent('no_kiss_exp', 1)
        javelin.talent.pop('lover', None)

        t = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx, target=javelin, score=550
        )
        assert len(t) == 1
        assert isinstance(t[0], DateEndConfessEvent)
        # 此时挂起了选择
        assert world.event_manager.pending_choice is not None
        assert world.event_manager.pending_choice.event_id == "date_end_confess"
        assert len(world.event_manager.pending_choice.options) == 2

        # 分支 A：接受告白
        res_accept = world.event_manager.choose_option("accept")
        assert isinstance(res_accept, list)
        assert javelin.has_talent('lover')
        assert javelin.exp.get('love_exp', 0) >= 20

    def test_date_end_confess_reject(self, world):
        ctx = CommandContext(world)
        javelin = world.npc_manager.get_npc_by_id('javelin')
        javelin.set_talent('no_kiss_exp', 1)
        javelin.talent.pop('lover', None)
        javelin.trust = 100

        t = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx, target=javelin, score=550
        )
        assert len(t) == 1
        assert world.event_manager.pending_choice is not None

        # 分支 B：拒绝告白
        res_reject = world.event_manager.choose_option("reject")
        assert isinstance(res_reject, list)
        assert not javelin.has_talent('lover')
        assert javelin.trust == 80

    def test_date_end_normal_event_tiers(self, world):
        ayanami = world.npc_manager.get_npc_by_id('ayanami')
        ayanami.talent['kiss_virgin'] = 0
        ayanami.exp['kiss_exp'] = 5
        ayanami.talent['lover'] = 1  # 已经是恋人，不告白

        # 高分档
        ctx = CommandContext(world)
        t1 = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx, target=ayanami, score=360
        )
        assert isinstance(t1[0], DateEndNormalEvent)
        assert any("心满意足" in msg for msg in ctx.messages)

        # 超时档
        ctx_to = CommandContext(world)
        t2 = world.event_manager.trigger(
            EventTrigger.DATE_END, ctx_to, target=ayanami, score=200, time_out=True
        )
        assert isinstance(t2[0], DateEndNormalEvent)
        assert any("时间已经这么晚了" in msg for msg in ctx_to.messages)


class TestEndDateCommandIntegration:
    """测试 end_date 指令完整调用与事件集成"""

    def test_end_date_command_flow(self, world):
        laffey = world.npc_manager.get_npc_by_id('laffey')
        laffey.location = world.player.location.copy()
        laffey.cflag['dating'] = True
        world.player.cflag['dating'] = True
        laffey.cflag['dating_following'] = True
        laffey.set_talent('no_kiss_exp', 1)
        laffey.set_talent('relationship', '2')
        laffey.favor = 500
        laffey.abl['intimacy_abl'] = 10
        laffey.exp['date_exp'] = 100
        laffey.exp['love_exp'] = 100
        laffey.base['emotion'] = 500
        laffey.base['rationality'] = 200

        result = world.command_manager.do_cmd('end_date', 'laffey')
        assert isinstance(result, list)
        # 约会状态已解除
        assert laffey.cflag['dating'] is False
        assert world.player.cflag['dating'] is False
        assert laffey.cflag['dating_following'] is False
        # 事件已记录
        assert world.event_manager.has_triggered('date_end_kiss', laffey.id)


class TestEventSaveLoad:
    """测试事件管理器状态的存档与读档"""

    def test_event_history_serialization(self, world, tmp_path):
        world.save_manager.sav_dir = tmp_path
        world.event_manager.record_event('date_end_kiss', 'laffey')
        world.event_manager.record_event('milestone_oath', 'Z23')

        data = world.save_manager.serialize_world()
        assert 'events' in data['data']
        assert 'date_end_kiss:laffey' in data['data']['events']['history']
        assert 'milestone_oath:Z23' in data['data']['events']['history']

        # 读档到新 World
        new_world = World()
        new_world.menu_active = False
        new_world.save_manager.sav_dir = tmp_path
        err = new_world.save_manager.deserialize_world(data)
        assert err is None
        assert new_world.event_manager.has_triggered('date_end_kiss', 'laffey')
        assert new_world.event_manager.has_triggered('milestone_oath', 'Z23')
