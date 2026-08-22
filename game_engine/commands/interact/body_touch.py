from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, low_favor2favor, low_intimacy2favor, global_can, favor_trust_proc, \
    source_proc
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
    # 陷落阶段在喜欢以上 必定可用
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 工作中
    if npc.is_working():
        return False
    # 好感度过低
    if npc.favor < 50:
        return False

    return True

@register_cmd('body_touch', '身体接触', '亲昵', can=can)
def body_touch(world: World, option: str):
    """身体接触
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 200,    # 欢乐
        'love_source': 100,         # 情爱
        'exposure_source': 100,     # 露出
        'disgust_source': 100,      # 反感
        'conquest_source': 100,     # 征服
        'passivity_source': 100,    # 被动
    })
    ctx.say(f'尝试和{npc.name}身体接触……')

    say_chara_line(npc, ctx, 'body_touch')

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

    ctx.say_source(source)

    # TODO: source->mood
    # mood_delta = src2mood_proc(source, npc)
    # npc.base['mood'] += mood_delta

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 30
    ctx.consume(energy=energy_cost, chara=world.player)
    ctx.consume(energy=energy_cost, chara=npc)

    # 处理好感和信赖
    favor_trust_proc(source, npc, ctx, True)

    # 经验
    if npc.is_dating():
        ctx.say(exp_calc('love_exp', world.player))
        ctx.say(exp_calc('love_exp', npc))

    ctx.say(f'度过了{command_time_data["body_touch"]}分钟')
    return ctx.result()
