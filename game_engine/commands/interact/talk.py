from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import new_source
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.mood.mood_calc import src2mood_proc
from game_engine.data_pipeline.palam.palam2src import palam2src
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from ...data_pipeline.trust.trust_calc import trust_calc

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext
from data.time.time_data import command_time_data


@register_cmd('talk')
def talk(world: World, option: str):
    '''会话
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 200,    # 欢乐
        'conquest_source': 100,     # 征服
        'passivity_source': 100,    # 被动
    })

    line = npc.get_line('talk')
    ctx.say(f'和{npc.name}聊了一会儿……')
    if not line:
        return ctx.result()
    ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['talk'])

    # 获得经验处理
    npc.exp['talk_exp'] += 1
    world.player.exp['talk_exp'] += 1
    ctx.say(f'会话经验+1 ({world.player.name})', f'会话经验+1 ({npc.name})')

    # abl对source修正
    # abl: 亲密
    if npc.abl['intimacy_abl'] <= 1:
        source['happiness_source'] += npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 3:
        source['happiness_source'] += 200 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 5:
        source['happiness_source'] += 500 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 8:
        source['happiness_source'] += 750 + npc.abl['intimacy_abl'] * 50
    elif npc.abl['intimacy_abl'] <= 10:
        source['happiness_source'] += 1000 + npc.abl['intimacy_abl'] * 50
    else:
        source['happiness_source'] += 1600 + npc.abl['intimacy_abl'] * 30

    source['conquest_source'] += npc.abl['obedience_abl'] * 100
    source['passivity_source'] += npc.abl['sadism_abl'] * 100

    # abl: 话术
    match world.player.abl['talk_abl']:
        case 0:
            abl_multi = 0.2
        case 1:
            abl_multi = 0.4
        case 2:
            abl_multi = 0.7
        case 3:
            abl_multi = 1.0
        case 4:
            abl_multi = 1.2
        case 5:
            abl_multi = 1.5
        case _:
            abl_multi = 2.0

    # 通用source修正
    source = common_src_modify(source, npc)
    
    for k in source:
        source[k] = int(source[k] * abl_multi)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f'{ATTR_DEFS['source'][k]['name']}({v})')
    ctx.say(' '.join(source_list))

    # source->mood
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
    energy_cost = 10
    ctx.consume(energy=energy_cost, chara=world.player)
    ctx.consume(energy=energy_cost, chara=npc)

    # 处理好感和信赖
    favor_delta = favor_calc(npc, source)
    trust_delta = trust_calc(npc, source)
    npc.favor += favor_delta
    npc.trust += trust_delta

    if favor_delta > 0:
        ctx.say(f'好感+{favor_delta} ({npc.name})')
    elif favor_delta < 0:
        ctx.say(f'好感{favor_delta} ({npc.name})')
    if trust_delta > 0:
        ctx.say(f'信赖+{trust_delta} ({npc.name})')
    elif trust_delta < 0:
        ctx.say(f'信赖{trust_delta} ({npc.name})')

    ctx.say(f'度过了{command_time_data["talk"]}分钟')
    return ctx.result()
