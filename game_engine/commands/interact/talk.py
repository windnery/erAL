from random import randint

from .._common import mood_process
from .._commands import register_cmd
from .._context import CommandContext
from data.time.time_data import command_time_data


@register_cmd('talk')
def talk(world, option: str):
    '''会话
    world: 游戏世界对象
    option: 指令对象'''
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)

    line = npc.get_line('talk')
    ctx.say(f'和{npc.name}聊了一会儿……')
    if not line:
        return ctx.result()
    ctx.say(line.replace('{name}', npc.name))

    # 推进时间
    ctx.advance_time(command_time_data['talk'])

    # 体力和气力消耗
    stamina_cost = 5
    energy_cost = 10
    ctx.consume(stamina=stamina_cost, energy=energy_cost, npc=npc)

    # 处理好感和信赖
    ex_favor = randint(1, 2) * world.player.abl['talk_abl']
    ex_trust = randint(1, 2) * world.player.abl['talk_abl'] // 2
    ex_mood = mood_process(npc.get_mood())
    # TODO: 后续加成在这里添加

    favor = max(0, randint(1, 2) + ex_favor + ex_mood)
    trust = max(0, 1 + ex_trust + ex_mood)
    npc.base['favor'] += favor
    npc.base['trust'] += trust

    ctx.say(f'好感+{favor}', f'信赖+{trust}')

    # 获得经验处理
    npc.exp['talk_exp'] += 1
    world.player.exp['talk_exp'] += 1
    ctx.say(f'{npc.name} 会话经验+1', f'{world.player.name} 会话经验+1')

    ctx.say(f'度过了{command_time_data["talk"]}分钟')
    return ctx.result()
