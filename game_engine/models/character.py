from dataclasses import dataclass, field

from config.palam_config import PALAM_LV
from config.attr_defs import ATTR_DEFS


@dataclass
class Character:
    """角色基类 - Player 和 ShipGirl 的公共抽象"""
    id: str
    name: str
    location: dict[str, str] = field(default_factory=dict)
    base: dict[str, int] = field(default_factory=dict)
    abl: dict[str, int] = field(default_factory=dict)
    cflag: dict[str, bool] = field(default_factory=dict)
    exp: dict[str, int] = field(default_factory=dict)
    juel: dict[str, int] = field(default_factory=dict)
    palam: dict[str, int] = field(default_factory=dict)
    palam_lv: dict[str, int] = field(default_factory=dict)
    talent: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # 初始化palam等级
        for k in self.palam.keys():
            self.palam_lv[k] = 0

    def set_stamina(self, value: int) -> bool:
        """设置体力，返回是否还有剩余"""
        self.base['stamina'] = max(0, min(value, self.base['max_stamina']))
        return bool(self.base['stamina'])

    def set_energy(self, value: int) -> bool:
        """设置气力，返回是否还有剩余"""
        self.base['energy'] = max(0, min(value, self.base['max_energy']))
        return bool(self.base['energy'])

    def get_stamina(self) -> int:
        """获取体力"""
        return self.base['stamina']

    def get_energy(self) -> int:
        """获取气力"""
        return self.base['energy']

    def is_energy_empty(self) -> bool:
        """气力是否为0"""
        return self.get_energy() == 0

    def set_abl(self, abl: str, value: int) -> None:
        """设置abl"""
        self.abl[abl] = max(0, value)

    def get_abl(self, abl: str) -> int:
        """获取abl"""
        return self.abl.get(abl, 0)

    def set_exp(self, exp: str, value: int) -> None:
        """设置exp"""
        self.exp[exp] = max(0, value)

    def get_exp(self, exp: str) -> int:
        """获取exp"""
        return self.exp.get(exp, 0)

    def clear_palam(self) -> None:
        """清空palam"""
        for k in self.palam.keys():
            self.palam[k] = 0
        # 更新等级
        self.update_palam_level()

    def update_palam_level(self) -> None:
        """更新palam等级"""
        for k, v in self.palam.items():
            for level, threshold in PALAM_LV.items():
                if v < threshold:
                    self.palam_lv[k] = level - 1
                    break

    def get_talent_list(self) -> list[str]:
        """获取天赋列表"""
        talents = []
        for k, v in self.talent.items():
            if ATTR_DEFS['talent'][k]['has_value']:
                # 多分类素质
                talents.append(ATTR_DEFS['talent'][k]['value'][v])
            else:
                # 二分类素质
                talents.append(ATTR_DEFS['talent'][k]['name'])
        return talents

    def set_talent(self, talent_id: str, value: str):
        """设置天赋"""
        self.talent[talent_id] = value

    def has_talent(self, talent_id: str) -> bool:
        """检查是否拥有某天赋"""
        return talent_id in self.talent

    def get_talent_value(self, talent_id: str) -> int:
        """获取某天赋的等级"""
        return int(self.talent.get(talent_id, 0))

    def get_talent_name(self, talent_id: str):
        """获取某天赋的名字"""
        if ATTR_DEFS['talent'][talent_id]['has_value']:
            # 多分类素质
            return ATTR_DEFS['talent'][talent_id]['value'][self.talent.get(talent_id, '0')]
        else:
            # 二分类素质
            return ATTR_DEFS['talent'][talent_id]['name']
