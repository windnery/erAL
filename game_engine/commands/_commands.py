from __future__ import annotations
from typing import Any

REGISTER_CMD = {}
REGISTER_CMD_NAME: dict[str, str] = {}
REGISTER_CAN = {}
REGISTER_CAT: dict[str, str] = {}
REGISTER_MODE: dict[str, bool] = {}
REGISTER_NEEDS_TARGET: dict[str, bool] = {}
REGISTER_FRONTEND: dict[str, bool] = {}
REGISTER_CONTINUOUS: dict[str, bool] = {}
REGISTER_CONTINUOUS_TEXT: dict[str, str] = {}
REGISTER_ACTOR_SLOTS: dict[str, dict[str, int]] = {}
REGISTER_TARGET_SLOTS: dict[str, dict[str, int]] = {}
REGISTER_CONTINUOUS_TICK: dict[str, Any] = {}

def register_cmd(
    key: str,
    name: str,
    cat: str,
    train_mode: bool = False,
    can = None,
    needs_target: bool = True,
    frontend: bool = False,
    continuous: bool = False,
    continuous_text: str | None = None,
    actor_slots: dict[str, int] | None = None,
    target_slots: dict[str, int] | None = None,
    continuous_tick = None,
):
    """装饰器：自动把指令注册到字典中
    frontend: 纯前端指令标记，前端直接调用本地回调，不走后端 do_cmd
    continuous: 是否支持持续模式
    continuous_text: 持续状态显示模板，支持 {actors} 和 {targets}
    actor_slots: 调教方每人占用槽位
    target_slots: 被调教方每人占用槽位
    continuous_tick: 持续状态轮次结算函数"""
    def decorator(func):
        REGISTER_CMD[key] = func
        REGISTER_CMD_NAME[key] = name
        REGISTER_CAT[key] = cat
        REGISTER_MODE[key] = train_mode
        if can:
            REGISTER_CAN[key] = can
        REGISTER_NEEDS_TARGET[key] = needs_target
        if frontend:
            REGISTER_FRONTEND[key] = frontend
        REGISTER_CONTINUOUS[key] = continuous
        if continuous_text:
            REGISTER_CONTINUOUS_TEXT[key] = continuous_text
        REGISTER_ACTOR_SLOTS[key] = actor_slots or {}
        REGISTER_TARGET_SLOTS[key] = target_slots or {}
        if continuous_tick:
            REGISTER_CONTINUOUS_TICK[key] = continuous_tick
        return func
    return decorator

