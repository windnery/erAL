from dataclasses import dataclass

from data.data_loader import load_player
from game_engine.models.character import Character


@dataclass
class Player(Character):
    '''玩家类'''
    player_data = load_player()

    id: str = player_data['id']
    name: str = player_data['name']
    money: int = 0

    def __post_init__(self):
        self.location = self.player_data['location']
        self.base = self.player_data['base']
        self.abl = self.player_data['abl']
        self.exp = self.player_data['exp']
        self.talent = self.player_data['talent']

    def get_state(self):
        '''返回玩家状态'''
        return {
            'name': self.name,
            'location': self.location,
            'base': self.base,
            'money': self.money
        }

    def set_money(self, value: int):
        '''设置金钱'''
        self.money = max(0, value)
