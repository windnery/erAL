from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._common import say_chara_line
from game_engine.events._base import BaseEvent, register_event
from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


@register_event
class DateEndNormalEvent(BaseEvent):
    """约会归途通常道别事件：根据综合约会得分分档进行反馈道别（兜底事件）"""
    event_id = "date_end_normal"
    name = "约会通常道别"
    trigger = EventTrigger.DATE_END
    priority = 0
    exclusive = True
    once = False

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        return target is not None

    def execute(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        if target is None:
            return False

        score = kwargs.get('score', 0)
        time_out = kwargs.get('time_out', False)

        if time_out:
            ctx.say(f"『时间已经这么晚了呀……虽然有点舍不得，但今天就先到这里吧。』")
            ctx.say(f"{target.name}挥了挥手，互道晚安后各自返回了房间。")
        elif score >= 350:
            ctx.say(f"『今天玩得非常非常开心！谢谢你，指挥官……下次一定要再约我出来哦！』")
            ctx.say(f"{target.name}依依不舍地轻挥小手，脸上洋溢着心满意足的灿烂笑容。")
        elif score >= 150:
            ctx.say(f"『今天过得很充实呢。指挥官回去也早点休息吧。』")
            ctx.say(f"{target.name}微笑着向你颔首道别。")
        else:
            ctx.say(f"『呼……感觉稍微有点累了呢，那我先回去了。』")
            ctx.say(f"{target.name}有些疲倦地向你道别。")

        say_chara_line(target, ctx, 'date_end')
        return True
