# -*- coding: utf-8 -*-
"""NPC 自由行动移动（wander）逻辑测试

覆盖在途状态（move_path / to_region / next_node_time）的推进、续走与打断：
- 同区域移动：一步到达 / 走一半停下续走
- 跨区域移动：倒计时续走 / 到达后切换 region / 在途不被同区分支破坏
- set_loc 打断清空移动状态
- 回归：同区在途经过 entry_node 时不得污染 region
"""

from __future__ import annotations

import pytest

import game_engine.managers.NpcManager as npc_mod
from data.time.time_data import LEAVE_TIME_DATA

DORM = "eagle_union_dorm"
ENTRY = "corridor"  # regions[DORM]["entry_node"]
COMMUTE = LEAVE_TIME_DATA[DORM]["home"]  # = 3


class TestNpcWander:
    @pytest.fixture(autouse=True)
    def _setup(self, world):
        self.world = world
        self.nm = world.npc_manager
        self.z23 = self.nm.shipgirls["Z23"]
        # 只让 Z23 参与调度，避免其他舰娘消耗随机数序列、干扰断言
        # （类属性 NpcManager.shipgirls 仍指向完整 dict，activity tick 不受影响）
        self.nm.shipgirls = {"Z23": self.z23}
        # 清掉 NOT_MAPPING["free"] 涉及的全部状态，保证 Z23 处于双自由
        self.nm.secretary_ship = None
        for key in (
            "secretary_ship", "secretary_ship_following", "dating",
            "dating_following", "working", "sleeping", "resting", "following",
        ):
            self.z23.cflag[key] = False
        self.z23.schedule["works"] = []
        # 12:00 不在睡觉/工作时段
        world.time_manager.hour = 12
        world.time_manager.minute = 0

    def _patch_random(self, monkeypatch, randint_values=None):
        """固定 NpcManager 内的随机数：randint 依次返回队列值（用尽后返回 1，
        即首掷必成功）；choice 恒取第一个候选（同区 → corridor，跨区 → home）"""
        queue = list(randint_values or [])
        monkeypatch.setattr(npc_mod, "randint", lambda a, b: queue.pop(0) if queue else 1)
        monkeypatch.setattr(npc_mod, "choice", lambda seq: seq[0])

    def _call(self, elapsed, will="free"):
        """重置活动后调用 update_positions（上一次 tick 的 roll 会污染暂存活动）
        will: 非默认时先设置候选活动（模拟 roll_activity 已选中某活动）"""
        self.world.activity_manager.will_activities["Z23"] = will
        self.world.activity_manager.reset_activity("Z23")
        self.nm.update_positions(elapsed, self.world.map_manager, self.world.player)

    # ==================== set_loc 打断 ====================

    def test_set_loc_clears_move_state(self):
        """set_loc（睡觉/工作/跟随接管）必须清空全部在途状态"""
        self.z23.move_steps = [{"region": "home", "node": "corridor", "time": 7}]
        self.nm.set_loc("Z23", DORM, ENTRY)
        assert self.z23.move_steps == []

    # ==================== 同区域移动 ====================

    def test_same_region_move_arrives(self, monkeypatch):
        """同区移动：时间充足一步到达，状态清空"""
        self._patch_random(monkeypatch, [1])
        self.nm.set_loc("Z23", DORM, "laffey_room")
        self._call(10)
        assert self.z23.location == {"region": DORM, "node": "corridor"}
        assert self.z23.move_steps == []

    def test_same_region_inflight_walks_partway_then_arrives(self, monkeypatch):
        """同区在途：走不完停在原地只扣时间，下一 tick 续走直到到达"""
        # 两 tick 首掷都成功（队列值用尽后 randint 恒返回 1）
        self._patch_random(monkeypatch, [1])
        self.nm.set_loc("Z23", DORM, "laffey_room")
        # 人为构造在途状态：还剩 corridor -> oklahoma_room 两步，到下一节点还差 5 分钟
        self.z23.move_steps = [
            {"region": DORM, "node": "corridor", "time": 5},
            {"region": DORM, "node": "oklahoma_room", "time": 1},
        ]

        self._call(3)
        assert self.z23.location == {"region": DORM, "node": "laffey_room"}
        assert self.z23.move_steps[0] == {"region": DORM, "node": "corridor", "time": 2}

        self._call(10)
        assert self.z23.location == {"region": DORM, "node": "oklahoma_room"}
        assert self.z23.move_steps == []

    def test_same_region_inflight_at_entry_not_corrupted(self, monkeypatch):
        """回归（region 空串污染）：同区在途且恰好位于 entry_node，
        即使二掷成功进入跨区分支，也不得动 region/误开始跨区移动"""
        self._patch_random(monkeypatch, [100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)  # 在途且站在 entry_node
        self.z23.move_steps = [{"region": DORM, "node": "oklahoma_room", "time": 5}]

        self._call(3)
        # 推进已提到分支外：首掷失败在途也照样前进（3 < 5，未到下一节点）
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.move_steps == [{"region": DORM, "node": "oklahoma_room", "time": 2}]

    # ==================== 跨区域移动 ====================

    def test_cross_region_move_arrives(self, monkeypatch):
        """跨区移动：时间充足时到达目标区入口，region 与路径全部正确"""
        # 首掷失败 + 二掷成功 → 进入跨区分支；choice 取第一个候选区域 = home
        self._patch_random(monkeypatch, [100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)
        self._call(10)  # commute=3，一步到达
        assert self.z23.location == {"region": "home", "node": "living_room"}
        assert self.z23.move_steps == []

    def test_cross_region_inflight_counts_down_then_arrives(self, monkeypatch):
        """回归（跨区在途永久冻结）：走不完时倒计时留存，下一 tick 续走并落地"""
        self._patch_random(monkeypatch, [100, 1, 100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)

        # elapsed=2：自由移动概率 2%（跨区 1%），开启跨区移动但走不完
        self._call(2)
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.move_steps == [{"region": "home", "node": "living_room", "time": COMMUTE - 2}]

        self._call(10)  # 时间充足，到达
        assert self.z23.location == {"region": "home", "node": "living_room"}
        assert self.z23.move_steps == []

    def test_cross_region_inflight_not_consumed_by_same_region_branch(self, monkeypatch):
        """回归（同区 while 消费跨区路径）：跨区在途 + 首掷成功进入同区分支时，
        统一步进处理正常扣减并正确落地"""
        self._patch_random(monkeypatch, [100, 1, 1])  # tick1 开启跨区；tick2 首掷成功
        self.nm.set_loc("Z23", DORM, ENTRY)

        # elapsed=2：进入跨区在途，剩 1 分钟
        self._call(2)
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.move_steps == [{"region": "home", "node": "living_room", "time": COMMUTE - 2}]

        self._call(10)  # 时间充足正常落地
        assert self.z23.location == {"region": "home", "node": "living_room"}
        assert self.z23.move_steps == []

    # ==================== 候选活动到达激活 ====================

    def test_heading_activity_activates_on_arrival(self, monkeypatch):
        """前往候选活动的舰娘到达合适节点后，同 tick 激活活动"""
        self._patch_random(monkeypatch, [1])  # 首掷必成功（relax 权重路径不掷骰，保险）
        # Z23 在走廊（非 CAN_SIT 节点），候选活动 relax 要求 CAN_SIT 地点
        self.nm.set_loc("Z23", DORM, ENTRY)
        self._call(10, will="relax")
        # 走到第一个 CAN_SIT 节点（laffey_room）并立即激活
        assert self.z23.location == {"region": DORM, "node": "laffey_room"}
        assert self.world.activity_manager.activities["Z23"].id == "relax"
        assert self.world.activity_manager.will_activities["Z23"] == "free"

    def test_pending_activity_not_activated_at_unsuitable_node(self):
        """站在不合适节点时，候选活动不得被就地激活"""
        self.nm.set_loc("Z23", DORM, ENTRY)  # 走廊不是 CAN_SIT 节点
        self._call(0, will="relax")  # elapsed=0：不发生移动与决策
        assert self.world.activity_manager.activities["Z23"].id == "free"
        assert self.world.activity_manager.will_activities["Z23"] == "relax"

    def test_pending_activity_not_activated_while_working(self):
        """working 状态下候选活动不得被激活（否则会被 tick_all 的活动守卫吞掉）"""
        self.z23.schedule["works"] = [{
            "desc": "测试工作",
            "location": {"region": "office", "node": "desk"},
            "time": {"start": [9, 0], "end": [17, 0]},
        }]
        self._call(10, will="relax")  # 12:00 在工作时段内
        assert self.z23.cflag["working"] is True
        assert self.z23.location == {"region": "office", "node": "desk"}
        # 候选活动保留到下班，不被激活也不被吞掉
        assert self.world.activity_manager.activities["Z23"].id == "free"
        assert self.world.activity_manager.will_activities["Z23"] == "relax"
