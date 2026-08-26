from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._common import say_chara_line, get_attitude
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.events._base import BaseEvent, register_event
from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


@register_event
class DateEndKissEvent(BaseEvent):
    """约会归途初吻事件：当角色未曾接吻、氛围良好且有思慕/恋慕好感时在归途接吻"""
    event_id = "date_end_kiss"
    name = "约会归途初吻"
    trigger = EventTrigger.DATE_END
    priority = 100
    exclusive = True
    once = True

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        if target is None:
            return False
        # 检查是否为初吻（接吻未经验）
        if not target.has_talent('no_kiss_exp'):
            return False
        # 友好以上
        if target.get_talent_value('relationship') < 1:
            return False
        # 合意判定
        _, attitude_score = get_attitude(world.player, target, 30)
        if attitude_score < 180:
            return False
        # 约会氛围得分检查
        score = kwargs.get('score', 0)
        threshold = 220
        if target.has_talent('impassable_line'):
            # 难以逾越的底线
            threshold += 30
        if score < threshold:
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

        player = world.player
        ctx.say(f"在约会回去的路上，夕阳将两人的影子拉得很长……")
        ctx.say(f"{target.name}忽然停下脚步，有些羞涩地轻轻拉住了{player.name}的衣角。")
        ctx.say(f"四目相对间，两人的距离不知不觉拉近，在归途的微风中轻柔地吻在了一起……")

        # 尝试输出专属口上
        say_chara_line(target, ctx, 'date_end_kiss')

        # 经验与素质变更
        target.set_talent('no_kiss_exp', '0')
        ctx.say_exp(exp_calc('kiss_exp', target, 1))
        ctx.say_exp(exp_calc('love_exp', target, 10))

        if player.has_talent('no_kiss_exp'):
            player.set_talent('no_kiss_exp', '0')
        ctx.say_exp(exp_calc('kiss_exp', player, 1))
        ctx.say_exp(exp_calc('love_exp', player, 10))
        return True
