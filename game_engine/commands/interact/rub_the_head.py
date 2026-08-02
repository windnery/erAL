from random import randint

from .._commands import register_cmd
from .._context import CommandContext
from data.time.time_data import command_time_data


@register_cmd('rub_the_head')
def rub_the_head(world, option: str):
    '''摸头
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)

    line = npc.get_line('rub_the_head')
    ctx.say(f'摸了摸{npc.name}的头')
    if not line:
        return ctx.result()
    ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['rub_the_head'])

    # 体力和气力消耗
    stamina_cost = 5
    energy_cost = 10
    ctx.consume(stamina=stamina_cost, energy=energy_cost, chara=npc)

    # 处理好感和信赖
    # TODO: 增加属性加成
    favor = randint(1, 4)
    trust = randint(1, 2)
    npc.base['favor'] += favor
    npc.base['trust'] += trust

    ctx.say(f'好感+{favor}', f'信赖+{trust}')

    ctx.say(f'度过了{command_time_data["rub_the_head"]}分钟')
    return ctx.result()
