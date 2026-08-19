from __future__ import annotations
from typing import TYPE_CHECKING
from random import randint

from config.map_actions import NAP_LOC, SLEEP_LOC, WORK_LOC
from game_engine.commands._commands import register_cmd
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data
from game_engine.data_pipeline.exp_calc import exp_calc

if TYPE_CHECKING:
    from world import World


def can_nap(world: World, npc=None):
    """判断是否可以小睡"""
    player = world.player
    if player.location['region'] not in NAP_LOC:
        return False
    if player.location['node'] not in NAP_LOC[player.location['region']]:
        return False
    return True

def can_sleep(world: World, npc=None):
    """判断是否可以睡觉"""
    player = world.player
    if player.location['region'] not in SLEEP_LOC:
        return False
    if player.location['node'] not in SLEEP_LOC[player.location['region']]:
        return False
    return True

def can_work(world: World, npc=None):
    """判断是否可以工作"""
    player = world.player
    if player.location['region'] not in WORK_LOC:
        return False
    if player.location['node'] not in WORK_LOC[player.location['region']]:
        return False
    if world.work_manager.works <= 0:
        return False
    if world.player.is_energy_empty():
        return False
    return True

@register_cmd('nap', '小睡', '日常', can=can_nap, needs_target=False)
def nap(world, option=None):
    """小睡"""
    ctx = CommandContext(world)
    player = world.player

    ctx.say(f"{player.name}在沙发上躺下……")

    # 推进时间
    ctx.advance_time(command_time_data['nap'])

    # 回复体力和气力
    stamina_recovered = max(0, int(player.get_stamina() * 0.25) + randint(-80, 100))
    energy_recovered = max(0, int(player.get_energy() * 0.25) + randint(-80, 100))
    ctx.recover(stamina=stamina_recovered, energy=energy_recovered)

    ctx.say(f"小睡了一会儿，恢复了{stamina_recovered}点体力和{energy_recovered}点气力")
    return ctx.result()


@register_cmd('sleep', '睡觉', '日常', can=can_sleep, needs_target=False)
def sleep(world, option=None):
    """睡觉"""
    # 调用settle_day方法进行日终结算
    mes = world.settle_day(sleep=True)
    return mes


@register_cmd('work', '工作', '日常', can=can_work, needs_target=False)
def work(world, option=None):
    """工作"""
    ctx = CommandContext(world)
    work_manager = world.work_manager

    ctx.say("埋头认真工作……")

    # 推进时间
    ctx.advance_time(command_time_data['work'])

    # 做工作
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
    works = int(works)
    work_manager.do_work(works)

    # 消耗体力和气力
    stamina_cost = 150
    energy_cost = 200
    ctx.consume(stamina_cost, energy_cost, world.player)
    ctx.say(f"{world.player.name}完成了{works}工作量，还剩{work_manager.works}工作量")

    # 经验
    ctx.say(exp_calc(['work_exp'], world.player))

    ctx.say(f'度过了{command_time_data["work"]}分钟')

    return ctx.result()
