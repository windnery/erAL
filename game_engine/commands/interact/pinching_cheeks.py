from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, low_intimacy2favor, low_favor2favor, global_can, favor_trust_proc, \
    source_proc
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from config.attr_defs import ATTR_DEFS
from game_engine.data_pipeline.trust.trust_calc import trust_calc
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
    # 好感度低
    if npc.favor < 200:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 4:
        return False

    return True

@register_cmd('pinching_cheeks', '揉脸蛋', '亲昵', can=can)
def pinching_cheeks(world: World, option: str):
    """揉脸蛋
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'happiness_source': 100,  # 欢乐
        'pain_source': 100,  # 苦痛
        'disgust_source': 120  # 反感
    })

    line = npc.get_line('pinching_cheeks')
    ctx.say(f'揉了揉{npc.name}的脸蛋……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['pinching_cheeks'])

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
    else:
        source['happiness_source'] += 1200 + npc.abl['intimacy_abl'] * 40
        source['love_source'] += 1500 + npc.abl['intimacy_abl'] * 20

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
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(' '.join(source_list))

    # TODO: source->mood

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    n_stamina_cost = 20
    n_energy_cost = 50
    ctx.consume(n_stamina_cost, n_energy_cost, npc)

    # 好感和信赖处理
    favor_trust_proc(source, npc, ctx, True)

    # 经验
    if npc.is_dating():
        ctx.say(*exp_calc(['love_exp'], world.player, npc, True))

    ctx.say(f'度过了{command_time_data["pinching_cheeks"]}分钟')
    return ctx.result()
