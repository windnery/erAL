from random import randint

from .._common import mood_process
from .._commands import register_cmd
from data.time.time_data import command_time_data


@register_cmd('talk')
def talk(world, option: str):
    '''会话
    world: 游戏世界对象
    option: 指令对象'''
    mes = []

    npc = world.npc_manager.get_npc_by_id(option)
    line = npc.get_line('talk')

    mes.append(f'和{npc.name}聊了一会儿……')
    # fallback: 如果没有找到合适的台词，返回默认消息
    if not line:
        return mes
    line = line.replace('{name}', npc.name)
    mes.append(line)

    # 推进时间并获取NPC变动消息
    npc_events = world.advance_time_with_events(command_time_data['talk'])

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
    # abl: 会话
    ex_favor = randint(1, 2) * world.player.abl['talk']
    ex_trust = randint(1, 2) * world.player.abl['talk'] // 2
    # mood: 心情
    ex_mood = mood_process(npc.get_mood())
    # TODO: 后续加成在这里添加

    favor = max(0, randint(1, 2) + ex_favor + ex_mood)
    trust = max(0, 1 + ex_trust + ex_mood)
    npc.base['favor'] += favor
    npc.base['trust'] += trust

    mes.append(f'好感+{favor}')
    mes.append(f'信赖+{trust}')

    # 获得经验处理
    # exp: 会话经验
    npc.exp['talk_exp'] += 1
    world.player.exp['talk_exp'] += 1

    mes += npc_events

    mes.append(f'度过了{command_time_data["talk"]}分钟')
    if ex_mes:
        mes.append(ex_mes)
    return mes


