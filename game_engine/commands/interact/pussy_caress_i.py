from __future__ import annotations

from typing import TYPE_CHECKING

from data.time.time_data import COMMAND_TIME_DATA
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    favor_trust_proc,
    new_source,
    say_chara_line,
    source_proc,
)
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.managers.NpcManager import NpcManager
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_notice

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 气力0
    if world.player.is_energy_empty():
        return False
    # 无可用手
    if world.player.body_slots["hands"] == 0:
        return False
    # 工作中且陷落阶段在“爱”以下
    if npc.is_working() and npc.get_talent_value("relationship") < 3:
        return False
    # 陷落阶段在喜欢以上
    if npc.get_talent_value("relationship") >= 2:
        return True
    # 好感度低
    if npc.favor < 400:
        return False
    # 亲密低
    return not npc.abl["intimacy_abl"] < 5



@register_cmd("pussy_caress_i", "秘穴爱抚", "性骚扰", can=can)
def pussy_caress_i(world: World, option: str):
    """秘穴爱抚
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source(
        {
            "c_pleasure_source": 80,  # 快C
            "happiness_source": 100,  # 欢乐
            "love_source": 150,  # 情爱
            "lust_source": 150,  # 欲情
            "exposure_source": 250,  # 露出
            "disgust_source": 600,  # 反感
            "passivity_source": 145,  # 被动
        }
    )
    ctx.say(f"把手伸向{npc.name}的秘穴抚摸……")

    say_chara_line(npc, ctx, "pussy_caress_i")

    # 推进时间
    ctx.advance_time(COMMAND_TIME_DATA["pussy_caress_i"])

    # abl: 指
    source["c_pleasure_source"] += npc.abl["finger_abl"] * 10

    # TODO: 衣装影响

    # 旁人在场
    if (
        NpcManager.with_mob(npc.location["region"], npc.location["node"])
        and npc.abl["exposure_abl"] < 6  # abl:露出 < 6
        and npc.get_talent_value("sense_of_shame") > -1  # talent:不知羞耻
    ):
        source["exposure_source"] += 200
        source["escape_source"] += 130
        ctx.say(c_notice(f"有旁人在场，{npc.name}似乎有些害羞……"))

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say_source(source)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    ctx.consume(5, 50, npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx, True, ex_trust=-5)

    # 经验
    if npc.is_dating():
        ctx.say_exp(exp_calc("date_exp", world.player))
        ctx.say_exp(exp_calc("date_exp", npc))
    ctx.say_exp(exp_calc("c_exp", npc))
    ctx.say_exp(exp_calc("finger_exp", world.player))
    

    return ctx.result()
