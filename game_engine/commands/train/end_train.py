from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._context import CommandContext

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    return True


@register_cmd('end_train', '结束调教', '特殊', train_mode=True, can=can, needs_target=False)
def end_train(world: World):
    """结束调教"""
    ctx = CommandContext(world)

    # 结束调教
    world.train_manager.end_train()

    ctx.say('结束了调教')
    return ctx.result()
