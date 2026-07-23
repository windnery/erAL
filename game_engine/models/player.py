from dataclasses import dataclass, field

from data.data_loader import load_player


@dataclass
class Player:
    '''玩家类'''
    player_data = load_player()
    
    id: str = player_data['id']                 # 玩家ID
    name: str = player_data['name']              # 姓名
    location: dict[str, str] = field(default_factory=dict)  # 位置
    base: dict[str, int] = field(default_factory=dict)    # 基础属性
    money: int = 0                                            # 金钱

    def __post_init__(self):
        self.location = self.player_data['location']
        self.base = self.player_data['base']

    def get_state(self):
        '''返回玩家状态'''
        return {
            'name': self.name,
            'location': self.location,
            'base': self.base,
            'money': self.money
        }

    def set_stamina(self, value: int):
        '''设置体力'''
        self.base['stamina'] = max(0, min(value, self.base['max_stamina']))
        return bool(self.base['stamina'])

    def set_energy(self, value: int):
        '''设置气力'''
        self.base['energy'] = max(0, min(value, self.base['max_energy']))
        return bool(self.base['energy'])

    def get_stamina(self):
        '''获取体力'''
        return self.base['stamina']

    def get_energy(self):
        '''获取气力'''
        return self.base['energy']

    def set_money(self, value: int):
        '''设置金钱'''
        self.money = max(0, value)