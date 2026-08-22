from __future__ import annotations
from game_engine.commands._common import say_chara_line, work_abl_modifier
from random import randint
from typing import TYPE_CHECKING

from config.map_actions import WORK_LOC
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import favor_trust_proc, new_source
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.exp_calc import exp_calc
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


@register_cmd('work_together', '一起工作', '日常', can=can)
def work_together(world, option=None):
    """一起工作"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    work_manager = world.work_manager
    ctx.say(f"和{npc.name}一起认真工作……")

    say_chara_line(npc, ctx, 'work_together')

    # 推进时间
    ctx.advance_time(command_time_data['work_together'])

    # 做工作
    # 玩家的工作部分
    player_works = randint(120, 180)
    work_abl = world.player.abl['work_abl']
    # abl加成
    player_works = work_abl_modifier(work_abl, player_works)
    # 秘书舰的工作部分
    secretary_works = randint(80, 140)
    work_abl = npc.abl['work_abl']
    # abl加成
    secretary_works = work_abl_modifier(work_abl, secretary_works)
    works = int(player_works + secretary_works)
    work_manager.do_work(works)

    # 消耗体力和气力
    p_stamina_cost = 150
    p_energy_cost = 200
    n_stamina_cost = 100
    n_energy_cost = 150
    ctx.consume(p_stamina_cost, p_energy_cost, world.player)
    ctx.consume(n_stamina_cost, n_energy_cost, npc)
    ctx.say(f"在{npc.name}的协作下完成了{works}工作量，还剩{work_manager.works}工作量")

    # 处理好感和信赖
    favor_trust_proc(new_source({}), npc, ctx, ex_favor=randint(1, 3), ex_trust=randint(1, 2))

    # 经验
    if npc.is_dating():
        ctx.say(exp_calc('love_exp', world.player))
        ctx.say(exp_calc('love_exp', npc))
    ctx.say(exp_calc('work_exp', world.player))
    ctx.say(exp_calc('work_exp', npc))

    ctx.say(f'度过了{command_time_data["work_together"]}分钟')

    return ctx.result()
