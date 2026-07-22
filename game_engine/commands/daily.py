from random import randint

from game_engine.commands._commands import register_cmd
from data.time.time_data import daily_time_data

@register_cmd('nap')
def nap(manager, option=None):
    '''小睡'''
    # 推进时间
    manager.time_manager.advance_time(daily_time_data['nap'])
    # 回复体力和气力
    player = manager.player
    stamina_recovered = int(player.max_stamina * 0.25) + randint(-80, 100)
    energy_recovered = int(player.max_energy * 0.25) + randint(-80, 100)

    manager.change_energy(energy_recovered)
    manager.change_stamina(stamina_recovered)
    
    mes = f"{player.name}小睡了一会儿，恢复了{stamina_recovered}点体力和{energy_recovered}点气力"
    return mes

@register_cmd('sleep')
def sleep(manager, option=None):
    '''睡觉'''
    # 调用settle_day方法进行日终结算
    mes = manager.settle_day(sleep=True)
    
    return mes

@register_cmd('work')
def work(manager, option=None):
    '''工作'''
    # 推进时间
    manager.time_manager.advance_time(daily_time_data['work'])
    # 做工作
    work_manager = manager.work_manager

    works = randint(100, 200)  # 随机工作量
    stamina_cost = 150
    energy_cost = 200
    work_manager.do_work(works)
    # 消耗体力和气力
    mes = f"体力-{stamina_cost} 气力-{energy_cost}\n"
    mes += f"{manager.player.name}完成了{works}工作，还剩{work_manager.works}工作量"

    mes += manager.change_energy(-energy_cost)
    mes += manager.change_stamina(-stamina_cost)
    
    return mes