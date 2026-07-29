from dataclasses import dataclass, field

from config.palam_lv import palam_lv
from data.data_loader import load_attr_defs

attr_defs = load_attr_defs()

@dataclass
class Character:
    '''角色基类 - Player 和 ShipGirl 的公共抽象'''
    id: str
    name: str
    location: dict[str, str] = field(default_factory=dict)
    base: dict[str, int] = field(default_factory=dict)
    abl: dict[str, int] = field(default_factory=dict)
    exp: dict[str, int] = field(default_factory=dict)
    palam: dict[str, int] = field(default_factory=dict)
    palam_lv: dict[str, int] = field(default_factory=dict)
    talent: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # 初始化palam等级
        for k in self.palam.keys():
            self.palam_lv[k] = 0

    def set_stamina(self, value: int) -> bool:
        '''设置体力，返回是否还有剩余'''
        self.base['stamina'] = max(0, min(value, self.base['max_stamina']))
        return bool(self.base['stamina'])

    def set_energy(self, value: int) -> bool:
        '''设置气力，返回是否还有剩余'''
        self.base['energy'] = max(0, min(value, self.base['max_energy']))
        return bool(self.base['energy'])

    def get_stamina(self) -> int:
        '''获取体力'''
        return self.base['stamina']

    def get_energy(self) -> int:
        '''获取气力'''
        return self.base['energy']

    def update_palam_level(self) -> None:
        '''更新palam等级'''
        for k, v in self.palam.items():
            for level, threshold in palam_lv.items():
                if v < threshold:
                    self.palam_lv[k] = level - 1
                    break

    def get_talent_list(self) -> list[str]:
        '''获取天赋列表'''
        talents = []
        for k, v in self.talent.items():
            if attr_defs['talent'][k]['has_value']:
                # 多分类素质
                talents.append(attr_defs['talent'][k]['value'][v])
            else:
                # 二分类素质
                talents.append(attr_defs['talent'][k]['name'])
        return talents