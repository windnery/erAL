from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, low_favor2favor
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    '''执行判定'''
    # 气力0
    if world.player.is_energy_empty():
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

@register_cmd('hug', '拥抱', '亲昵', can)
def hug(world: World, option: str):
    '''拥抱
    world: 游戏世界对象
    option: 指令对象'''
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

    line = npc.get_line('hug')
    ctx.say(f'抱住了{npc.name}……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

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

    # TODO: 睡眠中

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f'{ATTR_DEFS['source'][k]['name']}({v})')
    ctx.say(' '.join(source_list))

    # TODO: source->mood
    # mood_delta = src2mood_proc(source, npc)
    # npc.base['mood'] += mood_delta

    # source->palam
    mes_source, mes_target = palam_calc(source, world.player, npc)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 更新palam等级
    world.player.update_palam_level()
    npc.update_palam_level()

    # 体力和气力消耗
    p_energy_cost = 50
    n_energy_cost = 50
    ctx.consume(energy=p_energy_cost, chara=world.player)
    ctx.consume(energy=n_energy_cost, chara=npc)

    # 处理好感和信赖
    favor_delta = favor_calc(npc, source)
    trust_delta = trust_calc(npc, source)
    # 好感度低会导致好感度下降
    favor_delta += low_favor2favor(npc.favor)
    npc.favor += favor_delta
    npc.trust += trust_delta

    # 推进时间
    ctx.advance_time(command_time_data['hug'])

    if favor_delta > 0:
        ctx.say(f'好感+{favor_delta} ({npc.name})')
    elif favor_delta < 0:
        ctx.say(f'好感{favor_delta} ({npc.name})')
    if trust_delta > 0:
        ctx.say(f'信赖+{trust_delta} ({npc.name})')
    elif trust_delta < 0:
        ctx.say(f'信赖{trust_delta} ({npc.name})')

    ctx.say(f'度过了{command_time_data["hug"]}分钟')
    return ctx.result()
