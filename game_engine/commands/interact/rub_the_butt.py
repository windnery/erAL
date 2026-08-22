from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

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
    # 陷落阶段在喜欢以上
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 好感度低
    if npc.favor < 350:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 5:
        return False

    return True


@register_cmd('rub_the_butt', '摸屁股', '性骚扰', can=can)
def rub_the_butt(world: World, option: str):
    """摸屁股
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 100,  # 欢乐
        'love_source': 100,  # 情爱
        'exposure_source': 200,  # 暴露
        'disgust_source': 300,  # 反感
        'lust_source': 100,  # 欲情
        'passivity_source': 100,  # 被动
    })
    ctx.say(f'摸了摸{npc.name}的屁股……')

    say_chara_line(npc, ctx, 'rub_the_butt')

    # 推进时间
    ctx.advance_time(command_time_data['rub_the_butt'])

    # abl对source修正
    # abl: 亲密
    if npc.abl['intimacy_abl'] <= 5:
        source['disgust_source'] -= npc.abl['intimacy_abl'] * 5
    elif npc.abl['intimacy_abl'] <= 7:
        source['happiness_source'] += 400 + npc.abl['intimacy_abl'] * 5
        source['love_source'] += 400 + npc.abl['intimacy_abl'] * 10
        source['disgust_source'] -= npc.abl['intimacy_abl'] * 10
    elif npc.abl['intimacy_abl'] <= 9:
        source['happiness_source'] += 700 + npc.abl['intimacy_abl'] * 10
        source['love_source'] += 600 + npc.abl['intimacy_abl'] * 15
        source['disgust_source'] -= npc.abl['intimacy_abl'] * 15
        source['lust_source'] += 200 * npc.abl['desire_abl']
        source['passivity_source'] += 200 * npc.abl['obedience_abl']
    elif npc.abl['intimacy_abl'] <= 11:
        source['happiness_source'] += 1200 + npc.abl['intimacy_abl'] * 20
        source['love_source'] += 800 + npc.abl['intimacy_abl'] * 25
        source['disgust_source'] -= npc.abl['intimacy_abl'] * 20
        source['lust_source'] += 250 * npc.abl['desire_abl']
        source['passivity_source'] += 250 * npc.abl['obedience_abl']
    else:
        source['happiness_source'] += 2000 + npc.abl['intimacy_abl'] * 20
        source['love_source'] += 1800 + npc.abl['intimacy_abl'] * 30
        source['disgust_source'] -= npc.abl['intimacy_abl'] * 50
        source['lust_source'] += 1000 + 250 * npc.abl['desire_abl']
        source['passivity_source'] += 1000 + 250 * npc.abl['obedience_abl']

    # TODO: 睡眠中

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say_source(source)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    p_energy_cost = 50
    n_energy_cost = 50
    ctx.consume(energy=p_energy_cost, chara=world.player)
    ctx.consume(energy=n_energy_cost, chara=npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx, True, ex_trust=-1)

    # 经验
    if npc.is_dating():
        ctx.say_exp(exp_calc('love_exp', world.player))
        ctx.say_exp(exp_calc('love_exp', npc))

    return ctx.result()
