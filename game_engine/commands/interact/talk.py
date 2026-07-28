from __future__ import annotations
from typing import TYPE_CHECKING
from random import randint

from game_engine.data_pipeline.palam_effect import palam2favor
from game_engine.data_pipeline.src2palam_proc import src2palam_proc
if TYPE_CHECKING:
    from world import World

from ...data_pipeline.favor_effect import favor2source
from .._commands import register_cmd
from .._context import CommandContext
from data.time.time_data import command_time_data


@register_cmd('talk')
def talk(world: World, option: str):
    '''会话
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    player = world.player
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = {
        'happiness_source': 200,    # 欢乐
        'conquest_source': 100,     # 征服
        'passivity_source': 100,    # 被动
    }

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

    # 好感对source修正
    favor_multi = favor2source(npc.favor)

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
    match player.abl['talk_abl']:
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
        case _:
            abl_multi = 1.5
    
    for k in source:
        source[k] = int(source[k] * favor_multi * abl_multi)

    ctx.say(f'欢乐({source["happiness_source"]}) 征服({source["conquest_source"]}) 被动({source["passivity_source"]})')

    # source->palam
    mes_source, mes_target = src2palam_proc(source, world.player, npc)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 更新palam等级
    world.player.update_palam_level()
    npc.update_palam_level()
    
    # 体力和气力消耗
    energy_cost = 10
    ctx.consume(energy=energy_cost, npc=npc)

    # 处理好感和信赖
    ex_favor = randint(1, 2) * world.player.abl['talk_abl']
    ex_trust = randint(1, 2) * world.player.abl['talk_abl'] // 2
    # palam对好感的修正
    ex_favor += palam2favor(npc.palam)
    # TODO: 心情加成
    # TODO: 后续加成在这里添加

    favor = max(0, randint(1, 2) + ex_favor)
    trust = max(0, 1 + ex_trust)
    npc.favor += favor
    npc.trust += trust

    ctx.say(f'好感+{favor} ({npc.name})', f'信赖+{trust} ({npc.name})')

    ctx.say(f'度过了{command_time_data["talk"]}分钟')
    return ctx.result()
