from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

from config.mood_config import MOOD_BAD
from data.time.time_data import COMMAND_TIME_DATA
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    favor_trust_proc,
    global_can,
    new_source,
    say_chara_line,
    source_proc,
)
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False
    # 失望刻印
    if npc.mark["disappointment_mark"] > 0:
        return False
    # 不处于生气
    if npc.get_mood() > MOOD_BAD:
        return False
    # 亲密低
    return not npc.abl["intimacy_abl"] < 3


@register_cmd("listen_to_complaints", "听牢骚", "日常", can=can)
def listen_to_complaints(world: World, option: str):
    """听牢骚
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source(
        {
            "happiness_source": 400,  # 欢乐
        }
    )
    ctx.say(f"耐心听{npc.name}发牢骚……")

    say_chara_line(npc, ctx, "listen_to_complaints")

    # 推进时间
    ctx.advance_time(COMMAND_TIME_DATA["listen_to_complaints"])

    score = 50 + world.player.abl["talk_abl"] * 5 + npc.abl["intimacy_abl"] * 2
    rand = randint(0, score)
    if rand < 20:
        result = 1
    elif rand < 50:
        result = 2
    else:
        result = 3
    # 陷落阶段加成
    result += npc.get_talent_value("relationship")

    match result:
        case 1:
            source["disgust_source"] = 100
        case 2:
            source["happiness_source"] += 30 * npc.abl["intimacy_abl"]
        case 3:
            source["happiness_source"] += 50 * npc.abl["intimacy_abl"]
            source["love_source"] = 200
            npc.set_mood(npc.get_mood() + 1)
        case _:
            source["happiness_source"] += 75 * npc.abl["intimacy_abl"]
            source["love_source"] = 300
            npc.set_mood(npc.get_mood() + 2)

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say_source(source)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()
