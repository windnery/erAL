from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._common import say_chara_line
from game_engine.events._base import BaseEvent, register_event
from game_engine.events._enums import EventTrigger
from game_engine.utils.text_color import c_success

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


@register_event
class DateEndDisappointmentClearEvent(BaseEvent):
    """约会归途失望刻印消除事件：在约会氛围良好时消解心中的隔阂"""
    event_id = "date_end_disappointment_clear"
    name = "约会失望刻印消除"
    trigger = EventTrigger.DATE_END
    priority = 90
    exclusive = True
    once = False

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        if target is None:
            return False
        # 必须存在失望刻印
        disappointment_lv = target.mark['disappointment_mark']
        if disappointment_lv <= 0:
            return False
        # 刻印lv1且约会得分大于50
        score = kwargs.get('score', 0)
        if disappointment_lv == 1:
            if score < 150:
                return False
        elif disappointment_lv == 2:
            if score < 300:
                return False
        else:
            if score < 450:
                return False
        return True

    def execute(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        if target is None:
            return False

        # 获取并减少失望刻印
        current_disappointment = target.mark['disappointment_mark']
        new_disappointment = max(0, current_disappointment - 1)
        target.mark['disappointment_mark'] = new_disappointment

        ctx.say(f"在愉快的约会气氛中，{target.name}心中的隔阂与芥蒂悄然消解……")
        if new_disappointment == 0:
            ctx.say(c_success(f"{target.name}完全失去了失望刻印！"))
        else:
            ctx.say(c_success(f"{target.name}的失望刻印下降为 LV{new_disappointment}！"))

        say_chara_line(target, ctx, 'date_end_disappointment_clear')
        return True
