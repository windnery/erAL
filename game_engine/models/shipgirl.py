from dataclasses import dataclass
import random
from typing import Any


from config.mood_enum import Mood


@dataclass
class ShipGirl:
    '''舰娘类'''
    id: str                         # 舰娘ID
    name: str                       # 姓名
    location: dict[str, str]        # 位置

    base: dict[str, int]            # 基础属性
    abl: dict[str, int]             # 能力值
    exp: dict[str, int]             # 经验值
    talent: dict[str, str]          # 天赋/素质

    schedule: dict[str, Any]        # 作息时间表
    lines: list[dict[str, Any]]     # 台词

    def get_state(self):
        '''返回舰娘状态'''
        return {
            'id': self.id,
            'name': self.name,
            'base': self.base,
            'abl': self.abl,
            'exp': self.exp,
            'talent': self.talent,
            'schedule': self.schedule,
            'mood_label': self.get_mood().value,
        }

    def set_stamina(self, value: int):
        '''设置体力'''
        self.base['stamina'] = max(0, min(value, self.base['max_stamina']))
        return bool(self.base['stamina'])

    def set_energy(self, value: int):
        '''设置气力'''
        self.base['energy'] = max(0, min(value, self.base['max_energy']))
        return bool(self.base['energy'])

    def get_line(self, action: str) -> str | None:
        '''获取台词'''
        candidates = [l for l in self.lines if l['action'] == action
                      and self._check_conditions(l.get('conditions', {}))]
        if not candidates:
            return None
        # 随机选择一条台词
        line = random.choice(candidates)
        texts = line.get('texts', [])
        if not texts:
            return None
        return random.choice(texts)

    def _check_conditions(self, conds: dict[str, Any]) -> bool:
        '''检查条件是否满足'''
        for key, value in conds.items():
            if key == 'min_favor' and self.base.get('favor', 0) < value:
                return False
            elif key == 'max_favor' and self.base.get('favor', 0) > value:
                return False
            elif key == 'min_trust' and self.base.get('trust', 0) < value:
                return False
            elif key == 'max_trust' and self.base.get('trust', 0) > value:
                return False
            # TODO: 后续条件检查在这里添加
        return True

    def get_mood(self) -> Mood:
        '''获取心情值'''
        if -10 <= self.base.get('mood', 0) < -5:
            return Mood.ANGRY
        elif -5 <= self.base.get('mood', 0) < 0:
            return Mood.UNHAPPY
        elif 0 <= self.base.get('mood', 0) < 2:
            return Mood.NEUTRAL
        elif 2 <= self.base.get('mood', 0) < 5:
            return Mood.HAPPY
        elif 5 <= self.base.get('mood', 0) < 8:
            return Mood.DELIGHTED
        else:
            return Mood.BLISS