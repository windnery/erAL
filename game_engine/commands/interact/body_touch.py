from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.source.src2mood_proc import src2mood_proc
from game_engine.data_pipeline.source.src2palam_proc import src2palam_proc
if TYPE_CHECKING:
    from world import World


@register_cmd('body_touch')
def body_touch(world: World, option: str):
    '''身体接触
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    player = world.player
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = {
        'happiness_source': 100,    # 欢乐
        'love_source': 100,         # 情爱
        'exposure_source': 20,      # 露出
        'disgust_source': 50,       # 反感
        'conquest_source': 100,     # 征服
        'passivity_source': 100,    # 被动
    }

    line = npc.get_line('body_touch')
    ctx.say(f'尝试和{npc.name}身体接触……')
    # if not line:
    #     return ctx.result()
    # ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['body_touch'])

    # abl对source修正
    # abl: 亲密
    if npc.abl['intimacy_abl'] <= 1:
        source['happiness_source'] += npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 3:
        source['happiness_source'] += 100 + npc.abl['intimacy_abl'] * 40
        source['love_source'] += 200 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 5:
        source['happiness_source'] += 400 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 400 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 8:
        source['happiness_source'] += 700 + npc.abl['intimacy_abl'] * 60
        source['love_source'] += 600 + npc.abl['intimacy_abl'] * 40
    elif npc.abl['intimacy_abl'] <= 11:
        source['happiness_source'] += 1200 + npc.abl['intimacy_abl'] * 80
        source['love_source'] += 800 + npc.abl['intimacy_abl'] * 40
    else:
        source['happiness_source'] += 2000 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 1800 + npc.abl['intimacy_abl'] * 20

    source['conquest_source'] += npc.abl['sadism_abl'] * 200
    source['passivity_source'] += npc.abl['obedience_abl'] * 200

    # 好感度->source
    favor = npc.favor
    if favor <= 500:
        source['happiness_source'] += favor
    elif favor <= 5000:
        source['happiness_source'] += 500 + (favor - 500) // 3
    else:
        source['happiness_source'] += 2000 + (favor - 5000) // 5

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say(f'欢乐({source["happiness_source"]}) \
            情爱({source["love_source"]}) \
            露出({source["exposure_source"]}) \
            反感({source["disgust_source"]}) \
            征服({source["conquest_source"]}) \
            被动({source["passivity_source"]})')

    # source->mood
    mood_delta = src2mood_proc(source, npc)
    npc.base['mood'] += mood_delta

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
    energy_cost = 30
    ctx.consume(energy=energy_cost, npc=npc)

    # 处理好感和信赖
    # abl亲密低会导致好感度下降
    favor_delta = 0
    if npc.abl['intimacy_abl'] == 0:
        favor_delta -= 3
    elif npc.abl['intimacy_abl'] == 1:
        favor_delta -= 2
    elif npc.abl['intimacy_abl'] == 2:
        favor_delta -= 1
    # 好感度低会导致好感度下降
    if npc.favor < 50:
        favor_delta -= 3
    elif npc.favor < 100:
        favor_delta -= 2
    elif npc.favor < 200:
        favor_delta -= 1

    favor_delta += favor_calc(npc, source)
    npc.favor += favor_delta

    ctx.say(f'好感+{favor_delta} ({npc.name})')

    ctx.say(f'度过了{command_time_data["body_touch"]}分钟')
    return ctx.result()





