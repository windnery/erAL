from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._common import say_chara_line
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.events._base import BaseEvent, register_event, ChoiceOption
from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


@register_event
class DateEndConfessEvent(BaseEvent):
    """约会归途告白事件：极高约会得分下角色向玩家主动告白确立恋人关系"""
    event_id = "date_end_confess"
    name = "约会归途告白"
    trigger = EventTrigger.DATE_END
    priority = 80
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
        # 无接吻经验不触发
        if not target.has_talent('no_kiss_exp'):
            return False
        # 已是恋人则不触发告白
        if target.has_talent('lover'):
            return False

        score = kwargs.get('score', 0)
        threshold = 530
        if target.has_talent('impassable_line'):
            threshold += 20

        return score >= threshold

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

        if not say_chara_line(target, ctx, 'date_end_confess'):
            # 无口上时使用通用口上
            ctx.say(f"走在回程的路上，{target.name}忽然停下了脚步，双手紧紧攥着胸口，双颊泛起如晚霞般的红晕。")
            ctx.say(f"『那个……{player.name}，今天真的非常非常开心……』")
            ctx.say(f"『我……我不想只做一般的同伴了，我想一直一直陪在你的身边！请和我交往吧！』")

        # 挂起选择，等待玩家做出决定
        world.event_manager.set_pending_choice(
            event_id=self.event_id,
            target_id=target.id,
            title=f"面对{target.name}的告白……",
            options=[
                ChoiceOption(key="accept", text="接受告白"),
                ChoiceOption(key="reject", text="拒绝"),
            ],
            extra_data=kwargs
        )
        return True

    def on_choice(
            self,
            world: World,
            ctx: CommandContext,
            option_key: str,
            target: ShipGirl | None = None,
            **kwargs
    ) -> bool:
        if target is None:
            return False

        player = world.player
        if option_key == "accept":
            ctx.say(f"{player.name}温柔地微笑着握住{target.name}的手，将她紧紧拥入怀中，接受了这份真挚的心意。")
            ctx.say(f"从今天开始，{player.name}和{target.name}正式成为了[[c:#ff6fae]][恋人][[/c]]！")

            # 确立恋人关系
            target.set_talent('lover', '1')
            target.favor += 300
            target.trust += 100
            ctx.say_exp(exp_calc('love_exp', target, 20))
            ctx.say_exp(exp_calc('love_exp', player, 20))

        elif option_key == "reject":
            target.trust = max(0, target.trust - 20)
            if not say_chara_line(target, ctx, 'date_end_confess_reject'):
                # 无口上时使用通用口上
                ctx.say(f"{player.name}有些歉意地摇了摇头，委婉地谢绝了{target.name}的心意……")
                ctx.say(f"{target.name}眼神中闪过一丝失落，但还是强撑着微笑道：『没、没关系的……是{target.name}太心急了……』")

        return True
