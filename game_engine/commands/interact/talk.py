from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import new_source, global_can, favor_trust_proc, source_proc
from game_engine.data_pipeline.common_src_modify import common_src_modify
from ...data_pipeline.exp_calc import exp_calc
from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext
from data.time.time_data import command_time_data


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False

    return True


@register_cmd('talk', '会话', '日常', can=can)
def talk(world: World, option: str):
    """会话
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 200,  # 欢乐
        'conquest_source': 100,  # 征服
        'passivity_source': 100,  # 被动
    })

    line = npc.get_line('talk')
    ctx.say(f'和{npc.name}聊了一会儿……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['talk'])

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
    abl_multi_dict = {0: 0.2, 1: 0.4, 2: 0.7, 3: 1.0, 4: 1.2, 5: 1.5}
    for k in source:
        source[k] = int(source[k] * abl_multi_dict.get(world.player.abl['talk_abl'], 2.0))

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(' '.join(source_list))

    # source->mood
    # mood_delta = src2mood_proc(source, npc)
    # npc.base['mood'] += mood_delta

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 10
    ctx.consume(energy=energy_cost, chara=world.player)
    ctx.consume(energy=energy_cost, chara=npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx)

    # 获得经验处理
    if npc.is_dating():
        ctx.say(*exp_calc(['talk_exp', 'love_exp'], world.player, npc, True))
    else: ctx.say(*exp_calc(['talk_exp'], world.player, npc, True))

    ctx.say(f'度过了{command_time_data["talk"]}分钟')
    return ctx.result()
