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
    player.stamina = min(player.stamina + stamina_recovered, player.max_stamina)
    player.energy = min(player.energy + energy_recovered, player.max_energy)

    mes = f"{player.name}小睡了一会儿，恢复了{stamina_recovered}点体力和{energy_recovered}点气力。"
    return mes