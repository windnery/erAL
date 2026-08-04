from random import randint

from game_engine.commands._commands import register_cmd
from game_engine.commands._context import CommandContext
from data.time.time_data import command_time_data


@register_cmd('nap', '小睡', '日常')
def nap(world, option=None):
    '''小睡'''
    ctx = CommandContext(world)
    player = world.player

    ctx.say(f"{player.name}在沙发上躺下……")

    # 推进时间
    ctx.advance_time(command_time_data['nap'])

    # 回复体力和气力
    stamina_recovered = int(player.get_stamina() * 0.25) + randint(-80, 100)
    energy_recovered = int(player.get_energy() * 0.25) + randint(-80, 100)
    ctx.recover(stamina=stamina_recovered, energy=energy_recovered)

    ctx.say(f"小睡了一会儿，恢复了{stamina_recovered}点体力和{energy_recovered}点气力")
    return ctx.result()


@register_cmd('sleep', '睡觉', '日常')
def sleep(world, option=None):
    '''睡觉'''
    # 调用settle_day方法进行日终结算
    mes = world.settle_day(sleep=True)
    return mes


@register_cmd('work', '工作', '日常')
def work(world, option=None):
    '''工作'''
    ctx = CommandContext(world)
    work_manager = world.work_manager

    ctx.say("埋头认真工作……")

    # 推进时间
    ctx.advance_time(command_time_data['work'])

    # 做工作
    works = randint(100, 200)
    stamina_cost = 150
    energy_cost = 200
    work_manager.do_work(works)

    # 消耗体力和气力
    ctx.consume(stamina=stamina_cost, energy=energy_cost)
    ctx.say(f"{world.player.name}完成了{works}工作量，还剩{work_manager.works}工作量")

    return ctx.result()
