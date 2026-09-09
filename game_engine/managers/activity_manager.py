from random import choices

import game_engine.activities
from config.cflag_config import NOT_MAPPING
from game_engine.activities.free import Free
from game_engine.managers import ACTIVITY_REGISTRY
from game_engine.managers.MapManager import MapManager
from game_engine.managers.NpcManager import NpcManager
from game_engine.managers.TimeManager import TimeManager
from game_engine.models.activity import Activity
from game_engine.models.player import Player


class ActivityManager:
    """活动管理器类"""

    def __init__(self, time_manager: TimeManager, npc_manager: NpcManager):
        self.activities: dict[str, Activity] = {}  # 存储所有活动实例 {舰娘id:活动实例}
        self.will_activities: dict[
            str, str
        ] = {}  # 存储所有即将开始的活动id {舰娘id:活动id}
        self.time_manager = time_manager
        self.npc_manager = npc_manager
        self.ex_init()

    def ex_init(self):
        # hook: 初始化所有舰娘的活动为自由活动
        for sg in self.npc_manager.get_all_npcs():
            self.activities[sg.id] = Free(
                "free",
                self.time_manager.get_total_minutes(),
            )
            self.will_activities[sg.id] = "free"

    def reset_activity(self, sg_id: str):
        """重置指定舰娘的活动"""
        self.activities[sg_id] = Free(
            "free",
            self.time_manager.get_total_minutes(),
        )

    def reset_will_activity(self, sg_id: str):
        """重置指定舰娘的即将开始的活动"""
        self.will_activities[sg_id] = "free"

    def add_activity(self, sg_id: str, activity_id: str):
        """给指定舰娘添加活动"""
        # 添加暂存活动
        self.will_activities[sg_id] = activity_id

    def activate_activity(self, sg_id: str):
        """激活指定舰娘的暂存活动"""
        mes_lst: list[str] = []
        if self.will_activities[sg_id] != "free":
            # 如果不是自由活动，激活暂存活动
            activity_cls: type[Activity] = ACTIVITY_REGISTRY[self.will_activities[sg_id]]
            activity = activity_cls(
                self.will_activities[sg_id],
                self.time_manager.get_total_minutes(),
            )
            # 调用活动开始钩子
            if MapManager.is_same_loc(self.npc_manager.world.player, self.npc_manager.get_npc_by_id(sg_id)):
                # 只展示和玩家同一地点的活动的开始信息
                mes = activity.on_start(self.npc_manager.get_npc_by_id(sg_id))
                mes_lst.append(mes)
            self.activities[sg_id] = activity
            self.reset_will_activity(sg_id)  # 重置暂存活动为自由活动
        return mes_lst

    def tick_all(self, player: Player, minutes: int):
        """对所有活动进行tick处理"""
        mes_lst: list[str] = []
        for sg_id, activity in self.activities.items():
            if activity is not None:
                sg = NpcManager.get_npc_by_id(sg_id)
                if any(sg.cflag.get(key, False) for key in NOT_MAPPING.get("activity", [])):
                    # 如果舰娘处于不允许活动的状态，直接重置活动
                    self.reset_activity(sg_id)
                    continue
                if MapManager.is_same_loc(player, sg):
                    # 只展示和玩家同一地点的活动的tick信息
                    tick_mes = activity.tick(sg, minutes)
                    if tick_mes:
                        mes_lst.append(tick_mes)
                else:
                    activity.tick(sg, minutes)
            if activity.id != "free" and activity.duration == 0:
                # 活动结束，重置为自由活动
                if MapManager.is_same_loc(player, NpcManager.get_npc_by_id(sg_id)):
                    # 只展示和玩家同一地点的活动的结束信息
                    mes = activity.on_end(NpcManager.get_npc_by_id(sg_id))
                    if mes:
                        mes_lst.append(mes)
                self.reset_activity(sg_id)
        return mes_lst

    def roll_activity(self, sg_id: str):
        """为指定舰娘按权重选择一个活动"""
        # 获取舰娘实例
        sg = NpcManager.get_npc_by_id(sg_id)
        # 计算每个活动的权重
        weights = {
            activity_id: activity_cls.get_weight(sg)
            for activity_id, activity_cls in ACTIVITY_REGISTRY.items()
        }
        # 根据权重随机选择一个活动
        activity_id = choices(list(weights.keys()), weights=list(weights.values()))[0]
        # 添加暂存活动
        self.add_activity(sg_id, activity_id)
