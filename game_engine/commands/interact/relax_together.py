from __future__ import annotations

import bisect
from typing import TYPE_CHECKING

from game_engine.commands._common import (
    favor_trust_proc,
    global_can,
    new_source,
    say_chara_line,
    source_proc,
)
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.utils.text_color import c_recover

from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from data.time.time_data import COMMAND_TIME_DATA

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False
    # 判定是否在放松活动中
    return world.activity_manager.activities[npc.id].id == "relax"


@register_cmd("relax_together", "一起放松", "日常", can=can)
def relax_together(world: World, option: str):
    """一起放松
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source(
        {
            "happiness_source": 100,  # 欢乐
            "passivity_source": 50,  # 被动
        }
    )
    ctx.say(f"{world.player.name}和{npc.name}一起悠闲自在地度过一段时间…")

    say_chara_line(npc, ctx, "relax_together")

    # abl: 亲密、好感度系数、时间系数修正
    favor_lst = [100, 500, 1000, 5000, 10000, 30000]
    score = bisect.bisect_right(favor_lst, npc.favor)
    activity_remaining_time = world.activity_manager.activities[npc.id].duration
    minutes = min(activity_remaining_time, COMMAND_TIME_DATA["relax_together"])
    time_ratio = minutes / 10
    source["happiness_source"] = int((
        source["happiness_source"] + (npc.abl["intimacy_abl"] + score) * 10
    ) * time_ratio)
    source["passivity_source"] = int((
        source["passivity_source"] + (npc.abl["obedience_abl"] + score) * 5
    ) * time_ratio)

    # 恢复体力和气力(舰娘的恢复逻辑在活动中处理)
    stamina_recovery = int(world.player.get_max_stamina() * 0.003 * minutes)
    energy_recovery = int(world.player.get_max_energy() * 0.005 * minutes)
    world.player.set_stamina(world.player.get_stamina() + stamina_recovery)
    world.player.set_energy(world.player.get_energy() + energy_recovery)
    ctx.say(
        f"{world.player.name}正在放松 "
        + c_recover(f"体力+{stamina_recovery} 气力+{energy_recovery}")
    )

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say_source(source, npc.name)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 10
    ctx.consume(energy=energy_cost, chara=world.player)
    ctx.consume(energy=energy_cost, chara=npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx)

    # 推进时间
    ctx.advance_time(minutes)

    return ctx.result()
