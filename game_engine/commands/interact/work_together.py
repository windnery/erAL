from __future__ import annotations
from random import randint
from typing import TYPE_CHECKING

from config.map_actions import WORK_LOC
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import favor_trust_proc, new_source
from game_engine.commands._context import CommandContext
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """判断是否可以一起工作"""
    player = world.player
    if player.location['region'] not in WORK_LOC:
        return False
    if player.location['node'] not in WORK_LOC[player.location['region']]:
        return False
    if npc != world.npc_manager.secretary_ship:
        return False
    if world.work_manager.works <= 0:
        return False
    if world.player.is_energy_empty():
        return False
    return True


@register_cmd('work_together', '一起工作', '日常', can)
def work_together(world, option=None):
    """一起工作"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    work_manager = world.work_manager

    line = npc.get_line('work_together')
    ctx.say(f"和{npc.name}一起认真工作……")
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['work_together'])

    # 做工作
    # 玩家的工作部分
    works = randint(120, 180)
    work_abl = world.player.abl['work_abl']
    # abl加成
    match work_abl:
        case 1:
            works *= 1.25
        case 2:
            works *= 1.5
        case 3:
            works *= 1.75
        case 4:
            works *= 2
        case 5:
            works *= 2.5
        case 6:
            works *= 3
    # 秘书舰的工作部分
    works += randint(80, 140)
    work_abl = npc.abl['work_abl']
    # abl加成
    match work_abl:
        case 1:
            works *= 1.25
        case 2:
            works *= 1.5
        case 3:
            works *= 1.75
        case 4:
            works *= 2
        case 5:
            works *= 2.5
        case 6:
            works *= 3
    works = int(works)
    work_manager.do_work(works)

    # 消耗体力和气力
    p_stamina_cost = 150
    p_energy_cost = 200
    n_stamina_cost = 100
    n_energy_cost = 150
    ctx.consume(p_stamina_cost, p_energy_cost, world.player)
    ctx.consume(n_stamina_cost, n_energy_cost, npc)
    ctx.say(f"在{npc.name}的协作下完成了{works}工作量，还剩{work_manager.works}工作量")

    # 工作经验
    world.player.exp['work_exp'] += 1
    npc.exp['work_exp'] += 1
    ctx.say(f'工作经验+1 ({world.player.name})', f'工作经验+1 ({npc.name})')

    # 处理好感和信赖
    favor_trust_proc(new_source({}), npc, ctx, ex_favor=randint(1, 3), ex_trust=randint(1, 2))

    ctx.say(f'度过了{command_time_data["work_together"]}分钟')

    return ctx.result()
