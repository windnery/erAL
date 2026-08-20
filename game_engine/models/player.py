from copy import deepcopy
from dataclasses import dataclass

from data.data_loader import load_player
from game_engine.models.character import Character


@dataclass
class Player(Character):
    """玩家类"""
    player_data = load_player()
    id: str = player_data['id']
    name: str = player_data['name']
    money: int = 0

    def __post_init__(self):
        self.wake_time = deepcopy(self.player_data['wake_time'])
        self.location = deepcopy(self.player_data['location'])
        self.base = deepcopy(self.player_data['base'])
        self.abl = deepcopy(self.player_data['abl'])
        self.exp = deepcopy(self.player_data['exp'])
        self.juel = deepcopy(self.player_data['juel'])
        self.palam = deepcopy(self.player_data['palam'])
        self.talent = deepcopy(self.player_data['talent'])
        super().__post_init__()

    def get_state(self):
        """返回玩家状态"""
        return {
            'name': self.name,
            'wake_time': self.wake_time,
            'location': self.location,
            'base': self.base,
            'abl': self.abl,
            'exp': self.exp,
            'talent_list': self.get_talent_list(),
            'money': self.money
        }

    def set_money(self, value: int):
        """设置金钱"""
        self.money = max(0, value)
