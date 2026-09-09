# -*- coding: utf-8 -*-
"""舰娘活动前端显示与消息管线测试

覆盖：
1. world.get_state() 下发 nearby_npcs 的 activity_desc 属性
2. update_positions() 返回同地点舰娘的活动消息（tick 与生命周期）
3. 0 分钟时不产生无效 tick 消息，空串完全过滤
4. TimeManager.advance_time_with_events() 合并活动消息
5. CommandContext.advance_time() 与 result() 全屏消息包含活动消息
"""

from __future__ import annotations

import pytest
from game_engine.activities.relax import Relax
from game_engine.commands._context import CommandContext


class TestActivityDisplay:
    @pytest.fixture(autouse=True)
    def _setup(self, world):
        self.world = world
        self.nm = world.npc_manager
        self.player = world.player
        self.z23 = self.nm.shipgirls["Z23"]
        # 将玩家与 Z23 放置在同一地点（如 home, living_room）
        self.player.location = {"region": "home", "node": "living_room"}
        self.nm.set_loc("Z23", "home", "living_room")
        # 清除干扰状态
        for key in (
            "secretary_ship", "secretary_ship_following", "dating",
            "dating_following", "working", "sleeping", "resting", "following",
        ):
            self.z23.cflag[key] = False

    def test_get_state_activity_desc(self):
        """get_state 包含 nearby_npcs 的 activity_desc 属性"""
        # 默认自由活动：描述为空
        st = self.world.get_state()
        z23_data = next(n for n in st["nearby_npcs"] if n["id"] == "Z23")
        assert z23_data["activity_desc"] == ""

        # 设置为 relax 活动：描述为 'Z23 正在放松'
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        self.world.activity_manager.activities["Z23"] = relax_act
        st2 = self.world.get_state()
        z23_data2 = next(n for n in st2["nearby_npcs"] if n["id"] == "Z23")
        assert z23_data2["activity_desc"] == "Z23 正在放松"

    def test_update_positions_returns_tick_messages_same_loc(self):
        """与玩家同地点且 minutes > 0 时，update_positions 返回有效 tick 消息"""
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        self.world.activity_manager.activities["Z23"] = relax_act

        msgs = self.nm.update_positions(10, self.world.map_manager, self.player)
        assert any("Z23 正在放松" in m and "体力+" in m for m in msgs)

    def test_update_positions_zero_minutes_no_messages(self):
        """minutes == 0 时不产生无效 tick 消息"""
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        self.world.activity_manager.activities["Z23"] = relax_act

        msgs = self.nm.update_positions(0, self.world.map_manager, self.player)
        assert msgs == []

    def test_update_positions_different_loc_no_messages(self):
        """舰娘在其他地点时，虽然 tick 推进恢复，但不向玩家展示消息"""
        self.nm.set_loc("Z23", "eagle_union_dorm", "corridor")
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        relax_act.duration = 50
        self.world.activity_manager.activities["Z23"] = relax_act

        msgs = self.nm.update_positions(10, self.world.map_manager, self.player)
        assert msgs == []
        # 但 Z23 的持续时间正常扣减
        assert relax_act.duration == 40

    def test_advance_time_with_events_includes_activity_messages(self):
        """advance_time_with_events 返回列表中包含活动 tick 消息"""
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        self.world.activity_manager.activities["Z23"] = relax_act

        events = self.world.advance_time_with_events(10)
        assert any("Z23 正在放松" in e for e in events)

    def test_command_context_result_includes_activity_messages(self):
        """CommandContext 在 advance_time 后，result() 包含活动消息"""
        relax_act = Relax("relax", self.world.time_manager.get_total_minutes())
        self.world.activity_manager.activities["Z23"] = relax_act

        ctx = CommandContext(self.world)
        ctx.say("执行了一次测试指令")
        ctx.advance_time(10)
        res = ctx.result()

        assert any("执行了一次测试指令" in line for line in res)
        assert any("Z23 正在放松" in line for line in res)
        assert any("度过了10分钟" in line for line in res)

    def test_activity_lifecycle_messages(self):
        """测试活动激活 on_start 与活动结束 on_end 消息在同地点时的收集"""
        # 1. 激活活动
        self.world.activity_manager.will_activities["Z23"] = "relax"
        start_msgs = self.world.activity_manager.activate_activity("Z23")
        assert any("Z23 准备坐下来放松" in m for m in start_msgs)

        # 2. 将 duration 设为 1，进行 5 分钟 tick，触发 duration <= 0 结束
        act = self.world.activity_manager.activities["Z23"]
        act.duration = 1
        tick_msgs = self.nm.update_positions(5, self.world.map_manager, self.player)
        assert any("Z23 结束了放松" in m for m in tick_msgs)
        # 结束后自动重置为 free
        assert self.world.activity_manager.activities["Z23"].id == "free"
