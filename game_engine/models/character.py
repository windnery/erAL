from dataclasses import dataclass, field


@dataclass
class Character:
    '''角色基类 - Player 和 ShipGirl 的公共抽象'''
    id: str
    name: str
    location: dict[str, str] = field(default_factory=dict)
    base: dict[str, int] = field(default_factory=dict)
    abl: dict[str, int] = field(default_factory=dict)
    exp: dict[str, int] = field(default_factory=dict)
    talent: dict[str, str] = field(default_factory=dict)

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
