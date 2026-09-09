from __future__ import annotations
from typing import TYPE_CHECKING, Any

from data.time.time_data import LEAVE_TIME_DATA
from game_engine.events._base import ChoiceOption
from game_engine.models.movement import MovementSession
from game_engine.utils.text_color import c_chara, c_loc

if TYPE_CHECKING:
    from world import World
    from game_engine.models.shipgirl import ShipGirl


class MovementManager:
    """移动管理器：统一驱动区域内逐点步进与跨区域三阶段离开流水线"""

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

    def _build_steps(self, region: str, path_nodes: list[str]) -> list[dict]:
        """将 find_path 返回的节点列表转换为带耗时的单步队列"""
        steps: list[dict] = []
        if not path_nodes or len(path_nodes) < 2:
            return steps

        region_map = self.world.map_manager.maps.get(region, {})
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            # links 为单字典模式 {目标: 耗时}，O(1) 取边耗时
            time_cost = region_map.get(u, {}).get("links", {}).get(v, 1)
            steps.append({
                "region": region,
                "node": v,
                "time": time_cost,
            })
        return steps

    def start_local_move(self, target_node: str) -> list[str]:
        """发起区域内移动"""
        player = self.world.player
        region = player.location["region"]
        cur_node = player.location["node"]

        if cur_node == target_node:
            return ["已经在该地点"]

        try:
            steps = self.world.map_manager.find_path(region, cur_node, region, target_node)
        except KeyError:
            return ["无法前往该地点"]
        if not steps:
            return ["无法前往该地点"]

        dst_name = self.world.map_manager.get_node_name(region, target_node)
        self.session = MovementSession(
            is_cross_region=False,
            phase=1,
            src_region=region,
            dst_region=region,
            dst_node=target_node,
            dst_name=dst_name,
            remaining_steps=steps,
            rush_to_end=False,
            accumulated_msgs=[],
        )
        return self.process_movement()

    def start_leave(self, target_region: str) -> list[str]:
        """发起跨区域离开（三段式复合流水线）"""
        player = self.world.player
        src_region = player.location["region"]
        cur_node = player.location["node"]

        if target_region == src_region:
            return ["已经在该区域"]

        if target_region not in LEAVE_TIME_DATA.get(src_region, {}):
            return ["无法前往该区域"]

        src_entry_node = self.world.map_manager.regions[src_region]["entry_node"]
        dst_entry_node = self.world.map_manager.regions[target_region]["entry_node"]

        steps: list[dict] = []
        if cur_node != src_entry_node:
            try:
                steps = self.world.map_manager.find_path(src_region, cur_node, src_region, src_entry_node)
            except KeyError:
                steps = []

        dst_name = self.world.map_manager.get_node_name(target_region, dst_entry_node)
        self.session = MovementSession(
            is_cross_region=True,
            phase=1,
            src_region=src_region,
            dst_region=target_region,
            dst_node=dst_entry_node,
            dst_name=dst_name,
            remaining_steps=steps,
            rush_to_end=False,
            accumulated_msgs=[],
        )
        return self.process_movement()

    def process_movement(self) -> list[str]:
        """推进移动会话步进核心状态机"""
        while self.session and self.session.remaining_steps:
            step = self.session.remaining_steps.pop(0)

            # 更新玩家位置
            self.world.player.location["region"] = step["region"]
            self.world.player.location["node"] = step["node"]

            # 推进单步时间并调度 NPC
            step_time = step.get("time", 1)
            self.world.time_manager.advance_time(step_time)
            self.world.npc_manager.update_positions(
                step_time, self.world.map_manager, self.world.player
            )

            # 若仍处于途中（同区域中继点，或跨区域出境步进阶段），检查是否触发偶遇中断
            is_transit = self.session.is_cross_region or bool(self.session.remaining_steps)

            if is_transit:
                npcs = [
                    sg
                    for sg in self.world.npc_manager.get_npcs_at(step["region"], step["node"])
                    if self._is_available_for_encounter(sg)
                ]

                if npcs and not self.session.rush_to_end:
                    # 挂起三选项拦截决策
                    node_name = self.world.map_manager.get_node_name(step["region"], step["node"])
                    names_str = "、".join([c_chara(sg.name, sg.color) for sg in npcs])
                    title = f"在【{c_loc(node_name)}】遇到了 {names_str}，是否停下？"
                    options = [
                        ChoiceOption(key="greet_and_continue", text="打个招呼继续"),
                        ChoiceOption(key="stop", text="停下"),
                        ChoiceOption(key="continue_to_end", text="继续直到目的地"),
                    ]
                    self.world.event_manager.set_pending_choice(
                        event_id="movement_encounter",
                        title=title,
                        options=options,
                        extra_data={
                            "region": step["region"],
                            "node": step["node"],
                            "npc_ids": [sg.id for sg in npcs],
                        },
                    )
                    # 挂起中断，返回空列表以便前端唤起选项幕
                    return []

        if not self.session:
            return []

        # 所有步数消耗完毕
        if self.session.is_cross_region and self.session.phase == 1:
            # 阶段一（出境程）顺利到达出入口，转入阶段二（大地图通勤程）
            self.session.phase = 2
            commute_minutes = LEAVE_TIME_DATA[self.session.src_region][self.session.dst_region]
            self.world.time_manager.advance_time(commute_minutes)
            self.world.npc_manager.update_positions(
                commute_minutes, self.world.map_manager, self.world.player
            )

            src_name = self.world.map_manager.get_region_name(self.session.src_region)
            dst_name = self.world.map_manager.get_region_name(self.session.dst_region)
            self.session.accumulated_msgs.append(f"离开了{src_name}……")
            self.session.accumulated_msgs.append(f"经过约 {commute_minutes} 分钟的路程，前往了{dst_name}。")

            # 转入阶段三（入境程）：降落至目标区域 entry_node
            self.session.phase = 3
            self.world.player.location["region"] = self.session.dst_region
            self.world.player.location["node"] = self.session.dst_node

            # 抵达事件与迎面偶遇检测
            arrival_events = self.world.advance_time_with_events(0, player_move=True)
            dst_node_name = self.world.map_manager.get_node_name(
                self.session.dst_region, self.session.dst_node
            )
            final_msgs = list(self.session.accumulated_msgs)
            final_msgs.append(f"来到了{dst_name}的{dst_node_name}。")
            final_msgs.extend(arrival_events)

            self.session = None
            return final_msgs

        # 同区域移动终点抵达
        arrival_events = self.world.advance_time_with_events(0, player_move=True)
        final_msgs = list(self.session.accumulated_msgs)
        final_msgs.extend(arrival_events)
        self.session = None
        return final_msgs

    def handle_choice(self, option_key: str) -> list[str]:
        """处理玩家在偶遇选项幕中作出的决策"""
        if not self.session:
            return []

        cur_region = self.world.player.location["region"]
        cur_node = self.world.player.location["node"]
        node_name = self.world.map_manager.get_node_name(cur_region, cur_node)
        npcs = [
            sg
            for sg in self.world.npc_manager.get_npcs_at(cur_region, cur_node)
            if self._is_available_for_encounter(sg)
        ]

        if option_key == "greet_and_continue":
            if npcs:
                names = "、".join([sg.name for sg in npcs])
                self.session.accumulated_msgs.append(f"在【{node_name}】向{names}打了招呼。")
                for sg in npcs:
                    if not sg.cflag.get("have_encountered", False):
                        sg.cflag["have_encountered"] = True
                        self.session.accumulated_msgs.append(f"第一次遇到{sg.name}。")
                        self.session.accumulated_msgs.append(
                            f"将{c_chara(sg.name, sg.color)}加入到了通讯录中。"
                        )
            return self.process_movement()

        elif option_key == "stop":
            # 中止行程，停留在当前中继节点
            if self.session.is_cross_region:
                stop_msg = f"取消了离开，停留在【{node_name}】。"
            else:
                stop_msg = f"停下了脚步，停留在【{node_name}】。"

            # 停驻后触发当前房间在场 NPC 的抵达感知
            arrival_events = self.world.advance_time_with_events(0, player_move=True)
            final_msgs = list(self.session.accumulated_msgs) + [stop_msg] + arrival_events
            self.session = None
            self.world.event_manager.pending_choice = None
            return final_msgs

        elif option_key == "continue_to_end":
            self.session.rush_to_end = True
            if npcs:
                names = "、".join([sg.name for sg in npcs])
                self.session.accumulated_msgs.append(
                    f"在【{node_name}】向{names}打了招呼，快步走向目的地。"
                )
                for sg in npcs:
                    if not sg.cflag.get("have_encountered", False):
                        sg.cflag["have_encountered"] = True
                        self.session.accumulated_msgs.append(f"第一次遇到{sg.name}。")
                        self.session.accumulated_msgs.append(
                            f"将{c_chara(sg.name, sg.color)}加入到了通讯录中。"
                        )
            return self.process_movement()

        return []

    def serialize(self) -> dict | None:
        return self.session.to_dict() if self.session else None

    def deserialize(self, data: dict | None):
        self.session = MovementSession.from_dict(data)
