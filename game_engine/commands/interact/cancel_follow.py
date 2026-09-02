from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._common import say_chara_line
from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 同行中
    if npc.cflag["following"]:
        return True
    return False


@register_cmd("cancel_follow", "解除同行", "日常", can=can)
def cancel_follow(world: World, option: str):
    """解除同行
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)

    say_chara_line(npc, ctx, 'cancel_follow')
    ctx.say(f"{npc.name}不再跟随{world.player.name}了。")

    # 解除同行状态
    npc.cflag["following"] = False

    return ctx.result()
