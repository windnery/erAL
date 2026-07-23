from dataclasses import dataclass
from typing import Any


@dataclass
class ShipGirl:
    '''舰娘类'''
    id: str                   # 舰娘ID
    name: str                 # 姓名
    location: dict[str, str]  # 位置
    base: dict[str, int]      # 基础属性
    talent: dict[str, str]    # 天赋/素质
    schedule: dict[str, Any]  # 作息时间表

    def get_state(self):
            '''返回舰娘状态'''
            return {
                'id': self.id,
                'name': self.name,
                'base': self.base,
                'talent': self.talent,
                'schedule': self.schedule,
            }

    def set_stamina(self, value: int):
        '''设置体力'''
        self.base['stamina'] = max(0, min(value, self.base['max_stamina']))
        return bool(self.base['stamina'])

    def set_energy(self, value: int):
        '''设置气力'''
        self.base['energy'] = max(0, min(value, self.base['max_energy']))
        return bool(self.base['energy'])