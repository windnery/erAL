from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._context import CommandContext
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 睡觉中
    if npc.is_sleeping():
        return False
    # 不在约会中
    if not npc.is_dating():
        return False

    return True

@register_cmd("end_date", "结束约会", "日常", can=can)
def end_date(world: World, option: str, time_out: bool=False):
    """结束约会"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    if time_out:
        ctx.say(f'因为时间太晚了而不得不终止和{npc.name}的约会……')
    else: ctx.say(f'结束了和{npc.name}的约会……')

    say_chara_line(npc, ctx, 'end_date')

    # TODO: 约会后的处理 包括情绪、理性等

    # 解除约会状态
    npc.cflag['dating'] = False
    npc.cflag['dating_following'] = False

    return ctx.result()
