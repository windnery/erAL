from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, global_can, favor_trust_proc, source_proc
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False
    # 工作中且陷落阶段在“爱”以下
    if npc.is_working() and npc.get_talent_value('relationship') < 3:
        return False
    # 陷落阶段在喜欢以上 必定可用
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 好感度低
    if npc.favor < 260:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 5:
        return False

    return True

@register_cmd('hug', '拥抱', '亲昵', can=can)
def hug(world: World, option: str):
    """拥抱
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 120,  # 欢乐
        'love_source': 160,  # 情爱
        'exposure_source': 100,  # 暴露
        'disgust_source': 220,  # 反感
        'lust_source': 100,  # 欲情
        'passivity_source': 120,  # 被动
        'conquest_source': 120  # 征服
    })
    ctx.say(f'抱住了{npc.name}……')

    say_chara_line(npc, ctx, 'hug')

    # 推进时间
    ctx.advance_time(command_time_data['hug'])

    # abl对source修正
    # abl: 亲密
    if npc.abl['intimacy_abl'] <= 1:
        source['love_source'] += npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 3:
        source['love_source'] += 200 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 5:
        source['love_source'] += 400 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 8:
        source['love_source'] += 600 + npc.abl['intimacy_abl'] * 40
        source['exposure_source'] += 200 + npc.abl['desire_abl'] * 15
        source['lust_source'] += 200 + npc.abl['desire_abl'] * 15
    elif npc.abl['intimacy_abl'] <= 11:
        source['love_source'] += 800 + npc.abl['intimacy_abl'] * 40
        source['exposure_source'] += 300 + npc.abl['desire_abl'] * 15
        source['lust_source'] += 300 + npc.abl['desire_abl'] * 15
    else:
        source['love_source'] += 1800 + npc.abl['intimacy_abl'] * 20
        source['exposure_source'] += 700 + npc.abl['desire_abl'] * 10
        source['lust_source'] += 700 + npc.abl['desire_abl'] * 10

    source['passivity_source'] += 240 * npc.abl['obedience_abl']
    source['conquest_source'] += 240 * npc.abl['sadism_abl']

    # 好感度
    if npc.favor <= 5000:
        source['obedience_source'] += npc.favor // 5
    elif npc.favor <= 10000:
        source['obedience_source'] += 100 + npc.favor // 20
    else:
        source['obedience_source'] += 350 + npc.favor // 100

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(' '.join(source_list))

    # TODO: source->mood
    # mood_delta = src2mood_proc(source, npc)
    # npc.base['mood'] += mood_delta

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    p_energy_cost = 50
    n_energy_cost = 50
    ctx.consume(energy=p_energy_cost, chara=world.player)
    ctx.consume(energy=n_energy_cost, chara=npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx, True)

    # 经验
    if npc.is_dating():
        ctx.say(exp_calc('love_exp', world.player))
        ctx.say(exp_calc('love_exp', npc))

    ctx.say(f'度过了{command_time_data["hug"]}分钟')
    return ctx.result()
