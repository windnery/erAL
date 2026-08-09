from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.commands._common import new_source, global_can, favor_trust_proc
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
    # 陷落阶段在喜欢以上 必定可用
    if npc.get_talent_value('relationship') >= 2:
        return True
    # 好感度低
    if npc.favor < 350:
        return False
    # 亲密低
    if npc.abl['intimacy_abl'] < 5:
        return False

    return True

@register_cmd('rub_the_belly', '抚摸肚子', '性骚扰', can)
def rub_the_belly(world: World, option: str):
    """抚摸肚子
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    source: dict[str, int] = new_source({
        'v_pleasure_source': 30,  # 快V
        'happiness_source': 150,  # 欢乐
        'love_source': 100,  # 情爱
        'lust_source': 30,  # 欲情
        'exposure_source': 10,  # 露出
        'disgust_source': 150,  # 反感
        'passivity_source': 120,  # 被动
    })

    line = npc.get_line('rub_the_belly')
    ctx.say(f'揉了揉{npc.name}的肚子……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['body_touch'])

    # TODO: 怀孕补正
    # TODO: 衣服补正

    # ABL:PLAYER: 指
    finger_abl = world.player.abl['finger_abl']
    source['v_pleasure_source'] += finger_abl * 5

    # TODO: 情绪补正

    source['passivity_source'] = 120 + 240 * npc.abl['obedience_abl']

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
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
    n_stamina_cost = 5
    n_energy_cost = 30
    ctx.consume(n_stamina_cost, n_energy_cost, npc)

    # 好感和信赖处理
    if npc.abl['intimacy_abl'] <= 5:
        favor_trust_proc(source, npc, ctx, True, -3)
    else:
        favor_trust_proc(source, npc, ctx, True)

    # 经验
    if npc.is_dating():
        ctx.say(*exp_calc(['love_exp'], world.player, npc, True))

    ctx.say(f'度过了{command_time_data["body_touch"]}分钟')
    return ctx.result()
