from dataclasses import dataclass

from config.chara_config import PLAYER_DATA
from game_engine.models.character import Character


@dataclass
class Player(Character):
    """玩家类"""
    id: str = PLAYER_DATA['id']
    name: str = PLAYER_DATA['name']
    money: int = 0

    def __post_init__(self):
        self.wake_time = PLAYER_DATA['wake_time']
        self.location = PLAYER_DATA['location']
        self.base = PLAYER_DATA['base']
        self.abl = PLAYER_DATA['abl']
        self.exp = PLAYER_DATA['exp']
        self.juel = PLAYER_DATA['juel']
        self.palam = PLAYER_DATA['palam']
        self.talent = PLAYER_DATA['talent']

    def get_state(self):
        """返回玩家状态"""
        return {
            'name': self.name,
            'wake_time': self.wake_time,
            'location': self.location,
            'base': self.base,
            'money': self.money
        }

    def set_money(self, value: int):
        """设置金钱"""
        self.money = max(0, value)
