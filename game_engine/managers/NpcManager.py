from __future__ import annotations

from random import choice, randint
from typing import TYPE_CHECKING, Any

from config import map_config
from config.base_config import TALK_FATIGUE_RECOVER_THRESHOLD
from config.cflag_config import EXCEPT_MAPPING, NOT_MAPPING
from config.time_config import DATING_END_TIME, SECRETARY_FOLLOWING_END_TIME
from data.data_loader import load_shipgirls
from game_engine.managers import ACTIVITY_REGISTRY
from game_engine.managers.MapManager import MapManager
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def time_check(hour: int, minute: int, start: list[int], end: list[int]) -> bool:
    """判断当前时间 (hour, minute) 是否在 [start, end) 时段内
    start/end: [时, 分] 列表，如 [8, 30]
    支持：常规时段（8:30-19:30）、同小时时段（9:00-9:30）、跨天时段（22:00-2:00）
    """
    cur = hour * 60 + minute
    s = start[0] * 60 + start[1]
    e = end[0] * 60 + end[1]
    if s <= e:  # 常规或同小时时段：左闭右开 [s, e)
        return s <= cur < e
    else:  # 跨天时段（如 22:00-2:00）：越过午夜
        return cur >= s or cur < e


class NpcManager:
    """NPC管理器类"""

    # 所有舰娘的初始化数据
    shipgirls_db = load_shipgirls()
    # 初始化所有舰娘对象
    shipgirls = {sg_id: ShipGirl(**sg_data) for sg_id, sg_data in shipgirls_db.items()}

    def __init__(self, world: World):
        from copy import deepcopy

        self.shipgirls = {
            sg_id: ShipGirl(**deepcopy(sg_data))
            for sg_id, sg_data in self.shipgirls_db.items()
        }
        NpcManager.shipgirls = self.shipgirls
        # 秘书舰
        self.secretary_ship: ShipGirl | None = None
        self.world = world

    def set_loc(self, shipgirl_id: str, region: str, node: str):
        """设置舰娘位置"""
        self.shipgirls[shipgirl_id].location = {"region": region, "node": node}
        self.shipgirls[shipgirl_id].move_steps = []

    def get_all_npcs(self):
        """获取所有NPC列表"""
        return list(self.shipgirls.values())

    def set_secretary_ship_proc(self, sg_id: str, player: Player):
        """设置秘书舰处理"""
        if self.secretary_ship:
            """当前有秘书舰的情况"""
            # 移除当前秘书舰
            self.secretary_ship.cflag["secretary_ship"] = False
            self.secretary_ship.cflag["secretary_ship_following"] = False

        self.secretary_ship = self.shipgirls[sg_id]
        self.secretary_ship.cflag["secretary_ship"] = True
        self.secretary_ship.cflag_set_attach("secretary_ship")

    def update_positions(
        self, elapsed_minutes: int, map_manager: MapManager, player: Player
    ):
        """根据当前时间和推进时长更新所有舰娘位置
        elapsed_minutes: 本次推进的分钟数（仅用于自由行动时的移动概率）
        map_manager: 地图管理器（用于查询可前往的节点/区域）
        player: 玩家对象（秘书舰/约会舰娘跟随需要）

        当前时间（hour/minute）直接读 self.world.time_manager，不靠参数传入
        """
        hour = self.world.time_manager.hour
        minute = self.world.time_manager.minute
        current = self.world.time_manager.get_total_minutes()
        secretary_end_time = (self.world.time_manager.day - 1) * 24 * 60 + SECRETARY_FOLLOWING_END_TIME

        # 更新秘书舰情况
        if self.secretary_ship:
            self.secretary_ship.cflag["secretary_ship"] = True
            # 设置秘书舰的附属状态
            self.secretary_ship.cflag_set_attach("secretary_ship")
            if (
                self.secretary_ship.is_resting()
                or self.secretary_ship.is_sleeping()
                or current >= secretary_end_time
            ):
                # 秘书舰在休息/睡觉/不在秘书时间时，取消秘书舰同行状态
                self.secretary_ship.cflag["secretary_ship_following"] = False

        for sg in self.shipgirls.values():
            # 情绪&理性&心情自然变化
            sg.emotion_natural_change(elapsed_minutes)
            sg.rationality_natural_change(elapsed_minutes)
            sg.mood_natural_change(elapsed_minutes)

            # 会话疲劳值衰减 1分钟减2点
            sg.talk_fatigue_decay(elapsed_minutes * 2)
            if sg.talk_fatigue < TALK_FATIGUE_RECOVER_THRESHOLD:
                sg.is_talk_fatigue = False

            # 调教状态下忽略所有调度
            if self.world.is_training():
                continue

            # 睡觉时间：回家（睡觉优先级除调教外最高）
            sleep_start_time: list[int] = sg.schedule["sleep"]["start"]
            sleep_end_time: list[int] = sg.schedule["sleep"]["end"]
            if time_check(hour, minute, sleep_start_time, sleep_end_time):
                sleep_region = self.shipgirls_db[sg.id]["location"]["region"]
                sleep_node = self.shipgirls_db[sg.id]["location"]["node"]
                self.set_loc(sg.id, sleep_region, sleep_node)
                # 清除sleeping覆盖掉的cflag
                sg.cflag_clear_except(EXCEPT_MAPPING["sleeping"])
                sg.cflag["sleeping"] = True
                continue
            else:
                sg.cflag["sleeping"] = False

            # 工作时间：去工作地点
            sg.cflag["working"] = False
            if all(sg.cflag.get(key, False) is False for key in NOT_MAPPING["working"]):
                works: list[dict[str, Any]] = sg.schedule.get("works") or []
                for work in works:
                    work_region: str = work["location"]["region"]
                    work_node: str = work["location"]["node"]
                    work_start_time: list[int] = work["time"]["start"]
                    work_end_time: list[int] = work["time"]["end"]
                    if time_check(hour, minute, work_start_time, work_end_time):
                        # 工作时间
                        self.set_loc(sg.id, work_region, work_node)
                        sg.cflag["working"] = True
                        break

            # 睡觉结束后再判断一次秘书舰
            if sg == self.secretary_ship:
                if not sg.is_sleeping() and not sg.is_resting() and current < secretary_end_time:
                    # 秘书舰在秘书时间内且不在休息/睡觉状态时，跟随玩家
                    self.set_loc(sg.id, player.location["region"], player.location["node"])
                    sg.cflag_set_attach("secretary_ship")
                else:
                    sg.cflag["secretary_ship_following"] = False

            # 约会中
            if sg.is_dating():
                # 设置约会的附属状态
                sg.cflag_set_attach("dating")
                # 判断约会是否已到期
                dating_day = sg.cflag.get("dating_day")
                if dating_day is None:
                    dating_day = self.world.time_manager.day
                end_time = (dating_day - 1) * 24 * 60 + DATING_END_TIME
                if current >= end_time:
                    # 取消约会状态
                    from game_engine.commands.interact.end_date import end_date

                    end_date(self.world, sg.id, True)

            if sg.is_following() and not sg.is_sleeping() and not sg.is_resting():
                # 同行中(且不在休息/睡觉)
                self.set_loc(sg.id, player.location["region"], player.location["node"])

            if elapsed_minutes > 0 and all(
                sg.cflag.get(key, False) is False for key in NOT_MAPPING["free"]
            ):
                # 自由行动中
                will_activity = self.world.activity_manager.will_activities[sg.id]
                activity = self.world.activity_manager.activities[sg.id]
                # 决定舰娘的活动
                if will_activity == "free" and activity.id == "free":
                    # 现在和候选都是自由
                    # 随机选取一个地点移动 elapsed_minutes当做移动的概率
                    move_ratio = max(50, elapsed_minutes)
                    if randint(1, 100) <= move_ratio:
                        # ========== 同区域移动 ==========
                        if not sg.move_steps:
                            # 随机选取一个同区域的节点
                            nodes = list(
                                self.world.map_manager.maps[
                                    sg.location["region"]
                                ].keys()
                            )
                            if sg.location["node"] in nodes:
                                nodes.remove(
                                    sg.location["node"]
                                )  # 移除当前节点，避免原地移动
                            if nodes:
                                target_node = choice(nodes)  # 随机选择一个目标节点
                                sg.move_steps = self.world.map_manager.find_path(
                                    sg.location["region"],
                                    sg.location["node"],
                                    sg.location["region"],
                                    target_node,
                                )

                    elif (
                        # 跨区域移动的概率减半
                        randint(1, 100) <= move_ratio // 2
                        and not sg.move_steps
                    ):
                        # ========== 跨区域移动 ==========
                        # 随机选取一个跨区域的节点
                        regions = list(self.world.map_manager.regions.keys())
                        if sg.location["region"] in regions:
                            regions.remove(sg.location["region"])
                        if regions:
                            target_region = choice(regions)
                            target_node = self.world.map_manager.regions[target_region][
                                "entry_node"
                            ]
                            sg.move_steps = self.world.map_manager.find_path(
                                sg.location["region"],
                                sg.location["node"],
                                target_region,
                                target_node,
                            )

                    if not sg.move_steps:
                        # 双自由且不在移动 -> roll候选活动
                        self.world.activity_manager.roll_activity(sg.id)

                elif will_activity != "free" and activity.id == "free":
                    # 现在是自由 候选不是自由 前往候选活动的地点
                    # 活动的地点标签
                    required_loc_tags = ACTIVITY_REGISTRY[will_activity].loc_tags
                    # 优先选择当前区域的合适节点
                    for tag in required_loc_tags:
                        loc_dict: dict[str, list[str]] = getattr(map_config, tag)
                        if loc_dict.get(sg.location["region"], []):
                            # 当前区域有合适节点，选一个最近的
                            available_nodes = loc_dict[sg.location["region"]]
                            if sg.location["node"] in available_nodes:
                                # 当前节点已经是合适节点，无需移动，直接开始活动
                                self.world.activity_manager.activate_activity(sg.id)
                                break
                            else:
                                # 当前节点不是合适节点，移动到一个合适节点
                                target_node = choice(available_nodes)
                                sg.move_steps = self.world.map_manager.find_path(
                                    sg.location["region"],
                                    sg.location["node"],
                                    sg.location["region"],
                                    target_node,
                                )
                                break
                        else:
                            # TODO: 当前区域没有合适节点，尝试去其他区域
                            # 该功能暂时不做 区域没有合适节点直接重置该活动
                            self.world.activity_manager.reset_activity(sg.id)
                            break
                else:
                    # 现在不是自由活动 不打断当前活动
                    pass

            # 处理舰娘移动逻辑（统一被动时间消耗）
            temp_time = elapsed_minutes
            while temp_time > 0 and sg.move_steps:
                step = sg.move_steps[0]
                if temp_time >= step["time"]:
                    # 到达下一节点
                    temp_time -= step["time"]
                    sg.location["region"] = step["region"]
                    sg.location["node"] = step["node"]
                    sg.move_steps.pop(0)
                else:
                    # 尚未到达下一节点，扣减单步耗时，物理位置仍留在原节点
                    step["time"] -= temp_time
                    temp_time = 0

            # 移动结束后：有候选活动且已到达合适地点 -> 激活
            will_id = self.world.activity_manager.will_activities[sg.id]
            if (
                will_id != "free"
                and not sg.move_steps
                and all(
                    sg.cflag.get(key, False) is False for key in NOT_MAPPING["free"]
                )
            ):
                loc_tags = ACTIVITY_REGISTRY[will_id].loc_tags
                if any(
                    sg.location["node"]
                    in getattr(map_config, tag).get(sg.location["region"], [])
                    for tag in loc_tags
                ):
                    self.world.activity_manager.activate_activity(sg.id)

        mes_lst = self.world.activity_manager.tick_all(player, elapsed_minutes)
        # TODO: 前端显示活动的tick信息

    @staticmethod
    def get_npcs_at(region: str, node: str):
        """获取指定位置的NPC列表"""
        return [
            sg
            for sg in NpcManager.shipgirls.values()
            if sg.location["region"] == region and sg.location["node"] == node
        ]

    @staticmethod
    def get_npc_by_id(shipgirl_id: str):
        """根据舰娘ID获取舰娘对象
        shipgirl_id: 舰娘ID
        return: ShipGirl对象
        """
        return NpcManager.shipgirls[shipgirl_id]

    @staticmethod
    def with_mob(region: str, node: str) -> bool:
        """判断是否有旁人在场"""
        return len(NpcManager.get_npcs_at(region, node)) > 1
