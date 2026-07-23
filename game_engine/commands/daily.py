from random import randint

from game_engine.commands._commands import register_cmd
from data.time.time_data import daily_time_data

@register_cmd('nap')
def nap(world, option=None):
    '''小睡'''
    # 推进时间
    world.time_manager.advance_time(daily_time_data['nap'])
    # 回复体力和气力
    player = world.player
    stamina_recovered = int(player.get_stamina() * 0.25) + randint(-80, 100)
    energy_recovered = int(player.get_energy() * 0.25) + randint(-80, 100)

    world.change_energy(energy_recovered)
    world.change_stamina(stamina_recovered)
    
    return [f"{player.name}在沙发上躺下……",
            f"小睡了一会儿，恢复了{stamina_recovered}点体力和{energy_recovered}点气力"]

@register_cmd('sleep')
def sleep(world, option=None):
    '''睡觉'''
    # 调用settle_day方法进行日终结算
    mes = world.settle_day(sleep=True)
    
    return mes

@register_cmd('work')
def work(world, option=None):
    '''工作'''
    # 推进时间
    world.time_manager.advance_time(daily_time_data['work'])
    # 做工作
    work_manager = world.work_manager

    works = randint(100, 200)  # 随机工作量
    stamina_cost = 150
    energy_cost = 200
    work_manager.do_work(works)

    # 消耗体力和气力
    ex_mes = world.change_energy(-energy_cost)
    ex_mes += world.change_stamina(-stamina_cost)
    
    return [f"埋头认真工作……",
            f"体力-{stamina_cost}　气力-{energy_cost}",
            f"{world.player.name}完成了{works}工作量，还剩{work_manager.works}工作量",
            ex_mes]