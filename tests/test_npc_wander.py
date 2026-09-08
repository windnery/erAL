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

    def _call(self, elapsed):
        """重置为双自由后调用 update_positions（上一次 tick 的 roll 会污染暂存活动）"""
        self.world.activity_manager.will_activities["Z23"] = "free"
        self.world.activity_manager.reset_activity("Z23")
        self.nm.update_positions(elapsed, self.world.map_manager, self.world.player)

    # ==================== set_loc 打断 ====================

    def test_set_loc_clears_move_state(self):
        """set_loc（睡觉/工作/跟随接管）必须清空全部在途状态"""
        self.z23.move_path = ["corridor"]
        self.z23.to_region = "home"
        self.z23.next_node_time = 7
        self.nm.set_loc("Z23", DORM, ENTRY)
        assert self.z23.move_path == []
        assert self.z23.to_region == ""
        assert self.z23.next_node_time == 0

    # ==================== 同区域移动 ====================

    def test_same_region_move_arrives(self, monkeypatch):
        """同区移动：时间充足一步到达，状态清空"""
        self._patch_random(monkeypatch, [1])
        self.nm.set_loc("Z23", DORM, "laffey_room")
        self._call(10)
        assert self.z23.location == {"region": DORM, "node": "corridor"}
        assert self.z23.move_path == []
        assert self.z23.next_node_time == 0


    def test_same_region_inflight_walks_partway_then_arrives(self, monkeypatch):
        """同区在途：走不完停在原地只扣时间，下一 tick 续走直到到达"""
        # 两 tick 首掷都成功（队列值用尽后 randint 恒返回 1）
        self._patch_random(monkeypatch, [1])
        self.nm.set_loc("Z23", DORM, "laffey_room")
        # 人为构造在途状态：还剩 corridor -> oklahoma_room 两步，到下一节点还差 5 分钟
        self.z23.move_path = ["corridor", "oklahoma_room"]
        self.z23.next_node_time = 5

        self._call(3)
        assert self.z23.location == {"region": DORM, "node": "laffey_room"}
        assert self.z23.move_path == ["corridor", "oklahoma_room"]
        assert self.z23.next_node_time == 2

        self._call(10)
        assert self.z23.location == {"region": DORM, "node": "oklahoma_room"}
        assert self.z23.move_path == []
        assert self.z23.next_node_time == 0

    def test_same_region_inflight_at_entry_not_corrupted(self, monkeypatch):
        """回归（region 空串污染）：同区在途且恰好位于 entry_node，
        首掷失败二掷成功进入跨区分支时，不得动 region"""
        self._patch_random(monkeypatch, [100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)  # 在途且站在 entry_node
        self.z23.move_path = ["oklahoma_room"]
        self.z23.next_node_time = 5

        self._call(3)
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.move_path == ["oklahoma_room"]
        assert self.z23.next_node_time == 5

    # ==================== 跨区域移动 ====================

    def test_cross_region_move_arrives(self, monkeypatch):
        """跨区移动：时间充足时到达目标区入口，region/to_region/路径全部正确"""
        # 首掷失败 + 二掷成功 → 进入跨区分支；choice 取第一个候选区域 = home
        self._patch_random(monkeypatch, [100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)
        self._call(10)  # commute=3，一步到达
        assert self.z23.location == {"region": "home", "node": "living_room"}
        assert self.z23.to_region == ""
        assert self.z23.move_path == []
        assert self.z23.next_node_time == 0

    def test_cross_region_inflight_counts_down_then_arrives(self, monkeypatch):
        """回归（跨区在途永久冻结）：走不完时倒计时留存，下一 tick 续走并落地"""
        self._patch_random(monkeypatch, [100, 1, 100, 1])
        self.nm.set_loc("Z23", DORM, ENTRY)

        self._call(1)  # 开启跨区移动但走不完
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.to_region == "home"
        assert self.z23.move_path == ["living_room"]
        assert self.z23.next_node_time == COMMUTE - 1

        self._call(10)  # 时间充足，到达
        assert self.z23.location == {"region": "home", "node": "living_room"}
        assert self.z23.to_region == ""
        assert self.z23.move_path == []
        assert self.z23.next_node_time == 0

    def test_cross_region_inflight_not_consumed_by_same_region_branch(self, monkeypatch):
        """回归（同区 while 消费跨区路径）：跨区在途 + 首掷成功进入同区分支时，
        在途状态必须原样保留，不得出现旧 region + 新 region 节点的非法位置"""
        self._patch_random(monkeypatch, [100, 1, 1])  # tick1 开启跨区；tick2 首掷成功
        self.nm.set_loc("Z23", DORM, ENTRY)

        self._call(1)  # 进入跨区在途，剩 2 分钟
        self._call(10)  # 首掷成功：while 被 to_region 拦下，本 tick 停滞但状态完好
        assert self.z23.location == {"region": DORM, "node": ENTRY}
        assert self.z23.to_region == "home"
        assert self.z23.move_path == ["living_room"]
        assert self.z23.next_node_time == COMMUTE - 1
