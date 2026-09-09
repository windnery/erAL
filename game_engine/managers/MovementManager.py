from __future__ import annotations

from typing import TYPE_CHECKING

from data.time.time_data import LEAVE_TIME_DATA
from game_engine.events._enums import EventTrigger
from game_engine.models.movement import MovementSession
from game_engine.utils.text_color import c_chara

if TYPE_CHECKING:
    from game_engine.models.shipgirl import ShipGirl
    from world import World


class MovementManager:
    """移动管理器：统一驱动玩家逐点步进与事件化拦截"""

    def __init__(self, world: World):
        self.world = world
        self.session: MovementSession | None = None

    def _is_available_for_encounter(self, sg: ShipGirl) -> bool:
        """检查舰娘是否可触发沿途偶遇中断（排除跟随中、睡眠中、失去意识状态）"""
        return (
            not sg.is_following()
            and not sg.is_sleeping()
            and not sg.cflag.get("unconscious", False)
        )

    def start_move(self, target_region: str, target_node: str) -> list[str]:
        """统一发起移动（自动适配同区域房间步进与跨区域通勤）"""
        player = self.world.player
        cur_region = player.location["region"]
        cur_node = player.location["node"]

        if (cur_region, cur_node) == (target_region, target_node):
            return ["已经在该地点"]
        steps = self.world.map_manager.find_path(
            cur_region, cur_node, target_region, target_node
        )

        dst_name = self.world.map_manager.get_node_name(target_region, target_node)
        is_cross = cur_region != target_region

        self.session = MovementSession(
            is_cross_region=is_cross,
            dst_region=target_region,
            dst_node=target_node,
            dst_name=dst_name,
            remaining_steps=steps,
            rush_to_end=False,
            accumulated_msgs=[],
        )
        return self.process_movement()

    def start_local_move(self, target_node: str) -> list[str]:
        """发起区域内移动"""
        region = self.world.player.location["region"]
        return self.start_move(region, target_node)

    def start_leave(self, target_region: str) -> list[str]:
        """发起跨区域离开"""
        dst_entry_node = self.world.map_manager.regions[target_region]["entry_node"]
        return self.start_move(target_region, dst_entry_node)

    def process_movement(self) -> list[str]:
        """推进移动会话步进核心循环"""
        while self.session and self.session.remaining_steps:
            step = self.session.remaining_steps.pop(0)

            # 更新玩家位置
            self.world.player.location["region"] = step["region"]
            self.world.player.location["node"] = step["node"]

            # 推进单步时间并调度 NPC
            step_time = step.get("time", 1)
            self.world.time_manager.advance_time(step_time)
            step_msgs = self.world.npc_manager.update_positions(
                step_time, self.world.map_manager, self.world.player
            )
            if step_msgs:
                self.session.accumulated_msgs.extend(step_msgs)

            # 触发 MOVE_ENTER 事件（委托事件管理器处理在途拦截）
            from game_engine.commands._context import CommandContext

            ctx = CommandContext(self.world)
            self.world.event_manager.trigger(EventTrigger.MOVE_ENTER, ctx)

            # 若有事件挂起了选项且未开启免打扰直达，中断步进并返回空列表（等待前端弹窗）
            if self.world.event_manager.pending_choice and not self.session.rush_to_end:
                return []

        if not self.session:
            return []

        # 所有步数消耗完毕：到达目的地
        final_msgs = list(self.session.accumulated_msgs)
        dst_name = self.session.dst_name or self.world.map_manager.get_node_name(
            self.session.dst_region, self.session.dst_node
        )
        final_msgs.append(f"来到了【{dst_name}】。")

        # 抵达事件与在场 NPC 感知
        arrival_events = self.world.advance_time_with_events(0, player_move=True)
        final_msgs.extend(arrival_events)

        self.session = None
        return final_msgs

    def handle_choice(self, option_key: str) -> list[str]:
        """处理玩家在偶遇选项幕中作出的决策"""
        if not self.session:
            return []

        cur_region = self.world.player.location["region"]
        cur_node = self.world.player.location["node"]
        npcs = [
            sg
            for sg in self.world.npc_manager.get_npcs_at(cur_region, cur_node)
            if self._is_available_for_encounter(sg)
        ]

        if option_key == "greet_and_continue":
            if npcs:
                names = "、".join([sg.name for sg in npcs])
                self.session.accumulated_msgs.append(
                    f"向{names}打了声招呼后继续前进。"
                )
            return self.process_movement()

        elif option_key == "stop":
            # 中止行程，停留在当前中继节点

            # 停驻后触发当前房间在场 NPC 的抵达感知
            arrival_events = self.world.advance_time_with_events(0, player_move=True)
            final_msgs = (
                list(self.session.accumulated_msgs) + arrival_events
            )
            self.session = None
            self.world.event_manager.pending_choice = None
            return final_msgs

        elif option_key == "continue_to_end":
            self.session.rush_to_end = True
            return self.process_movement()

        return []

    def serialize(self) -> dict | None:
        return self.session.to_dict() if self.session else None

    def deserialize(self, data: dict | None):
        self.session = MovementSession.from_dict(data)
