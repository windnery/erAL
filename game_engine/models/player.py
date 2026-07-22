from dataclasses import dataclass

from data.data_loader import load_player


@dataclass
class Player:
    '''玩家类'''
    player_data = load_player()
    name: str = player_data.get('name', '指挥官')              # 姓名
    max_stamina: int = player_data.get('max_stamina', 2000)   # 最大体力
    max_energy: int = player_data.get('max_energy', 2000)     # 最大气力
    stamina: int = max_stamina                                # 体力
    energy: int = max_energy                                  # 气力

    def get_state(self):
        '''返回玩家状态'''
        return {
            'name': self.name,
            'max_stamina': self.max_stamina,
            'max_energy': self.max_energy,
            'stamina': self.stamina,
            'energy': self.energy
        }
