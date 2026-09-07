from random import random

from config.mood_config import MOOD_GOOD
from game_engine.models.character import Character
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_notice


def royal_tea(target: Character):
    """皇家红茶效果"""
    mes_lst: list[str] = []
    # 恢复体力和气力
    stamina_recovery = target.get_max_stamina() * 0.1
    energy_recovery = target.get_max_energy() * 0.1
    target.set_stamina(int(target.get_stamina() + stamina_recovery))
    target.set_energy(int(target.get_energy() + energy_recovery))

    mes_lst.append(
        f'{target.name} 体力+{int(stamina_recovery)} 气力+{int(energy_recovery)}')
    return mes_lst


def ice_cola(target: Character):
    """冰可乐效果"""
    mes_lst: list[str] = []
    energy_recovery = target.get_max_energy() * 0.15
    target.set_energy(int(target.get_energy() + energy_recovery))
    mes_lst.append(f'{target.name} 气力+{int(energy_recovery)}')

    if isinstance(target, ShipGirl) and target.get_mood() < MOOD_GOOD and random() < 0.1:
        # 舰娘额外进行心情判定 10%概率变为好心情
        target.set_mood(MOOD_GOOD)
        mes_lst.append(c_notice(f'{target.name} 的心情变好了！'))

    return mes_lst


def caffe(target: Character):
    """咖啡效果"""
    mes_lst: list[str] = []
    energy_recovery = target.get_max_energy() * 0.3
    target.set_energy(int(target.get_energy() + energy_recovery))
    mes_lst.append(f'{target.name} 气力+{int(energy_recovery)}')

    # 获得咖啡因效果
    target.cflag['caffeine'] = True

    return mes_lst
