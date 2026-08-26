from __future__ import annotations
from enum import Enum


class EventTrigger(str, Enum):
    """事件触发时机枚举"""
    DATE_END = "date_end"           # 约会结束/归宅时
    DAY_START = "day_start"         # 每日清晨醒来
    DAY_END = "day_end"             # 深夜入睡前
    TURN_END = "turn_end"           # 回合推进
    MOVE_ENTER = "move_enter"       # 进入地图节点时
    TRAIN_END = "train_end"         # 调教结束时
    MILESTONE = "milestone"         # 好感/属性/素质里程碑
