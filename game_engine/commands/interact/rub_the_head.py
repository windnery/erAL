from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, low_favor2favor, low_intimacy2favor, favor_trust_proc
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 气力0
    if world.player.is_energy_empty():
        return False
    # TODO: 睡眠中允许 但是后续加额外的惊醒判定
    # 陷落阶段在喜欢以上 必定可用
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 工作中
    if world.player.is_working():
        return False
    # 好感度低
    if npc.favor < 120:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 3:
        return False

    return True

@register_cmd('rub_the_head', '摸头', '亲昵', can)
def rub_the_head(world: World, option: str):
    """摸头
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 150,  # 欢乐
        'love_source': 150,  # 情爱
        'disgust_source': 80,  # 反感
    })

    line = npc.get_line('rub_the_head')
    ctx.say(f'摸了摸{npc.name}的头……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['rub_the_head'])

    # abl对source修正
    # abl: 亲密
    if npc.abl['intimacy_abl'] <= 3:
        source['happiness_source'] += 150 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 180 + npc.abl['intimacy_abl'] * 40
    elif npc.abl['intimacy_abl'] <= 5:
        source['happiness_source'] += 500 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 450 + npc.abl['intimacy_abl'] * 30
    elif npc.abl['intimacy_abl'] <= 8:
        source['happiness_source'] += 800 + npc.abl['intimacy_abl'] * 50
        source['love_source'] += 700 + npc.abl['intimacy_abl'] * 50
    elif npc.abl['intimacy_abl'] <= 11:
        source['happiness_source'] += 1000 + npc.abl['intimacy_abl'] * 90
        source['love_source'] += 900 + npc.abl['intimacy_abl'] * 50
    else:
        source['happiness_source'] += 1800 + npc.abl['intimacy_abl'] * 40
        source['love_source'] += 2000 + npc.abl['intimacy_abl'] * 20

    source['lust_source'] += 50 + npc.abl['desire_abl'] * 150
    source['passivity_source'] += 100 + npc.abl['obedience_abl'] * 200

    # 好感度->source
    favor = npc.favor
    if favor <= 500:
        source['happiness_source'] += favor
    elif favor <= 5000:
        source['happiness_source'] += 500 + (favor - 500) // 3
    else:
        source['happiness_source'] += 2000 + (favor - 5000) // 5

    # TODO: 睡眠中

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
    favor_trust_proc(source, npc, ctx, True, ex_trust=1)

    # 经验
    if npc.is_dating():
        ctx.say(*exp_calc(['love_exp'], world.player, npc, True))

    ctx.say(f'度过了{command_time_data["rub_the_head"]}分钟')
    return ctx.result()
