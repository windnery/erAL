from dataclasses import dataclass, field
from typing import ClassVar

from config.cflag_config import ATTACH_MAPPING
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
    body_slots: dict[str, int] = field(default_factory=dict)
    cmd_cooldowns: dict[str, int] = field(default_factory=dict)
    DEFAULT_BODY_SLOTS: ClassVar[dict[str, int]] = {}

    def __post_init__(self):
        # 初始化palam等级
        for k in self.palam.keys():
            self.palam_lv[k] = 0

    def is_cmd_cooling_down(self, command: str, current_time: int) -> bool:
        """检查指令是否处于冷却中"""
        return self.cmd_cooldowns.get(command, 0) > current_time

    def get_cmd_cooldown_remaining(self, command: str, current_time: int) -> int:
        """获取指令剩余冷却分钟数"""
        return max(0, self.cmd_cooldowns.get(command, 0) - current_time)

    def set_cmd_cooldown(self, command: str, expire_time: int) -> None:
        """设置指令冷却到期时间戳（绝对分钟数）"""
        self.cmd_cooldowns[command] = expire_time

    def clear_expired_cooldowns(self, current_time: int) -> None:
        """清理已过期的冷却记录"""
        self.cmd_cooldowns = {
            cmd: exp for cmd, exp in self.cmd_cooldowns.items()
            if exp > current_time
        }

    def has_body_slots(self, slots: dict[str, int]) -> bool:
        """检查身体槽位是否满足要求"""
        return all(self.body_slots.get(k, 0) >= v for k, v in slots.items())

    def consume_body_slots(self, slots: dict[str, int]) -> bool:
        """消耗/占用身体槽位"""
        if not self.has_body_slots(slots):
            return False
        for k, v in slots.items():
            self.body_slots[k] = self.body_slots.get(k, 0) - v
        return True

    def restore_body_slots(self, slots: dict[str, int]) -> None:
        """归还身体槽位（不超过默认上限）"""
        for k, v in slots.items():
            default_max = getattr(self, 'DEFAULT_BODY_SLOTS', {}).get(k, self.body_slots.get(k, 0) + v)
            self.body_slots[k] = min(default_max, self.body_slots.get(k, 0) + v)

    def reset_body_slots(self) -> None:
        """重置所有身体槽位为默认最大值"""
        from copy import deepcopy
        if hasattr(self, 'DEFAULT_BODY_SLOTS') and self.DEFAULT_BODY_SLOTS:
            self.body_slots = deepcopy(self.DEFAULT_BODY_SLOTS)

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

    def set_vitality(self, value: int) -> bool:
        """设置精力，并返回是否还有剩余。"""
        max_vitality = self.base.get('max_vitality', 2000)
        self.base['vitality'] = max(0, min(value, max_vitality))
        return bool(self.base['vitality'])

    def get_vitality(self) -> int:
        """获取精力。旧角色数据没有精力字段时按满精力处理。"""
        return self.base.get('vitality', self.base.get('max_vitality', 2000))

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
            # 倒序遍历：从最高等级往下找第一个满足 v >= threshold 的等级
            for level, threshold in reversed(PALAM_LV.items()):
                if v >= threshold:
                    self.palam_lv[k] = level
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

    def can_insert(self) -> bool:
        """是否有插入能力"""
        # 男
        # TODO: 穿戴假阳具的女
        if self.get_talent_value('sex') > 0:
            return True

        return False

    def cflag_clear_except(self, keys: list[str]) -> None:
        """除keys外，清空cflag"""
        for k in self.cflag.keys():
            if k not in keys:
                self.cflag[k] = False

    def cflag_set_attach(self, key: str) -> None:
        """设置key的附属cflag"""
        attach_cflags = ATTACH_MAPPING.get(key, [])
        for attach_cflag in attach_cflags:
            self.cflag[attach_cflag] = True

    def is_tired(self) -> bool:
        """是否疲倦"""
        return self.cflag['tired']

    def is_dating(self) -> bool:
        """是否正在约会"""
        return self.cflag.get("dating", False)