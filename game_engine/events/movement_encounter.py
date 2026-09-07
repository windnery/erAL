from __future__ import annotations
from typing import TYPE_CHECKING
from game_engine.events._base import BaseEvent, register_event
from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


@register_event
class MovementEncounterEvent(BaseEvent):
    """中继步进移动途中的偶遇中断事件"""
    event_id: str = "movement_encounter"
    name: str = "路途偶遇"
    trigger: EventTrigger = EventTrigger.MOVE_ENTER
    priority: int = 100
    exclusive: bool = True
    once: bool = False

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        # 该事件由 MovementManager 直接调度挂起 pending_choice，不通过 trigger() 自动触发
        return False

    def execute(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        return False

    def on_choice(
        self,
        world: World,
        ctx: CommandContext,
        option_key: str,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        """接收玩家的选择分支并交由 MovementManager 推进"""
        msgs = world.movement_manager.handle_choice(option_key)
        for msg in msgs:
            ctx.say(msg)
        return True
