from random import randint

from .._commands import register_cmd
from data.time.time_data import command_time_data

@register_cmd('rub_the_head')
def rub_the_head(world, option: str):
    '''摸头
    world: 游戏世界对象
    option: 指令对象'''
    mes = []

    npc = world.npc_manager.get_npc_by_id(option)
    line = npc.get_line('rub_the_head')

    mes.append(f'摸了摸{npc.name}的头')
    # fallback: 如果没有找到合适的台词，返回默认消息
    if not line:
        return mes
    line = line.replace('{name}', npc.name)
    mes.append(line)

    # 推进时间并获取NPC变动消息
    npc_events = world.advance_time_with_events(command_time_data['rub_the_head'])
    # 体力和气力消耗
    stamina_cost = 5
    energy_cost = 10
    ex_mes = world.change_energy(-energy_cost)
    ex_mes += world.change_stamina(-stamina_cost)
    npc.set_stamina(npc.base.get('stamina', 0) - stamina_cost)
    npc.set_energy(npc.base.get('energy', 0) - energy_cost)
    mes.append(f'体力-{stamina_cost}')
    mes.append(f'气力-{energy_cost}')
    mes.append(f'{npc.name} 体力-{stamina_cost}')
    mes.append(f'{npc.name} 气力-{energy_cost}')
    # 处理好感和信赖
    # TODO: 增加属性加成
    favor = randint(1, 4)
    trust = randint(1, 2)
    npc.base['favor'] += favor
    npc.base['trust'] += trust

    mes.append(f'好感+{favor}')
    mes.append(f'信赖+{trust}')
    mes += npc_events

    mes.append(f'度过了{command_time_data["rub_the_head"]}分钟')
    if ex_mes:
        mes.append(ex_mes)
    return mes