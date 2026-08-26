from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl

# 事件注册表：按 EventTrigger 组织的所有注册事件类列表
EVENT_REGISTRY: dict[EventTrigger, list[Type[BaseEvent]]] = {
    trigger: [] for trigger in EventTrigger
}


@dataclass
class ChoiceOption:
    """玩家选择选项"""
    key: str                    # 选项标识，如 "accept", "reject"
    text: str                   # 选项文本，如 "接受告白", "委婉拒绝"
    desc: str = ""              # 附加描述或说明


@dataclass
class PendingChoice:
    """挂起等待玩家决策的选择状态"""
    event_id: str               # 来源事件 ID
    target_id: str | None       # 目标角色 ID
    title: str                  # 选择标题或情境描述
    options: list[ChoiceOption] # 选项列表
    extra_data: dict            # 携带的事件上下文参数


class BaseEvent:
    """事件基类

    所有具体事件继承此类，并声明自身的元数据与判定/执行逻辑。
    """
    event_id: str = ""                         # 唯一事件标识符
    name: str = ""                             # 可读事件名称
    trigger: EventTrigger = EventTrigger.DATE_END  # 触发时机
    priority: int = 0                          # 优先级（数值越大越先判定）
    exclusive: bool = True                     # 是否排他（触发后是否中断同一触发点的后续低优先级事件）
    once: bool = False                         # 是否为单次事件（触发一次后不再重复触发）
    target_chara_id: str | None = None         # 专属舰娘 ID（None 为通用事件，指定字符串时仅对该舰娘生效）

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        """判定前置条件是否满足"""
        raise NotImplementedError

    def execute(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        """执行事件效果：文本输出、数值/状态变更、口上调用等
        返回 True 表示成功执行，False 表示执行失败或被放弃
        """
        raise NotImplementedError

    def on_choice(
        self,
        world: World,
        ctx: CommandContext,
        option_key: str,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        """当事件挂起选择且玩家做出决定后触发的分支逻辑"""
        return True


def register_event(cls: Type[BaseEvent]) -> Type[BaseEvent]:
    """装饰器：注册事件类到全局 EVENT_REGISTRY 表中"""
    trigger = cls.trigger
    if trigger not in EVENT_REGISTRY:
        EVENT_REGISTRY[trigger] = []
    
    # 避免重复注册同名事件
    existing_ids = [e.event_id for e in EVENT_REGISTRY[trigger]]
    if cls.event_id not in existing_ids:
        EVENT_REGISTRY[trigger].append(cls)
    return cls
