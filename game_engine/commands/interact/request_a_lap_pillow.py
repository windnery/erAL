from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, low_favor2favor, global_can, favor_trust_proc, source_proc
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
    # 工作中且陷落阶段在“爱”以下
    if npc.is_working() and npc.get_talent_value('relationship') < 3:
        return False
    # TODO: 必须在室内且不是厕所/浴室
    # 陷落阶段在喜欢以上
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 好感度低
    if npc.favor < 300:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 5:
        return False

    return True

@register_cmd('request_a_lap_pillow', '索求膝枕', '亲昵', can)
def request_a_lap_pillow(world: World, option: str):
    """索求膝枕
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'love_source': 170,  # 情爱
        'exposure_source': 55,  # 露出
        'disgust_source': 50,  # 反感
    })

    line = npc.get_line('request_a_lap_pillow')
    ctx.say(f'向{npc.name}请求膝枕……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['request_a_lap_pillow'])

    # ABL: 亲密
    if npc.abl['intimacy_abl'] <= 1:
        source['love_source'] += npc.abl['intimacy_abl'] * 20
    elif npc.abl['intimacy_abl'] <= 3:
        source['love_source'] += 200 + npc.abl['intimacy_abl'] * 20
    elif npc.abl['intimacy_abl'] <= 5:
        source['love_source'] += 400 + npc.abl['intimacy_abl'] * 20
    elif npc.abl['intimacy_abl'] <= 8:
        source['love_source'] += 600 + npc.abl['intimacy_abl'] * 30
        source['exposure_source'] += 200 + npc.abl['intimacy_abl'] * 10
    elif npc.abl['intimacy_abl'] <= 11:
        source['love_source'] += 800 + npc.abl['intimacy_abl'] * 30
        source['exposure_source'] += 300 + npc.abl['intimacy_abl'] * 10
    else:
        source['love_source'] += 1800 + npc.abl['intimacy_abl'] * 20
        source['exposure_source'] += 700 + npc.abl['intimacy_abl'] * 10

    # 好感度
    if npc.favor <= 500:
        source['love_source'] += npc.favor // 2
        source['obedience_source'] += npc.favor // 5
    elif npc.favor <= 5000:
        source['love_source'] += 400 + (npc.favor - 500) // 5
        source['obedience_source'] += 150 + npc.favor // 20
        source['happiness_source'] += 400 + (npc.favor - 500) // 4
    else:
        source['love_source'] += 1200 + (npc.favor - 5000) // 7
        source['obedience_source'] += 400 + npc.favor // 100
        source['happiness_source'] += 1200 + (npc.favor - 5000) // 4

    source['passivity_source'] = 120 + 240 * npc.abl['obedience_abl']

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
    p_energy_cost = 50
    n_energy_cost = 100
    ctx.consume(energy=p_energy_cost, chara=world.player)
    ctx.consume(energy=n_energy_cost, chara=npc)

    # 好感和信赖处理
    favor_trust_proc(source, npc, ctx, True)

    # 经验
    if npc.is_dating():
        ctx.say(*exp_calc(['love_exp'], world.player, npc, True))

    ctx.say(f'度过了{command_time_data["request_a_lap_pillow"]}分钟')
    return ctx.result()
