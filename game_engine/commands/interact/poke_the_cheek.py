from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from config.attr_defs import ATTR_DEFS
from game_engine.data_pipeline.trust.trust_calc import trust_calc

if TYPE_CHECKING:
    from world import World


@register_cmd('poke_the_cheek')
def poke_the_cheek(world: World, option: str):
    '''戳脸颊
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 80,  # 欢乐
        'love_source': 50,  # 情爱
        'disgust_source': 120,  # 反感
        'submission_source': 500,  # 屈服
        'passivity_source': 100,  # 被动
    })

    line = npc.get_line('poke_the_cheek')
    ctx.say(f'戳了戳{npc.name}的脸蛋……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # ABL: 亲密
    if npc.abl['intimacy_abl'] <= 3:
        source['happiness_source'] += 100 + npc.abl['intimacy_abl'] * 20
        source['love_source'] += 150+npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 5:
        source['happiness_source'] += 300 + npc.abl['intimacy_abl'] * 40
        source['love_source'] += 350 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 8:
        source['happiness_source'] += 600 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 500 + npc.abl['intimacy_abl'] * 40
    elif npc.abl['intimacy_abl'] <= 11:
        source['happiness_source'] += 800 + npc.abl['intimacy_abl'] * 70
        source['love_source'] += 700 + npc.abl['intimacy_abl'] * 60
    else:
        source['happiness_source'] += 1200 + npc.abl['intimacy_abl'] * 40
        source['love_source'] += 1500 + npc.abl['intimacy_abl'] * 20

    # ABL: 顺从
    source['passivity_source'] += 200 * npc.abl['obedience_abl']

    # 好感度
    if npc.favor <= 500:
        source['happiness_source'] += npc.favor
    elif npc.favor <= 5000:
        source['happiness_source'] += 200 + (npc.favor - 500) // 3
    else:
        source['happiness_source'] += 1000 + (npc.favor - 5000) // 5

    # TODO: 睡眠中

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f'{ATTR_DEFS['source'][k]['name']}({v})')
    ctx.say(' '.join(source_list))

    # TODO: source->mood

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
    ctx.consume(p_energy_cost, world.player)
    ctx.consume(n_energy_cost, npc)

    # 好感和信赖处理
    favor_delta = favor_calc(npc, source)
    trust_delta = trust_calc(npc, source)
    npc.favor += favor_delta
    npc.trust += trust_delta

    # 推进时间
    ctx.advance_time(command_time_data['poke_the_cheek'])

    if favor_delta > 0:
        ctx.say(f'好感+{favor_delta} ({npc.name})')
    elif favor_delta < 0:
        ctx.say(f'好感{favor_delta} ({npc.name})')
    if trust_delta > 0:
        ctx.say(f'信赖+{trust_delta} ({npc.name})')
    elif trust_delta < 0:
        ctx.say(f'信赖{trust_delta} ({npc.name})')

    ctx.say(f'度过了{command_time_data["poke_the_cheek"]}分钟')
    return ctx.result()
