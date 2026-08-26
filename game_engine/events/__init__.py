from __future__ import annotations

from game_engine.events._enums import EventTrigger
from game_engine.events._base import BaseEvent, register_event, EVENT_REGISTRY
from game_engine.managers.EventManager import EventManager

# 导入所有内置事件子模块以完成自动注册
import game_engine.events.date

__all__ = [
    'EventManager',
    'EventTrigger',
    'BaseEvent',
    'register_event',
    'EVENT_REGISTRY',
]
